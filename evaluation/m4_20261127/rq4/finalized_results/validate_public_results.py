"""Validate the publication-safe RQ4 tables without rerunning scoring."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    with (HERE / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


outputs = read("RQ4_PER_OUTPUT.csv")
summary = read("RQ4_SUMMARY.csv")
assert len(outputs) == 12
assert len({r["output_id"] for r in outputs}) == 12
assert {r["method"] for r in outputs} == {"qwen", "template"}
assert all("blind_item_id" not in r for r in outputs)
assert all("new_statement" not in r for r in outputs)

expected = {
    "qwen": {"correct_repair": (9, 9), "defect_fixed=yes": (9, 9),
             "revised_claim_supported_by_evidence=yes": (9, 9),
             "new_problem_introduced=yes": (0, 9), "scope_preserved=yes": (9, 9),
             "invalid": (0, 9), "abstained": (0, 9), "missing_or_no_reply": (0, 9)},
    "template": {"correct_repair": (2, 3), "defect_fixed=yes": (3, 3),
                 "revised_claim_supported_by_evidence=yes": (2, 3),
                 "new_problem_introduced=yes": (1, 3), "scope_preserved=yes": (2, 3),
                 "invalid": (0, 3), "abstained": (0, 3), "missing_or_no_reply": (0, 3)},
}

def measure(rows, metric):
    if metric == "correct_repair":
        n = sum(r["correct_repair"] == "1" for r in rows)
    elif metric in ("invalid", "abstained", "missing_or_no_reply"):
        n = sum(r["status"] == metric for r in rows)
    else:
        field, value = metric.split("=", 1)
        n = sum(r[field] == value for r in rows)
    return n, len(rows)

for method, metrics in expected.items():
    rows = [r for r in outputs if r["method"] == method]
    for metric, pair in metrics.items():
        got = measure(rows, metric)
        assert got == pair, (method, metric, got, pair)
        published = [r for r in summary if r["method"] == method and r["metric"] == metric]
        assert len(published) == 1, (method, metric, len(published))
        assert (int(published[0]["numerator"]), int(published[0]["denominator"])) == pair

for method in expected:
    rows = [r for r in outputs if r["method"] == method]
    assert sum(int(r["second_reviews"]) for r in rows) == 9
    assert sum(int(r["second_reviews_missing"]) for r in rows) == 0
    assert sum(int(r["second_reviews_target_flagged"]) for r in rows) == 0
    assert sum(int(r["second_reviews_with_new_objection"]) for r in rows) == 2

print("PASS: 12 sanitized output rows; frozen primary numerators/denominators and second-Critic counts match.")
