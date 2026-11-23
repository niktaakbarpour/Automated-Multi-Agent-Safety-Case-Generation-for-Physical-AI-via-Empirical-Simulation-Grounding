#!/usr/bin/env python3
"""Rebuild and verify the RQ3 conditional-source admission matrix using repository metadata only."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BUILD_REPORT = ROOT / "evaluation/r1_v3_human_validation_20/BUILD_REPORT.json"
SOURCE_CATALOGUE = HERE / "PARENT_SOURCE_INVENTORY.csv"
GATE_SNAPSHOT = HERE / "SOURCE_GATE_SNAPSHOT.json"
MATRIX = HERE / "SOURCE_ELIGIBILITY_MATRIX.csv"
BLOCKERS = HERE / "BLOCKER_COUNTS.csv"

BLOCKER_DESCRIPTIONS = {
    "SOURCE_GROUP_INDEPENDENCE_NOT_VERIFIED": "The build receipt records distinct executions but no authoritative independent source-group identity or grouping rationale.",
    "PROJECT_SCOPE_APPROVAL_PENDING": "Aggregate RQ3/RQ4 wording, strata, rubric, and scoring approval is absent.",
    "R1_OWNER_SCOPE_AND_SOURCE_REUSE_APPROVAL_PENDING": "R1 owner approval of scope, source reuse, and admissible-evidence policy is absent.",
    "INDEPENDENT_R1_REFERENCE_AND_FREEZE_PENDING": "The authoritative intake has no completed independent R1 reference, adjudication, approval, or freeze.",
    "CRITIC_OWNER_AUDIT_ACCEPTANCE_PENDING": "Critic owner has not closed or explicitly accepted the adversarial/contract audit gate.",
    "CASE_PARTITION_LEAKAGE_AND_BLINDING_APPROVAL_PENDING": "Case eligibility, partition, leakage, reviewer effort, and blinding custody are not approved.",
    "EVIDENCE_ARMS_AND_RUN_PROTOCOL_APPROVAL_PENDING": "Evidence adapters, model/run settings, repetitions, interval method, and cost accounting are not approved.",
    "PER_RECORD_APPROVAL_NOT_VERIFIED": "No per-record approval receipt is present in the authoritative intake.",
    "REQUIREMENT_CONFIGURATION_BINDING_MISSING": "The complete execution-bound Drafter requirement configuration and its digest are absent.",
    "OBJECT_SURFACE_ROLE_MAPPING_UNVERIFIED": "The focal object ID is recorded, but the approved target/protected roster, support-surface role, and execution-specific mapping are not bound.",
    "MONITORING_SCOPE_BINDING_MISSING": "A prior R1 package describes frames 10 through terminal; no approved source-bound Drafter interval and boundary provenance are supplied.",
    "SOURCE_PATH_AND_CURRENT_BYTES_NOT_REVERIFIED": "Prior build receipts record matching hashes, but the resolved recording root/path was not retained and current source bytes were not re-opened in this audit.",
    "DRAFTER_EVIDENCE_CONTRACT_BINDING_MISSING": "Prior R1 evidence exports are not supplied as a validated Phase 5 structured request or registry bundle with exact evidence bindings.",
    "CRITIC_EXPOSURE_REVIEW_PENDING": "Prior R1 review exposure is known; Critic prompt/rule exposure and source leakage have not been cleared.",
    "DRAFTER_REQUEST_NOT_CONSTRUCTED": "No source-admitted, schema-validated request exists for this candidate."
}
BLOCKER_CODES = list(BLOCKER_DESCRIPTIONS)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def make_rows():
    if not BUILD_REPORT.is_file() or not GATE_SNAPSHOT.is_file() or not SOURCE_CATALOGUE.is_file():
        raise SystemExit("required repository source records are missing")
    build = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
    gate = json.loads(GATE_SNAPSHOT.read_text(encoding="utf-8"))
    if gate["case_count"] != 0 or gate["eligible_case_count"] != 0 or gate["frozen"] or gate["labels_assigned"]:
        raise SystemExit("gate snapshot no longer describes a zero-admission intake")
    selected = build.get("selected_source_cases", [])
    if len(selected) != 20:
        raise SystemExit(f"expected 20 recorded source cases, got {len(selected)}")
    archive_hash = build.get("source_archive_sha256", "")
    videos = build.get("video_verification", [])
    if not re.fullmatch(r"[0-9a-f]{64}", archive_hash):
        raise SystemExit("prior source archive hash receipt is malformed")
    if build.get("source_files_verified") != 1214 or len(videos) != 180:
        raise SystemExit("prior build receipt counts differ from the documented source package")
    if any(not re.fullmatch(r"[0-9a-f]{64}", v.get("sha256", "")) for v in videos):
        raise SystemExit("prior video receipt has a malformed hash")
    run_ids = [x["run_id"] for x in selected]
    hashes = [x["recording_sha256"] for x in selected]
    if len(set(run_ids)) != 20 or len(set(hashes)) != 20:
        raise SystemExit("source execution IDs and trajectory hashes must be distinct")
    if any(not x.get("source_stat_preserved") or not x.get("all_raw_camera_arrays_match_old_export") for x in selected):
        raise SystemExit("prior build receipt does not verify every selected recording")
    catalogue_ids = {r["canonical_execution_id"] for r in read_csv(SOURCE_CATALOGUE)}
    rows = []
    for x in selected:
        run_id = x["run_id"]
        match = re.search(r"_task(\d+)_", run_id)
        if not match:
            raise SystemExit(f"cannot parse task token from {run_id}")
        task_id = "task" + match.group(1)
        blockers = list(BLOCKER_CODES)
        rows.append({
            "canonical_execution_id": run_id,
            "independent_source_group_id": "not_verified_from_source_receipt",
            "source_group_status": "not_verified",
            "benchmark": "LIBERO-long",
            "task_id_from_execution_id": task_id,
            "scene_or_environment_id": "not_recorded_in_case_receipt",
            "model_family": "OpenVLA-OFT",
            "checkpoint_revision": "not_recorded_in_case_receipt",
            "variant_token_from_execution_id": run_id.rsplit("_", 1)[-1],
            "requirement_version_in_prior_review_form": "r1-initial-table-support-v3-20261024",
            "requirement_configuration_status": "pending",
            "focal_object_id_in_build_receipt": x["object_id"],
            "target_protected_object_and_surface_mapping_status": "pending",
            "monitoring_interval_in_prior_review_package": "frame 10 through terminal (not request-bound)",
            "monitoring_interval_status": "pending",
            "source_path_recorded": "no; build code uses --recordings/long/{task_00|task_01}/episode_{episode}/trajectory.h5 but per-case resolved selector/root is absent from receipt",
            "source_bytes_status": "verified_at_prior_package_build; current bytes not reverified",
            "source_trajectory_sha256": x["recording_sha256"],
            "source_provenance_status": "prior_build_receipt_verified",
            "source_stat_preserved_at_build": str(bool(x["source_stat_preserved"])).lower(),
            "prior_r1_review_exposure": "yes; selected in R1 human-validation package",
            "critic_development_exposure_status": "not_verified",
            "exact_id_overlap_with_rq3_source_catalogue": "yes" if run_id in catalogue_ids else "no",
            "recorded_evidence_families_at_prior_build": "agentview/wrist video; frame references; contact records; object poses; native geometry; raw image hashes",
            "evidence_integrity_status": "verified_at_prior_package_build; current evidence bundle not present in repository",
            "drafter_evidence_binding_status": "pending",
            "project_approval_status": "pending",
            "per_record_approval_status": "not_verified",
            "independent_r1_reference_status": "pending; no intake case or frozen reference",
            "drafter_request_constructibility": "no_currently",
            "request_sha256": "",
            "admission_decision": "not_admitted",
            "blocker_codes": ";".join(blockers),
            "supporting_evidence": "evaluation/r1_v3_human_validation_20/BUILD_REPORT.json#selected_source_cases; evaluation/r1_v3_human_validation_20/build_packages.py; SOURCE_GATE_SNAPSHOT.json"
        })
    return rows


FIELDS = [
    "canonical_execution_id", "independent_source_group_id", "source_group_status", "benchmark", "task_id_from_execution_id",
    "scene_or_environment_id", "model_family", "checkpoint_revision", "variant_token_from_execution_id",
    "requirement_version_in_prior_review_form", "requirement_configuration_status",
    "focal_object_id_in_build_receipt", "target_protected_object_and_surface_mapping_status",
    "monitoring_interval_in_prior_review_package", "monitoring_interval_status", "source_path_recorded",
    "source_bytes_status", "source_trajectory_sha256", "source_provenance_status",
    "source_stat_preserved_at_build", "prior_r1_review_exposure", "critic_development_exposure_status",
    "exact_id_overlap_with_rq3_source_catalogue", "recorded_evidence_families_at_prior_build",
    "evidence_integrity_status", "drafter_evidence_binding_status", "project_approval_status",
    "per_record_approval_status", "independent_r1_reference_status", "drafter_request_constructibility",
    "request_sha256", "admission_decision", "blocker_codes", "supporting_evidence"
]


def expected_blocker_counts(rows):
    counts = Counter(code for row in rows for code in row["blocker_codes"].split(";") if code)
    return [{"blocker_code": code, "affected_recordings": str(counts[code]),
             "description": BLOCKER_DESCRIPTIONS[code]} for code in BLOCKER_CODES]


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="compare checked-in generated CSVs; write nothing")
    args = p.parse_args()
    rows = make_rows()
    blocker_rows = expected_blocker_counts(rows)
    if args.check:
        if read_csv(MATRIX) != rows:
            raise SystemExit("SOURCE_ELIGIBILITY_MATRIX.csv differs from source receipts")
        if read_csv(BLOCKERS) != blocker_rows:
            raise SystemExit("BLOCKER_COUNTS.csv differs from matrix")
        print("PASS: 20 distinct execution IDs/hashes; source-group independence not verified; 20 prior-build receipts; 0 admitted; blocker counts consistent")
    else:
        write_csv(MATRIX, FIELDS, rows)
        write_csv(BLOCKERS, ["blocker_code", "affected_recordings", "description"], blocker_rows)
        print("WROTE: 20 source rows; independent source-group IDs not verified; 0 admitted; blocker counts are overlapping")
    task_counts = Counter(row["task_id_from_execution_id"] for row in rows)
    catalogue_overlap = sum(row["exact_id_overlap_with_rq3_source_catalogue"] == "yes" for row in rows)
    print("TASK_COUNTS:", json.dumps(dict(sorted(task_counts.items())), sort_keys=True))
    print("EXACT_ID_OVERLAP_WITH_432_SOURCE_CATALOGUE:", catalogue_overlap)
    print("INDEPENDENT_SOURCE_GROUPS_VERIFIED: 0 (source receipts do not define group IDs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
