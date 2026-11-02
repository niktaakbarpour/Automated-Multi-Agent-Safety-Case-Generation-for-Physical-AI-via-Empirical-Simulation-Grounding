"""Applicability and object outcomes from admitted declarations, never raw poses."""
from .configuration import unsupported_for_object
from .contracts import Applicability as A, Outcome as O, Truth, Validity as V, ObjectAssessment
from .temporal import coverage_for


def assess_object(config, object_id, records, admissions, cells, model, runtime_errors=()):
    own = [r for r in records if r.object_id == object_id]
    admitted = [r for r in own if admissions[r.id].status == V.VERIFIED]
    coverage = coverage_for(object_id, records, admissions, cells)
    uncertainty = sorted({reason for r in own for reason in admissions[r.id].reasons})
    dependency_ids = {d for r in own for d in admissions[r.id].dependencies}
    uncertainty += [r.id + ':' + description for r in records if r.id in dependency_ids
                    for description in r.uncertainty.description]
    reasons = list(runtime_errors)
    def truths(claim):
        return {r.truth for r in admitted if r.claim == claim}
    def invalid(claims):
        return any(r.claim in claims and admissions[r.id].status == V.INVALID_CONTRACT for r in own)
    absent = Truth.FALSE in truths('presence')
    if runtime_errors:
        applicability = A.IC
    elif absent:
        if invalid({'presence','identity'}):
            applicability = A.IC
            reasons.append('invalid_absence_identity_foundation')
        else:
            applicability = A.NA
            reasons.append('verified_absent')
    else:
        reasons.extend(unsupported_for_object(config, object_id))
        # Verify the declared model support scope per object, not globally across rows.
        for root in config['object_surface_mapping'][object_id]:
            root_geometry = model['surfaces'].get(root, {})
            if root_geometry != {'shape': 'box', 'static': True, 'horizontal': True, 'complete': True}:
                reasons.append('unsupported_or_unresolved_root:' + root)
        if reasons or invalid({'identity', 'presence', 'geometry', 'initial_support'}):
            applicability = A.IC
            reasons.append('invalid_essential_applicability_contract')
        elif Truth.TRUE not in truths('presence') or Truth.TRUE not in truths('identity'):
            applicability = A.UNKNOWN
            reasons.append('presence_or_identity_unresolved')
        elif Truth.TRUE in truths('initial_support'):
            applicability = A.APPLICABLE
            reasons.append('initial_support_established')
        elif Truth.FALSE in truths('initial_support'):
            applicability = A.NA
            reasons.append('initial_support_excluded')
        else:
            applicability = A.UNKNOWN
            reasons.append('initial_support_unresolved')
    if applicability == A.IC:
        outcome = O.IC
    elif applicability == A.NA:
        outcome = O.NA
    elif applicability == A.UNKNOWN:
        outcome = O.U
    elif any(r.claim == 'violation' and r.truth == Truth.TRUE for r in admitted):
        outcome = O.V
    elif invalid({'violation', 'static_negative'}):
        outcome = O.IC
        reasons.append('invalid_remaining_assessment_contract')
    elif not coverage.missing:
        outcome = O.N
    else:
        outcome = O.U
        reasons.append('negative_coverage_incomplete')
    scope_unresolved = any(r.claim == 'scope_boundary' for r in own)
    if scope_unresolved:
        uncertainty.append('unresolved_scope_suffix_no_rearm')
    complete = (applicability == A.NA or outcome == O.N or
                outcome == O.V and not coverage.missing and not uncertainty)
    if outcome in (O.U, O.IC) or scope_unresolved or uncertainty:
        complete = False
    return ObjectAssessment(object_id, tuple(sorted(config['object_surface_mapping'][object_id])),
                            applicability, outcome, tuple(sorted(set(reasons))),
                            tuple(r.id for r in admitted), coverage, tuple(sorted(set(uncertainty))),
                            complete, absent, 'pending_protocol_decision' if absent else 'not_decided_by_checker',
                            execution_id=config['execution_id'], adapter_version=config['assessment_manifest']['adapter']['version'],
                            profile_version=config['assessment_manifest']['inference_profile']['version'])
