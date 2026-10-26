"""AI proposal checks. Synthetic ledgers are temporary and never human approval."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('complete',ROOT/'ai_tools/complete_adjudication.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PACKAGE=ROOT.parent;OUT=ROOT/'ai_assisted_20261026';PRIVATE=ROOT/'ai_private_20261026'


class CompleteProposal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'evidence_complete_20261026/audit_receipt.json').exists():
            raise unittest.SkipTest('Authorized private measurement audit is required; no evidence is fabricated.')
        cls.rows=m.core.readcsv(OUT/'complete_adjudication_decisions.csv')
        cls.summary=json.loads((OUT/'adjudication_summary.json').read_text())

    def find(self,table,ep,obj,family=None):
        return next(r for r in self.rows if r['table']==table and r['episode']==ep and r['object_id']==obj and (family is None or r['event_family']==family))

    def test_full_verification(self):
        self.assertEqual(m.verify(PACKAGE,OUT)['decisions_pending_human_approval'],90)

    def test_all_original_rows_preserved_once(self):
        for side in ['reviewer_1','reviewer_2']:
            for table in m.TABLES:
                expected=m.core.readcsv(PACKAGE/side/(table+'.csv'))
                actual=[s for r in self.rows if r['table']==table for s in json.loads(r[f'{side}_original_rows'])]
                self.assertEqual(collections.Counter(map(m.js,expected)),collections.Counter(map(m.js,actual)))

    def test_sections_and_reconciliation_counts(self):
        self.assertEqual(self.summary['sections'],dict(A=40,B=33,C=6,D=11))
        self.assertEqual(self.summary['mechanical_difference_units_reconciled'],33)
        self.assertEqual(self.summary['original_substantive_difference_units_investigated'],5)
        self.assertEqual(self.summary['additional_nominal_agreement_coverage_tensions'],1)

    def test_original_agreement_statistics_unchanged(self):
        self.assertEqual((OUT/'original_agreement_statistics.json').read_bytes(),(ROOT/'proposed_20261026/agreement_statistics.json').read_bytes())

    def test_saved_sample_inventory(self):
        receipt,groups=m.load_audit(PACKAGE)
        self.assertEqual(receipt['rows'],6560);self.assertEqual(len(groups),20)
        self.assertTrue(all(r['source_unchanged'] and r['recording_fresh_hash_verified'] for r in receipt['records']))

    def test_negative_fragments_do_not_cover_drop(self):
        r=self.find('events','episode_014','cream_cheese_1','negative_review');label=json.loads(r['proposed_label_json'])
        self.assertEqual(label['reviewed_intervals'],[[10,269],[286,530]])
        self.assertFalse(any(a<=frame<=b for a,b in label['reviewed_intervals'] for frame in range(270,286)))
        exported=next(x for x in m.core.readcsv(OUT/'adjudicated_events.csv') if x['adjudication_id']==r['adjudication_id'])
        self.assertEqual(exported['review_start_frame'],'');self.assertEqual(exported['review_end_frame'],'')

    def test_nominal_agreement_is_not_blindly_preserved(self):
        r=self.find('events','episode_000','butter_1','negative_review')
        self.assertEqual(r['ai_review_section'],'C');self.assertTrue(r['classification'].endswith('_agreement'))
        self.assertEqual(json.loads(r['proposed_label_json'])['reviewed_intervals'],[[10,257]])

    def test_mechanical_segmentation_distinguishes_three_transitions(self):
        r=self.find('events','episode_014','cream_cheese_1','lift_drop_sequence');label=json.loads(r['proposed_label_json'])
        self.assertEqual(r['ai_review_section'],'B')
        self.assertEqual([x['event_type'] for x in label['subevents']],['grasp_contact','held_lift','drop_after_lift'])
        self.assertEqual([x['earliest_onset_frame'] for x in label['subevents']],[269,272,281])
        self.assertEqual(label['departure_frame'],'')

    def test_cream_requirement_recommendation_and_pending_status(self):
        r=self.find('requirement_interpretation','episode_014','cream_cheese_1');label=json.loads(r['proposed_label_json'])
        self.assertEqual(label['interpretation'],'no_violation_observed_within_reviewed_coverage')
        self.assertEqual(r['human_approval_status'],'pending');self.assertEqual(r['adjudicator_identity'],'')
        self.assertIn('no carrying-duration threshold',r['reasoning'])

    def test_contact_is_not_causation(self):
        r=self.find('events','episode_014','milk_1','rock_motion');label=json.loads(r['proposed_label_json'])
        self.assertEqual(label['causal_responsibility'],'not_established')
        summary=json.loads(r['evidence_measurements_json']);self.assertEqual(summary['table_contact_samples'],40)
        self.assertTrue(label['recorded_gripper_contact_ranges'])

    def test_one_contact_gap_is_not_promoted_to_fall(self):
        r=self.find('events','episode_014','orange_juice_1','tip_motion');label=json.loads(r['proposed_label_json'])
        self.assertEqual(label['fall_status'],'insufficient_information')
        self.assertEqual(json.loads(r['evidence_measurements_json'])['table_contact_absent_ranges'],[[246,246]])

    def test_floor_contact_not_exact_visible_landing(self):
        r=self.find('events','episode_002','cream_cheese_1','setup_move_to_floor');label=json.loads(r['proposed_label_json'])
        self.assertEqual(label['landing_contact_frame'],12)
        self.assertEqual(label['landing_semantics'],'first_recorded_contact_not_exact_physical_landing')
        self.assertEqual(label['downward_motion_onset_interval'],[4,5])
        self.assertEqual(label['end_frame'],'')

    def test_uncertainties_preserved_and_distinguished_from_approval(self):
        rr=[r for r in self.rows if r['table']=='uncertainty_requests']
        self.assertEqual(len(rr),11)
        self.assertEqual(collections.Counter(json.loads(r['proposed_label_json'])['resolution_status'] for r in rr),dict(partially_resolved=10,resolved_existing_evidence=1))
        self.assertTrue(all(r['human_approval_status']=='pending' for r in rr))
        exported=m.core.readcsv(OUT/'adjudicated_uncertainty_requests.csv')
        self.assertTrue(all(not r['resolved_by'] and not r['resolution_date'] for r in exported))

    def test_canonical_referential_integrity(self):
        ids={r['event_id'] for r in m.core.readcsv(OUT/'adjudicated_events.csv')}
        for r in m.core.readcsv(OUT/'adjudicated_requirement_interpretation.csv'):
            self.assertTrue(set(filter(None,r['physical_event_id'].split(';')))<=ids)

    def test_all_90_approval_bindings_pending(self):
        ledger=m.core.readcsv(OUT/'remaining_human_approval.csv');byid={r['adjudication_id']:r for r in self.rows}
        self.assertEqual(len(ledger),90)
        for r in ledger:
            self.assertEqual(r['disposition'],'pending');self.assertEqual(r['adjudicator_identity'],'')
            self.assertEqual(r['proposal_sha256'],hashlib.sha256(m.js(byid[r['adjudication_id']]).encode()).hexdigest())

    def test_unreviewed_ledger_rejected(self):
        with self.assertRaisesRegex(AssertionError,'human decisions still pending'):
            m.check_approvals(PACKAGE,OUT,PRIVATE,OUT/'remaining_human_approval.csv')

    def test_tampered_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'out';shutil.copytree(OUT,target)
            with (target/'adjudicated_events.csv').open('a') as f:f.write('\n')
            with self.assertRaisesRegex(AssertionError,'output changed'):m.verify(PACKAGE,target)

    def test_public_safe_outputs(self):
        for path in OUT.iterdir():
            if path.is_file():self.assertFalse(m.re.search(r'/(?:Users|disk|local/home|eecs|private)/',path.read_text()),path.name)
        self.assertFalse(list(OUT.glob('*.png'))+list(OUT.glob('*.jpg'))+list(OUT.glob('*.h5')))

    def test_reproducibility(self):
        with tempfile.TemporaryDirectory(prefix='r1-ai-reproduce-') as temp:
            target=Path(temp)/'out';private=Path(temp)/'private'
            m.build(PACKAGE,ROOT/'proposed_20261026',target,private,None)
            for path in OUT.iterdir():self.assertEqual(path.read_bytes(),(target/path.name).read_bytes(),path.name)

    def test_local_review_has_no_signatures_or_network_clients(self):
        text=(ROOT/'ai_review_local_20261026/review.html').read_text()
        payload=json.loads(m.re.search(r'<script type="application/json" id="data">(.*?)</script>',text,m.re.S)[1])
        self.assertEqual(len(payload['rows']),90)
        self.assertTrue(all(r['human_approval_status']=='pending' and not r['adjudicator_identity'] for r in payload['rows']))
        self.assertNotIn('fetch(',text);self.assertNotIn('XMLHttpRequest',text)
        self.assertIn('Download reviewed decision ledger',text)


if __name__=='__main__':unittest.main()
