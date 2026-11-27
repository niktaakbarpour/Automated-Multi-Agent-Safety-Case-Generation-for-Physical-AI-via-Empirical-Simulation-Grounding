"""Version 2.1 records and citations for the Task 8C custom HDF5 layout.

The module delegates all source measurement validation/reconstruction to the
recovered versioned Task 8C adapter. Records are source citations only and are
marked development-only; this module cannot issue physical admission.
"""
from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import h5py
from jsonschema import Draft202012Validator

from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.task8c_r1v3_adapter import task8c_adapter
from evaluation.r1_v4.evidence_registry_gsn.registry_v3 import (
    R1_V3, _record_id, _verify_artifact,
)

TASK8C_RECORD_SCHEMA_VERSION = "2.1.0"
TASK8C_LAYOUT_VERSION = "1.0.0"
TASK8C_STRIDE = task8c_adapter.NATIVE_PER_FRAME
TASK8C_RECORD_SCHEMA = Draft202012Validator(
    load(Path(__file__).with_name("task8c_registry_v3_record.schema.json"))
)
TASK8C_SELECTORS = {
    "object_pose": ("/physics/body_xpos", "/physics/body_xquat"),
    "native_geometry": ("/physics/body_xpos", "/physics/body_xquat"),
    "contact": (
        "/contacts/sample_index", "/contacts/geom1", "/contacts/geom2",
        "/contacts/body1", "/contacts/body2", "/contacts/pos", "/contacts/dist",
        "/contacts/frame", "/contacts/force_contact_frame", "/contacts/geom1_name",
        "/contacts/geom2_name", "/contacts/body1_name", "/contacts/body2_name", "/physics/ncon",
    ),
    "timestamp": ("/observations/source_frame", "/observations/time", "/physics/time_after"),
}


def _file_binding(path):
    raw = Path(path)
    if raw.is_symlink():
        raise ValueError("Task 8C source artifact cannot be a symlink")
    p = raw.resolve(strict=True)
    if raw != p or not p.is_file():
        raise ValueError("Task 8C source artifact must be a regular file")
    return {"path": str(p), "sha256": _sha256(p)}


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_task8c_record(record):
    error = next(TASK8C_RECORD_SCHEMA.iter_errors(record), None)
    if error:
        field = ".".join(map(str, error.absolute_path)) or "record"
        raise ValueError(f"invalid Task 8C R1 v3 record field {field}: {error.message}")
    if record["trajectory_sha256"] != record["source"]["sha256"]:
        raise ValueError("Task 8C source hash must equal the trajectory hash")
    interval = record["interval"]
    frames = record["saved_frames"]
    if interval[0] > interval[1] or interval[0] < 10 or interval[1] > 257:
        raise ValueError("Task 8C interval must remain inside saved frames 10..257")
    indices = [item["frame"] for item in frames]
    if indices != sorted(set(indices)) or not interval[0] <= indices[0] <= indices[-1] <= interval[1]:
        raise ValueError("Task 8C saved frames must be ordered, unique, and in scope")
    selectors = TASK8C_SELECTORS[record["measurement_type"]]
    is_complete = indices == list(range(interval[0], interval[1] + 1))
    if record["coverage_status"] != ("complete" if is_complete else "partial"):
        raise ValueError("Task 8C coverage status does not match cited frame set")
    if any(item["native_sample_index"] != item["frame"] * TASK8C_STRIDE for item in frames):
        raise ValueError("Task 8C saved-frame/native-sample mapping mismatch")
    if any(tuple(item["selectors"]) != selectors for item in frames):
        raise ValueError("Task 8C selector set does not match the measurement type")
    binding = record["task8c_binding"]
    if binding["runner_status"] == "VERIFIED" and binding["runner_source"] is None:
        raise ValueError("verified Task 8C runner requires an exact source binding")
    if binding["runner_status"] == "UNVERIFIED" and binding["runner_source"] is not None:
        raise ValueError("unverified Task 8C runner cannot claim an exact source binding")
    if record["measurement_type"] == "native_geometry" and record["derivation"] != "reconstructed_from_recorded_body_pose_and_xml":
        raise ValueError("native geometry must be explicitly marked as reconstructed")
    if record["measurement_type"] != "native_geometry" and record["derivation"] != "direct_source_measurement":
        raise ValueError("direct source measurements cannot claim a reconstruction")
    body = {key: value for key, value in record.items() if key != "id"}
    if record["id"] != _record_id(body):
        raise ValueError("Task 8C record content hash mismatch")
    return record


