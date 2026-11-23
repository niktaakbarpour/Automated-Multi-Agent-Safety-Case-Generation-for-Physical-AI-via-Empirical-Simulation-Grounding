#!/usr/bin/env python3
"""Score frozen RQ2 predictions against an explicitly supplied finalized reference.

Standard-library only. This program never searches for reference files and never
reads reviewer submissions; the caller must name the finalized adjudication CSV.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


KEY = ("case_id", "object", "source_group_id", "requirement_version")
PREDICTION_FIELDS = KEY + (
    "split",
    "applicability_prediction",
    "violation_prediction",
)
REFERENCE_FIELDS = KEY + (
    "split",
    "applicability_reference",
    "violation_reference",
    "adjudication_status",
    "eligibility",
    "exclusion_reason",
)
SPLITS = {"development_calibration", "independent_evaluation"}
APP_PREDICTIONS = {"applicable", "not_applicable", "abstain", "invalid_contract"}
VIOLATION_PREDICTIONS = {
    "violation",
    "no_violation",
    "not_applicable",
    "abstain",
    "invalid_contract",
}
APP_REFERENCES = {"applicable", "not_applicable", "unknown"}
VIOLATION_REFERENCES = {"violation", "no_violation", "not_applicable", "unscorable"}


class EvaluationError(ValueError):
    """Input violates the frozen scoring contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(required) - set(reader.fieldnames or ()))
        if missing:
            raise EvaluationError(f"{path}: missing required columns: {', '.join(missing)}")
        rows = []
        for line, row in enumerate(reader, start=2):
            clean = {name: (row.get(name) or "").strip() for name in required}
            if any(not clean[name] for name in KEY + ("split",)):
                raise EvaluationError(f"{path}:{line}: blank key or split field")
            rows.append(clean)
    return rows


def load_prediction_input(path: Path, prediction_split: str | None = None,
                          case_manifest_path: Path | None = None) -> list[dict[str, str]]:
    """Load normalized CSV or adapt the frozen checker JSON prediction array."""
    if path.suffix.lower() != ".json":
        return load_csv(path, PREDICTION_FIELDS)
    document = json.loads(path.read_text(encoding="utf-8"))
    raw = document.get("predictions") if isinstance(document, dict) else document
    if not isinstance(raw, list):
        raise EvaluationError("prediction JSON must be a list or an object with a predictions list")
    case_groups: dict[str, str] = {}
    if case_manifest_path is not None:
        manifest = json.loads(case_manifest_path.read_text(encoding="utf-8"))
        group = manifest.get("source_group_id")
        cases = manifest.get("cases", [])
        if not group or not isinstance(cases, list):
            raise EvaluationError("case manifest must contain source_group_id and cases")
        case_groups = {case["case_id"]: group for case in cases if case.get("case_id")}
    app_map = {"applies": "applicable", "applicable": "applicable",
               "not_applicable": "not_applicable", "not_established": "abstain",
               "unknown": "abstain", "abstain": "abstain", "invalid_contract": "invalid_contract"}
    violation_map = {
        "violation_observed": "violation",
        "no_violation_observed_within_validated_coverage": "no_violation",
        "not_applicable": "not_applicable",
        "insufficient_information": "abstain",
        "invalid_contract": "invalid_contract",
        "violation": "violation",
        "no_violation": "no_violation",
        "abstain": "abstain",
    }
    rows = []
    for index, record in enumerate(raw):
        if not isinstance(record, dict):
            raise EvaluationError(f"prediction JSON record {index} is not an object")
        case_id = record.get("case_id", "")
        scope = record.get("scope") if isinstance(record.get("scope"), dict) else {}
        object_name = record.get("object") or scope.get("object", "")
        group = record.get("source_group_id") or case_groups.get(case_id, "")
        split = record.get("split") or prediction_split or ""
        req = record.get("requirement_version", "")
        app = app_map.get(record.get("applicability", ""))
        prediction = violation_map.get(record.get("prediction", ""))
        if not req and case_manifest_path is not None:
            req = json.loads(case_manifest_path.read_text(encoding="utf-8")).get("requirement_version", "")
        row = {
            "case_id": case_id,
            "object": object_name,
            "source_group_id": group,
            "requirement_version": req,
            "split": split,
            "applicability_prediction": app or "",
            "violation_prediction": prediction or "",
        }
        if not all(row[field] for field in PREDICTION_FIELDS):
            raise EvaluationError(f"prediction JSON record {index} lacks required mapped keys/values")
        rows.append(row)
    return rows


