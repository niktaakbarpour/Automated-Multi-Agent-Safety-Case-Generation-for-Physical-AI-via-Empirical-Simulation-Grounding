"""Deployment-blocked demonstrations are deterministic mocks, never model runs.

These checks use the original archived input and actual shared GSN validation.
They require no model, network connection or GPU.
"""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.r1_v4.evidence_registry_gsn.gsn import Graph, Node, Edge
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.provenance import digest
from drafter.__main__ import main
from drafter.mock_demo import run_mock_demo, validate_mock_demo
from drafter.validation import ROOT, ContractError, read_json, validate_argument


FIXTURE = ROOT / 'drafter/cases/scenario_a.request.json'


class MockDemoTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(FIXTURE)
        self.result = run_mock_demo(self.request)
        self.demo = self.result['argument']

    def test_mock_is_explicit_without_model_or_network_activity(self):
        with patch('drafter.generation.LocalModelClient') as client, \
                patch('socket.create_connection') as connect:
            result = run_mock_demo(self.request)
        client.assert_not_called()
        connect.assert_not_called()
        self.assertEqual(result['schema_version'], 'drafter-mock-run/0.1.0')
        self.assertEqual(result['status'], 'mock_demonstration')
        self.assertEqual(result['mode'], 'mock_demonstration')
        self.assertFalse(result['model_called'])
        self.assertFalse(result['project_evidence_sent'])
        self.assertFalse(result['live_model_result'])
        demo = result['argument']
        self.assertEqual(demo['schema_version'], 'drafter-mock-demo/0.1.0')
        self.assertEqual(demo['generation_status'], 'mock_demonstration')
        self.assertEqual(demo['deployment_status'], 'blocked')
        self.assertIsNone(demo['model_id'])
        self.assertIsNone(demo['prompt_sha256'])
        self.assertFalse(demo['model_called'])
        self.assertFalse(demo['live_model_result'])

    def test_original_input_and_evidence_are_unchanged(self):
        before = deepcopy(self.request)
        original_bytes = FIXTURE.read_bytes()
        result = run_mock_demo(self.request)
        self.assertEqual(self.request, before)
        self.assertEqual(FIXTURE.read_bytes(), original_bytes)
        self.assertEqual(result['argument']['request_sha256'], digest(before))
        self.assertEqual(result['argument']['requirement_configuration_sha256'],
                         before['requirement_configuration_sha256'])
        self.assertEqual(result['argument']['evidence_package_sha256'],
                         before['evidence_package_sha256'])

    def test_graphs_pass_original_gsn_validator_with_original_registry_records(self):
        records = tuple(Record.parse(r) for r in self.request['evidence_package']['records'])

        class ExportView:
            def records(self):
                return records

        for item in self.demo['argument_bundle']['graphs']:
            value = item['graph']
            graph = Graph(tuple(Node(**n) for n in value['nodes']),
                          tuple(Edge(**e) for e in value['edges']), value['schema_version'])
            self.assertIs(graph.validate(ExportView()), graph)
        self.assertEqual(validate_mock_demo(self.demo, self.request)['contract_status'],
                         'valid_mock_demonstration')

    def test_all_objects_and_missing_coverage_remain_unresolved(self):
        bundle = self.demo['argument_bundle']
        roster = self.request['requirement_configuration']['protected_objects']
        self.assertEqual(bundle['protected_objects'], roster)
        self.assertEqual([item['object_id'] for item in bundle['graphs']], roster)
        self.assertEqual(bundle['execution_conclusion']['claimed_outcome'], 'insufficient_information')
        self.assertEqual(bundle['execution_conclusion']['object_outcomes'],
                         {obj: 'insufficient_information' for obj in roster})
        all_text = json.dumps(self.demo)
        for obj in self.request['retrieval_context']['missing_objects']:
            self.assertIn(obj, all_text)
        self.assertFalse(self.demo['empirical_admission_enabled'])
        self.assertFalse(self.demo['safety_claim_verified'])
        for item in bundle['graphs']:
            for node in item['graph']['nodes']:
                if node['physical_claim']:
                    self.assertEqual(node['validation_status'], 'unresolved')

    def test_citations_preserve_exact_source_and_measurement_scope(self):
        records = {r['id']: r for r in self.request['evidence_package']['records']}
        eligible = set(self.request['evidence_handling']['graph_eligible_evidence_ids'])
        cited = set()
        for item in self.demo['argument_bundle']['graphs']:
            for node in item['graph']['nodes']:
                if node['type'] != 'solution':
                    self.assertEqual(node['origin'], 'unresolved_conclusion')
                    self.assertNotEqual(node['origin'], 'llm_proposal')
                    continue
                self.assertIn(node['evidence_id'], eligible)
                cited.add(node['evidence_id'])
                record = records[node['evidence_id']]
                self.assertEqual(node['scope']['object_id'], item['object_id'])
                for field in ('source_path', 'source_sha256', 'selector'):
                    self.assertEqual(node['provenance'][field], record[field])
                for field in ('requirement_id', 'requirement_version', 'execution_id',
                              'object_id', 'interval', 'clock', 'domain'):
                    self.assertEqual(node['scope'][field], record[field])
                self.assertEqual(node['validation_status'], record['validation_status'])
        self.assertTrue(cited)

    def test_repeat_runs_have_identical_graphs_and_plan_without_model_identity(self):
        second = run_mock_demo(self.request)['argument']
        self.assertEqual(self.demo['argument_bundle'], second['argument_bundle'])
        self.assertEqual(self.demo['mock_provenance']['plan'], second['mock_provenance']['plan'])
        self.assertEqual(self.demo['mock_provenance']['plan_sha256'],
                         second['mock_provenance']['plan_sha256'])
        self.assertEqual(self.demo['mock_provenance']['plan_sha256'],
                         digest(self.demo['mock_provenance']['plan']))

    def assert_tamper_rejected(self, mutate):
        demo = deepcopy(self.demo)
        mutate(demo)
        with self.assertRaises(ContractError):
            validate_mock_demo(demo, self.request)

    def test_mock_cannot_claim_model_execution_or_physical_verification(self):
        for field in ('model_called', 'live_model_result', 'empirical_admission_enabled',
                      'safety_claim_verified'):
            with self.subTest(field=field):
                self.assert_tamper_rejected(lambda d, f=field: d.__setitem__(f, True))
        self.assert_tamper_rejected(lambda d: d.__setitem__('model_id', 'Qwen/Qwen3-32B'))
        self.assert_tamper_rejected(lambda d: d.__setitem__('prompt_sha256', '0' * 64))

    def test_mock_and_live_argument_contracts_remain_separate(self):
        with self.assertRaises(ContractError):
            validate_argument(self.demo, self.request)

    def test_input_bindings_and_plan_hash_cannot_be_forged(self):
        for field in ('request_sha256', 'requirement_configuration_sha256', 'evidence_package_sha256'):
            with self.subTest(field=field):
                self.assert_tamper_rejected(lambda d, f=field: d.__setitem__(f, '0' * 64))
        for field in ('plan_sha256', 'template_sha256'):
            with self.subTest(field=field):
                self.assert_tamper_rejected(
                    lambda d, f=field: d['mock_provenance'].__setitem__(f, '0' * 64))

    def test_altered_plan_cannot_hide_behind_an_updated_hash(self):
        def mutate(demo):
            plan = demo['mock_provenance']['plan']
            plan['graphs'][0]['nodes'][0]['statement'] = 'The execution is certified safe.'
            demo['mock_provenance']['plan_sha256'] = digest(plan)
        self.assert_tamper_rejected(mutate)

    def test_wrong_source_or_outside_window_graph_is_rejected(self):
        def wrong_source(demo):
            node = next(n for g in demo['argument_bundle']['graphs']
                        for n in g['graph']['nodes'] if n['type'] == 'solution')
            node['provenance']['source_sha256'] = '0' * 64
        self.assert_tamper_rejected(wrong_source)
        self.assert_tamper_rejected(
            lambda d: d['argument_bundle']['graphs'][0]['graph']['nodes'][0]['scope'].__setitem__(
                'interval', [0, 12]))

    def test_invalid_graph_edges_and_promoted_claims_are_rejected(self):
        def invalid_edge(demo):
            graph = demo['argument_bundle']['graphs'][0]['graph']
            graph['edges'].append({'source': graph['nodes'][0]['id'],
                                   'target': 'MISSING', 'type': 'supported_by'})
        self.assert_tamper_rejected(invalid_edge)
        self.assert_tamper_rejected(
            lambda d: d['argument_bundle']['graphs'][0]['graph']['nodes'][0].__setitem__(
                'validation_status', 'verified_measurement'))

    def test_invalid_input_never_creates_a_demo_or_contacts_a_model(self):
        del self.request['requirement_configuration']
        with patch('drafter.generation.LocalModelClient') as client, \
                patch('socket.create_connection') as connect:
            result = run_mock_demo(self.request)
        self.assertEqual(result['status'], 'rejected')
        self.assertIsNone(result['argument'])
        self.assertFalse(result['model_called'])
        client.assert_not_called()
        connect.assert_not_called()


