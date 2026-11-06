"""Configurable, source-bound inputs for unresolved drafting.

The original pinned archive profile is deliberately separate. These profiles
accept caller-supplied snapshots without claiming that their source bytes were
opened, authenticated, or sufficient to establish an R1 physical outcome.
"""
from copy import deepcopy

from evaluation.r1_v4.configuration import validate_configuration
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.evidence_registry_gsn.registry import dependency_issues
from evaluation.r1_v4.provenance import digest

SUPPLIED_PROFILES = ('supplied_registry', 'phase5_structured')
SOURCE_LIMITATION = ('Supplied metadata and structured bundles are checked for internal consistency; '
                     'the Drafter has not authenticated source bytes or established physical sufficiency.')


def _contract_error(issues):
    from .validation import ContractError
    return ContractError(sorted(set(issues)))


def _input_parts(request):
    """Use authoritative schemas before indexing caller-controlled structures."""
    from .validation import schema_issues
    issues = schema_issues(request, 'draft_request.schema.json')
    if issues:
        raise _contract_error(issues)
    if request.get('input_profile') not in SUPPLIED_PROFILES:
        raise _contract_error(['unsupported_supplied_input_profile'])
    config = request['requirement_configuration']
    issues = validate_configuration(config)
    checkpoint = config['benchmark'].get('policy_checkpoint')
    if not isinstance(checkpoint, str) or not checkpoint.strip():
        issues.append('configuration_checkpoint_required')
    if issues:
        raise _contract_error(issues)
    return config, request['target_execution'], request['monitoring_scope']


def eligible_registry_ids(request, *, linked_ids=None):
    """Original scoped observation IDs only; raw Phase 5 items are not Records."""
    from .validation import graph_eligible_ids
    ids = graph_eligible_ids(request)
    return ids if linked_ids is None else [key for key in ids if key in linked_ids]


def validate_supplied_request(request):
    """Validate a complete configurable request, returning no physical verdict."""
    from .validation import known_saved_frame_gaps
    config, target, scope = _input_parts(request)
    issues = []
    export, provenance = request['evidence_package'], request['input_provenance']
    for field, value in (('requirement_configuration_sha256', config), ('evidence_package_sha256', export)):
        if request[field] != digest(value):
            issues.append(field + '_mismatch')
    if provenance['configuration_sha256'] != request['requirement_configuration_sha256']:
        issues.append('configuration_provenance_mismatch')
    if provenance['evidence_package_sha256'] != request['evidence_package_sha256']:
        issues.append('evidence_provenance_mismatch')
    if config['assessment_manifest']['purpose'] == 'analytical_fixture' and not request['test_fixture']:
        issues.append('analytical_fixture_requires_test_fixture_label')
    if (config['execution_id'], config['task_id'], config['benchmark']['id'],
            config['benchmark']['policy_checkpoint']) != (target['execution_id'], target['task_id'],
                                                         target['benchmark'], target['model_checkpoint']):
        issues.append('configuration_target_scope_mismatch')
    bounds = config['monitoring_interval']
    if (bounds['axis'], scope['domain'], scope['clock']) != ('saved_frame', 'frame', 'saved_frame_index'):
        issues.append('unsupported_drafter_clock_or_axis')
    start, end = scope['interval']
    if any(type(x) is not int or x < 0 for x in (start, end)) or start > end:
        issues.append('invalid_monitoring_interval')
    if (bounds['start']['kind'], bounds['end']['kind']) != ('explicit_index', 'explicit_index'):
        issues.append('explicit_monitoring_boundaries_required')
    elif [bounds['start']['value'], bounds['end']['value']] != scope['interval']:
        issues.append('configuration_boundary_mismatch')
    if issues:
        raise _contract_error(issues)

    records = {}
    for index, value in enumerate(export['records']):
        try:
            record = Record.parse(value)
            if record.id in records:
                issues.append('duplicate_record:' + record.id)
            records[record.id] = record
            if (record.requirement_id, record.requirement_version, record.execution_id,
                    record.benchmark, record.task_id, record.model_checkpoint) != (
                    config['requirement_id'], config['requirement_version'], target['execution_id'],
                    target['benchmark'], target['task_id'], target['model_checkpoint']):
                issues.append('record_target_scope:' + record.id)
            if record.object_id not in config['protected_objects']:
                issues.append('record_object_scope:' + record.id)
        except (ValueError, TypeError, KeyError) as error:
            issues.append('record:' + str(index) + ':' + str(error))
    if records:
        for key, errors in dependency_issues(records).items():
            issues.extend('record_dependency:' + key + ':' + error for error in errors)

    linked = None
    if request['input_profile'] == 'phase5_structured':
        from .phase5_adapter import evidence_context
        if request['structured_evidence_sha256'] != digest(request['structured_evidence']):
            issues.append('structured_evidence_digest_mismatch')
        if provenance['structured_evidence_sha256'] != request['structured_evidence_sha256']:
            issues.append('structured_evidence_provenance_mismatch')
        # Recomputes consumer checks rather than trusting cached status fields.
        context = evidence_context(request)
        linked = {key for row in context['citations'] for key in row['original_evidence_ids']}
    eligible = eligible_registry_ids(request, linked_ids=linked)
    handling = request['evidence_handling']
    if (sorted(handling['graph_eligible_evidence_ids']) != eligible
            or set(handling['context_only_evidence_ids']) != set(records) - set(eligible)):
        issues.append('evidence_partition_mismatch')
    retrieval = request['retrieval_context']
    if retrieval['requested_objects'] != config['protected_objects'] or retrieval['requested_interval'] != scope['interval']:
        issues.append('retrieval_scope_mismatch')
    observed = {r.object_id for key, r in records.items() if key in eligible}
    if set(retrieval['missing_objects']) != set(config['protected_objects']) - observed:
        issues.append('missing_object_inventory_mismatch')
    supplied_gaps = [(g['object_id'], *g['interval']) for g in retrieval['gaps']]
    expected = known_saved_frame_gaps(config['protected_objects'], records, set(eligible), scope['interval'])
    if sorted(supplied_gaps) != expected:
        issues.append('known_gap_inventory_mismatch')
    if any(any(type(v) is not int for v in gap['interval']) for gap in retrieval['gaps']):
        issues.append('saved_frame_gap_requires_integer_endpoints')
    if SOURCE_LIMITATION not in request['limitations']:
        issues.append('supplied_source_limitations_required')
    if issues:
        raise _contract_error(issues)
    return {'contract_status': 'valid_supplied_input', 'input_profile': request['input_profile'],
            'configuration_schema': 'valid', 'registry_metadata_contract': 'valid',
            'records': len(records), 'graph_eligible_records': len(eligible),
            'source_replay': 'not_performed', 'source_authentication': 'not_performed',
            'physical_sufficiency': 'not_evaluated', 'empirical_admission_enabled': False,
            'safety_claim_verified': False, 'model_called': False}


