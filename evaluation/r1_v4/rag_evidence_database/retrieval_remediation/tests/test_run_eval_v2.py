"""Synthetic-only tests for resumable planner-v2 actual-retrieval replay."""
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.run_eval_v2 import (
    file_sha256, run,
)


class FakeRetriever:
    def __init__(self, catalogue, catalogue_hash, store=None, responses=None):
        self.responses = responses or {}
        self.calls = []
    def retrieve(self, request, mode="bundle"):
        self.calls.append(request.query)
        value = self.responses.get(request.query)
        if isinstance(value, Exception): raise value
        return value
    def close(self): pass


def response(family="raw.robot0_joint_pos", value=None, execution="exec-A", frame=2,
             status="AVAILABLE", claimed="COMPLETE WITHIN VERIFIED CONTRACT"):
    item = {"execution_id": execution, "task_id": "task-A", "variant_id": "variant-A",
            "integrity_status": "verified_source",
            "source_artifact": {"path": "/source/trajectory.h5", "sha256": "source-hash"},
            "family": family, "samples": [{"saved_frame_index": frame, "value": value if value is not None else [1.0],
                         "dtype": "float64", "source_selector": "/frames/000002/value"}]}
    plan = {"families": [family], "status": "RESOLVED", "obligation_plan_status": "COMPLETE",
            "query_interpretation_status": "RESOLVED", "measurement_obligations": [{"family": family}],
            "temporal_obligations": [], "unresolved_obligations": []}
    return {"interpretation": plan, "resolved_scope": {"execution_id": execution, "task_id": "task-A", "variant_id": "variant-A"},
            "requested_families": [family], "groups": [{"family": family, "status": status, "items": [item]}],
            "completeness_status": claimed, "retrieval_completeness_status": claimed,
            "obligation_plan_status": "COMPLETE", "query_interpretation_status": "RESOLVED"}


class ReplayHarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.srcroot = self.root / "sources"; self.srcroot.mkdir()
        self.source = self.srcroot / "trajectory.h5"; self.source.write_bytes(b"fixture")
        self.inputs = {}
        for name, content in (("db", b"db-fixture"), ("catalogue", b"catalogue-fixture"), ("encoder", b"encoder-fixture")):
            path = self.root / name; path.write_bytes(content); self.inputs[name] = path
        self.ref = self.root / "references.jsonl"
        self.rows = [self.row("CASE-A", "joint positions at frame 2", ["raw.robot0_joint_pos"],
                              {"raw.robot0_joint_pos": [{"frame": 2, "value": [1.0], "dtype": "float64", "selector": "/frames/000002/value"}]})]
        self.write_refs()
        self.out = self.root / "out"

    def tearDown(self): self.tmp.cleanup()

    def row(self, case, query, families, samples=None):
        return {"id": case, "query": query, "request": {"execution_id": "exec-A", "task_id": "task-A", "variant_id": "variant-A"},
                "expected_families": families, "reference_samples": samples or {},
                "source_artifacts": [{"path": str(self.source), "sha256": "source-hash"}]}

    def write_refs(self): self.ref.write_text("".join(json.dumps(r) + "\n" for r in self.rows))

    def execute(self, fake, cases=None):
        for value in getattr(fake, "responses", {}).values():
            if isinstance(value, dict):
                for group in value.get("groups", []):
                    for item in group.get("items", []):
                        item.setdefault("source_artifact", {})["path"] = str(self.source)
        hashes = {name + "_sha256": file_sha256(path) for name, path in self.inputs.items()}
        return run(database=self.inputs["db"], database_sha256=hashes["db_sha256"],
                   catalogue=self.inputs["catalogue"], catalogue_sha256=hashes["catalogue_sha256"],
                   source_root=self.srcroot, encoder=self.inputs["encoder"], encoder_sha256=hashes["encoder_sha256"],
                   encoder_revision="synthetic-encoder-v1", references=self.ref, references_sha256=file_sha256(self.ref),
                   output=self.out, case_ids=cases,
                   retriever_factory=lambda c, h, store=None: fake)

    def test_complete_retrieval_and_aggregate(self):
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: response()})
        result = self.execute(fake)
        record = json.loads((self.out / "case-CASE-A.json").read_text())
        self.assertEqual(result["retrieval_complete_verified"], 1)
        self.assertTrue(record["planner_complete"])
        self.assertTrue(record["retrieval_complete"])
        self.assertEqual(record["physical_evidence_eligibility"], "NOT_EVALUATED")
        self.assertEqual(result["expected_family_obligations"], 1)
        self.assertEqual(result["available_expected_family_obligations"], 1)

    def test_missing_family_and_false_complete(self):
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: response(status="UNAVAILABLE")})
        result = self.execute(fake)
        record = json.loads((self.out / "case-CASE-A.json").read_text())
        self.assertEqual(result["false_complete"], 1)
        self.assertEqual(record["missing_expected_families"], ["raw.robot0_joint_pos"])

    def test_partial_retrieval_and_out_of_scope_frame_are_not_complete(self):
        self.rows[0]["reference_frame_indices"] = [2]
        self.write_refs()
        bad = response(frame=3, status="PARTIAL", claimed="PARTIAL")
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: bad})
        result = self.execute(fake)
        record = json.loads((self.out / "case-CASE-A.json").read_text())
        self.assertFalse(record["retrieval_complete"])
        self.assertIn("sample_outside_reference_scope", record["citation_or_reference_errors"])
        self.assertEqual(result["partial_retrieval_responses"], 1)

    def test_recorded_time_frame_and_timestamp_are_checked_against_reference(self):
        row = self.rows[0]
        row["expected_families"] = ["raw.robot0_joint_pos", "recorded_time"]
        row["reference_frame_indices"] = [2]
        row["reference_metadata"] = {"recorded_time": {"simulator_endpoint_seconds": 2.1, "wall_ns": 2100, "sensor_clock": False}}
        self.write_refs()
        result = response()
        result["requested_families"].append("recorded_time")
        result["groups"].append({"family": "recorded_time", "status": "AVAILABLE", "items": [{
            "execution_id": "exec-A", "task_id": "task-A", "variant_id": "variant-A", "family": "recorded_time",
            "integrity_status": "verified_source", "source_artifact": {"path": str(self.source), "sha256": "source-hash"},
            "value": {"saved_frame_index": 2, "simulator_endpoint_seconds": 2.1,
                      "recorder_host_wall_ns": 2100, "synchronized_physical_instant": False}}]})
        result["interpretation"]["families"].append("recorded_time")
        fake = FakeRetriever("", "", responses={row["query"]: result})
        summary = self.execute(fake)
        self.assertEqual(summary["retrieval_complete_verified"], 1)
        # A timestamp mismatch cannot be hidden behind a complete retrieval label.
        self.out = self.root / "out-bad-timestamp"
        result["groups"][1]["items"][0]["value"]["simulator_endpoint_seconds"] = 99.0
        fake = FakeRetriever("", "", responses={row["query"]: result})
        summary = self.execute(fake)
        self.assertEqual(summary["false_complete"], 1)

    def test_missing_source_artifact_is_recorded_as_retrieval_unavailable(self):
        missing = response(status="UNAVAILABLE", claimed="UNAVAILABLE")
        missing["groups"][0]["items"] = []
        missing["groups"][0]["reason"] = "source artifact unavailable"
        missing["completeness_status"] = "UNAVAILABLE"
        missing["retrieval_completeness_status"] = "UNAVAILABLE"
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: missing})
        result = self.execute(fake)
        record = json.loads((self.out / "case-CASE-A.json").read_text())
        self.assertEqual(record["retrieval_status"], "UNAVAILABLE")
        self.assertEqual(result["abstentions"], 1)
        self.assertEqual(record["physical_evidence_eligibility"], "NOT_EVALUATED")

    def test_wrong_values_scope_and_citation_are_detected(self):
        samples = {"raw.robot0_joint_pos": [{"frame": 2, "value": [1.0], "dtype": "float64", "selector": "/frames/000002/value"}]}
        self.rows[0]["reference_samples"] = samples; self.write_refs()
        bad = response(value=[9.0], execution="other-exec")
        bad["groups"][0]["items"][0]["integrity_status"] = "unverified"
        bad["groups"][0]["items"][0]["source_artifact"]["sha256"] = "wrong-source-hash"
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: bad})
        self.execute(fake)
        record = json.loads((self.out / "case-CASE-A.json").read_text())
        self.assertIn("scope:execution_id", record["citation_or_reference_errors"])
        self.assertIn("citation_integrity", record["citation_or_reference_errors"])
        self.assertIn("citation_source_not_bound_to_reference", record["citation_or_reference_errors"])
        self.assertIn("value_frame_or_selector_mismatch", record["citation_or_reference_errors"])

    def test_ambiguous_and_unsupported_are_recorded(self):
        for status in ("AMBIGUOUS", "UNSUPPORTED"):
            with self.subTest(status=status):
                self.out = self.root / ("out-" + status)
                plan = {"status": status, "obligation_plan_status": "INCOMPLETE", "query_interpretation_status": status,
                        "families": [], "measurement_obligations": [], "temporal_obligations": [],
                        "unresolved_obligations": [{"status": status}]}
                resp = {"interpretation": plan, "groups": [], "requested_families": [],
                        "completeness_status": status, "retrieval_completeness_status": "NOT_RUN",
                        "obligation_plan_status": "INCOMPLETE", "query_interpretation_status": status}
                fake = FakeRetriever("", "", responses={self.rows[0]["query"]: resp})
                result = self.execute(fake)
                record = json.loads((self.out / "case-CASE-A.json").read_text())
                self.assertEqual(result["retrieval_complete_verified"], 0)
                self.assertEqual(record["ambiguity"], status == "AMBIGUOUS")
                self.assertTrue(record["abstention"])

    def test_execution_and_database_errors_are_retained(self):
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: RuntimeError("synthetic DB failure")})
        result = self.execute(fake)
        self.assertEqual(result["execution_errors"], 1)
        record = json.loads((self.out / "case-CASE-A.json").read_text())
        self.assertEqual(record["retrieval_status"], "EXECUTION_ERROR")

    def test_database_initialization_failure_records_attempts(self):
        hashes = {name + "_sha256": file_sha256(path) for name, path in self.inputs.items()}
        def fail_init(*args, **kwargs): raise OSError("synthetic database open failure")
        result = run(database=self.inputs["db"], database_sha256=hashes["db_sha256"],
                     catalogue=self.inputs["catalogue"], catalogue_sha256=hashes["catalogue_sha256"],
                     source_root=self.srcroot, encoder=self.inputs["encoder"], encoder_sha256=hashes["encoder_sha256"],
                     encoder_revision="synthetic-encoder-v1", references=self.ref, references_sha256=file_sha256(self.ref),
                     output=self.out, retriever_factory=fail_init)
        self.assertEqual(result["execution_errors"], 1)
        self.assertIn("database open failure", json.loads((self.out / "case-CASE-A.json").read_text())["execution_error"]["message"])

    def test_resume_skips_completed_cases_without_duplicate_attempts(self):
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: response()})
        self.execute(fake)
        calls_after_first = len(fake.calls)
        self.execute(fake)
        self.assertEqual(len(fake.calls), calls_after_first)
        per_case = json.loads((self.out / "PER_CASE.json").read_text())
        self.assertEqual(len(per_case), 1)

    def test_resume_after_interruption_and_configuration_mismatch(self):
        self.rows.append(self.row("CASE-B", "query B", ["raw.robot0_joint_pos"]))
        self.write_refs()
        fake = FakeRetriever("", "", responses={self.rows[0]["query"]: response(), self.rows[1]["query"]: response()})
        # The fake's second call interrupts the process after CASE-A was committed.
        class Interrupting(FakeRetriever):
            def retrieve(inner, request, mode="bundle"):
                if len(inner.calls) == 1: raise KeyboardInterrupt()
                return super(Interrupting, inner).retrieve(request, mode)
        interrupted = Interrupting("", "", responses=fake.responses)
        with self.assertRaises(KeyboardInterrupt): self.execute(interrupted)
        self.execute(fake)
        self.assertTrue((self.out / "case-CASE-A.json").exists())
        self.assertTrue((self.out / "case-CASE-B.json").exists())
        self.assertEqual(len(json.loads((self.out / "PER_CASE.json").read_text())), 2)
        changed = self.inputs["encoder"]; changed.write_bytes(b"different encoder")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch|resume rejected"):
            self.execute(fake)

    def test_duplicate_case_ids_and_out_of_root_sources_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate case IDs"):
            self.rows.append(dict(self.rows[0])); self.write_refs(); self.execute(FakeRetriever("", ""))
        self.rows = [self.row("CASE-C", "query C", ["raw.robot0_joint_pos"])]
        self.rows[0]["source_artifacts"][0]["path"] = "/outside/source.h5"; self.write_refs()
        self.out = self.root / "out-source"
        with self.assertRaisesRegex(ValueError, "outside declared source root"):
            self.execute(FakeRetriever("", ""))


if __name__ == "__main__": unittest.main()