def _source_manifest_row(record, root, checked, trusted_manifest_hashes):
    binding = record["task8c_binding"]
    manifest = binding["source_manifest"]
    if manifest["sha256"] not in trusted_manifest_hashes:
        raise ValueError("Task 8C source manifest is not authorized by registry trust configuration")
    _verify_artifact(manifest, root, checked)
    try:
        with Path(manifest["path"]).open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError("cannot read Task 8C source manifest") from error
    matching = [row for row in rows if row.get("blinded_case_id") == binding["case_id"]]
    if len(matching) != 1:
        raise ValueError("Task 8C manifest must contain exactly one bound case")
    row = matching[0]
    expected = {
        "new_execution_id": record["execution_id"],
        "coordinator_group_id": binding["source_group_id"],
        "raw_hdf5_sha256": record["trajectory_sha256"],
        "xml_sha256": record["native_binding"]["simulator_xml"]["sha256"],
    }
    if any(row.get(key) != value for key, value in expected.items()):
        raise ValueError("Task 8C case, execution, group, recording, or XML binding mismatch")
    raw_path = row.get("raw_hdf5_path")
    raw_recording = Path(raw_path) if raw_path else None
    if (raw_recording is None or raw_recording.is_symlink() or
        raw_recording.resolve(strict=True) != raw_recording or raw_recording != Path(record["source"]["path"])):
        raise ValueError("Task 8C manifest path does not bind the registered recording")
    runner_manifest = binding["runner_bindings"]
    try:
        with Path(runner_manifest["path"]).open(newline="", encoding="utf-8-sig") as stream:
            runner_rows = list(csv.DictReader(stream))
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError("cannot read Task 8C runner binding manifest") from error
    matches = [item for item in runner_rows if binding["case_id"] in item.get("case_ids", "").split(";")]
    if len(matches) != 1:
        raise ValueError("Task 8C runner manifest must bind exactly one case")
    runner_row = matches[0]
    expected_runner_sha = runner_row.get("recorded_runner_sha256")
    available = runner_row.get("matching_source_script_available") == "True"
    if runner_row.get("source_execution_id") != record["execution_id"] or runner_row.get("source_group_id") != binding["source_group_id"]:
        raise ValueError("Task 8C runner provenance scope mismatch")
    if expected_runner_sha != binding["recorded_runner_sha256"]:
        raise ValueError("Task 8C recorded runner hash does not match its provenance manifest")
    if binding["runner_status"] != ("VERIFIED" if available else "UNVERIFIED"):
        raise ValueError("Task 8C runner status disagrees with the provenance manifest")
    if binding["runner_status"] == "VERIFIED":
        if runner_row.get("script_path_if_available") != binding["runner_source"]["path"] or expected_runner_sha != binding["runner_source"]["sha256"]:
            raise ValueError("Task 8C runner file is not the case-bound runner")
    elif binding["runner_source"] is not None:
        raise ValueError("Task 8C unavailable runner provenance was fabricated")
    return row


def verify_task8c_artifacts(record, root, checked, trusted_manifest_hashes, trusted_artifact_hashes, trusted_runner_hashes):
    validate_task8c_record(record)
    if record["task8c_binding"]["source_manifest"]["sha256"] not in trusted_manifest_hashes:
        raise ValueError("Task 8C source manifest is not authorized by registry trust configuration")
    for artifact in (record["source"], record["task8c_binding"]["source_manifest"],
                     record["native_binding"]["simulator_xml"], record["native_binding"]["mapping"],
                     *record["source_files"].values()):
        _verify_artifact(artifact, root, checked)
    expected_artifacts = {"simulator_xml": record["native_binding"]["simulator_xml"]["sha256"],
        "mapping": record["native_binding"]["mapping"]["sha256"],
        **{name: artifact["sha256"] for name, artifact in record["source_files"].items()}}
    if any(trusted_artifact_hashes.get(name) != digest for name, digest in expected_artifacts.items()):
        raise ValueError("Task 8C model/config artifact is not authorized by registry trust configuration")
    runner = record["task8c_binding"]["runner_source"]
    if record["task8c_binding"]["runner_status"] == "VERIFIED":
        if runner is None or runner["sha256"] not in trusted_runner_hashes:
            raise ValueError("verified Task 8C runner is not authorized by registry trust configuration")
        _verify_artifact(runner, root, checked)
    elif runner is not None:
        raise ValueError("unverified Task 8C runner cannot have a trusted source binding")
    runner_bindings = record["task8c_binding"]["runner_bindings"]
    if trusted_artifact_hashes.get("runner_bindings") != runner_bindings["sha256"]:
        raise ValueError("Task 8C runner binding manifest is not authorized")
    _verify_artifact(runner_bindings, root, checked)
    _source_manifest_row(record, root, checked, trusted_manifest_hashes)


