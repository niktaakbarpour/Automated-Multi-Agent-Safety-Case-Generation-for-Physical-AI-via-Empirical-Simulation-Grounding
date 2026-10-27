"""Package readiness and software-only approval/scoring controls.

Temporary TEST_* examples below are not selected recording labels or empirical results.
No actual reviewer answers or accuracy results are produced by this suite.
"""
import argparse
import contextlib
import copy
import csv
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import workflow as w
from sample_cases import select
from score_after_approval import compare,verify_reference,score,normalized_events


class SelectionAndPackages(unittest.TestCase):
    def test_selection_reproduces_without_prediction_inputs(self):
        parent=ROOT.parent/'r1_v3_generalization'
        selected=select(json.loads((ROOT/'SAMPLING_PROTOCOL.json').read_text()),json.loads((parent/'INPUTS.json').read_text()),json.loads((parent/'blinded_review/evidence_manifest.json').read_text()))
        self.assertEqual(selected,json.loads((ROOT/'COORDINATOR_ASSIGNMENTS.json').read_text())['cases'])
        self.assertEqual(len({x['run_id'] for x in selected}),20)
        self.assertEqual(Counter(x['stratum'] for x in selected),dict(reserved_same_task=10,changed_task=10))
        for group in ['reserved_same_task','changed_task']:
            self.assertEqual(sorted(Counter(x['object_id'] for x in selected if x['stratum']==group).values()),[2]*5)
    def test_sampler_never_opens_predictions(self):
        text=(ROOT/'sample_cases.py').read_text()
        self.assertNotIn('predictions.json',text)
        self.assertNotIn('summary.json',text)
        self.assertNotIn('adjudicated_',text)
    def test_actual_archives_are_complete_and_equivalent(self):
        p=json.loads((ROOT/'PACKAGE_VALIDATION.json').read_text())
        self.assertTrue(p['ready_to_distribute']);self.assertTrue(p['equivalent_information_for_both_reviewers'])
        self.assertEqual(p['unavailable_or_inadequate_evidence'],[])
        for a in p['archives']:
            self.assertEqual((a['case_count'],a['distinct_recordings'],a['videos'],a['full_videos'],a['preview_videos']),(20,20,180,60,120))
            self.assertTrue(a['all_answers_blank']);self.assertTrue(a['neutral_identifiers_verified']);self.assertTrue(a['original_protocol_byte_identical'])
    def test_all_original_protected_bytes_unchanged(self):
        f=json.loads((ROOT/'PROVENANCE_FREEZE.json').read_text());repo=ROOT.parents[1]
        for n,h in f['protected_files'].items():self.assertEqual(hashlib.sha256((repo/n).read_bytes()).hexdigest(),h,n)
    def test_prereview_scoring_freeze_matches_code_and_selection(self):
        f=json.loads((ROOT/'SCORING_FREEZE.json').read_text())
        for n,h in f['files'].items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)

    def test_original_four_headers_preserved(self):
        x=json.loads((ROOT/'FORM_HEADERS.json').read_text())
        self.assertEqual(set(x),{t+'.csv' for t in w.TABLES})
        for n,h in x.items():
            with (ROOT.parents[1]/'human_review_package/reviewer_1'/n).open(encoding='utf-8-sig',newline='') as f:self.assertEqual(next(csv.reader(f)),h)


