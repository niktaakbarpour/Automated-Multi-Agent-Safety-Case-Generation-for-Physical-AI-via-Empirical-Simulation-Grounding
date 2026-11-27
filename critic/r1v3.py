"""Deterministic Critic route for a lossless R1 v3 Drafter handoff."""

from collections import Counter, defaultdict
from copy import deepcopy

from drafter import r1v3_profile as P
from drafter.r1v3_generation import validate_accepted_run
from drafter.validation import ContractError, json_value_issues

from . import contract as K, llm as L, schema
from .checks import finding
from .claims import absolute_safety_phrase
from .r1v3_assessments import validate_checker_inputs

VERSION = 'r1v3-cpu/0.1.0'
REQUIREMENT_REF = 'requirements/r1_initial_table_support_v3/'


def validate_draft_input(request):
    """Validate the handoff and its Drafter artifacts before interpreting evidence."""
    issues = json_value_issues(request) or schema.errors(request, schema.load('request_r1v3'))
    if not issues:
        issues = P.reference_label_issues({'checker_assessments': request['checker_assessments']})
    if issues:
        raise ContractError(issues)
    report = request['generation_report']
    try:
        argument = validate_accepted_run(request['drafter_request'], report)
    except (KeyError, TypeError, IndexError, OverflowError, RecursionError) as error:
        raise ContractError(['invalid_drafter_source_package_or_run_structure']) from error
    if request['request_id'] != report['run_id'] + ':critic':
        raise ContractError(['critic_run_id_mismatch'])
    return argument


def provenance_for(request):
    draft = request['drafter_request']
    report = request['generation_report']
    bundle = report['argument']['argument_bundle']
    bundle_sha = K.digest(bundle)
    return {
        'generation_run_id': report['run_id'],
        'generation_report_sha256': K.digest(report),
        'drafter_request_sha256': report['request_sha256'],
        'requirement_configuration_sha256': draft['requirement_configuration_sha256'],
        'source_package_sha256': draft['source_package_sha256'],
        'original_argument_bundle_sha256': bundle_sha,
        'critic_argument_bundle_sha256': bundle_sha,
        'critic_request_sha256': K.digest(request),
    }


def _review_objects(bundle, assessments):
    by_object = defaultdict(list)
    for assessment in assessments:
        if assessment['admission_status'] == 'admitted':
            by_object[assessment['scope']['object_id']].append(assessment)

    objects, findings, concerns = [], [], []
    for object_id in bundle['protected_objects']:
        claimed = bundle['execution_conclusion']['object_outcomes'][object_id]
        evidence = by_object[object_id]
        outcomes = {assessment['conclusion']['outcome'] for assessment in evidence}
        hashes = sorted({assessment['assessment_hash'] for assessment in evidence})
        outcome = next(iter(outcomes)) if len(outcomes) == 1 else None
        conflict = len(outcomes) > 1
        objects.append({
            'object_id': object_id,
            'draft_outcome': claimed,
            'verified_checker_outcome': outcome,
            'admitted_assessment_hashes': hashes,
            'assessment_conflict': conflict,
        })
        if conflict:
            findings.append(finding(
                'R1V3-CHECKER-CONFLICT', 'C09',
                'Admitted Checker assessments disagree for this object and saved-frame window.',
                'Resolve the conflict using the cited source and gate ledgers.',
                object_id=object_id, evidence_ids=hashes, requirement_refs=[REQUIREMENT_REF],
                human_review_required=True,
            ))
        elif outcome == 'violation' and claimed != outcome:
            explanation = (
                'The draft leaves the outcome unresolved. An independently admitted Checker assessment '
                'records a fall witness for this object and saved-frame window.'
                if claimed == P.INSUFFICIENT else
                'An independently admitted fall witness contradicts the object outcome in the draft.'
            )
            findings.append(finding(
                'R1V3-ADMITTED-WITNESS', 'C07', explanation,
                'Reconcile the graph with the admitted assessment and its saved-frame witness.',
                object_id=object_id, evidence_ids=hashes, requirement_refs=[REQUIREMENT_REF],
                human_review_required=True,
            ))
        elif claimed != P.INSUFFICIENT and claimed != outcome:
            category = 'C08' if 'not_applicable' in (claimed, outcome) else 'C06'
            findings.append(finding(
                'R1V3-OUTCOME-BACKING', category,
                'The draft outcome lacks matching independently admitted Checker evidence.',
                'Resolve the evidence gap or record the outcome as unresolved.',
                object_id=object_id, evidence_ids=hashes, requirement_refs=[REQUIREMENT_REF],
                additional_evidence_needed=True, human_review_required=True,
            ))
        if not evidence:
            concerns.append(f'{object_id} has no independently admitted Checker assessment.')
    return objects, findings, concerns


