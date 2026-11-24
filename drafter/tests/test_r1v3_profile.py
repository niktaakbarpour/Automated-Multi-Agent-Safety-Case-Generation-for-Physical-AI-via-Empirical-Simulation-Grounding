"""R1 v3 source-package profile: drafter-request/0.2.0 and draft-argument/0.2.0. CPU only, no model.

    python3 -m unittest drafter.tests.test_r1v3_profile -v

The real package (evaluation/m4_20261127/integration/ORIGINAL_EXECUTION_EVIDENCE_PACKAGE.json) has no admitted
checker assessment and no record citable under R1 v3, so every object stays insufficient_information. To test the
path where a definite outcome is allowed, some tests build a synthetic fixture (test_fixture=True): copies of one
record per object marked as R1 v3, and a test-only admission contract registered only for the duration of the test.
Neither is evidence or an admission.
"""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from drafter import argument_checks as AC, r1v3_profile as P, validation as V
from evaluation.r1_v4.provenance import digest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'evaluation/m4_20261127/integration/ORIGINAL_EXECUTION_EVIDENCE_PACKAGE.json'
TEST_CONTRACT = 'test-only-admission-contract'


def load_package():
    return json.loads(PACKAGE.read_text(encoding='utf-8'))


def graph(request, obj):
    scope = {'requirement_id': 'R1', 'requirement_version': P.REQUIREMENT_VERSION,
             'execution_id': request['target_execution']['execution_id'], 'object_id': obj,
             'domain': 'frame', 'clock': 'saved_frame_index', 'interval': list(request['monitoring_scope']['interval'])}
    provenance = {'request_sha256': digest(request), 'prose_review': 'required',
                  'role': 'proposed_reasoning_not_verified_physical_evidence', 'run_id': 'test-run'}

    def node(suffix, kind, statement, physical):
        return {'id': f'{obj}:{suffix}', 'type': kind, 'statement': statement, 'physical_claim': physical,
                'validation_status': 'unresolved' if physical else 'proposed', 'origin': 'llm_proposal',
                'evidence_id': None, 'scope': deepcopy(scope), 'provenance': deepcopy(provenance)}
    nodes = [node('G1', 'goal', f'R1 holds for {obj} from frame 10 to the terminal snapshot.', True),
             node('S1', 'strategy', 'Argue over initial table support and any fall from that support.', False),
             node('C1', 'context', 'The R1 v3 scope and the source package limitations apply.', False),
             node('U1', 'unresolved_claim', f'Initial support and falls of {obj} are not established here.', True)]
    edges = [{'source': f'{obj}:G1', 'target': f'{obj}:S1', 'type': 'supported_by'},
             {'source': f'{obj}:S1', 'target': f'{obj}:U1', 'type': 'supported_by'},
             {'source': f'{obj}:G1', 'target': f'{obj}:C1', 'type': 'in_context_of'}]
    return {'schema_version': '1.0.0', 'empirical_admission_enabled': False, 'nodes': nodes, 'edges': edges}


def argument(request, outcomes=None, backing=None):
    roster = request['requirement_configuration']['protected_objects']
    backing = backing or P.unresolved_backing(request)
    outcomes = outcomes or {obj: backing[obj]['outcome'] for obj in roster}
    return {
        'schema_version': P.ARGUMENT_VERSION, 'request_id': request['request_id'],
        'test_fixture': request['test_fixture'], 'request_sha256': digest(request),
        'requirement_configuration_sha256': request['requirement_configuration_sha256'],
        'source_package_sha256': request['source_package_sha256'], 'generation_status': 'accepted',
        'argument_bundle': {'execution_id': request['target_execution']['execution_id'], 'protected_objects': roster,
                            'graphs': [{'object_id': obj, 'graph': graph(request, obj)} for obj in roster],
                            'execution_conclusion': {'claimed_outcome': P.aggregate(outcomes),
                                                     'statement': P.authoritative_conclusion(outcomes),
                                                     'object_outcomes': outcomes, 'outcome_backing': backing}},
        'summary': P.authoritative_summary(request, outcomes),
        'reasoning_review': {'status': 'required', 'warning': AC.REVIEW_WARNING,
                             'summary': 'The model proposes an argument over initial support and falls.',
                             'limitations': ['Model text has not been checked against the source recordings.']},
        'limitations': AC.authoritative_limitations(request),
        'diagnostics': [],
        'validation': {'input_schema': 'passed', 'input_semantics': 'passed', 'output_schema': 'passed',
                       'graph_semantics': 'passed', 'evidence_references': 'passed', 'outcome_backing': 'passed',
                       'physical_sufficiency': 'not_assessed'},
        'generation_provenance': {'backend': 'not_run', 'model_id': None, 'model_revision': None, 'prompt_version': None,
                                  'prompt_sha256': None, 'run_id': None, 'raw_output_sha256': None},
        'empirical_admission_enabled': False, 'safety_claim_verified': False}


