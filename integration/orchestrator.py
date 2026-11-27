"""Fail-closed orchestration for the M4 R1 v3 integration path.

``resume-task8a`` consumes the immutable, genuine Task 8A request and accepted
generation report and runs only the existing deterministic R1 v3 Critic route.
It does not claim a fresh end-to-end run: retrieval and Checker assessments
remain unavailable, the Critic has no R1 v3 model route, Revision consumes a
different contract, and human reasoning review remains required.

``generate-r1v3`` is the explicit fresh model entry point. It requires an
additional opt-in flag and a caller-provided frozen model configuration. This
command is never invoked by resume or CPU verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from evaluation.r1_v4.provenance import canonical, digest, strict_loads

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = Path("evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json")
DEFAULT_RUN = Path("evaluation/m4_20261127/integration/task8a_r1v3/DRAFTER_GENERATION_REPORT.json")
DEFAULT_ARGUMENT = Path("evaluation/m4_20261127/integration/task8a_r1v3/DRAFTER_ARGUMENT.json")
RUNNER_VERSION = "m4-orchestrator/0.1.0"


class OrchestrationError(RuntimeError):
    """An input, provenance, stage-contract, or artifact collision failed closed."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path):
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise OrchestrationError("required_input_unavailable:" + str(path)) from exc
    try:
        return strict_loads(raw.decode("utf-8")), _sha256(raw)
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise OrchestrationError("invalid_json_input:" + str(path)) from exc


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _source_snapshot(root: Path):
    """Bind a local run to HEAD and any uncommitted candidate files."""
    commit = _git_commit(root)
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=str(root), stderr=subprocess.DEVNULL, text=True
        ).strip()
        changed = subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only", "-z"], cwd=str(root), stderr=subprocess.DEVNULL
        ).decode("utf-8").split("\0")
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=str(root), stderr=subprocess.DEVNULL
        ).decode("utf-8").split("\0")
        paths = sorted({name for name in changed + untracked if name})
        files = {name: _sha256((root / name).read_bytes()) for name in paths if (root / name).is_file()}
        return {"commit": commit, "branch": branch or "detached", "working_tree_dirty": bool(paths),
                "changed_file_count": len(paths), "working_tree_changes_sha256": digest(files)}
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return {"commit": commit, "branch": "unavailable", "working_tree_dirty": None,
                "changed_file_count": None, "working_tree_changes_sha256": "unavailable"}


def _atomic_new_or_identical(path: Path, data: bytes) -> str:
    """Create output without overwriting; permit exact-byte recovery after interruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_bytes()
        if existing != data:
            raise OrchestrationError("output_collision_existing_artifact_differs:" + str(path))
        return _sha256(existing)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise OrchestrationError("output_collision_existing_artifact_differs:" + str(path))
        return _sha256(path.read_bytes())
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _validate_critic_report(report, request_id: str, expected_objects):
    """Validate the R1 v3 Critic's current contract without inventing a new schema."""
    required = {
        "schema_version", "critic_version", "request_id", "execution_id", "test_fixture",
        "input_valid", "review_status", "llm", "provenance", "criticisms", "checker_admission",
        "object_reviews", "drafter_evidence_gaps", "unresolved_concerns", "safety_claim_verified",
        "reasoning_review", "summary",
    }
    if not isinstance(report, dict) or not required.issubset(report):
        raise OrchestrationError("critic_report_missing_required_fields")
    if report["schema_version"] != "critic-report/r1v3/0.1.0" or report["request_id"] != request_id:
        raise OrchestrationError("critic_report_contract_or_request_mismatch")
    if report["review_status"] != "completed" or report["input_valid"] is not True:
        raise OrchestrationError("critic_report_not_completed")
    if report["safety_claim_verified"] is not False:
        raise OrchestrationError("critic_must_not_verify_safety_claim")
    review = report["reasoning_review"]
    if not isinstance(review, dict) or review.get("status") != "required":
        raise OrchestrationError("human_reasoning_review_must_remain_required")
    reviews = report["object_reviews"]
    if not isinstance(reviews, list) or [row.get("object_id") for row in reviews] != list(expected_objects):
        raise OrchestrationError("critic_object_roster_or_order_mismatch")
    findings = report["criticisms"]
    if not isinstance(findings, list):
        raise OrchestrationError("critic_findings_must_be_a_list")
    finding_ids = [row.get("criticism_id") for row in findings if isinstance(row, dict)]
    if len(finding_ids) != len(findings) or len(finding_ids) != len(set(finding_ids)):
        raise OrchestrationError("critic_findings_malformed_or_duplicate")
    if not isinstance(report["checker_admission"], list) or not isinstance(report["provenance"], dict):
        raise OrchestrationError("critic_admission_or_provenance_malformed")
    return True