def _absolute_safety_findings(bundle):
    for item in bundle['graphs']:
        for node in item['graph']['nodes']:
            if absolute_safety_phrase(node['statement']):
                yield finding(
                    'CLAIM-ABSOLUTE-SAFETY', 'C12',
                    'This graph statement makes an unconditional safety claim.',
                    'Limit the statement to the reviewed evidence and saved-frame coverage.',
                    object_id=item['object_id'], node_id=node['id'],
                    requirement_refs=[REQUIREMENT_REF], human_review_required=True,
                )


def review(request, llm, *, source_root=None, registry=None, trusted_review_hashes=(), task_id=None):
    """Review validated artifacts and independently reproduced assessments on CPU."""
    has_backend = not isinstance(llm, L.NullLLM)
    model = L.empty_status(llm, 'R1 v3 currently supports deterministic review only.' if has_backend else None)
    model['prompt_version'] = None
    request_id = request.get('request_id')
    request_id = request_id if isinstance(request_id, str) else ''
    try:
        request_id.encode('utf-8')
    except UnicodeEncodeError:
        request_id = ''
    report = {
        'schema_version': K.R1V3_REPORT_SCHEMA_VERSION, 'critic_version': VERSION,
        'request_id': request_id,
        'execution_id': '', 'test_fixture': False, 'input_valid': False,
        'review_status': 'rejected_invalid_input', 'status_detail': None, 'llm': model,
        'provenance': None, 'criticisms': [], 'checker_admission': [], 'object_reviews': [],
        'drafter_evidence_gaps': [], 'unresolved_concerns': [],
        'safety_claim_verified': False, 'reasoning_review': {'status': 'required'},
        'summary': {'blocking_defects': True, 'claimed_execution_outcome': None,
                    'recomputed_execution_outcome': None, 'accepted_execution_outcome': None},
    }
    try:
        argument = validate_draft_input(request)
        draft = request['drafter_request']
        assessments = validate_checker_inputs(
            draft, request['checker_assessments'], source_root=source_root, registry=registry,
            trusted_review_hashes=trusted_review_hashes, task_id=task_id,
        )
    except (ValueError, OSError) as error:
        diagnostics = error.issues if isinstance(error, ContractError) else [str(error)]
        report['status_detail'] = 'R1 v3 input validation failed.'
        report['unresolved_concerns'] = diagnostics
        return report

    bundle = argument['argument_bundle']
    objects, findings, concerns = _review_objects(bundle, assessments)
    findings += _absolute_safety_findings(bundle)
    criticisms = [{'criticism_id': f'CRIT-{index:03d}', 'critic_version': VERSION, **row}
                  for index, row in enumerate(findings, 1)]
    blocked = {row['object_id'] for row in criticisms if row['blocking']}
    verified = {row['object_id']: row['verified_checker_outcome'] or P.INSUFFICIENT for row in objects}
    accepted = {
        row['object_id']: row['draft_outcome'] if row['object_id'] not in blocked
        and row['draft_outcome'] == row['verified_checker_outcome'] else P.INSUFFICIENT
        for row in objects
    }
    model['ok'] = not has_backend
    report.update(
        input_valid=True, review_status='completed_llm_failed' if has_backend else 'completed',
        status_detail=model['error'], execution_id=bundle['execution_id'], test_fixture=draft['test_fixture'],
        provenance=provenance_for(request), criticisms=criticisms, checker_admission=assessments,
        object_reviews=objects, drafter_evidence_gaps=deepcopy(draft['evidence_gaps']),
        unresolved_concerns=concerns + ['The GSN reasoning still requires review.'],
        reasoning_review=deepcopy(argument['reasoning_review']),
        summary={
            'blocking_defects': bool(blocked),
            'claimed_execution_outcome': bundle['execution_conclusion']['claimed_outcome'],
            'recomputed_execution_outcome': P.aggregate(verified),
            'accepted_execution_outcome': P.aggregate(accepted),
            'counts_by_category': dict(Counter(row['category'] for row in criticisms)),
        },
    )
    return report
