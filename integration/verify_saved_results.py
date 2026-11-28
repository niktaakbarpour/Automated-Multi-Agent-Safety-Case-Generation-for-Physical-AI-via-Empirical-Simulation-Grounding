#!/usr/bin/env python3
"""Check committed public RQ2 CSV/JSON consistency; never opens review records."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RQ2 = ROOT / "evaluation/m4_20261127/rq2"
def rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def truth(value):
    return str(value).strip().lower() in ("true", "1", "yes")
def retrospective():
    root = RQ2 / "task7c_retrospective"
    cohort = rows(root / "COHORT_ACCOUNTING.csv")
    matrix = rows(root / "CONFUSION_MATRIX.csv")
    labels = ["violation_observed", "no_violation_observed_within_validated_coverage", "TOTAL"]
    positive = "checker_violation_prediction"
    negative = "checker_no_violation_prediction"
    excluded = "not_executed_source_provenance_unavailable"
    assert [r["human_reference"] for r in cohort] == [r["human_reference"] for r in matrix] == labels
    for row, scored in zip(cohort, matrix):
        assert (row[positive], row[negative]) == (scored[positive], scored[negative])
        assert int(scored["total"]) == int(row[positive]) + int(row[negative])
        assert int(row["total"]) == int(scored["total"]) + int(row[excluded])
    for column in (positive, negative, excluded, "total"):
        assert int(cohort[2][column]) == sum(int(r[column]) for r in cohort[:2])
    tp, fn = int(matrix[0][positive]), int(matrix[0][negative])
    fp, tn = int(matrix[1][positive]), int(matrix[1][negative])
    total = tp + tn + fp + fn
    confusion = {"TP": tp, "FP": fp, "TN": tn, "FN": fn}
    metrics = {
        name: {"numerator": n, "denominator": d, "percent": round(100 * n / d, 2)}
        for name, n, d in (
            ("precision", tp, tp + fp), ("recall_sensitivity", tp, tp + fn),
            ("f1", 2 * tp, 2 * tp + fp + fn), ("accuracy", tp + tn, total),
        )
    }
    provenance = json.loads((root / "PROVENANCE.json").read_text(encoding="utf-8"))
    assert dict(confusion, **metrics) == provenance["metrics_determinate_subset_n18"]
    assert total == provenance["cohort"]["checker_executed"] == int(matrix[2]["total"])
    exclusions = rows(root / "NOT_EXECUTED_CASES.csv")
    case_ids = {row["case_id"] for row in exclusions}
    assert len(case_ids) == len(exclusions) == int(cohort[2][excluded])
    assert all(row["status"] == "not_executed" and row["reason"] == "source_runner_provenance_unavailable"
               for row in exclusions)
    return {"cases": int(cohort[2]["total"]), "scored": total, "confusion": confusion,
            "metrics": metrics, "not_executed": sorted(case_ids)}

def main():
    results = rows(RQ2 / "R1_RESULTS.csv")
    metrics = json.loads((RQ2 / "R1_METRICS.json").read_text(encoding="utf-8"))
    assert len(results) == 3
    assert all(truth(r["applicability_agreement"]) for r in results)
    applicable = [r for r in results if truth(r["binary_metric_eligible"])]
    na = [r for r in results if r["human_binary_outcome"] == "not_applicable"]
    assert len(applicable) == 2 and len(na) == 1
    counts = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    for r in applicable:
        human = r["human_binary_outcome"]
        pred = r["checker_prediction"]
        positive = pred == "violation_observed"
        if human == "violation":
            counts["TP" if positive else "FN"] += 1
        elif human == "no_violation":
            counts["FP" if positive else "TN"] += 1
        else:
            raise AssertionError(f"unexpected binary reference: {human}")
    abstentions = sum(truth(r["binary_decision_abstention"]) for r in applicable)
    groups = len({r["canonical_source_id"] for r in results})
    assert groups == metrics["sample"]["canonical_source_groups"]
    declared = metrics["binary_violation_metrics"]["confusion"]
    declared = {"TP": declared["true_positive"], "TN": declared["true_negative"],
                "FP": declared["false_positive"], "FN": declared["false_negative"]}
    assert counts == declared == {"TP": 1, "TN": 1, "FP": 0, "FN": 0}
    assert metrics["applicability"]["agreement"] == {"numerator": 3, "denominator": 3, "rate": 1.0}
    assert metrics["binary_violation_metrics"]["not_applicable_excluded"] == 1

    expanded = rows(RQ2 / "expanded_evaluation/CHECKER_CASE_RESULTS.csv")
    summary = json.loads((RQ2 / "expanded_evaluation/SUMMARY_METRICS.json").read_text(encoding="utf-8"))
    general = [r for r in expanded if r["population"] == "same_scene_generalization_60"]
    assert len(general) == 300
    app = [r for r in general if r["applicability"] == "applies"]
    na_rows = [r for r in general if r["applicability"] == "does_not_apply"]
    abstained = [r for r in app if truth(r["abstention"])]
    determinate = [r for r in app if not truth(r["abstention"])]
    assert (len(app), len(na_rows), len(abstained), len(determinate)) == (120, 180, 100, 20)
    assert summary["generalization_coverage_only"]["overall"]["applicable_units"] == len(app)
    assert summary["generalization_coverage_only"]["overall"]["determinate_decisions"] == len(determinate)
    assert summary["generalization_coverage_only"]["overall"]["abstentions"] == len(abstained)
    assert summary["generalization_coverage_only"]["frozen_summary_comparison"]["matches_frozen_counts"]
    cross_task = [r for r in general if r["benchmark_task_id"] != "0"]
    cross_app = [r for r in cross_task if r["applicability"] == "applies"]
    cross_determinate = sum(not truth(r["abstention"]) for r in cross_app)
    transfer = summary["generalization_coverage_only"]["partitions"]["cross_task_same_scene"]
    assert len(cross_task) == transfer["object_units"] == 250
    assert len(cross_app) == transfer["applicable_units"] == 100
    assert cross_determinate == transfer["determinate_decisions"] == 0
    exclusions = rows(RQ2 / "expanded_evaluation/EXCLUSIONS.csv")
    gated = {r["canonical_execution_id"] for r in exclusions if r["stage"] == "mapping_gate"}
    assert len(gated) == 38

    print(json.dumps({
        "result": "PASS", "private_review_records_opened": 0,
        "task7c_retrospective": retrospective(),
        "task_transfer": {"cross_task_same_scene": f"{cross_determinate}/{len(cross_app)}",
                          "cross_scene_mapping_rejections": len(gated)},
        "calibration": {"cases": 3, "applicability_agreement": "3/3",
                        "applicable": 2, "not_applicable": 1, "confusion": counts,
                        "groups": groups, "coverage": f"{len(applicable)-abstentions}/{len(applicable)}",
                        "abstention_rate": f"{abstentions}/{len(applicable)}"},
        "generalization_coverage_only": {"executions": 60, "object_units": len(general),
                                        "applicable": len(app), "not_applicable": len(na_rows),
                                        "determinate": len(determinate), "abstentions": len(abstained),
                                        "coverage": "20/120", "abstention_rate": "100/120"},
    }, indent=2, sort_keys=True))
if __name__ == "__main__":
    main()
