"""Saved/simulated Phase 5 consumer tests. No Hestia, database or LLM calls."""
from copy import deepcopy
import unittest

from critic import retrieval as consumer
from evaluation.r1_v4.provenance import digest
from drafter.phase5_adapter import adapt_phase5_request, evidence_context
from drafter.request_profiles import validate_supplied_request
from drafter.validation import ContractError, ROOT, read_json, validate_request


def fixture_parts():
    """Current Critic synthetic fixture, retained as synthetic throughout."""
    fixture = read_json(ROOT / 'critic/cases/case_e_partial_structured_retrieval.json')
    ctx = fixture['evaluation_context']
    config = deepcopy(ctx['r1_configuration'])
    config['benchmark']['policy_checkpoint'] = ctx['model_checkpoint']
    return dict(
        request_id='synthetic-phase5-adapter', requirement_configuration=config,
        target_execution={k: ctx[k] for k in ('execution_id', 'benchmark', 'task_id', 'model_checkpoint', 'variant_id')},
        monitoring_scope={**deepcopy(ctx['monitored_interval']), 'bounds': 'inclusive',
                          'resolution_status': 'fixture_declared', 'boundary_provenance': ['synthetic:test-fixture']},
        structured_request=deepcopy(fixture['structured_evidence'][0]['request']),
        evidence_bundle=deepcopy(fixture['structured_evidence'][0]['bundle']), test_fixture=True)


def request_with(parts=None):
    return adapt_phase5_request(**(fixture_parts() if parts is None else parts))


def rebind_query(parts):
    """Maintain legitimate transport bindings when changing a test query."""
    q, b = parts['structured_request'], parts['evidence_bundle']
    b['query_id'] = 'query:' + digest(q)
    b['requested_obligations'] = deepcopy(q['obligations'])
    for obligation, group in zip(q['obligations'], b['groups']):
        group['request_digest'] = digest(obligation)


def rejected_snapshot(parts, status='INVALID SCOPE'):
    """Echo a structurally invalid query exactly, as a no-evidence rejection."""
    q, b = parts['structured_request'], parts['evidence_bundle']
    b['query_id'] = 'query:' + digest(q)
    obligations = q.get('obligations', [])
    b['requested_obligations'] = deepcopy(obligations) if isinstance(obligations, list) else []
    b.update(completeness_status=status, conditional_assumptions=[])
    b['independent_validation'] = {'passed': False}
    b['assurance_status'].update(satisfied=False, returned_values_verified=False)
    by_id = {o['id']: o for o in obligations if isinstance(o, dict) and isinstance(o.get('id'), str)} \
        if isinstance(obligations, list) else {}
    b['groups'] = [g for g in b['groups'] if g['obligation_id'] in by_id]
    for g in b['groups']:
        g.update(status=status, items=[], reason='Synthetic invalid request', conditional_assumptions=[])
        g['request_digest'] = digest(by_id[g['obligation_id']])
    b['missing_obligations'] = [{k: g[k] for k in ('obligation_id', 'mandatory', 'status', 'reason')}
                                for g in b['groups']]


def linked_registry_item(parts):
    """A recorded contact reference, supported by both authoritative contracts."""
    group = next(g for g in parts['evidence_bundle']['groups']
                 if g['family'] == 'contact_references' and g['status'] == 'AVAILABLE')
    return group, group['items'][0]


