"""Independent PR20 regression boundaries; all completions here are scripted."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.r1_v4.provenance import digest
from drafter.generation import generate_argument
from drafter.validation import (ROOT, ContractError, read_json, validate_argument,
                                validate_argument_bundle, validate_request, schema_issues)
from drafter.request_profiles import build_supplied_request
from drafter.phase5_adapter import adapt_phase5_request
from drafter.llm import FrozenLocalModelConfig, ModelDiscoveryResult
from drafter.__main__ import main
from .test_generation import model_plan, reply
from .test_llm import MODEL, configuration
from .test_phase5_adapter import fixture_parts, rebind_query


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        self.config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))

    def generated(self, request=None, plan=None):
        request = self.request if request is None else request
        with patch('drafter.generation.LocalModelClient') as client:
            client.return_value.discover_models.return_value = ModelDiscoveryResult(
                status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.return_value.complete.return_value = reply(model_plan(request) if plan is None else plan)
            result = generate_argument(request, self.config)
        self.assertEqual(schema_issues(result, 'generation_run.schema.json'), [])
        return result

    def parts(self):
        return dict(request_id='independent-supplied',
                    requirement_configuration=deepcopy(self.request['requirement_configuration']),
                    target_execution=deepcopy(self.request['target_execution']),
                    monitoring_scope=deepcopy(self.request['monitoring_scope']),
                    registry_records=deepcopy(self.request['evidence_package']['records']), test_fixture=True)

    def test_original_semantic_provenance_forgeries_are_rejected(self):
        argument = self.generated()['argument']
        for key in ('run_id', 'request_sha256', 'prompt_sha256', 'role', 'serializer_version'):
            with self.subTest(key=key):
                changed = deepcopy(argument)
                changed['argument_bundle']['graphs'][0]['graph']['nodes'][0]['provenance'][key] = 'FORGED'
                with self.assertRaisesRegex(ContractError, 'provenance_binding'):
                    validate_argument(changed, self.request)

    def test_other_reasoning_nodes_and_removed_fields_are_bound(self):
        argument = self.generated()['argument']
        for kind in ('strategy', 'context', 'unresolved_claim'):
            with self.subTest(kind=kind):
                changed = deepcopy(argument)
                node = next(n for n in changed['argument_bundle']['graphs'][0]['graph']['nodes'] if n['type'] == kind)
                del node['provenance']['request_sha256']
                with self.assertRaisesRegex(ContractError, 'provenance_binding'):
                    validate_argument(changed, self.request)

    def test_standalone_cannot_promote_context_status(self):
        argument = self.generated()['argument']
        next(n for n in argument['argument_bundle']['graphs'][0]['graph']['nodes']
             if n['type'] == 'context')['validation_status'] = 'verified_source'
        with self.assertRaisesRegex(ContractError, 'reasoning_status'):
            validate_argument(argument, self.request)

    def test_prompt_identity_and_oversized_standalone_graph_fail_closed(self):
        argument = self.generated()['argument']
        argument['generation_provenance']['prompt_version'] = 'another-prompt'
        with self.assertRaisesRegex(ContractError, 'prompt_version_binding'):
            validate_argument(argument, self.request)
        argument = self.generated()['argument']; graph = argument['argument_bundle']['graphs'][1]['graph']
        prior = next(n['id'] for n in graph['nodes'] if n['type'] == 'unresolved_claim')
        template = deepcopy(next(n for n in graph['nodes'] if n['type'] == 'unresolved_claim'))
        for i in range(1100):
            n = deepcopy(template); n['id'] = 'ketchup_1:overflow_' + str(i)
            graph['nodes'].append(n)
            graph['edges'].append({'source': prior, 'target': n['id'], 'type': 'supported_by'})
            prior = n['id']
        with self.assertRaisesRegex(ContractError, 'argument_plan_schema'):
            validate_argument_bundle(argument['argument_bundle'], self.request)

    def test_overlong_and_word_placeholders_reject_without_repair(self):
        for text in ('TODO TODO TODO', 'placeholder placeholder', 'TBD TBD TBD', 'R1 ' * 15,
                     'A complete statement. ' * 100):
            for where in ('summary', 'statement', 'limitations'):
                with self.subTest(text=text[:30], where=where):
                    plan = model_plan(self.request)
                    if where == 'summary': plan['summary'] = text
                    elif where == 'limitations': plan['limitations'] = [text]
                    else: plan['graphs'][0]['nodes'][0]['statement'] = text
                    original = deepcopy(plan)
                    result = self.generated(plan=plan)
                    self.assertEqual(result['status'], 'rejected')
                    self.assertIsNone(result['argument']['argument_bundle'])
                    self.assertEqual(plan, original)

    def test_standalone_applies_decoder_graph_shape_limits(self):
        original = self.generated()['argument']
        for what in ('text', 'identifier', 'nodes', 'edges'):
            with self.subTest(what=what):
                argument = deepcopy(original)
                graph = argument['argument_bundle']['graphs'][0]['graph']
                if what == 'text': graph['nodes'][0]['statement'] = 'A complete sentence. ' * 100
                elif what == 'identifier':
                    old = graph['nodes'][0]['id']; new = old + '!'  # GSN alone allows it, decoder does not.
                    graph['nodes'][0]['id'] = new
                    for e in graph['edges']:
                        for key in ('source', 'target'):
                            if e[key] == old: e[key] = new
                elif what == 'nodes':
                    for i in range(25):
                        n = deepcopy(next(n for n in graph['nodes'] if n['type'] == 'context'))
                        n['id'] += ':' + str(i); graph['nodes'].append(n)
                        graph['edges'].append({'source': graph['nodes'][0]['id'], 'target': n['id'], 'type': 'in_context_of'})
                else: graph['edges'] *= 30
                with self.assertRaises(ContractError):
                    validate_argument(argument, self.request)

    def test_model_review_cannot_evade_text_limit_with_whitespace(self):
        original = self.generated()['argument']
        text = 'R1' + ' ' * 1700 + 'remains unresolved.'
        for field in ('summary', 'limitations'):
            with self.subTest(field=field):
                argument = deepcopy(original)
                argument['reasoning_review'][field] = text if field == 'summary' else [text]
                with self.assertRaisesRegex(ContractError, 'unusable_prose'):
                    validate_argument(argument, self.request)

    def test_huge_numeric_request_is_rejected_before_client(self):
        for where in ('scope', 'configuration', 'record', 'nested_provenance'):
            with self.subTest(where=where):
                request = deepcopy(self.request)
                if where == 'scope': request['monitoring_scope']['interval'][1] = 10**1000
                elif where == 'configuration': request['requirement_configuration']['monitoring_interval']['end']['value'] = 10**1000
                elif where == 'record': request['evidence_package']['records'][0]['interval'][1] = 10**1000
                else: request['evidence_package']['records'][0]['provenance']['huge'] = 10**1000
                with patch('drafter.generation.LocalModelClient') as client:
                    result = generate_argument(request, self.config)
                client.assert_not_called()
                self.assertEqual(result['status'], 'rejected')
                self.assertEqual(schema_issues(result, 'generation_run.schema.json'), [])
                self.assertTrue(any('number_outside_supported_finite_range' in d['code'] for d in result['diagnostics']))

    def test_huge_standalone_intervals_are_contract_errors(self):
        argument = self.generated()['argument']
        argument['argument_bundle']['graphs'][0]['graph']['nodes'][0]['scope']['interval'][1] = 10**1000
        with self.assertRaisesRegex(ContractError, 'number_outside_supported_finite_range'):
            validate_argument(argument, self.request)

    def test_builder_rejects_unsupported_numbers_and_cycles_before_hashing(self):
        parts = self.parts()
        parts['monitoring_scope']['interval'][1] = 10**1000
        with self.assertRaisesRegex(ContractError, 'number_outside_supported_finite_range'):
            build_supplied_request(**parts)
        parts = self.parts(); parts['requirement_configuration']['cycle'] = parts['requirement_configuration']
        with self.assertRaisesRegex(ContractError, 'cyclic_input'):
            build_supplied_request(**parts)

    def test_deep_input_and_nonstring_keys_have_clear_diagnostics(self):
        for value in ('depth', 'keys'):
            request = deepcopy(self.request)
            if value == 'keys': request['evidence_package']['records'][0]['provenance'][0] = 'bad key'
            else:
                nested = 0
                for _ in range(140): nested = [nested]
                request['evidence_package']['records'][0]['provenance']['deep'] = nested
            result = generate_argument(request, self.config)
            self.assertEqual(result['status'], 'rejected')
            self.assertFalse(result['model_called'])
            self.assertEqual(schema_issues(result, 'generation_run.schema.json'), [])

    def test_empty_scope_rejected_but_shared_noncyclic_values_work(self):
        parts = self.parts(); parts['requirement_configuration']['protected_objects'] = []
        parts['requirement_configuration']['object_surface_mapping'] = {}; parts['registry_records'] = []
        with self.assertRaisesRegex(ContractError, 'nonempty_drafter_object_scope_required'):
            build_supplied_request(**parts)
        parts = self.parts(); shared = ['Source remains unauthenticated.']
        parts['registry_records'][0]['provenance']['first'] = shared
        parts['registry_records'][0]['provenance']['second'] = shared
        parts['registry_records'][0]['id'] = 'ev:' + digest({k: v for k, v in parts['registry_records'][0].items() if k != 'id'})
        # Other records depend on original IDs, so test the JSON guard separately.
        from drafter.validation import json_value_issues
        self.assertEqual(json_value_issues(parts), [])

    def test_original_public_request_status_mismatch_is_rejected(self):
        parts = fixture_parts()
        # The frozen public API does not support an object-filtered contact query.
        obligation = next(o for o in parts['structured_request']['obligations'] if o['family'] == 'contact_references')
        obligation['object_id'] = parts['requirement_configuration']['protected_objects'][0]
        rebind_query(parts)
        from critic.phase5_request import refusal
        self.assertEqual(refusal(parts['structured_request'])[0], 'UNSUPPORTED')
        with self.assertRaisesRegex(ContractError, 'public_request_refused'):
            adapt_phase5_request(**parts)

    def test_old_consumer_dependency_fails_closed(self):
        with patch.dict('sys.modules', {'critic.phase5_request': None}):
            with self.assertRaisesRegex(ContractError, 'current_consumer_required'):
                adapt_phase5_request(**fixture_parts())

    def test_cli_malformed_input_reports_have_a_schema(self):
        for text in ('{broken', '{"x":1,"x":2}', '{"x":NaN}', '[' * 2000 + '0' + ']' * 2000):
            with self.subTest(text=text[:20]), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / 'input.json'; source.write_text(text)
                target = Path(directory) / 'report.json'
                args = ['drafter', '--generate', str(source), '--model-config',
                        str(ROOT / 'drafter/config/qwen3_32b_sglang.example.json'), '--out', str(target)]
                with patch('sys.argv', args), redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)
                self.assertEqual(schema_issues(read_json(target), 'operation_rejection.schema.json'), [])


if __name__ == '__main__':
    unittest.main()
