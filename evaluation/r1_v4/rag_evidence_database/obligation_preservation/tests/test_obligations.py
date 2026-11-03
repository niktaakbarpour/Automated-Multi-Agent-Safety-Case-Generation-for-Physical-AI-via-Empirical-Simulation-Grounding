import unittest,json,copy
from dataclasses import asdict,replace
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.retrieve import Retriever,BundleRequest
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.config import *
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.intent import derive
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.validator import validate
class Obligations(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.r=Retriever();cls.e=cls.r.catalogue.execute('select execution from catalogue order by execution limit 1').fetchone()[0];cls.c=json.loads(cls.r.catalogue.execute('select body from catalogue where execution=?',(cls.e,)).fetchone()[0]);cls.q=BundleRequest('Joint positions and velocities at frame 20.',cls.e,verification_mode='verified_session')
 @classmethod
 def tearDownClass(cls):cls.r.close()
 def model(self,text):q=replace(self.q,query=text);return q,derive(text,asdict(q),self.c)
 def test_joint_configuration_is_preserved(self):
  b=self.r.retrieve(replace(self.q,query='Joint configuration at simulator time 2.5 seconds.'));self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertIn(CHANNELS[2],b['requested_families']);self.assertTrue(b['obligation_preservation']['passed']);self.assertTrue(b['evidence_fulfillment']['passed'])
 def test_conjunction(self):self.assertEqual(set(self.r.retrieve(self.q)['requested_families']),{CHANNELS[2],CHANNELS[3]})
 def test_mutation_drop_each_measurement(self):
  for text in ('Arm and gripper configurations at frame 20.','Joint positions and velocities at frame 20.','Gripper state and motor output at frame 20.','All six measurement channels at frame 20.'):
   q,m=self.model(text)
   for family in m['families']:
    with self.subTest(text=text,family=family):self.assertFalse(validate(text,asdict(q),m,[f for f in m['families'] if f!=family])['passed'])
 def test_circular_reduced_model_and_plan_fails(self):
  q,m=self.model('Joint configuration at simulator time 2.5 seconds.');m['obligations']=[o for o in m['obligations'] if o['target']!=CHANNELS[2]];m['families'].remove(CHANNELS[2]);self.assertFalse(validate(q.query,asdict(q),m,m['families'])['passed'])
 def test_missing_temporal_attachment(self):
  q,m=self.model(self.q.query)
  for o in m['obligations']:
   if o['type']=='measurement':o['required_temporal_scope']=[]
  self.assertFalse(validate(q.query,asdict(q),m,m['families'])['passed'])
 def test_forged_clock(self):
  q,m=self.model('Arm positions at simulator time 2.5.')
  for o in m['obligations']:
   if o['type']=='temporal':o['selector']['value']=4.
  self.assertFalse(validate(q.query,asdict(q),m,m['families'])['passed'])
 def test_explicit_reduced_plan_cannot_complete(self):self.assertEqual(self.r.retrieve(replace(self.q,plan=(CHANNELS[2],)))['completeness_status'],'UNVERIFIED PLAN')
 def test_temporal_measurement_word_order(self):
  sets=[]
  for t in ('At frame 20 give joint positions and velocities.','Give joint positions and velocities at frame 20.','At frame 20, velocities and positions of the arm.'):
   q,m=self.model(t);sets.append({o['target'] for o in m['obligations'] if o['type']=='measurement'})
  self.assertTrue(all(x=={CHANNELS[2],CHANNELS[3]} for x in sets))
 def test_entity_conjunction_word_order(self):
  for t in ('Arm and gripper configurations at frame 20.','Configurations of gripper and arm at frame 20.'):
   q,m=self.model(t);self.assertEqual({o['target'] for o in m['obligations'] if o['type']=='measurement'},{CHANNELS[0],CHANNELS[2]})
 def test_quote_is_not_request(self):
  b=self.r.retrieve(replace(self.q,query='Source excerpt: "Read joint positions". Give source hash.'));self.assertEqual(b['requested_families'],['source_provenance']);self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_quoted_field_is_request(self):self.assertIn(CHANNELS[2],self.r.retrieve(replace(self.q,query='Read "joint configurations" at frame 20.'))['requested_families'])
 def test_configuration_not_always_arm(self):self.assertNotEqual(self.r.retrieve(replace(self.q,query='Scene configuration at frame 20.'))['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_missing_instant(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Gripper state and motor output.'))['completeness_status'],'AMBIGUOUS')
 def test_near_is_not_exact(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Joint positions and velocities near frame 20.'))['completeness_status'],'AMBIGUOUS')
 def test_comparison_preserved_not_answered(self):
  b=self.r.retrieve(replace(self.q,query='What changed between two timestamps?'));self.assertTrue(any(o['type']=='comparison' for o in b['query_obligations']));self.assertNotEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_motion_geometry_ambiguous(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give geometry and motion measurements.'))['completeness_status'],'AMBIGUOUS')
 def test_inventory_visible(self):self.assertTrue(any(o['type']=='availability' for o in self.r.retrieve(replace(self.q,query='Which measurements are available and which are missing?'))['query_obligations']))
 def test_unrecorded_does_not_hide_behind_time(self):self.assertNotEqual(self.r.retrieve(replace(self.q,query='Thermal pressure at simulator time 2.5.'))['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_unknown_head_does_not_hide(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Joint positions and magnetometer telemetry at frame 20.'))['completeness_status'],'UNVERIFIED PLAN')
 def test_component_ambiguity_visible(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Elbow joint position at frame 20.'))['completeness_status'],'UNSUPPORTED')
 def test_conditional_cache_preserved(self):
  b=self.r.retrieve(replace(self.q,query='Raw joint positions at frame 20 under the conditional cache interpretation.',allow_conditional=True));self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertTrue(any(o['target']=='cache_offset_seconds:conditional' for o in b['query_obligations']))
 def test_component_binding_uses_existing_native_order(self):
  b=self.r.retrieve(replace(self.q,query='Give first joint angle at the initial snapshot.'));self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');o=next(o for o in b['query_obligations'] if o['type']=='component');self.assertEqual(o['component_bindings'][0]['array_index'],0)
 def test_gripper_joint_is_not_arm(self):
  q,m=self.model('Gripper joint positions at frame 20.');self.assertEqual([o['target'] for o in m['obligations'] if o['type']=='measurement'],[CHANNELS[0]])
 def test_unknown_conjunct_cannot_disappear(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Motor output and bone health at frame 20.'))['completeness_status'],'UNVERIFIED PLAN')
 def test_changed_scope_model_fails(self):
  q,m=self.model(self.q.query)
  for o in m['obligations']:o['scope']['execution_id']='another'
  self.assertFalse(validate(q.query,asdict(q),m,m['families'])['passed'])
 def test_independent_validator_does_not_import_planner(self):
  text=(HERE/'validator.py').read_text();self.assertNotIn('from .intent import',text);self.assertNotIn('from .planner import',text);self.assertNotIn('vocabulary.json',text)
 def test_unfulfilled_comparison_never_complete_even_with_values(self):
  b=self.r.retrieve(replace(self.q,query='Do joint positions at frame 20 equal zero?'));self.assertEqual(b['completeness_status'],'PARTIAL');self.assertFalse(b['evidence_fulfillment']['passed']);self.assertTrue(b['unsatisfied_obligation_ids'])
 def test_explicit_raw_under_unsupported_transform_is_partial(self):
  b=self.r.retrieve(replace(self.q,query='Raw joint positions at frame 20 with a world transform.'));self.assertEqual(b['completeness_status'],'PARTIAL');self.assertFalse(b['evidence_fulfillment']['passed'])
 def test_selector_dependency_has_explicit_source_family_node(self):
  q,m=self.model('Joint velocity at simulation time 2.5.');self.assertTrue(any(o['type']=='source_family' and o['target']=='recorded_time' for o in m['obligations']))
 def test_quantified_registry_accepts_singular_channel_head(self):
  q,m=self.model('Every measurement channel at frame 20.');self.assertEqual({o['target'] for o in m['obligations'] if o['type']=='measurement'},set(CHANNELS))
 def test_residual_inspection_is_never_query_fulfillment(self):
  b=self.r.retrieve(replace(self.q,query='Show joint positions from the saved frame 20.'));self.assertEqual(b['completeness_status'],'UNVERIFIED PLAN');self.assertTrue(b['inspection_only']);self.assertFalse(b['evidence_fulfillment']['passed'])
 def test_explicit_mutant_plan_is_not_inspection(self):
  b=self.r.retrieve(replace(self.q,plan=(CHANNELS[2],)));self.assertEqual(b['completeness_status'],'UNVERIFIED PLAN');self.assertFalse(b.get('inspection_only',False))
 def test_auxiliary_field_span_does_not_swallow_unknown_conjunct(self):
  b=self.r.retrieve(replace(self.q,query='Actuator outputs and joint forces at frame 20.'));self.assertEqual(b['completeness_status'],'UNVERIFIED PLAN');self.assertFalse(b['evidence_fulfillment']['passed'])
 def test_unknown_quantifier_modifier_not_six_known_arrays(self):
  b=self.r.retrieve(replace(self.q,query='All six bone health channels at frame 20.'));self.assertNotEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_clock_proof_span_cannot_swallow_unknown_conjunct(self):
  b=self.r.retrieve(replace(self.q,query='Joint positions and bone health at simulation time 2.5.'));self.assertEqual(b['completeness_status'],'UNVERIFIED PLAN')
 def test_actual_selection_must_match_original_selector(self):
  original=self.r.backend.retrieve
  def corrupt(q,mode):
   b=original(q,mode);b['interpretation']['resolved_frame_interval']=[21,21];return b
  self.r.backend.retrieve=corrupt
  try:
   b=self.r.retrieve(replace(self.q,query='Joint positions at frame 20.'));self.assertEqual(b['completeness_status'],'PARTIAL');self.assertFalse(b['evidence_fulfillment']['passed'])
  finally:self.r.backend.retrieve=original
