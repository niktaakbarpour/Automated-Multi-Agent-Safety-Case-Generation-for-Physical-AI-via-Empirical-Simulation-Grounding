"""CPU policy tests; all stage-state examples here are synthetic, never model outputs."""
import tempfile
import unittest
import json
import hashlib
from pathlib import Path

from integration.orchestrator import (
    OrchestrationError,
    _atomic_new_or_identical,
    _validate_critic_report,
    run_fresh_generation,
    run_saved_task8a,
    stage_decisions,
)


class OrchestratorPolicyTests(unittest.TestCase):
    def test_synthetic_valid_critic_envelope_preserves_pending_review(self):
        report = {
            "schema_version": "critic-report/r1v3/0.1.0", "critic_version": "synthetic-test/0",
            "request_id": "r:critic", "execution_id": "synthetic", "test_fixture": True,
            "input_valid": True, "review_status": "completed", "llm": {}, "provenance": {},
            "criticisms": [], "checker_admission": [], "object_reviews": [
                {"object_id": "obj-a", "draft_outcome": "insufficient_information", "verified_checker_outcome": None},
            ], "drafter_evidence_gaps": [], "unresolved_concerns": [],
            "safety_claim_verified": False, "reasoning_review": {"status": "required"}, "summary": {},
        }
        self.assertTrue(_validate_critic_report(report, "r:critic", ["obj-a"]))

    def test_rejects_invalid_critic_version_or_id(self):
        report = {"schema_version": "wrong", "request_id": "wrong"}
        with self.assertRaises(OrchestrationError):
            _validate_critic_report(report, "r:critic", [])

    def test_rejects_safety_promotion(self):
        report = {
            "schema_version": "critic-report/r1v3/0.1.0", "critic_version": "test",
            "request_id": "r:critic", "execution_id": "x", "test_fixture": True,
            "input_valid": True, "review_status": "completed", "llm": {}, "provenance": {},
            "criticisms": [], "checker_admission": [], "object_reviews": [],
            "drafter_evidence_gaps": [], "unresolved_concerns": [], "safety_claim_verified": True,
            "reasoning_review": {"status": "required"}, "summary": {},
        }
        with self.assertRaisesRegex(OrchestrationError, "must_not_verify"):
            _validate_critic_report(report, "r:critic", [])

    def test_incomplete_plan_never_becomes_complete_or_physical(self):
        result = stage_decisions(checker_status="unavailable", admission_status="not_admitted",
                                 retrieval_plan_status="INCOMPLETE", retrieval_status="COMPLETE WITHIN VERIFIED CONTRACT",
                                 critic_status="completed", actionable_findings=[])
        self.assertEqual(result["drafter"], "blocked_incomplete_or_unavailable_retrieval")
        self.assertEqual(result["physical_claim_admission"], "unavailable_or_not_admitted")
        self.assertEqual(result["revision"], "skipped_no_actionable_finding")

    def test_missing_evidence_and_development_only_block_physical_admission(self):
        for checker, admission in (("unavailable", "not_admitted"), ("available", "development_only")):
            result = stage_decisions(checker_status=checker, admission_status=admission,
                                     retrieval_plan_status="COMPLETE", retrieval_status="PARTIAL",
                                     critic_status="completed", actionable_findings=[])
            self.assertEqual(result["physical_claim_admission"], "unavailable_or_not_admitted")

    def test_no_findings_do_not_trigger_revision(self):
        result = stage_decisions(checker_status="unavailable", admission_status="not_admitted",
                                 retrieval_plan_status="COMPLETE", retrieval_status="COMPLETE WITHIN VERIFIED CONTRACT",
                                 critic_status="completed", actionable_findings=[])
        self.assertEqual(result["revision"], "skipped_no_actionable_finding")
        self.assertEqual(result["final_safety_case"], "not_approved_human_reasoning_review_required")

    def test_actionable_finding_blocks_on_incompatible_revision_contract(self):
        result = stage_decisions(checker_status="unavailable", admission_status="not_admitted",
                                 retrieval_plan_status="COMPLETE", retrieval_status="COMPLETE WITHIN VERIFIED CONTRACT",
                                 critic_status="completed", actionable_findings=[{"blocking": True}],
                                 revision_contract_available=False)
        self.assertEqual(result["revision"], "blocked_contract_unavailable")
        self.assertEqual(result["second_critic"], "not_applicable")

    def test_successful_conditional_revision_requires_second_critic_acceptance(self):
        result = stage_decisions(checker_status="available", admission_status="admitted",
                                 retrieval_plan_status="COMPLETE", retrieval_status="COMPLETE WITHIN VERIFIED CONTRACT",
                                 critic_status="completed", actionable_findings=[{"blocking": True}],
                                 revision_contract_available=True, revision_status="accepted",
                                 second_critic_status="rejected")
        self.assertEqual(result["revision"], "completed")
        self.assertEqual(result["second_critic"], "rejected_or_unavailable")

    def test_revision_failure_and_second_critic_states_are_explicit(self):
        result = stage_decisions(checker_status="available", admission_status="admitted",
                                 retrieval_plan_status="COMPLETE", retrieval_status="COMPLETE WITHIN VERIFIED CONTRACT",
                                 critic_status="completed", actionable_findings=[{"blocking": True}],
                                 revision_contract_available=True, revision_status="failed")
        self.assertEqual(result["revision"], "failed")
        self.assertEqual(result["second_critic"], "not_applicable")

    def test_resume_is_not_final_approval_even_with_all_gate_labels(self):
        result = stage_decisions(checker_status="available", admission_status="admitted",
                                 retrieval_plan_status="COMPLETE", retrieval_status="COMPLETE WITHIN VERIFIED CONTRACT",
                                 critic_status="completed", actionable_findings=[])
        self.assertEqual(result["final_safety_case"], "not_approved_human_reasoning_review_required")

    def test_interrupted_artifact_write_is_idempotent_and_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            first = _atomic_new_or_identical(path, b'{"synthetic":true}\n')
            second = _atomic_new_or_identical(path, b'{"synthetic":true}\n')
            self.assertEqual(first, second)
            with self.assertRaisesRegex(OrchestrationError, "collision"):
                _atomic_new_or_identical(path, b'{"synthetic":false}\n')

    def test_model_mode_requires_explicit_authorization_before_any_call(self):
        with self.assertRaisesRegex(OrchestrationError, "not_authorized"):
            run_fresh_generation("/tmp", "absent.json", "absent-config.json", "/tmp/out", authorized=False)

    def test_genuine_saved_task8a_resumes_without_mutating_frozen_inputs(self):
        root = Path(__file__).resolve().parents[2]
        argument_path = root / "evaluation/m4_20261127/integration/task8a_r1v3/DRAFTER_ARGUMENT.json"
        original_hash = hashlib.sha256(argument_path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            run = run_saved_task8a(root=root, out_dir=Path(directory) / "run")
            manifest = run["manifest"]
            self.assertEqual(manifest["run_kind"], "resumed_saved_genuine_task8a_downstream_cpu")
            self.assertEqual(manifest["stages"]["critic_execution"]["status"], "completed_deterministic_cpu")
            self.assertEqual(manifest["stages"]["checker_execution"]["status"], "unavailable")
            self.assertEqual(manifest["final_status"], "draft_pending_reasoning_review_and_downstream_integration")
            report = json.loads((Path(directory) / "run/CRITIC_REPORT.json").read_text())
            self.assertEqual(len(report["object_reviews"]), 5)
            self.assertEqual(report["criticisms"], [])
            self.assertFalse(report["safety_claim_verified"])
            self.assertEqual(report["reasoning_review"]["status"], "required")
        self.assertEqual(hashlib.sha256(argument_path.read_bytes()).hexdigest(), original_hash)


if __name__ == "__main__":
    unittest.main()
