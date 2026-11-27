"""Synthetic RegistryV3 source-schema v2.1 tests for Task 8C HDF5."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import h5py

TASK8C_DIR = Path(__file__).resolve().parents[2] / "task8c_r1v3_adapter"
sys.path.insert(0, str(TASK8C_DIR))
sys.path.insert(0, str(TASK8C_DIR / "tests"))
from test_task8c_adapter import fixture_geometry, write_h5

from evaluation.r1_v4.evidence_registry_gsn.registry_v3 import RegistryV3, make_record, validate_record
from evaluation.r1_v4.evidence_registry_gsn.registry_v3_task8c import (
    TASK8C_RECORD_SCHEMA_VERSION, Task8CRegistryV3Adapter,
)
from evaluation.r1_v4.checker_v3_admission.admission import PHYSICAL_GATES, _evidence_ledger
from evaluation.r1_v4.provenance import canonical
from evaluation.r1_v4.task8c_r1v3_adapter import task8c_adapter


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True) + "\n")


class Task8CRegistryV3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.path = self.root / "case.h5"
        self.xml = self.root / "simulator.xml"
        self.map_path = self.root / "native-map.json"
        self.physical_path = self.root / "physical.json"
        self.checker_path = self.root / "checker.json"
        self.inventory_path = self.root / "inventory.json"
        self.manifest_path = self.root / "manifest.csv"
        self.runner_manifest_path = self.root / "runner-bindings.csv"
        self.runner_path = self.root / "runner.py"
        self.database = self.root / "registry.sqlite"
        self.old_xml_sha = task8c_adapter.EXPECTED_XML_SHA256
        self.xml.write_text('<mujoco><worldbody><body name="cream_cheese_1_main"/></worldbody></mujoco>')
        self.xml_sha = sha(self.xml)
        task8c_adapter.EXPECTED_XML_SHA256 = self.xml_sha

        self.geometry = fixture_geometry()
        target = deepcopy(self.geometry["geometries"][1])
        target["native_geom_id"] = 104
        self.geometry["geometries"][104] = target
        self.geometry["geometries"][1].update(owner_body_id=0, owner_body="world", body_ancestry=["world"], collision_capable=False)
        self.geometry["source_xml_sha256"] = self.xml_sha
        dump(self.map_path, self.geometry)
        self.physical = dict(table_geom_ids=[10], floor_geom_ids=[8], gripper_left_ids=[76], gripper_right_ids=[79])
        self.checker = dict(objects=["cream_cheese_1"], arithmetic_eps_multiplier=512,
                            start_frame=10, sample_period_s=.05, time_arithmetic_allowance_s=1e-8)
        self.inventory = {"schema_version":"corrected-entity-inventory-v2","records":[
            {"source_xml_sha256":self.xml_sha,"entities":[
                {"name":"cream_cheese_1","root_body_name":"cream_cheese_1_main","body_id":22,"native_geom_ids":[104]}]}]}
        dump(self.physical_path, self.physical)
        dump(self.checker_path, self.checker)
        dump(self.inventory_path, self.inventory)
        self.runner_path.write_text("frozen synthetic capture source")
        write_h5(self.path)
        with h5py.File(self.path, "r+") as h:
            h["contacts/geom2"][:] = 104
        self.execution = "libero_long_openvla_oft_task00_freshreset_seedfixture_task8c_v1"
        self.group = "group_fixture"
        self.case_id = "case_fixture"
        with self.manifest_path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["blinded_case_id", "new_execution_id", "coordinator_group_id", "raw_hdf5_sha256", "raw_hdf5_path", "xml_sha256"])
            writer.writeheader()
            writer.writerow({"blinded_case_id":self.case_id,"new_execution_id":self.execution,"coordinator_group_id":self.group,
                             "raw_hdf5_sha256":sha(self.path),"raw_hdf5_path":str(self.path),"xml_sha256":self.xml_sha})
        self.manifest_sha = sha(self.manifest_path)
        with self.runner_manifest_path.open("w", newline="") as stream:
            fields = ["source_execution_id", "source_group_id", "case_ids", "recorded_runner_sha256", "matching_source_script_available", "script_path_if_available"]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"source_execution_id":self.execution,"source_group_id":self.group,"case_ids":self.case_id,
                             "recorded_runner_sha256":sha(self.runner_path),"matching_source_script_available":"True",
                             "script_path_if_available":str(self.runner_path)})
        self.trusted_artifacts = {
            "simulator_xml": self.xml_sha, "mapping": sha(self.map_path),
            "physical_config": sha(self.physical_path), "checker_config": sha(self.checker_path),
            "entity_inventory": sha(self.inventory_path),
            "runner_bindings": sha(self.runner_manifest_path),
        }
        self.runner_sha = sha(self.runner_path)
        self.adapter = Task8CRegistryV3Adapter(
            source_root=self.root, source_manifest=self.manifest_path, runner_binding_manifest=self.runner_manifest_path,
            trusted_manifest_hashes={self.manifest_sha}, simulator_xml=self.xml,
            native_mapping=self.map_path, physical_config=self.physical_path,
            checker_config=self.checker_path, entity_inventory=self.inventory_path,
        )
        self.registry = RegistryV3(
            self.database, source_root=self.root, create=True,
            trusted_task8c_manifest_hashes={self.manifest_sha},
            trusted_task8c_artifact_hashes=self.trusted_artifacts,
            trusted_task8c_runner_hashes={self.runner_sha},
        )
        self.addCleanup(self.registry.close)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(setattr, task8c_adapter, "EXPECTED_XML_SHA256", self.old_xml_sha)

    def records(self, frames=None, runner_status="VERIFIED", runner_source=None):
        if runner_source is None and runner_status == "VERIFIED":
            runner_source = self.runner_path
        return self.adapter.build_records(case_id=self.case_id, recording_path=self.path,
                                          runner_status=runner_status, runner_source=runner_source, frames=frames)

    def resolve(self, record, **changes):
        scope = dict(execution_id=record["execution_id"],
            task_id=record["task_id"], object_id=record["object_id"], trajectory_sha256=record["trajectory_sha256"],
            measurement_type=record["measurement_type"], frames=[10])
        scope.update(changes)
        return self.registry.resolve_citation(record["id"], **scope)

    def test_valid_registration_resolution_and_development_flag(self):
        records = self.records()
        self.assertEqual({r["schema_version"] for r in records}, {TASK8C_RECORD_SCHEMA_VERSION})
        self.assertEqual({r["measurement_type"] for r in records}, {"object_pose", "native_geometry", "contact", "timestamp"})
        self.registry.add(records)
        resolved = self.resolve(next(r for r in records if r["measurement_type"] == "object_pose"))
        self.assertEqual(resolved["native_binding"]["body_id"], 22)
        self.assertTrue(resolved["development_only"])
        self.assertEqual(resolved["saved_frames"][0]["native_sample_index"], 250)
        self.assertEqual(resolved["saved_frames"][0]["simulator_time_seconds"], .5)

    def test_partial_scope_is_explicit_and_missing_initial_support_cannot_resolve(self):
        record = next(r for r in self.records(frames=[11, 12]) if r["measurement_type"] == "contact")
        self.assertEqual(record["coverage_status"], "complete")
        self.assertEqual(record["interval"], [11, 12])
        self.registry.add([record])
        with self.assertRaisesRegex(ValueError, "explicitly recorded saved frames"):
            self.resolve(record)

    def test_partial_frame_set_cannot_claim_complete_coverage(self):
        record = next(r for r in self.records(frames=[10, 12]) if r["measurement_type"] == "timestamp")
        self.assertEqual(record["coverage_status"], "partial")
        body = {k:v for k,v in record.items() if k != "id"}
        body["coverage_status"] = "complete"
        with self.assertRaisesRegex(ValueError, "coverage status"):
            make_record(body)

    def test_backward_compatible_standard_registry_record(self):
        # The original RegistryV3 2.0 tests remain the compatibility oracle; a
        # 2.1 record can coexist in the same immutable SQLite registry.
        records = self.records(frames=[10])
        self.registry.add(records)
        self.assertEqual(len(self.registry.records()), 4)
        self.assertEqual(self.registry.export()["schema_version"], "2.0.0")

    def test_untrusted_manifest_and_model_artifacts_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "contact")
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "registry.sqlite"
            registry = RegistryV3(db, source_root=self.root, create=True)
            try:
                with self.assertRaisesRegex(ValueError, "manifest is not authorized"):
                    registry.add([record])
            finally:
                registry.close()
        registry = RegistryV3(self.root / "registry2.sqlite", source_root=self.root, create=True,
            trusted_task8c_manifest_hashes={self.manifest_sha}, trusted_task8c_artifact_hashes={},
            trusted_task8c_runner_hashes={self.runner_sha})
        try:
            with self.assertRaisesRegex(ValueError, "not authorized by registry trust configuration"):
                registry.add([record])
        finally:
            registry.close()

    def test_incorrect_recording_hash_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "object_pose")
        body = {k:v for k,v in record.items() if k != "id"}
        body["source"] = {**body["source"], "sha256":"0"*64}
        body["trajectory_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "recording SHA-256 mismatch|artifact hash mismatch"):
            self.registry.add([make_record(body)])

    def test_unsupported_record_schema_version_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "object_pose")
        body = {k:v for k,v in record.items() if k != "id"}
        body["schema_version"] = "2.2.0"
        with self.assertRaises(ValueError):
            make_record(body)

    def test_missing_file_and_invalid_selector_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "timestamp")
        body = {k:v for k,v in record.items() if k != "id"}
        body["source"] = {**body["source"], "path":str(self.root/"absent.h5")}
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.registry.add([make_record(body)])
        body = {k:v for k,v in record.items() if k != "id"}
        body["saved_frames"] = [{**f, "selectors":["/actions/policy_trajectory"]} for f in body["saved_frames"]]
        with self.assertRaisesRegex(ValueError, "selector set"):
            make_record(body)

    def test_object_model_body_and_scope_mismatches_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "object_pose")
        self.registry.add([record])
        with self.assertRaisesRegex(ValueError, "scope mismatch"):
            self.resolve(record, object_id="butter_1")
        with self.assertRaisesRegex(ValueError, "scope mismatch"):
            self.resolve(record, execution_id="other-execution")
        body = {k:v for k,v in record.items() if k != "id"}
        body["native_binding"] = {**body["native_binding"], "body_id":21}
        with self.assertRaisesRegex(ValueError, "native binding"):
            self.registry.add([make_record(body)])

    def test_timestamp_and_native_sample_mismatch_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "timestamp")
        body = {k:v for k,v in record.items() if k != "id"}
        body["saved_frames"] = [{**body["saved_frames"][0], "simulator_time_seconds":.6}]
        with self.assertRaisesRegex(ValueError, "timestamp or index mismatch"):
            self.registry.add([make_record(body)])
        body = {k:v for k,v in record.items() if k != "id"}
        body["saved_frames"] = [{**body["saved_frames"][0], "native_sample_index":251}]
        with self.assertRaisesRegex(ValueError, "sample mapping"):
            make_record(body)

    def test_missing_contact_channel_and_missing_boundary_support_are_not_filled(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "contact")
        with h5py.File(self.path, "r+") as source:
            del source["contacts/geom1"]
        with self.assertRaises((KeyError, ValueError)):
            self.registry.add([record])

    def test_missing_temporal_frame_cannot_be_cited(self):
        record = next(r for r in self.records(frames=[10, 11, 13]) if r["measurement_type"] == "object_pose")
        self.registry.add([record])
        with self.assertRaisesRegex(ValueError, "explicitly recorded saved frames"):
            self.resolve(record, frames=[12])

    def test_unverified_runner_may_be_stored_diagnostically_but_not_cited(self):
        with self.runner_manifest_path.open("w", newline="") as stream:
            fields = ["source_execution_id", "source_group_id", "case_ids", "recorded_runner_sha256", "matching_source_script_available", "script_path_if_available"]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"source_execution_id":self.execution,"source_group_id":self.group,"case_ids":self.case_id,
                             "recorded_runner_sha256":"e"*64,
                             "matching_source_script_available":"False","script_path_if_available":""})
        runner_bindings_sha = sha(self.runner_manifest_path)
        self.adapter.artifacts["runner_bindings"] = {"path":str(self.runner_manifest_path),"sha256":runner_bindings_sha}
        self.registry.trusted_task8c_artifact_hashes["runner_bindings"] = runner_bindings_sha
        records = self.records(frames=[10], runner_status="UNVERIFIED", runner_source=None)
        self.registry.add(records)
        with self.assertRaisesRegex(ValueError, "lacks verified capture-runner provenance"):
            self.resolve(next(r for r in records if r["measurement_type"] == "contact"))

    def test_unrecognized_measurement_or_human_judgment_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "contact")
        for field, value in (("measurement_type", "human_judgment"), ("kind", "derived_checker_event"),
                             ("development_only", False)):
            body = {k:v for k,v in record.items() if k != "id"}
            body[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                make_record(body)

    def test_valid_development_citation_remains_blocked_by_admission_ledger(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "object_pose")
        self.registry.add([record])
        citation = {"record_id":record["id"],"measurement_type":"object_pose","frames":[10]}
        scope = {key:record[key] for key in ("execution_id","task_id","object_id","trajectory_sha256")}
        ledger = _evidence_ledger([citation], self.registry, scope, [10, 257])
        self.assertEqual(ledger[0]["status"], "blocked")
        self.assertEqual(ledger[0]["diagnostic"], "development_only_source")
        self.assertEqual(len(PHYSICAL_GATES), 9)

    def test_fabricated_native_contact_binding_is_rejected(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "contact")
        with h5py.File(self.path, "r+") as source:
            source["contacts/body2"][0] = 21
        with self.assertRaises((ValueError, IndexError)):
            self.registry.add([record])

    def test_schema_rejects_checker_events_and_claimed_physical_outcomes(self):
        record = next(r for r in self.records(frames=[10]) if r["measurement_type"] == "object_pose")
        for field, value in (("measurement_type", "checker_event"), ("kind", "derived_checker_event"),
                             ("outcome", "violation_observed"), ("development_only", False)):
            body = {k:v for k,v in record.items() if k != "id"}
            body[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                make_record(body)


if __name__ == "__main__":
    unittest.main()
