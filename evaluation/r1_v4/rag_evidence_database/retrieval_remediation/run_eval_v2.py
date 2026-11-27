"""Resumable actual-retrieval evaluation for requested-obligations planner v2.

This entry point is deliberately separate from frozen ``run_eval.py``. It
executes the v2 retriever for each selected development query and records the
planner and retrieval layers independently. Physical eligibility is always
NOT_EVALUATED.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import platform
import sys
import time
import uuid
from pathlib import Path

from .bundle import BundleRequest
from .bundle_v2 import RequestedObligationsRetriever
from .store import BundleStore

HARNESS_VERSION = "requested-obligations-retrieval-replay-1.0.0"
HERE = Path(__file__).resolve().parent
DEFAULT_DATASET = HERE / "FROZEN_HOLDOUT_DATASET.jsonl"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_identity():
    files = ("run_eval_v2.py", "bundle_v2.py", "requested_obligations_v2.py", "bundle.py", "store.py", "planner.py")
    source_hashes = {name: file_sha256(HERE / name) for name in files}
    try:
        commit = subprocess.run(["git", "-C", str(HERE), "rev-parse", "HEAD"], check=True,
                                capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "UNAVAILABLE"
    from importlib import metadata
    packages = ("numpy", "h5py", "jsonschema", "scipy")
    runtime = {"python": sys.version, "platform": platform.platform(),
               "packages": {name: metadata.version(name) for name in packages if _has_dist(name)}}
    return {"source_commit": commit, "source_file_sha256": source_hashes, "runtime": runtime}


def _has_dist(name):
    from importlib import metadata
    try: metadata.version(name); return True
    except metadata.PackageNotFoundError: return False


def read_rows(path: Path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ids = [row.get("id") for row in rows]
    if not rows or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError("reference dataset must contain rows with non-empty case IDs")
    if len(ids) != len(set(ids)):
        raise ValueError("reference dataset contains duplicate case IDs")
    return rows


def _check_hash(path: Path, expected: str, label: str):
    if not path.is_file():
        raise FileNotFoundError(f"{label} is not a readable file: {path}")
    actual = file_sha256(path)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")
    return actual


def _request(row):
    fields = dict(row.get("request", {}))
    # Test/development metadata in the reference row is not passed to retrieval.
    return BundleRequest(query=row["query"], **fields)


def _sample_audit(response, row):
    errors, checks = [], 0
    expected_scope = row.get("request", {})
    retrieved = []
    verified = set()
    references = {(entry.get("path"), entry.get("sha256")) for entry in row.get("source_artifacts", [])}
    expected_frames = row.get("reference_frame_indices")
    if expected_scope.get("frame_interval") is not None:
        lo, hi = expected_scope["frame_interval"]
        expected_frames = list(range(lo, hi + 1))
    resolved_scope = response.get("resolved_scope", {})
    for key in ("execution_id", "task_id", "variant_id"):
        wanted = expected_scope.get(key)
        if wanted is not None and resolved_scope.get(key) != wanted:
            errors.append("response_scope:" + key)
    groups = response.get("groups")
    if not isinstance(groups, list):
        return ["groups_not_list"], 0, []
    for group in groups:
        if not isinstance(group, dict):
            errors.append("invalid_group")
            continue
        retrieved.append(group.get("family"))
        family = group.get("family")
        if family not in response.get("requested_families", []):
            errors.append("unrequested_family_returned")
        for item in group.get("items", []):
            if item.get("family", family) != family:
                errors.append("citation_family_mismatch")
            for key in ("execution_id", "task_id", "variant_id"):
                wanted = expected_scope.get(key)
                if wanted is not None and item.get(key) != wanted:
                    errors.append("scope:" + key)
            if item.get("integrity_status") != "verified_source":
                errors.append("citation_integrity")
            artifact = item.get("source_artifact", {})
            if not artifact.get("path") or not artifact.get("sha256"):
                errors.append("citation_provenance_missing")
            elif references and (artifact.get("path"), artifact.get("sha256")) not in references:
                errors.append("citation_source_not_bound_to_reference")
            matched_reference = False
            value = item.get("value", {})
            if expected_frames is not None and value.get("saved_frame_index") is not None and value["saved_frame_index"] not in expected_frames:
                errors.append("sample_outside_reference_scope")
            for sample in item.get("samples", []):
                refs = row.get("reference_samples", {}).get(family, [])
                ref = next((candidate for candidate in refs if candidate.get("frame") == sample.get("saved_frame_index")), None)
                if expected_frames is not None and sample.get("saved_frame_index") not in expected_frames:
                    errors.append("sample_outside_reference_scope")
                if ref is not None:
                    matched_reference = True
                    checks += 1
                    if (sample.get("value") != ref.get("value") or sample.get("dtype") != ref.get("dtype")
                            or sample.get("source_selector") != ref.get("selector")):
                        errors.append("value_frame_or_selector_mismatch")
            if matched_reference:
                verified.add(family)
    for family, family_refs in row.get("reference_samples", {}).items():
        if family in response.get("requested_families", []):
            observed = {sample.get("saved_frame_index") for group in groups if isinstance(group, dict) and group.get("family") == family
                        for item in group.get("items", []) for sample in item.get("samples", [])}
            if {entry.get("frame") for entry in family_refs} - observed:
                errors.append("reference_samples_missing:" + family)
    for family, expected in row.get("reference_metadata", {}).items():
        for group in groups:
            if not isinstance(group, dict) or group.get("family") != family:
                continue
            for item in group.get("items", []):
                value = item.get("value", {})
                if family == "recorded_time":
                    matched = (value.get("simulator_endpoint_seconds") == expected.get("simulator_endpoint_seconds")
                               and value.get("recorder_host_wall_ns") == expected.get("wall_ns")
                               and value.get("saved_frame_index") in (row.get("reference_frame_indices") or [value.get("saved_frame_index")])
                               and value.get("synchronized_physical_instant") is False)
                else:
                    fields = ("object_id", "root_body", "body_id", "collision_geom_ids") if family == "geometry_identity" else ("body_name", "geom_name")
                    matched = all(value.get(key) == expected.get(key) for key in fields)
                if matched:
                    verified.add(family)
                else:
                    errors.append("reference_metadata_mismatch:" + family)
    return sorted(set(errors)), checks, sorted(verified)


def evaluate_case(row, retriever):
    started = time.perf_counter()
    record = {
        "case_id": row["id"], "query": row["query"],
        "execution_id": row.get("request", {}).get("execution_id"),
        "reference_expected_families": row.get("expected_families", []),
        "physical_evidence_eligibility": "NOT_EVALUATED",
        "attempt_status": "ATTEMPTED",
    }
    try:
        response = retriever.retrieve(_request(row), mode="bundle")
        record["response"] = response
        plan = response.get("interpretation") or {}
        plan_status = response.get("obligation_plan_status", plan.get("obligation_plan_status", plan.get("status", "UNKNOWN")))
        interpretation_status = response.get("query_interpretation_status", plan.get("query_interpretation_status", "UNKNOWN"))
        requested = response.get("requested_families", plan.get("families", [])) or []
        groups = response.get("groups", [])
        returned = [g.get("family") for g in groups if isinstance(g, dict)]
        available = [g.get("family") for g in groups if isinstance(g, dict) and g.get("status") == "AVAILABLE"]
        expected = list(row.get("expected_families", []))
        errors, numeric_checks, audited_families = _sample_audit(response, row)
        missing_expected = sorted(set(expected) - set(available))
        missing_plan = sorted(set(expected) - set(requested))
        missing_planned = sorted(set(requested) - set(available))
        claimed_complete = response.get("retrieval_completeness_status", response.get("completeness_status")) == "COMPLETE WITHIN VERIFIED CONTRACT"
        reference_families = set(row.get("reference_samples", {})) | set(row.get("reference_metadata", {}))
        reference_verified = set(expected).issubset(set(audited_families)) and set(expected).issubset(reference_families)
        verified_complete = (bool(expected) and not missing_expected and not missing_plan and not missing_planned
                             and not errors and plan_status == "COMPLETE" and reference_verified)
        record.update({
            "query_interpretation_status": interpretation_status,
            "requested_obligations": plan.get("measurement_obligations", []),
            "temporal_obligations": plan.get("temporal_obligations", []),
            "unresolved_obligations": plan.get("unresolved_obligations", []),
            "obligation_plan_status": plan_status,
            "planner_complete": plan_status == "COMPLETE",
            "requested_families": requested,
            "groups": groups,
            "retrieved_families": returned,
            "available_families": available,
            "retrieval_status": response.get("retrieval_completeness_status", response.get("completeness_status", "UNKNOWN")),
            "retrieval_complete": claimed_complete and verified_complete,
            "claimed_complete": claimed_complete,
            "false_complete": claimed_complete and not verified_complete,
            "missing_expected_families": missing_expected,
            "expected_families_missing_from_plan": missing_plan,
            "planned_families_missing_from_retrieval": missing_planned,
            "citation_or_reference_errors": errors,
            "reference_sample_checks": numeric_checks,
            "reference_verified_families": audited_families,
            "reference_verification_complete": reference_verified,
            "ambiguity": interpretation_status == "AMBIGUOUS" or plan_status == "AMBIGUOUS",
            "unsupported": response.get("completeness_status") == "UNSUPPORTED" or plan_status == "INCOMPLETE" and bool(plan.get("unsupported")),
            "abstention": response.get("completeness_status") in ("AMBIGUOUS", "UNSUPPORTED", "UNAVAILABLE", "INVALID SCOPE"),
            "execution_error": None,
        })
    except Exception as exc:  # record the query attempt; never mislabel an execution error as a result
        record.update({"retrieval_status": "EXECUTION_ERROR", "retrieval_complete": False,
                       "claimed_complete": False, "false_complete": False,
                       "planner_complete": False, "query_interpretation_status": "NOT_RETURNED",
                       "obligation_plan_status": "NOT_RETURNED", "requested_obligations": [],
                       "temporal_obligations": [], "unresolved_obligations": [],
                       "requested_families": [], "groups": [], "retrieved_families": [],
                       "available_families": [], "missing_expected_families": row.get("expected_families", []),
                       "expected_families_missing_from_plan": row.get("expected_families", []),
                       "planned_families_missing_from_retrieval": [],
                       "citation_or_reference_errors": [], "reference_sample_checks": 0,
                       "ambiguity": False, "unsupported": False, "abstention": False,
                       "execution_error": {"type": type(exc).__name__, "message": str(exc)[:2000]}})
    record["latency_seconds"] = time.perf_counter() - started
    record["record_sha256"] = canonical_sha(record)
    return record


def _write_json_atomic(path: Path, value):
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    os.replace(temp, path)


def _summarize(records):
    n = len(records)
    def count(key): return sum(bool(row.get(key)) for row in records)
    obligations = sum(len(row.get("reference_expected_families", [])) for row in records)
    covered = sum(len(set(row.get("reference_expected_families", [])) - set(row.get("missing_expected_families", []))) for row in records)
    return {
        "attempted_queries": n,
        "planner_complete": count("planner_complete"),
        "retrieval_complete_verified": count("retrieval_complete"),
        "claimed_complete": count("claimed_complete"),
        "false_complete": count("false_complete"),
        "ambiguous": count("ambiguity"), "unsupported": count("unsupported"),
        "abstentions": count("abstention"),
        "execution_errors": sum(row.get("retrieval_status") == "EXECUTION_ERROR" for row in records),
        "reference_value_or_scope_errors": sum(bool(row.get("citation_or_reference_errors")) for row in records),
        "missing_expected_family_cases": sum(bool(row.get("missing_expected_families")) for row in records),
        "expected_family_obligations": obligations,
        "available_expected_family_obligations": covered,
        "expected_family_coverage": covered / obligations if obligations else None,
        "partial_retrieval_responses": sum(row.get("retrieval_status") == "PARTIAL" for row in records),
        "mean_latency_seconds": sum(float(row.get("latency_seconds", 0)) for row in records) / n if n else None,
        "physical_evidence_eligibility": "NOT_EVALUATED",
    }


def _write_reports(out: Path, records, manifest):
    ordered = sorted(records, key=lambda item: item["case_id"])
    _write_json_atomic(out / "PER_CASE.json", ordered)
    failures = [r for r in ordered if r.get("false_complete") or r.get("execution_error") or r.get("missing_expected_families") or r.get("planned_families_missing_from_retrieval") or r.get("citation_or_reference_errors") or not r.get("planner_complete")]
    fields = ["case_id", "execution_id", "query_interpretation_status", "obligation_plan_status", "retrieval_status", "claimed_complete", "false_complete", "missing_expected_families", "planned_families_missing_from_retrieval", "citation_or_reference_errors", "execution_error"]
    tmp = out / ("FAILURE_ANALYSIS.csv." + uuid.uuid4().hex + ".tmp")
    with tmp.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for r in failures:
            writer.writerow({k: json.dumps(r.get(k), sort_keys=True) if isinstance(r.get(k), (list, dict)) else r.get(k) for k in fields})
    os.replace(tmp, out / "FAILURE_ANALYSIS.csv")
    summary = _summarize(ordered)
    summary.update(run_id=manifest["run_id"], dataset_cases=len(manifest["selected_case_ids"]), completed_case_records=len(ordered))
    _write_json_atomic(out / "AGGREGATE.json", summary)
    manifest["case_records"] = {r["case_id"]: r["record_sha256"] for r in ordered}
    manifest["aggregate_sha256"] = file_sha256(out / "AGGREGATE.json")
    _write_json_atomic(out / "PROVENANCE_MANIFEST.json", manifest)


class _FailedRetriever:
    def __init__(self, error): self.error = error
    def retrieve(self, request, mode="bundle"): raise RuntimeError(self.error)
    def close(self): pass


def run(*, database, database_sha256, catalogue, catalogue_sha256, source_root,
        encoder, encoder_sha256, encoder_revision, references, references_sha256,
        output, case_ids=None, limit=None, retriever_factory=None):
    database, catalogue, source_root = Path(database), Path(catalogue), Path(source_root)
    encoder, references, output = Path(encoder), Path(references), Path(output)
    # Verify all run-defining inputs before opening the database.
    hashes = {
        "database_sha256": _check_hash(database, database_sha256, "database"),
        "catalogue_sha256": _check_hash(catalogue, catalogue_sha256, "catalogue"),
        "encoder_sha256": _check_hash(encoder, encoder_sha256, "encoder"),
        "reference_dataset_sha256": _check_hash(references, references_sha256, "reference dataset"),
    }
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root is not a directory: {source_root}")
    rows = read_rows(references)
    root = source_root.resolve()
    for row in rows:
        for artifact in row.get("source_artifacts", []):
            source = Path(artifact["path"])
            if not source.is_absolute() or not source.resolve(strict=False).is_relative_to(root):
                raise ValueError(f"source artifact falls outside declared source root: {row['id']}")
    by_id = {row["id"]: row for row in rows}
    selected = list(case_ids) if case_ids else [row["id"] for row in rows]
    if len(selected) != len(set(selected)):
        raise ValueError("selected case IDs contain duplicates")
    unknown = sorted(set(selected) - set(by_id))
    if unknown:
        raise ValueError("unknown case IDs: " + ", ".join(unknown))
    if limit is not None:
        if limit < 1: raise ValueError("limit must be positive")
        selected = selected[:limit]
    config = {"harness_version": HARNESS_VERSION, "retriever": "RequestedObligationsRetriever", "mode": "bundle",
              "planner_version": "requested-obligations-2.0.0", "encoder_revision": encoder_revision,
              "encoder_used_by_bundle_mode": False,
              "source_root": str(source_root.resolve()), "hashes": hashes,
              "selected_case_ids": selected, **source_identity()}
    config_sha = canonical_sha(config)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "PROVENANCE_MANIFEST.json"
    manifest = {**config, "configuration_sha256": config_sha, "run_id": output.name,
                "physical_evidence_eligibility": "NOT_EVALUATED",
                "reference_kind": "frozen exposed development references; not independent evaluation"}
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous.get("configuration_sha256") != config_sha:
            raise ValueError("resume rejected: output directory is bound to different inputs/configuration")
        manifest = previous
    else:
        existing = list(output.glob("case-*.json"))
        if existing: raise ValueError("output has case records but no provenance manifest; refusing unsafe resume")
        _write_json_atomic(manifest_path, manifest)
    lock_path = output / ".replay.lock"
    with lock_path.open("a+") as lock:
        import fcntl
        try: fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise RuntimeError("another replay process holds the output lock") from exc
        try:
            if retriever_factory is None:
                retriever = RequestedObligationsRetriever(
                    catalogue, catalogue_sha256,
                    store=BundleStore(database, expected_sha256=database_sha256))
            else:
                retriever = retriever_factory(catalogue, catalogue_sha256)
        except Exception as exc:
            # Keep the selected query attempts visible even when opening a
            # verified database/catalogue fails before retrieval starts.
            retriever = _FailedRetriever(f"retriever initialization failed: {type(exc).__name__}: {exc}")
        try:
            for case_id in selected:
                path = output / ("case-" + case_id + ".json")
                if path.exists():
                    record = json.loads(path.read_text())
                    if record.get("case_id") != case_id or record.get("input_binding_sha256") != canonical_sha([by_id[case_id], config_sha]):
                        raise ValueError(f"completed record binding mismatch for {case_id}")
                    expected_record_hash = record.get("record_sha256")
                    observed_record_hash = canonical_sha({k: v for k, v in record.items() if k != "record_sha256"})
                    if expected_record_hash != observed_record_hash:
                        raise ValueError(f"completed record content hash mismatch for {case_id}")
                    continue
                record = evaluate_case(by_id[case_id], retriever)
                record["input_binding_sha256"] = canonical_sha([by_id[case_id], config_sha])
                record["record_sha256"] = canonical_sha({k: v for k, v in record.items() if k != "record_sha256"})
                _write_json_atomic(path, record)
                records = [json.loads((output / ("case-" + cid + ".json")).read_text()) for cid in selected if (output / ("case-" + cid + ".json")).exists()]
                _write_reports(output, records, dict(manifest))
        finally:
            retriever.close()
    records = [json.loads((output / ("case-" + cid + ".json")).read_text()) for cid in selected]
    _write_reports(output, records, dict(manifest))
    return _summarize(records)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "catalogue", "source-root", "encoder", "references", "output"):
        parser.add_argument("--" + name, required=True)
    for name in ("database-sha256", "catalogue-sha256", "encoder-sha256", "references-sha256", "encoder-revision"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--limit", type=int)
    args = vars(parser.parse_args(argv))
    result = run(database=args.pop("database"), database_sha256=args.pop("database_sha256"),
                 catalogue=args.pop("catalogue"), catalogue_sha256=args.pop("catalogue_sha256"),
                 source_root=args.pop("source_root"), encoder=args.pop("encoder"),
                 encoder_sha256=args.pop("encoder_sha256"), encoder_revision=args.pop("encoder_revision"),
                 references=args.pop("references"), references_sha256=args.pop("references_sha256"),
                 output=args.pop("output"), case_ids=args.pop("case_ids"), limit=args.pop("limit"))
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
