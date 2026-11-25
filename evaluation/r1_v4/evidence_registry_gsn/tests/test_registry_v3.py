"""CPU tests for the R1 v3 registry using synthetic source bytes."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import h5py

from evaluation.r1_v4.evidence_registry_gsn.registry_v3 import (
    R1_V3,
    RegistryV3,
    make_record,
    validate_record,
)
from evaluation.r1_v4.provenance import canonical


def file_binding(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class RegistryV3Tests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.trajectory = self.root / "trajectory.h5"
        with h5py.File(self.trajectory, "w") as trajectory:
            trajectory.attrs["global_episode_id"] = "synthetic-execution"
            trajectory.attrs["task_configuration_id"] = "synthetic-task"
            for frame in (10, 12):
                simulator = trajectory.create_group(f"frames/{frame:06d}/simulator")
                simulator["body_xpos/value"] = [[0.0, 0.0, 1.0], [0.1, 0.0, 1.0]]
                simulator["geom_xpos/value"] = [[0.0, 0.0, 1.0], [0.1, 0.0, 1.0]]
                simulator["time/value"] = frame / 20
                simulator["ncon/value"] = 0
                simulator.create_group("contacts").attrs["json"] = "[]"
        self.simulator_xml = self.root / "simulator.xml"
        self.simulator_xml.write_text(
            '<mujoco><worldbody><body name="cream_cheese_1_main"/>'
            '<body name="butter_1_main"/></worldbody></mujoco>'
        )
        self.native_map = self.root / "native-map.json"
        self.native_map.write_text(json.dumps({
            "schema_version": "native-geometry-index-v2",
            "body_names": ["cream_cheese_1_main", "butter_1_main"],
            "native_geom_count": 2,
            "geometries": [
                {"native_geom_id": 0, "name": "cheese_collision", "owner_body_id": 0, "collision_capable": True},
                {"native_geom_id": 1, "name": "butter_collision", "owner_body_id": 1, "collision_capable": True},
            ],
            "source_xml_sha256": file_binding(self.simulator_xml)["sha256"],
            "validated_run_ids": ["synthetic-execution"],
        }))
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({
            "checker_version": "r1-evidence-v3.0.0",
            "requirement_id": "R1",
            "requirement_version": R1_V3,
            "objects": ["cream_cheese_1", "butter_1"],
        }))
        self.predictions = self.root / "predictions.json"
        identity = {
            "run_id": "synthetic-execution",
            "canonical_object_id": "cream_cheese_1",
            "requirement_version": R1_V3,
        }
        self.predictions.write_text(json.dumps([{
            **identity,
            "requirement_id": "R1",
            "checker_version": "r1-evidence-v3.0.0",
            "recording_sha256": file_binding(self.trajectory)["sha256"],
            "configuration_sha256": file_binding(self.config)["sha256"],
            "events": [{**identity, "event_id": "synthetic:event", "interval": [10, 12]}],
        }]))
        self.database = self.root / "registry.sqlite"
        self.registry = RegistryV3(self.database, source_root=self.root, create=True)
        self.addCleanup(self.registry.close)

    def measurement(self, frames=(10, 12), measurement_type="object_pose"):
        source = file_binding(self.trajectory)
        selector = {
            "object_pose": "body_xpos/value",
            "native_geometry": "geom_xpos/value",
            "contact": "contacts",
        }[measurement_type]
        payload = {
            "schema_version": "2.0.0",
            "requirement_id": "R1",
            "requirement_version": R1_V3,
            "execution_id": "synthetic-execution",
            "task_id": "synthetic-task",
            "object_id": "cream_cheese_1",
            "kind": "raw_measurement",
            "measurement_type": measurement_type,
            "validation_status": "verified_source",
            "source": source,
            "trajectory_sha256": source["sha256"],
            "domain": "frame",
            "clock": "saved_frame_index",
            "interval": [frames[0], frames[-1]],
            "saved_frames": [
                {
                    "frame": frame,
                    "selectors": [f"/frames/{frame:06d}/simulator/{selector}"],
                    "simulator_time_seconds": frame / 20,
                }
                for frame in frames
            ],
            "uncertainty": ["Recorded endpoints only."],
            "limitations": ["Synthetic source for a registry test."],
        }
        if measurement_type == "object_pose":
            payload["native_binding"] = self.native_binding()
        return payload

    def event(self, inputs, frames=(10, 12)):
        payload = self.measurement(frames)
        del payload["native_binding"]
        payload.update(
            kind="derived_checker_event",
            measurement_type="checker_event",
            validation_status="provisional",
            source=file_binding(self.predictions),
            saved_frames=[{"frame": frame} for frame in frames],
            checker={
                "version": "r1-evidence-v3.0.0",
                "config": file_binding(self.config),
                "event_id": "synthetic:event",
                "selector": "/0/events/0",
                "input_record_ids": [record["id"] for record in inputs],
            },
        )
        return payload

    def native_binding(self):
        return {
            "body_id": 0,
            "collision_geom_ids": [0],
            "pose_phase": "native_last_forward_cache_uncalibrated_phase",
            "simulator_xml": file_binding(self.simulator_xml),
            "mapping": {**file_binding(self.native_map), "selector": "/geometries"},
        }

    def resolve(self, record, *, registry=None, **changes):
        scope = {
            field: record[field]
            for field in ("execution_id", "task_id", "object_id", "trajectory_sha256", "measurement_type")
        }
        scope["frames"] = [10]
        scope.update(changes)
        registry = self.registry if registry is None else registry
        return registry.resolve_citation(record["id"], **scope)

    def test_reopen_preserves_citation_and_unadmitted_status(self):
        record = make_record(self.measurement())
        self.registry.add([record])
        reopened = RegistryV3(self.database, source_root=self.root)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.records(), [record])
        self.assertEqual(self.resolve(record, registry=reopened), record)
        exported = reopened.export()
        self.assertEqual(exported["requirement_id"], "R1")
        self.assertEqual(exported["requirement_version"], R1_V3)
        self.assertEqual(exported["records"], [record])
        self.assertIs(exported["empirical_admission_enabled"], False)

    def test_citation_requires_exact_scope_and_recorded_frames(self):
        record = make_record(self.measurement())
        self.registry.add([record])
        self.assertEqual(self.resolve(record, frames=[10, 12]), record)
        for bad_scope in (
            {"execution_id": "other-execution"},
            {"object_id": "butter_1"},
            {"task_id": "other-task"},
            {"trajectory_sha256": "0" * 64},
            {"measurement_type": "contact"},
            {"frames": [10, 11, 12]},
            {"frames": [13]},
        ):
            with self.subTest(scope=bad_scope), self.assertRaises(ValueError):
                self.resolve(record, **bad_scope)

    def test_rejects_version_and_selector_mismatch(self):
        payload = self.measurement()
        with self.assertRaises(ValueError):
            make_record({**payload, "requirement_version": "2.0.0"})
        payload["saved_frames"][0]["selectors"] = ["/frames/000011/simulator/body_xpos/value"]
        with self.assertRaises(ValueError):
            make_record(payload)

    def test_rejects_record_tampering(self):
        record = make_record(self.measurement())
        changed = deepcopy(record)
        changed["limitations"].append("Post-export edit")
        with self.assertRaises(ValueError):
            validate_record(changed)

    def test_rejects_missing_hdf5_selector_and_wrong_recorded_time(self):
        absent = self.measurement()
        absent["saved_frames"][0]["selectors"] = ["/frames/000010/simulator/body_xquat/value"]
        mistimed = self.measurement()
        mistimed["saved_frames"][0]["simulator_time_seconds"] = 1.0
        for payload in (absent, mistimed):
            with self.subTest(payload=payload["saved_frames"][0]), self.assertRaises(ValueError):
                self.registry.add([make_record(payload)])

    def test_rejects_trajectory_scope_mismatch_and_indirect_link(self):
        with self.assertRaisesRegex(ValueError, "trajectory execution or task"):
            self.registry.add([make_record({**self.measurement(), "task_id": "different-task"})])
        with h5py.File(self.trajectory, "r+") as trajectory:
            trajectory["frames/000010/simulator/body_xquat"] = h5py.SoftLink(
                "/frames/000012/simulator/body_xpos"
            )
        payload = self.measurement()
        payload["saved_frames"][0]["selectors"] = ["/frames/000010/simulator/body_xquat/value"]
        with self.assertRaisesRegex(ValueError, "indirect trajectory selector"):
            self.registry.add([make_record(payload)])

    def test_native_pose_requires_the_recorded_row_shape(self):
        with h5py.File(self.trajectory, "r+") as trajectory:
            poses = trajectory["frames/000010/simulator/body_xpos"]
            del poses["value"]
            poses["value"] = [[0.0], [0.1]]
        with self.assertRaisesRegex(ValueError, "valid rows for the cited native IDs"):
            self.registry.add([make_record(self.measurement())])

    def test_rejects_wrong_digest_and_rechecks_changed_source(self):
        payload = self.measurement()
        record = make_record(payload)
        asserted_digest = "0" * 64
        wrong = make_record({
            **payload,
            "source": {**payload["source"], "sha256": asserted_digest},
            "trajectory_sha256": asserted_digest,
        })
        with self.assertRaises(ValueError):
            self.registry.add([wrong])
        self.registry.add([record])
        self.trajectory.write_bytes(b"changed after registration")
        with self.assertRaises(ValueError):
            self.resolve(record)

    def test_evaluation_only_reference_is_excluded(self):
        reference = self.root / "HUMAN_REFERENCE_EVALUATION_ONLY.json"
        reference.write_bytes(b"synthetic excluded file")
        source = file_binding(reference)
        record = make_record({
            **self.measurement(),
            "source": source,
            "trajectory_sha256": source["sha256"],
        })
        with self.assertRaises(ValueError):
            self.registry.add([record])
        self.assertEqual(self.registry.records(), [])

    def test_geometry_and_contact_preserve_verified_native_mapping(self):
        binding = self.native_binding()
        for measurement_type in ("native_geometry", "contact"):
            with self.subTest(measurement_type=measurement_type):
                payload = self.measurement(measurement_type=measurement_type)
                with self.assertRaises(ValueError):
                    make_record(payload)
                record = make_record({**payload, "native_binding": binding})
                self.registry.add([record])
                self.assertEqual(self.resolve(record)["native_binding"], binding)
                wrong_owner = make_record({
                    **payload,
                    "native_binding": {**binding, "collision_geom_ids": [1]},
                })
                with self.assertRaisesRegex(ValueError, "ownership mismatch"):
                    self.registry.add([wrong_owner])
        self.native_map.write_bytes(b"changed native map")
        with self.assertRaises(ValueError):
            self.resolve(record)

    def test_accepts_wrapped_native_profile_used_by_task5_pipeline(self):
        profile = {
            "mapping": json.loads(self.native_map.read_text()),
            "objects": {"cream_cheese_1": {"body_id": 0, "collision_geom_ids": [0]}},
        }
        self.native_map.write_text(json.dumps(profile))
        binding = self.native_binding()
        binding["mapping"]["selector"] = "/mapping/geometries"
        record = make_record({**self.measurement(), "native_binding": binding})
        self.registry.add([record])
        self.assertEqual(self.resolve(record), record)

    def test_rejects_map_from_different_simulator_xml(self):
        unrelated = json.loads(self.native_map.read_text())
        unrelated["source_xml_sha256"] = "1" * 64
        self.native_map.write_text(json.dumps(unrelated))
        with self.assertRaisesRegex(ValueError, "geometry identity mismatch"):
            self.registry.add([make_record(self.measurement())])

    def test_rejects_map_with_wrong_recorded_geometry_count(self):
        short_map = json.loads(self.native_map.read_text())
        short_map["geometries"].pop()
        short_map["native_geom_count"] = 1
        self.native_map.write_text(json.dumps(short_map))
        with self.assertRaisesRegex(ValueError, "geometry identity mismatch"):
            self.registry.add([make_record(self.measurement())])

    def test_citation_rejects_simulator_xml_changed_after_registration(self):
        record = make_record(self.measurement())
        self.registry.add([record])
        with self.simulator_xml.open("a") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            self.resolve(record)

    def test_reopened_registry_checks_source_selector_before_citing(self):
        payload = self.measurement()
        payload["saved_frames"][0]["selectors"] = ["/frames/000010/simulator/body_xquat/value"]
        record = make_record(payload)
        with self.registry.db:
            self.registry.db.execute(
                "INSERT INTO evidence VALUES (?,?,?,?,?,?,?)",
                (
                    record["id"], record["requirement_id"], record["requirement_version"],
                    record["execution_id"], record["object_id"], record["kind"],
                    canonical(record).decode(),
                ),
            )
        reopened = RegistryV3(self.database, source_root=self.root)
        self.addCleanup(reopened.close)
        with self.assertRaisesRegex(ValueError, "missing or indirect trajectory selector"):
            self.resolve(record, registry=reopened)

    def test_contact_count_cannot_stand_in_for_contact_group(self):
        payload = self.measurement(measurement_type="contact")
        payload["saved_frames"][0]["selectors"] = ["/frames/000010/simulator/ncon/value"]
        payload["native_binding"] = self.native_binding()
        with self.assertRaisesRegex(ValueError, "measurement type"):
            make_record(payload)

    def test_missing_serialized_contacts_leave_batch_empty(self):
        with h5py.File(self.trajectory, "r+") as trajectory:
            del trajectory["frames/000010/simulator/contacts"].attrs["json"]
        pose = make_record(self.measurement())
        contacts = make_record({
            **self.measurement(measurement_type="contact"),
            "native_binding": self.native_binding(),
        })
        with self.assertRaisesRegex(ValueError, "missing or invalid serialized contact data"):
            self.registry.add([pose, contacts])
        self.assertEqual(self.registry.records(), [])

    def test_contact_group_requires_actual_native_pairs_and_matching_count(self):
        with h5py.File(self.trajectory, "r+") as trajectory:
            simulator = trajectory["frames/000010/simulator"]
            simulator["ncon/value"][()] = 1
            simulator["contacts"].attrs["json"] = '["not a contact"]'
        with self.assertRaisesRegex(ValueError, "native pair data"):
            self.registry.add([make_record({
                **self.measurement(frames=(10,), measurement_type="contact"),
                "native_binding": self.native_binding(),
            })])

        pair = {"geom1": 0, "geom2": 1, "dist": -0.001, "pos": [0.0, 0.0, 0.2]}
        with h5py.File(self.trajectory, "r+") as trajectory:
            simulator = trajectory["frames/000010/simulator"]
            simulator["contacts"].attrs["json"] = json.dumps([pair])
        contact = make_record({
            **self.measurement(frames=(10,), measurement_type="contact"),
            "native_binding": self.native_binding(),
        })
        self.registry.add([contact])
        self.assertEqual(self.resolve(contact), contact)

        with h5py.File(self.trajectory, "r+") as trajectory:
            trajectory["frames/000010/simulator/ncon/value"][()] = 0
        with self.assertRaisesRegex(ValueError, "contact count"):
            self.registry.add([make_record({
                **self.measurement(frames=(10,), measurement_type="contact"),
                "native_binding": self.native_binding(),
            })])

    def test_derived_event_preserves_lineage_and_is_not_citable(self):
        raw = make_record(self.measurement())
        event = make_record(self.event([raw]))
        self.registry.add([raw, event])
        stored = {record["id"]: record for record in self.registry.records()}
        self.assertEqual(stored[event["id"]], event)
        self.assertEqual(stored[event["id"]]["checker"]["input_record_ids"], [raw["id"]])
        with self.assertRaises(ValueError):
            self.resolve(event)

    def test_derived_event_rejects_out_of_scope_and_incomplete_inputs(self):
        other_object = make_record({
            **self.measurement(),
            "object_id": "butter_1",
            "native_binding": {**self.native_binding(), "body_id": 1, "collision_geom_ids": [1]},
        })
        missing_frame = make_record(self.measurement(frames=(10,)))
        self.registry.add([other_object, missing_frame])
        for record in (other_object, missing_frame):
            with self.subTest(record=record["id"]), self.assertRaises(ValueError):
                self.registry.add([make_record(self.event([record]))])

    def test_object_pose_requires_matching_native_body(self):
        payload = self.measurement()
        del payload["native_binding"]
        with self.assertRaises(ValueError):
            make_record(payload)
        wrong_body = make_record({**self.measurement(), "object_id": "butter_1"})
        with self.assertRaisesRegex(ValueError, "ownership mismatch"):
            self.registry.add([wrong_body])

    def test_measurement_families_reject_unrelated_selectors(self):
        for measurement_type in ("camera_reference", "robot_state", "recorded_state"):
            with self.subTest(measurement_type=measurement_type), self.assertRaisesRegex(
                ValueError, "selector does not match"
            ):
                make_record({**self.measurement(), "measurement_type": measurement_type})

    def test_derived_event_checks_config_bytes(self):
        raw = make_record(self.measurement())
        event = make_record(self.event([raw]))
        self.registry.add([raw])
        self.config.write_bytes(b"changed checker configuration")
        with self.assertRaises(ValueError):
            self.registry.add([event])

    def test_derived_event_requires_real_prediction_selector_identity_and_interval(self):
        raw = make_record(self.measurement())
        self.registry.add([raw])
        base = self.event([raw])
        for changes, diagnostic in (
            ({"checker": {**base["checker"], "selector": "/0/events/3"}}, "does not resolve"),
            ({"checker": {**base["checker"], "event_id": "unrecorded"}}, "identity or interval"),
            ({"interval": [9, 12]}, "identity or interval"),
        ):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, diagnostic):
                self.registry.add([make_record({**base, **changes})])

    def test_derived_event_rejects_correctly_hashed_wrong_prediction_scope(self):
        raw = make_record(self.measurement())
        self.registry.add([raw])
        original = json.loads(self.predictions.read_text())
        for field, wrong in (
            ("configuration_sha256", "0" * 64),
            ("recording_sha256", "0" * 64),
            ("canonical_object_id", "butter_1"),
        ):
            predictions = [{**original[0], field: wrong}]
            self.predictions.write_text(json.dumps(predictions))
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "prediction scope"):
                self.registry.add([make_record(self.event([raw]))])
