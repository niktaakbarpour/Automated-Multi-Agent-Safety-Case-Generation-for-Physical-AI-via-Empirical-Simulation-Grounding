"""Local regressions for the reported constrained-output failures.

These use constructed plans, not the unshared Hestia model output. They do not
claim to rerun Qwen or XGrammar; the separate compatibility tool does CPU checks
when that optional serving dependency is available.
"""
from copy import deepcopy
import unittest

from jsonschema import Draft202012Validator

from drafter.generation import _serialize_plan
from drafter.mock_demo import _mock_provenance
from drafter.plan_schema import build_plan_schema, validate_plan_prose
from drafter.validation import ContractError, ROOT, read_json
from .test_generation import model_plan


class DecoderRegressionTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        self.plan = model_plan(self.request)
        self.schema = build_plan_schema(self.request)
        self.validator = Draft202012Validator(self.schema)

    def test_full_sentences_and_valid_graph_reference_shape_are_allowed(self):
        self.validator.validate(self.plan)
        validate_plan_prose(self.plan)
        text = Draft202012Validator(self.schema['$defs']['text'])
        self.assertTrue(text.is_valid('R1 remains unresolved for all protected objects.'))
        self.assertFalse(text.is_valid('R'))
        self.assertFalse(text.is_valid('R' * 1601))

    def test_decoder_text_has_no_substring_regex_or_unique_items(self):
        self.assertNotIn('pattern', self.schema['$defs']['text'])
        def walk(value):
            if isinstance(value, dict):
                self.assertNotIn('uniqueItems', value)
                for nested in value.values():
                    walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested)
        walk(self.schema)

    def test_original_evidence_identity_is_not_a_graph_endpoint(self):
        graph = self.plan['graphs'][0]
        evidence = self.request['evidence_handling']['graph_eligible_evidence_ids'][0]
        graph['edges'][-1]['target'] = evidence
        self.assertFalse(self.validator.is_valid(self.plan))
        with self.assertRaises(ContractError) as caught:
            _serialize_plan(self.plan, self.request, _mock_provenance(self.plan), mock=True)
        self.assertTrue(any('invalid_edge_endpoint' in issue for issue in caught.exception.issues))

    def test_missing_declared_node_remains_a_host_rejection(self):
        graph = self.plan['graphs'][0]
        graph['edges'][-1]['target'] = graph['object_id'] + ':not_declared'
        # Namespace alone cannot express data-dependent membership in nodes.
        self.validator.validate(self.plan)
        with self.assertRaises(ContractError) as caught:
            _serialize_plan(self.plan, self.request, _mock_provenance(self.plan), mock=True)
        self.assertTrue(any('invalid_edge_endpoint' in issue for issue in caught.exception.issues))

    def test_solution_with_null_citation_is_not_silently_repaired(self):
        graph = self.plan['graphs'][0]
        solution = next(node for node in graph['nodes'] if node['type'] == 'solution')
        solution['evidence_id'] = None
        self.assertFalse(self.validator.is_valid(self.plan))
        before = deepcopy(self.plan)
        with self.assertRaises(ContractError) as caught:
            _serialize_plan(self.plan, self.request, _mock_provenance(self.plan), mock=True)
        self.assertTrue(any('solution' in issue for issue in caught.exception.issues))
        self.assertEqual(self.plan, before)

    def test_reasoning_nodes_cannot_take_evidence_citations(self):
        self.plan['graphs'][0]['nodes'][0]['evidence_id'] = self.request['evidence_handling']['graph_eligible_evidence_ids'][0]
        self.assertFalse(self.validator.is_valid(self.plan))
        with self.assertRaises(ContractError):
            _serialize_plan(self.plan, self.request, _mock_provenance(self.plan), mock=True)

    def test_empty_catalogue_has_no_solution_alternative(self):
        # Exercise the builder's empty-catalogue branch; request admission remains
        # a separate check of the caller's actual records and partition.
        request = deepcopy(self.request)
        request['evidence_handling']['graph_eligible_evidence_ids'] = []
        schema = build_plan_schema(request)
        validator = Draft202012Validator(schema)
        no_solutions = model_plan(request)
        validator.validate(no_solutions)
        no_solutions['graphs'][0]['nodes'][-1]['type'] = 'solution'
        self.assertFalse(validator.is_valid(no_solutions))

    def test_physical_claim_flags_follow_node_types(self):
        self.plan['graphs'][0]['nodes'][0]['physical_claim'] = False
        self.assertFalse(self.validator.is_valid(self.plan))

    def test_all_r_response_fails_schema_and_authoritative_prose_check(self):
        self.plan['summary'] = 'R'
        self.plan['limitations'] = ['R']
        for graph in self.plan['graphs']:
            for node in graph['nodes']:
                node['statement'] = 'R'
        self.assertFalse(self.validator.is_valid(self.plan))
        with self.assertRaises(ContractError) as caught:
            validate_plan_prose(self.plan)
        self.assertTrue(any('plan/summary' in issue for issue in caught.exception.issues))
        self.assertTrue(any('/statement' in issue for issue in caught.exception.issues))

    def test_degenerate_long_text_is_not_accepted_merely_by_length(self):
        self.plan['summary'] = 'R' * 20
        self.validator.validate(self.plan)
        with self.assertRaises(ContractError):
            validate_plan_prose(self.plan)

    def test_limitation_uniqueness_remains_authoritative(self):
        self.plan['limitations'] *= 2
        self.validator.validate(self.plan)
        with self.assertRaises(ContractError) as caught:
            validate_plan_prose(self.plan)
        self.assertIn('plan_duplicate_limitations', caught.exception.issues)


if __name__ == '__main__':
    unittest.main()
