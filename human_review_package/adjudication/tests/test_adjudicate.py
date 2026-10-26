"""Matching unit tests and real-input integration tests; synthetic approvals only.

Any finalized test datasets exist ONLY inside temporary directories and are removed
by unittest cleanup. Test approval names are fixtures, never project approvals.
"""
import collections
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools'
spec=importlib.util.spec_from_file_location('adjudicate',TOOLS/'adjudicate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PACKAGE=TOOLS.parents[1]


def event(name='E1',run='run1',obj='milk_1',lo='10',hi='20',kind='rock_and_shift'):
    return dict(event_id=name,run_id=run,object_id=obj,episode='episode_000',
                observation_status='observed',event_type=kind,
                earliest_onset_frame=lo,end_frame=hi)


class Alignment(unittest.TestCase):
    def test_categorical_conflict(self):
        self.assertEqual(m.categorical([{'x':'applies'}],[{'x':'does_not_apply'}],['x']),'conflicting_annotations')

    def test_harmless_formatting(self):
        self.assertEqual(m.categorical([{'x':' Applies '}],[{'x':'applies'}],['x']),'semantically_equivalent_agreement')

    def test_missing_is_not_negative(self):
        self.assertEqual(m.categorical([{'x':'unsupported'}],[],['x']),'incomplete_annotation')

    def test_blank_is_incomplete(self):
        self.assertEqual(m.categorical([{'x':''}],[{'x':'unsupported'}],['x']),'incomplete_annotation')

    def test_reordered_repeated_events(self):
        a=[event('A1',lo='10',hi='20'),event('A2',lo='50',hi='60')]
        b=[event('B2',lo='50',hi='60'),event('B1',lo='10',hi='20')]
        matched=m.align_events(a,b)
        self.assertEqual({(x[1][0]['event_id'],x[2][0]['event_id']) for x in matched},{('A1','B1'),('A2','B2')})

    def test_duplicate_event_identity_rejected(self):
        with self.assertRaisesRegex(AssertionError,'duplicate'):
            m.align_events([event(),event()],[])

    def test_cross_run_identity_never_matches(self):
        rows=m.align_events([event(run='run1')],[event(run='run2')])
        self.assertEqual(len(rows),2)
        self.assertTrue(all(not a or not b for _,a,b in rows))

    def test_distinct_object_never_matches(self):
        self.assertEqual(len(m.align_events([event(obj='milk_1')],[event(obj='ketchup_1')])),2)

    def test_temporal_tolerance(self):
        self.assertTrue(m.overlap(event(lo='0',hi='10'),event(lo='11',hi='20')))
        self.assertFalse(m.overlap(event(lo='0',hi='10'),event(lo='12',hi='20')))

    def test_unknown_timing_not_zero(self):
        self.assertIsNone(m.integer(''))
        self.assertFalse(m.overlap(event(lo='',hi=''),event()))

    def test_ambiguous_overlap_not_arbitrarily_paired(self):
        rows=m.align_events([event('A')],[event('B1'),event('B2')])
        self.assertEqual(len(rows),3)

    def test_compound_sequence(self):
        rows=m.align_events([event('A',lo='269',hi='285',kind='picked up and dropped')],
            [event('B1',lo='272',hi='281',kind='held_lift'),event('B2',lo='281',hi='285',kind='drop_after_lift')])
        self.assertEqual(len(rows),1)
        self.assertEqual(m.classify_event(rows[0][1],rows[0][2]),'event_segmentation_difference')

    def test_negative_coverage_is_not_positive_event(self):
        a=event();a.update(observation_status='no_event_observed_in_window',event_type='none')
        rows=m.align_events([a],[event()])
        self.assertEqual(len(rows),2)

    def test_kappa_known(self):
        self.assertAlmostEqual(m.kappa(['a','a','b','b'],['a','b','b','b'])['kappa'],0.5)

    def test_kappa_no_variance(self):
        self.assertIsNone(m.kappa(['a'],['a'])['kappa'])

    def test_unresolved_semantics(self):
        m.validate_label('uncertainty_requests',{'resolution_status':'unresolved_missing_evidence'},{'last_frame':530})
        with self.assertRaises(AssertionError):
            m.validate_label('requirement_interpretation',{'applicability':'does_not_apply','interpretation':'violation'},{'last_frame':530})


class RealSubmissions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('R1_PUBLIC_ONLY_TESTS')=='1' or not (PACKAGE/'adjudication/evidence_20261026/recorded_evidence.json').is_file():
            raise unittest.SkipTest('Authorized private excerpts are excluded from Git; these evidence-dependent integration tests run locally. Portable publication/source tests run separately.')
        cls.tmp=tempfile.TemporaryDirectory(prefix='r1-adjudication-tests-')
        cls.root=Path(cls.tmp.name)
        cls.proposal=cls.root/'proposal'
        cls.stats=m.build(PACKAGE,cls.proposal)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ledger(self):
        rows=m.readcsv(self.proposal/'approval_template.csv')
        decisions={r['adjudication_id']:r for r in m.readcsv(self.proposal/'adjudication_decisions.csv')}
        for r in rows:
            r.update(disposition='approved',adjudicator_identity='Nikta (SYNTHETIC TEST FIXTURE)',approval_date='2026-10-26',
                     label_json=decisions[r['adjudication_id']]['proposed_label_json'],reason='SYNTHETIC TEST ONLY; no real human approval',
                     evidence_references=json.loads(decisions[r['adjudication_id']]['evidence_references'])[0])
        return rows

    def save_ledger(self,rows,name):
        p=self.root/name;m.writecsv(p,rows);return p

    def test_actual_counts(self):
        self.assertEqual(self.stats['total_source_rows'],160)
        self.assertEqual(self.stats['categorical_reliability']['initial_support.support_label']['agreements'],20)
        self.assertEqual(self.stats['categorical_reliability']['requirement_interpretation.interpretation']['agreements'],19)

    def test_missing_both_reviewers_still_reported(self):
        data,_,scope,runs,byrun=m.load_sources(PACKAGE)
        key=(runs[0]['run_id'],scope['protected_objects'][0])
        for side in ['reviewer_1','reviewer_2']:
            data[(side,'initial_support')]=[r for r in data[(side,'initial_support')] if (r['run_id'],r['object_id'])!=key]
        units=m.build_alignment(data,[key],byrun)
        unit=next(u for u in units if u['table']=='initial_support' and (u['run_id'],u['object_id'])==key)
        self.assertEqual(unit['classification'],'incomplete_annotation')
        self.assertFalse(unit['reviewer_1_rows'] or unit['reviewer_2_rows'])

    def test_every_source_row_represented_once(self):
        units=m.readcsv(self.proposal/'alignment_report.csv')
        for side in ['reviewer_1','reviewer_2']:
            for table in m.FILES:
                before=m.readcsv(PACKAGE/side/(table+'.csv'))
                after=[r for u in units if u['table']==table for r in json.loads(u[f'{side}_original_rows'])]
                self.assertEqual(collections.Counter(map(m.js,before)),collections.Counter(map(m.js,after)))

    def test_source_integrity(self):
        manifest=json.loads((self.proposal/'dataset_manifest.json').read_text())
        for p,h in manifest['source_file_sha256'].items():self.assertEqual(m.digest(PACKAGE/p),h)

    def test_no_real_approval(self):
        rows=m.readcsv(self.proposal/'adjudication_decisions.csv')
        self.assertTrue(all(r['human_approval_status']=='pending' and not r['adjudicator_identity'] for r in rows))
        self.assertFalse(list(self.proposal.glob('adjudicated_*.csv')))

    def test_approval_required(self):
        with self.assertRaisesRegex(AssertionError,'explicit human decision'):
            m.finalize(PACKAGE,self.proposal,self.proposal/'approval_template.csv',self.root/'not-approved')

    def test_changed_proposal_rejected(self):
        import shutil
        copydir=self.root/'tampered'
        shutil.copytree(self.proposal,copydir)
        with (copydir/'adjudication_decisions.csv').open('a') as f:f.write('\n')
        with self.assertRaisesRegex(AssertionError,'proposal changed'):
            m.verify(PACKAGE,copydir)

    def test_missing_evidence_rejected(self):
        # Copy proposal metadata; replace only its integrity map to point at a
        # nonexistent evidence file. No actual recording/submission is changed.
        import shutil
        copydir=self.root/'missing-evidence';shutil.copytree(self.proposal,copydir)
        p=copydir/'dataset_manifest.json';d=json.loads(p.read_text());d['evidence_file_sha256']['absent-evidence.csv']='0'*64;m.writejson(p,d)
        p=copydir/'proposal_checksums.json';d=json.loads(p.read_text());d['dataset_manifest.json']=m.digest(copydir/'dataset_manifest.json');m.writejson(p,d)
        with self.assertRaises(FileNotFoundError):m.verify(PACKAGE,copydir)

    def test_synthetic_approved_exports_reproduce_and_protect_versions(self):
        ledger=self.save_ledger(self.ledger(),'synthetic-approved.csv')
        out=m.finalize(PACKAGE,self.proposal,ledger,self.root/'exports-a')
        out2=m.finalize(PACKAGE,self.proposal,ledger,self.root/'exports-b')
        self.assertEqual(out.name,out2.name)
        for p in out.iterdir():self.assertEqual(p.read_bytes(),(out2/p.name).read_bytes())
        events=m.readcsv(out/'adjudicated_events.csv');event_ids={r['event_id'] for r in events}
        requirements=m.readcsv(out/'adjudicated_requirement_interpretation.csv')
        self.assertTrue(all(set(filter(None,r['physical_event_id'].split(';')))<=event_ids for r in requirements))
        self.assertIn('support_label',m.readcsv(out/'adjudicated_initial_support.csv')[0])
        (out/'adjudicated_events.csv').write_text('tampered')
        with self.assertRaisesRegex(AssertionError,'existing frozen outputs changed'):
            m.finalize(PACKAGE,self.proposal,ledger,self.root/'exports-a')

    def test_pending_ledger_row_rejected(self):
        rows=self.ledger();rows[0]['disposition']='pending'
        with self.assertRaisesRegex(AssertionError,'explicit human decision'):
            m.finalize(PACKAGE,self.proposal,self.save_ledger(rows,'pending.csv'),self.root/'pending')

    def test_unsupported_correction_rejected(self):
        rows=self.ledger();rows[0]['evidence_references']='REQUIREMENT_FOR_REVIEW.md'
        with self.assertRaisesRegex(AssertionError,'decision-specific supporting evidence'):
            m.finalize(PACKAGE,self.proposal,self.save_ledger(rows,'unsupported.csv'),self.root/'unsupported')

    def test_cross_run_final_label_rejected(self):
        rows=self.ledger();label=json.loads(rows[0]['label_json']);label['run_id']='another-run';rows[0]['label_json']=m.js(label)
        with self.assertRaisesRegex(AssertionError,'cross-run final label'):
            m.finalize(PACKAGE,self.proposal,self.save_ledger(rows,'cross-run.csv'),self.root/'cross-run')

    def test_indirect_without_entity_rejected(self):
        rows=self.ledger();decisions={r['adjudication_id']:r for r in m.readcsv(self.proposal/'adjudication_decisions.csv')}
        row=next(r for r in rows if decisions[r['adjudication_id']]['table']=='initial_support');row['label_json']=m.js({'support_label':'indirect'})
        with self.assertRaisesRegex(AssertionError,'chain entity'):
            m.finalize(PACKAGE,self.proposal,self.save_ledger(rows,'indirect.csv'),self.root/'indirect')

    def test_changed_approval_binding_rejected(self):
        rows=self.ledger();rows[0]['proposal_sha256']='0'*64
        with self.assertRaisesRegex(AssertionError,'does not bind'):
            m.finalize(PACKAGE,self.proposal,self.save_ledger(rows,'binding.csv'),self.root/'binding')

    def test_unresolved_retained(self):
        rows=self.ledger();decisions={r['adjudication_id']:r for r in m.readcsv(self.proposal/'adjudication_decisions.csv')}
        row=next(r for r in rows if decisions[r['adjudication_id']]['table']=='uncertainty_requests')
        row['disposition']='unresolved';row['label_json']=m.js({'resolution_status':'unresolved_missing_evidence','remaining_uncertainty':'Test missing subframe evidence'})
        out=m.finalize(PACKAGE,self.proposal,self.save_ledger(rows,'unresolved.csv'),self.root/'unresolved')
        labels=m.readcsv(out/'adjudicated_uncertainty_requests.csv')
        self.assertTrue(any(r['human_approval_status']=='unresolved' for r in labels))

    def test_rebuild_is_identical(self):
        other=self.root/'rebuild';m.build(PACKAGE,other)
        for p in self.proposal.iterdir():self.assertEqual(p.read_bytes(),(other/p.name).read_bytes(),p.name)


if __name__=='__main__':unittest.main()
