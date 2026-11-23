import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest
import json


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
spec = importlib.util.spec_from_file_location("score_rq2", BASE / "score_rq2.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)


def read_fixture(name, fields):
    return score.load_csv(BASE / "fixtures" / name, fields)


class ScoreRQ2Tests(unittest.TestCase):
    def setUp(self):
        self.predictions = read_fixture("synthetic_predictions.csv", score.PREDICTION_FIELDS)
        self.references = read_fixture("synthetic_finalized_references.csv", score.REFERENCE_FIELDS)

    def test_all_decision_categories_and_split_summaries(self):
        rows, summary = score.evaluate(self.predictions, self.references, "a" * 64, "b" * 64)
        self.assertEqual(len(rows), 6)
        development = summary["split_summaries"]["development_calibration"]
        self.assertEqual(development["violation_detection"]["TP"], 1)
        self.assertEqual(development["violation_detection"]["TN"], 1)
        self.assertEqual(development["violation_detection"]["abstentions_or_nonbinary_predictions"], 1)
        self.assertEqual(development["applicability"]["reference_not_applicable"], 1)
        self.assertEqual(development["not_applicable_and_excluded"]["reference_not_applicable_units"], 1)
        evaluation = summary["split_summaries"]["independent_evaluation"]
        self.assertEqual(evaluation["not_applicable_and_excluded"]["excluded_reference_units"], 1)
        self.assertEqual(evaluation["violation_detection"]["decided_binary_pairs"], 0)
        self.assertIsNone(evaluation["violation_detection"]["specificity"])

    def test_abstention_is_not_negative_or_correct(self):
        rows, summary = score.evaluate(self.predictions, self.references, "a" * 64, "b" * 64)
        abstained = next(row for row in rows if row["case_id"] == "dev_abstain")
        self.assertEqual(abstained["score_status"], "abstained_or_invalid")
        self.assertIsNone(abstained["violation_correct"])
        matrix = summary["split_summaries"]["development_calibration"]["violation_detection"]
        self.assertEqual((matrix["TP"], matrix["FP"], matrix["TN"], matrix["FN"]), (1, 0, 1, 0))

    def test_duplicate_keys_rejected(self):
        with self.assertRaisesRegex(score.EvaluationError, "duplicate prediction key"):
            score.evaluate(self.predictions + [self.predictions[0]], self.references, "a", "b")

    def test_missing_join_rejected_and_reported(self):
        with self.assertRaisesRegex(score.EvaluationError, "missing_prediction_joins"):
            score.evaluate(self.predictions[:-1], self.references, "a", "b")

    def test_unfinalized_reference_rejected(self):
        refs = [dict(row) for row in self.references]
        refs[0]["adjudication_status"] = "incomplete"
        with self.assertRaisesRegex(score.EvaluationError, "not finalized"):
            score.evaluate(self.predictions, refs, "a", "b")

    def test_source_group_cannot_cross_splits(self):
        predictions = [dict(row) for row in self.predictions]
        references = [dict(row) for row in self.references]
        predictions[4]["source_group_id"] = "dev_group"
        references[4]["source_group_id"] = "dev_group"
        with self.assertRaisesRegex(score.EvaluationError, "multiple .* splits"):
            score.evaluate(predictions, references, "a", "b")

    def test_not_applicable_reference_cannot_be_a_binary_negative(self):
        refs = [dict(row) for row in self.references]
        refs[2]["violation_reference"] = "no_violation"
        with self.assertRaisesRegex(score.EvaluationError, "not-applicable reference has binary"):
            score.evaluate(self.predictions, refs, "a", "b")

    def test_empty_metric_denominators_are_null(self):
        rows, _ = score.evaluate(self.predictions, self.references, "a", "b")
        sparse = score.summarize(rows, "independent_evaluation")["violation_detection"]
        self.assertIsNone(sparse["precision"])
        self.assertIsNone(sparse["recall"])
        self.assertIsNone(sparse["specificity"])

    def test_auditable_csv_and_json_outputs_written(self):
        rows, summary = score.evaluate(self.predictions, self.references, "a" * 64, "b" * 64)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "result"
            score.write_outputs(rows, summary, target)
            self.assertTrue((target / "per_case.csv").is_file())
            self.assertTrue((target / "summary.json").is_file())
            self.assertEqual(json.loads((target / "summary.json").read_text())["joined_units"], 6)

    def test_frozen_json_predictions_map_statuses_and_manifest_identity(self):
        rows = score.load_prediction_input(
            BASE / "fixtures" / "synthetic_frozen_predictions.json",
            "development_calibration",
            BASE / "fixtures" / "synthetic_case_manifest.json",
        )
        self.assertEqual(rows[0]["source_group_id"], "json_group")
        self.assertEqual(rows[0]["applicability_prediction"], "applicable")
        self.assertEqual(rows[0]["violation_prediction"], "violation")


if __name__ == "__main__":
    unittest.main()
