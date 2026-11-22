"""Regression tests for CPU input checks without reviewer keys or model calls."""

from copy import deepcopy
from hashlib import sha256
import unittest

from evaluation.m4_20261127.rq3.gsn_inputs.build_inputs import load_parents
from evaluation.m4_20261127.rq3.gsn_inputs.validate_controlled_inputs import (
    Case,
    DEMONSTRATIONS,
    build_receipt,
    expected_request,
    target_node,
    validate_case,
)


class ControlledInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents = load_parents()
        cls.cases = {case.case_id: case for case in DEMONSTRATIONS}

    def setUp(self):
        self.parents = deepcopy(self.parents)

    def example(self, case_id):
        case = self.cases[case_id]
        parent = self.parents[case.parent_id]
        request_id = 'test:' + case_id
        request = expected_request(case, parent, request_id)
        return case, parent, request, request_id

    def test_semantic_controls_pass_input_checks_and_dangling_control_does_not(self):
        receipt = build_receipt()
        self.assertEqual(receipt['model_calls'], 0)
        self.assertFalse(receipt['independent_scoring_eligible'])
        self.assertFalse(receipt['label_audit_performed'])
        self.assertEqual(receipt['counts'], {
            'clean_control': 2, 'semantic_mutation': 3, 'pre_model_validation_control': 1,
        })
        rows = {row['case_id']: row for row in receipt['cases']}
        for case_id in ('P1-guarantee', 'P2-citation', 'P2-narrower'):
            with self.subTest(case=case_id):
                self.assertTrue(rows[case_id]['shared_gsn_valid'])
                self.assertTrue(rows[case_id]['critic_input_valid'])
                self.assertEqual(rows[case_id]['pre_model_validation_codes'], [])
        self.assertFalse(rows['P2-dangling']['shared_gsn_valid'])
        self.assertFalse(rows['P2-dangling']['critic_input_valid'])
        self.assertEqual(rows['P2-dangling']['pre_model_validation_codes'], ['EV-MISSING'])

    def test_scope_mutation_cannot_change_the_structured_monitoring_interval(self):
        case, parent, request, request_id = self.example('P2-narrower')
        request['evaluation_context']['monitored_interval']['interval'][1] = 60
        with self.assertRaisesRegex(ValueError, '/evaluation_context/monitored_interval/interval/1'):
            validate_case(case, parent, request, request_id)

    def test_citation_mutation_cannot_hide_an_edit_to_an_unused_record(self):
        case, parent, request, request_id = self.example('P2-citation')
        cited_id = target_node(request, case)['evidence_id']
        untouched = next(record for record in request['evidence_package']['records'] if record['id'] != cited_id)
        untouched['limitations'].append('Collateral edit outside the intended link.')
        with self.assertRaisesRegex(ValueError, '/evidence_package/records/'):
            validate_case(case, parent, request, request_id)

    def test_correct_citation_id_with_stale_source_binding_is_rejected(self):
        case, parent, request, request_id = self.example('P2-citation')
        target_node(request, case)['provenance'] = deepcopy(target_node(parent, case)['provenance'])
        with self.assertRaisesRegex(ValueError, '/provenance/'):
            validate_case(case, parent, request, request_id)

    def test_declared_text_only_edit_rejects_different_prose_at_target(self):
        sample, parent, request, request_id = self.example('P1-guarantee')
        declared = Case(sample.case_id, sample.operator, sample.object_id, sample.node_id,
                        sample.target_type, sha256(sample.statement.encode()).hexdigest())
        target_node(request, sample)['statement'] = 'A different nonempty statement.'
        with self.assertRaisesRegex(ValueError, 'statement differs from the pinned engineering edit'):
            validate_case(declared, parent, request, request_id)


if __name__ == '__main__':
    unittest.main()
