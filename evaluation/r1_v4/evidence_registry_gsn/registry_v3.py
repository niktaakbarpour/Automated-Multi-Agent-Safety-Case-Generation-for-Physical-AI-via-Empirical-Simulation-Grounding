"""R1 v3 saved-frame registry. Records describe sources, not physical conclusions."""

import hashlib
import math
from pathlib import Path
import sqlite3
from xml.etree import ElementTree

import h5py
from jsonschema import Draft202012Validator

from evaluation.r1_v4.libero_measurement_reader.reader import native_index
from evaluation.r1_v4.provenance import canonical, digest, load, strict_loads


R1_V3 = "r1-initial-table-support-v3-20261024"
SCHEMA_VERSION = "2.0.0"
APPLICATION_ID = 0x52315633
HERE = Path(__file__).parent
RECORD_SCHEMA = Draft202012Validator(load(HERE / "registry_v3_record.schema.json"))
IDENTITY_FIELDS = ("execution_id", "task_id", "object_id", "trajectory_sha256")
INDEX_FIELDS = ("requirement_id", "requirement_version", "execution_id", "object_id", "kind")
FRAME_SELECTORS = {
    "contact": ("simulator/contacts",),
    "native_geometry": ("simulator/geom_xpos/value", "simulator/geom_xmat/value"),
    "object_pose": ("simulator/body_xpos/value", "simulator/body_xquat/value"),
    "timestamp": ("simulator/time/value",),
    "camera_reference": (
        "raw_observation/agentview_image/value",
        "raw_observation/robot0_eye_in_hand_image/value",
    ),
    "robot_state": (
        "raw_observation/robot0_eef_pos/value",
        "raw_observation/robot0_eef_quat/value",
        "raw_observation/robot0_joint_pos/value",
        "raw_observation/robot0_joint_vel/value",
        "raw_observation/robot0_gripper_qpos/value",
        "raw_observation/robot0_gripper_qvel/value",
        "simulator/qpos/value",
        "simulator/qvel/value",
        "simulator/ctrl/value",
        "simulator/actuator_force/value",
    ),
    "recorded_state": ("simulator/flattened/value",),
}
NATIVE_ROW_WIDTHS = {"body_xpos": 3, "body_xquat": 4, "geom_xpos": 3, "geom_xmat": 9}


def _record_id(body):
    return "ev:" + digest(body)


def make_record(payload):
    """Assign a content ID to proposed JSON metadata and validate the result."""
    if "id" in payload:
        raise ValueError("new record payload must omit id")
    return validate_record({"id": _record_id(payload), **payload})


def validate_record(record):
    """Check a versioned record and content ID without opening its artifact."""
    if isinstance(record, dict) and record.get("schema_version") == "2.1.0":
        from evaluation.r1_v4.evidence_registry_gsn.registry_v3_task8c import validate_task8c_record
        return validate_task8c_record(record)
    error = next(RECORD_SCHEMA.iter_errors(record), None)
    if error is not None:
        field = ".".join(map(str, error.absolute_path)) or "record"
        raise ValueError(f"invalid R1 v3 record field {field}: {error.message}")

    first, last = record["interval"]
    frames = record["saved_frames"]
    indices = [entry["frame"] for entry in frames]
    if any(type(n) is not int for n in (first, last, *indices)):
        raise ValueError("saved frame indices must be integers")
    if indices != sorted(set(indices)) or not first <= indices[0] <= indices[-1] <= last:
        raise ValueError("saved frames must be ordered, unique and within the inclusive interval")

    binding = record.get("native_binding")
    if binding is not None and any(
        type(n) is not int for n in (binding["body_id"], *binding["collision_geom_ids"])
    ):
        raise ValueError("native body and geometry IDs must be integers")

    if record["kind"] == "raw_measurement":
        if record["source"]["sha256"] != record["trajectory_sha256"]:
            raise ValueError("raw source must bind the original trajectory hash")
        for entry in frames:
            prefix = f'/frames/{entry["frame"]:06d}/'
            if any(not selector.startswith(prefix) or selector == prefix for selector in entry["selectors"]):
                raise ValueError("measurement selector must identify the declared saved frame")
            if any(
                selector.removeprefix(prefix) not in FRAME_SELECTORS[record["measurement_type"]]
                for selector in entry["selectors"]
            ):
                raise ValueError("selector does not match the declared measurement type")

    body = {key: value for key, value in record.items() if key != "id"}
    if record["id"] != _record_id(body):
        raise ValueError("record content hash mismatch")
    return record


