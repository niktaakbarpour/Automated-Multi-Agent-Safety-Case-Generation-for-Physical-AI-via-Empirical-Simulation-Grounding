"""Lossless, validated Drafter -> Critic envelope projection. No inference or checking of physics."""
from copy import deepcopy
from critic import checks, contract as K
from drafter.validation import ContractError, schema_issues, validate_argument, validate_request

ORIGINAL_CONTEXT_PREFIX = 'Original Drafter retrieval_context (lossless JSON): '


def build_critic_request(draft_request, generation_report):
    """Return (critic_request, provenance_sidecar); never change a graph or manufacture a field observation.

    The Critic has no field for the full Drafter retrieval/review envelopes. Keep
    the original retrieval context as JSON in limitations, visible to its model,
    and both original envelopes in the sidecar. Gaps lacking measurement_type
    cannot become typed Critic gaps: retain them verbatim instead of guessing.
    Only accepted fully validated generation reports may enter this handoff.
    """
    validate_request(draft_request)
    problems = schema_issues(generation_report, 'generation_run.schema.json')
    if problems:
        raise ContractError(['handoff_generation_report:' + x for x in problems])
    if generation_report['status'] != 'accepted':
        raise ContractError(['handoff_requires_accepted_draft'])
    if generation_report['request_sha256'] != K.digest(draft_request):
        raise ContractError(['handoff_original_request_hash_mismatch'])
    argument = generation_report['argument']
    validate_argument(argument, draft_request)
    cfg = draft_request['requirement_configuration']
    target = draft_request['target_execution']
    scope = draft_request['monitoring_scope']
    retrieval = draft_request['retrieval_context']
    structured = draft_request.get('structured_evidence', [])
    requested = retrieval.get('requested_measurement_types')
    if requested is None:
        requested = list(dict.fromkeys(o['family'] for entry in structured
                                      for o in entry['request'].get('obligations', [])))
    # Unknown registry completeness must not inherit Phase5's narrower mandatory-
    # obligation completeness. A genuine explicit flag may be copied; otherwise
    # this conservative false is explained with the exact original context.
    complete = retrieval.get('complete_within_requested_scope') is True
    limitations = (deepcopy(retrieval.get('limitations', []))
                   + deepcopy(draft_request['limitations'])
                   + deepcopy(argument['limitations'])
                   + [argument['reasoning_review']['warning'],
                      ORIGINAL_CONTEXT_PREFIX + K.canonical(retrieval).decode('utf-8')])
    req = {
        'schema_version': K.REQUEST_SCHEMA_VERSION,
        'request_id': generation_report['run_id'] + ':critic',
        'test_fixture': draft_request['test_fixture'],
        'evaluation_context': {
            'requirement_id': cfg['requirement_id'], 'requirement_version': cfg['requirement_version'],
            **{k: deepcopy(target[k]) for k in ('execution_id', 'benchmark', 'task_id', 'model_checkpoint')},
            'variant_id': target.get('variant_id'),
            'r1_configuration': deepcopy(cfg), 'r1_configuration_sha256': K.digest(cfg),
            'protected_objects': deepcopy(cfg['protected_objects']),
            'support_surfaces': [s['id'] for s in cfg['support_surfaces']],
            'monitored_interval': {k: deepcopy(scope[k]) for k in ('domain', 'clock', 'interval')},
            'contract_versions': {'gsn': K.GSN_SCHEMA_VERSION, 'registry_record': K.RECORD_SCHEMA_VERSION},
        },
        'argument_bundle': deepcopy(argument['argument_bundle']),
        'evidence_package': {'records': deepcopy(draft_request['evidence_package']['records'])},
        'checker_assessments': deepcopy(draft_request['checker_context']['assessments']),
        'structured_evidence': deepcopy(structured),
        'retrieval_context': {
            'requested_measurement_types': deepcopy(requested),
            'complete_within_requested_scope': complete,
            'gaps': [deepcopy(g) for g in retrieval.get('gaps', []) if 'measurement_type' in g],
            'related_case_evidence_ids': deepcopy(retrieval.get('related_case_evidence_ids', [])),
            'limitations': limitations,
        },
    }
    # Non-explicit boundary provenance formats are not interchangeable. Do not
    # synthesize a checker-compatible certificate from free-form Drafter prose.
    for edge in ('start', 'end'):
        if cfg['monitoring_interval'][edge]['kind'] != 'explicit_index':
            raise ContractError(['handoff_requires_explicit_boundaries_or_validated_boundary_adapter'])
    findings, info = checks.run_all(req)
    if not info['input_valid']:
        raise ContractError(['handoff_critic_input:' + f['check_id'] + ':' + f['explanation']
                             for f in findings if f['phase'] == 'validation'])
    sidecar = {
        'schema_version': 'one-pass-handoff/0.1.0', 'automatic_revision': False,
        'drafter_request': deepcopy(draft_request),
        'drafter_argument': deepcopy(argument),
        'generation_run_id': generation_report['run_id'],
        'generation_report_sha256': K.digest(generation_report),
        'original_argument_bundle_sha256': K.digest(argument['argument_bundle']),
        'critic_argument_bundle_sha256': K.digest(req['argument_bundle']),
        'critic_request_sha256': K.digest(req),
        'projection_notes': [
            'Only explicit-index boundaries supported; no boundary source is inferred.',
            'Untyped original gaps remain verbatim in original context JSON and the sidecar; no measurement_type invented.',
            'test_fixture classifies analytical configuration authority; source measurements remain genuine when retrieved genuinely.',
            'Model prose/review envelope remains unchanged in the sidecar; its review warning is passed in limitations.',
            'No checker result, evidence record, graph, outcome or citation is created by this adapter.',
        ],
    }
    return req, sidecar
