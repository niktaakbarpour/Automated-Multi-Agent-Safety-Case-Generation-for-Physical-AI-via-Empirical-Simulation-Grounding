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
    ref_meta = row.get("rvßÎí¢G§²ÚîÆ­yØØ][ÙİYHŠ_Bˆš[˜[N‚ˆ‹˜ÛÜÙJ
B‚‚™YˆÛ\ÜÚYWØØ\ÙJ›İË™XÛÜ™Ø][ÙİYKÛİ\˜ÙWÜ›Ûİ]X˜\ÙWÜÚK\ÚØØXÚJN‚ˆØ\ÙWÚYH›İÖÈšY—BˆXYÛ›ÜİXÜÈH×Bˆš[™[™ÜÈH×Bˆ™\ÜÛœÙHH™XÛÜ™™Ù]
œ™\ÜÛœÙHŠHÜˆßBˆÛZ[YYH›ÛÛ
™XÛÜ™™Ù]
˜ÛZ[YYØÛÛ\]HŠJBˆ^XİYH\İ
›İË™Ù]
™^XİYÙ˜[Z[Y\È‹×JJBˆÜ›İ\ÈH™\ÜÛœÙK™Ù]
™Ü›İ\È‹™XÛÜ™™Ù]
™Ü›İ\È‹×JJHÜˆ×BˆWÙ˜[Z[HHÙË™Ù]
™˜[Z[HŠNˆÈ›ÜˆÈ[ˆÜ›İ\ÈYˆ\Ú[œİ[˜ÙJËXİ
_Bˆ[Ú][\ÈHÚH›ÜˆÈ[ˆÜ›İ\ÈYˆ\Ú[œİ[˜ÙJËXİ
H›ÜˆH[ˆË™Ù]
š][\È‹×JHYˆ\Ú[œİ[˜ÙJKXİ
WB‚ˆYˆ›İË™Ù]
™˜][ŠN‚ˆXYÛ›ÜİXÜË˜\[™
™˜][Ùš^\™WÛ›İØ\YYØWÜ[—Ù]˜[İŒˆŠBˆ\ÜÙ\ÜÛY[H™]˜[X][Û—İ[˜]˜Z[X›H‚ˆ[ÙN‚ˆ\ÜÙ\ÜÛY[H›Û™B‚ˆ™XÛÜ™ÜÚHH™XÛÜ™™Ù]
œ™XÛÜ™ÜÚLMˆŠBˆØœÙ\™YÜÚHHØ[›ÛšXØ[ÜÚJÚÎˆˆ›ÜˆËˆ[ˆ™XÛÜ™š][\Ê
HYˆÈOHœ™XÛÜ™ÜÚLMˆŸJBˆYˆ™XÛÜ™ÜÚHOHØœÙ\™YÜÚN‚ˆXYÛ›ÜİXÜË˜\[™
œØ]™YØØ\ÙWÜ™XÛÜ™Ú\ÚÛZ\ÛX]ÚŠBˆ\ÜÙ\ÜÛY[H[œ™\ÛÛ™YÙ\ØÜ™\[˜ŞH‚‚ˆÛİ\˜ÙWÜİ]\ÈH×Bˆ›Üˆ][H[ˆ[Ú][\Î‚ˆ˜[HH][K™Ù]
™˜[Z[HŠBˆÚË™X\ÛÛˆHÜÛİ\˜ÙWØš[™
›İË][K˜[KØ][ÙİYKÛİ\˜ÙWÜ›Ûİ]X˜\ÙWÜÚK\ÚØØXÚJBˆÛİ\˜ÙWÜİ]\Ë˜\[™

ÚË™X\ÛÛŠJBˆYˆ™X\ÛÛˆ›İ[ˆ
™œ›Ş™[—ÜÛİ\˜ÙWÜZ\ˆ‹˜Ø][ÙİYWÛY]Y]WØ[˜ÚÜˆ‹˜Ø][ÙİYWÛXZ[—İX›WØ[˜ÚÜˆŠN‚ˆXYÛ›ÜİXÜË˜\[™
œÛİ\˜ÙWÈˆ
È™X\ÛÛŠBˆ[Yˆ™X\ÛÛˆ[ˆ
˜Ø][ÙİYWÛY]Y]WØ[˜ÚÜˆ‹˜Ø][ÙİYWÛXZ[—İX›WØ[˜ÚÜˆŠN‚ˆXYÛ›ÜİXÜË˜\[™
˜[YØ[\›˜]]™WÜÛİ\˜ÙWÛ›İÛ\İYÚ[—Ùœ›Ş™[—ÜÛİ\˜ÙWØ\Y˜XİÎˆˆ
ÈİŠ˜[JJBˆ™\HH›İË™Ù]
œ™\]Y\İ‹ßJBˆ›ÜˆÙ^H[ˆ
™^Xİ][Û—ÚY‹\Ú×ÚY‹˜\šX[ÚYŠN‚ˆYˆ™\K™Ù]
Ù^JH\È›İ›Û™H[™][K™Ù]
Ù^JHOH™\K™Ù]
Ù^JN‚ˆXYÛ›ÜİXÜË˜\[™
š][WÜØÛÜWÛZ\ÛX]Úˆˆ
ÈÙ^JBˆš[™[™ÜË˜\[™
È˜Ø]YÛÜHˆ[\Ü˜[ÛÜ—Ù^Xİ][Û—ÜØÛÜWÛZ\ÛX]Ú‹™˜[Z[Hˆ˜[K™šY[ˆÙ^_JB‚ˆ˜[Z[WÙš[™[™ÜÈHßBˆ›Üˆ˜[Z[KÜ›İ\[ˆWÙ˜[Z[Kš][\Ê
N‚ˆ][\ÈHÜ›İ\™Ù]
š][\È‹×JHÜˆ×BˆYˆÜ›İ\™Ù]
œİ]\ÈŠHOHURSP“H‚ˆÚXÚÜÈH×Bˆ›Üˆ][H[ˆ][\Î‚ˆYH[Ú][\Ëš[™^
][JHYˆ][H[ˆ[Ú][\È[ÙHLBˆÚXÚÜË˜\[™
Ûİ\˜ÙWÜİ]\ÖÚYHYˆYH[ÙH
˜[ÙKš][WÛZ\ÜÚ[™ÈŠJBˆ›ÜˆØ[\H[ˆ][K™Ù]
œØ[\\È‹×JHÜˆ×N‚ˆ\H][K™Ù]
œÛİ\˜ÙWØ\Y˜XİŠHÜˆßBˆ]H]
\™Ù]
œ]‹ˆŠJBˆÙ[XİÜˆHØ[\K™Ù]
œÛİ\˜ÙWÜÙ[XİÜˆŠBˆN‚ˆÚË™X\ÛÛ‹›ÙHHÚWÜÙ[XİÜ—ØÚXÚÊ]Ù[XİÜ‹Ø[\K™Ù]
˜[YHŠJBˆYˆÚÈ[™İŠ›ÙK™\JHOHİŠØ[\K™Ù]
™\HŠJN‚ˆÚË™X\ÛÛˆH˜[ÙK™\WÛZ\ÛX]Ú‚ˆYˆ›İÚÎ‚ˆš[™[™ÜË˜\[™
È˜Ø]YÛÜHˆš[˜ÛÜœ™XİÛ[Y\šXØ[İ˜[YH‹™˜[Z[Hˆ˜[Z[KˆœÙ[XİÜˆˆÙ[XİÜ‹œ™X\ÛÛˆˆ™X\ÛÛŸJBˆœ˜[Y\ÈH›İË™Ù]
œ™Y™\™[˜ÙWÙœ˜[YWÚ[™XÙ\ÈŠBˆœ˜[YHHØ[\K™Ù]
œØ]™YÙœ˜[YWÚ[™^ŠBˆYˆœ˜[Y\È\È›İ›Û™H[™œ˜[YH›İ[ˆœ˜[Y\Î‚ˆš[™[™ÜË˜\[™
È˜Ø]YÛÜHˆ[\Ü˜[ÛÜ—Ù^Xİ][Û—ÜØÛÜWÛZ\ÛX]Ú‹ˆ™˜[Z[Hˆ˜[Z[K™œ˜[YHˆœ˜[Y_JBˆ^Ù\
ÔÑ\œ›Ü‹Ù^Q\œ›Ü‹˜[YQ\œ›Ü‹[\Ü\œ›ÜŠN‚ˆÚXÚÜË˜\[™

˜[ÙKœØ[\WÜÛİ\˜ÙWİ[™\šYšXX›HŠJBˆÛİ\˜ÙWØÚXÚÜÈHŞ›Üˆ[ˆÚXÚÜÈYˆBˆİ]\ËÚHHİ˜[Y]WÙ˜[Z[J˜[Z[K][\Ë›İËÛİ\˜ÙWØÚXÚÜË]X˜\ÙWÜÚJBˆ˜[Z[WÙš[™[™ÜÖÙ˜[Z[WHHÈœİ]\Èˆİ]\Ëœ™X\ÛÛˆˆÚ_Bˆ[ÙN‚ˆ˜[Z[WÙš[™[™ÜÖÙ˜[Z[WHHÈœİ]\Èˆ[˜]˜Z[X›H‹œ™X\ÛÛˆˆÜ›İ\™Ù]
œ™X\ÛÛˆ‹Ü›İ\™Ù]
œİ]\ÈŠJ_B‚ˆ]˜Z[X›HHÙˆ›Üˆ‹È[ˆWÙ˜[Z[Kš][\Ê
HYˆË™Ù]
œİ]\ÈŠHOHURSP“HŸBˆZ\ÜÚ[™ÈHÛÜY
Ù]
^XİY
HH]˜Z[X›JBˆYˆZ\ÜÚ[™Î‚ˆXYÛ›ÜİXÜË˜\[™
™^XİYÙ˜[Z[WÛ›İØ]˜Z[X›Nˆˆ
È‹‹š›Ú[ŠZ\ÜÚ[™ÊJBˆYˆ™XÛÜ™™Ù]
˜Ú]][Û—ÛÜ—Ü™Y™\™[˜ÙWÙ\œ›ÜœÈŠN‚ˆXYÛ›ÜİXÜË˜\[™
›YØXŞWÙ]˜[X]Ü—Ù›YÜÎˆˆ
È‹‹š›Ú[Š™XÛÜ™È˜Ú]][Û—ÛÜ—Ü™Y™\™[˜ÙWÙ\œ›ÜœÈ—JJBˆ›Üˆ˜[Z[H[ˆ^XİY‚ˆYˆ˜[Z[H›İ[ˆ›İË™Ù]
œ™Y™\™[˜ÙWÜØ[\\È‹ßJH[™˜[Z[H›İ[ˆ›İË™Ù]
œ™Y™\™[˜ÙWÛY]Y]H‹ßJN‚ˆXYÛ›ÜİXÜË˜\[™
™œ›Ş™[—Ü™Y™\™[˜ÙWÙ˜[Z[WØÛİ™\˜YÙWØXœÙ[ˆˆ
È˜[Z[JBˆYˆœ™Y™\™[˜ÙWÛY]Y]WÛZ\ÛX]Úœ™XÛÜ™Yİ[YHˆ[ˆ™XÛÜ™™Ù]
˜Ú]][Û—ÛÜ—Ü™Y™\™[˜ÙWÙ\œ›ÜœÈ‹×JN‚ˆYˆ[ŠWÙ˜[Z[K™Ù]
œ™XÛÜ™Yİ[YH‹ßJK™Ù]
š][\È‹×JJHˆN‚ˆXYÛ›ÜİXÜË˜\[™
œØØ[\—Ü™XÛÜ™Yİ[YWÜ™Y™\™[˜ÙWØÛÛ\\™Yİ×Û][\WÙœ˜[Y\ÈŠBˆYˆœ™Y™\™[˜ÙWÛY]Y]WÛZ\ÛX]Ú›XZ[—İX›WÚY[]Hˆ[ˆ™XÛÜ™™Ù]
˜Ú]][Û—ÛÜ—Ü™Y™\™[˜ÙWÙ\œ›ÜœÈ‹×JN‚ˆXYÛ›ÜİXÜË˜\[™
›XZ[—İX›WÜ™Y™\™[˜ÙWØ›ÙWÙÙ[ÛWÚÙ^\×ÙY™™\—Ùœ›ÛWÜ™\ÜÛœÙWØ›ÙWÛ˜[YWÙÙ[ÛWÛ˜[YHŠBˆYˆ[JİŠ
Kœİ\İÚ]
œ™Y™\™[˜ÙWÜØ[\\×ÛZ\ÜÚ[™ÎˆŠH›Üˆ[ˆ™XÛÜ™™Ù]
˜Ú]][Û—ÛÜ—Ü™Y™\™[˜ÙWÙ\œ›ÜœÈ‹×JJN‚ˆYˆ›İ[Ú][\Î‚ˆXYÛ›ÜİXÜË˜\[™
œ™Y™\™[˜ÙWØXœÙ[˜ÙWÙYWİ×Ü™]šY]˜[Û›İÜ[ˆŠB‚ˆ[œİ\ÜYÜ™YœÈHÙˆ›Üˆˆ[ˆ^XİYYˆ˜[Z[WÙš[™[™ÜË™Ù]
‹ßJK™Ù]
œİ]\ÈŠHOH[™\šYšXX›H—BˆÛÛ™š\›YYÙ˜[Z[WÙ\œ›ÜœÈHÙˆ›Üˆˆ[ˆ^XİYYˆ˜[Z[WÙš[™[™ÜË™Ù]
‹ßJK™Ù]
œİ]\ÈŠHOH˜ÛÛ™š\›YYÙ\œ›Üˆ—BˆYˆÛÛ™š\›YYÙ˜[Z[WÙ\œ›ÜœÎ‚ˆš[™[™ÜË™^[™
È˜Ø]YÛÜHˆ˜ÛÛ™š\›YYÜ™]šY]˜[ÙY™Xİ‹™˜[Z[HˆŸH›Üˆˆ[ˆÛÛ™š\›YYÙ˜[Z[WÙ\œ›ÜœÊB‚ˆYˆ\ÜÙ\ÜÛY[\È›Û™N‚ˆYˆÛZ[YY‚ˆYˆš[™[™ÜÈÜˆZ\ÜÚ[™ÈÜˆ[J›İÚÈ›ÜˆÚËÈ[ˆÛİ\˜ÙWÜİ]\ÊN‚ˆ\ÜÙ\ÜÛY[H˜ÛÛ™š\›YYÙ˜[ÙWØÛÛ\]HˆYˆš[™[™ÜÈÜˆZ\ÜÚ[™È[ÙH˜ÛZ[YYØÛÛ\]Wİ[™\šYšXX›H‚ˆ[Yˆ[œİ\ÜYÜ™YœÎ‚ˆ\ÜÙ\ÜÛY[H˜ÛZ[YYØÛÛ\]Wİ[™\šYšXX›H‚ˆ[Yˆ›İ^XİY‚ˆXYÛ›ÜİXÜË˜\[™
››×Ùœ›Ş™[—Ù^XİYÙ˜[Z[WØÛÛ˜XİŠBˆ\ÜÙ\ÜÛY[H˜ÛZ[YYØÛÛ\]Wİ[™\šYšXX›H‚ˆ[Yˆ[
˜[Z[WÙš[™[™ÜË™Ù]
‹ßJK™Ù]
œİ]\ÈŠHOH™\šYšYYˆ›Üˆˆ[ˆ^XİY
N‚ˆ\ÜÙ\ÜÛY[H˜ÛÜœ™XİØ[™İ™\šYšYYØÛÛ\]H‚ˆ[ÙN‚ˆ\ÜÙ\ÜÛY[H˜ÛZ[YYØÛÛ\]Wİ[™\šYšXX›H‚ˆ[ÙN‚ˆ™\ÜÛœÙWÜİ]\ÈH™XÛÜ™™Ù]
œ™]šY]˜[Üİ]\ÈŠBˆ›×Ü™]\›ˆH›İ[Ú][\Âˆ[ˆH™XÛÜ™™Ù]
›Ø›YØ][Û—Ü[—Üİ]\ÈŠBˆ[œİ\ÜYH›ÛÛ

™\ÜÛœÙK™Ù]
š[\œ™]][ÛˆŠHÜˆßJK™Ù]
[œİ\ÜYŠJBˆ[XšYİ[İ\ÈH™XÛÜ™™Ù]
œ]Y\WÚ[\œ™]][Û—Üİ]\ÈŠH[ˆ
SP’QÕSÕTÈ‹”T•PS‹•S’Ó“ÕÓˆ‹’S•SQĞÓÔH‹•S”ÕTÔ•QŠBˆ™Y—ÜØ^\×İ[œİ\ÜYH[Jˆ\Ú[œİ[˜ÙJ›İË™Ù]
œ™Y™\™[˜ÙWÛY]Y]H‹ßJK™Ù]
ŠKXİ
Bˆ[™›İÖÈœ™Y™\™[˜ÙWÛY]Y]H—VÙ—K™Ù]
œİ\ÜYŠH\È˜[ÙH›Üˆˆ[ˆ^XİYˆ
BˆYˆ™\ÜÛœÙWÜİ]\ÈOH‘VPÕUSÓ—ÑT”“Ôˆ‚ˆ\ÜÙ\ÜÛY[H™]˜[X][Û—İ[˜]˜Z[X›H‚ˆ[Yˆ›×Ü™]\›ˆ[™
›İË™Ù]
˜Üš]XØ[ØXœİ[[ÛˆŠHÜˆ[œİ\ÜYÜˆ[XšYİ[İ\ÈÜˆ™Y—ÜØ^\×İ[œİ\ÜYˆÜˆ™\ÜÛœÙWÜİ]\È[ˆ
•SURSP“H‹’S•SQĞÓÔH‹•S”ÕTÔ•Q‹““ÕÔ•SˆŠJN‚ˆ\ÜÙ\ÜÛY[H˜ÛÜœ™XİØXœİ[[Ûˆ‚ˆYˆ[œİ\ÜYÜˆ[XšYİ[İ\ÈÜˆ™Y—ÜØ^\×İ[œİ\ÜY‚ˆXYÛ›ÜİXÜË˜\[™
˜[XšYİ[İ\×ÛÜ—İ[œİ\ÜYÜ™\]Y\İŠBˆ[YˆZ\ÜÚ[™Î‚ˆ\ÜÙ\ÜÛY[H™\šYšYYÚ[˜ÛÛ\]H‚ˆš[™[™ÜË™^[™
È˜Ø]YÛÜHˆ˜ÛÛ™š\›YYÛZ\ÜÚ[™×Ü™\]Y\İYÙ]šY[˜ÙH‹™˜[Z[HˆŸH›Üˆˆ[ˆZ\ÜÚ[™ÊBˆ[Yˆ^XİY[™™\ÜÛœÙWÜİ]\È›İ[ˆ
ÓÓTUHÒUSˆ‘T’Q’QQÓÓ•PÕ‹
N‚ˆ\ÜÙ\ÜÛY[H[œ™\ÛÛ™YÙ\ØÜ™\[˜ŞH‚ˆ[ÙN‚ˆ\ÜÙ\ÜÛY[H™]˜[X][Û—İ[˜]˜Z[X›H‚‚ˆ™]\›ˆÂˆ˜Ø\ÙWÚYˆØ\ÙWÚYˆ˜\ÜÙ\ÜÛY[ˆ\ÜÙ\ÜÛY[ˆ˜ÛZ[YYØÛÛ\]HˆÛZ[YYˆœ™]šY]˜[Üİ]\Èˆ™XÛÜ™™Ù]
œ™]šY]˜[Üİ]\ÈŠKˆ™^XİYÙ˜[Z[Y\Èˆ^XİYˆ˜]˜Z[X›WÙ˜[Z[Y\ÈˆÛÜY
]˜Z[X›JKˆ›Z\ÜÚ[™×Ù^XİYÙ˜[Z[Y\ÈˆZ\ÜÚ[™Ëˆ™˜[Z[WÙš[™[™ÜÈˆ˜[Z[WÙš[™[™ÜËˆ™XYÛ›ÜİXÜÈˆÛÜY
Ù]
XYÛ›ÜİXÜÊJKˆ˜ÛÛ™š\›YYÙš[™[™ÜÈˆš[™[™ÜËˆ›YØXŞWÙ]˜[X]Ü—Ù\œ›ÜœÈˆ™XÛÜ™™Ù]
˜Ú]][Û—ÛÜ—Ü™Y™\™[˜ÙWÙ\œ›ÜœÈ‹×JKˆ™˜][Ùš^\™WÜ™\]Z\™Yˆ›İË™Ù]
™˜][ŠKˆ˜Xœİ[[Ûˆˆ›ÛÛ
™XÛÜ™™Ù]
˜Xœİ[[ÛˆŠJKˆB‚‚™YˆÚ[YÜš]WÜİ[[X\J™\ÜÛœÙWÜ]
N‚ˆX[šY™\İÜ]H™\ÜÛœÙWÜ]È”“Õ‘SSÑWÓPS’Q‘TÕšœÛÛˆ‚ˆX[šY™\İHœÛÛ‹›ØYÊX[šY™\İÜ]œ™XYİ^

JBˆ˜YH×Bˆ›ÜˆÚYØ[Y[ˆX[šY™\İ™Ù]
˜Ø\ÙWÜ™XÛÜ™È‹ßJKš][\Ê
N‚ˆ™XÛÜ™Ü]H™\ÜÛœÙWÜ]È
˜Ø\ÙKHˆ
ÈÚY
È‹šœÛÛˆŠBˆ™XÛÜ™HœÛÛ‹›ØYÊ™XÛÜ™Ü]œ™XYİ^

JBˆØ[›ÛšXØ[HØ[›ÛšXØ[ÜÚJÚÎˆˆ›ÜˆËˆ[ˆ™XÛÜ™š][\Ê
HYˆÈOHœ™XÛÜ™ÜÚLMˆŸJBˆYˆ™XÛÜ™™Ù]
œ™XÛÜ™ÜÚLMˆŠHOHØ[YÜˆØ[›ÛšXØ[OHØ[Y‚ˆ˜Y˜\[™
ÚY
BˆYÙÜ™YØ]WÜ]H™\ÜÛœÙWÜ]ÈQÑÔ‘QĞUKšœÛÛˆ‚ˆYÙÜ™YØ]WÜÚHHš[WÜÚLMŠYÙÜ™YØ]WÜ]
BˆYˆYÙÜ™YØ]WÜÚHOHX[šY™\İ™Ù]
˜YÙÜ™YØ]WÜÚLMˆŠHÜˆ˜Y‚ˆ˜Z\ÙH˜[YQ\œ›ÜŠˆœ™\Ù\™Y™\ÜÛœÙH[YÜš]H˜Z[\™Nˆ˜YØØ\Ù\Ï^Ø˜YKYÙÜ™YØ]WÛX]Ú^ØYÙÜ™YØ]WÜÚHOHX[šY™\İ™Ù]
	ØYÙÜ™YØ]WÜÚLM‰Ê_HŠBˆ™]\›ˆÂˆœ]ˆİŠ™\ÜÛœÙWÜ]
Kˆ›X[šY™\İÜÚLMˆˆš[WÜÚLMŠX[šY™\İÜ]
Kˆ˜YÙÜ™YØ]WÜÚLMˆˆYÙÜ™YØ]WÜÚKˆ˜Ø\ÙWØÛİ[ˆ[ŠX[šY™\İ™Ù]
˜Ø\ÙWÜ™XÛÜ™È‹ßJJKˆ˜[ØØ\ÙWÜ™XÛÜ™Ú\Ú\×İ˜[YˆYKˆB‚‚™Yˆ]˜[X]J™Y™\™[˜Ù\Ë™\ÜÛœÙ\ËØ][ÙİYWÜ]İ]]Ûİ\˜ÙWÜ›Ûİ]X˜\ÙWÜÚK™YWØØ\ÙWÜ™\ÜÛœÙ\ÏS›Û™JN‚ˆ™Yœ×Ü]İ]Ü]H]
™Y™\™[˜Ù\ÊK]
İ]]
Bˆ™\ÜÛœÙWÜ]H]
™\ÜÛœÙ\ÊBˆ[—ÛX[šY™\İÜ]H™\ÜÛœÙWÜ]È”“Õ‘SSÑWÓPS’Q‘TÕšœÛÛˆ‚ˆ[—Ú[YÜš]HHÚ[YÜš]WÜİ[[X\J™\ÜÛœÙWÜ]
Bˆ™YWÚ[YÜš]HHÚ[YÜš]WÜİ[[X\J]
™YWØØ\ÙWÜ™\ÜÛœÙ\ÊJHYˆ™YWØØ\ÙWÜ™\ÜÛœÙ\È[ÙH›Û™Bˆ[—ÛX[šY™\İHœÛÛ‹›ØYÊ[—ÛX[šY™\İÜ]œ™XYİ^

JBˆX[šY™\İÜ™XÛÜ™ÈH[—ÛX[šY™\İ™Ù]
˜Ø\ÙWÜ™XÛÜ™È‹ßJBˆ›İÜÈHÚœÛÛ‹›ØYÊ
H›Üˆ[ˆ™Yœ×Ü]œ™XYİ^

KœÜ][™\Ê
HYˆœİš\

WBˆ›İ×ØWÚYHÜ–ÈšY—Nˆˆ›Üˆˆ[ˆ›İÜßBˆYˆ[Š›İ×ØWÚY
HOH[Š›İÜÊN‚ˆ˜Z\ÙH˜[YQ\œ›ÜŠ™\XØ]Hœ›Ş™[ˆ™Y™\™[˜ÙHØ\ÙHQÈŠBˆYˆÙ]
X[šY™\İÜ™XÛÜ™ÊHOHÙ]
›İ×ØWÚY
N‚ˆ˜Z\ÙH˜[YQ\œ›ÜŠœ™\ÜÛœÙHX[šY™\İ[™œ›Ş™[ˆ™Y™\™[˜ÙHØ\ÙHÙ]ÈY™™\ˆŠBˆYˆš[WÜÚLMŠ™Yœ×Ü]
HOH[—ÛX[šY™\İÈš\Ú\È—VÈœ™Y™\™[˜ÙWÙ]\Ù]ÜÚLMˆ—N‚ˆ˜Z\ÙH˜[YQ\œ›ÜŠ™œ›Ş™[ˆ™Y™\™[˜ÙH\ÚÙ\È›İX]Ú™\ÜÛœÙHX[šY™\İŠBˆØ][ÙİYHHÛØYØØ][ÙİYJØ][ÙİYWÜ]
Bˆ›ÛİH]
Ûİ\˜ÙWÜ›Ûİ
Kœ™\ÛÛ™J
Bˆ\ÚØØXÚHHßBˆØ\Ù\ÈH×Bˆ›ÜˆÚY[ˆÛÜY
›İ×ØWÚY
N‚ˆ]H™\ÜÛœÙWÜ]Èˆ˜Ø\ÙK^ØÚYKšœÛÛˆ‚ˆ™XÈHœÛÛ‹›ØYÊ]œ™XYİ^

JBˆØ[YHX[šY™\İÜ™XÛÜ™ÖØÚYBˆXİX[Ü™XÛÜ™H™XË™Ù]
œ™XÛÜ™ÜÚLMˆŠBˆØ[›ÛšXØ[Ü™XÛÜ™HØ[›ÛšXØ[ÜÚJÚÎˆˆ›ÜˆËˆ[ˆ™XËš][\Ê
HYˆÈOHœ™XÛÜ™ÜÚLMˆŸJBˆYˆXİX[Ü™XÛÜ™OHØ[YÜˆØ[›ÛšXØ[Ü™XÛÜ™OHØ[Y‚ˆ˜Z\ÙH˜[YQ\œ›ÜŠˆœØ]™Y™\ÜÛœÙH™XÛÜ™\ÚY™™\œÈœ›ÛH™\Ù\™YX[šY™\İˆØÚYHŠBˆØ\Ù\Ë˜\[™
Û\ÜÚYWØØ\ÙJ›İ×ØWÚYØÚYK™XËØ][ÙİYK›Ûİ]X˜\ÙWÜÚK\ÚØØXÚJJB‚ˆÛİ[ÈHßBˆ›ÜˆØ\ÙH[ˆØ\Ù\Î‚ˆÛİ[ÖØØ\ÙVÈ˜\ÜÙ\ÜÛY[—WHHÛİ[Ë™Ù]
Ø\ÙVÈ˜\ÜÙ\ÜÛY[—K
H
ÈBˆYØXŞWÙ\œ›ÜœÈHßBˆXYÛ›ÜİX×ØÛİ[ÈHßBˆ›ÜˆØ\ÙH[ˆØ\Ù\Î‚ˆ›Üˆ\œ›Üˆ[ˆØ\ÙVÈ›YØXŞWÙ]˜[X]Ü—Ù\œ›ÜœÈ—N‚ˆYØXŞWÙ\œ›ÜœÖÙ\œ›Ü—HHYØXŞWÙ\œ›ÜœË™Ù]
\œ›Ü‹
H
ÈBˆ›ÜˆXYÛ›ÜİXÈ[ˆØ\ÙVÈ™XYÛ›ÜİXÜÈ—N‚ˆÙ^HHXYÛ›ÜİXËœÜ]
ˆ‹JVÌBˆXYÛ›ÜİX×ØÛİ[ÖÚÙ^WHHXYÛ›ÜİX×ØÛİ[Ë™Ù]
Ù^K
H
ÈBˆYØXŞWÙ˜[ÙWÚYÈHØÚY›ÜˆÚY[ˆ›İ×ØWÚYYˆœÛÛ‹›ØYÊ
™\ÜÛœÙWÜ]È
˜Ø\ÙKHˆ
ÈÚY
È‹šœÛÛˆŠJKœ™XYİ^

JK™Ù]
™˜[ÙWØÛÛ\]HŠ_BˆWØØ\ÙHHØØ\ÙVÈ˜Ø\ÙWÚY—NˆØ\ÙH›ÜˆØ\ÙH[ˆØ\Ù\ßBˆYÙÜ™YØ]HHÂˆ™]˜[X]Ü—İ™\œÚ[Ûˆˆ‘T”ÒSÓ‹ˆ›YØXŞWÙ˜[ÙWØÛÛ\]WÙ›YÜÈˆ[ŠYØXŞWÙ˜[ÙWÚYÊKˆ›YØXŞWÙ˜[ÙWØÛÛ\]WÜ™XÛ\ÜÚYšYYİ™\šYšYYˆİ[JWØØ\ÙVØÚYVÈ˜\ÜÙ\ÜÛY[—HOH˜ÛÜœ™XİØ[™İ™\šYšYYØÛÛ\]Hˆ›ÜˆÚY[ˆYØXŞWÙ˜[ÙWÚYÊKˆ›YØXŞWÙ˜[ÙWØÛÛ\]WÜ™XÛ\ÜÚYšYYÙ]˜[X][Û—İ[˜]˜Z[X›Hˆİ[JWØØ\ÙVØÚYVÈ˜\ÜÙ\ÜÛY[—HOH™]˜[X][Û—İ[˜]˜Z[X›Hˆ›ÜˆÚY[ˆYØXŞWÙ˜[ÙWÚYÊKˆ›YØXŞWÙ\œ›Ü—ØÛİ[ÈˆYØXŞWÙ\œ›ÜœËˆ™XYÛ›ÜİX×ØØ\ÙWØÛİ[ÈˆXYÛ›ÜİX×ØÛİ[Ëˆ˜Ø\Ù\Èˆ[ŠØ\Ù\ÊKˆ˜\ÜÙ\ÜÛY[ÈˆÛİ[Ëˆ˜ÛÛ™š\›YYÙ˜[ÙWØÛÛ\]HˆÛİ[Ë™Ù]
˜ÛÛ™š\›YYÙ˜[ÙWØÛÛ\]H‹
Kˆ˜ÛZ[YYØÛÛ\]Wİ[™\šYšXX›HˆÛİ[Ë™Ù]
˜ÛZ[YYØÛÛ\]Wİ[™\šYšXX›H‹
Kˆ™\šYšYYØÛÛ\]HˆÛİ[Ë™Ù]
˜ÛÜœ™XİØ[™İ™\šYšYYØÛÛ\]H‹
Kˆ˜ÛÜœ™XİØXœİ[[ÛœÈˆÛİ[Ë™Ù]
˜ÛÜœ™XİØXœİ[[Ûˆ‹
Kˆ˜ÛÛ™š\›YYÛZ\ÜÚ[™×Ü™\]Y\İYÙ]šY[˜ÙHˆİ[JˆH›ÜˆÈ[ˆØ\Ù\È›Üˆˆ[ˆÖÈ˜ÛÛ™š\›YYÙš[™[™ÜÈ—HYˆ–È˜Ø]YÛÜH—HOH˜ÛÛ™š\›YYÛZ\ÜÚ[™×Ü™\]Y\İYÙ]šY[˜ÙH‚ˆ
Kˆ˜ÛÛ™š\›YYÚ[˜ÛÜœ™XİÛ[Y\šXØ[İ˜[Y\Èˆİ[JˆH›ÜˆÈ[ˆØ\Ù\È›Üˆˆ[ˆÖÈ˜ÛÛ™š\›YYÙš[™[™ÜÈ—HYˆ–È˜Ø]YÛÜH—HOHš[˜ÛÜœ™XİÛ[Y\šXØ[İ˜[YH‚ˆ
Kˆ˜Ø\Ù\×İÚ]ÛYØXŞWÙ\œ›ÜœÈˆİ[J›ÛÛ
ÖÈ›YØXŞWÙ]˜[X]Ü—Ù\œ›ÜœÈ—JH›ÜˆÈ[ˆØ\Ù\ÊKˆš[œ]Ü[—ØYÙÜ™YØ]WÜÚLMˆˆ[—ÛX[šY™\İ™Ù]
˜YÙÜ™YØ]WÜÚLMˆŠKˆBˆ›İ™[˜[˜ÙHHÂˆ™]˜[X]Ü—İ™\œÚ[Ûˆˆ‘T”ÒSÓ‹ˆ™]˜[X]Ü—ÜÛİ\˜ÙWÜÚLMˆˆš[WÜÚLMŠ]
×Ùš[W×ÊJKˆ˜ÛÜœ™Xİ[Û—ØÚXÚÛİ]ØÛÛ[Z]ˆİXœ›ØÙ\ÜËœ[ŠˆÈ™Ú]‹‹PÈ‹İŠ™^
\™[›Üˆ\™[[ˆ]
×Ùš[W×ÊKœ™\ÛÛ™J
Kœ\™[ÈYˆ
\™[È‹™Ú]ŠK™^\İÊ
JJKœ™]‹\\œÙH‹’PQ—KˆØ\\™WÛİ]]UYK^UYKÚXÚÏQ˜[ÙBˆ
Kœİİ]œİš\

HÜˆ•SURSP“H‹ˆœÛİ\˜ÙWØÛÛ[Z]ˆ[—ÛX[šY™\İ™Ù]
œÛİ\˜ÙWØÛÛ[Z]ŠKˆ™[Ü™\^WÚ[YÜš]Hˆ[—Ú[YÜš]Kˆ™YWØØ\ÙWÜ™\^WÚ[YÜš]Hˆ™YWÚ[YÜš]Kˆœ™\ÜÛœÙWÛX[šY™\İÜÚLMˆˆš[WÜÚLMŠ[—ÛX[šY™\İÜ]
Kˆœ™Y™\™[˜ÙWÜÚLMˆˆš[WÜÚLMŠ™Yœ×Ü]
Kˆ˜Ø][ÙİYWÜÚLMˆˆš[WÜÚLMŠ]
Ø][ÙİYWÜ]
JKˆ™]X˜\ÙWÜÚLMˆˆ]X˜\ÙWÜÚKˆœÛİ\˜ÙWÜ›ÛİˆİŠ›Ûİ
Kˆ™\šYšYYØÚ]YÙš[\Èˆ[Š\ÚØØXÚJKˆ˜Ü™X]YØHˆ›Ù™›[™HØ]™Y\™\ÜÛœÙH]˜[X][ÛÈ›È™]šY]˜[Ø\È[ˆ‹ˆBˆYˆİ]Ü]™^\İÊ
H[™[Jİ]Ü]š]\™\Š
JN‚ˆ˜Z\ÙHš[Q^\İÑ\œ›ÜŠˆœ™Y\Ú[™ÈÈİ™\Üš]H›Û™[\H]˜[X][Ûˆİ]]ˆÛİ]Ü]HŠBˆİ]Ü]›ZÙ\Š\™[ÏUYK^\İÛÚÏUYJBˆ
İ]Ü]ÈĞTÑWĞÓTÔÒQ’PĞUSÓ”ËšœÛÛ›ŠKÜš]Wİ^
ˆˆ‹š›Ú[ŠœÛÛ‹™[\ÊËÛÜÚÙ^\ÏUYK[İ×Û˜[Q˜[ÙJH
È—ˆˆ›ÜˆÈ[ˆØ\Ù\ÊBˆ
Bˆ
İ]Ü]ÈQÑÔ‘QĞUKšœÛÛˆŠKÜš]Wİ^
œÛÛ‹™[\ÊYÙÜ™YØ]KÛÜÚÙ^\ÏUYK[™[LŠH
È—ˆŠBˆ
İ]Ü]È”“Õ‘SSÑWÓPS’Q‘TÕšœÛÛˆŠKÜš]Wİ^
œÛÛ‹™[\Ê›İ™[˜[˜ÙKÛÜÚÙ^\ÏUYK[™[LŠH
È—ˆŠBˆ™]\›ˆYÙÜ™YØ]B‚‚™YˆXZ[Š\™İS›Û™JN‚ˆH\™Ü\œÙK\™İ[Y[\œÙ\Š\ØÜš\[ÛW×ÙØ××ÊBˆ˜YØ\™İ[Y[
‹K\™Y™\™[˜Ù\È‹™\]Z\™YUYJBˆ˜YØ\™İ[Y[
‹K\™\ÜÛœÙ\È‹™\]Z\™YUYJBˆ˜YØ\™İ[Y[
‹KXØ][ÙİYH‹™\]Z\™YUYJBˆ˜YØ\™İ[Y[
‹K\Ûİ\˜ÙK\›Ûİ‹™\]Z\™YUYJBˆ˜YØ\™İ[Y[
‹KY]X˜\ÙK\ÚLMˆ‹™\]Z\™YUYJBˆ˜YØ\™İ[Y[
‹K[İ]]‹™\]Z\™YUYJBˆ˜YØ\™İ[Y[
‹K]™YKXØ\ÙK\™\ÜÛœÙ\ÈŠBˆHHœ\œÙWØ\™ÜÊ\™İŠBˆš[
œÛÛ‹™[\Ê]˜[X]JKœ™Y™\™[˜Ù\ËKœ™\ÜÛœÙ\ËK˜Ø][ÙİYKK›İ]]ˆKœÛİ\˜ÙWÜ›ÛİK™]X˜\ÙWÜÚLM‹K™YWØØ\ÙWÜ™\ÜÛœÙ\ÊKÛÜÚÙ^\ÏUYK[™[LŠJB‚‚šYˆ×Û˜[YW×ÈOH—×ÛXZ[—×È‚ˆXZ[Š
B