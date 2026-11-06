"""Configurable software inputs; no source replay, inference or safety results."""
from copy import deepcopy
import unittest

from evaluation.r1_v4.configuration import validate_configuration
from evaluation.r1_v4.provenance import digest
from drafter.request_profiles import build_supplied_request, validate_supplied_request
from drafter.validation import ContractError, ROOT, read_json, validate_request


def registry_input(*, objects=None, records=True):
    fixture = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
    config = deepcopy(fixture['requirement_configuration'])
    if objects is not None:
        surface = next(iter(config['object_surface_mapping'].values()))
        config['protected_objects'] = list(objects)
        config['object_surface_mapping'] = {obj: list(surface) for obj in objects}
    return build_supplied_request(
        request_id='supplied-registry-test', requirement_configuration=config,
        target_execution=fixture['target_execution'], monitoring_scope=fixture['monitoring_scope'],
        registry_records=fixture['evidence_package']['records'] if records else [], test_fixture=True)


class ConfigurableInputTests(unittest.TestCase):
    def test_valid_four_object_configuration_is_not_limited_to_archive(self):
        fixture = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        roster = [obj for obj in fixture['requirement_configuration']['protected_objects'] if obj != 'butter_1']
        request = registry_input(objects=roster)
        self.assertEqual(validate_configuration(request['requirement_configuration']), [])
        self.assertEqual(validate_supplied_request(request)['contract_status'], 'valid_supplied_input')
        self.assertEqual(validate_request(request)['contract_status'], 'valid_supplied_input')

    def test_other_object_names_and_empty_evidence_preserve_missing_information(self):
        request = registry_input(objects=['new_object_a', 'new_object_b'], records=False)
        self.assertEqual(request['retrieval_context']['missing_objects'], ['new_object_a', 'new_object_b'])
        self.assertEqual(len(request['retrieval_context']['gaps']), 2)
        self.assertFalse(request['safety_claim_verified'])
        self.assertEqual(validate_supplied_request(request)['graph_eligible_records'], 0)

    def test_original_records_and_configuration_are_not_modified_by_builder(self):
        fixture = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        before = deepcopy(fixture)
        request = build_supplied_request(
            request_id='unchanged', requirement_configuration=fixture['requirement_configuration'],
            target_execution=fixture['target_execution'], monitoring_scope=fixture['monitoring_scope'],
            registry_records=fixture['evidence_package']['records'], test_fixture=True)
        self.assertEqual(fixture, before)
        self.assertEqual(request['evidence_package'], fixture['evidence_package'])
        self.assertEqual(request['requirement_configuration'], fixture['requirement_configuration'])

    def test_missing_checkpoint_is_clear_validation_error(self):
        request = registry_input()
        del request['requirement_configuration']['benchmark']['policy_checkpoint']
        request['requirement_configuration_sha256'] = digest(request['requirement_configuration'])
        request['input_provenance']['configuration_sha256'] = request['requirement_configuration_sha256']
        with self.assertRaisesRegex(ContractError, 'checkpoint_required'):
            validate_supplied_request(request)

    def test_record_for_other_execution_is_rejected(self):
        request = registry_input()
        record = request['evidence_package']['records'][0]
        record['execution_id'] = 'another-execution'
        record['id'] = 'ev:' + digest({k: v for k, v in record.items() if k != 'id'})
        request['evidence_package_sha256'] = digest(request['evidence_package'])
        request['input_provenance']['evidence_package_sha256'] = request['evidence_package_sha256']
        with self.assertRaisesRegex(ContractError, 'record_target_scope'):
            validate_supplied_request(request)

    def test_dropped_source_bindings_cannot_pass_digest_checks(self):
        request = registry_input()
        request['evidence_package']['records'].pop()
        with self.assertRaisesRegex(ContractError, 'evidence_package_sha256_mismatch'):
            validate_supplied_request(request)

    def test_missing_gap_is_not_treated_as_complete_coverage(self):
        request = registry_input(records=False)
        request['retrieval_context']['gaps'].pop()
        with self.assertRaisesRegex(ContractError, 'known_gap_inventory_mismatch'):
            validate_supplied_request(request)

    def test_clock_mapping_is_explicit_and_never_guessed(self):
        request = registry_input()
        request['monitoring_scope']['clock'] = 'simulator_time'
        with self.assertRaisesRegex(ContractError, 'unsupported_drafter_clock_or_axis'):
            validate_supplied_request(request)

    def test_malformed_builder_inputs_return_contract_errors(self):
        fixture = read_json(ROOT / 'drafter/cases/scenario_a.request.json')
        kwargs = dict(request_id='malformed', requirement_configuration=fixture['requirement_configuration'],
                      target_execution=fixture['target_execution'], monitoring_scope=fixture['monitoring_scope'],
                      test_fixture=True)
        for key, value in [('requirement_configuration', []), ('monitoring_scope', None),
                           ('registry_records', None), ('limitations', [{}])]:
            with self.subTest(key=key), self.assertRaises(ContractError):
                build_supplied_request(**{**kwargs, key: value})

    def test_fixture_label_cannot_be_removed_from_analytical_input(self):
        request = registry_input()
        request['test_fixture'] = False
        with self.assertRaisesRegex(ContractError, 'analytical_fixture_requires_test_fixture_label'):
            validate_supplied_request(request)

    def test_archive_mode_cannot_silently_use_supplied_provenance(self):
        request = registry_input()
        del request['input_profile']
        with self.assertRaises(ContractError):
            validate_request(request)


if __name__ == '__main__':
    unittest.main()