def keyed_rows(rows: list[dict[str, str]], label: str) -> dict[tuple[str, ...], dict[str, str]]:
    result: dict[tuple[str, ...], dict[str, str]] = {}
    case_object_groups: dict[tuple[str, str, str], tuple[str, ...]] = {}
    splits_by_group: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        key = tuple(row[field] for field in KEY)
        if key in result:
            raise EvaluationError(f"duplicate {label} key: {key}")
        group_key = (row["case_id"], row["object"], row["requirement_version"])
        prior = case_object_groups.get(group_key)
        if prior is not None and prior != key:
            raise EvaluationError(f"conflicting source-group assignment in {label}: {group_key}")
        case_object_groups[group_key] = key
        splits_by_group[row["source_group_id"]].add(row["split"])
        result[key] = row
    for group, splits in splits_by_group.items():
        if len(splits) != 1:
            raise EvaluationError(f"source group appears in multiple {label} splits: {group}")
    return result


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def confusion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(r["reference_violation"] == "violation" and r["prediction_violation"] == "violation" for r in rows)
    fp = sum(r["reference_violation"] == "no_violation" and r["prediction_violation"] == "violation" for r in rows)
    tn = sum(r["reference_violation"] == "no_violation" and r["prediction_violation"] == "no_violation" for r in rows)
    fn = sum(r["reference_violation"] == "violation" and r["prediction_violation"] == "no_violation" for r in rows)
    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "decided_binary_pairs": tp + fp + tn + fn,
        "accuracy": ratio(tp + tn, tp + fp + tn + fn),
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
    }


def summarize(rows: list[dict[str, Any]], split: str) -> dict[str, Any]:
    eligible = [r for r in rows if r["split"] == split and r["eligibility"] == "included"]
    determinate_app = [r for r in eligible if r["reference_applicability"] in {"applicable", "not_applicable"}]
    decided_app = [r for r in determinate_app if r["prediction_applicability"] in {"applicable", "not_applicable"}]
    app_correct = sum(r["reference_applicability"] == r["prediction_applicability"] for r in decided_app)

    applicable_refs = [r for r in eligible if r["reference_applicability"] == "applicable"
                       and r["reference_violation"] in {"violation", "no_violation"}]
    violation_pairs = [r for r in applicable_refs if r["prediction_violation"] in {"violation", "no_violation"}
                       and r["prediction_applicability"] == "applicable"]
    matrix = confusion(violation_pairs)

    app_prediction_counts = Counter(r["prediction_applicability"] for r in eligible)
    violation_prediction_counts = Counter(r["prediction_violation"] for r in eligible)
    reference_app_counts = Counter(r["reference_applicability"] for r in eligible)
    reference_violation_counts = Counter(r["reference_violation"] for r in eligible)
    statuses = Counter(r["score_status"] for r in eligible)
    all_statuses = Counter(r["score_status"] for r in rows if r["split"] == split)
    groups = sorted({r["source_group_id"] for r in eligible})

    by_group: dict[str, Any] = {}
    for group in groups:
        group_rows = [r for r in eligible if r["source_group_id"] == group]
        group_decided = [r for r in group_rows if r["score_status"] == "scored_binary"]
        by_group[group] = {
            "joined_units": len(group_rows),
            "applicability_accuracy_conditional_on_decision": _app_accuracy(group_rows),
            "violation": confusion(group_decided),
        }

    return {
        "split": split,
        "joined_units": len(eligible),
        "independent_source_groups": len(groups),
        "source_group_ids": groups,
        "applicability": {
            "reference_applicable": reference_app_counts["applicable"],
            "reference_not_applicable": reference_app_counts["not_applicable"],
            "reference_unknown": reference_app_counts["unknown"],
            "decided": len(decided_app),
            "abstained_or_invalid": len(determinate_app) - len(decided_app),
            "decision_coverage": ratio(len(decided_app), len(determinate_app)),
            "agreement": {"numerator": app_correct, "denominator": len(decided_app), "value": ratio(app_correct, len(decided_app))},
            "accuracy": {"numerator": app_correct, "denominator": len(decided_app), "value": ratio(app_correct, len(decided_app))},
        },
        "violation_detection": {
            "eligible_applicable_references": len(applicable_refs),
            "binary_decisions": len(violation_pairs),
            "decision_coverage": ratio(len(violation_pairs), len(applicable_refs)),
            "abstentions_or_nonbinary_predictions": len(applicable_refs) - len(violation_pairs),
            **matrix,
            "abstentions_by_reference": {
                label: sum(r["prediction_violation"] in {"abstain", "invalid_contract", "not_applicable"}
                           or r["prediction_applicability"] != "applicable"
                           for r in applicable_refs if r["reference_violation"] == label)
                for label in ("violation", "no_violation")
            },
        },
        "not_applicable_and_excluded": {
            "reference_not_applicable_units": reference_app_counts["not_applicable"],
            "prediction_not_applicable_units": app_prediction_counts["not_applicable"],
            "reference_violation_not_applicable_units": reference_violation_counts["not_applicable"],
            "reference_violation_unscorable_units": reference_violation_counts["unscorable"],
            "excluded_reference_units": all_statuses["excluded"],
            "excluded_reference_reason_counts": dict(sorted(Counter(
                r["exclusion_reason"] or "unspecified" for r in rows
                if r["split"] == split and r["eligibility"] == "excluded").items())),
            "unknown_or_unscorable_reference_units": statuses["reference_unscorable"],
        },
        "prediction_status_counts": dict(sorted(app_prediction_counts.items())),
        "violation_prediction_counts": dict(sorted(violation_prediction_counts.items())),
        "score_status_counts": dict(sorted(statuses.items())),
        "per_source_group": by_group,
        "inference": "descriptive only; source execution group is the independent unit; no case-level inferential uncertainty computed",
    }


