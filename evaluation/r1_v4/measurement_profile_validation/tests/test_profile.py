import csv,json,math,unittest
import numpy as np
from evaluation.r1_v4.measurement_profile_validation.geometry import corners,union,displacement,contact_metrics
from evaluation.r1_v4.measurement_profile_validation.temporal import phase_residual,clock_summary
from evaluation.r1_v4.measurement_profile_validation.numerical_checks import check
from evaluation.r1_v4.measurement_profile_validation.gates import rows
from evaluation.r1_v4.measurement_profile_validation.analyze import HERE
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha,load
class Geometry(unittest.TestCase):
 def test_exact_rational_enclosures(self):self.assertEqual(check()['exact_rational_coordinate_checks'],648)
 def test_identity_box_dimensions(self):
  c=corners([0,0,1],np.eye(3),[.2,.3,.4]);b=union([c]);np.testing.assert_allclose(b['min'],[-.2,-.3,.6]);np.testing.assert_allclose(b['max'],[.2,.3,1.4]);self.assertIsNone(b['input_physical_uncertainty'])
 def test_collision_union_keeps_all_pieces(self):
  a=corners([0,0,0],np.eye(3),[1,1,1]);b=corners([10,0,0],np.eye(3),[1,1,1]);u=union([a,b]);self.assertEqual(u['min'][0],-1);self.assertEqual(u['max'][0],11)
 def test_root_height_is_not_collision_bottom(self):
  b=union([corners([0,0,1],np.eye(3),[.1,.1,.2])]);self.assertNotEqual(b['min'][2],1);self.assertNotIn('support',b)
 def test_rotated_box(self):
  r=np.array([[0,0,1],[0,1,0],[-1,0,0]]);b=union([corners([0,0,0],r,[1,2,3])]);self.assertEqual(b['min'],[-3,-2,-1]);self.assertEqual(b['max'],[3,2,1])
 def test_missing_union(self):
  with self.assertRaises(ValueError):union([])
 def test_invalid_size(self):
  for size in ([1,0,1],[1,-1,1],[1,np.nan,1]):
   with self.subTest(size=size),self.assertRaises(ValueError):corners([0,0,0],np.eye(3),size)
 def test_wrong_shape(self):
  with self.assertRaises(ValueError):corners([0,0],np.eye(3),[1,1,1])
 def test_downward_indicator_is_not_witness(self):
  d=displacement(corners([0,0,2],np.eye(3),[1,1,1]),corners([0,0,1],np.eye(3),[1,1,1]));self.assertLess(d['max_vertex_dz_upper'],0);self.assertFalse(d['physical_motion_witness']);self.assertIsNone(d['input_physical_uncertainty'])
 def test_identical_samples_do_not_certify_rest(self):
  c=corners([.1,.2,.3],np.eye(3),[.01,.02,.03]);d=displacement(c,c);self.assertEqual(d['max_vertex_displacement'],0);self.assertFalse(d['physical_motion_witness'])
 def test_correspondence_required(self):
  c=corners([0,0,0],np.eye(3),[1,1,1])
  with self.assertRaises(ValueError):displacement(c,tuple(x[:4] for x in c))
class ContactAndTime(unittest.TestCase):
 def test_contact_alone_does_not_prove_support(self):
  gs=[dict(owner_body='world') for _ in range(105)];gs[10]={'owner_body':'living_room_table_col'};gs[104]={'owner_body':'cream_cheese_1_main'}
  b={104:dict(min=[0,0,1],max=[1,1,2]),10:dict(min=[0,0,0],max=[1,1,1])}
  r=contact_metrics([dict(geom1=10,geom2=104,dist=0,pos=[0,0,1])],[104],gs,b);self.assertEqual(r['categories']['table'],1);self.assertIsNone(r['load_bearing_support'])
 def test_missing_contact_is_not_absence_certificate(self):self.assertIsNone(contact_metrics([],[],[],{})['load_bearing_support'])
 def test_cache_identity_is_hypothesis_only(self):
  r=phase_residual([1,2,3],[0,0,0],[0,0,0],[1,2,3],[1,2,3],0,0,.002);self.assertEqual(r['endpoint_cache_residual'],0);self.assertIsNone(r['calibrated_phase_bound'])
 def test_missing_phase_input_stays_unknown(self):self.assertIsNone(phase_residual(None,None,None,None,None,0,0,.002)['endpoint_cache_residual'])
 def test_raw_phase_not_camera_phase(self):
  r=phase_residual([1,2,3],[1,1,1],None,[1,2,3],[1,2,3],0,0,.002);self.assertIsNone(r['raw_two_substep_hypothesis_residual']);self.assertIsNone(r['calibrated_phase_bound'])
 def test_clock_gaps_remain_visible(self):
  r=clock_summary([0,2],[0,.1]);self.assertEqual(r['missing_indices'],[1]);self.assertFalse(r['continuous_coverage']);self.assertIsNone(r['camera_exposure_bound'])
 def test_nonmonotonic_clock_not_repaired(self):self.assertFalse(clock_summary([0,1],[1,0])['strictly_monotonic'])
 def test_incomplete_clock_rejected(self):
  with self.assertRaises(ValueError):clock_summary([0],[0])
