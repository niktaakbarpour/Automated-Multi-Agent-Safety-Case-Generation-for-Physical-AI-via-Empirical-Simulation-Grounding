"""Shared-validation regressions from the audit; no real model is called."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from drafter.argument_checks import (REVIEW_WARNING, authoritative_conclusion,
                                     authoritative_limitations, authoritative_summary,
                                     graph_structure_issues, prose_issues)
from drafter.generation import generate_argument
from drafter.llm import FrozenLocalModelConfig, ModelDiscoveryResult
from drafter.mock_demo import run_mock_demo
from drafter.validation import (ROOT, ContractError, read_json, validate_argument,
                                 validate_argument_bundle)
from .test_generation import model_plan, reply
from .test_llm import MODEL, configuration


class UnifiedGraphValidationTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        result = run_mock_demo(self.request)
        self.assertEqual(result['status'], 'mock_demonstration', result['diagnostics'])
        self.bundle = deepcopy(result['argument']['argument_bundle'])

    def rejected(self, diagnostic):
        with self.assertRaises(ContractError) as caught:
            validate_argument_bundle(self.bundle, self.request)
        self.assertTrue(any(diagnostic in x for x in caught.exception.issues), caught.exception.issues)

    def remove_type(self, kind):
        value = self.bundle['graphs'][0]['graph']
        removed = {node['id'] for node in value['nodes'] if node['type'] == kind}
        value['nodes'] = [node for node in value['nodes'] if node['id'] not in removed]
        value['edges'] = [edge for edge in value['edges']
                          if not removed.intersection((edge['source'], edge['target']))]

    def test_complete_mock_bundle_still_passes_shared_validation(self):
        self.assertEqual(validate_argument_bundle(self.bundle, self.request)['contract_status'],
                         'valid_argument_bundle')

    def test_standalone_no_longer_accepts_one_goal_per_object(self):
        for wrapped in self.bundle['graphs']:
            value = wrapped['graph']
            value['nodes'] = [node for node in value['nodes'] if node['type'] == 'goal'][:1]
            value['edges'] = []
        self.rejected('argument_strategy_and_context_required:')

    def test_missing_strategy_rejected(self):
        self.remove_type('strategy')
        self.rejected('argument_strategy_and_context_required:')

    def test_missing_context_rejected(self):
        self.remove_type('context')
        self.rejected('argument_strategy_and_context_required:')

    def test_disconnected_node_rejected(self):
        value = self.bundle['graphs'][0]['graph']
        node = deepcopy(next(n for n in value['nodes'] if n['type'] == 'context'))
        node['id'] += ':disconnected'
        value['nodes'].append(node)
        self.rejected('argument_disconnected_nodes:')

    def test_strategy_without_subclaim_rejected(self):
        value = self.bundle['graphs'][0]['graph']
        strategies = {n['id'] for n in value['nodes'] if n['type'] == 'strategy'}
        value['edges'] = [e for e in value['edges'] if e['source'] not in strategies]
        self.rejected('argument_strategy_needs_subclaim:')

    def test_no_physical_goal_root_rejected(self):
        node = next(n for n in self.bundle['graphs'][0]['graph']['nodes'] if n['type'] == 'goal')
        node['type'], node['physical_claim'] = 'unresolved_claim', True
        self.rejected('argument_physical_root_required:')

    def test_false_physical_flag_cannot_hide_goal(self):
        next(n for n in self.bundle['graphs'][0]['graph']['nodes'] if n['type'] == 'goal')['physical_claim'] = False
        self.rejected('argument_physical_claim_type:')

    def test_available_evidence_cannot_be_omitted(self):
        self.remove_type('solution')
        self.rejected('argument_missing_available_evidence:')

    def test_evidence_id_is_not_a_graph_endpoint(self):
        value = self.bundle['graphs'][0]['graph']
        evidence_id = next(n['evidence_id'] for n in value['nodes'] if n['type'] == 'solution')
        value['edges'][0]['target'] = evidence_id
        self.rejected('argument_invalid_edge_endpoint:')

    def test_solution_statement_cannot_claim_physical_success(self):
        next(n for n in self.bundle['graphs'][0]['graph']['nodes'] if n['type'] == 'solution')['statement'] = 'This proves all objects are safe.'
        self.rejected('argument_solution_statement_mismatch:')

    def test_embedded_record_cannot_lose_original_limitations(self):
        node = next(n for n in self.bundle['graphs'][0]['graph']['nodes'] if n['type'] == 'solution')
        node['provenance']['registry_record']['limitations'] = []
        self.rejected('argument_solution_record_binding:')

    def test_single_character_node_statement_rejected(self):
        self.bundle['graphs'][0]['graph']['nodes'][0]['statement'] = 'R'
        self.rejected('unusable_prose:node:')

    def test_conflicting_execution_conclusion_rejected(self):
        self.bundle['execution_conclusion']['statement'] = 'All objects are certified safe.'
        self.rejected('argument_authoritative_conclusion_mismatch')

    def test_graph_order_matches_supplied_configuration(self):
        self.bundle['graphs'].reverse()
        self.rejected('argument_graph_roster_mismatch')

    def test_plan_and_serialized_graph_share_structure_rules(self):
        wrapped = self.bundle['graphs'][0]
        value, obj = wrapped['graph'], wrapped['object_id']
        root = next(n['id'] for n in value['nodes'] if n['type'] == 'goal')
        self.assertEqual(graph_structure_issues(value, obj, root_id=root, prefix='plan'), [])
        plan = dict(deepcopy(value), root_id=root)
        self.assertEqual(graph_structure_issues(plan, obj, prefix='plan'), [])
        self.assertTrue(graph_structure_issues(plan, obj, root_id=obj + ':unknown', prefix='plan'))


class ProseReviewValidationTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        self.plan = model_plan(self.request)
        self.config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))

    def generate(self):
        with patch('drafter.generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(
                status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.complete.return_value = reply(self.plan)
            return generate_argument(self.request, self.config)

    def valid_argument(self):
        result = self.generate()
        self.assertEqual(result['status'], 'accepted', result['diagnostics'])
        return result['argument']

    def rejected(self, argument, diagnostic):
        with self.assertRaises(ContractError) as caught:
            validate_argument(argument, self.request)
        self.assertTrue(any(diagnostic in x for x in caught.exception.issues), caught.exception.issues)

    def test_model_claims_cannot_replace_authoritative_unresolved_summary(self):
        self.plan['summary'] = 'All objects are certified safe and R1 is satisfied.'
        self.plan['limitations'] = ['A validated checker proved no violations during the full execution.']
        self.plan['graphs'][0]['nodes'][0]['statement'] = 'Cream cheese is proven safe and did not fall.'
        argument = self.valid_argument()
        self.assertEqual(argument['summary'], authoritative_summary(self.request))
        self.assertEqual(argument['limitations'], authoritative_limitations(self.request))
        self.assertEqual(argument['argument_bundle']['execution_conclusion']['statement'], authoritative_conclusion())
        self.assertEqual(argument['reasoning_review']['status'], 'required')
        self.assertEqual(argument['reasoning_review']['warning'], REVIEW_WARNING)
        self.assertEqual(argument['reasoning_review']['summary'], self.plan['summary'])
        for wrapped in argument['argument_bundle']['graphs']:
            for node in wrapped['graph']['nodes']:
                if node['type'] != 'solution':
                    self.assertEqual(node['provenance']['prose_review'], 'required')

    def test_standalone_rejects_changed_authoritative_summary(self):
        argument = self.valid_argument()
        argument['summary'] = 'All objects are certified safe.'
        self.rejected(argument, 'argument_authoritative_summary_mismatch')

    def test_standalone_rejects_changed_authoritative_limitations(self):
        argument = self.valid_argument()
        argument['limitations'].append('A validated checker proved no violations.')
        self.rejected(argument, 'argument_authoritative_limitations_mismatch')

    def test_standalone_rejects_removed_node_review_marker(self):
        argument = self.valid_argument()
        del argument['argument_bundle']['graphs'][0]['graph']['nodes'][0]['provenance']['prose_review']
        self.rejected(argument, 'argument_node_prose_review_required:')

    def test_unreviewed_model_prose_cannot_masquerade_as_deterministic_mock(self):
        argument = self.valid_argument()
        argument['argument_bundle']['graphs'][0]['graph']['nodes'][0]['origin'] = 'unresolved_conclusion'
        self.rejected(argument, 'argument_model_prose_origin:')

    def test_single_character_and_whitespace_prose_rejected(self):
        for text in ('R', ' ', 'RRRRRRRRRR', 'R1'):
            with self.subTest(text=text):
                self.assertTrue(prose_issues(text, 'test'))
        self.assertEqual(prose_issues('R1 remains unresolved.', 'test'), [])

    def test_bad_model_summary_is_rejected_without_accepting_empty_reasoning(self):
        self.plan['summary'] = 'R'
        result = self.generate()
        self.assertEqual(result['status'], 'rejected')
        self.assertIsNone(result['argument']['argument_bundle'])


if __name__ == '__main__':
    unittest.main()