def stage_decisions(*, checker_status, admission_status, retrieval_plan_status,
                    retrieval_status, critic_status, actionable_findings,
                    revision_contract_available=False, revision_status=None,
                    second_critic_status=None):
    """Pure fail-closed stage policy, exported to make orchestration rules testable."""
    retrieval_complete = (retrieval_plan_status == "COMPLETE" and
                          retrieval_status == "COMPLETE WITHIN VERIFIED CONTRACT")
    can_assert_physical = checker_status == "available" and admission_status == "admitted"
    if not retrieval_complete:
        drafter = "blocked_incomplete_or_unavailable_retrieval"
    else:
        drafter = "eligible_for_validated_request_construction"
    if actionable_findings:
        if not revision_contract_available:
            revision = "blocked_contract_unavailable"
        elif revision_status == "accepted":
            revision = "completed"
        elif revision_status == "failed":
            revision = "failed"
        else:
            revision = "eligible"
    else:
        revision = "skipped_no_actionable_finding"
    if revision_status == "accepted" and second_critic_status != "accepted":
        second = "rejected_or_unavailable"
    elif revision_status == "accepted":
        second = "accepted"
    else:
        second = "not_applicable"
    return {
        "physical_claim_admission": "eligible_only_after_all_gates" if can_assert_physical else "unavailable_or_not_admitted",
        "drafter": drafter,
        "revision": revision,
        "second_critic": second,
        "final_safety_case": "not_approved_human_reasoning_review_required",
    }