def _app_accuracy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decided = [r for r in rows if r["reference_applicability"] in {"applicable", "not_applicable"}
               and r["prediction_applicability"] in {"applicable", "not_applicable"}]
    correct = sum(r["reference_applicability"] == r["prediction_applicability"] for r in decided)
    return {"numerator": correct, "denominator": len(decided), "value": ratio(correct, len(decided))}


def evaluate(prediction_rows: list[dict[str, str]], reference_rows: list[dict[str, str]],
             prediction_sha256: str, reference_sha256: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    predictions = keyed_rows(prediction_rows, "prediction")
    references = keyed_rows(reference_rows, "reference")
    pred_keys, ref_keys = set(predictions), set(references)
    missing_references = sorted(pred_keys - ref_keys)
    missing_predictions = sorted(ref_keys - pred_keys)
    if missing_references or missing_predictions:
        raise EvaluationError(json.dumps({
            "missing_reference_joins": missing_references,
            "missing_prediction_joins": missing_predictions,
        }, sort_keys=True))

    groups_across_splits: dict[str, set[str]] = defaultdict(set)
    for source in (predictions, references):
        for row in source.values():
            groups_across_splits[row["source_group_id"]].add(row["split"])
    for group, splits in groups_across_splits.items():
        if len(splits) != 1:
            raise EvaluationError(f"source group leaks across development/evaluation splits: {group}")

    scored: list[dict[str, Any]] = []
    for key in sorted(predictions):
        pred, ref = predictions[key], references[key]
        for row, label in ((pred, "prediction"), (ref, "reference")):
            if row["split"] not in SPLITS:
                raise EvaluationError(f"unknown {label} split for {key}: {row['split']}")
        if pred["split"] != ref["split"]:
            raise EvaluationError(f"split mismatch for key: {key}")
        if pred["applicability_prediction"] not in APP_PREDICTIONS:
            raise EvaluationError(f"invalid applicability prediction for {key}")
        if pred["violation_prediction"] not in VIOLATION_PREDICTIONS:
            raise EvaluationError(f"invalid violation prediction for {key}")
        if ref["adjudication_status"] != "finalized":
            raise EvaluationError(f"reference is not finalized for {key}")
        if ref["eligibility"] not in {"included", "excluded"}:
            raise EvaluationError(f"invalid reference eligibility for {key}")
        if ref["applicability_reference"] not in APP_REFERENCES:
            raise EvaluationError(f"invalid applicability reference for {key}")
        if ref["violation_reference"] not in VIOLATION_REFERENCES:
            raise EvaluationError(f"invalid violation reference for {key}")
        if ref["applicability_reference"] == "not_applicable" and ref["violation_reference"] not in {"not_applicable", "unscorable"}:
            raise EvaluationError(f"not-applicable reference has binary violation label for {key}")
        if ref["applicability_reference"] == "applicable" and ref["violation_reference"] == "not_applicable":
            raise EvaluationError(f"applicable reference has not-applicable violation label for {key}")

        if ref["eligibility"] == "excluded":
            status = "excluded"
        elif ref["applicability_reference"] == "unknown" or ref["violation_reference"] == "unscorable":
            status = "reference_unscorable"
        elif ref["applicability_reference"] == "not_applicable":
            status = "not_applicable"
        elif pred["applicability_prediction"] != "applicable":
            status = "checker_not_applicable_mismatch" if pred["applicability_prediction"] == "not_applicable" else "abstained_or_invalid"
        elif pred["violation_prediction"] in {"violation", "no_violation"}:
            status = "scored_binary"
        else:
            status = "abstained_or_invalid"

        app_decided = pred["applicability_prediction"] in {"applicable", "not_applicable"}
        app_match = (pred["applicability_prediction"] == ref["applicability_reference"]
                     if ref["applicability_reference"] in {"applicable", "not_applicable"} and app_decided else None)
        binary_scored = status == "scored_binary"
        scored.append({
            **{field: pred[field] for field in KEY},
            "split": pred["split"],
            "prediction_applicability": pred["applicability_prediction"],
            "reference_applicability": ref["applicability_reference"],
            "applicability_match": app_match,
            "prediction_violation": pred["violation_prediction"],
            "reference_violation": ref["violation_reference"],
            "eligibility": ref["eligibility"],
            "exclusion_reason": ref["exclusion_reason"],
            "score_status": status,
            "violation_scored": binary_scored,
            "violation_correct": (pred["violation_prediction"] == ref["violation_reference"] if binary_scored else None),
        })

    summaries = {split: summarize(scored, split) for split in sorted(SPLITS)}
    summary = {
        "protocol": "RQ2 final scoring v1",
        "prediction_sha256": prediction_sha256,
        "finalized_reference_sha256": reference_sha256,
        "joined_units": len(scored),
        "split_summaries": summaries,
        "global_source_group_split_check": "PASS",
        "note": "Abstentions, invalid contracts, and applicability mismatches are never converted to negative predictions or correct negatives.",
    }
    return scored, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else list(KEY) + ["split", "score_status"]
    with (output_dir / "per_case.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else str(row.get(k)).lower() if isinstance(row.get(k), bool) else row.get(k) for k in fields})
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="immutable checker predictions CSV or JSON")
    parser.add_argument("--prediction-sha256", required=True, help="expected SHA-256 from the frozen output seal")
    parser.add_argument("--prediction-split", choices=sorted(SPLITS), help="assign this split to raw checker JSON")
    parser.add_argument("--case-manifest", type=Path, help="authorized source manifest for raw checker JSON missing source IDs")
    parser.add_argument("--finalized-references", required=True, type=Path, help="separate finalized adjudicated-reference CSV")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    actual_hash = sha256_file(args.predictions)
    if actual_hash.lower() != args.prediction_sha256.lower():
        raise SystemExit(f"prediction SHA-256 mismatch: expected {args.prediction_sha256}, got {actual_hash}")
    # This is the only reference path read; no discovery/globbing is performed.
    reference_hash = sha256_file(args.finalized_references)
    rows, summary = evaluate(load_prediction_input(args.predictions, args.prediction_split, args.case_manifest),
                             load_csv(args.finalized_references, REFERENCE_FIELDS),
                             actual_hash, reference_hash)
    write_outputs(rows, summary, args.output_dir)
    print(json.dumps({"status": "complete", "joined_units": len(rows), "output_dir": str(args.output_dir)}, sort_keys=True))


if __name__ == "__main__":
    main()
