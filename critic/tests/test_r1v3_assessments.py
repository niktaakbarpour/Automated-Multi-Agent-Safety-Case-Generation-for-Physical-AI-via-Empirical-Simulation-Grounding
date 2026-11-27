"""CPU checks of the Critic boundary with Task 2's synthetic source artifacts."""

from copy import deepcopy
from io import BytesIO
import unittest
from unittest.mock import patch

from critic.critic import review
from critic.r1v3_assessments import validate_checker_inputs
from drafter.generation import generate_argument
from drafter.llm import FrozenLocalModelConfig
from drafter.r1v3_profile import INSUFFICIENT, PACKAGE_SCHEMA, build_configuration, build_request
from drafter.tests.test_generation import reply
from drafter.tests.test_llm import MODEL, configuration
from drafter.tests.test_r1v3_generation import model_plan
from evaluation.r1_v4.checker_v3_admission.admission import NEGATIVE
from evaluation.r1_v4.checker_v3_admission.tests import test_admission
from evaluation.r1_v4.provenance import canonical, digest
from integration.handoff import build_critic_request


class CheckerAssessmentInputsTests(unittest.TestCase):
    def setUp(self):
        fixture = test_admission.AdmissionTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.fixture = fixture
        self.admission_request = fixture.request(outcome="violation")
        self.trusted = fixture.approve(self.admission_request)
        self.runtime = {"source_root": fixture.root, "registry": fixture.registry, "task_id": fixture.task_id}
        self.drafter_request = self._draft_request()

    def _draft_request(self):
        config = build_configuration()
        request = self.admission_request
        scope = request["scope"]
        roster = config["protected_objects"]
        version = request["requirement_version"]
        checker = self.fixture.checker
        database = test_admission.binding(self.fixture.registry.path)
        package = {
            "schema": PACKAGE_SCHEMA,
            "execution": {
                "execution_id": scope["execution_id"],
                "trajectory_sha256": scope["trajectory_sha256"],
                "trajectory_path_hestia": str(self.fixture.trajectory),
                "source_identity_status": "synthetic test fixture",
                "monitoring_interval_saved_frames_inclusive": scope["frame_interval"],
                "requirement_id": request["requirement_id"],
                "requirement_version": version,
                "protected_objects": roster,
            },
            "rag_source": {
                "database_path": database["path"],
                "database_sha256": database["sha256"],
                "source_commit": checker["source_commit"],
                "retrieval_api": "synthetic fixture registry",
                "queried_interval": scope["frame_interval"],
                "indexed_requirement_version": version,
                "record_types_included": [],
                "record_count_included": 0,
                "records": [],
                "citation_status": {},
                "coverage_queries": [],
            },
            "checker_assessment": {
                "status": "synthetic development context",
                "checker_version": checker["version"],
                "config_sha256": checker["configuration_sha256"],
                "predictions_sha256": request["prediction"]["artifact"]["sha256"],
                "seal_sha256": request["prediction"]["seal"]["sha256"],
                "reference_answers_loaded": False,
                "object_assessments": [
                    {"object_id": obj, "requirement_version": version, "checker_version": checker["version"],
                     "classification": "insufficient_information", "applicability": "insufficient_information"}
                    for obj in roster
                ],
            },
            "coverage_and_limitations": ["Synthetic source fixture."],
        }
        return build_request(package, request_id="synthetic-critic-review", test_fixture=True)

    def _pair(self, trusted=()):
        return {
            "request": self.admission_request,
            "assessment": self.fixture.run_assessment(self.admission_request, trusted),
        }

    def _verify(self, pair, trusted=(), **overrides):
        return validate_checker_inputs(
            self.drafter_request, [pair], trusted_review_hashes=trusted, **(self.runtime | overrides),
        )

    def test_admitted_violation_retains_witness_and_provenance(self):
        pair = self._pair(self.trusted)
        [verified] = self._verify(pair, self.trusted)
        self.assertEqual(verified, pair["assessment"])
        self.assertEqual(verified["admission_status"], "admitted")
        self.assertEqual(verified["conclusion"]["outcome"], "violation")
        self.assertEqual(verified["conclusion"]["witness_event"]["selector"], "/0/events/0")
        self.assertEqual(verified["review"]["sha256"], self.trusted[0])
        self.assertEqual({gate["status"] for gate in verified["gate_ledger"]}, {"verified"})
        self.assertFalse(verified["coverage"]["continuous_time_coverage"])
        self.assertTrue(self.drafter_request["test_fixture"])

    def _generation_report(self):
        plan = model_plan(self.drafter_request)
        for graph in plan["graphs"]:
            for node in graph["nodes"]:
                if node["type"] == "context":
                    node["statement"] = "The synthetic review covers saved frames 10 through 13."
        config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))
        with patch("drafter.llm.build_opener") as opener:
            opener.return_value.open.side_effect = [
                BytesIO(canonical({"data": [{"id": MODEL}]})),
                BytesIO(canonical(reply(plan).raw_response)),
            ]
            run = generate_argument(self.drafter_request, config)
        self.assertEqual(run["status"], "accepted", run["diagnostics"])
        return run

    def test_admitted_witness_survives_public_handoff_and_critic_review(self):
        run = self._generation_report()
        conclusion = run["argument"]["argument_bundle"]["execution_conclusion"]
        self.assertEqual(conclusion["claimed_outcome"], INSUFFICIENT)

        pair = self._pair(self.trusted)
        request, sidecar = build_critic_request(self.drafter_request, run, checker_assessments=[pair])
        request_bytes = canonical(request)
        report = review(request, trusted_review_hashes=self.trusted, **self.runtime)
        self.assertEqual(report["review_status"], "completed", report["status_detail"])
        self.assertTrue(report["test_fixture"])
        self.assertFalse(report["llm"]["called"])
        self.assertFalse(report["safety_claim_verified"])
        self.assertEqual(report["checker_admission"], [pair["assessment"]])
        self.assertEqual(report["provenance"]["critic_request_sha256"], sidecar["critic_request_sha256"])
        [witness] = [finding for finding in report["criticisms"] if finding["category"] == "C07"]
        self.assertEqual(witness["object_id"], self.fixture.object_id)
        self.assertEqual(witness["evidence_ids"], [pair["assessment"]["assessment_hash"]])
        self.assertEqual(report["summary"]["claimed_execution_outcome"], INSUFFICIENT)
        self.assertEqual(report["summary"]["accepted_execution_outcome"], INSUFFICIENT)
        self.assertEqual(report["summary"]["recomputed_execution_outcome"], "violation")
        self.assertEqual(canonical(request), request_bytes)

        rejected = review(request, **self.runtime)
        self.assertEqual(rejected["review_status"], "rejected_invalid_input")
        self.assertFalse(rejected["llm"]["called"])
        self.assertEqual(rejected["checker_admission"], [])
        self.assertFalse(any(finding["category"] == "C07" for finding in rejected["criticisms"]))

    def test_review_preserves_admitted_negative_scope(self):
        self.admission_request = self.fixture.request(outcome=NEGATIVE)
        self.trusted = self.fixture.approve(self.admission_request)
        self.drafter_request = self._draft_request()
        pair = self._pair(self.trusted)
        request, _ = build_critic_request(self.drafter_request, self._generation_report(), checker_assessments=[pair])
        report = review(request, trusted_review_hashes=self.trusted, **self.runtime)

        self.assertEqual(report["review_status"], "completed", report["status_detail"])
        [assessment] = report["checker_admission"]
        self.assertEqual(assessment["conclusion"]["outcome"], NEGATIVE)
        self.assertEqual(assessment["coverage"]["checker_reported_negative_intervals"], [[10, 13]])
        self.assertFalse(assessment["coverage"]["continuous_time_coverage"])
        object_review = next(row for row in report["object_reviews"] if row["object_id"] == self.fixture.object_id)
        self.assertEqual(object_review["verified_checker_outcome"], NEGATIVE)
        self.assertEqual(report["summary"]["accepted_execution_outcome"], INSUFFICIENT)
        self.assertFalse(report["safety_claim_verified"])

    def test_review_hash_in_request_cannot_authorize_itself(self):
        admitted = self._pair(self.trusted)
        with self.assertRaisesRegex(ValueError, "failed independent verification"):
            self._verify(admitted)

        blocked = self._pair()
        [verified] = self._verify(blocked)
        self.assertEqual(verified["admission_status"], "not_admitted")
        self.assertIn("independent_review_not_authorized", verified["blockers"])
        self.assertIsNone(verified["conclusion"])

    def test_development_purpose_remains_blocked_with_host_trust(self):
        self.admission_request["purpose"] = "development_diagnostic"
        trusted = self.fixture.approve(self.admission_request)
        pair = self._pair(trusted)
        request, _ = build_critic_request(self.drafter_request, self._generation_report(), checker_assessments=[pair])
        report = review(request, trusted_review_hashes=trusted, **self.runtime)
        self.assertEqual(report["review_status"], "completed", report["status_detail"])
        [verified] = report["checker_admission"]
        self.assertIn("development_only_prediction", verified["blockers"])
        self.assertIsNone(verified["conclusion"])
        self.assertTrue(all(row["verified_checker_outcome"] is None for row in report["object_reviews"]))
        self.assertFalse(any(finding["category"] == "C07" for finding in report["criticisms"]))

    def test_foreign_scope_is_rejected_before_source_replay(self):
        pair = self._pair(self.trusted)
        with patch("critic.r1v3_assessments.require_admitted_assessment") as replay:
            for field, foreign in (
                ("execution_id", "another-execution"), ("object_id", "another-object"),
                ("task_id", "another-task"), ("trajectory_sha256", "0" * 64),
                ("clock", "action_index"), ("frame_interval", [10, 12]),
            ):
                for part in ("request", "assessment"):
                    with self.subTest(field=field, part=part):
                        changed = deepcopy(pair)
                        changed[part]["scope"][field] = foreign
                        with self.assertRaisesRegex(ValueError, "outside the declared review scope"):
                            self._verify(changed, self.trusted)
            replay.assert_not_called()

    def test_rehashed_witness_tamper_fails_independent_verification(self):
        pair = self._pair(self.trusted)
        forged = pair["assessment"]
        forged["conclusion"]["witness_event"]["selector"] = "/0/events/99"
        del forged["assessment_hash"]
        forged["assessment_hash"] = digest(forged)
        with self.assertRaisesRegex(ValueError, "failed independent verification"):
            self._verify(pair, self.trusted)

    def test_nonempty_pairs_require_verifier_settings(self):
        pair = self._pair(self.trusted)
        for field in self.runtime:
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "approved source root, registry and task"):
                    self._verify(pair, self.trusted, **{field: None})
        with self.assertRaisesRegex(ValueError, "approved source root, registry and task"):
            self._verify(pair, self.trusted, source_root="")
        self.assertEqual(validate_checker_inputs(self.drafter_request, []), [])
