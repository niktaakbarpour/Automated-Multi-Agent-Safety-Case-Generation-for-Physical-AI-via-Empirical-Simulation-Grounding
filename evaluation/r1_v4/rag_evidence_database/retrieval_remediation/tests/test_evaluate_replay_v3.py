"""Regression tests for conservative offline retrieval adjudication v3."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.evaluate_replay_v3 import (
    _source_bind,
    _validate_family,
    canonical_sha,
    classify_case,
)


class OfflineAdjudicationV3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_claimed_complete_with_no_frozen_family_contract_is_unverifiable(self):
        record = {
            "case_id": "CASE",
            "claimed_complete": True,
            "retrieval_status": "COMPLETE WITHIN VERIFIED CONTRACT",
            "response": {"groups": []},
            "groups": [],
            "record_sha256": "",
        }
        record["record_sha256"] = canonical_sha({k: v for k, v in record.items() if k != "record_sha256"})
        result = classify_case(
            {"id": "CASE", "expected_families": [], "request": {}, "source_artifacts": []},
            record, {}, self.root, "dbhash", {},
        )
        self.assertEqual(result["assessment"], "claimed_complete_unverifiable")
        self.assertNotEqual(result["assessment"], "confirmed_false_complete")

    def test_missing_reference_coverage_does_not_confirm_retrieval_failure(self):
        source = self.root / "trajectory.h5"
        source.write_bytes(b"fixture")
        sha = hashlib.sha256(source.read_bytes()).hexdigest()
        row = {
            "id": "CASE",
            "expected_families": ["unreferenced_family"],
            "request": {"execution_id": "ex", "task_id": "task", "variant_id": "variant"},
            "source_artifacts": [{"path": str(source), "sha256": sha}],
            "reference_samples": {},
            "reference_metadata": {},
        }
        item = {
            "family": "unreferenced_family",
            "execution_id": "ex", "task_id": "task", "variant_id": "variant",
            "source_artifact": {"path": str(source), "sha256": sha},
        }
        record = {
            "case_id": "CASE",
            "claimed_complete": True,
            "retrieval_status": "COMPLETE WITHIN VERIFIED CONTRACT",
            "response": {"groups": [{"family": "unreferenced_family", "status": "AVAILABLE", "items": [item]}]},
            "groups": [{"family": "unreferenced_family", "status": "AVAILABLE", "items": [item]}],
            "record_sha256": "",
        }
        record["record_sha256"] = canonical_sha({k: v for k, v in record.items() if k != "record_sha256"})
        result = classify_case(row, record, {}, self.root, "dbhash", {})
        self.assertEqual(result["assessment"], "claimed_complete_unverifiable")
        self.assertEqual(result["family_findings"]["unreferenced_family"]["status"], "unverifiable")

    def test_catalogue_bound_alternative_metadata_source_is_verified(self):
        path = self.root / "run_metadata.json"
        projection = {
            "source_commit": "abc",
            "versions": {"numpy": "1.0"},
            "python": "3.12.16",
            "platform": "linux",
            "checkpoint_revision": "rev",
            "checkpoint_weight_sha256": {},
            "control_frequency_hz": 20,
            "settling_steps": 10,
            "historical_running_binary_attested": False,
        }
        original = {k: v for k, v in projection.items() if k != "historical_running_binary_attested"}
        path.write_text(json.dumps(original))
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        row = {
            "request": {"execution_id": "ex", "task_id": "task", "variant_id": "variant"},
            "source_artifacts": [],
        }
        item = {
            "family": "execution_metadata",
            "source_artifact": {"path": str(path), "sha256": sha, "selector": "/"},
            "value": projection,
        }
        catalogue = {"ex": {"metadata_path": str(path), "metadata_sha256": sha}}
        self.assertEqual(
            _source_bind(row, item, "execution_metadata", catalogue, self.root, "dbhash", {}),
            (True, "catalogue_metadata_anchor"),
        )

    def test_recorded_time_range_uses_matching_anchor_not_one_scalar_for_every_frame(self):
        path = self.root / "trajectory.h5"
        with h5py.File(path, "w") as h5:
            for frame, seconds, wall in ((7, 0.7, 700), (8, 0.8, 800)):
                group = h5.create_group(f"frames/{frame:06d}")
                group.attrs["wall_time_ns"] = wall
                group.attrs["monotonic_ns"] = wall + 1
                group.attrs["utc"] = f"t{frame}"
                group.create_dataset("simulator/time/value", data=seconds)
        items = []
        for frame, seconds, wall in ((7, 0.7, 700), (8, 0.8, 800)):
            items.append({
                "source_artifact": {"path": str(path), "selector": f"/frames/{frame:06d}"},
                "value": {
                    "saved_frame_index": frame,
                    "simulator_endpoint_seconds": seconds,
                    "recorder_host_wall_ns": wall,
                    "recorder_host_monotonic_ns": wall + 1,
                    "recorder_utc": f"t{frame}",
                    "synchronized_physical_instant": False,
                },
            })
        row = {
            "reference_metadata": {"recorded_time": {
                "simulator_endpoint_seconds": 0.8, "wall_ns": 800, "sensor_clock": False,
            }}
        }
        self.assertEqual(
            _validate_family("recorded_time", items, row, [(True, "frozen_source_pair")]*2, "dbhash")[0],
            "verified",
        )

    def test_main_table_reference_field_aliases_are_typed(self):
        row = {"reference_metadata": {"main_table_identity": {
            "supported": True, "body": "table", "geom": "table_collision",
        }}}
        item = {"value": {"body_name": "table", "geom_name": "table_collision"}}
        self.assertEqual(
            _validate_family("main_table_identity", [item], row, [(True, "catalogue")], "dbhash")[0],
            "verified",
        )
        item["value"]["geom_name"] = "different_geom"
        self.assertEqual(
            _validate_family("main_table_identity", [item], row, [(True, "catalogue")], "dbhash")[0],
            "confirmed_error",
        )

    def test_action_metadata_requires_expected_selector_and_attributes(self):
        row = {"reference_metadata": {"action_metadata": {
            "selector": "/policy_steps/000003",
            "attributes": {"step": 3, "triggered_inference": False},
        }}}
        path = self.root / "trajectory.h5"
        with h5py.File(path, "w") as h5:
            h5.create_group("policy_steps/000003").attrs.update(
                {"step": 3, "triggered_inference": False}
            )
        item = {
            "source_artifact": {"path": str(path), "selector": "/policy_steps/000003"},
            "value": {"policy_step": 3, "policy_attributes": {"step": 3, "triggered_inference": False}},
        }
        self.assertEqual(_validate_family("action_metadata", [item], row, [], "dbhash")[0], "verified")
        item["value"]["policy_attributes"]["step"] = 4
        self.assertEqual(_validate_family("action_metadata", [item], row, [], "dbhash")[0], "confirmed_error")

    def test_unsupported_reference_type_stays_unverifiable(self):
        self.assertEqual(
            _validate_family("future_metadata_family", [{"value": {}}], {}, [], "dbhash")[0],
            "unverifiable",
        )


if __name__ == "__main__":
    unittest.main()