def _verify_artifact(artifact, root, checked):
    path = Path(artifact["path"])
    if path.name.casefold() == "human_reference_evaluation_only.json":
        raise ValueError("evaluation-only human reference is outside the registry scope")
    if not path.is_relative_to(root) or ".." in path.parts:
        raise ValueError("artifact outside the approved source root")
    if path not in checked:
        try:
            if path.resolve(strict=True) != path or not path.is_file():
                raise ValueError("artifact must be a regular file without symlinks")
            with path.open("rb") as stream:
                checked[path] = hashlib.file_digest(stream, "sha256").hexdigest()
        except (OSError, RuntimeError) as error:
            raise ValueError(f"cannot verify artifact: {path}") from error
    if checked[path] != artifact["sha256"]:
        raise ValueError(f"artifact hash mismatch: {path}")


def _verify_record_sources(
    record, root, checked, trusted_task8c_manifest_hashes=(),
    trusted_task8c_artifact_hashes=None, trusted_task8c_runner_hashes=(),
):
    _verify_artifact(record["source"], root, checked)
    if record.get("schema_version") == "2.1.0":
        from evaluation.r1_v4.evidence_registry_gsn.registry_v3_task8c import verify_task8c_artifacts
        verify_task8c_artifacts(
            record, root, checked, trusted_task8c_manifest_hashes,
            trusted_task8c_artifact_hashes or {}, trusted_task8c_runner_hashes,
        )
        return
    if "native_binding" in record:
        binding = record["native_binding"]
        _verify_artifact(binding["mapping"], root, checked)
        _verify_artifact(binding["simulator_xml"], root, checked)
    if "checker" in record:
        _verify_artifact(record["checker"]["config"], root, checked)


def _trajectory_node(trajectory, selector):
    node = trajectory
    for component in selector[1:].split("/"):
        if (
            not component or component in (".", "..") or not isinstance(node, h5py.Group)
            or not isinstance(node.get(component, getlink=True), h5py.HardLink)
        ):
            raise ValueError(f"missing or indirect trajectory selector: {selector}")
        node = node[component]
    if isinstance(node, h5py.Dataset) and (node.external or node.is_virtual):
        raise ValueError(f"external or virtual trajectory data: {selector}")
    return node


def _check_contact_payload(trajectory, simulator, native):
    path = simulator + "/contacts"
    contacts = _trajectory_node(trajectory, path)
    if not isinstance(contacts, h5py.Group):
        raise ValueError("invalid serialized contact group")
    pairs = None
    if "json" in contacts.attrs:
        payload = contacts.attrs["json"]
        if isinstance(payload, (str, bytes)):
            pairs = strict_loads(payload)
    elif isinstance(contacts.get("value", getlink=True), h5py.HardLink):
        empty = _trajectory_node(trajectory, path + "/value")
        if isinstance(empty, h5py.Dataset) and empty.shape == (0,):
            pairs = []
    if not isinstance(pairs, list):
        raise ValueError("missing or invalid serialized contact data")
    count = _trajectory_node(trajectory, simulator + "/ncon/value")
    if (
        not isinstance(count, h5py.Dataset) or count.shape != ()
        or count.dtype.kind not in "iu" or count[()] != len(pairs)
    ):
        raise ValueError("serialized contact count does not match the trajectory")
    for pair in pairs:
        if not isinstance(pair, dict) or not {"geom1", "geom2", "dist", "pos"} <= pair.keys():
            raise ValueError("contact is missing native pair data")
        native.contact_pair(pair)
        position = pair["pos"]
        if not isinstance(position, list) or len(position) != 3 or any(
            type(value) not in (int, float) or not math.isfinite(value)
            for value in (pair["dist"], *position)
        ):
            raise ValueError("invalid recorded contact numerics")


