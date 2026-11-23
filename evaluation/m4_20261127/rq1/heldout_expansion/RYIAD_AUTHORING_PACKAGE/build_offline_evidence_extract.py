#!/usr/bin/env python3
"""One-time exporter for exact, selected evidence values from verified HDF5 sources."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import sqlite3
from pathlib import Path

import h5py
import numpy as np

PACKAGE = Path(__file__).resolve().parent
OUT = PACKAGE / "OFFLINE_EVIDENCE"
RAW_FAMILIES = {"timestamp", "contact", "object_pose", "robot_state", "native_geometry"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def safe_value(value):
    if isinstance(value, np.ndarray):
        return safe_value(value.tolist())
    if isinstance(value, np.generic):
        return safe_value(value.item())
    if isinstance(value, dict):
        return {str(k): safe_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_value(v) for v in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numeric sample")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)

def read_h5_group(node):
    if isinstance(node, h5py.Dataset):
        return safe_value(node[()])
    return {str(k): read_h5_group(node[k]) for k in sorted(node.keys())}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-db", required=True, help="Read-only Phase 5I evidence SQLite database")
    args = ap.parse_args()
    required_outputs = [
        OUT / "EVIDENCE_SAMPLES.jsonl.gz",
        OUT / "EVIDENCE_RECORDS.jsonl.gz",
        OUT / "TASK_CONTEXT.csv",
        OUT / "UNEXTRACTED_EVIDENCE.csv",
        OUT / "EXTRACT_MANIFEST.json",
    ]
    if any(p.exists() for p in required_outputs):
        raise SystemExit("refusing to overwrite existing offline extract files")
    OUT.mkdir(parents=True, exist_ok=True)

    caps = list(csv.DictReader((PACKAGE / "SOURCE_CAPABILITIES.csv").open(newline="", encoding="utf-8")))
    verification = {r["execution_id"]: r for r in csv.DictReader((PACKAGE / "SOURCE_RECOVERY_VERIFICATION.csv").open(newline="", encoding="utf-8"))}
    refs = list(csv.DictReader((PACKAGE / "SOURCE_EVIDENCE_INDEX.csv").open(newline="", encoding="utf-8")))
    selected = {r["execution_id"] for r in caps}
    assert len(caps) == 30 and len(selected) == 30
    assert all(verification[x]["verification_status"] == "PASS" for x in selected)

    db_path = Path(args.evidence_db).resolve()
    db = sqlite3.connect("file:" + str(db_path) + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    evidence_by_id = {}
    for row in db.execute("SELECT id,requirement_id,requirement_version,execution_id,object_id,kind,body FROM evidence"):
        if row["execution_id"] in selected:
            evidence_by_id[row["id"]] = dict(row)
    assert len(evidence_by_id) == len([r for r in refs if r["execution_id"] in selected])
    for ref in refs:
        if ref["execution_id"] in selected:
            assert ref["evidence_id"] in evidence_by_id

    source_file_manifest = []
    for cap in caps:
        ex = cap["execution_id"]
        rec = verification[ex]
        source = Path(cap["trajectory_path"])
        actual = sha256(source)
        expected = rec["trajectory_sha256_recomputed"]
        if actual != expected or actual != rec["trajectory_sha256_receipt"]:
            raise SystemExit("trajectory hash mismatch: " + ex)
        source_file_manifest.append({
            "execution_id": ex,
            "task_id": cap["task_id"],
            "variant_id": cap["variant_id"],
            "source_trajectory_path_provenance_only": str(source),
            "source_trajectory_sha256": actual,
            "source_bytes": source.stat().st_size,
            "recovery_status": rec["verification_status"],
            "saved_frame_start": int(rec["saved_frame_start"]),
            "saved_frame_end": int(rec["saved_frame_end"]),
        })

    sample_path = OUT / "EVIDENCE_SAMPLES.jsonl.gz"
    record_path = OUT / "EVIDENCE_RECORDS.jsonl.gz"
    task_path = OUT / "TASK_CONTEXT.csv"
    unextracted_path = OUT / "UNEXTRACTED_EVIDENCE.csv"
    rows_by_type = {}
    sample_rows = 0
    record_rows = 0
    unextracted = []
    task_rows = []

    clock = {}
    for row in db.execute(
        "SELECT execution,frame,sim_time,wall_ns,monotonic_ns,utc FROM i_clock_labels"
    ):
        if row["execution"] in selected:
            clock[(row["execution"], int(row["frame"]))] = dict(row)

    with gzip.GzipFile(filename=str(sample_path), mode="wb", mtime=0) as gz:
        for ref in refs:
            ex = ref["execution_id"]
            if ex not in selected:
                continue
            mt = ref["measurement_type"]
            if mt not in RAW_FAMILIES:
                if mt == "camera_reference":
                    unextracted.append({
                        "execution_id": ex, "evidence_id": ref["evidence_id"],
                        "measurement_type": mt, "object_id": ref["object_id"],
                        "original_selector": ref["selector"],
                        "reason": "image pixels not included in compact offline package; visual judgment is unsupported",
                    })
                continue
            body = json.loads(evidence_by_id[ref["evidence_id"]]["body"])
            prov = body.get("provenance", {})
            source = Path(ref["source_path"])
            if str(source) != str(Path(next(c["trajectory_path"] for c in caps if c["execution_id"] == ex))):
                raise SystemExit("indexed source path differs from verified trajectory: " + ref["evidence_id"])
            lo, hi = int(ref["saved_frame_start"]), int(ref["saved_frame_end"])
            with h5py.File(source, "r") as h5:
                for frame in range(lo, hi + 1):
                    frame_root = "frames/{:06d}".format(frame)
                    sim_selector = frame_root + "/simulator/time/value"
                    time_h5 = safe_value(h5[sim_selector][()]) if sim_selector in h5 else None
                    clock_row = clock.get((ex, frame))
                    value = {}
                    resolved = []
                    status = "ok"
                    try:
                        if mt == "timestamp":
                            resolved = ["/" + sim_selector]
                            value = {"simulator_time": time_h5}
                            if clock_row:
                                value["indexed_clock_label"] = {
                                    "sim_time": clock_row["sim_time"],
                                    "wall_ns": clock_row["wall_ns"],
                                    "monotonic_ns": clock_row["monotonic_ns"],
                                    "utc": clock_row["utc"],
                                    "source_table": "i_clock_labels",
                                }
                        elif mt == "contact":
                            path = frame_root + "/simulator/contacts"
                            resolved = ["/" + path]
                            value = {"recorded_contacts": read_h5_group(h5[path]) if path in h5 else None}
                            ncon_path = frame_root + "/simulator/ncon/value"
                            value["simulator_ncon"] = safe_value(h5[ncon_path][()]) if ncon_path in h5 else None
                            if value["recorded_contacts"] == {}:
                                status = "empty_recorded_group"
                        elif mt == "object_pose":
                            body_id = prov.get("body_id")
                            if body_id is None:
                                status = "mapping_missing"
                            else:
                                pos_path = frame_root + "/simulator/body_xpos/value"
                                quat_path = frame_root + "/simulator/body_xquat/value"
                                resolved = ["/" + pos_path + "[{}]".format(body_id), "/" + quat_path + "[{}]".format(body_id)]
                                value = {
                                    "body_id": body_id,
                                    "position": safe_value(h5[pos_path][int(body_id)]),
                                    "quaternion": safe_value(h5[quat_path][int(body_id)]),
                                }
                        elif mt == "robot_state":
                            for field in ("qpos", "qvel", "ctrl"):
                                path = frame_root + "/simulator/" + field + "/value"
                                resolved.append("/" + path)
                                value[field] = safe_value(h5[path][()]) if path in h5 else None
                        elif mt == "native_geometry":
                            geom_ids = prov.get("collision_geom_ids") or []
                            pos_path = frame_root + "/simulator/geom_xpos/value"
                            mat_path = frame_root + "/simulator/geom_xmat/value"
                            resolved = ["/" + pos_path + "[collision_geom_ids]", "/" + mat_path + "[collision_geom_ids]"]
                            value = {
                                "collision_geom_ids": geom_ids,
                                "geom_position": safe_value(h5[pos_path][geom_ids]) if pos_path in h5 else None,
                                "geom_matrix": safe_value(h5[mat_path][geom_ids]) if mat_path in h5 else None,
                            }
                    except (KeyError, IndexError, ValueError, TypeError) as exc:
                        value = {}
                        status = "unsupported_source_sample:" + type(exc).__name__
                    payload = {
                        "execution_id": ex,
                        "task_id": ref["task_id"],
                        "variant_id": ref["variant_id"],
                        "evidence_id": ref["evidence_id"],
                        "requirement_id": ref["requirement_id"],
                        "requirement_version": ref["requirement_version"],
                        "object_id": ref["object_id"],
                        "measurement_type": mt,
                        "frame_index": frame,
                        "source_trajectory_sha256": verification[ex]["trajectory_sha256_recomputed"],
                        "original_selector": ref["selector"],
                        "resolved_selectors": resolved,
                        "simulator_time_h5": time_h5,
                        "value": value,
                        "extract_status": status,
                    }
                    line = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
                    gz.write(line)
                    sample_rows += 1
                    rows_by_type[mt] = rows_by_type.get(mt, 0) + 1

    with gzip.GzipFile(filename=str(record_path), mode="wb", mtime=0) as gz:
        for ex in sorted(selected):
            for row in db.execute(
                "SELECT id,requirement_id,requirement_version,execution_id,object_id,kind,body FROM evidence WHERE execution_id=? ORDER BY id",
                (ex,),
            ):
                line = json.dumps(dict(row), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
                gz.write(line)
                record_rows += 1

    for cap in caps:
        ex = cap["execution_id"]
        row = db.execute("SELECT body FROM rag_catalog WHERE execution=?", (ex,)).fetchone()
        catalog = json.loads(row["body"]) if row else {}
        ti = catalog.get("task_instruction") or {}
        task_ref = next(r for r in refs if r["execution_id"] == ex and r["measurement_type"] == "task_instruction")
        task_source = Path(task_ref["source_path"])
        task_sha = sha256(task_source)
        if task_sha != task_ref["source_sha256"]:
            raise SystemExit("task metadata hash mismatch: " + ex)
        meta = json.loads(task_source.read_text(encoding="utf-8"))
        task_rows.append({
            "execution_id": ex,
            "task_id": cap["task_id"],
            "variant_id": cap["variant_id"],
            "suite": cap["suite"],
            "environment_identity": cap["environment_identity"],
            "task_instruction_evidence_id": task_ref["evidence_id"],
            "task_instruction_original_selector": task_ref["selector"],
            "task_metadata_sha256": task_sha,
            "task_name_recorded": meta.get("task_name", ""),
            "policy_instruction_recorded": meta.get("instruction", ""),
            "catalog_policy_instruction": ti.get("recorded_policy_instruction", ""),
            "environment_bddl_language": ti.get("environment_bddl_language", ""),
            "catalog_exact_mismatch": ti.get("exact_mismatch", ""),
            "catalog_primary_source": ti.get("primary_source", ""),
            "task_horizon_recorded": meta.get("task_horizon", ""),
            "settling_steps_recorded": meta.get("settling_steps", ""),
            "control_frequency_hz_recorded": meta.get("control_frequency_hz", ""),
        })
    with task_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(task_rows[0]))
        writer.writeheader()
        writer.writerows(task_rows)
    with unextracted_path.open("w", newline="", encoding="utf-8") as f:
        cols = ["execution_id", "evidence_id", "measurement_type", "object_id", "original_selector", "reason"]
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(unextracted)

    files = {}
    for p in (sample_path, record_path, task_path, unextracted_path):
        files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    manifest = {
        "schema_version": "offline-evidence-extract/1.0",
        "execution_count": len(caps),
        "distinct_execution_count": len(selected),
        "task_count": len({c["task_id"] for c in caps}),
        "variant_count": len({c["variant_id"] for c in caps}),
        "verified_source_hash_count": len(source_file_manifest),
        "source_files": source_file_manifest,
        "evidence_record_count": record_rows,
        "sample_value_row_count": sample_rows,
        "sample_rows_by_measurement_type": rows_by_type,
        "unextracted_evidence_count": len(unextracted),
        "files": files,
        "generator": "build_offline_evidence_extract.py",
        "h5py_version": h5py.__version__,
        "numeric_policy": "raw values only; no interpolation, normalization, unit conversion, labeling, or physical interpretation",
    }
    manifest_path = OUT / "EXTRACT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("execution_count", "task_count", "variant_count", "evidence_record_count", "sample_value_row_count", "sample_rows_by_measurement_type", "unextracted_evidence_count", "files")}, indent=2))

if __name__ == "__main__":
    main()