class WorkflowRoundTrip(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.assignment=self.root/'assignment.json'
        w.save(self.assignment,dict(cases=[dict(case_id='TEST01',run_id='SYNTHETIC_RECORDING_ONLY',object_id='synthetic_object',episode=0,frame_count=21,recording_sha256='0'*64)]))
        self.collected=self.root/'collected'
    def submit(self,who,complete=True):
        source=self.root/(who+'_return');a=source/'annotations';a.mkdir(parents=True)
        fields=json.loads((ROOT/'FORM_HEADERS.json').read_text())
        common=dict(record_id='TEST01:software-only',run_id='TEST01',episode='TEST01',object_id='synthetic_object',reviewer_copy=who,reviewer_identity='SYNTHETIC '+who,review_date='2026-10-27')
        for name,columns in fields.items():
            rr=[]
            if name!='uncertainty_requests.csv':
                row=dict(common)
                if name=='initial_support.csv':row.update(boundary_frame='10',support_label='uncertain',evidence_reasoning='SYNTHETIC SOFTWARE TEST ONLY')
                if name=='events.csv':row.update(event_id='TEST01:E1',observation_status='uncertain',event_type='uncertain')
                if name=='requirement_interpretation.csv':row.update(requirement_version=w.VERSION,applicability='insufficient_information',interpretation='insufficient_information',evidence_coverage='insufficient_information')
                if not complete:
                    for k in ['support_label','observation_status','applicability','interpretation']:row[k]=''
                rr=[{k:row.get(k,'') for k in columns}]
            w.csvwrite(a/name,columns,rr)
        if complete:
            (a/'physical_stage').mkdir()
            for t in ['initial_support','events','uncertainty_requests']:shutil.copyfile(a/(t+'.csv'),a/'physical_stage'/(t+'.csv'))
        archive=self.root/(who+'.zip')
        with zipfile.ZipFile(archive,'w') as z:
            for p in source.rglob('*.csv'):z.write(p,str(p.relative_to(source)))
        args=argparse.Namespace(reviewer=who,submission=archive,out=self.collected,assignments=self.assignment)
        with contextlib.redirect_stdout(io.StringIO()):w.collect(args)
        return archive
    def approved_reference(self):
        self.submit('reviewer_1');self.submit('reviewer_2')
        adjudication=self.root/'adjudication'
        with contextlib.redirect_stdout(io.StringIO()):w.template(argparse.Namespace(collected=self.collected,assignments=self.assignment,out=adjudication))
        for t in w.TABLES:
            p=adjudication/('adjudicated_'+t+'.csv');rr=w.rows(p)
            for row in rr:
                self.assertEqual(row['final_label_json'],'')
                label=dict(boundary_frame=10,support_label='uncertain') if t=='initial_support' else dict(applicability='insufficient_information',interpretation='insufficient_information',observation_domain='saved_frame_projection',reviewed_intervals=[[10,20]]) if t=='requirement_interpretation' else dict(observation_status='uncertain',event_type='synthetic_uncertainty',reviewed_intervals=[[0,20]])
                row.update(final_label_json=json.dumps(label),human_approval_status='approved',adjudicator_identity='SYNTHETIC TEST ADJUDICATOR',approval_date='2026-10-27')
            w.csvwrite(p,w.REFERENCE_FIELDS,rr)
        approval=self.root/'approval.json'
        with contextlib.redirect_stdout(io.StringIO()):w.approval_template(argparse.Namespace(collected=self.collected,assignments=self.assignment,adjudication=adjudication,out=approval))
        a=json.loads(approval.read_text());self.assertEqual(a['approval_decision'],'');self.assertFalse(a['independent_submissions_confirmed'])
        a.update(approval_decision='approve',adjudicator_identity='SYNTHETIC TEST ADJUDICATOR',approval_date='2026-10-27',independent_submissions_confirmed=True,approval_statement='SYNTHETIC SOFTWARE TEST ONLY; NOT A REAL HUMAN REFERENCE')
        w.save(approval,a)
        out=self.root/'approved'
        args=argparse.Namespace(collected=self.collected,assignments=self.assignment,adjudication=adjudication,approval=approval,out=out)
        with contextlib.redirect_stdout(io.StringIO()):w.freeze(args)
        return out,approval,adjudication
    def test_collect_preserves_original_return_bytes(self):
        source=self.submit('reviewer_1')
        self.assertEqual(w.sha(source),w.sha(self.collected/'reviewer_1/original_submission.zip'))
        receipt=json.loads((self.collected/'reviewer_1/RECEIPT.json').read_text());self.assertTrue(receipt['complete'])
    def test_blank_or_incomplete_submission_is_preserved_but_rejected(self):
        with self.assertRaisesRegex(ValueError,'preserved but incomplete'):self.submit('reviewer_1',complete=False)
        self.assertTrue((self.collected/'reviewer_1/original_submission.zip').exists())
        self.assertFalse(json.loads((self.collected/'reviewer_1/RECEIPT.json').read_text())['complete'])
    def test_no_overwrite_of_original_submission(self):
        source=self.submit('reviewer_1')
        with self.assertRaises(FileExistsError):w.collect(argparse.Namespace(reviewer='reviewer_1',submission=source,out=self.collected,assignments=self.assignment))
    def test_freeze_and_gate_roundtrip_without_checker_inputs(self):
        out,_,_=self.approved_reference();data,seal=verify_reference(out,self.assignment)
        self.assertTrue(seal['approved']);self.assertFalse(seal['prediction_inputs_used'])
        self.assertEqual(data['requirement_interpretation'][0]['final']['interpretation'],'insufficient_information')
    def test_approved_but_wrong_sample_is_rejected_before_prediction_read(self):
        reference,_,_=self.approved_reference()
        args=argparse.Namespace(reference=reference,assignments=self.assignment,predictions=self.root/'MUST_NOT_READ_PREDICTIONS',out=self.root/'not_a_score.json')
        with self.assertRaisesRegex(ValueError,'preregistered 20-case sample'):score(args)
        self.assertFalse(args.out.exists())

    def test_reference_tamper_is_rejected(self):
        out,_,_=self.approved_reference();p=out/'adjudicated_events.csv';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'reference changed'):verify_reference(out,self.assignment)
    def test_nonboolean_exact_endpoint_flag_rejected(self):
        out,_,adjudication=self.approved_reference();p=adjudication/'adjudicated_events.csv';rr=w.rows(p)
        label=json.loads(rr[0]['final_label_json']);label['evaluation_mapping']=dict(offset_established_exact='false')
        rr[0]['final_label_json']=json.dumps(label);w.csvwrite(p,w.REFERENCE_FIELDS,rr)
        with self.assertRaisesRegex(ValueError,'flag must be boolean'):w.reference_rows(adjudication,self.assignment)

    def test_original_human_tamper_rejected(self):
        self.submit('reviewer_1');self.submit('reviewer_2')
        p=self.collected/'reviewer_1/original_files/annotations/events.csv';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Original human'):w.verify_collected(self.collected,self.assignment)
    def test_unapproved_reference_rejected_before_prediction_read(self):
        # Neither path exists: reference gate must fail first, with no accuracy file.
        args=argparse.Namespace(reference=self.root/'UNAPPROVED',assignments=self.assignment,predictions=self.root/'MUST_NOT_READ_PREDICTIONS',out=self.root/'score.json')
        with self.assertRaises(FileNotFoundError) as e:score(args)
        self.assertIn('REFERENCE_SEAL.json',str(e.exception));self.assertFalse(args.out.exists())
    def test_original_run_wide_uncertainty_question_is_accepted(self):
        self.submit('reviewer_1');folder=self.collected/'reviewer_1/original_files/annotations'
        data={t:w.rows(folder/(t+'.csv')) for t in w.TABLES}
        data['uncertainty_requests']=[dict(run_id='TEST01',object_id='',reviewer_copy='reviewer_1',reviewer_identity='SYNTHETIC reviewer_1',review_date='2026-10-27',cannot_determine='Synthetic run-wide timing question')]
        self.assertEqual(w.validate_submission(data,'reviewer_1',w.cases(self.assignment)),[])

    def test_blank_approval_cannot_freeze(self):
        out,approval,adjudication=self.approved_reference();a=json.loads(approval.read_text());a['approval_decision']='';w.save(approval,a)
        with self.assertRaisesRegex(ValueError,'explicit independent human approval'):w.freeze(argparse.Namespace(collected=self.collected,assignments=self.assignment,adjudication=adjudication,approval=approval,out=self.root/'must_not_freeze'))