def direct_registry_link(parts):
    """Synthetic raw-contact Record with an exact direct source reference.

    Geometry identity stays context: the release's object_identity crosswalk is
    not an allowed raw-measurement type in the shared registry Record contract.
    The existing available contact group supplies a legitimate overlap/citation
    without changing any obligation fulfillment or missing-evidence status.
    """
    record = deepcopy(read_json(ROOT / 'drafter/cases/scenario_a.request.json')['evidence_package']['records'][0])
    group, item = linked_registry_item(parts)
    obligation = next(o for o in parts['structured_request']['obligations']
                      if o['id'] == group['obligation_id'])
    # Frozen public contact_references accepts no object filter. This explicit
    # synthetic Record belongs to a configured object; the global contact source
    # is not relabelled as an object-specific retrieval obligation.
    obj = parts['requirement_configuration']['protected_objects'][0]
    frame = item['value']['saved_frame_index']
    target = parts['target_execution']
    record.update(object_id=obj, execution_id=target['execution_id'], task_id=target['task_id'],
                  benchmark=target['benchmark'], model_checkpoint=target['model_checkpoint'],
                  interval=[frame, frame], dependencies=[], conflicts=[], missing_intervals=[],
                  source_path='/disk/1/data/niktakbr/drafter-adapter-synthetic/contacts.json',
                  source_sha256=item['source_artifact']['sha256'], selector=item['source_artifact']['selector'],
                  measurement_type='contact', provenance={'synthetic': True, 'physical_truth': 'U'})
    record['id'] = 'ev:' + digest({k: v for k, v in record.items() if k != 'id'})
    item['source_artifact']['path'] = record['source_path']
    item['id'] = 'source-ref:' + digest([item['source_artifact'][k] for k in ('path', 'sha256', 'selector')])
    item['original_evidence_ids'] = [record['id']]
    item['citation_basis'] = consumer.expected_basis(item, obligation)
    item['citation_id'] = 'evidence-citation:' + digest(item['citation_basis'])
    parts['registry_records'] = [record]
    return record


