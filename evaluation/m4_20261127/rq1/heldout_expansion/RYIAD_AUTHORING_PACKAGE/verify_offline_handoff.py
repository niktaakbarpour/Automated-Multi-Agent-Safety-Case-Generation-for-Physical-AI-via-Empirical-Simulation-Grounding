#!/usr/bin/env python3
"""Verify the RQ1 offline package using only the Python 3 standard library."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
OFF = PKG / "OFFLINE_EVIDENCE"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    caps = rows(PKG / "SOURCE_CAPABILITIES.csv")
    form = rows(PKG / "BLANK_QUERY_REFERENCE_FORM.csv")
    recovery = {r["execution_id"]: r for r in rows(PKG / "SOURCE_RECOVERY_VERIFICATION.csv")}
    refs = rows(PKG / "SOURCE_EVIDENCE_INDEX.csv")
    ref_by_id = {r["evidence_id"]: r for r in refs}
    ref_hashes = rows(PKG / "SOURCE_REFERENCE_HASH_VERIFICATION.csv")
    manifest = json.loads((OFF / "EXTRACT_MANIFEST.json").read_text(encoding="utf-8"))

    assert len(caps) == 30 and len({r["execution_id"] for r in caps}) == 30
    assert len({r["task_id"] for r in caps}) == 4
    assert len({r["variant_id"] for r in caps}) == 4
    assert len(form) == 60
    human_fields = [k for k in form[0] if k not in {"case_id", "execution_id", "task_id", "variant_id", "reference_author_verification"}]
    assert all(not r[k].strip() for r in form for k in human_fields)
    assert len(recovery) >= 30
    for cap in caps:
        r = recovery[cap["execution_id"]]
        assert r["verification_status"] == "PASS"
        assert r["trajectory_sha256_recomputed"] == r["trajectory_sha256_receipt"]
    assert len({(r["source_path"], r["current_sha256"]) for r in ref_hashes}) == 67
    assert all(r["status"] == "PASS" for r in ref_hashes)

    source_manifest = {r["execution_id"]: r for r in manifest["source_files"]}
    assert len(source_manifest) == 30
    for cap in caps:
        ex = cap["execution_id"]
        assert source_manifest[ex]["source_trajectory_sha256"] == recovery[ex]["trajectory_sha256_recomputed"]

    for name, info in manifest["files"].items():
        p = OFF / name
        assert p.is_file(), name
        assert p.stat().st_size == info["bytes"], name
        assert sha256(p) == info["sha256"], name
        assert p.stat().st_size < 100 * 1024 * 1024, name

    sample_count = 0
    type_counts = {}
    with gzip.open(OFF / "EVIDENCE_SAMPLES.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            ref = ref_by_id[x["evidence_id"]]
            assert x["execution_id"] == ref["execution_id"]
            assert x["task_id"] == ref["task_id"]
            assert x["variant_id"] == ref["variant_id"]
            assert x["object_id"] == ref["object_id"]
            assert x["measurement_type"] == ref["measurement_type"]
            assert x["original_selector"] == ref["selector"]
            assert int(ref["saved_frame_start"]) <= x["frame_index"] <= int(ref["saved_frame_end"])
            assert x["source_trajectory_sha256"] == recovery[x["execution_id"]]["trajectory_sha256_recomputed"]
            sample_count += 1
            type_counts[x["measurement_type"]] = type_counts.get(x["measurement_type"], 0) + 1
    assert sample_count == manifest["sample_value_row_count"]
    assert type_counts == manifest["sample_rows_by_measurement_type"]

    evidence_count = 0
    seen = set()
    with gzip.open(OFF / "EVIDENCE_RECORDS.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            assert x["id"] in ref_by_id
            assert x["id"] not in seen
            seen.add(x["id"])
            ref = ref_by_id[x["id"]]
            assert x["execution_id"] == ref["execution_id"]
            assert x["object_id"] == ref["object_id"]
            evidence_count += 1
    assert evidence_count == manifest["evidence_record_count"] == len(seen)

    task_context = rows(OFF / "TASK_CONTEXT.csv")
    assert len(task_context) == 30
    task_refs = {r["execution_id"]: r for r in refs if r["measurement_type"] == "task_instruction"}
    for task in task_context:
        ref = task_refs[task["execution_id"]]
        assert task["task_instruction_evidence_id"] == ref["evidence_id"]
        assert task["task_metadata_sha256"] == ref["source_sha256"]

    unextracted = rows(OFF / "UNEXTRACTED_EVIDENCE.csv")
    camera_refs = [r for r in refs if r["measurement_type"] == "camera_reference"]
    assert len(unextracted) == len(camera_refs) == manifest["unextracted_evidence_count"]
    assert {r["evidence_id"] for r in unextracted} == {r["evidence_id"] for r in camera_refs}

    failures = {
        "libero_goal_openvla_oft_task08_seed1017_trial017_cfafd9ddc3db",
        "libero_long_openvla_oft_task00_seed1003_trial003_cfafd9ddc3db",
        "libero_spatial_openvla_oft_task00_seed1049_trial049_cfafd9ddc3db",
    }
    assert not failures.intersection({r["execution_id"] for r in caps})
    required = [
        "README.md", "AUTHORING_GUIDE.md", "AUTHORING_FORM_SCHEMA.json",
        "SOURCE_CAPABILITIES.csv", "SOURCE_EVIDENCE_INDEX.csv",
        "SOURCE_RECOVERY_VERIFICATION.csv", "SOURCE_REFERENCE_HASH_VERIFICATION.csv",
        "SOURCE_RECOVERY_SUMMARY.json", "OFFLINE_EVIDENCE/EXTRACT_LIMITATIONS.md",
    ]
    assert all((PKG / n).is_file() for n in required)
    print("PASS: 30 executions, 4 tasks, 4 variants, 60 blank slots")
    print("PASS: 67 unique source references and source hash receipts")
    print("PASS: {} value samples across {}".format(sample_count, type_counts))
    print("PASS: {} evidence envelopes; {} camera references explicitly unextracted".format(evidence_count, len(unextracted)))
    print("PASS: extract and task-context hashes bind to the frozen source-recovery records")
    print("PASS: no overlap with the 3 known false-complete development cases")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
