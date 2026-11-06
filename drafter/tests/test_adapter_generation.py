"""End-to-end consumer boundary with scripted model responses only."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from drafter.__main__ import main
from drafter.generation import generate_argument, render_review
from drafter.llm import FrozenLocalModelConfig, ModelDiscoveryResult
from drafter.mock_demo import run_mock_demo
from drafter.phase5_adapter import evidence_context
from drafter.validation import ContractError, ROOT, read_json, validate_argument, validate_request
from .test_generation import model_plan, reply
from .test_llm import MODEL, configuration
from .test_phase5_adapter import fixture_parts, request_with, direct_registry_link
from .test_input_profiles import registry_input


class AdapterGenerationTests(unittest.TestCase):
    def generate(self, request):
        plan = model_plan(request)
        config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(
                status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.complete.return_value = reply(plan)
            result = generate_argument(request, config)
        self.assertEqual(result['status'], 'accepted', result['diagnostics'])
        return result

    def test_phase5_raw_context_reaches_model_trace_and_accepted_output(self):
        request = request_with()
        result = self.generate(request)
        payload = json.loads(result['trace']['messages'][1]['content'])
        expected = evidence_context(request)
        self.assertEqual(payload['structured_evidence'], expected)
        self.assertEqual(result['argument']['evidence_context'], expected)
        self.assertEqual(result['argument']['argument_bundle']['protected_objects'],
                         request['requirement_configuration']['protected_objects'])
        self.assertFalse(result['argument']['safety_claim_verified'])
        self.assertEqual(validate_argument(result['argument'], request)['contract_status'], 'valid_output_contract')
        self.assertIn('review required', render_review(result))
        for mutation in ('drop', 'alter'):
            argument = deepcopy(result['argument'])
            if mutation == 'drop':
                del argument['evidence_context']
            else:
                argument['evidence_context']['citations'].pop()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ContractError, 'structured_evidence_binding'):
                validate_argument(argument, request)

    def test_phase5_direct_registry_reference_is_a_real_solution_node(self):
        parts = fixture_parts()
        record = direct_registry_link(parts)
        request = request_with(parts)
        result = self.generate(request)
        solutions = [n for wrapped in result['argument']['argument_bundle']['graphs']
                     for n in wrapped['graph']['nodes'] if n['type'] == 'solution']
        self.assertEqual([n['evidence_id'] for n in solutions], [record['id']])
        self.assertEqual(solutions[0]['provenance']['registry_record'], record)
        for wrapped in result['argument']['argument_bundle']['graphs']:
            ids = {node['id'] for node in wrapped['graph']['nodes']}
            self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in wrapped['graph']['edges']))

    def test_alternate_roster_works_in_mock_and_scripted_generation(self):
        request = registry_input(objects=['different_object_a', 'different_object_b'], records=False)
        result = self.generate(request)
        mock = run_mock_demo(request)
        self.assertEqual(mock['status'], 'mock_demonstration', mock['diagnostics'])
        self.assertEqual(result['argument']['argument_bundle']['protected_objects'], ['different_object_a', 'different_object_b'])

    def test_prepare_commands_save_validated_inputs_without_model_access(self):
        fixture = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        registry_parts = dict(request_id='cli-supplied', requirement_configuration=fixture['requirement_configuration'],
                              target_execution=fixture['target_execution'], monitoring_scope=fixture['monitoring_scope'],
                              registry_records=fixture['evidence_package']['records'], test_fixture=True)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for mode, parts in (('--adapt-phase5', fixture_parts()), ('--prepare-registry', registry_parts)):
                source, target = folder / (mode[2:] + '.input.json'), folder / (mode[2:] + '.request.json')
                source.write_text(json.dumps(parts))
                with patch('sys.argv', ['drafter', mode, str(source), '--out', str(target)]), \
                        patch('drafter.generation.LocalModelClient') as client, redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 0)
                client.assert_not_called()
                request = read_json(target)
                self.assertEqual(validate_request(request)['contract_status'], 'valid_supplied_input')
