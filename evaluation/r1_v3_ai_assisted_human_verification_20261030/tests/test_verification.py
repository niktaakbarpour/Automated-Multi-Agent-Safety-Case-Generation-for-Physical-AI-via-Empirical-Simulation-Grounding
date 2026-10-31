"""Integrity and approval-boundary tests; synthetic confirmations never leave temp dirs."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ai_assisted_verification', ROOT / 'verification.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='trustworthy-verification-test-')
        self.root = Path(self.temp.name) / 'copy'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__'))

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_transfer_and_all_twenty_cases(self):
        result = v.validate(self.root)
        self.assertTrue(result['passed'], result['errors'])
        self.assertEqual(result['source_files_verified'], 66)
        self.assertEqual(result['remote_files_inventoried'], 718)
        self.assertEqual({r['case_id'] for r in v.reference(self.root)}, set(v.case_map()))

    def test_source_annotation_tamper_detected(self):
        path = v.source(1, self.root) / 'annotations/events.csv'
        path.write_bytes(path.read_bytes().replace(b'Cause of upward impulse', b'Invented upward impulse', 1))
        self.assertFalse(v.validate(self.root)['passed'])

    def test_omitted_uncertainty_detected(self):
        path = v.source(2, self.root) / 'annotations/uncertainty_requests.csv'
        fields, rows = v.read_csv(path)
        v.write_csv(path, fields, rows[1:])
        self.assertFalse(v.validate(self.root)['passed'])

    def test_missing_case_or_changed_outcome_detected(self):
        path = self.root / 'adjudicated_reference.csv'
        fields, rows = v.read_csv(path)
        v.write_csv(path, fields, rows[:-1])
        self.assertFalse(v.validate(self.root)['passed'])

    def test_nv12_exact_rationale_and_uncertainties_retained(self):
        nv = v.load(self.root / 'human_evaluator_3_adjudication/NV12.json')
        dd = v.data(self.root)
        self.assertEqual(nv['selected_ai_requirement_row'], v.one(dd[2]['requirement_interpretation'], 'NV12'))
        self.assertEqual(nv['selected_outcome'], 'no_violation_observed_within_reviewed_coverage')
        self.assertEqual(nv['both_sources_uncertainties']['2'], v.by_case(dd[2]['uncertainty_requests'], 'NV12'))
        self.assertIsNone(nv['human_identity'])
        self.assertIsNone(nv['human_review_date'])

    def test_every_field_and_event_accounted_for(self):
        comparisons = v.compare(self.root)
        dd = v.data(self.root)
        for case in v.case_map():
            for table in v.TABLES:
                fields = set().union(*(set(r) for n in (1, 2) for r in v.by_case(dd[n][table], case)))
                observed = {r['field'] for r in comparisons if r['case_id'] == case and r['table'] == table}
                self.assertEqual(fields, observed)
        groups = v.event_alignment_candidates(self.root)
        for n in (1, 2):
            flattened = [r['event_id'] for g in groups for r in g['source_rows'][str(n)]]
            self.assertEqual(sorted(flattened), sorted(r['event_id'] for r in dd[n]['events']))
        self.assertTrue(any(d['case_id'] == 'NV20' and d['field'] == 'end_frame' and not d['exact_equal'] for d in comparisons))

    def test_blank_approval_rejected_before_prediction_access(self):
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            if path.name == 'predictions.json':
                raise AssertionError('Prediction data must not be read')
            return original_open(path, *args, **kwargs)

        with patch.object(Path, 'open', guarded_open):
            with self.assertRaisesRegex(ValueError, 'Missing authorized human approval'):
                v.check_approval(self.root / 'APPROVAL_TEMPLATE.json', self.root)
        self.assertFalse((self.root / 'REFERENCE_SEAL.json').exists())

    def synthetic_declaration(self):
        """TEST ONLY: never an empirical human approval."""
        approval = copy.deepcopy(v.load(self.root / 'APPROVAL_TEMPLATE.json'))
        approval.update(approval_decision='approve', authorized_approver_identity='TEST_APPROVER',
                        approval_date='TEST_DATE', approval_statement='TEST_ONLY',
                        ai_assisted_nonindependent_method_acknowledged=True,
                        unresolved_evidence_limits_accepted=True)
        for n, c in approval['reviewer_confirmations'].items():
            c.update(identity='TEST_HUMAN_' + n, actual_review_date='TEST_DATE',
                     confirmation_statement='TEST_ONLY', user_report_is_accurate=True,
                     human_inspected_evidence_description='TEST_ONLY_UNKNOWN_COVERAGE',
                     ai_explanations_remain_ai_authored=True)
        approval['third_reviewer'].update(identity='TEST_HUMAN_3', actual_adjudication_date='TEST_DATE',
            confirmation_statement='TEST_ONLY', nv12_outcome_selection_confirmed=True)
        return approval

    def test_outcome_acceptance_does_not_clear_other_disagreements(self):
        approval = self.synthetic_declaration()
        path = self.root / 'TEST_ONLY_APPROVAL.json'
        v.save(path, approval)
        with self.assertRaisesRegex(ValueError, 'Unresolved physical/coverage/detail'):
            v.check_approval(path, self.root)

    def test_complete_test_declarations_still_cannot_freeze_or_score(self):
        approval = self.synthetic_declaration()
        approval['discrepancy_resolutions'] = [dict(
            discrepancy_id=f"{d['case_id']}:{d['table']}:{d['field']}",
            decision='retain_both_unscorable', human_reason='TEST_ONLY')
            for d in v.load(self.root / 'discrepancies.json') if d['disposition'] in
            ['unresolved', 'additional_confirmation_required', 'retained_not_semantically_adjudicated']]
        approval['comparison_domain_by_case'] = {c: dict(status='unscorable', reason='TEST_ONLY') for c in v.case_map()}
        path = self.root / 'TEST_ONLY_APPROVAL.json'
        v.save(path, approval)
        result = v.check_approval(path, self.root)
        self.assertTrue(result['declaration_complete'])
        self.assertFalse(result['authenticated_by_software'])
        self.assertFalse(result['scoring_permitted_by_this_tool'])
        self.assertFalse(result['frozen'])
        self.assertFalse((self.root / 'REFERENCE_SEAL.json').exists())

    def test_fake_human_authorship_or_coverage_detected(self):
        path = self.root / 'human_evaluator_1/acceptance.json'
        acceptance = v.load(path)
        acceptance['human_identity'] = 'INVENTED_TEST_IDENTITY'
        acceptance['human_inspected_evidence_coverage'] = 'full_execution'
        v.save(path, acceptance)
        self.assertFalse(v.validate(self.root)['passed'])

    def test_prepare_never_overwrites_existing_human_records(self):
        before = v.sha(self.root / 'adjudicated_reference.csv')
        with self.assertRaises(FileExistsError):
            v.prepare(self.root)
        self.assertEqual(before, v.sha(self.root / 'adjudicated_reference.csv'))


if __name__ == '__main__':
    unittest.main()
