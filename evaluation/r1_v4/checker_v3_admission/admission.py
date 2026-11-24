"""Scope-bound admission for sealed R1 v3 Checker output."""

from pathlib import Path
import sqlite3

from jsonschema import Draft202012Validator

from evaluation.r1_v4.evidence_registry_gsn.adapter import PHYSICAL_GATES
from evaluation.r1_v4.evidence_registry_gsn.registry_v3 import R1_V3, RegistryV3
from evaluation.r1_v4.provenance import bytes_digest, canonical, digest, load, strict_loads


HERE = Path(__file__).resolve().parent
CHECKER = HERE.parents[1] / "r1_v3"
SCHEMA = load(HERE / "contract.schema.json")
GATE_REQUIREMENTS = {
    "G03_geometry_empirical_admission": "independent calibration of the native geometry",
    "G07_static_coverage_composition": "qualified composition of compatible static observation windows",
    "G09_contact_based_physical_evidence": "validation of the physical interpretation of recorded contacts",
    "G04_initial_support_applicability": "validation of initial support or established absence",
    "G05_validated_falling_witness": "validation of the falling-witness method",
    "G06_qualified_negative_certificate": "validation of the scoped negative-certificate method",
    "G10_uncertainty_propagation": "validated uncertainty bounds and their propagation",
    "G11_temporal_empirical_admission": "validation of the saved-frame boundary and phase uncertainty",
    "G12_independent_reference_validation": "independent reference validation for this source group",
}
NEGATIVE = "no_violation_observed_within_reviewed_coverage"
SCOPE_FIELDS = ("execution_id", "task_id", "object_id", "trajectory_sha256")


def _validate(definition, value):
    validator = Draft202012Validator({
        "$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{definition}",
    })
    error = next(validator.iter_errors(value), None)
    if error:
        field = ".".join(map(str, error.absolute_path)) or definition
        raise ValueError(f"invalid {definition} field {field}: {error.validator}")


def frozen_checker_configuration():
    """Return the versioned configuration with its frozen implementation binding."""
    freeze_bytes = (CHECKER / "FREEZE.json").read_bytes()
    freeze = strict_loads(freeze_bytes)
    config_bytes = (CHECKER / "config.json").read_bytes()
    configuration_sha256 = bytes_digest(config_bytes)
    for name, data in (
        ("config.json", config_bytes),
        ("r1_checker.py", (CHECKER / "r1_checker.py").read_bytes()),
        ("execute.py", (CHECKER / "execute.py").read_bytes()),
    ):
        if bytes_digest(data) != freeze["implementation_files"][name]:
            raise ValueError(f"frozen R1 v3 Checker file hash mismatch: {name}")
    configuration = strict_loads(config_bytes)
    _validate("configuration", configuration)
    return {
        "version": configuration["checker_version"],
        "configuration": configuration,
        "configuration_sha256": configuration_sha256,
        "implementation_freeze_sha256": bytes_digest(freeze_bytes),
        "source_commit": freeze["source_commit"],
    }


def _read_bound_json(reference, root):
    path = Path(reference["path"])
    if path.name.casefold() == "human_reference_evaluation_only.json":
        raise ValueError("evaluation-only human reference is outside the admission contract")
    if not path.is_relative_to(root) or ".." in path.parts:
        raise ValueError("artifact outside the approved source root")
    try:
        if path.resolve(strict=True) != path or not path.is_file():
            raise ValueError("artifact must be a regular file without symlinks")
        data = path.read_bytes()
    except (OSError, RuntimeError) as error:
        raise ValueError(f"cannot read bound artifact: {path.name}") from error
    if bytes_digest(data) != reference["sha256"]:
        raise ValueError(f"artifact hash mismatch: {path.name}")
    return strict_loads(data)


def _interval(value):
    return (
        isinstance(value, list) and len(value) == 2
        and all(type(frame) is int and frame >= 0 for frame in value) and value[0] <= value[1]
    )


def _intervals(value, scope):
    if not isinstance(value, list):
        raise ValueError("invalid Checker coverage intervals")
    previous = None
    for interval in value:
        if (
            not _interval(interval) or interval[0] < scope[0] or interval[1] > scope[1]
            or (previous is not None and interval[0] <= previous + 1)
        ):
            raise ValueError("Checker coverage intervals must be ordered and inside the saved-frame scope")
        previous = interval[1]
    return value