class SyntheticScoringTests(unittest.TestCase):
    def fixture(self):
        version='SYNTHETIC_TEST_R1';selection={};ps=[];data={t:[] for t in w.TABLES}
        scenarios=[('TP','applies','violation','applies','violation'),('FP','applies','no_violation_observed_within_reviewed_coverage','applies','violation'),('FN','applies','violation','applies','no_violation_observed_within_reviewed_coverage'),('TN','applies','no_violation_observed_within_reviewed_coverage','applies','no_violation_observed_within_reviewed_coverage'),('NA','does_not_apply','not_applicable','does_not_apply','not_applicable'),('ABSTAIN','applies','violation','applies','insufficient_information')]
        for cid,app,out,papp,pout in scenarios:
            run='SYNTHETIC_'+cid;obj='test_object';selection[cid]=dict(run_id=run,object_id=obj)
            identity=dict(run_id=run,object_id=obj,requirement_version=version)
            data['initial_support'].append(dict(identity,final=dict(boundary_frame=10,support_label='unsupported' if app=='does_not_apply' else 'direct_table')))
            data['requirement_interpretation'].append(dict(identity,final=dict(applicability=app,interpretation=out,reviewed_intervals=[[10,20]],observation_domain='saved_frame_projection')))
            mapping=dict(compatible_type='r1_fall',phase='departure',scope='in_scope',onset_bracket=[12,12],interval=[12,13])
            physical=dict(observation_status='observed',event_type='synthetic_fall',evaluation_mapping=mapping) if out=='violation' else dict(observation_status='no_event_observed_in_window',event_type='none',reviewed_intervals=[[10,20]])
            data['events'].append(dict(identity,adjudication_id=cid,final=physical))
            events=[]
            if pout=='violation':events=[dict(run_id=run,canonical_object_id=obj,requirement_version=version,event_id='P_'+cid,type='r1_fall',compatible_type='r1_fall',scope='in_scope',phase='departure',status='established',onset=12,onset_bracket=[12,12],interval=[12,13])]
            ps.append(dict(run_id=run,canonical_object_id=obj,requirement_version=version,applicability=papp,outcome=pout,measurement_frame_intervals=[[10,20]],applicable_observation_intervals=[[10,20]],events=events,abstention_reason='synthetic abstention' if pout=='insufficient_information' else None))
        protocol=dict(requirement_version=version,compatible_types=['r1_fall','setup_departure','post_lift_drop','grasp','lift','contact'])
        return ps,data,selection,protocol
    def test_positive_capable_counts_and_abstentions(self):
        r=compare(*self.fixture())
        self.assertEqual(r['binary_counts'],dict(TP=1,FP=1,FN=1,TN=1))
        self.assertEqual(r['decision_coverage'],dict(numerator=4,denominator=5))
        self.assertEqual(r['positive_class_recall'],.5);self.assertEqual(r['positive_class_F1'],.5)
        self.assertEqual(r['end_to_end_positive_recall'],1/3)
        self.assertEqual(r['counts']['reference_non_applicable'],1)
    def test_zero_positive_recall_and_F1_not_estimable(self):
        ps,data,sel,protocol=self.fixture()
        for r in data['requirement_interpretation']:
            if r['final']['interpretation']=='violation':r['final']['interpretation']='no_violation_observed_within_reviewed_coverage'
        result=compare(ps,data,sel,protocol)
        self.assertIsNone(result['positive_class_recall']);self.assertIsNone(result['positive_class_F1']);self.assertIsNone(result['end_to_end_positive_recall'])
    def test_partial_coverage_does_not_make_an_abstention_a_negative(self):
        ps,data,sel,protocol=self.fixture();ps[-1]['applicable_observation_intervals']=[[10,20]]
        r=compare(ps,data,sel,protocol);self.assertEqual(r['counts']['abstentions'],1);self.assertEqual(r['binary_counts']['TN'],1)
    def test_missing_measurement_domain_excludes_negative(self):
        ps,data,sel,protocol=self.fixture();ps[3]['measurement_frame_intervals']=[[10,11],[14,20]]
        r=compare(ps,data,sel,protocol);self.assertEqual(r['binary_counts']['TN'],0);self.assertEqual(r['counts']['uncovered_domains'],1)
    def test_event_matching_and_explicit_negative_FP_window(self):
        r=compare(*self.fixture())
        for tol in ['0','1']:
            m=r['localization'][tol];self.assertEqual(m['event_TP'],1);self.assertEqual(m['event_FN'],2);self.assertEqual(m['adjudicable_event_FP_ids'],['P_FP'])
    def test_unknown_reference_is_not_a_known_wrong_applicability(self):
        ps,data,sel,protocol=self.fixture();data['initial_support'][3]['final']['support_label']='uncertain'
        data['requirement_interpretation'][3]['final'].update(applicability='insufficient_information',interpretation='insufficient_information')
        r=compare(ps,data,sel,protocol);self.assertEqual(r['counts']['applicability_incorrect'],0);self.assertEqual(r['counts']['reference_unknown_with_determinate_prediction'],1)

    def test_run_wide_uncertainty_is_retained_in_secondary_analysis(self):
        ps,data,sel,protocol=self.fixture();data['uncertainty_requests']=[dict(run_id='SYNTHETIC_TN',object_id='',requirement_version=protocol['requirement_version'],final=dict(resolution_status='partially_resolved'))]
        r=compare(ps,data,sel,protocol);self.assertEqual(r['uncertainty_free_sensitivity']['units'],5);self.assertEqual(r['binary_counts']['TN'],1)

    def test_unknown_event_bounds_stay_unscorable(self):
        row=dict(run_id='TEST',object_id='test_object',requirement_version='TEST',adjudication_id='U',final=dict(observation_status='observed',event_type='unresolved',evaluation_mapping=dict(compatible_type='r1_fall',phase='departure',scope='in_scope',onset_bracket=[None,None],interval=[10,20])))
        p,n,u=normalized_events([row],['r1_fall']);self.assertEqual(p,[]);self.assertEqual(len(u),1)
    def test_established_subevent_survives_parent_uncertainty(self):
        row=dict(run_id='TEST',object_id='test_object',requirement_version='TEST',adjudication_id='GROUP',final=dict(observation_status='uncertain',event_type='compound',subevents=[dict(observation_status='observed',event_type='contact',evaluation_mapping=dict(compatible_type='contact',phase='contact',scope='post_lift',onset_bracket=[14,14],interval=[14,14],offset_established_exact=True)),dict(observation_status='uncertain',event_type='fall',fall_status='insufficient_information')]))
        p,n,u=normalized_events([row],['contact']);self.assertEqual(len(p),1);self.assertEqual(len(u),1);self.assertEqual(p[0]['compatible_type'],'contact')

    def test_disjoint_negative_windows_not_collapsed(self):
        ps,data,sel,protocol=self.fixture();data['events'][1]['final']['reviewed_intervals']=[[10,11],[14,20]]
        r=compare(ps,data,sel,protocol);self.assertEqual(r['localization']['0']['adjudicable_event_FP_ids'],[]);self.assertEqual(r['localization']['0']['unscorable_unmatched_prediction_ids'],['P_FP'])

if __name__=='__main__':unittest.main()
