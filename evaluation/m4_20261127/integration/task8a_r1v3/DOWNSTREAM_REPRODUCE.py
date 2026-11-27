"""Reproduce the Drafter-to-Critic contract result locally; this makes no model calls."""
import json
from pathlib import Path

from integration.handoff import build_critic_request

ROOT = Path(__file__).resolve().parents[4]
REQUEST = ROOT / "evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json"
REPORT = Path(__file__).with_name("DRAFTER_GENERATION_REPORT.json")

try:
    build_critic_request(json.loads(REQUEST.read_text()), json.loads(REPORT.read_text()))
except Exception as exc:  # the expected result is the contract rejection
    print(f"{type(exc).__name__}: {exc}")
    raise SystemExit(2)
print("Adapter accepted this R1 v3 report; compare with DOWNSTREAM_INTERFACE_COMPATIBILITY_PUBLIC.json")
