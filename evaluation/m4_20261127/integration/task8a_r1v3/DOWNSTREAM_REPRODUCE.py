"""Reproduce the Drafter-to-Critic contract result locally; this makes no model calls."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from integration.handoff import build_critic_request  # noqa: E402
from drafter.validation import ContractError  # noqa: E402

REQUEST = ROOT / "evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json"
REPORT = Path(__file__).with_name("DRAFTER_GENERATION_REPORT.json")

try:
    build_critic_request(json.loads(REQUEST.read_text()), json.loads(REPORT.read_text()))
except ContractError as exc:
    message = str(exc)
    expected = (
        "outcome_backing",
        "draft-argument-r1v3-prompt/0.1.0",
        "graph-plan-to-gsn-r1v3/0.1.0",
        "decoder_relaxation",
        "validation_schema_sha256",
    )
    missing = [diagnostic for diagnostic in expected if diagnostic not in message]
    if missing:
        print(f"Unexpected ContractError; expected diagnostic markers missing: {missing}")
        raise SystemExit(1)
    print("Expected ContractError reproduced (no model calls):")
    print("- execution_conclusion.outcome_backing rejected by generation-run schema")
    print("- R1 v3 prompt and serializer versions rejected by the adapter")
    print("- decoder_relaxation and validation_schema_sha256 rejected as extra trace fields")
    raise SystemExit(2)
print("Adapter accepted this R1 v3 report; compare with DOWNSTREAM_INTERFACE_COMPATIBILITY_PUBLIC.json")
raise SystemExit(1)