def run_saved_task8a(root=DEFAULT_ROOT, request_path=DEFAULT_REQUEST,
                     run_path=DEFAULT_RUN, argument_path=DEFAULT_ARGUMENT, out_dir=None,
                     *, checker_assessments=(), checker_source_root=None, registry=None,
                     trusted_review_hashes=(), task_id=None):
    """CPU-resume a genuine Task 8A accepted run through the deterministic R1 v3 Critic."""
    root = Path(root).resolve()
    request_path, run_path, argument_path = (root / Path(p) for p in (request_path, run_path, argument_path))
    out_dir = Path(out_dir or (root / "artifacts/m4-orchestration/task8a-resume" )).resolve()
    start_wall, start_cpu = time.monotonic(), time.process_time()
    request, request_file_hash = _read_json(request_path)
    generation_report, report_file_hash = _read_json(run_path)
    argument, argument_file_hash = _read_json(argument_path)

    from drafter.r1v3_profile import validate_argument, validate_request
    from drafter.r1v3_generation import validate_accepted_run
    from evaluation.m4_20261127.integration.build_r1v3_request import build as rebuild_original_request
    from integration.handoff import build_critic_request
    from critic.r1v3 import review as critic_review
    from critic import llm as critic_llm

    validate_request(request)
    if request != strict_loads(rebuild_original_request()):
        raise OrchestrationError("original_frozen_request_differs_from_builder_rebuild")
    accepted_argument = validate_accepted_run(request, generation_report)
    validate_argument(argument, request)
    if accepted_argument != argument:
        raise OrchestrationError("saved_argument_differs_from_generation_report")
    if generation_report.get("status") != "accepted":
        raise OrchestrationError("saved_generation_not_accepted")

    critic_request, handoff_provenance = build_critic_request(
        request, generation_report, checker_assessments=checker_assessments
    )
    critic_report = critic_review(
        critic_request, critic_llm.NullLLM(), source_root=checker_source_root, registry=registry,
        trusted_review_hashes=trusted_review_hashes, task_id=task_id,
    )
    protected_objects = request["requirement_configuration"]["protected_objects"]
    _validate_critic_report(critic_report, critic_request["request_id"], protected_objects)
    if critic_report["execution_id"] != request["target_execution"]["execution_id"]:
        raise OrchestrationError("critic_execution_identity_mismatch")
    if critic_report["provenance"].get("critic_request_sha256") != digest(critic_request):
        raise OrchestrationError("critic_request_provenance_mismatch")
    # With no supplied assessment, the frozen Task 8A argument must remain
    # conservative. Supplied assessments never edit this immutable argument.
    if not checker_assessments:
        backing = argument["argument_bundle"]["execution_conclusion"].get("outcome_backing", {})
        if set(backing) != set(request["requirement_configuration"]["protected_objects"]):
            raise OrchestrationError("argument_outcome_backing_roster_mismatch")
        if argument["argument_bundle"]["execution_conclusion"].get("object_outcomes") != {
            object_id: "insufficient_information" for object_id in request["requirement_configuration"]["protected_objects"]
        }:
            raise OrchestrationError("saved_object_outcomes_not_conservative")
        for object_id, row in backing.items():
            if row.get("outcome") != "insufficient_information" or row.get("checker_assessment") is not None:
                raise OrchestrationError("unexpected_physical_outcome_or_checker_backing:" + object_id)

    actionable = [row for row in critic_report["criticisms"] if row.get("blocking") is True]
    assessments_admitted = bool(critic_report["checker_admission"]) and all(
        row.get("admission_status") == "admitted" for row in critic_report["checker_admission"]
    )
    decisions = stage_decisions(
        checker_status="unavailable" if not checker_assessments else "validated",
        admission_status="admitted" if assessments_admitted else "not_admitted",
        retrieval_plan_status="NOT_RUN", retrieval_status="NOT_RUN", critic_status="completed",
        actionable_findings=actionable, revision_contract_available=False,
    )
    # R1 v3 resume starts after the Drafter. Retrieval and Checker remain explicitly not run.
    stages = {
        "source_execution": {"status": "validated_from_bound_request", "execution_id": request["target_execution"]["execution_id"]},
        "evidence_package": {"status": "validated_immutable_request_package", "sha256": request["source_package_sha256"]},
        "evidence_registration": {"status": "not_run", "reason": "saved Task 8A source package is already frozen"},
        "rq1_retrieval": {"status": "not_run", "reason": "no authorized local indexed evidence database supplied"},
        "checker_execution": {"status": "unavailable" if not checker_assessments else "assessment_supplied_for_independent_replay"},
        "checker_admission": {"status": "admitted" if assessments_admitted else "not_admitted",
                              "assessment_count": len(critic_report["checker_admission"])},
        "drafter_generation": {"status": "accepted_genuine_saved_run", "run_id": generation_report["run_id"]},
        "drafter_host_validation": {"status": "passed", "argument_sha256": argument_file_hash},
        "critic_request": {"status": "validated", "request_id": critic_request["request_id"]},
        "critic_execution": {"status": "completed_deterministic_cpu", "critic_version": critic_report["critic_version"]},
        "critic_response_validation": {"status": "passed", "schema_version": critic_report["schema_version"]},
        "revision": {"status": decisions["revision"], "reason": "R1 v3 Critic findings do not map to the current Revision R1 v2 contract" if actionable else "no actionable finding"},
        "second_critic": {"status": "not_applicable" if not actionable else "blocked_revision_contract"},
        "final_argument": {"status": "draft_pending_human_reasoning_review", "safety_claim_verified": False},
    }
    files = {
        "CRITIC_REQUEST.json": canonical(critic_request) + b"\n",
        "CRITIC_REPORT.json": canonical(critic_report) + b"\n",
        "HANDOFF_PROVENANCE.json": canonical(handoff_provenance) + b"\n",
    }
    artifact_hashes = {name: _atomic_new_or_identical(out_dir / name, data) for name, data in files.items()}
    source_snapshot = _source_snapshot(root)
    commit = source_snapshot["commit"]
    manifest = {
        "schema_version": "m4-orchestration-run/0.1.0", "runner_version": RUNNER_VERSION,
        "run_kind": "resumed_saved_genuine_task8a_downstream_cpu", "source_commit": commit,
        "source_snapshot": source_snapshot,
        "component_versions": {"drafter_request": request["schema_version"],
                                "drafter_generation_report": generation_report["schema_version"],
                                "critic": critic_report["critic_version"],
                                "rq1_planner": "requested-obligations-2.0.0_available_not_run"},
        "inputs": {"request_file_sha256": request_file_hash, "request_sha256": digest(request),
                   "generation_report_file_sha256": report_file_hash,
                   "generation_report_sha256": digest(generation_report),
                   "argument_file_sha256": argument_file_hash,
                   "source_package_sha256": request["source_package_sha256"]},
        "execution_id": request["target_execution"]["execution_id"],
        "requirement": {"id": request["requirement_configuration"]["requirement_id"],
                        "version": request["requirement_configuration"]["requirement_version"]},
        "stages": stages, "stage_policy": decisions,
        "explicit_evidence_gaps": request["evidence_gaps"],
        "human_review": {"reasoning_review": "required", "physical_safety_approval": "not_claimed"},
        "model_configuration": generation_report["configuration"],
        "generation_provenance": {
            "model_id": argument["generation_provenance"]["model_id"],
            "model_revision": argument["generation_provenance"]["model_revision"],
            "backend": argument["generation_provenance"]["backend"],
            "generation_run_id": generation_report["run_id"],
            "generation_seconds": generation_report.get("elapsed_seconds"),
            "generation_configuration_sha256": generation_report.get("configuration_sha256"),
            "prompt_sha256": argument["generation_provenance"]["prompt_sha256"],
            "raw_output_sha256": argument["generation_provenance"]["raw_output_sha256"],
            "decoder_schema_sha256": digest(generation_report["trace"]["json_schema"]),
            "host_validation_schema_sha256": generation_report["trace"]["validation_schema_sha256"],
            "completion_status": generation_report["trace"]["completion"]["status"],
            "response_sha256": generation_report["trace"]["completion"]["response_sha256"],
        },
        "model_inference_this_run": False,
        "resource_usage": {"wall_seconds": round(time.monotonic() - start_wall, 6),
                           "process_cpu_seconds": round(time.process_time() - start_cpu, 6)},
        "artifacts": artifact_hashes,
        "reproduction_command": "python -m integration.orchestrator resume-task8a --out-dir <new-or-identical-output-dir>",
        "final_status": "draft_pending_reasoning_review_and_downstream_integration",
        "safety_claim_verified": False,
    }
    manifest_path = out_dir / "RUN_MANIFEST.json"
    if manifest_path.exists():
        previous, manifest_hash = _read_json(manifest_path)
        stable_keys = ("run_kind", "source_commit", "source_snapshot", "inputs", "execution_id", "requirement", "artifacts")
        if any(previous.get(key) != manifest.get(key) for key in stable_keys):
            raise OrchestrationError("output_collision_existing_manifest_has_different_inputs")
        manifest = previous
    else:
        manifest_data = canonical(manifest) + b"\n"
        manifest_hash = _atomic_new_or_identical(manifest_path, manifest_data)
    return {"manifest": manifest, "manifest_sha256": manifest_hash, "output_dir": str(out_dir)}