def verify_task8c_record(record, root, trusted_manifest_hashes, trusted_artifact_hashes, trusted_runner_hashes):
    checked = {}
    verify_task8c_artifacts(record, root, checked, trusted_manifest_hashes, trusted_artifact_hashes, trusted_runner_hashes)
    runner = record["task8c_binding"]["runner_source"]
    manifest_row = _source_manifest_row(record, root, checked, trusted_manifest_hashes)

    xml_path = record["native_binding"]["simulator_xml"]["path"]
    map_path = record["native_binding"]["mapping"]["path"]
    physical_path = record["source_files"]["physical_config"]["path"]
    checker_path = record["source_files"]["checker_config"]["path"]
    inventory_path = record["source_files"]["entity_inventory"]["path"]
    geometry_index = load(map_path)
    physical_config = load(physical_path)
    checker_config = load(checker_path)
    entity_inventory = load(inventory_path)
    execution_id = record["execution_id"]
    task_id = record["task_id"]
    expected_task = execution_id.split("_freshreset_", 1)[0]
    if task_id != expected_task:
        raise ValueError("Task 8C task identity does not match the manifest execution identifier")
    case_binding = {
        "case_id": record["task8c_binding"]["case_id"],
        "source_execution_id": execution_id,
        "source_group_id": record["task8c_binding"]["source_group_id"],
        "recording_sha256": record["trajectory_sha256"],
        "runner_sha256": runner["sha256"] if runner else "0" * 64,
        "runner_source_path": runner["path"] if runner else None,
        "source_provenance_status": record["task8c_binding"]["runner_status"],
        "xml_sha256": record["native_binding"]["simulator_xml"]["sha256"],
    }
    task8c_adapter.prepare_case(
        record["source"]["path"], xml_path, case_binding, geometry_index, physical_config,
        checker_config, entity_inventory,
        diagnostic_unverified=record["task8c_binding"]["runner_status"] != "VERIFIED",
    )
    body_id = record["native_binding"]["body_id"]
    geometry_ids = record["native_binding"]["collision_geom_ids"]
    if body_id != 22 or geometry_ids != [104] or record["object_id"] != "cream_cheese_1":
        raise ValueError("Task 8C native binding is outside the frozen protected-object mapping")
    with h5py.File(record["source"]["path"], "r") as source:
        obs_frames = source["observations/source_frame"]
        obs_times = source["observations/time"]
        times = source["physics/time_after"]
        positions = source["physics/body_xpos"]
        quaternions = source["physics/body_xquat"]
        for item in record["saved_frames"]:
            frame, sample = item["frame"], item["native_sample_index"]
            if int(obs_frames[frame]) != frame or not math.isclose(float(obs_times[frame]), item["simulator_time_seconds"], rel_tol=0, abs_tol=1e-8):
                raise ValueError("Task 8C saved-frame timestamp or index mismatch")
            if not math.isclose(float(times[sample]), item["simulator_time_seconds"], rel_tol=0, abs_tol=1e-8):
                raise ValueError("Task 8C native-sample timestamp mismatch")
            if record["measurement_type"] in ("object_pose", "native_geometry"):
                if positions.shape[1:] != (29, 3) or quaternions.shape[1:] != (29, 4):
                    raise ValueError("Task 8C body-state shape mismatch")
                if not all(math.isfinite(float(x)) for x in positions[sample, body_id]) or not all(math.isfinite(float(x)) for x in quaternions[sample, body_id]):
                    raise ValueError("Task 8C protected-object pose is nonfinite")
            elif record["measurement_type"] == "contact":
                sample_ids = source["contacts/sample_index"]
                count = int(source["physics/ncon"][sample])
                actual = int((sample_ids[()] == sample).sum())
                if actual != count:
                    raise ValueError("Task 8C cited contact set is incomplete for the native sample")
            elif record["measurement_type"] == "timestamp":
                if not math.isfinite(float(obs_times[frame])):
                    raise ValueError("Task 8C timestamp is nonfinite")
    return manifest_row


