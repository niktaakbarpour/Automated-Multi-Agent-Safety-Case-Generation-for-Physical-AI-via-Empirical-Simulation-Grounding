#!/usr/bin/env python3
"""Verify the committed one-pass fixture without model calls or external data."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from critic import checks, schema
FIXTURE = ROOT / "integration" / "fixtures" / "one_pass_20261113"
MODELS = FIXTURE / "artifacts" / "models"
def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))
def main():
    manifest = read_json(FIXTURE / "MANIFEST.json")
    verified = []
    for entry in manifest["artifacts"]:
        path = FIXTURE / entry["file"]
        data = path.read_bytes()
        assert len(data) == entry["bytes"], f"size mismatch: {entry['file']}"
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], f"SHA-256 mismatch: {entry['file']}"
        verified.append(entry["file"])
    cases = [
        ("original", "critic.request.json", "critic.qwen.report.json"),
        ("controlled-negative", "critic.controlled-negative.request.json", "critic.controlled-negative.qwen.report.json"),
    ]
    results = []
    for label, request_name, report_name in cases:
        request = read_json(MODELS / request_name)
        report = read_json(MODELS / report_name)
        assert not schema.errors(request, schema.load("request")), f"{label} request schema invalid"
        assert not schema.errors(report, schema.load("report")), f"{label} report schema invalid"
        findings, info = checks.run_all(request)
        assert info["input_valid"], f"{label} Critic input invalid: {info}"
        assert report["request_id"] == request["request_id"]
        assert report["execution_id"] == request["evaluation_context"]["execution_id"]
        assert report["test_fixture"] is True and request["test_fixture"] is True
        assert report["review_status"] == "completed" and report["criticisms"] == []
        assert report["llm"]["backend"] in ("openai_compatible", "openai")
        results.append({"case": label, "request_schema": "pass", "critic_input": "pass",
                        "report_schema": "pass", "identity_binding": "pass",
                        "saved_qwen_report": "completed, zero criticisms",
                        "deterministic_findings": len(findings)})
    argument = read_json(MODELS / "drafter.argument.json")
    original_request = read_json(MODELS / "critic.request.json")
    assert argument["argument_bundle"] == original_request["argument_bundle"]
    assert argument["test_fixture"] is True
    print(json.dumps({"result": "PASS", "model_calls": 0,
                      "manifest_artifacts_hash_and_size_verified": len(verified),
                      "verified_files": verified, "cases": results,
                      "drafter_bundle_matches_original_critic_request": True,
                      "classification": "saved development fixture; not independent empirical evaluation"},
                     indent=2, sort_keys=True))
if __name__ == "__main__":
    main()
