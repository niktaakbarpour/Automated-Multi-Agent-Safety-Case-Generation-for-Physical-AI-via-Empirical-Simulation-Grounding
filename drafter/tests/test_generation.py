"""Generation checks with scripted responses, never a live model evaluation.

The original archived scenario A supplies real registry metadata. All model replies
in this module are explicitly constructed test data and establish no safety result.
"""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.r1_v4.provenance import digest
from drafter.generation import generate_argument, solution_statement
from drafter.__main__ import main
from drafter.llm import CompletionResult, FrozenLocalModelConfig, ModelDiscoveryResult
from drafter.validation import ROOT, read_json, validate_argument
from .test_llm import MODEL, configuration, fake_endpoint


FIXTURE = ROOT / 'drafter/cases/scenario_a.request.json'


def model_plan(request):
    """Construct a test response, not a saved example or executed LLM result."""
    eligible = set(request['evidence_handling']['graph_eligible_evidence_ids'])
    graphs = []
    for obj in request['requirement_configuration']['protected_objects']:
        prefix = obj + ':'
        nodes = [
            {'id': prefix + 'G1', 'type': 'goal', 'statement': 'Whether R1 is satisfied remains unresolved.',
             'evidence_id': None, 'physical_claim': True},
            {'id': prefix + 'S1', 'type': 'strategy', 'statement': 'Assess initial applicability and falling departures using available evidence.',
             'evidence_id': None, 'physical_claim': False},
            {'id': prefix + 'C1', 'type': 'context', 'statement': 'Saved frames 10-12 contain metadata references only; missing observations remain explicit.',
             'evidence_id': None, 'physical_claim': False},
            {'id': prefix + 'U1', 'type': 'unresolved_claim', 'statement': 'Initial support and any qualifying fall cannot be established from supplied metadata.',
             'evidence_id': None, 'physical_claim': True},
        ]
        edges = [
            {'source': prefix + 'G1', 'target': prefix + 'S1', 'type': 'supported_by'},
            {'source': prefix + 'G1', 'target': prefix + 'C1', 'type': 'in_context_of'},
            {'source': prefix + 'S1', 'target': prefix + 'U1', 'type': 'supported_by'},
        ]
        records = [r for r in request['evidence_package']['records'] if r['id'] in eligible and r['object_id'] == obj]
        if records:
            record = records[0]
            nodes.append({'id': prefix + 'E1', 'type': 'solution', 'statement': solution_statement(record),
                          'evidence_id': record['id'], 'physical_claim': False})
            edges.append({'source': prefix + 'U1', 'target': prefix + 'E1', 'type': 'supported_by'})
        graphs.append({'object_id': obj, 'root_id': prefix + 'G1', 'nodes': nodes, 'edges': edges})
    return {'graphs': graphs, 'summary': 'The supplied metadata cannot establish the physical R1 outcome.',
            'limitations': ['No source replay or physical checker was performed; missing observations remain unresolved.']}


