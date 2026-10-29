import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run_frozen import adapt,intervals
from matching import match_events,contained

class AdapterTests(unittest.TestCase):
    def test_missing_events_never_imply_a_negative(self):
        result={'initial_applicability':'direct_table_support_candidate','events':[], 'gaps':[], 'support_transitions':[], 'unconfirmed_descent_sequences':[], 'requirement_verdict':'not_assessed_pending_approval'}
        samples=[{'frame':10,'valid':True},{'frame':11,'valid':False},{'frame':12,'valid':True}]
        p=adapt('run','object',result,samples,{}, {'requirement_version':'r1','adapter_version':'v1'})
        self.assertEqual(p['applicability'],'unknown')
        self.assertEqual(p['outcome'],'insufficient_information')
        self.assertEqual(p['measurement_frame_intervals'],[[10,10],[12,12]])
        self.assertEqual(p['reviewed_frame_intervals'],[])
        self.assertFalse(p['compatible_reference_domain_established'])
    def test_no_support_candidate_does_not_prove_non_applicability(self):
        r={'initial_applicability':'initial_table_support_not_established','events':[], 'gaps':[], 'support_transitions':[], 'unconfirmed_descent_sequences':[], 'requirement_verdict':'pending'}
        p=adapt('r','o',r,[{'frame':10,'valid':True}],{}, {'requirement_version':'r1','adapter_version':'v1'})
        self.assertEqual(p['applicability'],'unknown')
        self.assertIn('does not establish absence',p['abstention_reason'])

class MatchingTests(unittest.TestCase):
    def event(self,id,start,end,**kwargs):
        e=dict(event_id=id,run_id='r',canonical_object_id='o',requirement_version='r1',phase='departure',scope='in_scope',compatible_type='r1_fall',status='established',interval=[start,end],onset=start,onset_bracket=[start,start])
        e.update(kwargs);return e
    def test_max_cardinality_beats_greedy(self):
        # p1 can match either, p2 only r1. Best cardinality is two.
        p=[self.event('p1',11,14),self.event('p2',10,10)]
        r=[self.event('r1',10,12,onset_bracket=[10,11]),self.event('r2',11,14)]
        m=match_events(p,r)
        self.assertEqual([(x['prediction_id'],x['reference_id']) for x in m['matches']],[('p1','r2'),('p2','r1')])
    def test_tolerance_and_scope_and_candidates(self):
        p=self.event('p',11,12);r=self.event('r',10,10)
        self.assertEqual(len(match_events([p],[r],0)['matches']),0)
        self.assertEqual(len(match_events([p],[r],1)['matches']),1)
        for change in [dict(scope='setup'),dict(phase='contact'),dict(status='candidate'),dict(requirement_version='r2')]:
            self.assertEqual(len(match_events([dict(p,**change)],[r],1)['matches']),0)
    def test_stable_ids_and_duplicate_predictions(self):
        ps=[self.event('b',10,12),self.event('a',10,12)]
        r=[self.event('r',10,12)]
        self.assertEqual(match_events(ps,r)['matches'][0]['prediction_id'],'a')
        self.assertEqual(match_events(ps,r)['unmatched_predictions'],['b'])
    def test_disjoint_windows_not_collapsed(self):
        self.assertTrue(contained([10,269],[[10,269],[286,530]]))
        self.assertFalse(contained([269,286],[[10,269],[286,530]]))
    def test_unknown_endpoints_do_not_become_errors(self):
        p=self.event('p',10,12);r=self.event('r',9,13,onset_bracket=[9,11])
        m=match_events([p],[r])['matches'][0]
        self.assertIsNone(m['onset_error_saved_frames']);self.assertIsNone(m['offset_error_saved_frames'])


