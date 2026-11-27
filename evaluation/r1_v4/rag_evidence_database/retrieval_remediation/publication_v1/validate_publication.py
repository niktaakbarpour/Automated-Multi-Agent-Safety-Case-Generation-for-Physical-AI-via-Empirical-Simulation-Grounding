#!/usr/bin/env python3
"""Validate public RQ1 publication encodings, CSV semantics, and checksums."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_CASE_IDS = [f"KH2-C{cluster}-{case:02d}" for cluster in range(1, 10) for case in range(24)]
EXPECTED_TEMPORAL_CASE_IDS = ["KH2-C2-02", "KH2-C2-10", "KH2-C2-18"]
EXPECTED_FAULT_IDS = [f"KH2-C8-{case:02d}" for case in (4, 5, 6, 7, 12, 13, 14, 15, 20, 21, 22, 23)]
EXPECTED_FAULTS = {
    "KH2-C8-04": "missing_source", "KH2-C8-05": "corrupt_source",
    "KH2-C8-06": "symlink_source", "KH2-C8-07": "replace_source",
    "KH2-C8-12": "missing_source", "KH2-C8-13": "corrupt_source",
    "KH2-C8-14": "symlink_source", "KH2-C8-15": "replace_source",
    "KH2-C8-20": "missing_source", "KH2-C8-21": "corrupt_source",
    "KH2-C8-22": "symlink_source", "KH2-C8-23": "replace_source",
}
EXPECTED_PUBLIC_FILES = {
    "RQ1_FINAL_RESULTS.md", "CASE_ASSESSMENTS.csv",
    "THREE_CASE_ACTUAL_RETRIEVALS.csv", "FAULT_INJECTION_CASES.csv",
}


def _read_csv(root: Path, name: str, required_columns: set[str]) -> list[dict[str, str]]:
    raw = (root / name).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{name}: UTF-8 BOM is not permitted")
    if b"\r" in raw:
        raise ValueError(f"{name}: expected canonical UTF-8 with LF line endings")
    try:
        content = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name}: not valid UTF-8") from exc
    reader = csv.DictReader(io.StringIO(content, newline=""))
    if not reader.fieldnames or set(reader.fieldnames) != required_columns:
        raise ValueError(f"{name}: unexpected CSV header")
    rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{name}: malformed row width")
    return rows


def validate_case_assessments(rows: list[dict[str, str]]) -> None:
    ids = [row["case_id"] for row in rows]
    if ids != EXPECTED_CASE_IDS:
        raise ValueError("CASE_ASSESSMENTS.csv: case IDs, row count, or ordering changed")
    counts = Counter(row["final_assessment"] for row in rows)
    expected = Counter({"correct_and_verified_complete": 133, "correct_abstention": 71, "evaluation_unavailable": 12})
    if counts != expected:
        raise ValueError(f"CASE_ASSESSMENTS.csv: unexpected assessment counts: {dict(counts)}")
    if any(row["final_assessment"] == "confirmed_false_complete" for row in rows):
        raise ValueError("CASE_ASSESSMENTS.csv: confirmed false-complete rows are not expected")
    if sum(row["legacy_false_complete_flag"] == "true" for row in rows) != 49:
        raise ValueError("CASE_ASSESSMENTS.csv: historical false-complete flag count changed")
    fault_rows = {row["case_id"]: row for row in rows if row["fault_fixture_required"]}
    if set(fault_rows) != set(EXPECTED_FAULT_IDS):
        raise ValueError("CASE_ASSESSMENTS.csv: frozen fault-fixture case set changed")
    if any(row["fault_fixture_required"] != EXPECTED_FAULTS[case_id] for case_id, row in fault_rows.items()):
        raise ValueError("CASE_ASSESSMENTS.csv: frozen fault condition changed")
    if any(row["final_assessment"] != "evaluation_unavailable" for row in fault_rows.values()):
        raise ValueError("CASE_ASSESSMENTS.csv: fault-fixture cases must remain evaluation-unavailable in normal replay")


def validate_temporal_cases(rows: list[dict[str, str]]) -> None:
    ids = [row["case_id"] for row in rows]
    if ids != EXPECTED_TEMPORAL_CASE_IDS:
        raise ValueError("THREE_CASE_ACTUAL_RETRIEVALS.csv: temporal case IDs or ordering changed")
    expected_families = "recorded_time;raw.robot0_joint_pos"
    for row in rows:
        if row["retrieval_status"] != "COMPLETE WITHIN VERIFIED CONTRACT":
            raise ValueError(f"{row['case_id']}: retrieval is not verified complete")
        if row["requested_families"] != expected_families or row["available_families"] != expected_families:
            raise ValueError(f"{row['case_id']}: expected temporal families are missing or reordered")
        if row["numeric_sample_count"] != "1" or row["corrected_assessment"] != "correct_and_verified_complete":
            raise ValueError(f"{row['case_id']}: unexpected temporal verification fields")


def validate_fault_cases(rows: list[dict[str, str]]) -> None:
    ids = [row["case_id"] for row in rows]
    if ids != EXPECTED_FAULT_IDS:
        raise ValueError("FAULT_INJECTION_CASES.csv: frozen fault case IDs or ordering changed")
    for row in rows:
        case_id = row["case_id"]
        if row["fault_condition"] != EXPECTED_FAULTS[case_id]:
            raise ValueError(f"{case_id}: fault condition changed")
        if row["retrieval_status"] != "UNAVAILABLE" or row["correct_abstention"] != "True":
            raise ValueError(f"{case_id}: expected unavailable retrieval with correct abstention")
        if row["execution_error"] != "False" or row["authoritative_source_unchanged"] != "True":
            raise ValueError(f"{case_id}: unexpected execution error or authoritative-source change")


def validate_publication(root: Path = ROOT) -> None:
    root = Path(root)
    assessment_rows = _read_csv(root, "CASE_ASSESSMENTS.csv", {
        "case_id", "final_assessment", "retrieval_status", "claimed_complete",
        "legacy_false_complete_flag", "expected_families", "available_families",
        "diagnostic_tags", "legacy_evaluator_errors", "fault_fixture_required",
    })
    temporal_rows = _read_csv(root, "THREE_CASE_ACTUAL_RETRIEVALS.csv", {
        "case_id", "retrieval_status", "planner_version", "requested_families",
        "available_families", "numeric_sample_count", "corrected_assessment",
    })
    fault_rows = _read_csv(root, "FAULT_INJECTION_CASES.csv", {
        "case_id", "fault_condition", "fixture_procedure", "planner_status",
        "requested_families", "retrieval_status", "correct_abstention",
        "rejection_code", "execution_error", "authoritative_source_unchanged",
    })
    validate_case_assessments(assessment_rows)
    validate_temporal_cases(temporal_rows)
    validate_fault_cases(fault_rows)

    manifest_path = root / "PUBLICATION_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("publication_encoding") != {
        "character_encoding": "UTF-8",
        "csv_byte_order_mark": False,
        "csv_line_endings": "LF",
    }:
        raise ValueError("PUBLICATION_MANIFEST.json: canonical publication encoding is not declared")
    declared = manifest.get("publication_files")
    if not isinstance(declared, dict) or set(declared) != EXPECTED_PUBLIC_FILES:
        raise ValueError("PUBLICATION_MANIFEST.json: publication file inventory changed")
    for name, expected_hash in declared.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"PUBLICATION_MANIFEST.json: checksum mismatch for {name}")

    sums: dict[str, str] = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        if not match or match.group(2) in sums:
            raise ValueError("SHA256SUMS.txt: malformed or duplicate entry")
        sums[match.group(2)] = match.group(1)
    expected_files = EXPECTED_PUBLIC_FILES | {"PUBLICATION_MANIFEST.json"}
    if set(sums) != expected_files:
        raise ValueError("SHA256SUMS.txt: publication inventory changed")
    for name, expected_hash in sums.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"SHA256SUMS.txt: checksum mismatch for {name}")


if __name__ == "__main__":
    validate_publication()
    print("PASS: RQ1 publication encodings, records, and checksums")