class Phase5AdapterTests(unittest.TestCase):
    def test_exact_query_bundle_values_provenance_and_citations_are_preserved(self):
        parts = fixture_parts()
        before = deepcopy(parts)
        request = request_with(parts)
        self.assertEqual(parts, before)
        self.assertEqual(request['structured_evidence'], [{'request': parts['structured_request'],
                                                         'bundle': parts['evidence_bundle']}])
        ctx = evidence_context(request)
        self.assertEqual(ctx['entries'], request['structured_evidence'])
        self.assertEqual(ctx['retrieval'][0]['completeness_status'], 'PARTIAL')
        self.assertTrue(ctx['citations'])
        self.assertTrue(all(row['citation_id'].startswith('evidence-citation:') for row in ctx['citations']))
        self.assertFalse(ctx['safety_claim_verified'])
        self.assertEqual(request['evidence_package']['records'], [])
        self.assertEqual(request['evidence_handling']['graph_eligible_evidence_ids'], [])
        self.assertEqual(validate_request(request)['contract_status'], 'valid_supplied_input')

    def test_missing_mandatory_and_optional_obligations_remain_distinct(self):
        request = request_with()
        row = evidence_context(request)['retrieval'][0]
        missing = {entry['obligation_id']: entry for entry in row['missing_obligations']}
        self.assertTrue(missing['settling_actions']['mandatory'])
        self.assertFalse(missing['camera_frames']['mandatory'])
        self.assertFalse(request['empirical_admission_enabled'])

    def test_complete_retrieval_keeps_optional_gap_and_does_not_become_safety(self):
        parts = fixture_parts()
        q, b = parts['structured_request'], parts['evidence_bundle']
        q['obligations'][1]['mandatory'] = False
        b['groups'][1]['mandatory'] = False
        b['missing_obligations'][0]['mandatory'] = False
        b['independent_validation']['obligations'][1]['mandatory'] = False
        b['independent_validation']['mandatory_fulfilled'] = True
        b['assurance_status']['satisfied'] = True
        b['completeness_status'] = 'COMPLETE WITHIN VERIFIED CONTRACT'
        rebind_query(parts)
        request = request_with(parts)
        self.assertEqual(evidence_context(request)['retrieval'][0]['completeness_status'], b['completeness_status'])
        self.assertFalse(request['safety_claim_verified'])
        self.assertEqual(len(request['structured_evidence'][0]['bundle']['missing_obligations']), 2)

    def test_noncomplete_empty_responses_are_preserved(self):
        for status in ('UNAVAILABLE', 'UNSUPPORTED', 'INVALID SCOPE', 'UNVERIFIED PLAN'):
            with self.subTest(status=status):
                parts = fixture_parts()
                b = parts['evidence_bundle']
                b['completeness_status'] = status
                b['independent_validation'] = {'passed': False, 'errors': ['synthetic source unavailable']}
                b['assurance_status']['satisfied'] = False
                b['assurance_status']['returned_values_verified'] = False
                for g in b['groups']:
                    g.update(status=status, items=[], reason='Synthetic unavailable response', conditional_assumptions=[])
                b['missing_obligations'] = [{k: g[k] for k in ('obligation_id', 'mandatory', 'status', 'reason')}
                                            for g in b['groups']]
                b['conditional_assumptions'] = []
                request = request_with(parts)
                ctx = evidence_context(request)
                self.assertEqual(ctx['retrieval'][0]['completeness_status'], status)
                self.assertEqual(ctx['citations'], [])

    def test_tampering_is_rejected(self):
        mutations = {
            'source_hash': lambda b: b['groups'][0]['items'][0]['source_artifact'].update(sha256='0' * 64),
            'citation_id': lambda b: b['groups'][0]['items'][0].update(citation_id='evidence-citation:' + '0' * 64),
            'dropped_mandatory': lambda b: b['groups'].pop(1),
            'dropped_gap': lambda b: b['missing_obligations'].pop(),
            'false_complete': lambda b: b.update(completeness_status='COMPLETE WITHIN VERIFIED CONTRACT'),
            'safety_promotion': lambda b: b.update(safety_claim_verified=True),
            'changed_units': lambda b: b['groups'][2]['items'][0]['units'].update(value='m'),
            'dropped_limitations': lambda b: b.update(limitations=[]),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                parts = fixture_parts()
                mutate(parts['evidence_bundle'])
                with self.assertRaises(ContractError):
                    request_with(parts)

    def test_wrong_execution_task_and_variant_are_rejected(self):
        for key in ('execution_id', 'task_id', 'variant_id'):
            with self.subTest(key=key):
                parts = fixture_parts()
                parts['target_execution'][key] = 'other-scope'
                with self.assertRaisesRegex(ContractError, 'SCOPE'):
                    request_with(parts)

    def test_wrong_object_or_window_is_rejected_even_after_query_rebinding(self):
        for key in ('object', 'window'):
            with self.subTest(key=key):
                parts = fixture_parts()
                if key == 'object':
                    # Missing group has no item: object scope still needs checking.
                    parts['structured_request']['obligations'][0]['object_id'] = 'object_not_configured'
                    parts['evidence_bundle']['groups'][0]['items'][0]['value']['object_id'] = 'object_not_configured'
                else:
                    parts['monitoring_scope']['interval'] = [1, 2]
                    parts['requirement_configuration']['monitoring_interval']['start']['value'] = 1
                rebind_query(parts)
                with self.assertRaisesRegex(ContractError, 'phase5_obligation_'):
                    request_with(parts)

    def test_conditional_assumptions_cannot_be_dropped(self):
        parts = fixture_parts()
        q, b = parts['structured_request'], parts['evidence_bundle']
        q['obligations'][2]['required_properties'] = ['units']
        group = b['groups'][2]
        item = group['items'][0]
        item['interpretation_properties']['units']['status'] = 'CONDITIONAL'
        item['units']['status'] = 'CONDITIONAL'
        group['conditional_assumptions'] = ['units']
        b['conditional_assumptions'] = [{'obligation_id': group['obligation_id'], 'properties': ['units']}]
        rebind_query(parts)
        item['citation_basis'] = consumer.expected_basis(item, q['obligations'][2])
        item['citation_id'] = 'evidence-citation:' + digest(item['citation_basis'])
        request = request_with(parts)
        self.assertEqual(evidence_context(request)['retrieval'][0]['conditional_assumptions'], b['conditional_assumptions'])
        b['conditional_assumptions'] = []
        with self.assertRaisesRegex(ContractError, 'CONDITIONAL'):
            request_with(parts)

    def test_valid_direct_registry_reference_uses_original_record_id(self):
        parts = fixture_parts()
        record = direct_registry_link(parts)
        request = request_with(parts)
        self.assertEqual(request['evidence_package']['records'], [record])
        self.assertEqual(request['evidence_handling']['graph_eligible_evidence_ids'], [record['id']])
        linked = [row for row in evidence_context(request)['citations']
                  if record['id'] in row['original_evidence_ids']]
        self.assertEqual(len(linked), 1)
        self.assertNotEqual(record['id'], linked[0]['citation_id'])
        self.assertEqual(record['measurement_type'], 'contact')

    def test_forged_registry_link_is_rejected_despite_valid_content_hashes(self):
        for field, value in [('source_path', '/disk/1/data/niktakbr/unrelated.json'),
                             ('source_sha256', '1' * 64), ('selector', '/another/source')]:
            with self.subTest(field=field):
                parts = fixture_parts()
                record = direct_registry_link(parts)
                record[field] = value
                record['id'] = 'ev:' + digest({k: v for k, v in record.items() if k != 'id'})
                linked_registry_item(parts)[1]['original_evidence_ids'] = [record['id']]
                with self.assertRaisesRegex(ContractError, 'registry_link_source_mismatch'):
                    request_with(parts)

    def test_registry_link_type_must_match_current_release_crosswalk(self):
        parts = fixture_parts()
        record = direct_registry_link(parts)
        record['measurement_type'] = 'native_geometry'
        record['id'] = 'ev:' + digest({k: v for k, v in record.items() if k != 'id'})
        linked_registry_item(parts)[1]['original_evidence_ids'] = [record['id']]
        with self.assertRaisesRegex(ContractError, 'RET-CROSSWALK'):
            request_with(parts)

    def test_structured_snapshot_digest_is_bound(self):
        request = request_with()
        request['structured_evidence'][0]['bundle']['reason'] = 'Changed after adaptation'
        with self.assertRaisesRegex(ContractError, 'structured_evidence_digest_mismatch'):
            validate_supplied_request(request)

    def test_malformed_nested_snapshot_is_clear_error(self):
        for value in (None, [], {'groups': None}, {'schema_version': 'wrong'}):
            with self.subTest(value=value):
                parts = fixture_parts()
                parts['evidence_bundle'] = value
                with self.assertRaises(ContractError):
                    request_with(parts)

    def test_rejected_request_with_malformed_selector_is_clear_error(self):
        for selector in (None, 7, {}, {'kind': 'frames'}, {'kind': 'frames', 'start': 0},
                         {'kind': 'frames', 'end': 2}, {'kind': 'frames', 'start': True, 'end': 2}):
            with self.subTest(selector=selector):
                parts = fixture_parts()
                parts['structured_request']['obligations'][1]['selector'] = selector
                rejected_snapshot(parts)
                with self.assertRaises(ContractError):
                    request_with(parts)

    def test_main_table_alias_remains_context_outside_protected_object_roster(self):
        for available in (True, False):
            with self.subTest(available=available):
                parts = fixture_parts()
                q, b = parts['structured_request'], parts['evidence_bundle']
                obligation, group = q['obligations'][0], b['groups'][0]
                obligation.update(family='main_table_identity', field='verified_symbolic_alias', object_id='main_table')
                group['family'] = 'main_table_identity'
                item = group['items'][0]
                item['family'] = 'main_table_identity'
                item['value'] = {'symbolic_alias': 'main_table', 'native_object': 'table',
                                 'physical_support_inferred': False}
                item['original_evidence_ids'] = []
                rebind_query(parts)
                item['citation_basis'] = consumer.expected_basis(item, obligation)
                item['citation_id'] = 'evidence-citation:' + digest(item['citation_basis'])
                if not available:
                    rejected_snapshot(parts, 'UNAVAILABLE')
                request = request_with(parts)
                context = evidence_context(request)
                self.assertNotIn('main_table', request['requirement_configuration']['protected_objects'])
                self.assertEqual(request['evidence_package']['records'], [])
                self.assertFalse(context['safety_claim_verified'])
                self.assertEqual(context['entries'][0]['request']['obligations'][0]['object_id'], 'main_table')

    def test_native_robot_filter_does_not_become_a_protected_object(self):
        parts = fixture_parts()
        parts['structured_request']['obligations'][2]['object_id'] = 'robot0'
        rebind_query(parts)
        request = request_with(parts)
        self.assertNotIn('robot0', request['requirement_configuration']['protected_objects'])
        self.assertEqual(request['evidence_package']['records'], [])
        self.assertEqual(evidence_context(request)['entries'][0]['request']['obligations'][2]['object_id'], 'robot0')

    def test_rejected_request_malformed_obligation_or_provenance_is_clear_error(self):
        for value in (None, 7, {}, [7], [{'id': []}], [{'id': None}]):
            with self.subTest(obligations=value):
                parts = fixture_parts()
                parts['structured_request']['obligations'] = value
                rejected_snapshot(parts)
                with self.assertRaises(ContractError):
                    request_with(parts)
        for value in (None, 7, []):
            with self.subTest(provenance=value):
                parts = fixture_parts()
                parts['structured_request']['provenance'] = value
                rejected_snapshot(parts)
                with self.assertRaises(ContractError):
                    request_with(parts)


if __name__ == '__main__':
    unittest.main()