def _verify_trajectory(
    record, *, source_root=None, trusted_task8c_manifest_hashes=(),
    trusted_task8c_artifact_hashes=None, trusted_task8c_runner_hashes=(),
):
    if record.get("schema_version") == "2.1.0":
        from evaluation.r1_v4.evidence_registry_gsn.registry_v3_task8c import verify_task8c_record
        return verify_task8c_record(
            record, source_root, trusted_task8c_manifest_hashes,
            trusted_task8c_artifact_hashes or {}, trusted_task8c_runner_hashes,
        )
    binding = record.get("native_binding")
    native = _verify_native_binding(record) if binding is not None else None
    measurement_type = record["measurement_type"]
    row_ids = ()
    if measurement_type == "object_pose":
        row_ids = (binding["body_id"],)
    elif measurement_type == "native_geometry":
        row_ids = binding["collision_geom_ids"]
    try:
        with h5py.File(record["source"]["path"], "r") as trajectory:
            if (
                trajectory.attrs.get("global_episode_id") != record["execution_id"]
                or trajectory.attrs.get("task_configuration_id") != record["task_id"]
            ):
                raise ValueError("trajectory execution or task binding mismatch")
            for frame in record["saved_frames"]:
                simulator = f'/frames/{frame["frame"]:06d}/simulator'
                if native is not None:
                    positions = _trajectory_node(trajectory, simulator + "/geom_xpos/value")
                    if (
                        not isinstance(positions, h5py.Dataset) or positions.ndim != 2
                        or positions.shape[1] != 3
                    ):
                        raise ValueError("missing native geometry rows for the recorded model")
                    native.validate_recording(
                        record["execution_id"], binding["simulator_xml"]["sha256"], positions.shape[0]
                    )
                for selector in frame["selectors"]:
                    value = _trajectory_node(trajectory, selector)
                    if measurement_type != "contact" and (
                        not isinstance(value, h5py.Dataset) or not value.size
                    ):
                        raise ValueError("measurement selector must locate a saved dataset")
                    if row_ids and (
                        value.ndim != 2 or value.shape[0] <= max(row_ids)
                        or value.shape[1] != NATIVE_ROW_WIDTHS[selector.rsplit("/", 2)[1]]
                        or value.dtype.kind != "f"
                    ):
                        raise ValueError("saved dataset lacks valid rows for the cited native IDs")
                if measurement_type == "contact":
                    _check_contact_payload(trajectory, simulator, native)
                if measurement_type == "timestamp" or "simulator_time_seconds" in frame:
                    timestamp = _trajectory_node(trajectory, simulator + "/time/value")
                    if (
                        not isinstance(timestamp, h5py.Dataset) or timestamp.shape != ()
                        or timestamp.dtype.kind not in "fiu" or not math.isfinite(timestamp[()])
                    ):
                        raise ValueError("invalid recorded simulator timestamp")
                    if (
                        "simulator_time_seconds" in frame
                        and timestamp[()] != frame["simulator_time_seconds"]
                    ):
                        raise ValueError("saved-frame timestamp does not match the trajectory")
    except OSError as error:
        raise ValueError("cannot read original HDF5 trajectory") from error


def _verify_native_binding(record):
    binding = record["native_binding"]
    xml_path = Path(binding["simulator_xml"]["path"])
    if xml_path != Path(record["source"]["path"]).with_name("simulator.xml"):
        raise ValueError("simulator XML must be from the same recording as the trajectory")
    try:
        profile = load(binding["mapping"]["path"])
        selector = "/mapping/geometries" if "mapping" in profile else "/geometries"
        if binding["mapping"]["selector"] != selector:
            raise ValueError("native mapping selector must identify the geometry index")
        index = native_index(profile.get("mapping", profile))
        if not isinstance(index.record["validated_run_ids"], list):
            raise ValueError("native map requires an explicit list of validated executions")
        bodies = index.record["body_names"]
        body_id = binding["body_id"]
        geometries = [index.by_id(geom) for geom in binding["collision_geom_ids"]]
        body_name = record["object_id"] + "_main"
        xml = ElementTree.parse(xml_path).getroot()
        if (
            xml.tag != "mujoco" or body_id >= len(bodies) or bodies[body_id] != body_name
            or not any(body.get("name") == body_name for body in xml.iter("body"))
            or any(
                geom["owner_body_id"] != body_id or geom["collision_capable"] is not True
                for geom in geometries
            )
        ):
            raise ValueError("native geometry mapping scope or ownership mismatch")
        if "mapping" in profile and "objects" in profile:
            selected = profile["objects"][record["object_id"]]
            if selected["body_id"] != body_id or not set(binding["collision_geom_ids"]).issubset(
                selected["collision_geom_ids"]
            ):
                raise ValueError("native profile object binding mismatch")
        return index
    except (AttributeError, KeyError, TypeError, ElementTree.ParseError) as error:
        raise ValueError("invalid native geometry index") from error


