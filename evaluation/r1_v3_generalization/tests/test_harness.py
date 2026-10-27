import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import bind_mapping,source_receipt
from controlled_audit import probes


class HarnessTests(unittest.TestCase):
    def original(self):
        return dict(source_xml_sha256='xml',body_names=['world','object_main'],native_geom_count=2,validated_run_ids=['old'])
    def test_no_modification_to_mapping_source_on_registration(self):
        class Index:
            def __init__(self,record):self.record=record
            def geometries_for_body(self,name):return [dict(native_geom_id=1)]
        source=self.original();before=copy.deepcopy(source)
        index,entities=bind_mapping(source,Index,dict(run_id='new',objects=[dict(name='object',root_body_name='object_main',body_id=1)]),'xml',dict(body_names=source['body_names']),2)
        self.assertEqual(source,before)
        self.assertEqual(index.record['validated_run_ids'],['new'])
        self.assertEqual(entities['object']['native_geom_ids'],[1])
    def test_different_xml_never_reuses_native_ids(self):
        with self.assertRaises(ValueError):bind_mapping(self.original(),object,dict(run_id='new',objects=[]),'different',dict(body_names=['world','object_main']),2)
    def test_body_order_and_geometry_count_mismatch_rejected(self):
        for names,count in [(['object_main','world'],2),(['world','object_main'],3)]:
            with self.assertRaises(ValueError):bind_mapping(self.original(),object,dict(run_id='new',objects=[]),'xml',dict(body_names=names),count)
    def test_reserved_partition_has_exact_ten_no_development_overlap(self):
        x=json.loads((ROOT/'INPUTS.json').read_text())
        self.assertEqual(len(x['reserved_run_ids']),10)
        self.assertFalse(set(x['reserved_run_ids'])&set(x['split_development']))
        self.assertEqual(len(x['records']),60)
    def test_frozen_checker_and_all_protected_hashes(self):
        repo=ROOT.parents[1];f=json.loads((ROOT/'FREEZE.json').read_text())
        for name,digest in f['protected_files'].items():
            self.assertEqual(hashlib.sha256((repo/name).read_bytes()).hexdigest(),digest,name)
    def test_no_prediction_input_to_review_exporter(self):
        text=(ROOT/'build_review.py').read_text()
        self.assertNotIn('import r1_checker',text)
        self.assertNotIn("/'predictions.json'",text)
        self.assertNotIn('applicability=p[',text)
    def test_controlled_probes_disclose_event_scope_inconsistency(self):
        result=probes()
        case=next(p for p in result if p['case']=='initial_absence_then_later_table_departure')
        self.assertEqual(case['applicability'],'does_not_apply')
        self.assertEqual(case['outcome'],'not_applicable')
        self.assertEqual(len(case['contradictory_event_tags']),1)
    def test_controlled_name_invariance_and_conservatism(self):
        result=probes()
        self.assertEqual(next(p for p in result if p['case']=='post_lift_identity_renaming')['post_lift_drops'],1)
        self.assertEqual(next(p for p in result if p['case']=='tiny_represented_pose_change')['applicability'],'insufficient_information')


class ResultsAndBlindingTests(unittest.TestCase):
    def test_unlabelled_metrics_are_null_not_zero(self):
        from summarize import summarize
        s=summarize(ROOT)
        for part in s['partitions'].values():
            self.assertIsNone(part['applicability_confusion'])
            self.assertTrue(all(v is None for v in part['coverage_compatible_binary_counts'].values()))
            self.assertIsNone(part['positive_recall'])
            self.assertEqual(part['independently_reviewed_units'],0)
    def test_actual_task_shift_coverage_counts(self):
        from summarize import summarize
        p=summarize(ROOT)['partitions']
        self.assertEqual(p['same_task_reserved']['operational_decision_coverage'],dict(numerator=20,denominator=20))
        self.assertEqual(p['cross_task_same_scene']['operational_decision_coverage'],dict(numerator=0,denominator=100))
        self.assertEqual(p['cross_task_same_scene']['predicted_applicable_abstentions'],100)
    def test_review_answer_columns_blank(self):
        import csv
        answer_fields=['support_label','observation_status','event_description','event_type','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','applicability','interpretation','reviewer_identity','reasoning','approval_decision']
        for p in (ROOT/'blinded_review').glob('reviewer_*/*.csv'):
            with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),0 if p.name=='uncertainty_requests.csv' else 300)
            self.assertTrue(all(not row.get(k,'') for row in rows for k in answer_fields))
    def test_harness_runtime_matches_pre_execution_freeze(self):
        runtime=json.loads((ROOT/'execution/runtime.json').read_text())
        freeze=json.loads((ROOT/'HARNESS_FREEZE.json').read_text())
        self.assertEqual(runtime['harness_sha256'],freeze['files']['run.py'])
        for n,h in freeze['files'].items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h)
    def test_no_complete_trajectory_duplicates_in_compared_64(self):
        from summarize import summarize
        s=summarize(ROOT)
        for d in s['duplicates'].values():
            self.assertEqual(d['records'],64)
            self.assertEqual(d['unique'],64)
            self.assertEqual(d['duplicate_groups'],[])

if __name__=='__main__':unittest.main()
