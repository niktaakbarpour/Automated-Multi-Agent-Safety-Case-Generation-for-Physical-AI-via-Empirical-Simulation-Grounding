"""Conservative offline adjudication of saved planner-v2 retrieval responses.

Version 3 separates demonstrated retrieval failures from incomplete reference
coverage and verifies cited source bytes/selectors without rerunning retrieval.
Unsupported reference schemas remain unverifiable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

VERSION = "offline-retrieval-adjudication-3.0.0"


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _same(a, b) -> bool:
    return json.dumps(a, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(
        b, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _json_subset(actual, claimed) -> bool:
    if isinstance(claimed, dict):
        return isinstance(actual, dict) and all(k in actual and _json_subset(actual[k], v) for k, v in claimed.items())
    if isinstance(claimed, list):
        return isinstance(actual, list) and len(actual) == len(claimed) and all(
            _json_subset(a, c) for a, c in zip(actual, claimed)
        )
    return _same(actual, claimed)


def _inside(path: Path, root: Path) -> bool:
    try:
        return path.resolve(strict=True).is_relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        return False


def _h5_selector_check(path: Path, selector: str, expected=None):
    import h5py
    import numpy as np

    key = selector.lstrip("/")
    with h5py.File(path, "r") as h5:
        if key not in h5:
            return False, "selector_missing", None
        node = h5[key]
        if expected is None:
            return True, "selector_exists", node
        if not isinstance(node, h5py.Dataset):
            return False, "selector_not_dataset", node
        value = node[()]
        actual = np.asarray(value)
        want = np.asarray(expected)
        if actual.shape != want.shape:
            return False, "shape_mismatch", node
        if actual.dtype.kind in "biufc" and want.dtype.kind in "biufc":
            ok = bool(np.array_equal(actual, want, equal_nan=True))
        else:
            ok = actual.tolist() == want.tolist()
        return (ok, "value_match" if ok else "value_mismatch", node)



def _py(value):
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode()
    if isinstance(value, tuple):
        return [_py(x) for x in value]
    if isinstance(value, list):
        return [_py(x) for x in value]
    return value


def _h5_metadata_item(item, family):
    import h5py
    import numpy as np

    art = item.get("source_artifact") or {}
    path = Path(art.get("path", ""))
    selector = (art.get("selector") or "").lstrip("/")
    value = item.get("value") or {}
    with h5py.File(path, "r") as h5:
        if selector not in h5:
            return False, "metadata_selector_missing"
        node = h5[selector]
        if not isinstance(node, h5py.Group):
            return False, "metadata_selector_not_group"
        if family == "recorded_time":
            frame = value.get("saved_frame_index")
            if selector != "frames/" + f"{int(frame):06d}":
                return False, "recorded_time_frame_selector_mismatch"
            if float(node["simulator/time/value"][()]) != value.get("simulator_endpoint_seconds"):
                return False, "recorded_time_simulator_value_mismatch"
            attrs = node.attrs
            mapping = {
                "wall_time_ns": value.get("recorder_host_wall_ns"),
                "monotonic_ns": value.get("recorder_host_monotonic_ns"),
                "utc": value.get("recorder_utc"),
            }
            if any(k not in attrs or _py(attrs[k]) != v for k, v in mapping.items()):
                return False, "recorded_time_clock_value_mismatch"
            return True, "recorded_frame_values_match"
        if family == "action_metadata":
            step = value.get("policy_step")
            if selector != "policy_steps/" + f"{int(step):06d}":
                return False, "action_step_selector_mismatch"
            if any(k not in node.attrs or _py(node.attrs[k]) != v
                   for k, v in (value.get("policy_attributes") or {}).items()):
                return False, "action_policy_attributes_mismatch"
            labels = value.get("transition_labels")
            if labels:
                transition = h5.get("transitions/" + f"{int(step):06d}")
                if transition is None:
                    return False, "action_transition_missing"
                for key, got in labels.items():
                    if key not in transition or not _same(_py(transition[key]["value"][()]), got):
                        return False, "action_transition_label_mismatch"
            ref = value.get("executed_action_reference")
            if ref:
                key = ref.get("selector", "").lstrip("/")
                if key not in h5 or list(h5[key].shape) != ref.get("shape") or str(h5[key].dtype) != ref.get("dtype"):
                    return False, "action_reference_selector_mismatch"
            return True, "policy_step_fields_match_source"
        if family == "inference_metadata":
            chunk = int(value.get("chunk_id", -1))
            if selector != "inference_calls/" + f"{chunk:06d}":
                return False, "inference_chunk_selector_mismatch"
            attrs = node.attrs
            recorded = value.get("recorded_attributes")
            if not isinstance(recorded, dict) or any(k not in attrs or _py(attrs[k]) != v for k, v in recorded.items()):
                return False, "inference_attributes_mismatch"
            step = int(recorded.get("step", -1))
            if int(value.get("policy_input_saved_frame", -1)) != 10 + step:
                return False, "inference_policy_input_frame_mismatch"
            return True, "inference_call_fields_match_source"
    return False, "unsupported_hdf5_metadata_family"


def _source_bind(row, item, family, catalogue, root, database_sha, hash_cache):
    art = item.get("source_artifact") or {}
    raw_path, claimed_sha = art.get("path"), art.get("sha256")
    if not raw_path or not claimed_sha:
        return False, "citation_missing"
    path = Path(raw_path)
    if not _inside(path, root):
        return False, "outside_source_root"
    try:
        key = str(path)
        if key not in hash_cache:
            hash_cache[key] = file_sha256(path)
        actual_sha = hash_cache[key]
    except (OSError, PermissionError):
        return False, "source_unreadable"
    if actual_sha != claimed_sha:
        return False, "source_hash_mismatch"

    frozen = {(x.get("path"), x.get("sha256")) for x in row.get("source_artifacts", [])}
    if (raw_path, claimed_sha) in frozen:
        return True, "frozen_source_pair"

    ex = row.get("request", {}).get("execution_id")
    cat = catalogue.get(ex, {})
    if family == "execution_metadata":
        if raw_path != cat.get("metadata_path") or claimed_sha != cat.get("metadata_sha256"):
            return False, "metadata_not_catalogue_bound"
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return False, "metadata_json_unreadable"
        projection = item.get("value") or {}
        allowed = ("source_commit", "versions", "python", "platform", "checkpoint_revision",
                   "checkpoint_weight_sha256", "control_frequency_hz", "settling_steps")
        if any(projection.get(k) != value.get(k) for k in allowed):
            return False, "metadata_projection_mismatch"
        if projection.get("historical_running_binary_attested") is not False:
            return False, "metadata_attestation_overclaim"
        return (True, "catalogue_metadata_anchor")

    if family == "main_table_identity":
        m = cat.get("main_table") or {}
        if (m.get("execution_id") != ex or
                m.get("task_id") != row.get("request", {}).get("task_id") or
                m.get("variant_id") != row.get("request", {}).get("variant_id")):
            return False, "main_table_catalogue_scope_mismatch"
        selector = art.get("selector", "")
        prefix = "/rows/execution_id="
        if not selector.startswith(prefix) or selector[len(prefix):] != ex:
            return False, "main_table_selector_mismatch"
        mapping = m.get("exact_mapping")
        if not mapping:
            return False, "main_table_mapping_unsupported"
        value = item.get("value") or {}
        aliases = {
            "body_id": value.get("body_id"),
            "body_name": value.get("body_name", value.get("body")),
            "geom_id": value.get("geom_id"),
            "geom_name": value.get("geom_name", value.get("geom")),
            "logical_alias": value.get("logical_alias"),
        }
        if any(mapping.get(k) != v for k, v in aliases.items()):
            return False, "main_table_catalogue_value_mismatch"
        mp, mh = m.get("mapping_path"), m.get("mapping_sha256")
        if not mp or not mh or file_sha256(Path(mp)) != mh:
            return False, "main_table_mapping_source_unverified"
        try:
            audit = json.loads(path.read_text())
            matches = [x for x in audit.get("rows", []) if x.get("execution_id") == ex]
        except (OSError, json.JSONDecodeError):
            return False, "main_table_audit_unreadable"
        if len(matches) != 1 or not _same(matches[0], m):
            return False, "main_table_audit_value_mismatch"
        if not isinstance(mapping, dict) or any(mapping.get(k) != v for k, v in aliases.items()):
            return False, "main_table_catalogue_value_mismatch"
        return True, "catalogue_main_table_anchor"

    # No generic fallback: an unbound alternative source is unverifiable.
    return False, "alternative_source_unbound"


def _validate_family(family, items, row, source_checks, database_sha):
    """Return a conservative family finding using explicit, typed validators."""
    if not items:
        return "unverifiable", "no_returned_items"
    ref_samples = row.get("reference_samples", {}).get(family)
    ref_meta = row.get("reference_metadata", {}).get(family)

    if family.startswith("raw.") or family == "simulator.ncon":
        if not ref_samples:
            return "unverifiable", "numeric_reference_absent"
        expected = {x.get("frame"): x for x in ref_samples}
        observed = set()
        for item in items:
            for sample in item.get("samples", []) or []:
                frame = sample.get("saved_frame_index")
                ref = expected.get(frame)
                if ref is None:
                    continue
                if (sample.get("value") != ref.get("value") or sample.get("dtype") != ref.get("dtype")
                        or sample.get("source_selector") != ref.get("selector")):
                    return "confirmed_error", "reference_sample_value_dtype_or_selector_mismatch"
                observed.add(frame)
        if set(expected) - observed:
            return "unverifiable", "reference_sample_not_returned"
        return "verified", "frozen_sample_and_source_selectors_match"

    if family == "recorded_time":
        if not isinstance(ref_meta, dict):
            return "unverifiable", "unsupported_recorded_time_reference"
        anchor_ok = False
        for item in items:
            val = item.get("value") or {}
            direct_ok, _ = _h5_metadata_item(item, family)
            if not direct_ok:
                return "confirmed_error", "recorded_time_source_selector_or_value_mismatch"
            if (val.get("simulator_endpoint_seconds") == ref_meta.get("simulator_endpoint_seconds")
                    and val.get("recorder_host_wall_ns") == ref_meta.get("wall_ns")
                    and val.get("synchronized_physical_instant") is False):
                anchor_ok = True
        if not anchor_ok:
            return "unverifiable", "scalar_time_anchor_not_found"
        # Multiple frame results are not all compared to one scalar anchor.
        return "verified", "reference_anchor_matches_one_frame; other_frames_source_checked"

    if family == "main_table_identity":
        if not isinstance(ref_meta, dict) or ref_meta.get("supported") is not True:
            return "unverifiable", "reference_marks_alias_unsupported"
        for item in items:
            val = item.get("value") or {}
            body = val.get("body_name", val.get("body"))
            geom = val.get("geom_name", val.get("geom"))
            if body != ref_meta.get("body") or geom != ref_meta.get("geom"):
                return "confirmed_error", "main_table_name_mismatch"
        return "verified", "body_geom_aliases_match_reference_and_catalogue"

    if family == "geometry_identity":
        if not isinstance(ref_meta, dict):
            return "unverifiable", "geometry_reference_missing"
        required = ("object_id", "root_body", "body_id", "collision_geom_ids")
        if any(k not in ref_meta for k in required):
            return "unverifiable", "unsupported_geometry_reference_schema"
        for item in items:
            value = item.get("value") or {}
            if any(value.get(k) != ref_meta[k] for k in required):
                return "confirmed_error", "geometry_identity_mismatch"
        return "verified", "typed_geometry_identity_fields_match"

    if family == "action_metadata":
        if not isinstance(ref_meta, dict) or not isinstance(ref_meta.get("attributes"), dict):
            return "unverifiable", "unsupported_action_metadata_reference"
        for item in items:
            value = item.get("value") or {}
            direct_ok, _ = _h5_metadata_item(item, family)
            if not direct_ok:
                return "confirmed_error", "action_metadata_source_selector_or_value_mismatch"
            if item.get("source_artifact", {}).get("selector") != ref_meta.get("selector"):
                return "confirmed_error", "action_metadata_selector_mismatch"
            attrs = value.get("policy_attributes")
            if not isinstance(attrs, dict) or any(attrs.get(k) != v for k, v in ref_meta["attributes"].items()):
                return "confirmed_error", "action_metadata_attributes_mismatch"
        return "verified", "policy_step_selector_and_attributes_match"

    if family == "execution_metadata":
        if not source_checks or not all(ok for ok, _ in source_checks):
            return "unverifiable", "execution_metadata_source_not_independently_bound"
        return "verified", "catalogue_metadata_path_hash_and_json_projection_match"

    if family == "source_provenance":
        if not source_checks or not all(ok for ok, _ in source_checks):
            return "unverifiable", "source_provenance_source_unbound"
        for item in items:
            val = item.get("value") or {}
            art = item.get("source_artifact") or {}
            if val.get("source_sha256") != art.get("sha256") or val.get("database_sha256") != database_sha:
                return "confirmed_error", "source_provenance_hash_mismatch"
        return "verified", "artifact_and_database_hashes_match"

    if family in ("camera_references", "contact_references"):
        import h5py
        for item in items:
            art = item.get("source_artifact") or {}
            path = Path(art.get("path", ""))
            val = item.get("value") or {}
            selector = art.get("selector") or ""
            with h5py.File(path, "r") as h5:
                key = selector.lstrip("/")
                if key not in h5:
                    return "unverifiable", family + "_selector_missing"
                node = h5[key]
                if family == "camera_references":
                    if not isinstance(node, h5py.Dataset):
                        return "unverifiable", "camera_selector_not_dataset"
                    if list(node.shape) != val.get("shape") or str(node.dtype) != val.get("dtype"):
                        return "confirmed_error", "camera_shape_or_dtype_mismatch"
                    if val.get("materialized") is not False or val.get("physical_contact_or_support_inferred") is not False:
                        return "confirmed_error", "camera_reference_overclaim"
                else:
                    if not isinstance(node, h5py.Group):
                        return "unverifiable", "contact_selector_not_group"
                    if val.get("materialized") is not False or val.get("physical_contact_or_support_inferred") is not False:
                        return "confirmed_error", "contact_reference_overclaim"
        return "verified", "recorded_reference_selectors_and_noninference_scope_match"

    if family == "inference_metadata":
        import h5py
        for item in items:
            ok, reason = _h5_metadata_item(item, family)
            if not ok:
                return "confirmed_error", "inference_metadata_" + reason
        return "verified", "inference_call_selector_and_attributes_match_source"

    return "unverifiable", "no_family_specific_validator"


def _load_catalogue(path):
    uri = "file:" + Path(path).resolve().as_posix() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        return {ex: json.loads(body) for ex, body in db.execute("SELECT execution, body FROM catalogue")}
    finally:
        db.close()


def classify_case(row, record, catalogue, source_root, database_sha, hash_cache):
    case_id = row["id"]
    diagnostics = []
    findings = []
    response = record.get("response") or {}
    claimed = bool(record.get("claimed_complete"))
    expected = list(row.get("expected_families", []))
    groups = response.get("groups", record.get("groups", [])) or []
    by_family = {g.get("family"): g for g in groups if isinstance(g, dict)}
    all_items = [i for g in groups if isinstance(g, dict) for i in g.get("items", []) if isinstance(i, dict)]

    if row.get("fault"):
        diagnostics.append("fault_fixture_not_applied_by_run_eval_v2")
        assessment = "evaluation_unavailable"
    else:
        assessment = None

    record_sha = record.get("record_sha256")
    observed_sha = canonical_sha({k: v for k, v in record.items() if k != "record_sha256"})
    if record_sha != observed_sha:
        diagnostics.append("saved_case_record_hash_mismatch")
        assessment = "unresolved_discrepancy"

    source_status = []
    for item in all_items:
        fam = item.get("family")
        ok, reason = _source_bind(row, item, fam, catalogue, source_root, database_sha, hash_cache)
        source_status.append((ok, reason))
        if reason not in ("frozen_source_pair", "catalogue_metadata_anchor", "catalogue_main_table_anchor"):
            diagnostics.append("source_" + reason)
        elif reason in ("catalogue_metadata_anchor", "catalogue_main_table_anchor"):
            diagnostics.append("valid_alternative_source_not_listed_in_frozen_source_artifacts:" + str(fam))
        req = row.get("request", {})
        for key in ("execution_id", "task_id", "variant_id"):
            if req.get(key) is not None and item.get(key) != req.get(key):
                diagnostics.append("item_scope_mismatch:" + key)
                findings.append({"category": "temporal_or_execution_scope_mismatch", "family": fam, "field": key})

    family_findings = {}
    for family, group in by_family.items():
        items = group.get("items", []) or []
        if group.get("status") == "AVAILABLE":
            checks = []
            for item in items:
                idx = all_items.index(item) if item in all_items else -1
                checks.append(source_status[idx] if idx >= 0 else (False, "item_missing"))
                for sample in item.get("samples", []) or []:
                    art = item.get("source_artifact") or {}
                    path = Path(art.get("path", ""))
                    selector = sample.get("source_selector")
                    try:
                        ok, reason, node = _h5_selector_check(path, selector, sample.get("value"))
                        if ok and str(node.dtype) != str(sample.get("dtype")):
                            ok, reason = False, "dtype_mismatch"
                        if not ok:
                            findings.append({"category": "incorrect_numerical_value", "family": family,
                                             "selector": selector, "reason": reason})
                        frames = row.get("reference_frame_indices")
                        frame = sample.get("saved_frame_index")
                        if frames is not None and frame not in frames:
                            findings.append({"category": "temporal_or_execution_scope_mismatch",
                                             "family": family, "frame": frame})
                    except (OSError, KeyError, ValueError, ImportError):
                        checks.append((False, "sample_source_unverifiable"))
            source_checks = [x for x in checks if x]
            status, why = _validate_family(family, items, row, source_checks, database_sha)
            family_findings[family] = {"status": status, "reason": why}
        else:
            family_findings[family] = {"status": "unavailable", "reason": group.get("reason", group.get("status"))}

    available = {f for f, g in by_family.items() if g.get("status") == "AVAILABLE"}
    missing = sorted(set(expected) - available)
    if missing:
        diagnostics.append("expected_family_not_available:" + ",".join(missing))
    if record.get("citation_or_reference_errors"):
        diagnostics.append("legacy_evaluator_flags:" + ",".join(record["citation_or_reference_errors"]))
    for family in expected:
        if family not in row.get("reference_samples", {}) and family not in row.get("reference_metadata", {}):
            diagnostics.append("frozen_reference_family_coverage_absent:" + family)
    if "reference_metadata_mismatch:recorded_time" in record.get("citation_or_reference_errors", []):
        if len(by_family.get("recorded_time", {}).get("items", [])) > 1:
            diagnostics.append("scalar_recorded_time_reference_compared_to_multiple_frames")
    if "reference_metadata_mismatch:main_table_identity" in record.get("citation_or_reference_errors", []):
        diagnostics.append("main_table_reference_body_geom_keys_differ_from_response_body_name_geom_name")
    if any(str(x).startswith("reference_samples_missing:") for x in record.get("citation_or_reference_errors", [])):
        if not all_items:
            diagnostics.append("reference_absence_due_to_retrieval_not_run")

    unsupported_refs = [f for f in expected if family_findings.get(f, {}).get("status") == "unverifiable"]
    confirmed_family_errors = [f for f in expected if family_findings.get(f, {}).get("status") == "confirmed_error"]
    if confirmed_family_errors:
        findings.extend({"category": "confirmed_retrieval_defect", "family": f} for f in confirmed_family_errors)

    if assessment is None:
        if claimed:
            if findings or missing or any(not ok for ok, _ in source_status):
                assessment = "confirmed_false_complete" if findings or missing else "claimed_complete_unverifiable"
            elif unsupported_refs:
                assessment = "claimed_complete_unverifiable"
            elif not expected:
                diagnostics.append("no_frozen_expected_family_contract")
                assessment = "claimed_complete_unverifiable"
            elif all(family_findings.get(f, {}).get("status") == "verified" for f in expected):
                assessment = "correct_and_verified_complete"
            else:
                assessment = "claimed_complete_unverifiable"
        else:
            response_status = record.get("retrieval_status")
            no_return = not all_items
            plan = record.get("obligation_plan_status")
            unsupported = bool((response.get("interpretation") or {}).get("unsupported"))
            ambiguous = record.get("query_interpretation_status") in ("AMBIGUOUS", "PARTIAL", "UNKNOWN", "INVALID SCOPE", "UNSUPPORTED")
            ref_says_unsupported = any(
                isinstance(row.get("reference_metadata", {}).get(f), dict)
                and row["reference_metadata"][f].get("supported") is False for f in expected
            )
            if response_status == "EXECUTION_ERROR":
                assessment = "evaluation_unavailable"
            elif no_return and (row.get("critical_abstention") or unsupported or ambiguous or ref_says_unsupported
                                or response_status in ("UNAVAILABLE", "INVALID SCOPE", "UNSUPPORTED", "NOT_RUN")):
                assessment = "correct_abstention"
                if unsupported or ambiguous or ref_says_unsupported:
                    diagnostics.append("ambiguous_or_unsupported_request")
            elif missing:
                assessment = "verified_incomplete"
                findings.extend({"category": "confirmed_missing_requested_evidence", "family": f} for f in missing)
            elif expected and response_status not in ("COMPLETE WITHIN VERIFIED CONTRACT",):
                assessment = "unresolved_discrepancy"
            else:
                assessment = "evaluation_unavailable"

    return {
        "case_id": case_id,
        "assessment": assessment,
        "claimed_complete": claimed,
        "retrieval_status": record.get("retrieval_status"),
        "expected_families": expected,
        "available_families": sorted(available),
        "missing_expected_families": missing,
        "family_findings": family_findings,
        "diagnostics": sorted(set(diagnostics)),
        "confirmed_findings": findings,
        "legacy_evaluator_errors": record.get("citation_or_reference_errors", []),
        "fault_fixture_required": row.get("fault"),
        "abstention": bool(record.get("abstention")),
    }


def _integrity_summary(response_path):
    manifest_path = response_path / "PROVENANCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    bad = []
    for cid, wanted in manifest.get("case_records", {}).items():
        record_path = response_path / ("case-" + cid + ".json")
        record = json.loads(record_path.read_text())
        canonical = canonical_sha({k: v for k, v in record.items() if k != "record_sha256"})
        if record.get("record_sha256") != wanted or canonical != wanted:
            bad.append(cid)
    aggregate_path = response_path / "AGGREGATE.json"
    aggregate_sha = file_sha256(aggregate_path)
    if aggregate_sha != manifest.get("aggregate_sha256") or bad:
        raise ValueError(f"preserved response integrity failure: bad_cases={bad}, aggregate_match={aggregate_sha == manifest.get('aggregate_sha256')}")
    return {
        "path": str(response_path),
        "manifest_sha256": file_sha256(manifest_path),
        "aggregate_sha256": aggregate_sha,
        "case_count": len(manifest.get("case_records", {})),
        "all_case_record_hashes_valid": True,
    }


def evaluate(references, responses, catalogue_path, output, source_root, database_sha, three_case_responses=None):
    refs_path, out_path = Path(references), Path(output)
    response_path = Path(responses)
    run_manifest_path = response_path / "PROVENANCE_MANIFEST.json"
    run_integrity = _integrity_summary(response_path)
    three_integrity = _integrity_summary(Path(three_case_responses)) if three_case_responses else None
    run_manifest = json.loads(run_manifest_path.read_text())
    manifest_records = run_manifest.get("case_records", {})
    rows = [json.loads(x) for x in refs_path.read_text().splitlines() if x.strip()]
    row_by_id = {r["id"]: r for r in rows}
    if len(row_by_id) != len(rows):
        raise ValueError("duplicate frozen reference case IDs")
    if set(manifest_records) != set(row_by_id):
        raise ValueError("response manifest and frozen reference case sets differ")
    if file_sha256(refs_path) != run_manifest["hashes"]["reference_dataset_sha256"]:
        raise ValueError("frozen reference hash does not match response manifest")
    catalogue = _load_catalogue(catalogue_path)
    root = Path(source_root).resolve()
    hash_cache = {}
    cases = []
    for cid in sorted(row_by_id):
        path = response_path / f"case-{cid}.json"
        rec = json.loads(path.read_text())
        wanted = manifest_records[cid]
        actual_record = rec.get("record_sha256")
        canonical_record = canonical_sha({k: v for k, v in rec.items() if k != "record_sha256"})
        if actual_record != wanted or canonical_record != wanted:
            raise ValueError(f"saved response record hash differs from preserved manifest: {cid}")
        cases.append(classify_case(row_by_id[cid], rec, catalogue, root, database_sha, hash_cache))

    counts = {}
    for case in cases:
        counts[case["assessment"]] = counts.get(case["assessment"], 0) + 1
    legacy_errors = {}
    diagnostic_counts = {}
    for case in cases:
        for error in case["legacy_evaluator_errors"]:
            legacy_errors[error] = legacy_errors.get(error, 0) + 1
        for diagnostic in case["diagnostics"]:
            key = diagnostic.split(":", 1)[0]
            diagnostic_counts[key] = diagnostic_counts.get(key, 0) + 1
    legacy_false_ids = {cid for cid in row_by_id if json.loads((response_path / ("case-" + cid + ".json")).read_text()).get("false_complete")}
    by_case = {case["case_id"]: case for case in cases}
    aggregate = {
        "evaluator_version": VERSION,
        "legacy_false_complete_flags": len(legacy_false_ids),
        "legacy_false_complete_reclassified_verified": sum(by_case[cid]["assessment"] == "correct_and_verified_complete" for cid in legacy_false_ids),
        "legacy_false_complete_reclassified_evaluation_unavailable": sum(by_case[cid]["assessment"] == "evaluation_unavailable" for cid in legacy_false_ids),
        "legacy_error_counts": legacy_errors,
        "diagnostic_case_counts": diagnostic_counts,
        "cases": len(cases),
        "assessments": counts,
        "confirmed_false_complete": counts.get("confirmed_false_complete", 0),
        "claimed_complete_unverifiable": counts.get("claimed_complete_unverifiable", 0),
        "verified_complete": counts.get("correct_and_verified_complete", 0),
        "correct_abstentions": counts.get("correct_abstention", 0),
        "confirmed_missing_requested_evidence": sum(
            1 for c in cases for f in c["confirmed_findings"] if f["category"] == "confirmed_missing_requested_evidence"
        ),
        "confirmed_incorrect_numerical_values": sum(
            1 for c in cases for f in c["confirmed_findings"] if f["category"] == "incorrect_numerical_value"
        ),
        "cases_with_legacy_errors": sum(bool(c["legacy_evaluator_errors"]) for c in cases),
        "input_run_aggregate_sha256": run_manifest.get("aggregate_sha256"),
    }
    provenance = {
        "evaluator_version": VERSION,
        "evaluator_source_sha256": file_sha256(Path(__file__)),
        "correction_checkout_commit": subprocess.run(
            ["git", "-C", str(next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False
        ).stdout.strip() or "UNAVAILABLE",
        "source_commit": run_manifest.get("source_commit"),
        "full_replay_integrity": run_integrity,
        "three_case_replay_integrity": three_integrity,
        "response_manifest_sha256": file_sha256(run_manifest_path),
        "reference_sha256": file_sha256(refs_path),
        "catalogue_sha256": file_sha256(Path(catalogue_path)),
        "database_sha256": database_sha,
        "source_root": str(root),
        "verified_cited_files": len(hash_cache),
        "created_by": "offline saved-response evaluation; no retrieval was run",
    }
    if out_path.exists() and any(out_path.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty evaluation output: {out_path}")
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "CASE_CLASSIFICATIONS.jsonl").write_text(
        "".join(json.dumps(c, sort_keys=True, allow_nan=False) + "\n" for c in cases)
    )
    (out_path / "AGGREGATE.json").write_text(json.dumps(aggregate, sort_keys=True, indent=2) + "\n")
    (out_path / "PROVENANCE_MANIFEST.json").write_text(json.dumps(provenance, sort_keys=True, indent=2) + "\n")
    return aggregate


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--references", required=True)
    p.add_argument("--responses", required=True)
    p.add_argument("--catalogue", required=True)
    p.add_argument("--source-root", required=True)
    p.add_argument("--database-sha256", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--three-case-responses")
    a = p.parse_args(argv)
    print(json.dumps(evaluate(a.references, a.responses, a.catalogue, a.output,
                              a.source_root, a.database_sha256, a.three_case_responses), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