def _check_event_source(record):
    checker = record["checker"]
    requirement = {key: record[key] for key in ("requirement_id", "requirement_version")}
    config = load(checker["config"]["path"])
    config_scope = {**requirement, "checker_version": checker["version"]}
    if (
        not isinstance(config, dict) or any(config.get(key) != value for key, value in config_scope.items())
        or not isinstance(config.get("objects"), list) or record["object_id"] not in config["objects"]
    ):
        raise ValueError("checker configuration identity or object scope mismatch")

    _, row, _, event_number = checker["selector"].split("/")
    row, event_number = int(row), int(event_number)
    if checker["selector"] != f"/{row}/events/{event_number}":
        raise ValueError("checker event selector must be a canonical JSON pointer")
    predictions = load(record["source"]["path"])
    try:
        if not isinstance(predictions, list):
            raise TypeError("predictions must be a list")
        prediction = predictions[row]
        if not isinstance(prediction, dict) or not isinstance(prediction.get("events"), list):
            raise TypeError("prediction must contain an event list")
        event = prediction["events"][event_number]
    except (IndexError, TypeError) as error:
        raise ValueError("checker event selector does not resolve to a saved prediction") from error

    identity = {
        "run_id": record["execution_id"],
        "canonical_object_id": record["object_id"],
        "requirement_version": record["requirement_version"],
    }
    prediction_scope = {
        **identity,
        **config_scope,
        "recording_sha256": record["trajectory_sha256"],
        "configuration_sha256": checker["config"]["sha256"],
    }
    if any(prediction.get(key) != value for key, value in prediction_scope.items()):
        raise ValueError("checker prediction scope or configuration hash mismatch")
    event_scope = {**identity, "event_id": checker["event_id"], "interval": record["interval"]}
    if not isinstance(event, dict) or any(
        canonical(event.get(key)) != canonical(value) for key, value in event_scope.items()
    ):
        raise ValueError("checker event identity or interval mismatch")


def _check_event_inputs(
    event, records, root, checked, verified_measurements,
    trusted_task8c_manifest_hashes=(), trusted_task8c_artifact_hashes=None,
    trusted_task8c_runner_hashes=(),
):
    covered = set()
    for record_id in event["checker"]["input_record_ids"]:
        record = records.get(record_id)
        if record is None or record["kind"] != "raw_measurement":
            raise ValueError("checker event requires registered R1 v3 measurement inputs")
        if any(record[key] != event[key] for key in IDENTITY_FIELDS):
            raise ValueError("checker event input scope mismatch")
        if record_id not in verified_measurements:
            _verify_record_sources(
                record, root, checked, trusted_task8c_manifest_hashes,
                trusted_task8c_artifact_hashes, trusted_task8c_runner_hashes,
            )
            _verify_trajectory(
                record, source_root=root,
                trusted_task8c_manifest_hashes=trusted_task8c_manifest_hashes,
                trusted_task8c_artifact_hashes=trusted_task8c_artifact_hashes,
                trusted_task8c_runner_hashes=trusted_task8c_runner_hashes,
            )
            verified_measurements.add(record_id)
        covered.update(entry["frame"] for entry in record["saved_frames"])
    if any(entry["frame"] not in covered for entry in event["saved_frames"]):
        raise ValueError("checker event references an unrecorded input frame")


