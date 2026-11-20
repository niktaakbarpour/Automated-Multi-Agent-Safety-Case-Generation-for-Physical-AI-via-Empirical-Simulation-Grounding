"""RQ3 rule-blind model-only evaluation regression tests (CPU, scripted responses).

These development fixtures do not establish empirical Critic detection rates.
The experiment-only flag does not change critic.review() or production screening.
"""
import json
import unittest
from pathlib import Path

from critic import checks, llm, review

ROOT = Path(__file__).resolve().parents[2]
NEGATIVE = ROOT / "integration/fixtures/one_pass_20261113/artifacts/models/critic.controlled-negative.request.json"


class RuleBlindRQ3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.req = json.loads(NEGATIVE.read_text(encoding="utf-8"))
        cls.deterministic, cls.info = checks.run_all(cls.req)
        assert cls.info["input_valid"]
        cls.reply = json.dumps({
            "findings": [{
                "object_id": "cream_cheese_1",
                "node_id": "cream_cheese_1:G1",
                "category": "C12",
                "severity": "high",
                "explanation": "The goal claims guaranteed physical safety without supporting evidence.",
                "evidence_ids": [],
                "suggested_action": "Qualify the guarantee and leave the safety claim unresolved."
            }]
        })

    def test_default_review_still_suppresses_rule_duplicate(self):
        report = review(self.req, llm.ScriptedLLM(self.reply))
        self.assertEqual(report["review_status"], "completed")
        self.assertTrue(any(c["check_id"] == "CLAIM-ABSOLUTE-SAFETY" for c in report["criticisms"]))
        self.assertFalse(any(c["finding_source"] == "llm_proposed" for c in report["criticisms"]))
        self.assertTrue(any("duplicate of a deterministic finding" in x["reason"]
                            for x in report["rejected_llm_findings"]))

    def test_experiment_model_can_independently_find_rule_detected_claim(self):
        accepted, rejected, status = llm.run(
            llm.ScriptedLLM(self.reply), self.req, self.deterministic,
            self.info["records"], self.info["checker_admission"],
            rq3_rule_blind=True)
        self.assertTrue(status["ok"], status["error"])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["category"], "C12")
        self.assertEqual(accepted[0]["finding_source"], "llm_proposed")
        self.assertFalse(rejected)
        self.assertEqual(len(self.deterministic),
                         len(checks.run_all(self.req)[0]))

    def test_experiment_prompt_does_not_expose_deterministic_findings(self):
        class CaptureLLM(llm.ScriptedLLM):
            def complete(self, system, user):
                self.user_prompt = user
                return self.text

        model = CaptureLLM(self.reply)
        _, _, status = llm.run(
            model, self.req, self.deterministic,
            self.info["records"], self.info["checker_admission"],
            rq3_rule_blind=True)
        self.assertTrue(status["ok"], status["error"])
        view = json.loads(model.user_prompt.split("Input JSON:\n", 1)[1])
        self.assertEqual(view["already_found"], [])
        self.assertIn("guaranteed physically safe", json.dumps(view["graphs"]))
        self.assertNotIn("CLAIM-ABSOLUTE-SAFETY", model.user_prompt)

    def test_invalid_evidence_citation_is_still_rejected(self):
        fabricated = json.loads(self.reply)
        fabricated["findings"][0]["evidence_ids"] = ["ev:" + "0" * 64]
        accepted, rejected, status = llm.run(
            llm.ScriptedLLM(json.dumps(fabricated)), self.req,
            self.deterministic, self.info["records"],
            self.info["checker_admission"], rq3_rule_blind=True)
        self.assertTrue(status["ok"], status["error"])
        self.assertFalse(accepted)
        self.assertTrue(any("not in the package" in x["reason"] for x in rejected))


if __name__ == "__main__":
    unittest.main()