def _read_prediction(request, root, checker):
    scope, binding = request["scope"], request["prediction"]
    seal = _read_bound_json(binding["seal"], root)
    artifact = binding["artifact"]
    if (
        not isinstance(seal, dict) or seal.get("reference_answers_loaded") is not False
        or not isinstance(seal.get("files"), dict)
        or seal["files"].get(Path(artifact["path"]).name) != artifact["sha256"]
    ):
        raise ValueError("prediction seal must bind the artifact and exclude reference answers")
    rows = _read_bound_json(artifact, root)
    index = binding["row_index"]
    if type(index) is not int or not isinstance(rows, list) or index >= len(rows):
        raise ValueError("prediction selector does not resolve to a saved row")
    identity = {
        "run_id": scope["execution_id"], "canonical_object_id": scope["object_id"],
        "requirement_id": request["requirement_id"], "requirement_version": request["requirement_version"],
    }
    matches = [
        i for i, row in enumerate(rows)
        if isinstance(row, dict) and all(row.get(key) == value for key, value in identity.items())
    ]
    if matches != [index]:
        raise ValueError("prediction must resolve to one row for the exact requirement, execution and object")
    prediction = rows[index]
    expected = {
        "recording_sha256": scope["trajectory_sha256"],
        "checker_version": checker["version"],
        "configuration_sha256": checker["configuration_sha256"],
        "implementation_freeze_sha256": checker["implementation_freeze_sha256"],
        "source_commit": checker["source_commit"],
    }
    window = prediction.get("requested_frame_interval")
    if (
        any(prediction.get(key) != value for key, value in expected.items())
        or not _interval(window) or window != scope["frame_interval"]
    ):
        raise ValueError("prediction trajectory, Checker provenance or frame scope mismatch")
    applicability, outcome = prediction.get("applicability"), prediction.get("outcome")
    if (
        applicability not in ("applies", "does_not_apply", "insufficient_information")
        or outcome not in ("violation", NEGATIVE, "not_applicable", "insufficient_information")
        or (outcome == "not_applicable") != (applicability == "does_not_apply")
        or (outcome in ("violation", NEGATIVE) and applicability != "applies")
        or not isinstance(prediction.get("events"), list)
        or any(not isinstance(event, dict) for event in prediction["events"])
    ):
        raise ValueError("invalid or inconsistent Checker decision fields")
    development = any(
        source.get(flag) is True
        for source in (prediction, seal)
        for flag in ("development_only", "development_exposed", "synthetic")
    )
    return prediction, {
        "sha256": artifact["sha256"], "seal_sha256": binding["seal"]["sha256"],
        "row_index": index, "row_sha256": digest(prediction),
    }, development


def _archived_development_scope(scope, prediction_sha256):
    reference = load(CHECKER.parent / "r1_reference" / "recordings.json")
    seal = load(CHECKER / "execution" / "PREDICTION_SEAL.json")
    for run in reference["runs"]:
        if scope["execution_id"] == run["run_id"] or scope["trajectory_sha256"] == run["recording_sha256"]:
            if (
                scope["execution_id"] != run["run_id"] or scope["trajectory_sha256"] != run["recording_sha256"]
                or scope["task_id"] != reference["task_id"]
            ):
                raise ValueError("archived recording execution, task or trajectory mismatch")
            return True
    return prediction_sha256 == seal["files"]["predictions.json"]


def _read_review(request, root, input_sha256, archived_development, trusted_review_hashes):
    if request["purpose"] == "development_diagnostic" or archived_development:
        return None, "development_only_prediction"
    reference = request.get("review")
    if reference is None:
        return None, "independent_review_missing"
    if reference["sha256"] not in trusted_review_hashes:
        return None, "independent_review_not_authorized"
    review = _read_bound_json(reference, root)
    _validate("review", review)
    if review["input_sha256"] != input_sha256 or set(review["gates"]) != set(PHYSICAL_GATES):
        raise ValueError("independent review scope or gate inventory mismatch")
    return review, None


def _evidence_ledger(citations, registry, scope, limits):
    if len({citation["record_id"] for citation in citations}) != len(citations):
        raise ValueError("duplicate record in citation ledger")
    identity = {key: scope[key] for key in SCOPE_FIELDS}
    ledger = []
    for citation in sorted(citations, key=lambda item: item["record_id"]):
        frames = citation["frames"]
        if any(type(frame) is not int or not limits[0] <= frame <= limits[1] for frame in frames):
            raise ValueError("citation falls outside the assessment or initial-support scope")
        row = {"citation": citation, "status": "blocked", "diagnostic": "registry_unavailable", "binding": None}
        if registry is not None:
            try:
                record = registry.resolve_citation(**identity, **citation)
            except (ValueError, OSError, sqlite3.DatabaseError):
                row["diagnostic"] = "citation_failed_source_or_scope_validation"
            else:
                row.update(
                    status="verified_source", diagnostic=None,
                    binding={
                        "source": record["source"], "native_binding": record.get("native_binding"),
                        "saved_frames": [item for item in record["saved_frames"] if item["frame"] in frames],
                    },
                )
        ledger.append(row)
    return ledger


