"""Synthetic transport tests, not actual inference or measurements."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from critic.critic import review
from drafter.generation import generate_argument
from drafter.llm import FrozenLocalModelConfig, ModelDiscoveryResult
from drafter.tests.test_generation import model_plan, reply
from drafter.tests.test_input_profiles import registry_input
from drafter.tests.test_llm import configuration, MODEL
from drafter.validation import ContractError
from integration.handoff import build_critic_request, ORIGINAL_CONTEXT_PREFIX


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.q = registry_input(records=False)
        cfg = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))
        with patch('drafter.generation.LocalModelClient') as cls:
            cls.return_value.discover_models.return_value = ModelDiscoveryResult(status='ok', configured_model_available=True, model_ids=(MODEL,))
            cls.return_value.complete.return_value = reply(model_plan(self.q))
            self.r = generate_argument(self.q, cfg)
        self.assertEqual(self.r['status'], 'accepted')

    def test_unchanged_graphs_scope_and_deterministic_input_validation(self):
        before = deepcopy((self.q, self.r))
        req, meta = build_critic_request(self.q, self.r)
        self.assertEqual(req['argument_bundle'], self.r['argument']['argument_bundle'])
        self.assertEqual(meta['original_argument_bundle_sha256'], meta['critic_argument_bundle_sha256'])
        self.assertEqual(req['evaluation_context']['protected_objects'], self.q['requirement_configuration']['protected_objects'])
        self.assertEqual(req['evaluation_context']['monitored_interval']['interval'], self.q['monitoring_scope']['interval'])
        self.assertTrue(review(req)['input_valid'])
        self.assertEqual(before, (self.q, self.r))

    def test_lossless_untyped_gaps_without_invented_measurement_type(self):
        req, meta = build_critic_request(self.q, self.r)
        encoded = [v[len(ORIGINAL_CONTEXT_PREFIX):] for v in req['retrieval_context']['limitations'] if v.startswith(ORIGINAL_CONTEXT_PREFIX)]
        self.assertEqual(json.loads(encoded[0]), self.q['retrieval_context'])
        self.assertFalse(req['retrieval_context']['gaps'])
        self.assertEqual(meta['drafter_request'], self.q)
        self.assertFalse(req['retrieval_context']['complete_within_requested_scope'])

    def test_empty_checker_and_registry_remain_empty(self):
        req, _ = build_critic_request(self.q, self.r)
        self.assertEqual(req['checker_assessments'], [])
        self.assertEqual(req['evidence_package']['records'], [])
        self.assertIn(self.r['argument']['reasoning_review']['warning'], req['retrieval_context']['limitations'])

    def test_rejected_generation_cannot_be_handed_off(self):
        self.r['status'] = 'rejected'
        with self.assertRaises(ContractError):build_critic_request(self.q, self.r)

    def test_changed_request_and_configuration_fail_closed(self):
        self.q['target_execution']['execution_id'] = 'wrong-execution'
        with self.assertRaises(ContractError):build_critic_request(self.q, self.r)

    def test_tampered_graph_fails_drafter_validation(self):
        self.r['argument']['argument_bundle']['graphs'][0]['graph']['edges'][0]['target'] = 'absent:G1'
        with self.assertRaises(ContractError):build_critic_request(self.q, self.r)

    def test_returned_objects_are_independent_snapshots(self):
        req, meta = build_critic_request(self.q, self.r)
        req['argument_bundle']['graphs'][0]['graph']['nodes'][0]['statement'] = 'changed'
        self.assertNotEqual(req['argument_bundle'], self.r['argument']['argument_bundle'])
        self.assertEqual(meta['drafter_argument'], self.r['argument'])

    def test_wrong_object_roster_fails_without_reordering(self):
        self.r['argument']['argument_bundle']['graphs'].reverse()
        with self.assertRaises(ContractError):build_critic_request(self.q, self.r)

    def test_exact_structured_pair_and_classification_are_preserved(self):
        from drafter.tests.test_phase5_adapter import request_with
        q = request_with()  # Explicit synthetic PARTIAL fixture, never real retrieval.
        cfg = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))
        with patch('drafter.generation.LocalModelClient') as cls:
            cls.return_value.discover_models.return_value = ModelDiscoveryResult(status='ok', configured_model_available=True, model_ids=(MODEL,))
            cls.return_value.complete.return_value = reply(model_plan(q))
            r = generate_argument(q, cfg)
        self.assertEqual(r['status'], 'accepted')
        req, meta = build_critic_request(q, r)
        self.assertEqual(req['structured_evidence'], q['structured_evidence'])
        self.assertEqual(req['test_fixture'], q['test_fixture'])
        self.assertEqual(meta['drafter_request'], q)
        self.assertTrue(review(req)['input_valid'])
