"""Validate the preserved genuine R1 v3 argument against its original request."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from drafter.r1v3_profile import validate_argument, validate_request  # noqa: E402

REQUEST = ROOT / "evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json"
ARGUMENT = Path(__file__).with_name("DRAFTER_ARGUMENT.json")

request = json.loads(REQUEST.read_text(encoding="utf-8"))
argument = json.loads(ARGUMENT.read_text(encoding="utf-8"))
validate_request(request)
validate_argument(argument, request)
print("PASS: genuine R1 v3 argument validates against original request")