def _fall_witness(prediction, index, frame_interval):
    first, last = frame_interval
    for offset, event in enumerate(prediction["events"]):
        evidence = event.get("evidence")
        interval = event.get("interval")
        onset = event.get("onset_bracket")
        if (
            event.get("type") != "r1_fall" or event.get("scope") != "in_scope"
            or event.get("status") != "established" or event.get("phase") != "departure"
            or any(event.get(key) != prediction[key] for key in ("run_id", "canonical_object_id", "requirement_version"))
            or not isinstance(event.get("event_id"), str) or not event["event_id"]
            or not isinstance(evidence, dict) or evidence.get("lift_event_id") is not None
            or not _interval(interval) or not _interval(onset)
        ):
            continue
        downward = evidence.get("downward_motion_bracket")
        if (
            not _interval(downward) or onset[1] - onset[0] != 1 or downward[1] - downward[0] != 1
            or onset != evidence.get("support_departure_bracket") or event.get("onset") != onset[1]
            or not first - 1 <= interval[0] <= onset[0] < onset[1] <= downward[1] <= interval[1] <= last
            or onset[1] < first or downward[0] < onset[0]
        ):
            continue
        return {"event_id": event["event_id"], "selector": f"/{index}/events/{offset}", "interval": interval}
    return None


def _encloses(intervals, start, end):
    return any(lo <= start and end <= hi for lo, hi in intervals)


def _qualification(prediction, prediction_binding, frame_interval, stencil, measurement, negative, ledger):
    first, last = frame_interval
    initial = prediction.get("initial_support")
    applicability, outcome = prediction["applicability"], prediction["outcome"]
    issues = {}
    blockers = []
    witness = None
    if not isinstance(initial, dict):
        initial = {}
    initial_evidence = initial.get("evidence")
    if not isinstance(initial_evidence, dict):
        initial_evidence = {}
    chain = initial_evidence.get("support_chain")
    support = initial.get("support_class")
    has_support = (
        support in ("direct_stable_table", "indirect_stable_table")
        and isinstance(chain, list) and len(chain) >= 2
        and all(isinstance(item, str) and item for item in chain)
        and len(set(chain)) == len(chain)
        and chain[0] == prediction["canonical_object_id"] and chain[-1] == "living_room_table"
    )
    if (
        initial.get("applicability") != applicability or initial_evidence.get("frames") != stencil
        or initial_evidence.get("boundary_frame") != first
        or not (has_support if applicability == "applies" else support == "established_absence")
    ):
        issues["G04_initial_support_applicability"] = "The Checker lacks a matching, qualified initial-support result."

    spans = [(stencil[0], stencil[-1])]
    if outcome == "insufficient_information":
        blockers.append("checker_abstained")
    if outcome == "violation":
        witness = _fall_witness(prediction, prediction_binding["row_index"], frame_interval)
        if witness is None or not _encloses(measurement, max(first, witness["interval"][0]), witness["interval"][1]):
            issues["G05_validated_falling_witness"] = "The Checker lacks a scoped fall witness with measurement coverage."
        else:
            spans.append(tuple(witness["interval"]))
    if outcome in (NEGATIVE, "not_applicable") and any(
        event.get("type") == "r1_fall" and event.get("scope") == "in_scope" for event in prediction["events"]
    ):
        blockers.append("checker_outcome_conflicts_with_an_in_scope_fall")
    if outcome == NEGATIVE:
        spans.append((first, last))
        if not (_encloses(measurement, first, last) and _encloses(negative, first, last)):
            for gate in ("G06_qualified_negative_certificate", "G07_static_coverage_composition"):
                issues[gate] = "The Checker lacks qualified negative coverage for the full saved-frame interval."

    available = {family: set() for family in ("object_pose", "native_geometry", "contact", "timestamp")}
    for row in ledger:
        if row["status"] != "verified_source":
            continue
        family = row["citation"]["measurement_type"]
        if family in available:
            available[family].update(row["citation"]["frames"])
        if family in ("object_pose", "native_geometry", "contact"):
            available["timestamp"].update(
                item["frame"] for item in row["binding"]["saved_frames"] if "simulator_time_seconds" in item
            )
    for family, gate in (
        ("object_pose", "G04_initial_support_applicability"),
        ("native_geometry", "G03_geometry_empirical_admission"),
        ("contact", "G09_contact_based_physical_evidence"),
        ("timestamp", "G11_temporal_empirical_admission"),
    ):
        if any(sum(lo <= frame <= hi for frame in available[family]) != hi - lo + 1 for lo, hi in spans):
            issues.setdefault(gate, f"Verified {family} records do not cover the required saved frames.")
    return {"applicability": applicability, "outcome": outcome, "witness_event": witness}, issues, blockers


