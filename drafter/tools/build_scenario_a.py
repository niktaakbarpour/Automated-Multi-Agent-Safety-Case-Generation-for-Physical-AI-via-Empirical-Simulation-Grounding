"""Build a contract fixture from unchanged archived evidence metadata.

This does not read the original recordings, run a checker or call a model.
Run from any directory with Python 3.12. Use --check to verify reproducibility.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from evaluation.r1_v4.provenance import digest, strict_loads

REVISION = "0cda4f32824d02c3c81a148db9998d88cde96b2c"
REPOSITORY = (
    "https://github.com/niktaakbarpour/"
    "Automated-Multi-Agent-Safety-Case-Generation-for-Physical-AI-"
    "via-Empirical-Simulation-Grounding"
)
BASE_CONFIG = "requirements/r1_generalized_v2/EXAMPLE_CONFIGS/A_LIBERO_FIVE_OBJECTS.json"
ARCHIVED_EXPORT = "evaluation/r1_v4/evidence_registry_gsn/demo/REGISTRY_EXPORT.json"
EXPECTED_BLOBS = {
    BASE_CONFIG: "b7bac77ac3d926eb5759646acc38674b7c752cd0",
    ARCHIVED_EXPORT: "f6fecbb8d63cee36b2a0ff1c04fe874ea3647f13",
}
INTERVAL = [10, 12]
CLOCK = "saved_frame_index"
JUDGMENTS = {"ai_reference_judgment", "human_reference_judgment", "checker_assessment"}


def source_artifact(path: str) -> tuple[dict, dict]:
    """Bind only committed JSON bytes; never follow an evidence source path."""
    raw = (REPO / path).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != EXPECTED_BLOBS[path]:
        raise ValueError(f"Pinned source artifact changed: {path}")
    value = strict_loads(raw.decode("utf-8"))
    binding = {
        "path": path,
        "git_blob_sha1": blob,
        "bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": digest(value),
    }
    return value, binding


def known_gaps(objects: list[str], records: list[dict]) -> list[dict]:
    """List absent saved-frame metadata, without declaring evidence sufficient."""
    gaps = []
    for object_id in objects:
        frames = {
            frame
            for record in records
            if record["object_id"] == object_id
            for frame in range(record["interval"][0], record["interval"][1] + 1)
        }
        missing = [frame for frame in range(INTERVAL[0], INTERVAL[1] + 1) if frame not in frames]
        if not missing:
            continue
        first = last = missing[0]
        for frame in missing[1:] + [None]:
            if frame is not None and frame == last + 1:
                last = frame
                continue
            gaps.append({
                "object_id": object_id,
                "interval": [first, last],
                "reason": "No archived record for this object and saved-frame interval in the supplied export.",
            })
            first = last = frame
    return gaps


def build() -> tuple[dict, dict]:
    original, config_source = source_artifact(BASE_CONFIG)
    export, export_source = source_artifact(ARCHIVED_EXPORT)
    records = export["records"]
    if export["schema_version"] != "1.0.0" or len(records) != 18:
        raise ValueError("Unexpected archived export")
    for record in records:
        if record["id"] != "ev:" + digest({k: v for k, v in record.items() if k != "id"}):
            raise ValueError("Archived record content-ID mismatch")
    identity_fields = ("execution_id", "benchmark", "task_id", "model_checkpoint")
    if any(len({record[field] for record in records}) != 1 for field in identity_fields):
        raise ValueError("Archived records do not have one target identity")
    identity = {field: records[0][field] for field in identity_fields}
    identity["variant_id"] = None
    if identity["task_id"] != original["task_id"]:
        raise ValueError("Archived task and base configuration differ")
    config = copy.deepcopy(original)
    changes = []

    def change(pointer: str, value) -> None:
        parts = pointer.lstrip("/").split("/")
        parent = config
        for part in parts[:-1]:
            parent = parent[part]
        key = parts[-1]
        changes.append({"pointer": pointer, "before": copy.deepcopy(parent[key]), "after": value})
        parent[key] = value

    change("/benchmark/id", identity["benchmark"])
    change("/benchmark/policy_checkpoint", identity["model_checkpoint"])
    change("/execution_id", identity["execution_id"])
    change("/monitoring_interval/end/kind", "explicit_index")
    change("/monitoring_interval/end/value", INTERVAL[1])
    objects = config["protected_objects"]
    eligible = [record for record in records if (
        record["kind"] not in JUDGMENTS
        and record["requirement_id"] == config["requirement_id"]
        and record["requirement_version"] == config["requirement_version"]
        and all(record[field] == identity[field] for field in identity_fields)
        and record["object_id"] in objects
        and record["domain"] == "frame"
        and record["clock"] == CLOCK
        and INTERVAL[0] <= record["interval"][0] <= record["interval"][1] <= INTERVAL[1]
    )]
    eligible_ids = [record["id"] for record in eligible]
    missing_objects = [obj for obj in objects if not any(r["object_id"] == obj for r in eligible)]
    request = {
        "schema_version": "drafter-request/0.1.0",
        "request_id": "scenario-a-archived-export",
        "test_fixture": True,
        "usage": "contract_fixture",
        "requirement_configuration": config,
        "requirement_configuration_sha256": digest(config),
        "target_execution": identity,
        "monitoring_scope": {
            "domain": "frame", "clock": CLOCK, "interval": list(INTERVAL), "bounds": "inclusive",
            "resolution_status": "fixture_declared",
            "boundary_provenance": [
                "This derived contract fixture declares the limited inclusive saved-frame interval 10..12.",
                "Start 10 is preserved from the illustrative base configuration; end 12 is an explicit fixture choice, not the execution's terminal boundary.",
            ],
        },
        "evidence_package": export,
        "evidence_package_sha256": digest(export),
        "evidence_handling": {
            "data_origin": "archived_registry_export", "source_replay": "not_performed",
            "empirical_admission_enabled": False,
            "graph_eligible_evidence_ids": eligible_ids,
            "context_only_evidence_ids": [r["id"] for r in records if r["id"] not in eligible_ids],
        },
        "checker_context": {"status": "not_available", "assessments": []},
        "safety_knowledge": [],
        "related_cases": [],
        "retrieval_context": {
            "format": "registry_export", "completeness_status": "not_evaluated",
            "requested_objects": list(objects), "requested_interval": list(INTERVAL),
            "missing_objects": missing_objects, "gaps": known_gaps(objects, eligible),
            "limitations": [
                "This is an archived metadata export, not a new structured retrieval or source replay.",
                "Known saved-frame gaps do not establish full per-measurement coverage or physical sufficiency.",
            ],
        },
        "limitations": [
            "Contract fixture using real archived records; it is not a simulated execution or a complete real-run assessment.",
            "The 18 original record envelopes, evidence IDs, source references, validation labels and provenance are unchanged.",
            "The export contains metadata and source references, not the original numerical pose/contact observations or camera pixels.",
            "Original HDF5 and metadata sources have not been reopened or rehashed here; archived validation labels do not establish a new source verification.",
            "Only cream_cheese_1 has archived evidence in this package; all five configured objects remain in scope and missing objects are explicit.",
            "Available object-scoped measurement envelopes cover frames 10 and 11 only; frame 12 has no archived record in this package.",
            "Frame 9 records, overlapping metadata documents and the AI reference judgment remain context-only; reference judgments are not physical checker results.",
            "Graph eligibility means scope-compatible citation metadata only; it does not admit evidence to a physical checker or prove support, falling, non-applicability or safety.",
            "The derived configuration remains illustrative_unvalidated, with its original unresolved adapter, manifest and physical capability gates.",
            "Camera exposure alignment and physical support/fall interpretation are not established by this metadata package.",
            "No checker assessment, LLM generation, argument graph or real-run safety conclusion is supplied.",
        ],
        "input_provenance": {
            "repository": REPOSITORY, "revision": REVISION,
            "source_artifacts": [config_source, export_source],
            "configuration_derivation": {
                "base_path": BASE_CONFIG, "base_canonical_sha256": digest(original), "changes": changes,
            },
        },
        "empirical_admission_enabled": False,
        "safety_claim_verified": False,
    }
    expectations = {
        "schema_version": "drafter-fixture-expectations/0.1.0",
        "request_id": request["request_id"], "request_sha256": digest(request),
        "expected_physical_claim_status": "unresolved",
        "expected_object_ids": list(objects),
        "expected_record_count": 18,
        "expected_graph_eligible_evidence_ids": eligible_ids,
        "expected_context_only_evidence_ids": request["evidence_handling"]["context_only_evidence_ids"],
        "expected_missing_objects": missing_objects,
        "expected_gaps": request["retrieval_context"]["gaps"],
        "empirical_admission_enabled": False, "safety_claim_verified": False,
        "required_invariants": [
            "All original archived record values and evidence IDs are retained.",
            "All five configured objects remain represented, including objects with no supplied evidence.",
            "Only scope-compatible, nonjudgment evidence metadata may be a graph Solution reference.",
            "Source replay, physical checking and LLM execution are not claimed.",
            "No prewritten graph or expected conclusion is supplied in the generation request.",
        ],
    }
    # Check that deriving the request never mutated either archived source object.
    if digest(original) != config_source["canonical_sha256"] or digest(export) != export_source["canonical_sha256"]:
        raise ValueError("Source artifact mutated while building fixture")
    return request, expectations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify existing fixture bytes without rewriting")
    args = parser.parse_args()
    request, expectations = build()
    outputs = {
        REPO / "drafter/cases/scenario_a.request.json": request,
        REPO / "drafter/cases/scenario_a.expectations.json": expectations,
    }
    for path, value in outputs.items():
        raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError(f"Fixture is stale: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({
        "status": "checked" if args.check else "built",
        "request_sha256": digest(request),
        "record_count": len(request["evidence_package"]["records"]),
        "graph_eligible_record_count": len(request["evidence_handling"]["graph_eligible_evidence_ids"]),
        "context_only_record_count": len(request["evidence_handling"]["context_only_evidence_ids"]),
        "missing_objects": request["retrieval_context"]["missing_objects"],
    }, indent=2))


if __name__ == "__main__":
    main()
