"""Independently verify Checker R1 v3 assessments at the Critic boundary."""

from evaluation.r1_v4.checker_v3_admission.admission import (
    require_admitted_assessment,
    validate_assessment,
)


def validate_checker_inputs(
    drafter_request, checker_assessments, *, source_root=None, registry=None,
    trusted_review_hashes=(), task_id=None,
):
    """Reproduce each assessment under host-supplied trust settings.

    The Drafter request has already passed its own contract validation. A
    reproduced blocked assessment describes a gap and carries no conclusion.
    Invalid inputs raise before the Critic uses any of the assessments.
    """
    if not isinstance(checker_assessments, list):
        raise ValueError("Checker assessments must be an array.")
    if not checker_assessments:
        return []
    if (
        source_root is None or (isinstance(source_root, str) and not source_root.strip())
        or registry is None or not isinstance(task_id, str) or not task_id.strip()
    ):
        raise ValueError("Checker verification requires an approved source root, registry and task.")
    if isinstance(trusted_review_hashes, (str, bytes)):
        raise ValueError("Checker verification requires a collection of trusted review hashes.")
    try:
        trusted_review_hashes = frozenset(trusted_review_hashes)
    except TypeError:
        raise ValueError("Checker verification requires a collection of trusted review hashes.") from None

    configuration = drafter_request["requirement_configuration"]
    target = drafter_request["target_execution"]
    window = drafter_request["monitoring_scope"]
    scope = {
        "execution_id": target["execution_id"],
        "trajectory_sha256": target["trajectory_sha256"],
        "task_id": task_id,
        "clock": window["clock"],
        "frame_interval": window["interval"],
    }
    requirement = (configuration["requirement_id"], configuration["requirement_version"])
    roster = configuration["protected_objects"]
    verified = []
    for index, pair in enumerate(checker_assessments):
        if not isinstance(pair, dict) or set(pair) != {"request", "assessment"}:
            raise ValueError(f"Checker assessment pair {index} must contain a request and assessment.")
        request, assessment = pair["request"], pair["assessment"]
        if not isinstance(request, dict) or not isinstance(assessment, dict):
            raise ValueError(f"Checker assessment pair {index} must contain JSON objects.")
        object_id = _check_scope(request, scope, roster, requirement, index)
        _check_scope(assessment, scope, (object_id,), requirement, index)

        # The consumer check also reproduces the assessment. Do it once.
        validate = (
            require_admitted_assessment if assessment.get("admission_status") == "admitted"
            else validate_assessment
        )
        try:
            result = validate(
                assessment, request, source_root=source_root, registry=registry,
                trusted_review_hashes=trusted_review_hashes,
            )
        except (ValueError, OSError, TypeError, KeyError, IndexError, OverflowError, RecursionError):
            raise ValueError(f"Checker assessment pair {index} failed independent verification.") from None
        verified.append(result)
    return verified


def _check_scope(value, expected_scope, roster, requirement, index):
    scope = value.get("scope")
    if (
        (value.get("requirement_id"), value.get("requirement_version")) != requirement
        or not isinstance(scope, dict)
        or scope.get("object_id") not in roster
        or scope != {**expected_scope, "object_id": scope.get("object_id")}
    ):
        raise ValueError(f"Checker assessment pair {index} is outside the declared review scope.")
    return scope["object_id"]
