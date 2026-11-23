"""Trace saved RQ1 failures. No retrieval, new labels, or source replay."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATABASE = ROOT / "evaluation/r1_v4/rag_evidence_database"
HISTORICAL = DATABASE / "readiness_evaluation"
REMEDIATION = DATABASE / "retrieval_remediation"
REPLAY_ARCHIVE = (DATABASE / "working_result_archive/additional_working_summaries"
                  / "trustworthy-phase5k-working")
MODES = ("exact", "semantic", "lexical")
TEMPORAL_CASES = ("KH2-C2-02", "KH2-C2-10", "KH2-C2-18")
JOINT_POSITION = "raw.robot0_joint_pos"
HISTORICAL_CASES = "RQ1_HISTORICAL_CASES.csv"
MISSING_OBLIGATIONS = "RQ1_MISSING_OBLIGATIONS.csv"

# These descriptions concern the frozen evidence for the exact named cases.
BOUNDARIES = {
    ("C4-08", "camera_exposure_timestamp"): (
        "exposure_clock_unsupported", "exact_source_unverified",
        "Raw joint velocity was returned. The reference has no case-bound camera exposure receipt."),
    ("C4-09", "historical_binary"): (
        "historical_attestation_unavailable", "not_found_in_audited_roots",
        "The producer audit could not find matching oft_adapter.py bytes in the audited roots. "
        "Current source verification is separate."),
    ("C4-13", "contact_pairs_and_force"): (
        "contact_detail_outside_raw_count_route", "exact_source_unverified",
        "Returned simulator.ncon is a count. Legacy contact references do not verify "
        "the requested pairs and force vectors at this frame."),
    ("C4-21", "sensor_clock_calibration"): (
        "sensor_clock_calibration_unsupported", "exact_source_unverified",
        "The reference has no calibration receipt. The exposed comparison lists this obligation as unmapped."),
}
REPLAY_PROOFS = {
    "action_metadata": (
        "action_metadata", "policy_metadata_outside_raw_response", "recorded_action_metadata_in_exposed_replay",
        "The exposed comparison returned policy and chunk metadata. Executed action arrays remain references."),
    "inference_metadata": (
        "inference_metadata", "policy_metadata_outside_raw_response", "recorded_inference_metadata_in_exposed_replay",
        "The exposed comparison returned a recorded inference call with its input-frame association."),
    "recorder_host_timestamp": (
        "recorded_time", "host_time_outside_raw_response", "recorded_host_labels_in_exposed_replay",
        "The exposed comparison returned the host monotonic, wall-clock and UTC fields for the saved frame."),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_bytes())


def file_hash(data):
    return sha256(data).hexdigest()


def frozen_artifact(folder, name, manifest_key, *, manifest_folder=None):
    manifest = read_json((manifest_folder or folder) / "ARTIFACT_MANIFEST.json")
    suffix = f"/{folder.name}/{name}"
    receipts = [row for row in manifest[manifest_key] if row["path"].endswith(suffix)]
    data = (folder / name).read_bytes()
    require(len(receipts) == 1 and receipts[0]["sha256"] == file_hash(data)
            and receipts[0]["bytes"] == len(data), f"Frozen artifact mismatch: {folder.name}/{name}")
    return data


def json_rows(data):
    return [(i, json.loads(line)) for i, line in enumerate(data.splitlines(), start=1)]


def indexed(rows, key):
    index = {}
    for line, row in rows:
        identifier = key(row)
        require(identifier not in index, f"Duplicate frozen row: {identifier}")
        index[identifier] = (line, row)
    return index


def joined(values):
    return ";".join(str(value) for value in values)


def span(value):
    return json.dumps(value, separators=(",", ":"))


def source_refs(records):
    # Preserve selectors and hashes without copying source-host filesystem paths.
    return joined(f'{PurePosixPath(r["path"]).name} {r["selector"]} sha256={r["sha256"]}'
                  for r in records)


def replay_source_proof(case, facet, replay, interval):
    family, stage, availability, note = REPLAY_PROOFS[facet]
    source = case["reference_artifacts"][0]
    require(replay["output"]["interpretation"]["resolved_frame_interval"] == interval,
            f"Retrospective scope differs for {case['id']}/{facet}")
    items = [item for item in replay["items"] if item["family"] == family]
    require(items and all(
        item["integrity_status"] == "verified_source"
        and item["source_artifact"]["sha256"] == source["sha256"]
        and item["source_artifact"]["path"] == source["path"]
        and all(item[key] == case[key] for key in ("execution_id", "task_id", "variant_id"))
        for item in items), f"Retrospective source differs for {case['id']}/{facet}")
    if facet == "recorder_host_timestamp":
        require(len(items) == 1 and items[0]["value"]["saved_frame_index"] == interval[0]
                and all(items[0]["value"][key] is not None for key in
                        ("recorder_host_monotonic_ns", "recorder_host_wall_ns", "recorder_utc")),
                f"Host label evidence missing for {case['id']}")
    return stage, availability, f"{replay['case_id']}: {note}", source_refs(
        item["source_artifact"] for item in items)


def historical_proof(case, facet, all_refs, rows, replay_rows):
    case_id = case["id"]
    if (case_id, facet) in BOUNDARIES:
        stage, availability, note = BOUNDARIES[case_id, facet]
        if facet == "sensor_clock_calibration":
            require(facet in replay_rows[f"JH-{case_id}"]["unmapped_original_obligations"],
                    f"Retrospective sensor-clock mapping changed for {case_id}")
        return stage, availability, note, ""
    if facet in REPLAY_PROOFS:
        return replay_source_proof(case, facet, replay_rows[f"JH-{case_id}"],
                                   rows[case_id, "exact"][1]["request"]["interval"])
    if (case_id, facet) == ("C4-18", "geometry_identity"):
        _, geometry = all_refs["C3-18"]
        _, c4 = rows[case_id, "exact"]
        require(all(geometry[k] == case[k] for k in ("execution_id", "task_id", "variant_id"))
                and geometry["request"]["interval"] == c4["request"]["interval"],
                "Geometry reference scope differs from its C4 case")
        refs = [r for r in geometry["reference_artifacts"] if r["selector"] != "/frames"]
        require(bool(refs), "Geometry reference lacks native/XML sources")
        return ("cross_family_composition_missing", "geometry_source_documented",
                "The same-scope C3-18 reference documents the object geometry sources. "
                "Source documentation is separate from retrieval. The C4 raw response "
                "returned only gripper positions.", source_refs(refs))
    require(case_id in ("C4-05", "C4-20"), f"No evidence classification for {case_id}/{facet}")
    for mode in ("exact", "semantic"):
        _, peer = rows[case_id, mode]
        require(facet in peer["assessment"]["fulfilled_facets"]
                and peer["request"]["interval"] == rows[case_id, "lexical"][1]["request"]["interval"],
                f"Missing companion evidence for {case_id}/{facet}")
    selectors = {r["selector"] for r in case["reference_samples"] if r["channel"] == facet}
    refs = [r for r in case["reference_artifacts"] if r["selector"] in selectors]
    require(bool(refs), f"Missing frozen raw reference for {case_id}/{facet}")
    return ("lexical_no_match", "raw_values_available_in_companion_modes",
            "The lexical response returned no records. Both saved companion modes fulfilled this facet.",
            source_refs(refs))


def historical():
    read = lambda name: frozen_artifact(HISTORICAL, name, "artifacts")
    data = read("EVALUATION_DATASET.jsonl")
    require(file_hash(data) == read_json(HISTORICAL / "DATASET_FREEZE.json")["dataset_sha256"],
            "Historical reference freeze mismatch")
    refs = indexed(json_rows(data), lambda r: r["id"])
    associations = json.loads(read("SOURCE_ASSOCIATIONS.json"))["rows"]
    replay = json.loads(frozen_artifact(
        REPLAY_ARCHIVE, "HISTORICAL_5J_COMPARISON_RESULTS.json", "external_artifacts",
        manifest_folder=REMEDIATION))
    require(replay["exposed_nonindependent"] is True
            and replay["original_record_id_metrics_not_comparable_with_family_metrics"] is True,
            "Retrospective comparison scope changed")
    replay_rows = {r["case_id"]: r for _, r in indexed(
        enumerate(replay["results"], start=1), lambda r: r["case_id"]).values()}
    cases = {key: item for key, item in refs.items()
             if item[1]["category"] == "C4" and item[1]["split"] == "final"}
    rows = indexed(((line, row) for line, row in json_rows(read("RETRIEVAL_RESULTS.jsonl"))
                    if row["category"] == "C4" and row["split"] == "final"),
                   lambda r: (r["case_id"], r["mode"]))
    require(len(cases) == 18 and len({r["execution_id"] for _, r in cases.values()}) == 18
            and set(rows) == {(key, mode) for key in cases for mode in MODES},
            "Historical C4 final denominator or case-mode pairing changed")

    case_table, missing_table, completed = [], [], Counter()
    for case_id, (ref_line, case) in sorted(cases.items()):
        for mode in MODES:
            result_line, result = rows[case_id, mode]
            output, assessment, request = (result[k] for k in ("output", "assessment", "request"))
            identity = ("execution_id", "task_id", "variant_id")
            require(all(request[k] == case[k] for k in identity), f"Reference scope changed for {case_id}")
            for item in output["items"]:
                binding = associations[item["id"]]
                require(all(item[k] == binding[k] for k in (*identity, "source_path", "source_sha256"))
                        and all(item[k] == case[k] for k in identity),
                        f"Returned record scope/source mismatch for {case_id}/{mode}")
            fulfilled, absent = (assessment[k] for k in ("fulfilled_facets", "missing_facets"))
            require(set(fulfilled).isdisjoint(absent)
                    and set(fulfilled) | set(absent) == set(case["required_facets"])
                    and assessment["complete_required_evidence"] == (not absent),
                    f"Saved C4 facet records conflict for {case_id}/{mode}")
            completed[mode] += int(assessment["complete_required_evidence"])
            shared = {
                "case_id": case_id, "mode": mode, "execution_id": case["execution_id"],
                "saved_scope": span(request["interval"]), "reference_line": ref_line,
                "saved_result_line": result_line, "saved_result_digest": result["canonical_digest"],
            }
            case_table.append({
                **shared, "task_id": case["task_id"], "variant_id": case["variant_id"],
                "endpoint": result["endpoint"], "saved_api_status": output["status"],
                "reference_expected_status": case["expected_status"],
                "saved_assessment_status": assessment["sufficiency"],
                "saved_complete": str(assessment["complete_required_evidence"]).lower(),
                "required": joined(case["required_facets"]), "fulfilled": joined(fulfilled),
                "missing": joined(absent), "returned_record_ids": joined(r["id"] for r in output["items"]),
            })
            for facet in absent:
                stage, availability, notes, evidence = historical_proof(case, facet, refs, rows, replay_rows)
                missing_table.append({
                    "phase": "5J", **shared, "missing_obligation": facet, "observed_stage": stage,
                    "plan_status": "not_recorded", "saved_api_status": output["status"],
                    "source_availability": availability, "source_binding": evidence, "evidence_note": notes,
                })
    require(dict(completed) == {"exact": 10, "semantic": 10, "lexical": 8},
            "Historical C4 completeness differs from the frozen reported result")
    return case_table, missing_table


def phase5k():
    read = lambda name: frozen_artifact(REMEDIATION, name, "internal_artifacts")
    freeze = read_json(REMEDIATION / "HOLDOUT_FREEZE.json")
    data = read("FROZEN_HOLDOUT_DATASET.jsonl")
    require(file_hash(data) == freeze["dataset_sha256"], "Phase 5K reference freeze mismatch")
    implementation = read_json(REMEDIATION / "FROZEN_IMPLEMENTATION.json")["files"]
    for name in ("planner.py", "config.py"):
        require(file_hash((REMEDIATION / name).read_bytes()) == implementation[name],
                f"Phase 5K planner freeze mismatch: {name}")
    sys.path.insert(0, str(ROOT))
    from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.planner import interpret

    refs = indexed(json_rows(data), lambda r: r["id"])
    rows = indexed(json_rows(read("HOLDOUT_RETRIEVAL_RESULTS.jsonl")),
                   lambda r: (r["case_id"], r["mode"]))
    require(len(refs) == freeze["questions"] == 216
            and len({r["execution_id"] for _, r in refs.values()}) == freeze["executions"] == 24
            and len({r["variant_id"] for _, r in refs.values()}) == freeze["variants"] == 18
            and len({r["template_id"] for _, r in refs.values()}) == freeze["templates"] == 72,
            "Phase 5K V2 population differs from the freeze")
    output = []
    for case_id in TEMPORAL_CASES:
        ref_line, ref = refs[case_id]
        result_line, bundle = rows[case_id, "bundle"]
        companion_line, exact = rows[case_id, "exact"]
        plan = interpret(ref["query"], {"objects": {}, "frames": ref["frames"]}, ref["request"])
        require(ref["category"] == "C2" and ref["template_id"] == "C2-2"
                and set(ref["expected_families"]) == {JOINT_POSITION, "recorded_time"}
                and plan["status"] == "RESOLVED" and plan["families"] == ["recorded_time"]
                and bundle["status"] == "COMPLETE WITHIN VERIFIED CONTRACT"
                and bundle["returned_families"] == plan["families"]
                and bundle["metrics"]["complete_required_set"] is False
                and JOINT_POSITION in exact["returned_families"]
                and not exact["metrics"]["scope_or_value_errors"], f"Frozen evidence changed for {case_id}")
        samples = ref["reference_samples"][JOINT_POSITION]
        require([r["frame"] for r in samples] == ref["reference_frame_indices"]
                and all(len(r["value"]) == 7 and r["dtype"] == "float64" for r in samples),
                f"Frozen joint source values missing for {case_id}")
        refs_for_samples = [
            {"path": ref["source_path"], "sha256": ref["source_sha256"], "selector": r["selector"]}
            for r in samples
        ]
        output.append({
            "phase": "5K v2", "case_id": case_id, "mode": "bundle", "execution_id": ref["execution_id"],
            "saved_scope": f'{span(plan["seconds_interval"])} simulator seconds; frames {span(ref["reference_frame_indices"])}',
            "reference_line": ref_line, "saved_result_line": result_line,
            "saved_result_digest": bundle["canonical_digest"], "missing_obligation": JOINT_POSITION,
            "observed_stage": "query_to_plan_obligation_loss", "plan_status": plan["status"] + " recorded_time only",
            "saved_api_status": bundle["status"], "source_availability": "frozen_joint_values_and_exact_result",
            "source_binding": source_refs(refs_for_samples),
            "evidence_note": f"Same-case exact result on saved line {companion_line} includes joint position. "
                             "The parsed plan omitted it before retrieval.",
        })
    return output


def csv_text(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with the saved case and obligation tables.")
    parser.add_argument("--out-dir", type=Path, help="Write tables in a new output directory.")
    args = parser.parse_args()
    if args.check == (args.out_dir is not None):
        parser.error("choose either --check or --out-dir")
    cases, gaps = historical()
    tables = {HISTORICAL_CASES: csv_text(cases), MISSING_OBLIGATIONS: csv_text(gaps + phase5k())}
    if args.check:
        for name, table in tables.items():
            require((HERE / name).read_bytes() == table.encode("utf-8"), f"Saved table differs: {name}")
        print("RQ1 audit tables match the frozen records and the CPU planner replay.")
    else:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        destinations = {name: args.out_dir / name for name in tables}
        collisions = [name for name, path in destinations.items() if path.exists() or path.is_symlink()]
        require(not collisions, f"Choose an unused output directory. Existing files: {', '.join(collisions)}")
        for name, table in tables.items():
            with destinations[name].open("x", encoding="utf-8", newline="") as stream:
                stream.write(table)


if __name__ == "__main__":
    main()