def _gate_ledger(review, issues, verified):
    ledger = []
    for gate in PHYSICAL_GATES:
        proof = None if review is None else review["gates"][gate]
        reason = issues.get(gate)
        if reason is None and proof is None:
            reason = f"Authorized review is required for {GATE_REQUIREMENTS[gate]}."
        if reason is None and not set(proof["evidence_ids"]) <= verified:
            reason = "The independent review cites missing or unverified evidence."
        ledger.append({
            "gate_id": gate,
            "status": "blocked" if reason else "verified",
            "reason": reason or f"An authorized scoped review documents {GATE_REQUIREMENTS[gate]}.",
            "evidence_ids": [] if reason else sorted(proof["evidence_ids"]),
            "verification_sha256": None if reason else proof["verification_sha256"],
        })
    return ledger


def assess(request, *, source_root, registry=None, trusted_review_hashes=()):
    """Return a hash-bound assessment. Authorization comes from deployment configuration."""
    _validate("request", request)
    if registry is not None and not isinstance(registry, RegistryV3):
        raise ValueError("admission requires the R1 v3 registry")
    if isinstance(trusted_review_hashes, (str, bytes)):
        raise ValueError("trusted_review_hashes must contain complete receipt hashes")
    trusted = frozenset(trusted_review_hashes)
    root = Path(source_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("approved source root must be a directory")
    checker = frozen_checker_configuration()
    configuration, scope = checker["configuration"], request["scope"]
    interval = scope["frame_interval"]
    if not _interval(interval) or interval[0] != configuration["start_frame"] or scope["object_id"] not in configuration["objects"]:
        raise ValueError("scope must use the frozen initial boundary and a named protected object")
    stencil = [interval[0] + offset for offset in configuration["initial_stencil_offsets"]]
    limits = (stencil[0], max(interval[1], stencil[-1]))
    prediction, prediction_binding, declared_development = _read_prediction(request, root, checker)
    measurement = _intervals(prediction.get("measurement_frame_intervals"), interval)
    negative = _intervals(prediction.get("applicable_observation_intervals"), interval)
    if any(not _encloses(measurement, lo, hi) for lo, hi in negative):
        raise ValueError("Checker negative intervals are outside its measurement coverage")
    input_sha256 = digest({key: value for key, value in request.items() if key != "review"})
    archived_development = _archived_development_scope(scope, prediction_binding["sha256"])
    review, denial = _read_review(request, root, input_sha256, declared_development or archived_development, trusted)
    evidence = _evidence_ledger(request["citations"], registry, scope, limits)
    verified = {row["citation"]["record_id"] for row in evidence if row["status"] == "verified_source"}
    conclusion, issues, blockers = _qualification(
        prediction, prediction_binding, interval, stencil, measurement, negative, evidence,
    )
    if denial:
        blockers.append(denial)
    if len(verified) != len(evidence):
        blockers.append("unverified_registry_citations")
    gates = _gate_ledger(review, issues, verified)
    blockers.extend(row["gate_id"] for row in gates if row["status"] == "blocked")
    admitted = not blockers
    result = {
        "assessment_schema_version": "1.0.0",
        "requirement_id": "R1",
        "requirement_version": R1_V3,
        "purpose": request["purpose"],
        "scope": scope,
        "input_sha256": input_sha256,
        "checker": checker,
        "prediction": prediction_binding,
        "coverage": {
            "checker_reported_measurement_intervals": measurement,
            "checker_reported_negative_intervals": negative,
            "continuous_time_coverage": False,
        },
        "evidence_ledger": evidence,
        "gate_ledger": gates,
        "review": None if review is None else {
            "sha256": request["review"]["sha256"], "review_id": review["review_id"],
            "source_group_id": review["source_group_id"],
        },
        "admission_status": "admitted" if admitted else "not_admitted",
        "blockers": sorted(set(blockers)),
        "empirical_admission_enabled": admitted,
        "conclusion": conclusion if admitted else None,
    }
    result["assessment_hash"] = digest(result)
    _validate("assessment", result)
    # The caller can edit either document without altering the other.
    return strict_loads(canonical(result))


def validate_assessment(assessment, request, *, source_root, registry=None, trusted_review_hashes=()):
    """Reproduce the assessment from its sources and the current trust policy."""
    _validate("assessment", assessment)
    expected = assess(
        request, source_root=source_root, registry=registry, trusted_review_hashes=trusted_review_hashes,
    )
    if canonical(assessment) != canonical(expected):
        raise ValueError("assessment does not match its verified inputs and admission policy")
    return expected


def require_admitted_assessment(assessment, request, *, source_root, registry, trusted_review_hashes=()):
    """Return the verified assessment only when it is eligible for consumption."""
    result = validate_assessment(
        assessment, request, source_root=source_root, registry=registry, trusted_review_hashes=trusted_review_hashes,
    )
    if result["admission_status"] != "admitted":
        raise ValueError("R1 v3 assessment is not admitted")
    return result
