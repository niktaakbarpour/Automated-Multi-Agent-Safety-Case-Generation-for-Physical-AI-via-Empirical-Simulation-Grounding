import unittest,json,tempfile,sqlite3
from pathlib import Path
from dataclasses import replace
import numpy as np,h5py
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.config import WORK,NAMES
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.store import PhysicalStore
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.retrieve import PhysicalQuery,retrieve
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceError

class PhysicalRetrieval(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.build=json.loads((WORK/'BUILD.json').read_text());cls.db=PhysicalStore(WORK/'expanded.sqlite',expected_sha256=cls.build['database_sha256']);cls.e=cls.db.db.execute('select execution from h_jobs order by execution limit 1').fetchone()[0];cls.b=cls.db.binding(cls.e);cls.q=PhysicalQuery(cls.e,task_id=cls.b['task_id'],variant_id=cls.b['variant_id'],channel_id='raw.robot0_joint_pos',interval=(0,0),verification_mode='verified_session')
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def result(self,**kw):return retrieve(self.db,replace(self.q,**kw))
 def status(self,**kw):return self.result(**kw)['status']
 def test_verified_model_units_preserve_raw_values(self):
  r=self.result(units='rad');self.assertEqual(r['status'],'ok');item=r['results'][0];sample=item['samples'][0]
  with h5py.File(item['raw_record']['source_path']) as f:self.assertTrue(np.array_equal(sample['value'],f[sample['source_selector']][()]))
  self.assertIsNone(item['raw_record']['contract']['units']);self.assertEqual(sample['value_units'],'rad');self.assertEqual(sample['origin'],'direct_recording')
 def test_strict_source_mode(self):self.assertEqual(self.status(verification_mode='strict'),'ok')
 def test_gripper_is_joint_configuration(self):
  r=self.result(channel_id='raw.robot0_gripper_qpos',units='m');self.assertEqual(r['status'],'ok');self.assertEqual(r['results'][0]['semantic_record']['properties']['coordinate_frame']['value'],'joint_configuration')
 def test_gripper_velocity_units(self):self.assertEqual(self.status(channel_id='raw.robot0_gripper_qvel',units='m/s'),'ok')
 def test_joint_velocity_units(self):self.assertEqual(self.status(channel_id='raw.robot0_joint_vel',units='rad/s'),'ok')
 def test_count_units(self):self.assertEqual(self.status(channel_id='simulator.ncon',units='count'),'ok')
 def test_wrong_units(self):self.assertEqual(self.status(units='m'),'unsupported_units')
 def test_no_world_frame(self):self.assertEqual(self.status(coordinate_frame='MuJoCo_world'),'unsupported_coordinate_frame')
 def test_wrong_source(self):self.assertEqual(self.status(source_sha256='f'*64),'invalid_source_scope')
 def test_wrong_task(self):self.assertEqual(self.status(task_id='wrong'),'invalid_query_scope')
 def test_wrong_variant(self):self.assertEqual(self.status(variant_id='wrong'),'invalid_query_scope')
 def test_wrong_execution(self):self.assertEqual(self.status(execution_id='wrong'),'unknown_execution')
 def test_wrong_object(self):self.assertEqual(self.status(object_id='butter_1'),'no_matching_record')
 def test_wrong_component(self):self.assertEqual(self.status(component='robot0_joint0'),'no_matching_record')
 def test_component_projection(self):
  r=self.result(component='robot0_joint3',transformation='component_projection');self.assertEqual(r['status'],'ok');s=r['results'][0]['samples'][0];self.assertEqual(s['selected_value'],s['value'][2]);self.assertEqual(s['selected_component']['qpos_address'],2)
 def test_no_synchronized_physical_time(self):self.assertEqual(self.status(alignment='same_physical_instant'),'unsupported_alignment')
 def test_no_endpoint_shift(self):self.assertEqual(self.status(transformation='endpoint_shift'),'unsupported_transformation')
 def test_no_world_transform(self):self.assertEqual(self.status(transformation='world_transform'),'unsupported_transformation')
 def test_unresolved_property_cannot_be_opted_in(self):self.assertEqual(self.status(required_properties=('physical_synchronization',),allow_conditional=True),'unsupported_semantic_status')
 def test_conditional_offset_requires_opt_in(self):self.assertEqual(self.status(required_properties=('cache_offset_seconds',)),'unsupported_semantic_status')
 def test_conditional_offset_labeled(self):
  r=self.result(required_properties=('cache_offset_seconds',),allow_conditional=True);self.assertEqual(r['status'],'ok');self.assertEqual(r['results'][0]['semantic_record']['properties']['cache_offset_seconds']['status'],'CONDITIONAL');self.assertFalse(r['results'][0]['synchronized_physical_instant'])
 def test_force_si_requires_opt_in(self):
  sem=self.db.db.execute("select body from h_semantics where execution=? and channel='raw.simulator_actuator_force'",(self.e,)).fetchone()[0];a=json.loads(sem)['components'][0]['name'];self.assertEqual(self.status(channel_id='raw.simulator_actuator_force',component=a,units='N*m'),'unsupported_semantic_status')
 def test_force_si_opt_in_remains_conditional(self):
  sem=json.loads(self.db.db.execute("select body from h_semantics where execution=? and channel='raw.simulator_actuator_force'",(self.e,)).fetchone()[0]);a=sem['components'][0]['name'];r=self.result(channel_id='raw.simulator_actuator_force',component=a,units='N*m',allow_conditional=True);self.assertEqual(r['status'],'ok');s=r['results'][0]['samples'][0];self.assertEqual(s['selected_unit_status'],'CONDITIONAL');self.assertEqual(s['value_units'],'native_actuator_force')
 def test_no_contact_force_interpretation(self):self.assertEqual(self.status(channel_id='raw.simulator_actuator_force',units='contact_force'),'unsupported_units')
 def test_unknown_property(self):self.assertEqual(self.status(required_properties=('invented',)),'unsupported_property')
 def test_no_logical_table_pose(self):self.assertEqual(self.status(channel_id='logical_main_table_pose'),'unsupported_channel')
 def test_queued_action_does_not_imply_new_inference(self):
  r=self.result(interval=(12,12));t=r['results'][0]['samples'][0]['temporal_relation'];self.assertEqual(t['latest_available_observation_frame'],11);self.assertEqual(t['policy_inference_input_frame'],10);self.assertFalse(t['inference_triggered'])
 def test_initial_is_not_policy_action(self):self.assertIsNone(self.result()['results'][0]['samples'][0]['temporal_relation']['preceding_policy_action'])
 def test_window_boundary_exact(self):self.assertEqual([s['saved_frame_index'] for s in self.result(interval=(31,32))['results'][0]['samples']],[31,32])
 def test_no_future_sample(self):self.assertEqual(self.status(interval=(9999,9999)),'no_matching_record')
 def test_no_unverified_inspection(self):self.assertEqual(self.status(verification_mode='unverified'),'unsupported_verification')
 def test_all_excluded_ids_no_source_access(self):
  before=self.db.verifier.hash_checks
  for e,status in self.db.db.execute("select execution,status from rag_scope_status where status!='indexed'"):self.assertEqual(self.status(execution_id=e),status)
  self.assertEqual(before,self.db.verifier.hash_checks)
 def test_untrusted_database_cannot_return_verified_evidence(self):
  other=PhysicalStore(WORK/'expanded.sqlite')
  try:self.assertEqual(retrieve(other,self.q)['status'],'unverified_database')
  finally:other.close()
 def test_wrong_database_hash_rejected(self):
  with self.assertRaises(SourceError):PhysicalStore(WORK/'expanded.sqlite',expected_sha256='f'*64)

class ModelAndTimeEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.audit=json.loads((WORK/'AUDIT_FINAL.json').read_text());cls.velocity=json.loads((WORK/'VELOCITY_VALIDATION.json').read_text())
 def test_complete_fixed_corpus(self):self.assertEqual((self.audit['executions'],self.audit['variants'],self.audit['samples']),(432,104,58075))
 def test_all_configuration_and_force_bounds(self):self.assertEqual(self.audit['contract_failures'],0)
 def test_inverse_velocity_bounds(self):self.assertTrue(self.velocity['passed']);self.assertEqual(self.velocity['samples'],58075);self.assertTrue(all(not r['failures'] for r in self.velocity['rows']))
 def test_no_simulation_stepping(self):self.assertEqual(self.velocity['simulation_steps'],0)
 def test_native_types_and_order(self):
  for r in self.audit['rows']:self.assertEqual([j['name'] for j in r['joints']],NAMES);self.assertEqual([j['type'] for j in r['joints']],[3]*7+[2]*2)
 def test_exact_actuator_transmissions(self):
  for r in self.audit['rows']:self.assertEqual([a['joint_id'] for a in r['actuators']],[j['id'] for j in r['joints']]);self.assertTrue(all(a['gear']==[1.,0.,0.,0.,0.,0.] for a in r['actuators']))
 def test_cache_values_not_relabelled_endpoint(self):self.assertGreater(max(r['raw_endpoint_difference']['max'] for r in self.audit['rows']),0.)
 def test_real_chunk_inputs_distinct(self):
  t=[t for r in self.audit['rows'] for t in r['temporal_rows'] if t['chunk_offset'] not in (None,0)];self.assertTrue(t);self.assertTrue(all(x['policy_inference_input_frame']<x['latest_available_observation_frame'] for x in t))
 def test_terminal_action_mapping(self):
  for r in self.audit['rows']:self.assertEqual(r['temporal_rows'][-1]['preceding_policy_action'],r['frames']-12)
 def test_main_table_mapping_not_broadened(self):
  g=json.loads(Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/MAIN_TABLE_AUDIT.json').read_text());self.assertEqual(g['status_counts'],{'verified_symbolic_alias':147,'not_applicable_other_recorded_workspace':285});self.assertEqual(g['verified_variants'],98)