def run_fresh_generation(root, request_path, model_config_path, out_dir, *, authorized=False):
    """Explicit genuine generation entry point; never used by CPU resume."""
    if not authorized:
        raise OrchestrationError("model_execution_not_authorized; pass --authorize-model-execution only after approval")
    from drafter.generation import generate_argument
    from drafter.llm import load_local_model_config
    from evaluation.m4_20261127.integration.build_r1v3_request import build as rebuild_original_request

    root = Path(root).resolve()
    request, _ = _read_json(root / request_path)
    if request != strict_loads(rebuild_original_request()):
        raise OrchestrationError("original_frozen_request_differs_from_builder_rebuild")
    config = load_local_model_config(root / model_config_path)
    output = Path(out_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise OrchestrationError("fresh_generation_output_directory_must_be_empty")
    output.mkdir(parents=True, exist_ok=True)
    report = generate_argument(request, config)
    payload = canonical(report) + b"\n"
    report_hash = _atomic_new_or_identical(output / "DRAFTER_GENERATION_REPORT.json", payload)
    argument_hash = None
    if report.get("argument") is not None:
        argument_hash = _atomic_new_or_identical(
            output / "DRAFTER_ARGUMENT.json", canonical(report["argument"]) + b"\n"
        )
    completion = report.get("trace", {}).get("completion") or {}
    provenance = report.get("argument", {}).get("generation_provenance", {})
    generation_manifest = {
        "schema_version": "m4-orchestration-run/0.1.0", "runner_version": RUNNER_VERSION,
        "run_kind": "fresh_genuine_model_attempt", "source_commit": _git_commit(root),
        "source_snapshot": _source_snapshot(root),
        "request_sha256": digest(request), "run_id": report.get("run_id"),
        "model_configuration": report.get("configuration"),
        "model_configuration_sha256": report.get("configuration_sha256"),
        "model_called": report.get("model_called"), "completion_attempted": report.get("completion_attempted"),
        "generation_status": report.get("status"), "diagnostics": report.get("diagnostics"),
        "generation_seconds": report.get("elapsed_seconds"),
        "prompt_sha256": provenance.get("prompt_sha256"),
        "raw_output_sha256": provenance.get("raw_output_sha256"),
        "decoder_schema_sha256": digest(report["trace"]["json_schema"]) if report.get("trace", {}).get("json_schema") else None,
        "host_schema_sha256": report.get("trace", {}).get("validation_schema_sha256"),
        "completion_status": completion.get("status"), "response_sha256": completion.get("response_sha256"),
        "artifacts": {"generation_report_sha256": report_hash, "argument_sha256": argument_hash},
        "model_inference_is_not_safety_approval": True,
    }
    _atomic_new_or_identical(output / "RUN_MANIFEST.json", canonical(generation_manifest) + b"\n")
    if report.get("status") == "accepted":
        run_saved_task8a(
            root, request_path,
            output / "DRAFTER_GENERATION_REPORT.json",
            output / "DRAFTER_ARGUMENT.json",
            output / "downstream-cpu",
        )
    return report


def run_rq1_v2_retrieval(*, index_path, expected_index_sha256, query, execution_id,
                         task_id=None, variant_id=None, object_id=None, frame_interval=None):
    """Invoke the actual v2 retrieval entry point; the pinned index must be supplied by caller."""
    from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import BundleRequest
    from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle_v2 import RequestedObligationsRetriever
    retriever = RequestedObligationsRetriever(index_path, expected_index_sha256)
    try:
        request = BundleRequest(query=query, execution_id=execution_id, task_id=task_id,
                                variant_id=variant_id, object_id=object_id,
                                frame_interval=tuple(frame_interval) if frame_interval else None)
        result = retriever.retrieve(request)
        result["physical_evidence_eligibility"] = "NOT_EVALUATED"
        result["safety_claim_sufficiency"] = "NOT_EVALUATED"
        if result.get("planner_version") != "requested-obligations-2.0.0":
            raise OrchestrationError("rq1_v2_planner_not_selected")
        if result.get("obligation_plan_status") != "COMPLETE" and result.get("completeness_status") == "COMPLETE WITHIN VERIFIED CONTRACT":
            raise OrchestrationError("rq1_incomplete_plan_cannot_report_complete_retrieval")
        return result
    finally:
        retriever.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    resume = sub.add_parser("resume-task8a", help="CPU-validate the genuine saved draft and run deterministic R1 v3 Critic")
    resume.add_argument("--root", default=str(DEFAULT_ROOT))
    resume.add_argument("--request", default=str(DEFAULT_REQUEST))
    resume.add_argument("--generation-report", default=str(DEFAULT_RUN))
    resume.add_argument("--argument", default=str(DEFAULT_ARGUMENT))
    resume.add_argument("--out-dir", required=True, help="new directory or exact-output recovery directory")
    fresh = sub.add_parser("generate-r1v3", help="one genuine model attempt; requires explicit authorization")
    fresh.add_argument("--root", default=str(DEFAULT_ROOT))
    fresh.add_argument("--request", default=str(DEFAULT_REQUEST))
    fresh.add_argument("--model-config", required=True)
    fresh.add_argument("--out-dir", required=True)
    fresh.add_argument("--authorize-model-execution", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "resume-task8a":
            result = run_saved_task8a(args.root, args.request, args.generation_report, args.argument, args.out_dir)
        else:
            result = run_fresh_generation(args.root, args.request, args.model_config, args.out_dir,
                                          authorized=args.authorize_model_execution)
        if args.command == "resume-task8a":
            manifest = result["manifest"]
            print(json.dumps({
                "run_kind": manifest["run_kind"], "final_status": manifest["final_status"],
                "output_dir": result["output_dir"], "manifest_sha256": result["manifest_sha256"],
                "stages": {name: row["status"] for name, row in manifest["stages"].items()},
                "safety_claim_verified": manifest["safety_claim_verified"],
            }, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({"status": result.get("status"), "run_id": result.get("run_id"),
                              "elapsed_seconds": result.get("elapsed_seconds"),
                              "model_called": result.get("model_called")}, indent=2, ensure_ascii=False))
        return 0
    except (OrchestrationError, ValueError, TypeError, OSError) as exc:
        print("orchestration failed closed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
