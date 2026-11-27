"""Planner-only comparison on the exposed frozen RQ1 corpus; not holdout evidence."""
import json
import re
from collections import Counter
from pathlib import Path

from .config import HERE
from .planner import interpret as frozen_interpret
from .requested_obligations_v2 import interpret_v2


def main():
    rows = [json.loads(line) for line in (HERE / "FROZEN_HOLDOUT_DATASET.jsonl").read_text().splitlines() if line.strip()]
    old_missing = old_false_complete = new_missing = new_false_complete = recovered = 0
    statuses = Counter()
    incomplete = 0
    errors = []
    for row in rows:
        object_ids = re.findall(r"\b[a-z][a-z0-9_]*_\d+\b", row["query"].lower())
        objects = {object_id: {"category": object_id.rsplit("_", 1)[0]} for object_id in object_ids}
        catalogue = {"frames": row["frames"], "objects": objects}
        context = dict(row.get("request", {}))
        context.setdefault("object_id", None)
        expected = set(row["expected_families"])
        old = frozen_interpret(row["query"], catalogue, context)
        new = interpret_v2(row["query"], catalogue, context)
        old_families = set(old.get("families", []))
        new_families = set(new.get("families", []))
        old_ok = expected.issubset(old_families)
        new_ok = expected.issubset(new_families)
        old_missing += not old_ok
        old_false_complete += old.get("status") == "RESOLVED" and not old_ok
        new_missing += not new_ok
        new_false_complete += new.get("status") == "RESOLVED" and not new_ok
        recovered += new_ok and not old_ok
        incomplete += new["obligation_plan_status"] != "COMPLETE"
        statuses[new["status"]] += 1
        if old_ok and not new_ok:
            errors.append({"case_id": row["id"], "new_status": new["status"], "missing": sorted(expected - new_families)})
    result = {
        "evaluation_type": "exposed development regression comparison; not independent evaluation",
        "rows": len(rows),
        "historical_frozen_planner": {"expected_family_omissions": old_missing, "false_complete_plans": old_false_complete},
        "requested_obligations_v2": {
            "expected_family_omissions": new_missing,
            "false_complete_plans": new_false_complete,
            "rows_recovered_from_frozen_omission": recovered,
            "incomplete_plans": incomplete,
            "statuses": dict(sorted(statuses.items())),
            "regressions_against_reference_families": errors,
        },
        "actual_retrieval_replayed": False,
        "historical_bundle_result_false_complete_cases": ["KH2-C2-02", "KH2-C2-10", "KH2-C2-18"],
        "limitation": "Corpus is exposed and historical retrieval outputs are unchanged; planner-only counts do not estimate generalization.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