def rebind(argument_value, request):
    """Re-point an argument at a changed request (digests and provenance)."""
    value = deepcopy(argument_value)
    value['request_sha256'] = digest(request)
    for item in value['argument_bundle']['graphs']:
        for node in item['graph']['nodes']:
            node['provenance']['request_sha256'] = digest(request)
    return value


class RealPackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_package()
        cls.request = P.build_request(cls.package, request_id='m4-e2e-original-r1v3')

    def test_request_reports_the_package_status(self):
        summary = V.validate_request(self.request)
        self.assertEqual((summary['records'], summary['graph_eligible_records'], summary['checker_admission']),
                         (135, 0, 'not_admitted'))
        self.assertEqual(self.request['evidence']['record_requirement_versions'], ['2.0.0'])
        evidence = self.request['evidence']
        self.assertEqual(sorted(evidence['record_sha256']), sorted(evidence['record_ids']))
        self.assertEqual(evidence['retrieval']['database_sha256'], self.package['rag_source']['database_sha256'])
        self.assertEqual(evidence['retrieval']['queried_interval'], [10, 257])
        self.assertEqual(self.request['monitoring_scope']['interval'], [10, 257])
        self.assertEqual(self.request['target_execution']['trajectory_sha256'],
                         self.package['execution']['trajectory_sha256'])
        gaps = {(g['object_id'], g['gap']) for g in self.request['evidence_gaps']}
        for obj in self.request['requirement_configuration']['protected_objects']:
            self.assertIn((obj, 'no_v3_citable_evidence'), gaps)
            self.assertIn((obj, 'checker_assessment_not_admitted'), gaps)

    def test_configuration_is_bound_to_the_frozen_v3_files(self):
        config = self.request['requirement_configuration']
        self.assertEqual(P.configuration_issues(config), [])
        self.assertEqual(config['checker']['config_sha256'], self.package['checker_assessment']['config_sha256'])
        for name, path in P.FROZEN_SOURCES.items():
            self.assertEqual(config['frozen_sources'][name], {'path': path, 'sha256': P.file_sha256(path)})
        changed = deepcopy(config)
        changed['frozen_sources']['checker_config']['sha256'] = '0' * 64
        self.assertTrue(P.configuration_issues(changed))

    def test_unresolved_argument_is_accepted(self):
        result = V.validate_argument(argument(self.request), self.request)
        self.assertEqual(result['contract_status'], 'valid_output_contract')

    def test_definite_outcome_without_admission_is_refused(self):
        backing = P.unresolved_backing(self.request)
        a = self.request['checker_context']['assessments'][0]
        backing[a['object_id']] = {'outcome': a['classification'], 'checker_assessment': {
            'object_id': a['object_id'], 'classification': a['classification'],
            'checker_version': a['checker_version'], 'config_sha256': self.request['checker_context']['config_sha256'],
            'admission_contract': 'none'}, 'citations': []}
        with self.assertRaises(V.ContractError) as caught:
            V.validate_argument(argument(self.request, backing=backing), self.request)
        text = str(caught.exception)
        self.assertIn('checker_assessment_not_admitted:' + a['object_id'], text)
        self.assertIn('missing_citations:' + a['object_id'], text)

    def test_citing_a_v2_record_is_refused(self):
        backing = P.unresolved_backing(self.request)
        obj = 'cream_cheese_1'
        record = next(r for r in self.package['rag_source']['records'] if r['object_id'] == obj)
        backing[obj]['citations'] = [record['id']]
        with self.assertRaises(V.ContractError) as caught:
            V.validate_argument(argument(self.request, backing=backing), self.request)
        self.assertIn('ineligible_citation:' + obj, str(caught.exception))

    def test_bad_requests_are_refused(self):
        def refused(change, expected):
            request = deepcopy(self.request)
            change(request)
            with self.assertRaises(V.ContractError, msg=expected) as caught:
                V.validate_request(request)
            self.assertIn(expected, str(caught.exception))
        refused(lambda r: r['target_execution'].update(trajectory_sha256='0' * 64), 'derived_field_mismatch:target_execution')
        refused(lambda r: r['source_package']['execution'].update(trajectory_sha256='0' * 64), 'source_package_sha256_mismatch')
        refused(lambda r: r.update(source_package_sha256='0' * 64), 'source_package_sha256_mismatch')
        refused(lambda r: r['requirement_configuration'].update(requirement_statement='Another requirement.'),
                'configuration_not_bound_to_frozen_sources:requirement_statement')
        refused(lambda r: r['evidence'].update(graph_eligible_evidence_ids=[r['evidence']['record_ids'][0]]),
                'derived_field_mismatch:evidence')
        refused(lambda r: r.update(evidence_gaps=r['evidence_gaps'][1:]), 'derived_field_mismatch:evidence_gaps')
        refused(lambda r: r['evidence']['record_sha256'].update({r['evidence']['record_ids'][0]: '0' * 64}),
                'derived_field_mismatch:evidence')
        refused(lambda r: r['evidence']['retrieval'].update(database_sha256='0' * 64), 'derived_field_mismatch:evidence')
        refused(lambda r: r['checker_context']['admission'].update(state='admitted', contract='made-up'),
                'checker_admission_contract_unavailable')

    def test_bad_packages_are_refused(self):
        def refused(change, expected):
            package = deepcopy(self.package)
            change(package)
            with self.assertRaises(V.ContractError, msg=expected) as caught:
                P.build_request(package, request_id='x')
            self.assertIn(expected, str(caught.exception))
        refused(lambda p: p['execution'].update(requirement_version='2.0.0'), 'package_requirement_mismatch')
        refused(lambda p: p['execution'].update(protected_objects=p['execution']['protected_objects'][:4]),
                'package_object_roster_mismatch')
        refused(lambda p: p['execution'].update(monitoring_interval_saved_frames_inclusive=[11, 257]),
                'package_monitoring_interval_mismatch')
        refused(lambda p: p['checker_assessment'].update(config_sha256='0' * 64), 'checker_config_hash_mismatch')
        refused(lambda p: p['checker_assessment'].update(reference_answers_loaded=True), 'checker_loaded_reference_answers')
        refused(lambda p: p['checker_assessment']['object_assessments'][0].update(requirement_version='2.0.0'),
                'checker_assessment_requirement_mismatch')
        refused(lambda p: p['checker_assessment']['object_assessments'].pop(), 'checker_assessment_roster_mismatch')
        refused(lambda p: p['rag_source']['records'][0].update(execution_id='another-run'), 'record_execution_mismatch')
        refused(lambda p: p['rag_source']['records'].pop(), 'record_count_mismatch')
        refused(lambda p: p['rag_source'].update(queried_interval=[10, 200]), 'retrieval_interval_mismatch')
        refused(lambda p: p.update(human_labels={'cream_cheese_1': 'violation'}), 'human_reference_label_present')
        refused(lambda p: p['checker_assessment']['object_assessments'][0].update(gold_label='violation'),
                'human_reference_label_present')

    def test_the_exclusion_note_is_not_a_label(self):
        self.assertIn('excluded', self.package['evidence_semantics']['human_reference'])
        self.assertFalse(self.request['human_reference_included'])

    def test_version_dispatch(self):
        v2 = argument(self.request)
        v2['schema_version'] = 'draft-argument/0.1.0'
        with self.assertRaises(V.ContractError) as caught:
            V.validate_argument(v2, self.request)
        self.assertIn('request_and_argument_contract_versions_differ', str(caught.exception))