class RegistryV3:
    """Immutable local SQLite index with an explicitly approved source root."""

    def __init__(
        self, path, *, source_root, create=False, trusted_task8c_manifest_hashes=(),
        trusted_task8c_artifact_hashes=None, trusted_task8c_runner_hashes=(),
    ):
        self.source_root = Path(source_root).resolve(strict=True)
        self.trusted_task8c_manifest_hashes = frozenset(trusted_task8c_manifest_hashes)
        self.trusted_task8c_artifact_hashes = dict(trusted_task8c_artifact_hashes or {})
        self.trusted_task8c_runner_hashes = frozenset(trusted_task8c_runner_hashes)
        if not self.source_root.is_dir():
            raise ValueError("source root must be a directory")
        self.path = Path(path).resolve()
        if create:
            # Reserve the destination exclusively. SQLite will initialize the new empty file.
            with self.path.open("xb"):
                pass
        mode = "rw" if create else "ro"
        self.db = sqlite3.connect(f"{self.path.as_uri()}?mode={mode}", uri=True)
        try:
            if create:
                self.db.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
                self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
            if (
                self.db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or self.db.execute("PRAGMA user_version").fetchone()[0] != 1
            ):
                raise ValueError("unsupported R1 v3 registry database")
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @staticmethod
    def _load_row(row):
        record_id, body, *scope = row
        record = validate_record(strict_loads(body))
        if record_id != record["id"] or scope != [record[key] for key in INDEX_FIELDS]:
            raise ValueError("database index/content mismatch")
        return record

    def records(self):
        return [
            self._load_row(row)
            for row in self.db.execute(
                "SELECT id,body,requirement_id,requirement_version,execution_id,object_id,kind "
                "FROM evidence ORDER BY id"
            )
        ]

    def add(self, records):
        """Verify every artifact and event input before inserting the batch."""
        batch = [validate_record(record) for record in records]
        checked = {}
        verified_measurements = set()
        events = []
        for record in batch:
            _verify_record_sources(
                record, self.source_root, checked,
                self.trusted_task8c_manifest_hashes, self.trusted_task8c_artifact_hashes,
                self.trusted_task8c_runner_hashes,
            )
            if record["kind"] == "raw_measurement":
                _verify_trajectory(
                    record, source_root=self.source_root,
                    trusted_task8c_manifest_hashes=self.trusted_task8c_manifest_hashes,
                    trusted_task8c_artifact_hashes=self.trusted_task8c_artifact_hashes,
                    trusted_task8c_runner_hashes=self.trusted_task8c_runner_hashes,
                )
                verified_measurements.add(record["id"])
            else:
                _check_event_source(record)
                events.append(record)
        if events:
            available = {record["id"]: record for record in (*self.records(), *batch)}
            for event in events:
                _check_event_inputs(
                    event, available, self.source_root, checked, verified_measurements,
                    self.trusted_task8c_manifest_hashes, self.trusted_task8c_artifact_hashes,
                    self.trusted_task8c_runner_hashes,
                )
        with self.db:
            self.db.executemany(
                "INSERT INTO evidence VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING",
                (
                    (record["id"], *(record[k] for k in INDEX_FIELDS), canonical(record).decode())
                    for record in batch
                ),
            )

    def resolve_citation(
        self, record_id, *, execution_id, task_id, object_id, trajectory_sha256,
        measurement_type, frames,
    ):
        """Resolve a measurement for exact saved frames. Gaps and events are ineligible."""
        if not isinstance(record_id, str):
            raise ValueError("citation ID must be a string")
        row = self.db.execute(
            "SELECT id,body,requirement_id,requirement_version,execution_id,object_id,kind "
            "FROM evidence WHERE id=?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise ValueError("unknown R1 v3 citation")
        record = self._load_row(row)
        if record["kind"] != "raw_measurement":
            raise ValueError("only raw measurements are eligible citations")
        scope = (execution_id, task_id, object_id, trajectory_sha256)
        if scope != tuple(record[key] for key in IDENTITY_FIELDS):
            raise ValueError("citation scope mismatch")
        if measurement_type != record["measurement_type"]:
            raise ValueError("citation measurement type mismatch")
        available = {entry["frame"] for entry in record["saved_frames"]}
        if not isinstance(frames, (list, tuple)) or not frames or any(
            type(frame) is not int or frame not in available for frame in frames
        ):
            raise ValueError("citation requires explicitly recorded saved frames")
        _verify_record_sources(
            record, self.source_root, {}, self.trusted_task8c_manifest_hashes,
            self.trusted_task8c_artifact_hashes, self.trusted_task8c_runner_hashes,
        )
        _verify_trajectory(
            record, source_root=self.source_root,
            trusted_task8c_manifest_hashes=self.trusted_task8c_manifest_hashes,
            trusted_task8c_artifact_hashes=self.trusted_task8c_artifact_hashes,
            trusted_task8c_runner_hashes=self.trusted_task8c_runner_hashes,
        )
        if record.get("schema_version") == "2.1.0" and record["task8c_binding"]["runner_status"] != "VERIFIED":
            raise ValueError("Task 8C citation lacks verified capture-runner provenance")
        return record

    def export(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "requirement_id": "R1",
            "requirement_version": R1_V3,
            "records": self.records(),
            "empirical_admission_enabled": False,
        }
