#!/usr/bin/env python3
"""CPU-only empty-manifest check; never invokes inference."""
import argparse
import csv
from pathlib import Path

REQUIRED = {
    "canonical_execution_id", "requirement_owner_approval_ref",
    "independent_r1_reference_status", "r1_adjudication_freeze_ref",
    "object_mapping_ref", "object_mapping_sha256", "configuration_path",
    "configuration_sha256", "source_manifest_path", "source_manifest_sha256",
    "source_trajectory_path", "source_trajectory_sha256", "evidence_bundle_path",
    "evidence_bundle_sha256", "retrieval_context_path", "retrieval_context_sha256",
    "critic_exposure_review_ref", "request_path", "request_sha256",
    "generation_status", "validation_status",
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-template", action="store_true")
    parser.add_argument("manifest", nargs="?", default=str(Path(__file__).with_name("DRAFTER_GENERATION_MANIFEST.csv")))
    args = parser.parse_args()
    with Path(args.manifest).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        rows = list(reader)
    missing = sorted(REQUIRED - columns)
    if missing:
        raise SystemExit("missing required columns: " + ", ".join(missing))
    if args.check_template and rows:
        raise SystemExit("template must remain empty before approvals; rows=" + str(len(rows)))
    print("manifest rows=" + str(len(rows)) + " required_columns=PASS inference=NOT_RUN")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