class ScoringTests(unittest.TestCase):
    def setUp(self):
        import json
        self.json=json
        self.pred=json.loads((ROOT/'execution/predictions.json').read_text())
        self.manifest=json.loads((ROOT/'recordings.json').read_text())
        self.protocol=json.loads((ROOT/'protocol.json').read_text())
    def test_unknown_run_object_and_requirement_rejected(self):
        from score import validate_predictions
        for field,value in [('run_id','wrong-run'),('canonical_object_id','unknown'),('requirement_version','r1-old')]:
            pred=copy.deepcopy(self.pred);pred[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_predictions(pred,self.manifest,self.protocol)
    def test_duplicate_and_missing_units_rejected(self):
        from score import validate_predictions
        for pred in [self.pred[:-1],self.pred+[self.pred[0]]]:
            with self.assertRaises(ValueError):validate_predictions(pred,self.manifest,self.protocol)
    def test_provisional_events_cannot_be_promoted(self):
        from score import validate_predictions
        for field,value in [('applicability','applies'),('outcome','violation'),('outcome','no_violation_observed_within_reviewed_coverage'),('compatible_reference_domain_established',True)]:
            pred=copy.deepcopy(self.pred);pred[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_predictions(pred,self.manifest,self.protocol)
    def test_valid_frozen_predictions(self):
        from score import validate_predictions
        self.assertEqual(len(validate_predictions(self.pred,self.manifest,self.protocol)),20)
    def test_final_label_json_is_authoritative(self):
        import csv,tempfile
        from score import read_final
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['human_approval_status','final_label_json','proposed_label_json','interpretation'])
                w.writeheader();w.writerow(dict(human_approval_status='approved',final_label_json='{"interpretation":"not_applicable"}',proposed_label_json='{"interpretation":"violation"}',interpretation=''))
            self.assertEqual(read_final(p)[0]['final']['interpretation'],'not_applicable')
    def test_compound_subevents_keep_group_and_contact_semantics(self):
        from score import normalize_reference_event
        row=dict(run_id='r',object_id='o',requirement_version='r1',adjudication_id='group',final=dict(event_type='held_lift_then_drop_after_lift',landing_contact_frame=284,subevents=[dict(event_type='grasp_contact',earliest_onset_frame=269,latest_onset_frame=270),dict(event_type='held_lift',earliest_onset_frame=272,latest_onset_frame=273,last_sampled_holding_frame=281),dict(event_type='drop_after_lift',earliest_onset_frame=281,latest_onset_frame=282,first_recorded_table_contact_frame=284)]))
        n=normalize_reference_event(row)
        self.assertEqual(len(n['phases']),4)
        self.assertEqual({p['reference_group_id'] for p in n['phases']},{'group'})
        self.assertTrue(all(p['scope']=='post_lift' for p in n['phases']))
        self.assertTrue(all(p['physical_end_frame'] is None for p in n['phases']))
    def test_missing_reference_event_is_not_a_negative_window(self):
        from score import normalize_reference_event
        row=dict(run_id='r',object_id='o',requirement_version='r1',adjudication_id='unknown',final=dict(event_type='tip_and_slide',fall_status='insufficient_information'))
        n=normalize_reference_event(row)
        self.assertEqual(n['reviewed_intervals'],[])
        self.assertEqual(n['scoring_status'],'physical_observation_without_established_fall')

    def test_checker_and_protocol_drift_rejected(self):
        from score import validate_predictions
        for field in ['checker_sha256','checker_config_sha256','checker_commit','evaluation_config_sha256','adapter_sha256']:
            pred=copy.deepcopy(self.pred);pred[0][field]='changed'
            with self.subTest(field=field),self.assertRaises(ValueError):validate_predictions(pred,self.manifest,self.protocol)
    def test_actual_reference_denominators_and_abstentions(self):
        from score import compare,read_final
        ref=ROOT.parents[1]/'human_review_package/adjudication/approved_reference/r1-reference-be76abc531f5c716efca'
        rows=[read_final(ref/('adjudicated_'+n+'.csv')) for n in ['initial_support','requirement_interpretation','events','uncertainty_requests']]
        result=compare(self.pred,*rows)
        self.assertEqual(result['total_units'],20)
        self.assertEqual(result['counts']['eligible_reference_units'],7)
        self.assertEqual(result['counts']['eligible_abstentions'],7)
        self.assertEqual(result['counts']['non_applicable_units'],13)
        self.assertEqual(result['binary_denominator'],0)
        self.assertEqual(result['binary_counts_on_determinate_compatible_subset'],dict(TP=0,FP=0,FN=0,TN=0))
        self.assertIsNone(result['positive_class_recall'])
        self.assertIsNone(result['positive_class_F1'])
        cream=next(c for c in result['cases'] if 'trial014' in c['run_id'] and c['canonical_object_id']=='cream_cheese_1')
        self.assertEqual(cream['reference_reviewed_negative_windows'],[[10,269],[286,530]])
        juice=next(c for c in result['cases'] if 'trial014' in c['run_id'] and c['canonical_object_id']=='orange_juice_1')
        self.assertEqual(juice['reference_requirement']['applicability'],'does_not_apply')
        self.assertFalse(juice['reference_eligible'])

class SealTests(unittest.TestCase):
    def test_tampered_predictions_rejected_before_reference_loading(self):
        import shutil,subprocess,tempfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            shutil.copytree(ROOT/'execution',root/'execution')
            pred=root/'execution/predictions.json'
            pred.write_text(pred.read_text()+' ')
            proc=subprocess.run([sys.executable,str(ROOT/'score.py'),'--execution',str(root/'execution'),'--reference',str(root/'nonexistent-reference'),'--output',str(root/'out.json')],capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('Sealed artifact changed: predictions.json',proc.stderr)
            self.assertFalse((root/'out.json').exists())

if __name__=='__main__':unittest.main()
