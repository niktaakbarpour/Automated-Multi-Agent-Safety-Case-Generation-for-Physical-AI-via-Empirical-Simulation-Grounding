import unittest
import json
from pathlib import Path
from unittest.mock import patch
import jsonschema

from evaluation.r1_v4.rag_evidence_database.retrieval_remediation import bundle_v2
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import BundleRequest
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.requested_obligations_v2 import VERSION


class _FakeFrozenRetriever:
    """Synthetic clean-checkout harness; no empirical data is used."""
    def __init__(self, *args, **kwargs):
        class Cursor:
            def fetchone(self):
                return ('{"frames":300,"objects":{"cream_cheese_1":{"category":"cream_cheese"}}}',)
        self.catalogue = type("Catalogue", (), {"execute": lambda self, sql, args: Cursor()})()
        self.retrieve_called = False

    def response(self, request, status, reason, plan=None, groups=None):
        return {
            "completeness_status": status,
            "interpretation": plan,
            "groups": groups or [],
            "requested_families": (plan or {}).get("families", []),
            "safety_claim_sufficiency": "NOT_EVALUATED",
            "safety_claim_verified": False,
            "empirical_admission_enabled": False,
        }

    def retrieve(self, request, mode):
        self.retrieve_called = True
        groups = [{"family": f, "status": "AVAILABLE"} for f in request.plan or []]
        return {
            "completeness_status": "COMPLETE WITHIN VERIFIED CONTRACT",
            "interpretation": {"frozen": True},
            "requested_families": list(request.plan or []),
            "groups": groups,
            "safety_claim_sufficiency": "NOT_EVALUATED",
            "safety_claim_verified": False,
            "empirical_admission_enabled": False,
        }


class RequestedObligationBundleV2Tests(unittest.TestCase):
    def assert_contract_schema(self, response):
        schema_path = Path(__file__).parents[1] / "EVIDENCE_BUNDLE_REQUESTED_OBLIGATIONS_V2.schema.json"
        jsonschema.validate(response, json.loads(schema_path.read_text()))

    def test_complete_retrieval_does_not_imply_physical_eligibility(self):
        fake = _FakeFrozenRetriever()
        with patch.object(bundle_v2, "FrozenRetriever", return_value=fake):
            retriever = bundle_v2.RequestedObligationsRetriever()
            response = retriever.retrieve(BundleRequest("Show joint configuration at simulator label 2.1 seconds.", "exec"))
        self.assertTrue(fake.retrieve_called)
        self.assertEqual(response["planner_version"], VERSION)
        self.assertEqual(response["query_interpretation_status"], "RESOLVED")
        self.assertEqual(response["obligation_plan_status"], "COMPLETE")
        self.assertEqual(response["retrieval_completeness_status"], "COMPLETE WITHIN VERIFIED CONTRACT")
        self.assertEqual(response["physical_evidence_eligibility"], "NOT_EVALUATED")
        self.assertEqual(set(response["requested_families"]), {"recorded_time", "raw.robot0_joint_pos"})
        self.assert_contract_schema(response)

    def test_incomplete_plan_does_not_call_retrieval(self):
        fake = _FakeFrozenRetriever()
        with patch.object(bundle_v2, "FrozenRetriever", return_value=fake):
            retriever = bundle_v2.RequestedObligationsRetriever()
            response = retriever.retrieve(BundleRequest("Report wrist orientation at frame 2.", "exec"))
        self.assertFalse(fake.retrieve_called)
        self.assertEqual(response["retrieval_completeness_status"], "NOT_RUN")
        self.assertNotEqual(response["completeness_status"], "COMPLETE WITHIN VERIFIED CONTRACT")
        self.assert_contract_schema(response)

    def test_retriever_cannot_omit_planned_family_and_claim_complete(self):
        fake = _FakeFrozenRetriever()
        fake.retrieve = lambda request, mode: {
            "completeness_status": "COMPLETE WITHIN VERIFIED CONTRACT",
            "requested_families": list(request.plan or []),
            "groups": [{"family": "recorded_time", "status": "AVAILABLE"}],
            "safety_claim_sufficiency": "NOT_EVALUATED",
            "safety_claim_verified": False,
        }
        with patch.object(bundle_v2, "FrozenRetriever", return_value=fake):
            retriever = bundle_v2.RequestedObligationsRetriever()
            response = retriever.retrieve(BundleRequest("Show joint configuration at simulator label 2.1 seconds.", "exec"))
        self.assertEqual(response["completeness_status"], "PARTIAL")
        self.assertEqual(response["retrieval_completeness_status"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