class GatesAndProvenance(unittest.TestCase):
 def test_source_proof_required_for_native_gate(self):
  r=rows(load(HERE/'DIAGNOSTIC_SUMMARY.json'),check());self.assertEqual(r[0]['status'],'BLOCKED_ON_EVIDENCE')
 def test_computational_success_cannot_enable_physical_gates(self):
  s=load(HERE/'DIAGNOSTIC_SUMMARY.json');s['independent_physical_reference_cases']=999
  gates=rows(s,check(),source_validated=True)
  for g in gates:
   if g['gate_id'].startswith(('G04','G05','G06','G07','G10','G11','G12')):self.assertEqual(g['status'],'BLOCKED_ON_EVIDENCE')
   self.assertFalse(g['empirical_admission_enabled'])
 def test_machine_gate_statuses_closed_set(self):
  gates=load(HERE/'GATE_STATUS.json');self.assertFalse(gates['empirical_admission_enabled']);self.assertTrue(all(g['status'] in {'VERIFIED','CONDITIONALLY_SUPPORTED','BLOCKED_ON_EVIDENCE','UNSUPPORTED'} for g in gates['gates']))
 def test_physical_parameters_have_no_invented_bound(self):
  for r in csv.DictReader((HERE/'CALIBRATION_PARAMETERS.csv').open()):
   if r['status']=='BLOCKED_ON_EVIDENCE':self.assertEqual(r['proposed_conservative_bound'],'')
   self.assertEqual(r['empirical_physical_threshold'],'False')
 def test_reference_proposals_not_ground_truth(self):
  proposals=list(csv.DictReader((HERE/'DEVELOPMENT_REFERENCE_CANDIDATES.csv').open()));self.assertEqual(len(proposals),11)
  for r in proposals:self.assertEqual(r['usable_as_ground_truth'],'False');self.assertEqual(r['human_validated'],'False');self.assertEqual(r['admitted_R1_violation'],'False')
 def test_sliding_category_not_fabricated(self):
  r=next(r for r in csv.DictReader((HERE/'DEVELOPMENT_REFERENCE_CANDIDATES.csv').open()) if r['category']=='sliding');self.assertEqual(r['source_path'],'');self.assertEqual(r['proposal_status'],'NO_VERIFIED_EXAMPLE_PREPARED')
 def test_no_heldout_reference_source(self):
  episodes={int(r['episode']) for r in csv.DictReader((HERE/'DEVELOPMENT_REFERENCE_CANDIDATES.csv').open()) if r['episode']};self.assertEqual(episodes,{0,2,14})
 def test_source_bindings_current(self):
  bindings=load(HERE/'SOURCE_BINDINGS.json')
  for r in bindings['recordings']:self.assertEqual(sha(r['path']),r['sha256'])
  self.assertEqual(sha(bindings['full_diagnostics']['path']),bindings['full_diagnostics']['sha256'])
 def test_camera_exposure_never_invented(self):
  for r in load(HERE/'CAMERA_EXCERPT_MANIFEST.json'):self.assertIsNone(r['capture_time']);self.assertEqual(sha(r['derived_sheet']),r['derived_sheet_sha256'])
 def test_no_runtime_judgments(self):
  summary=load(HERE/'DIAGNOSTIC_SUMMARY.json');self.assertEqual(summary['physical_judgments_issued'],0);self.assertFalse(summary['empirical_admission_enabled']);self.assertEqual(summary['independent_physical_reference_cases'],0)
class ReferenceSafeguards(unittest.TestCase):
 def test_new_review_forms_have_no_prefilled_decisions(self):
  forms=list(csv.DictReader((HERE/'REFERENCE_REVIEW_FORM.csv').open()));self.assertEqual(len(forms),10)
  for row in forms:self.assertTrue(row['candidate_id']);self.assertTrue(all(v=='' for k,v in row.items() if k!='candidate_id'))