def reply(plan):
    text = json.dumps(plan, separators=(',', ':'), sort_keys=True)
    raw = {'model': MODEL, 'choices': [{'message': {'role': 'assistant', 'content': text}, 'finish_reason': 'stop'}]}
    return CompletionResult(status='ok', text=text, parsed_json=plan, raw_response=raw,
                            finish_reason='stop', effective_model_id=MODEL,
                            request_sha256='1' * 64, response_sha256=hashlib.sha256(json.dumps(raw).encode()).hexdigest())


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(FIXTURE)
        self.config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))
        self.plan = model_plan(self.request)

    def run_plan(self, plan=None):
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(
                status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.complete.return_value = reply(self.plan if plan is None else plan)
            result = generate_argument(self.request, self.config)
            self.assertEqual(client.complete.call_count, 1)
            return result

    def assert_rejected(self):
        result = self.run_plan()
        self.assertEqual(result['status'], 'rejected', result)
        self.assertTrue(result['model_called'])
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertTrue(result['diagnostics'])
        self.assertEqual(validate_argument(result['argument'], self.request)['contract_status'], 'valid_failure_contract')

    def test_valid_response_builds_shared_gsn_and_preserves_input(self):
        before = deepcopy(self.request)
        result = self.run_plan()
        self.assertEqual(result['schema_version'], 'drafter-generation-run/0.1.0')
        self.assertEqual(result['status'], 'accepted', result)
        self.assertTrue(result['model_called'])
        argument = result['argument']
        self.assertEqual(argument['request_sha256'], digest(self.request))
        self.assertEqual(validate_argument(argument, self.request)['contract_status'], 'valid_output_contract')
        bundle = argument['argument_bundle']
        self.assertEqual(bundle['protected_objects'], before['requirement_configuration']['protected_objects'])
        self.assertEqual(bundle['execution_conclusion']['claimed_outcome'], 'insufficient_information')
        self.assertEqual(set(bundle['execution_conclusion']['object_outcomes'].values()), {'insufficient_information'})
        self.assertFalse(argument['empirical_admission_enabled'])
        self.assertFalse(argument['safety_claim_verified'])
        self.assertEqual(self.request, before)

    def test_host_attaches_exact_original_solution_source_scope_and_status(self):
        result = self.run_plan()
        records = {r['id']: r for r in self.request['evidence_package']['records']}
        count = 0
        for wrapped in result['argument']['argument_bundle']['graphs']:
            for node in wrapped['graph']['nodes']:
                self.assertEqual(node['scope']['object_id'], wrapped['object_id'])
                self.assertEqual(node['scope']['execution_id'], self.request['target_execution']['execution_id'])
                if node['physical_claim']:
                    self.assertEqual(node['validation_status'], 'unresolved')
                if node['type'] == 'solution':
                    count += 1
                    record = records[node['evidence_id']]
                    for key in ('source_path', 'source_sha256', 'selector'):
                        self.assertEqual(node['provenance'][key], record[key])
                    for key in ('requirement_id', 'requirement_version', 'object_id', 'execution_id', 'domain', 'clock', 'interval'):
                        self.assertEqual(node['scope'][key], record[key])
                    self.assertEqual(node['validation_status'], record['validation_status'])
                    self.assertEqual(node['statement'], solution_statement(record))
        self.assertEqual(count, 1)

    def test_trace_records_sent_prompt_schema_and_actual_model_identity(self):
        result = self.run_plan()
        trace = result['trace']
        text = '\n'.join(m['content'] for m in trace['messages'])
        for object_id in self.request['requirement_configuration']['protected_objects']:
            self.assertIn(object_id, text)
        for evidence_id in self.request['evidence_handling']['graph_eligible_evidence_ids']:
            self.assertIn(evidence_id, text)
        self.assertIn('metadata', text.lower())
        self.assertIn('unresolved', text.lower())
        self.assertIsInstance(trace['json_schema'], dict)
        self.assertIsInstance(trace['completion'], dict)
        provenance = result['argument']['generation_provenance']
        self.assertEqual(provenance['model_id'], MODEL)
        self.assertIsNone(provenance['model_revision'])
        self.assertEqual(provenance['raw_output_sha256'], hashlib.sha256(reply(self.plan).text.encode()).hexdigest())

    def test_invalid_input_is_rejected_before_client_creation(self):
        del self.request['requirement_configuration']
        with patch('drafter.generation.LocalModelClient') as constructor:
            result = generate_argument(self.request, self.config)
        constructor.assert_not_called()
        self.assertEqual(result['status'], 'rejected')
        self.assertFalse(result['model_called'])
        self.assertIsNone(result['argument'])

    def test_discovery_failure_never_attempts_completion_or_fallback(self):
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(
                status='error', model_ids=('other-model',), configured_model_available=False,
                error_code='configured_model_unavailable', message='No configured model.')
            result = generate_argument(self.request, self.config)
        client.complete.assert_not_called()
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['model_called'])
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertEqual(validate_argument(result['argument'], self.request)['contract_status'], 'valid_failure_contract')

    def test_completion_timeout_does_not_claim_model_execution(self):
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.complete.return_value = CompletionResult(status='error', error_code='timeout', message='Request timed out.')
            result = generate_argument(self.request, self.config)
        self.assertEqual(result['status'], 'failed')
        self.assertIsNone(result['model_called'])
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertEqual(validate_argument(result['argument'], self.request)['contract_status'], 'valid_failure_contract')

    def test_truncated_model_output_is_not_accepted_or_repaired(self):
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.complete.return_value = CompletionResult(status='error', finish_reason='length',
                effective_model_id=MODEL, raw_response={'model': MODEL, 'choices': []},
                error_code='incomplete_completion', message='Output truncated.')
            result = generate_argument(self.request, self.config)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['model_called'])
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertEqual(validate_argument(result['argument'], self.request)['contract_status'], 'valid_failure_contract')

    def test_invalid_model_configuration_returns_valid_failure_envelope(self):
        with patch('drafter.llm.LocalModelClient.discover_models') as discover:
            result = generate_argument(self.request, None)
        discover.assert_not_called()
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['model_called'])
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertEqual(validate_argument(result['argument'], self.request)['contract_status'], 'valid_failure_contract')

    def test_redacted_completion_is_not_used_to_build_a_graph(self):
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(status='ok', configured_model_available=True, model_ids=(MODEL,))
            value = reply(self.plan)
            client.complete.return_value = CompletionResult(**{**value.__dict__, 'response_redacted': True})
            result = generate_argument(self.request, self.config)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['model_called'])
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertEqual(validate_argument(result['argument'], self.request)['contract_status'], 'valid_failure_contract')

    def test_missing_object_graph_is_rejected(self):
        self.plan['graphs'].pop()
        self.assert_rejected()

    def test_duplicate_object_graph_is_rejected(self):
        self.plan['graphs'][1] = deepcopy(self.plan['graphs'][0])
        self.assert_rejected()

    def test_nonphysical_goal_cannot_hide_missing_safety_claim(self):
        self.plan['graphs'][0]['nodes'][0]['physical_claim'] = False
        self.assert_rejected()

    def test_physical_claim_cannot_be_hidden_in_context(self):
        self.plan['graphs'][0]['nodes'][2]['physical_claim'] = True
        self.assert_rejected()

    def test_forged_host_fields_are_rejected(self):
        self.plan['graphs'][0]['nodes'][0]['validation_status'] = 'checker_qualified'
        self.assert_rejected()

    def test_unknown_or_context_only_evidence_is_rejected(self):
        node = self.plan['graphs'][0]['nodes'][-1]
        for evidence_id in ('ev:invented', self.request['evidence_handling']['context_only_evidence_ids'][0]):
            with self.subTest(evidence_id=evidence_id):
                node['evidence_id'] = evidence_id
                self.assert_rejected()

    def test_evidence_cannot_move_to_another_object(self):
        solution = deepcopy(self.plan['graphs'][0]['nodes'][-1])
        graph = self.plan['graphs'][1]
        solution['id'] = graph['object_id'] + ':E1'
        graph['nodes'].append(solution)
        graph['edges'].append({'source': graph['object_id'] + ':U1', 'target': solution['id'], 'type': 'supported_by'})
        self.assert_rejected()

    def test_solution_text_cannot_promote_metadata_to_physical_evidence(self):
        self.plan['graphs'][0]['nodes'][-1]['statement'] = 'The object was fully supported and did not fall.'
        self.assert_rejected()

    def test_available_evidence_cannot_all_be_omitted(self):
        graph = self.plan['graphs'][0]
        removed = graph['nodes'].pop()['id']
        graph['edges'] = [e for e in graph['edges'] if e['target'] != removed]
        self.assert_rejected()

    def test_cycle_is_rejected_by_real_shared_graph_validator(self):
        graph = self.plan['graphs'][0]
        graph['edges'].append({'source': graph['object_id'] + ':U1', 'target': graph['root_id'], 'type': 'supported_by'})
        self.assert_rejected()

    def test_invalid_edge_type_relationship_is_rejected(self):
        self.plan['graphs'][0]['edges'][0]['type'] = 'in_context_of'
        self.assert_rejected()

    def test_dangling_edge_is_rejected(self):
        self.plan['graphs'][0]['edges'][0]['target'] = 'missing-node'
        self.assert_rejected()

    def test_disconnected_node_is_rejected(self):
        self.plan['graphs'][0]['edges'].pop(1)
        self.assert_rejected()

    def test_bare_unresolved_goal_is_not_a_complete_draft(self):
        graph = self.plan['graphs'][1]
        graph['nodes'] = graph['nodes'][:1]
        graph['edges'] = []
        self.assert_rejected()

    def test_strategy_requires_a_supported_subclaim_even_when_all_nodes_are_connected(self):
        graph = self.plan['graphs'][0]
        prefix = graph['object_id'] + ':'
        graph['edges'] = [edge for edge in graph['edges'] if edge['source'] != prefix + 'S1']
        graph['edges'].append({'source': prefix + 'G1', 'target': prefix + 'U1', 'type': 'supported_by'})
        self.assert_rejected()

    def test_node_identifiers_cannot_collide_across_object_graphs(self):
        self.plan['graphs'][1]['nodes'][0]['id'] = self.plan['graphs'][0]['root_id']
        self.assert_rejected()