class MockDemoCliTests(unittest.TestCase):
    def invoke(self, arguments):
        output = io.StringIO()
        with patch('sys.argv', ['drafter', *arguments]), redirect_stdout(output):
            code = main()
        return code, json.loads(output.getvalue())

    def test_cli_saves_clearly_labelled_graph_run_and_review_without_a_model(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / 'mock.run.json'
            argument_path = Path(directory) / 'mock.argument.json'
            review_path = Path(directory) / 'mock.review.md'
            with patch('drafter.generation.LocalModelClient') as client, \
                    patch('socket.create_connection') as connect:
                code, result = self.invoke([
                    '--mock-demo', str(FIXTURE), '--out', str(report_path),
                    '--argument-out', str(argument_path), '--review-out', str(review_path)])
            self.assertEqual(code, 0, result)
            self.assertEqual(result['status'], 'mock_demonstration')
            self.assertEqual(json.loads(report_path.read_text()), result)
            demo = json.loads(argument_path.read_text())
            self.assertEqual(demo, result['argument'])
            self.assertEqual(validate_mock_demo(demo, read_json(FIXTURE))['contract_status'],
                             'valid_mock_demonstration')
            review = review_path.read_text().lower()
            self.assertIn('mock', review)
            self.assertIn('unresolved', review)
            self.assertFalse(demo['model_called'])
            client.assert_not_called()
            connect.assert_not_called()

    def test_existing_outputs_are_preserved_before_demo_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / 'mock.run.json'
            report_path.write_text('existing result', encoding='utf-8')
            with patch('drafter.mock_demo.run_mock_demo') as run:
                code, result = self.invoke(['--mock-demo', str(FIXTURE), '--out', str(report_path)])
            self.assertEqual(code, 1)
            self.assertFalse(result['model_called'])
            self.assertEqual(report_path.read_text(), 'existing result')
            run.assert_not_called()

    def test_invalid_input_saves_rejection_and_no_argument(self):
        with tempfile.TemporaryDirectory() as directory:
            request = read_json(FIXTURE)
            del request['requirement_configuration']
            input_path = Path(directory) / 'invalid.json'
            input_path.write_text(json.dumps(request), encoding='utf-8')
            report_path = Path(directory) / 'mock.run.json'
            argument_path = Path(directory) / 'mock.argument.json'
            code, result = self.invoke(['--mock-demo', str(input_path), '--out', str(report_path),
                                        '--argument-out', str(argument_path)])
            self.assertEqual(code, 1)
            self.assertEqual(result['status'], 'rejected')
            self.assertFalse(result['model_called'])
            self.assertEqual(json.loads(report_path.read_text()), result)
            self.assertFalse(argument_path.exists())

    def test_mock_option_refuses_a_model_configuration(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            self.invoke(['--mock-demo', str(FIXTURE), '--model-config', 'model.json', '--out', 'out.json'])
        self.assertEqual(context.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