def build_supplied_request(*, request_id, requirement_configuration, target_execution,
                           monitoring_scope, registry_records=(), test_fixture=False,
                           limitations=(), structured_evidence=None):
    """Build and validate a configurable input without changing supplied evidence.

    Raw-channel Phase 5 observations remain context. Existing registry records
    linked by original_evidence_ids may be cited as observations, not outcomes.
    """
    from .validation import known_saved_frame_gaps
    if any(not isinstance(value, dict) for value in
           (requirement_configuration, target_execution, monitoring_scope)):
        raise _contract_error(['supplied_builder_requires_configuration_target_and_scope_objects'])
    if not isinstance(registry_records, (list, tuple)):
        raise _contract_error(['supplied_builder_registry_records_must_be_array'])
    if not isinstance(limitations, (list, tuple)) or any(not isinstance(value, str) for value in limitations):
        raise _contract_error(['supplied_builder_limitations_must_be_text_array'])
    config, target, scope = map(deepcopy, (requirement_configuration, target_execution, monitoring_scope))
    export = {'schema_version': '1.0.0', 'records': deepcopy(list(registry_records))}
    request = {'schema_version': 'drafter-request/0.1.0', 'input_profile': 'supplied_registry',
               'request_id': request_id, 'test_fixture': test_fixture, 'usage': 'proposed_argument',
               'requirement_configuration': config, 'requirement_configuration_sha256': digest(config),
               'target_execution': target, 'monitoring_scope': scope, 'evidence_package': export,
               'evidence_package_sha256': digest(export),
               'evidence_handling': {'data_origin': 'supplied_registry_export', 'source_replay': 'not_performed',
                                     'empirical_admission_enabled': False,
                                     'graph_eligible_evidence_ids': [], 'context_only_evidence_ids': []},
               'checker_context': {'status': 'not_available', 'assessments': []},
               'safety_knowledge': [], 'related_cases': [],
               'retrieval_context': {'format': 'registry_export', 'completeness_status': 'not_evaluated',
                                     'requested_objects': config.get('protected_objects', []),
                                     'requested_interval': scope.get('interval', []), 'missing_objects': [],
                                     'gaps': [], 'limitations': [SOURCE_LIMITATION]},
               'input_provenance': {'mode': 'supplied_snapshot', 'configuration_sha256': digest(config),
                                    'evidence_package_sha256': digest(export),
                                    'source_authentication': 'not_performed'},
               'limitations': list(dict.fromkeys([SOURCE_LIMITATION, *limitations])),
               'empirical_admission_enabled': False, 'safety_claim_verified': False}
    linked = None
    if structured_evidence is not None:
        from .phase5_adapter import evidence_context
        request['input_profile'] = 'phase5_structured'
        request['structured_evidence'] = deepcopy(structured_evidence)
        request['structured_evidence_sha256'] = digest(request['structured_evidence'])
        request['input_provenance']['structured_evidence_sha256'] = request['structured_evidence_sha256']
        request['evidence_handling']['data_origin'] = 'phase5_structured'
        # Validate the configuration and envelope before reading scope-dependent data.
        _input_parts(request)
        context = evidence_context(request)
        linked = {key for row in context['citations'] for key in row['original_evidence_ids']}
        request['limitations'] = list(dict.fromkeys([
            *request['limitations'], *[limit for row in context['retrieval'] for limit in row['limitations']]]))
    _input_parts(request)
    records = {}
    for value in export['records']:
        try:
            record = Record.parse(value)
            records[record.id] = record
        except (ValueError, TypeError, KeyError) as error:
            raise _contract_error(['record:' + str(error)]) from error
    eligible = eligible_registry_ids(request, linked_ids=linked)
    request['evidence_handling']['graph_eligible_evidence_ids'] = eligible
    request['evidence_handling']['context_only_evidence_ids'] = sorted(set(records) - set(eligible))
    observed = {r.object_id for key, r in records.items() if key in eligible}
    request['retrieval_context']['missing_objects'] = [obj for obj in config['protected_objects'] if obj not in observed]
    request['retrieval_context']['gaps'] = [
        {'object_id': obj, 'interval': [left, right],
         'reason': 'No eligible registry observation covers this saved-frame interval; Phase 5 context is retained separately.'}
        for obj, left, right in known_saved_frame_gaps(config['protected_objects'], records, set(eligible), scope['interval'])]
    validate_supplied_request(request)
    return request
