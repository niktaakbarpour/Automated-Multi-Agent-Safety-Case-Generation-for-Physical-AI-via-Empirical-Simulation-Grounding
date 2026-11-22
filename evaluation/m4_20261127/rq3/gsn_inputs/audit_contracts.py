"""Record byte-level contract compatibility for the CPU fixture handoff."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[4]
BASE = "20cec80bd44d19c6f58168132f366cbe38bd74e9"
V3 = Path("evaluation/r1_v3")
FREEZE = Path("evaluation/m4_20261127/rq3/freeze/CRITIC_FREEZE.json")
PHASE5 = "evaluation/r1_v4/rag_evidence_database/final_phase5_release/"
GSN = "evaluation/r1_v4/evidence_registry_gsn/"
CONTRACTS = (
    "requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json",
    "requirements/r1_generalized_v2/R1_V2_SPECIFICATION.md",
    "human_review_package/requirement_scope.v3.json",
    "evaluation/r1_v3/FREEZE.json",
    "evaluation/m4_20261127/shared/M4_PROTOCOL_FREEZE.md",
    GSN + "gsn.py",
    GSN + "gsn_graph.schema.json",
    GSN + "models.py",
    GSN + "registry_record.schema.json",
    PHASE5 + "STRUCTURED_QUERY_SCHEMA.json",
    PHASE5 + "EVIDENCE_BUNDLE_SCHEMA.json",
    "drafter/request_profiles.py",
    "drafter/validation.py",
    "drafter/phase5_adapter.py",
    "drafter/schemas/draft_request.schema.json",
    "drafter/schemas/draft_argument.schema.json",
    "integration/handoff.py",
    "critic/checks.py",
    "critic/schemas/critic_request.schema.json",
    "critic/schemas/critic_report.schema.json",
    "drafter/revision/contract.py",
    "drafter/revision/schemas/revision_request.schema.json",
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    return (ROOT / path).read_bytes()


def read_json(path):
    return json.loads(read_bytes(path))


def audit():
    contracts = []
    for path in CONTRACTS:
        data = read_bytes(path)
        reference = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
        value = {"path": path, "sha256": sha256(data), "matches_base": data == reference}
        if path.endswith(".schema.json"):
            value["schema_id"] = json.loads(data).get("$id")
        contracts.append(value)

    frozen_v3 = read_json(V3 / "FREEZE.json")
    v3_matches = {
        path: sha256(read_bytes(V3 / path)) == expected
        for path, expected in frozen_v3["implementation_files"].items()
    }
    critic_hashes = read_json(FREEZE)["files"]
    changed_critic_files = []
    for path, expected in sorted(critic_hashes.items()):
        full_path = ROOT / path
        actual = sha256(full_path.read_bytes()) if full_path.is_file() else None
        if actual != expected:
            changed_critic_files.append({"path": path, "frozen_sha256": expected,
                                         "current_sha256": actual})

    result = {
        "schema_version": "m4-rq3-cpu-contract-audit/0.1.0",
        "baseline_commit": BASE,
        "contracts": contracts,
        "r1_v3_frozen_implementation_matches": v3_matches,
        "critic_stored_freeze_manifest": str(FREEZE),
        "critic_freeze_file_mismatches": changed_critic_files,
    }
    passed = all(entry["matches_base"] for entry in contracts) and all(v3_matches.values())
    return result, passed


def main():
    report, passed = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
