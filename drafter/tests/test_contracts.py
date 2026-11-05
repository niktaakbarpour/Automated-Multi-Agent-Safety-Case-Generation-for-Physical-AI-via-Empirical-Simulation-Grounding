"""Offline contract checks, not model or robot-safety evaluation."""
from copy import deepcopy
import subprocess
import sys
import unittest

from evaluation.r1_v4.provenance import digest, strict_loads
from drafter.validation import (
    ContractError, ROOT, read_json, schema_validator, validate_request, validate_argument,
)

FIXTURE = ROOT / 'drafter/cases/scenario_a.request.json'


class RequestContractTests(unittest.TestCase):
    def setUp(self):
        self.request = read_json(FIXTURE)

    def assert_rejected(self, value, diagnostic):
        with self.assertRaises(ContractError) as context:
            validate_request(value)
        self.assertTrue(any(diagnostic in issue for issue in context.exception.issues), context.exception.issues)

    def test_archived_metadata_passes_real_record_contract_without_source_replay(self):
        report = validate_request(self.request)
        self.assertEqual(report['contract_status'], 'valid_fixture')
        self.assertEqual(report['records'], 18)
        self.assertEqual(report['graph_eligible_records'], 10)
        self.assertEqual(report['source_replay'], 'not_performed')
        self.assertFalse(report['safety_claim_verified'])
        self.assertFalse(report['model_called'])

    def test_required_context_is_enforced(self):
        del self.request['target_execution']
        self.assert_rejected(self.request, 'schema:')

    def test_unexpected_fields_cannot_hide_in_a_request(self):
        self.request['authority'] = 'validated_checker'
        self.assert_rejected(self.request, 'schema:')

    def test_empirical_promotion_is_rejected(self):
        self.request['empirical_admission_enabled'] = True
        self.assert_rejected(self.request, 'schema:')

    def test_unavailable_checker_cannot_be_replaced_by_a_flag(self):
        self.request['checker_context']['assessments'] = [{'authority': 'validated_checker'}]
        self.assert_rejected(self.request, 'schema:')

    def test_wrong_execution_is_rejected_even_when_configuration_digest_is_updated(self):
        self.request['target_execution']['execution_id'] = 'OTHER-EXECUTION'
        self.request['requirement_configuration']['execution_id'] = 'OTHER-EXECUTION'
        self.request['requirement_configuration_sha256'] = digest(self.request['requirement_configuration'])
        self.assert_rejected(self.request, 'record_target_scope:')

    def test_roster_cannot_be_reduced_to_only_the_observed_object(self):
        config = self.request['requirement_configuration']
        config['protected_objects'] = ['cream_cheese_1']
        config['object_surface_mapping'] = {'cream_cheese_1': ['living_room_table']}
        self.request['requirement_configuration_sha256'] = digest(config)
        self.assert_rejected(self.request, 'configuration_derivation_mismatch')

    def test_record_changes_cannot_be_hidden_by_rehashing_the_export(self):
        record = self.request['evidence_package']['records'][0]
        record['source_path'] = '/synthetic/pretend-source.h5'
        record['id'] = 'ev:' + digest({k: v for k, v in record.items() if k != 'id'})
        self.request['evidence_package_sha256'] = digest(self.request['evidence_package'])
        self.assert_rejected(self.request, 'source outside approved research scope')

    def test_context_record_cannot_be_promoted_to_in_window_solution_inventory(self):
        handling = self.request['evidence_handling']
        handling['graph_eligible_evidence_ids'].append(handling['context_only_evidence_ids'].pop(0))
        self.assert_rejected(self.request, 'evidence_partition_mismatch')

    def test_wrong_clock_is_rejected(self):
        self.request['monitoring_scope']['clock'] = 'unverified_camera_clock'
        self.assert_rejected(self.request, 'unsupported_fixture_clock_or_axis')

    def test_missing_objects_cannot_be_hidden(self):
        self.request['retrieval_context']['missing_objects'] = []
        self.assert_rejected(self.request, 'missing_object_inventory_mismatch')

    def test_known_saved_frame_gaps_cannot_be_removed(self):
        self.request['retrieval_context']['gaps'] = []
        self.assert_rejected(self.request, 'known_gap_inventory_mismatch')

    def test_saved_frame_gaps_cannot_use_fractional_indices(self):
        self.request['retrieval_context']['gaps'][0]['interval'] = [10.1, 10.2]
        self.assert_rejected(self.request, 'saved_frame_gap_requires_integer_endpoints')

    def test_unknown_variant_identity_cannot_be_invented(self):
        self.request['target_execution']['variant_id'] = 'made-up-variant'
        self.assert_rejected(self.request, 'archived_variant_identity_unavailable')

    def test_arbitrary_source_paths_are_not_opened(self):
        self.request['input_provenance']['source_artifacts'][0]['path'] = '/private/not-a-source'
        self.assert_rejected(self.request, 'source_artifact_inventory_mismatch')

    def test_real_source_verification_cannot_be_asserted(self):
        self.request['evidence_handling']['source_replay'] = 'verified'
        self.assert_rejected(self.request, 'schema:')

    def test_model_output_is_not_part_of_input(self):
        self.request['argument_bundle'] = {'graphs': []}
        self.assert_rejected(self.request, 'schema:')

    def test_duplicate_keys_and_nonfinite_json_are_rejected(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                strict_loads(value)

    def test_future_output_schema_and_original_gsn_reference_resolve_offline(self):
        validator = schema_validator('draft_argument.schema.json')
        self.assertTrue(list(validator.iter_errors({})))

    def test_fixture_builder_is_reproducible(self):
        subprocess.run([sys.executable, str(ROOT / 'drafter/tools/build_scenario_a.py'), '--check'],
                       cwd=ROOT, check=True, capture_output=True)

    def test_validation_cli_has_explicit_success_and_rejection_exit_codes(self):
        success = subprocess.run([sys.executable, '-m', 'drafter', '--validate-request', str(FIXTURE)],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(success.returncode, 0, success.stderr + success.stdout)
        self.assertFalse(strict_loads(success.stdout)['model_called'])
        failure = subprocess.run([sys.executable, '-m', 'drafter', '--validate-request', str(FIXTURE) + '.missing'],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(failure.returncode, 1)
        self.assertEqual(strict_loads(failure.stdout)['contract_status'], 'rejected')


class OutputContractTests(unittest.TestCase):
    """In-memory contract probes only; these are not generated model results."""
    def setUp(self):
        self.request = read_json(FIXTURE)
        config = self.request['requirement_configuration']
        target = self.request['target_execution']
        graphs = []
        for object_id in config['protected_objects']:
            node = {'id': 'G:' + object_id, 'type': 'goal',
                    'statement': 'R1 physical conclusion remains unresolved.',
                    'scope': {'requirement_id': 'R1', 'requirement_version': '2.0.0',
                              'execution_id': target['execution_id'], 'object_id': object_id,
                              'domain': 'frame', 'clock': 'saved_frame_index', 'interval': [10, 12]},
                    'provenance': {'purpose': 'in_memory_contract_probe_no_model_executed'},
                    'validation_status': 'unresolved', 'origin': 'unresolved_conclusion',
                    'evidence_id': None, 'physical_claim': True}
            graphs.append({'object_id': object_id, 'graph': {'schema_version': '1.0.0',
                           'nodes': [node], 'edges': [], 'empirical_admission_enabled': False}})
        self.argument = {
            'schema_version': 'draft-argument/0.1.0', 'request_id': self.request['request_id'],
            'test_fixture': True, 'request_sha256': digest(self.request),
            'requirement_configuration_sha256': self.request['requirement_configuration_sha256'],
            'evidence_package_sha256': self.request['evidence_package_sha256'],
            'generation_status': 'accepted',
            'argument_bundle': {'execution_id': target['execution_id'],
                                'protected_objects': list(config['protected_objects']), 'graphs': graphs,
                                'execution_conclusion': {'claimed_outcome': 'insufficient_information',
                                                        'statement': 'Unresolved contract probe.',
                                                        'object_outcomes': {o: 'insufficient_information' for o in config['protected_objects']}}},
            'summary': 'Test-only object, not an executed Drafter result.',
            'limitations': ['No model was executed; all run fields below are schema test values.'],
            'diagnostics': [],
            'validation': {**{name: 'passed' for name in ('input_schema', 'input_semantics', 'output_schema', 'graph_semantics', 'evidence_references')},
                           'physical_sufficiency': 'not_assessed'},
            'generation_provenance': {'backend': 'local_llm', 'model_id': 'TEST_VALUE_NOT_EXECUTED',
                                     'model_revision': None, 'prompt_version': 'TEST_VALUE_NOT_EXECUTED',
                                     'prompt_sha256': '0' * 64, 'run_id': 'TEST_VALUE_NOT_EXECUTED', 'raw_output_sha256': '0' * 64},
            'empirical_admission_enabled': False, 'safety_claim_verified': False,
        }

    def assert_rejected(self, diagnostic):
        with self.assertRaises(ContractError) as context:
            validate_argument(self.argument, self.request)
        self.assertTrue(any(diagnostic in issue for issue in context.exception.issues), context.exception.issues)

    def test_supplied_shape_is_distinct_from_execution_or_safety_verification(self):
        report = validate_argument(self.argument, self.request)
        self.assertEqual(report['contract_status'], 'valid_output_contract')
        self.assertFalse(report['safety_claim_verified'])
        self.assertFalse(report['model_called'])

    def test_missing_object_graph_is_rejected(self):
        self.argument['argument_bundle']['graphs'].pop()
        self.assert_rejected('argument_graph_roster_mismatch')

    def test_missing_object_outcome_is_rejected(self):
        self.argument['argument_bundle']['execution_conclusion']['object_outcomes'].pop('milk_1')
        self.assert_rejected('argument_outcome_roster_mismatch')

    def test_actual_gsn_validator_rejects_missing_edge_target(self):
        graph = self.argument['argument_bundle']['graphs'][0]['graph']
        graph['edges'].append({'source': graph['nodes'][0]['id'], 'target': 'MISSING', 'type': 'supported_by'})
        self.assert_rejected('invalid edge endpoint')

    def test_cross_object_node_scope_is_rejected(self):
        self.argument['argument_bundle']['graphs'][0]['graph']['nodes'][0]['scope']['object_id'] = 'milk_1'
        self.assert_rejected('argument_node_scope:')

    def test_frame_graph_nodes_cannot_use_fractional_indices(self):
        self.argument['argument_bundle']['graphs'][0]['graph']['nodes'][0]['scope']['interval'] = [10.1, 11.2]
        self.assert_rejected('argument_frame_indices_require_integers:')

    def test_promoted_physical_goal_is_rejected(self):
        self.argument['argument_bundle']['graphs'][0]['graph']['nodes'][0]['validation_status'] = 'proposed'
        self.assert_rejected('schema:')

    def test_unbound_input_digest_is_rejected(self):
        self.argument['request_sha256'] = 'f' * 64
        self.assert_rejected('argument_input_binding:request_sha256')

    def test_empty_graphs_cannot_be_accepted(self):
        self.argument['argument_bundle']['graphs'] = []
        self.assert_rejected('schema:')


if __name__ == '__main__':
    unittest.main()
