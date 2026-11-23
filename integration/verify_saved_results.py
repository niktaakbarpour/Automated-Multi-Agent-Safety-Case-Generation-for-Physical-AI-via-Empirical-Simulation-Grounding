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
    print(json.dumps({
        "result": "PASS", "private_review_records_opened": 0,
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
