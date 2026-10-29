"""Post-seal development regressions; no reference inputs enter checker code."""
import argparse
import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluate_reference import compare,verify,read_final,main


class RecordedRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pred=json.loads((ROOT/'execution/predictions.json').read_text())
    def get(self,trial,obj):
        return next(p for p in self.pred if f'trial{trial}' in p['run_id'] and p['canonical_object_id']==obj)
    def test_setup_cream_departure_not_policy_landing_alarm(self):
        p=self.get('002','cream_cheese_1')
        self.assertEqual(p['applicability'],'does_not_apply')
        self.assertEqual(p['outcome'],'not_applicable')
        setup=next(e for e in p['events'] if e['type']=='setup_departure')
        self.assertEqual(setup['onset_bracket'],[0,1])
        self.assertEqual(setup['evidence']['downward_motion_bracket'],[4,5])
        self.assertEqual(setup['evidence']['first_recorded_contact_frame'],12)
        self.assertEqual(setup['scope'],'setup')
    def test_held_cream_drop_retained_without_full_domain_pass(self):
        p=self.get('014','cream_cheese_1')
        self.assertEqual(p['applicability'],'applies')
        self.assertEqual(p['outcome'],'insufficient_information')
        lift=next(e for e in p['events'] if e['type']=='lift')
        drop=next(e for e in p['events'] if e['type']=='post_lift_drop')
        self.assertEqual(drop['scope'],'post_lift')
        self.assertEqual(drop['evidence']['lift_event_id'],lift['event_id'])
        self.assertEqual(lift['evidence']['upward_pair'],[273,274])
        self.assertEqual(drop['onset_bracket'],[281,282])
        self.assertEqual(drop['evidence']['first_recorded_contact_frame'],284)
        self.assertEqual(p['applicable_observation_intervals'],[[10,269],[289,530]])
    def test_orange_motion_uncertainty_not_fall(self):
        p=self.get('014','orange_juice_1')
        self.assertEqual(p['applicability'],'does_not_apply')
        later=[e for e in p['events'] if e['interval'][1]>=57]
        self.assertTrue(later)
        self.assertFalse(any(e['type']=='r1_fall' for e in later))
        self.assertTrue(any(e['evidence'].get('fall_status')=='insufficient_information' for e in later))
    def test_no_missing_output_or_false_scope_claim(self):
        self.assertEqual(len(self.pred),20)
        self.assertEqual(len({(p['run_id'],p['canonical_object_id']) for p in self.pred}),20)
        self.assertFalse(any(p['outcome']=='violation' for p in self.pred))


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo=ROOT.parents[1]
        cls.ref=cls.repo/'human_review_package/adjudication/approved_reference/r1-reference-be76abc531f5c716efca'
        cls.pred=json.loads((ROOT/'execution/predictions.json').read_text())
        cls.baseline=json.loads((ROOT.parent/'r1_reference/results.json').read_text())
        cls.rows=[read_final(cls.ref/f'adjudicated_{n}.csv') for n in ['requirement_interpretation','initial_support','events','uncertainty_requests']]
    def test_actual_denominators_no_nonscope_TNs(self):
        result=compare(self.pred,*self.rows,self.baseline)
        self.assertEqual(result['counts']['applicable_reference'],7)
        self.assertEqual(result['counts']['non_applicable_reference'],13)
        self.assertEqual(result['counts']['applicable_correct'],7)
        self.assertEqual(result['counts']['non_applicable_correct'],13)
        self.assertEqual(result['counts']['binary_compared'],6)
        self.assertEqual(result['counts']['eligible_abstentions'],1)
        self.assertEqual(result['binary_counts'],dict(TP=0,FP=0,FN=0,TN=6))
        self.assertIsNone(result['positive_class_recall']);self.assertIsNone(result['positive_class_F1'])
    def test_strict_and_one_frame_localization(self):
        result=compare(self.pred,*self.rows,self.baseline)
        for tol in ['0','1']:
            p=result['localization'][tol]['outside_R1_physical_diagnostic']
            self.assertEqual(len(p['matches']),37)
            self.assertEqual(p['unmatched_predictions'],[])
            self.assertEqual(len(p['unmatched_references']),1)
            self.assertEqual(result['localization'][tol]['R1']['matches'],[])
    def test_uncovered_domain_cannot_become_TN(self):
        predictions=copy.deepcopy(self.pred)
        target=next(p for p in predictions if p['outcome']=='no_violation_observed_within_reviewed_coverage')
        target['applicable_observation_intervals']=[[10,10]]
        result=compare(predictions,*self.rows,self.baseline)
        self.assertEqual(result['binary_counts']['TN'],5)
        self.assertEqual(result['counts']['eligible_abstentions'],2)
    def test_nonscope_alarm_is_scope_error_not_binary_FP(self):
        predictions=copy.deepcopy(self.pred)
        target=next(p for p in predictions if p['applicability']=='does_not_apply')
        target['applicability']='applies';target['outcome']='violation'
        result=compare(predictions,*self.rows,self.baseline)
        self.assertEqual(result['counts']['scope_errors'],1)
        self.assertEqual(result['binary_counts']['FP'],0)
    def test_tamper_rejected_before_any_reference_read(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'execution';shutil.copytree(ROOT/'execution',path)
            p=path/'predictions.json';p.write_text(p.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'Sealed prediction artifact changed'):
                verify(path,self.repo)
    def test_score_reproduces_saved_result(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'score.json'
            with contextlib.redirect_stdout(io.StringIO()):
                main(argparse.Namespace(execution=ROOT/'execution',reference=self.ref,output=p))
            self.assertEqual(p.read_bytes(),(ROOT/'results.json').read_bytes())

if __name__=='__main__':unittest.main()