class Task8CRegistryV3Adapter:
    """Build source-bound 2.1 measurement records; no Checker or labels used."""

    def __init__(self, *, source_root, source_manifest, runner_binding_manifest, trusted_manifest_hashes,
                 simulator_xml, native_mapping, physical_config, checker_config, entity_inventory):
        self.root = Path(source_root).resolve(strict=True)
        self.artifacts = {
            "source_manifest": _file_binding(source_manifest),
            "runner_bindings": _file_binding(runner_binding_manifest),
            "simulator_xml": _file_binding(simulator_xml),
            "mapping": _file_binding(native_mapping),
            "physical_config": _file_binding(physical_config),
            "checker_config": _file_binding(checker_config),
            "entity_inventory": _file_binding(entity_inventory),
        }
        self.trusted_manifest_hashes = frozenset(trusted_manifest_hashes)
        if self.artifacts["source_manifest"]["sha256"] not in self.trusted_manifest_hashes:
            raise ValueError("source manifest hash must be explicitly trusted")

    def build_records(self, *, case_id, recording_path, runner_status, runner_source=None, frames=None):
        from evaluation.r1_v4.evidence_registry_gsn.registry_v3 import make_record

        requested_recording = Path(recording_path)
        if requested_recording.is_symlink() or requested_recording.resolve(strict=True) != requested_recording:
            raise ValueError("Task 8C recording must be a regular source file without symlinks")
        recording = requested_recording
        if not recording.is_relative_to(self.root):
            raise ValueError("Task 8C recording must be within the approved source root")
        manifest_path = self.artifacts["source_manifest"]["path"]
        with Path(manifest_path).open(newline="", encoding="utf-8-sig") as stream:
            matching = [row for row in csv.DictReader(stream) if row.get("blinded_case_id") == case_id]
        if len(matching) != 1:
            raise ValueError("Task 8C case ID must resolve to exactly one manifest row")
        row = matching[0]
        if Path(row["raw_hdf5_path"]).resolve(strict=True) != recording:
            raise ValueError("requested recording path does not match its manifest row")
        recording_sha = _sha256(recording)
        if recording_sha != row["raw_hdf5_sha256"]:
            raise ValueError("Task 8C recording SHA-256 mismatch")
        runner_bindings_path = self.artifacts["runner_bindings"]["path"]
        with Path(runner_bindings_path).open(newline="", encoding="utf-8-sig") as stream:
            runner_rows = list(csv.DictReader(stream))
        runner_matches = [item for item in runner_rows if case_id in item.get("case_ids", "").split(";")]
        if len(runner_matches) != 1:
            raise ValueError("Task 8C runner manifest must bind exactly one case")
        runner_row = runner_matches[0]
        runner_available = runner_row.get("matching_source_script_available") == "True"
        if (runner_row.get("source_execution_id") != row["new_execution_id"] or
            runner_row.get("source_group_id") != row["coordinator_group_id"] or
            runner_status != ("VERIFIED" if runner_available else "UNVERIFIED")):
            raise ValueError("requested runner status does not match the case-bound provenance manifest")
        runner_file = _file_binding(runner_source) if runner_source is not None else None
        if runner_status == "VERIFIED" and runner_file is None:
            raise ValueError("verified runner requires its exact source file")
        if runner_status == "UNVERIFIED" and runner_file is not None:
            raise ValueError("unverified runner cannot have a trusted source binding")
        if runner_available:
            if (runner_row.get("script_path_if_available") != runner_file["path"] or
                runner_row.get("recorded_runner_sha256") != runner_file["sha256"]):
                raise ValueError("runner source does not match the case-bound provenance manifest")
        elif runner_row.get("script_path_if_available", "") or not runner_row.get("recorded_runner_sha256"):
            raise ValueError("unavailable runner record must preserve its recorded hash and missing path")
        native = {**self.artifacts["simulator_xml"], "path": self.artifacts["simulator_xml"]["path"]}
        map_binding = self.artifacts["mapping"]
        geometry = load(map_binding["path"])
        physical = load(self.artifacts["physical_config"]["path"])
        checker = load(self.artifacts["checker_config"]["path"])
        inventory = load(self.artifacts["entity_inventory"]["path"])
        case_binding = {
            "case_id": case_id, "source_execution_id": row["new_execution_id"],
            "source_group_id": row["coordinator_group_id"], "recording_sha256": recording_sha,
            "runner_sha256": runner_row["recorded_runner_sha256"],
            "runner_source_path": runner_file["path"] if runner_file else None,
            "source_provenance_status": runner_status, "xml_sha256": row["xml_sha256"],
        }
        prepared = task8c_adapter.prepare_case(
            recording, native["path"], case_binding, geometry, physical, checker, inventory,
            diagnostic_unverified=runner_status != "VERIFIED",
        )
        frames = list(range(10, 258)) if frames is None else list(frames)
        if not frames or frames != sorted(set(frames)) or any(type(frame) is not int or not 10 <= frame <= 257 for frame in frames):
            raise ValueError("requested Task 8C frames must be ordered, unique, and within 10..257")
        execution_id = row["new_execution_id"]
        task_id = execution_id.split("_freshreset_", 1)[0]
        common = {
            "schema_version": TASK8C_RECORD_SCHEMA_VERSION,
            "requirement_id": "R1", "requirement_version": R1_V3,
            "execution_id": execution_id, "task_id": task_id, "object_id": "cream_cheese_1",
            "kind": "raw_measurement", "validation_status": "verified_source",
            "source": {"path": str(recording), "sha256": recording_sha},
            "trajectory_sha256": recording_sha,
            "source_schema": {"format": "task8c_custom_hdf5", "version": TASK8C_LAYOUT_VERSION,
                              "adapter_version": task8c_adapter.ADAPTER_VERSION},
            "domain": "frame", "clock": "saved_frame_index", "interval": [frames[0], frames[-1]],
            "coverage_status": "complete" if frames == list(range(frames[0], frames[-1] + 1)) else "partial",
            "saved_frames": [{"frame": f, "native_sample_index": f * TASK8C_STRIDE,
                              "simulator_time_seconds": float(prepared["frames"][f]["time"]),
                              "selectors": []} for f in frames],
            "native_binding": {"body_id": 22, "collision_geom_ids": [104],
                               "simulator_xml": native, "mapping": map_binding},
            "task8c_binding": {"case_id": case_id, "source_group_id": row["coordinator_group_id"],
                                "source_manifest": self.artifacts["source_manifest"],
                                "runner_bindings": self.artifacts["runner_bindings"],
                                "recorded_runner_sha256": runner_row["recorded_runner_sha256"],
                                "runner_status": runner_status, "runner_source": runner_file,
                                "task_id_source": "manifest_execution_id_prefix"},
            "source_files": {key: self.artifacts[key] for key in ("physical_config", "checker_config", "entity_inventory")},
            "development_only": True,
            "limitations": ["Task 8C controlled development cohort; never independent holdout.",
                            "No policy-execution failure or policy trajectory is represented.",
                            "No contact force is interpreted as load-bearing support."],
        }
        definitions = {
            "object_pose": (TASK8C_SELECTORS["object_pose"], "direct_source_measurement",
                            ["Recorded body pose; no sensor uncertainty is reported."]),
            "native_geometry": (TASK8C_SELECTORS["native_geometry"], "reconstructed_from_recorded_body_pose_and_xml",
                                ["Geometry reconstructed using bound XML local transforms and frozen box-corner arithmetic; not a direct HDF5 geom_xpos channel."]),
            "contact": (TASK8C_SELECTORS["contact"], "direct_source_measurement",
                        ["Contact rows are observed contacts, not a validated load-bearing force measurement."]),
            "timestamp": (TASK8C_SELECTORS["timestamp"], "direct_source_measurement",
                          ["Native/observation times are recorded; uncertainty between saved frames remains unknown."]),
        }
        records = []
        for measurement, (selectors, derivation, uncertainty) in definitions.items():
            payload = {**common, "measurement_type": measurement, "derivation": derivation,
                       "uncertainty": uncertainty,
                       "saved_frames": [{**frame, "selectors": list(selectors)} for frame in common["saved_frames"]]}
            records.append(make_record(payload))
        return records
