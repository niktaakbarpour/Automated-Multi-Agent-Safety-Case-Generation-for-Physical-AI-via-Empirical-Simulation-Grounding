"""Transport tests for the original R1 v3 request with a scripted Drafter reply."""
from copy import deepcopy
from io import BytesIO
import json
import unittest
from unittest.mock import patch

from critic.critic import review
from critic.llm import ScriptedLLM
from drafter.generation import generate_argument
from drafter.llm import FrozenLocalModelConfig
from drafter.r1v3_profile import INSUFFICIENT, build_request
from drafter.tests.test_generation import reply
from drafter.tests.test_llm import MODEL, configuration
from drafter.tests.test_r1v3_generation import model_plan
from drafter.tests.test_r1v3_profile import load_package
from drafter.validation import ContractError
from evaluation.r1_v4.provenance import canonical, digest
from integration.handoff import build_critic_request


class R1V3HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drafter_request = build_request(load_package(), request_id='test-r1v3-critic-handoff')
        config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))
        model_list = {'data': [{'id': MODEL}]}
        model_reply = reply(model_plan(cls.drafter_request)).raw_response
        with patch('drafter.llm.build_opener') as build_opener:
            build_opener.return_value.open.side_effect = [
                BytesIO(canonical(model_list)),
                BytesIO(canonical(model_reply)),
            ]
            report = generate_argument(cls.drafter_request, config)
        if report['status'] != 'accepted':
            raise AssertionError(report['diagnostics'])
        cls.run_report = json.loads(canonical(report))

    def test_preserves_the_versioned_request_and_accepted_generation(self):
        original_request = canonical(self.drafter_request)
        original_report = canonical(self.run_report)
        critic_request, sidecar = build_critic_request(self.drafter_request, self.run_report)

        self.assertEqual(critic_request['schema_version'], 'critic-request/r1v3/0.1.0')
        self.assertEqual(critic_request['request_id'], self.run_report['run_id'] + ':critic')
        self.assertEqual(canonical(critic_request['drafter_request']), original_request)
        self.assertEqual(canonical(critic_request['generation_report']), original_report)
        self.assertEqual(canonical(self.drafter_request), original_request)
        self.assertEqual(canonical(self.run_report), original_report)
        self.assertEqual(critic_request['checker_assessments'], [])
        bundle_hash = digest(self.run_report['argument']['argument_bundle'])
        self.assertEqual(sidecar['original_argument_bundle_sha256'], bundle_hash)
        self.assertEqual(sidecar['critic_argument_bundle_sha256'], bundle_hash)
        self.assertEqual(sidecar['generation_report_sha256'], digest(self.run_report))
        self.assertEqual(sidecar['critic_request_sha256'], digest(critic_request))

    def test_returned_envelope_does_not_alias_the_inputs(self):
        critic_request, _ = build_critic_request(self.drafter_request, self.run_report)
        critic_request['drafter_request']['evidence']['record_ids'].clear()
        critic_request['generation_report']['argument']['argument_bundle']['graphs'].clear()
        self.assertTrue(self.drafter_request['evidence']['record_ids'])
        self.assertTrue(self.run_report['argument']['argument_bundle']['graphs'])

    def test_public_critic_keeps_original_execution_unresolved(self):
        critic_request, sidecar = build_critic_request(self.drafter_request, self.run_report)
        before = canonical(critic_request)
        report = review(critic_request)

        self.assertEqual(report['schema_version'], 'critic-report/r1v3/0.1.0')
        self.assertEqual(report['review_status'], 'completed')
        self.assertTrue(report['input_valid'])
        self.assertFalse(report['llm']['called'])
        self.assertFalse(report['safety_claim_verified'])
        self.assertEqual(report['checker_admission'], [])
        self.assertEqual(report['reasoning_review'], self.run_report['argument']['reasoning_review'])
        self.assertEqual(report['summary']['accepted_execution_outcome'], INSUFFICIENT)
        self.assertEqual(report['provenance']['critic_request_sha256'], sidecar['critic_request_sha256'])
        self.assertEqual(report['drafter_evidence_gaps'], self.drafter_request['evidence_gaps'])
        expected = dict.fromkeys(self.drafter_request['requirement_configuration']['protected_objects'], None)
        self.assertEqual({row['object_id']: row['verified_checker_outcome'] for row in report['object_reviews']},
                         expected)
        self.assertEqual(canonical(critic_request), before)

    def test_public_critic_does_not_call_requested_backend(self):
        critic_request, _ = build_critic_request(self.drafter_request, self.run_report)
        backend = ScriptedLLM('{"findings": []}')
        with patch.object(backend, 'complete') as complete:
            report = review(critic_request, backend)
        complete.assert_not_called()
        self.assertTrue(report['input_valid'])
        self.assertEqual(report['review_status'], 'completed_llm_failed')
        self.assertFalse(report['llm']['called'])
        self.assertEqual(report['summary']['accepted_execution_outcome'], INSUFFICIENT)

    def test_public_critic_rejects_tampered_original_without_calling_backend(self):
        critic_request, _ = build_critic_request(self.drafter_request, self.run_report)
        critic_request['drafter_request']['target_execution']['execution_id'] = 'different-execution'
        backend = ScriptedLLM('{"findings": []}')
        with patch.object(backend, 'complete') as complete:
            report = review(critic_request, backend)
        complete.assert_not_called()
        self.assertEqual(report['review_status'], 'rejected_invalid_input')
        self.assertFalse(report['input_valid'])
        self.assertFalse(report['llm']['called'])
        self.assertEqual(report['checker_admission'], [])

    def test_rejects_a_different_valid_request(self):
        changed = build_request(load_package(), request_id='different-r1v3-critic-handoff')
        with self.assertRaises(ContractError):
            build_critic_request(changed, self.run_report)

    def test_rejects_a_malformed_nested_source_package(self):
        changed = deepcopy(self.drafter_request)
        changed['source_package']['execution'] = []
        changed['source_package_sha256'] = digest(changed['source_package'])
        with self.assertRaises(ContractError):
            build_critic_request(changed, self.run_report)
        request, _ = build_critic_request(self.drafter_request, self.run_report)
        request['drafter_request'] = changed
        result = review(request)
        self.assertEqual(result['schema_version'], 'critic-report/r1v3/0.1.0')
        self.assertEqual(result['review_status'], 'rejected_invalid_input')

    def test_rejection_is_utf8_serializable_with_a_malformed_request_id(self):
        request, _ = build_critic_request(self.drafter_request, self.run_report)
        request['request_id'] = chr(0xD800)
        result = review(request)
        self.assertEqual(result['review_status'], 'rejected_invalid_input')
        self.assertEqual(result['request_id'], '')
        canonical(result)

    def test_rejects_a_run_id_that_disagrees_with_argument_provenance(self):
        changed = deepcopy(self.run_report)
        changed['run_id'] = 'different-run'
        with self.assertRaises(ContractError):
            build_critic_request(self.drafter_request, changed)

    def test_rejects_tampered_prompt_trace(self):
        changed = deepcopy(self.run_report)
        changed['trace']['messages'][0]['content'] += '\nExtra instruction.'
        with self.assertRaises(ContractError):
            build_critic_request(self.drafter_request, changed)

    def test_rejects_evaluation_references_in_saved_trace(self):
        markers = {
            'human_reference': {'synthetic_marker': True},
            'HUMAN_REFERENCE_EVALUATION_ONLY.json': {'synthetic_marker': True},
            'metadata': {'path': '/fixture/HUMAN_REFERENCE_EVALUATION_ONLY.json'},
        }
        for key, value in markers.items():
            with self.subTest(key=key):
                changed = deepcopy(self.run_report)
                changed['trace']['completion']['raw_response'][key] = value
                with self.assertRaisesRegex(ContractError, 'human_reference_label_present'):
                    build_critic_request(self.drafter_request, changed)

                request, _ = build_critic_request(self.drafter_request, self.run_report)
                request['generation_report'] = changed
                result = review(request)
                self.assertEqual(result['review_status'], 'rejected_invalid_input')
                self.assertFalse(result['llm']['called'])

    def test_rejects_evaluation_reference_in_checker_pair(self):
        pairs = [{
            'request': {'prediction': {'artifact': {'path': '/fixture/HUMAN_REFERENCE_EVALUATION_ONLY.json'}}},
            'assessment': {},
        }]
        with self.assertRaisesRegex(ContractError, 'human_reference_label_present'):
            build_critic_request(self.drafter_request, self.run_report, checker_assessments=pairs)

    def test_rejects_labels_appended_to_the_source_exclusion_note(self):
        changed = deepcopy(self.drafter_request)
        package = changed['source_package']
        package['evidence_semantics']['human_reference'] += '\nSynthetic marker.'
        changed['source_package_sha256'] = digest(package)
        with self.assertRaisesRegex(ContractError, 'human_reference_label_present'):
            build_critic_request(changed, self.run_report)

    def test_rejects_completion_detached_from_the_saved_reply(self):
        changed = deepcopy(self.run_report)
        message = changed['trace']['completion']['raw_response']['choices'][0]['message']
        message['content'] = '{"graphs": []}'
        with self.assertRaisesRegex(ContractError, 'handoff_generation_raw_output_mismatch'):
            build_critic_request(self.drafter_request, changed)

    def test_rejects_a_graph_edit_that_disagrees_with_the_saved_completion(self):
        changed = deepcopy(self.run_report)
        graph = changed['argument']['argument_bundle']['graphs'][0]['graph']
        graph['nodes'][0]['statement'] = 'A different proposal for the same protected object.'
        with self.assertRaises(ContractError):
            build_critic_request(self.drafter_request, changed)

    def test_rejects_a_run_without_accepted_status(self):
        changed = deepcopy(self.run_report)
        changed['status'] = 'rejected'
        with self.assertRaises(ContractError):
            build_critic_request(self.drafter_request, changed)
