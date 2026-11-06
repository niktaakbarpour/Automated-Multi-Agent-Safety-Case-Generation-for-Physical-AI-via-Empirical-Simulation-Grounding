"""Consume Phase 5 structured snapshots without promoting measurements to safety.

The shared consumer implementation is the current Critic's retrieval boundary.
This composition deliberately avoids maintaining a second copy of its integrity,
obligation, citation and status rules. No database or source path is opened here.
"""
from copy import deepcopy

from critic import retrieval as consumer
from evaluation.r1_v4.provenance import canonical, digest


def _fail(issues):
    from .validation import ContractError
    raise ContractError(sorted(set(issues)))


def evidence_context(request):
    """Validate and expose an exact, attributed Phase 5 context for generation.

    Returned citations are context references, not permitted graph node IDs or
    fabricated ev: records. Original request/bundle pairs are retained unchanged.
    Consumer success means internal consistency, not independent authentication.
    """
    if request.get('input_profile') != 'phase5_structured':
        return None
    entries = request.get('structured_evidence')
    target, scope, config = (request.get('target_execution'), request.get('monitoring_scope'),
                              request.get('requirement_configuration'))
    if (not isinstance(entries, list) or not 1 <= len(entries) <= 16
            or not isinstance(target, dict) or not isinstance(scope, dict)
            or not isinstance(config, dict)):
        _fail(['phase5_adapter_input_shape'])
    try:
        canonical(entries)
    except (ValueError, TypeError, RecursionError) as error:
        _fail(['phase5_invalid_json:' + str(error)])
    if not isinstance(config.get('protected_objects'), list) or not isinstance(scope.get('interval'), list) \
            or len(scope['interval']) != 2:
        _fail(['phase5_adapter_scope_shape'])
    if (scope.get('domain'), scope.get('clock')) != ('frame', 'saved_frame_index'):
        _fail(['phase5_unsupported_monitoring_clock'])
    start, end = scope['interval']
    if any(type(x) is not int for x in (start, end)) or start < 0 or start > end:
        _fail(['phase5_invalid_monitoring_interval'])
    # The Critic consumer enforces the pinned production release, exact scope,
    # query/obligation digests, original source/citation basis, assurance and all
    # missing/conditional/status relationships. It never verifies physical truth.
    registry_records = {value['id']: value for value in request.get('evidence_package', {}).get('records', [])
                        if isinstance(value, dict) and isinstance(value.get('id'), str)}
    # Fail closed on the pre-repair consumer shipped at the PR's original base.
    # Its copied request rules accepted unsupported requests as complete bundles.
    # Reuse the frozen public predicates; do not copy them into the Drafter.
    try:
        from critic.phase5_request import refusal
    except ImportError:
        _fail(['phase5_current_consumer_required: update to the merged Critic public-request validator'])
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get('request'), dict) \
                and isinstance(entry.get('bundle'), dict):
            bundle = entry['bundle']
            validation = bundle.get('independent_validation')
            if isinstance(validation, dict) and validation.get('passed') is True:
                problem = refusal(entry['request'])
                if problem:
                    _fail(['phase5_public_request_refused:' + problem[0] + ':' + problem[1]])
                # Shape-dependent window validation remains inside consumer.admit.
    try:
        problems, admitted, rows = consumer.admit({
            'structured_evidence': entries, 'evaluation_context': {
                key: target.get(key) for key in ('execution_id', 'task_id', 'variant_id')}},
                records=registry_records)
    except (KeyError, TypeError, ValueError, RecursionError) as error:
        _fail(['phase5_malformed_snapshot:' + str(error)])
    if problems:
        _fail(['phase5:' + check + ':' + text for check, category, text, query in problems])
    issues = []
    seen_queries = set()
    citations = []
    for index, entry in enumerate(entries):
        q, b = entry['request'], entry['bundle']
        if b['query_id'] in seen_queries:
            issues.append('phase5_duplicate_query:' + b['query_id'])
        seen_queries.add(b['query_id'])
        # A rejected query can legitimately be echoed by Phase 5 even when its
        # schema was invalid. Consumer acceptance of a rejection is not license
        # to interpret arbitrary query shapes as a verified selector or scope.
        obligations = q.get('obligations')
        if not isinstance(obligations, list) or any(not isinstance(o, dict) for o in obligations):
            issues.append('phase5_malformed_obligation_list')
            continue
        if not isinstance(q.get('provenance'), dict):
            issues.append('phase5_malformed_query_provenance')
        if any(not isinstance(o.get('id'), str) for o in obligations):
            issues.append('phase5_malformed_obligation_identity')
            continue
        by_obligation = {o['id']: o for o in obligations}
        for obligation in by_obligation.values():
            obj = obligation.get('object_id')
            family = obligation.get('family')
            if family == 'main_table_identity':
                if obj not in (None, 'main_table'):
                    issues.append('phase5_unsupported_table_alias:' + obligation['id'])
            elif family not in consumer.K.PHASE5_CHANNELS and obj is not None and obj not in config['protected_objects']:
                issues.append('phase5_obligation_object_scope:' + obligation['id'])
            selector = obligation.get('selector')
            if 'selector' in obligation:
                if not isinstance(selector, dict):
                    issues.append('phase5_malformed_selector:' + obligation['id'])
                elif selector.get('kind') != 'frames':
                    issues.append('phase5_selector_clock_not_mapped:' + obligation['id'])
                elif any(type(selector.get(key)) is not int for key in ('start', 'end')):
                    issues.append('phase5_malformed_selector:' + obligation['id'])
                elif not start <= selector['start'] <= selector['end'] <= end:
                    issues.append('phase5_obligation_outside_monitoring_window:' + obligation['id'])
        for group in b['groups']:
            seen_items = set()
            obligation = by_obligation.get(group['obligation_id'], {})
            for item in group['items']:
                if item['id'] in seen_items:
                    issues.append('phase5_duplicate_group_item:' + item['id'])
                seen_items.add(item['id'])
                value = item.get('value')
                if group['family'] == 'geometry_identity' and isinstance(value, dict) and value.get('object_id') is not None \
                        and (value['object_id'] not in config['protected_objects']
                             or obligation.get('object_id') is not None and value['object_id'] != obligation['object_id']):
                    issues.append('phase5_item_object_scope:' + item['id'])
                # Existing registry records can be linked only when this is a
                # direct, identical source reference. Aggregate/indirect lineage
                # needs a separate typed contract; matching IDs alone is not it.
                for original_id in item['original_evidence_ids']:
                    record = registry_records.get(original_id)
                    if record is None:
                        continue  # The original ID remains context, not a fabricated Record.
                    artifact = item['source_artifact']
                    if tuple(record.get(key) for key in ('source_path', 'source_sha256', 'selector')) != \
                            tuple(artifact[key] for key in ('path', 'sha256', 'selector')):
                        issues.append('phase5_registry_link_source_mismatch:' + original_id)
                    if (record.get('execution_id'), record.get('task_id')) != \
                            (item['execution_id'], item['task_id']) or \
                            obligation.get('object_id') is not None and record.get('object_id') != obligation['object_id']:
                        issues.append('phase5_registry_link_scope_mismatch:' + original_id)
                citations.append({'query_id': b['query_id'], 'obligation_id': group['obligation_id'],
                                  'mandatory': group['mandatory'], 'group_status': group['status'],
                                  'citation_id': item['citation_id'], 'item_id': item['id'],
                                  'original_evidence_ids': deepcopy(item['original_evidence_ids']),
                                  'source_artifact': deepcopy(item['source_artifact']),
                                  'citation_basis': deepcopy(item['citation_basis']),
                                  'evidence_role': 'retrieved_context_not_physical_verdict'})
    if issues:
        _fail(issues)
    return {'schema_version': 'drafter-phase5-context/1.0.0',
            'structured_evidence_sha256': digest(entries),
            'source_authentication': 'not_performed_by_drafter',
            'physical_sufficiency': 'not_evaluated', 'safety_claim_verified': False,
            'empirical_admission_enabled': False,
            'entries': deepcopy(entries), 'retrieval': deepcopy(rows), 'citations': citations,
            'limitations': ['Consistency-checked retrieval is not independently authenticated source data.',
                            'Retrieval completeness covers explicit obligations, not R1 safety sufficiency.',
                            'The main_table alias and native robot/channel identities remain separately scoped context; no protected-object equivalence is inferred.',
                            'Phase 5 item and citation IDs are context references, not GSN node IDs or registry records.']}


def adapt_phase5_request(*, request_id, requirement_configuration, target_execution,
                         monitoring_scope, structured_request, evidence_bundle,
                         registry_records=(), test_fixture=False, limitations=()):
    """Adapt an existing retrieve(request) response; never query a database here.

    The caller supplies the exact query and returned bundle, with the complete
    R1 configuration and explicit monitoring scope. Existing original registry
    records are optional. Raw-channel-only bundles remain useful context for an
    unresolved draft; no replacement registry records are invented.
    """
    from .request_profiles import build_supplied_request
    return build_supplied_request(
        request_id=request_id, requirement_configuration=requirement_configuration,
        target_execution=target_execution, monitoring_scope=monitoring_scope,
        registry_records=registry_records, test_fixture=test_fixture, limitations=limitations,
        structured_evidence=[{'request': deepcopy(structured_request), 'bundle': deepcopy(evidence_bundle)}])