class AdmittedFixture(unittest.TestCase):
    """Synthetic test fixture: admitted assessments and v3-marked record copies, to test the definite path."""

    @classmethod
    def setUpClass(cls):
        package = load_package()
        records = package['rag_source']['records']
        cls.cited = {}
        for obj in package['execution']['protected_objects']:
            record = deepcopy(next(r for r in records if r['object_id'] == obj))
            record['requirement_version'] = P.REQUIREMENT_VERSION
            record['id'] = 'ev:test-fixture-v3-' + obj
            records.append(record)
            cls.cited[obj] = record['id']
        package['rag_source']['record_count_included'] = len(records)
        P.ADMISSION_VERIFIERS[TEST_CONTRACT] = lambda request: []
        cls.request = P.build_request(package, request_id='test-fixture-admitted', test_fixture=True,
                                      admission={'state': 'admitted', 'contract': TEST_CONTRACT,
                                                 'reason': 'Test-only admission inside a unit test.'})

    @classmethod
    def tearDownClass(cls):
        P.ADMISSION_VERIFIERS.pop(TEST_CONTRACT, None)

    def backed(self, obj, **change):
        a = next(x for x in self.request['checker_context']['assessments'] if x['object_id'] == obj)
        claim = {'object_id': obj, 'classification': a['classification'], 'checker_version': a['checker_version'],
                 'config_sha256': self.request['checker_context']['config_sha256'], 'admission_contract': TEST_CONTRACT}
        back = {'outcome': a['classification'], 'checker_assessment': claim, 'citations': [self.cited[obj]]}
        for key, value in change.items():
            if key in claim:
                claim[key] = value
            else:
                back[key] = value
        return back

    def all_backed(self, **per_object):
        backing = {obj: self.backed(obj) for obj in self.request['requirement_configuration']['protected_objects']}
        backing.update(per_object)
        return backing

    def check(self, backing, outcomes=None):
        return V.validate_argument(argument(self.request, outcomes=outcomes, backing=backing), self.request)

    def refused(self, backing, expected, outcomes=None):
        with self.assertRaises(V.ContractError) as caught:
            self.check(backing, outcomes)
        self.assertIn(expected, str(caught.exception))

    def test_fixture_request_is_valid(self):
        self.assertEqual(V.validate_request(self.request)['checker_admission'], 'admitted')
        self.assertEqual(len(self.request['evidence']['graph_eligible_evidence_ids']), 5)

    def test_backed_definite_outcomes_are_accepted(self):
        backing = self.all_backed()
        self.assertEqual(self.check(backing)['contract_status'], 'valid_output_contract')
        outcomes = {obj: b['outcome'] for obj, b in backing.items()}
        self.assertEqual(P.aggregate(outcomes), 'no_violation_observed_within_reviewed_coverage')

    def test_mixed_backed_and_unresolved_aggregates_to_unresolved(self):
        backing = self.all_backed(ketchup_1={'outcome': P.INSUFFICIENT, 'checker_assessment': None, 'citations': []})
        self.assertEqual(self.check(backing)['contract_status'], 'valid_output_contract')
        outcomes = {obj: b['outcome'] for obj, b in backing.items()}
        self.assertEqual(P.aggregate(outcomes), P.INSUFFICIENT)

    def test_unbacked_and_mismatched_conclusions_are_refused(self):
        self.refused(self.all_backed(cream_cheese_1=self.backed('cream_cheese_1', checker_assessment=None)),
                     'unbacked_outcome:cream_cheese_1')
        self.refused(self.all_backed(cream_cheese_1=self.backed('cream_cheese_1', citations=[])),
                     'missing_citations:cream_cheese_1')
        self.refused(self.all_backed(cream_cheese_1=self.backed('cream_cheese_1', classification='violation',
                                                                outcome='violation')),
                     'backing_assessment_mismatch:cream_cheese_1')
        self.refused(self.all_backed(cream_cheese_1=self.backed('cream_cheese_1', config_sha256='0' * 64)),
                     'backing_assessment_mismatch:cream_cheese_1')
        self.refused(self.all_backed(cream_cheese_1=self.backed('cream_cheese_1', citations=[self.cited['butter_1']])),
                     'ineligible_citation:cream_cheese_1')
        backing = self.all_backed()
        outcomes = {obj: b['outcome'] for obj, b in backing.items()}
        outcomes['milk_1'] = P.INSUFFICIENT
        self.refused(backing, 'outcome_backing_mismatch:milk_1', outcomes)

    def test_execution_outcome_must_be_the_r1_aggregation(self):
        value = argument(self.request, backing=self.all_backed())
        value['argument_bundle']['execution_conclusion']['claimed_outcome'] = 'not_applicable'
        with self.assertRaises(V.ContractError) as caught:
            V.validate_argument(value, self.request)
        self.assertIn('execution_outcome_not_r1_aggregation', str(caught.exception))

    def test_definite_outcome_refused_once_admission_is_withdrawn(self):
        request = deepcopy(self.request)
        request['checker_context']['admission'] = P.not_admitted()
        request['evidence_gaps'] = P.derived_fields(request['source_package'], request['requirement_configuration'])['evidence_gaps']
        backing = self.all_backed()
        value = rebind(argument(self.request, backing=backing), request)
        value['summary'] = P.authoritative_summary(request, {o: b['outcome'] for o, b in backing.items()})
        with self.assertRaises(V.ContractError) as caught:
            V.validate_argument(value, request)
        self.assertIn('checker_assessment_not_admitted', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
