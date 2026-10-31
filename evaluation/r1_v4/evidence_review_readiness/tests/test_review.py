import csv,json,unittest
from pathlib import Path
from evaluation.r1_v4.evidence_review_readiness.review_sources import HERE,PROFILE,SHEETS
from evaluation.r1_v4.libero_evidence_audit.audit_sources import load,sha

def csvrows(name):return list(csv.DictReader((HERE/name).open()))
class EvidenceReview(unittest.TestCase):
 def test_all_eleven_candidates_reviewed(self):
  rows=csvrows('AI_REFERENCE_REVIEWS.csv');self.assertEqual({r['candidate_id'] for r in rows},{f'C{i:02d}' for i in range(1,12)})
 def test_unfilled_sliding_not_fabricated(self):
  r=next(r for r in csvrows('AI_REFERENCE_REVIEWS.csv') if r['candidate_id']=='C04');self.assertEqual(r['AI_evidence_sufficiency'],'NO_EVIDENCE');self.assertEqual(json.loads(r['numerical_frames_actually_inspected']),[]);self.assertEqual(r['execution_id'],'')
 def test_evidence_ledger_references_resolve(self):
  ledger=csvrows('EVIDENCE_LEDGER.csv');ids={r['evidence_id'] for r in ledger};self.assertEqual(len(ids),41)
  for r in csvrows('AI_REFERENCE_REVIEWS.csv'):self.assertTrue(set(json.loads(r['evidence_ids']))<=ids)
  for r in ledger:self.assertTrue(set(json.loads(r['dependency_evidence_ids']))<=ids)
 def test_visual_review_exactly_authorized_images(self):
  v=load(HERE/'AUTHORIZED_VISUAL_EVIDENCE.json');self.assertEqual(len(v['files']),3);self.assertEqual(v['total_bytes'],120932);self.assertEqual(len(v['panels']),24)
  for r in v['files']:self.assertEqual((r['sha256'],r['bytes']),SHEETS[r['episode']])
  self.assertFalse(v['raw_HDF5_or_video_transferred']);self.assertFalse(v['additional_images_transferred'])
 def test_visual_frame_coverage_not_invented(self):
  rows={r['candidate_id']:r for r in csvrows('AI_REFERENCE_REVIEWS.csv')}
  self.assertEqual(json.loads(rows['C07']['candidate_frames_visually_inspected']),[])
  self.assertEqual(json.loads(rows['C08']['candidate_frames_visually_inspected']),[282,284])
  self.assertEqual(json.loads(rows['C01']['candidate_frames_visually_inspected']),[10])
 def test_camera_identity_and_uncertain_exposure_preserved(self):
  for p in load(HERE/'AUTHORIZED_VISUAL_EVIDENCE.json')['panels']:
   self.assertIn(p['camera'],('agentview_image','robot0_eye_in_hand_image'));self.assertIsNone(p['exposure_time']);self.assertIsNone(p['capture_time']);self.assertIsInstance(p['snapshot_endpoint_time'],float);self.assertTrue(p['viewed_in_current_Codex_session'])
 def test_no_human_truth_or_empirical_witness(self):
  for r in csvrows('AI_REFERENCE_REVIEWS.csv'):
   for key in ('human_confirmation_obtained','reference_ground_truth','support_predicate_admitted','fall_witness_admitted','negative_certificate_admitted'):self.assertEqual(r[key],'False')
   self.assertEqual(r['empirical_admission_sufficiency'],'INSUFFICIENT')
 def test_gate_statuses_not_promoted_by_review(self):
  g=csvrows('UPDATED_EVIDENCE_GATES.csv');self.assertEqual(len(g),12)
  for r in g:self.assertEqual(r['previous_status'],r['status_after_review']);self.assertEqual(r['empirical_admission_enabled'],'False');self.assertTrue(r['minimum_additional_evidence'])
 def test_readiness_separates_measurements_and_predicates(self):
  r=load(HERE/'READINESS_STATUS.json');self.assertTrue(r['read_only_measurements_ready']);self.assertTrue(r['geometric_computations_ready_for_declared_inputs'])
  for key in ('empirical_support_witness_ready','empirical_fall_witness_ready','qualified_negative_certification_ready','empirical_admission_enabled'):self.assertFalse(r[key])
 def test_same_exposed_AI_not_independent_confirmation(self):
  r=load(HERE/'REVIEW_PROVENANCE.json');self.assertTrue(r['single_AI_review']);self.assertTrue(r['prior_context_exposure']);self.assertEqual(r['independent_AI_reviews'],0);self.assertEqual(r['human_reviews'],0);self.assertEqual(r['verified_physical_reference_cases'],0)
 def test_old_human_review_forms_unchanged_and_blank(self):
  s=load(HERE/'SOURCE_BINDINGS.json');self.assertEqual(sha(PROFILE/'REFERENCE_REVIEW_FORM.csv'),s['human_form_sha256'])
  for row in csv.DictReader((PROFILE/'REFERENCE_REVIEW_FORM.csv').open()):self.assertTrue(all(v=='' for k,v in row.items() if k!='candidate_id'))
 def test_no_heldout_numerical_case(self):
  for r in load(HERE/'NUMERICAL_REVIEW_SUMMARY.json'):
   if r['available']:self.assertIn(r['episode'],(0,2,14));self.assertFalse(r['physical_event_admitted']);self.assertFalse(r['physical_support_validated']);self.assertTrue(r['co_motion_measurement_is_not_holding_proof'])
 def test_measurement_evidence_not_AI_physical_truth(self):
  for r in csvrows('EVIDENCE_LEDGER.csv'):self.assertEqual(r['physical_predicate_admitted'],'False')
 def test_no_media_or_original_data_in_git_artifacts(self):
  self.assertFalse([p for p in HERE.rglob('*') if p.is_file() and p.suffix.lower() in ('.h5','.jpg','.png','.mp4')])
 def test_source_host_timestamps_preserved_without_exposure_claim(self):
  for p in load(HERE/'AUTHORIZED_VISUAL_EVIDENCE.json')['panels']:
   self.assertTrue(p['snapshot_host_timestamps']['utc']);self.assertIsInstance(p['snapshot_host_timestamps']['wall_time_ns'],int);self.assertIsInstance(p['snapshot_host_timestamps']['monotonic_ns'],int);self.assertIsNone(p['exposure_time'])