class GenerationCliTests(unittest.TestCase):
    """A temporary HTTP server returns scripted plans, never real inference."""
    def invoke(self, arguments):
        output = io.StringIO()
        with patch('sys.argv', ['drafter', *arguments]), redirect_stdout(output):
            code = main()
        return code, json.loads(output.getvalue())

    def config_file(self, directory, base_url):
        path = Path(directory) / 'model.json'
        path.write_text(json.dumps(configuration(base_url, max_response_bytes=1048576)), encoding='utf-8')
        return path

    def test_http_generation_saves_valid_graph_trace_and_readable_review(self):
        request = read_json(FIXTURE)
        original_bytes = FIXTURE.read_bytes()
        with fake_endpoint() as state, tempfile.TemporaryDirectory() as directory:
            config = self.config_file(directory, state['base_url'])
            state['completion_body']['choices'][0]['message']['content'] = json.dumps(model_plan(request))
            report_path = Path(directory) / 'run.json'
            argument_path = Path(directory) / 'argument.json'
            review_path = Path(directory) / 'review.md'
            arguments = ['--generate', str(FIXTURE), '--model-config', str(config),
                         '--out', str(report_path), '--argument-out', str(argument_path),
                         '--review-out', str(review_path)]
            code, result = self.invoke(arguments)
            self.assertEqual(code, 0, result)
            self.assertEqual(result['status'], 'accepted')
            self.assertEqual(json.loads(report_path.read_text()), result)
            argument = json.loads(argument_path.read_text())
            self.assertEqual(argument, result['argument'])
            self.assertEqual(validate_argument(argument, request)['contract_status'], 'valid_output_contract')
            self.assertIn(MODEL, review_path.read_text())
            self.assertIn('unresolved', review_path.read_text().lower())
            self.assertEqual([r['method'] for r in state['requests']], ['GET', 'POST'])
            payload = state['requests'][1]['body']
            self.assertEqual(payload['model'], MODEL)
            self.assertEqual(payload['messages'], result['trace']['messages'])
            self.assertEqual(payload['response_format']['json_schema']['schema'], result['trace']['json_schema'])
            self.assertIn('choices', result['trace']['completion']['raw_response'])
            # Re-running into existing outputs stops before either HTTP operation.
            saved = {p: p.read_bytes() for p in (report_path, argument_path, review_path)}
            code, repeated = self.invoke(arguments)
            self.assertEqual(code, 1)
            self.assertFalse(repeated['model_called'])
            self.assertEqual(len(state['requests']), 2)
            for path, content in saved.items():
                self.assertEqual(path.read_bytes(), content)
        self.assertEqual(FIXTURE.read_bytes(), original_bytes)

    def test_invalid_input_saves_rejection_without_contacting_server(self):
        with fake_endpoint() as state, tempfile.TemporaryDirectory() as directory:
            config = self.config_file(directory, state['base_url'])
            request = read_json(FIXTURE)
            del request['requirement_configuration']
            input_path = Path(directory) / 'invalid.json'
            input_path.write_text(json.dumps(request), encoding='utf-8')
            report_path = Path(directory) / 'run.json'
            argument_path = Path(directory) / 'argument.json'
            code, result = self.invoke(['--generate', str(input_path), '--model-config', str(config),
                                        '--out', str(report_path), '--argument-out', str(argument_path)])
            self.assertEqual(code, 1)
            self.assertEqual(result['status'], 'rejected')
            self.assertFalse(result['model_called'])
            self.assertIsNone(result['argument'])
            self.assertEqual(json.loads(report_path.read_text()), result)
            self.assertFalse(argument_path.exists())
            self.assertEqual(state['requests'], [])

    def test_rejected_model_reply_preserves_trace_and_failure_artifacts(self):
        request = read_json(FIXTURE)
        with fake_endpoint() as state, tempfile.TemporaryDirectory() as directory:
            config = self.config_file(directory, state['base_url'])
            # Valid JSON with no usable graph must remain a rejection, not a repair.
            state['completion_body']['choices'][0]['message']['content'] = '{"graphs":[]}'
            report_path = Path(directory) / 'run.json'
            argument_path = Path(directory) / 'argument.json'
            review_path = Path(directory) / 'review.md'
            code, result = self.invoke(['--generate', str(FIXTURE), '--model-config', str(config),
                                        '--out', str(report_path), '--argument-out', str(argument_path),
                                        '--review-out', str(review_path)])
            self.assertEqual(code, 1)
            self.assertEqual(result['status'], 'rejected')
            self.assertTrue(result['model_called'])
            self.assertTrue(result['diagnostics'])
            self.assertIsNone(result['argument']['argument_bundle'])
            self.assertEqual(result['trace']['completion']['text'], '{"graphs":[]}')
            self.assertEqual(json.loads(report_path.read_text()), result)
            self.assertEqual(validate_argument(json.loads(argument_path.read_text()), request)['contract_status'],
                             'valid_failure_contract')
            self.assertIn('No argument was accepted.', review_path.read_text())

    def test_conflicting_or_missing_parent_output_paths_prevent_model_access(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config_file(directory, 'http://127.0.0.1:12345/v1')
            report_path = Path(directory) / 'run.json'
            variants = [
                ['--out', str(report_path), '--argument-out', str(report_path)],
                ['--out', str(Path(directory) / 'missing' / 'run.json')],
            ]
            for outputs in variants:
                with self.subTest(outputs=outputs), patch('drafter.generation.LocalModelClient') as constructor:
                    code, result = self.invoke(['--generate', str(FIXTURE), '--model-config', str(config), *outputs])
                    self.assertEqual(code, 1)
                    self.assertFalse(result['model_called'])
                    constructor.assert_not_called()

    def test_repeated_scripted_runs_preserve_citations_and_scopes_without_changing_input(self):
        request = read_json(FIXTURE)
        before = FIXTURE.read_bytes()
        with fake_endpoint() as state, tempfile.TemporaryDirectory() as directory:
            config = self.config_file(directory, state['base_url'])
            state['completion_body']['choices'][0]['message']['content'] = json.dumps(model_plan(request))
            runs = []
            for index in range(2):
                code, result = self.invoke(['--generate', str(FIXTURE), '--model-config', str(config),
                                            '--out', str(Path(directory) / f'run-{index}.json')])
                self.assertEqual(code, 0, result)
                runs.append(result)
            def citations(run):
                return [(wrapped['object_id'], node['id'], node['evidence_id'], node['scope'])
                        for wrapped in run['argument']['argument_bundle']['graphs']
                        for node in wrapped['graph']['nodes']]
            self.assertEqual(citations(runs[0]), citations(runs[1]))
            self.assertNotEqual(runs[0]['run_id'], runs[1]['run_id'])
            self.assertEqual([r['method'] for r in state['requests']], ['GET', 'POST', 'GET', 'POST'])
        self.assertEqual(FIXTURE.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
