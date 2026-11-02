import copy,json,tempfile,unittest
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.libero_measurement_reader.reader import read,MAP,COORDINATES
from evaluation.r1_v4.libero_measurement_reader.bridge import observations
from evaluation.r1_v4.provenance import canonical
from evaluation.r1_v4.contracts import Truth,Measurement
from evaluation.r1_v4.libero_measurement_reader.tests.fixtures import Fixture,REAL
class Synthetic(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='/disk/1/data/niktakbr',prefix='r1v4-reader-test-');self.addCleanup(self.tmp.cleanup);self.f=Fixture(self.tmp.name)
 def result(self,**kw):return read(self.f.root,0,[10],expected=self.f.expected,synthetic=True,**kw)
 def codes(self,r):return [x.code for x in r.diagnostics]
 def test_valid_synthetic_measurements(self):
  r=self.result();self.assertEqual(r.status,'verified_measurements');self.assertEqual(r.coverage['validated'],list(range(13)));self.assertTrue(r.synthetic)
 def test_missing_file(self):
  (self.f.ep/'run_metadata.json').unlink();r=self.result();self.assertEqual(r.status,'missing');self.assertEqual(r.frames,[])
 def test_hash_mismatch(self):
  (self.f.ep/'run_metadata.json').write_text('{}');r=self.result();self.assertEqual(r.status,'invalid');self.assertIn('hash_mismatch:run_metadata.json',self.codes(r))
 def test_corrupted_hdf5(self):
  self.f.h5.write_bytes(b'not HDF5');self.f.reseal();r=self.result();self.assertEqual(r.status,'invalid');self.assertEqual(r.frames,[])
 def test_missing_metadata_field(self):
  p=self.f.ep/'run_metadata.json';m=json.loads(p.read_text());del m['checkpoint'];p.write_text(json.dumps(m));self.f.reseal();self.assertEqual(self.result().status,'missing')
 def test_checkpoint_mismatch(self):
  p=self.f.ep/'run_metadata.json';m=json.loads(p.read_text());m['checkpoint_revision']='other';p.write_text(json.dumps(m));self.f.reseal();self.assertEqual(self.result().status,'invalid')
 def test_incorrect_native_mapping(self):
  g=json.loads(MAP.read_text());g['geometries'].pop(10);self.assertEqual(self.result(geometry=g).status,'invalid')
 def test_anonymous_geometry_preserved(self):
  g=self.result().native_geometry['geometries'];self.assertEqual(len(g),161);self.assertIsNone(g[10]['name']);self.assertEqual(g[15]['native_geom_id'],15)
 def test_nonmonotonic_time(self):
  def change(h):
   h['frames/000010/simulator/time/value'][()]=0;h['frames/000010/simulator/flattened/value'][0]=0
  self.f.mutate(change);r=self.result();self.assertEqual(r.status,'invalid');self.assertIn('non_monotonic_simulator_time',self.codes(r))
 def test_frame_state_offset(self):
  self.f.mutate(lambda h:h['frames/000011'].attrs.__setitem__('control_step',1));self.assertEqual(self.result().status,'invalid')
 def test_transition_clock_mismatch(self):
  self.f.mutate(lambda h:h['transitions/000000/simulator_time/value'].__setitem__((),99));self.assertEqual(self.result().status,'invalid')
 def test_missing_contact_field(self):
  def change(h):
   h['frames/000010/simulator/contacts'].attrs['json']='[{"geom1":10,"geom2":104,"pos":[0,0,0]}]';h['frames/000010/simulator/ncon/value'][()]=1
  self.f.mutate(change);r=self.result();self.assertEqual(r.status,'missing');self.assertIn('contact_fields',self.codes(r))
 def test_out_of_range_contact(self):
  def change(h):
   h['frames/000010/simulator/contacts'].attrs['json']='[{"geom1":999,"geom2":104,"pos":[0,0,0],"dist":0}]';h['frames/000010/simulator/ncon/value'][()]=1
  self.f.mutate(change);self.assertEqual(self.result().status,'invalid')
 def test_contact_count_mismatch(self):
  self.f.mutate(lambda h:h['frames/000010/simulator/ncon/value'].__setitem__((),1));self.assertEqual(self.result().status,'invalid')
 def test_unsupported_camera_alignment(self):
  r=self.result();self.assertIn('camera_exposure_alignment',self.codes(r));self.assertIsNone(r.frames[0].camera_references[0]['capture_time']);self.assertFalse(r.frames[0].camera_references[0]['pixels_read'])
 def test_inconsistent_object_identity(self):
  p=self.f.ep/'simulator_index.json';m=json.loads(p.read_text());m['body_names'][22]='replacement';p.write_text(json.dumps(m));self.f.reseal();self.assertEqual(self.result().status,'invalid')
 def test_invalid_coordinate_frame(self):
  c=dict(COORDINATES);c['length_unit']='cm';self.assertEqual(self.result(coordinates=c).status,'invalid')
 def test_incomplete_saved_coverage(self):
  self.f.mutate(lambda h:h['frames'].__delitem__('000009'));r=self.result();self.assertEqual(r.status,'invalid');self.assertEqual(r.coverage['missing'],[9]);self.assertEqual(r.coverage['negative_certificates'],[])
 def test_missing_array(self):
  self.f.mutate(lambda h:h['frames/000010/simulator'].__delitem__('body_xpos'));self.assertEqual(self.result().status,'missing')
 def test_bad_shape(self):
  def change(h):
   g=h['frames/000010/simulator/qpos'];del g['value'];g.create_dataset('value',data=np.zeros(2))
  self.f.mutate(change);self.assertEqual(self.result().status,'invalid')
 def test_bad_dtype(self):
  def change(h):
   g=h['frames/000010/simulator/qpos'];del g['value'];g.create_dataset('value',data=np.zeros(65,dtype=np.int64))
  self.f.mutate(change);self.assertEqual(self.result().status,'invalid')
 def test_nonfinite(self):
  self.f.mutate(lambda h:h['frames/000010/simulator/qpos/value'].__setitem__(0,np.nan));self.assertEqual(self.result().status,'invalid')
 def test_static_root_motion(self):
  mapping=json.loads(MAP.read_text());owner=mapping['geometries'][10]['owner_body_id']
  def change(h):
   g=h['frames/000010/simulator'];g['body_xpos/value'][owner,0]+=1
   for geom in mapping['geometries']:
    if geom['owner_body_id']==owner:g['geom_xpos/value'][geom['native_geom_id'],0]+=1
  self.f.mutate(change);self.assertEqual(self.result().status,'invalid')
 def test_soft_link_rejected(self):
  def change(h):
   g=h['frames/000010/simulator'];del g['qpos'];g['qpos']=h5py.SoftLink('/frames/000009/simulator/qpos')
  self.f.mutate(change);self.assertEqual(self.result().status,'invalid')
 def test_deterministic_serialization(self):self.assertEqual(canonical(self.result()),canonical(self.result()))
 def test_typed_bridge_preserves_provenance_and_unknown_truth(self):
  r=self.result();records=observations(r);self.assertTrue(records)
  for e in records:
   self.assertEqual(e.kind,'direct_measurement');self.assertEqual(e.truth,Truth.UNKNOWN);self.assertIsInstance(e.payload,Measurement);self.assertEqual(e.source_ref,'sha256:'+r.source_hashes['trajectory.h5']['sha256']);self.assertIsNone(e.uncertainty.temporal)
 def test_root_height_jump_cannot_create_event(self):
  self.f.mutate(lambda h:h['frames/000010/simulator/qpos/value'].__setitem__(18,-1000));r=self.result();self.assertFalse(r.physical_safety_conclusion);self.assertFalse(r.empirical_admission_enabled);self.assertEqual(r.inferred_events,());self.assertEqual(r.checker_judgments,());self.assertEqual(r.evidence_records,())
 def test_heldout_episode_rejected(self):self.assertEqual(read(self.f.root,4).status,'unsupported')
 def test_custom_real_contract_rejected(self):self.assertEqual(read(self.f.root,0,expected=self.f.expected).status,'unsupported')
 def test_invalid_result_has_no_bridge(self):
  self.f.mutate(lambda h:h['frames/000010/simulator/qpos/value'].__setitem__(0,np.nan));self.assertEqual(observations(self.result()),())
class Development(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.results={e:read(REAL,e,[0,10]) for e in (0,1,2,14)}
 def test_four_hash_bound_executions(self):
  for ep,r in self.results.items():
   with self.subTest(ep=ep):self.assertEqual(r.status,'verified_measurements',[(d.code,d.frame) for d in r.diagnostics[:5]]);self.assertFalse(r.synthetic);self.assertEqual(len(r.source_hashes),11)
 def test_complete_saved_measurement_projection(self):
  self.assertEqual(sum(len(r.coverage['validated']) for r in self.results.values()),1312)
  for r in self.results.values():self.assertEqual(r.coverage['missing'],[]);self.assertEqual(r.coverage['invalid'],[]);self.assertEqual(r.coverage['negative_certificates'],[])
 def test_native_pose_contact_and_camera_fields(self):
  for r in self.results.values():
   f=r.frames[1];self.assertEqual(len(f.object_bindings),5);self.assertEqual(len(f.cameras),2);self.assertTrue(f.contact_bundle.complete)
   self.assertTrue(any(c.measurement.quantity=='raw_observation:robot0_gripper_qpos' for c in f.channels));self.assertEqual(len(r.native_geometry['geometries']),161)
   self.assertTrue(all(c.normal is None and c.force is None for c in f.contacts))
 def test_no_empirical_judgment(self):
  for r in self.results.values():self.assertFalse(r.empirical_admission_enabled);self.assertFalse(r.physical_safety_conclusion);self.assertEqual(r.checker_judgments,());self.assertEqual(r.inferred_events,())
class Additional(unittest.TestCase):
 setUp=Synthetic.setUp
 result=Synthetic.result
 codes=Synthetic.codes
 def test_mixed_joint_units_are_not_meters(self):
  r=self.result();q=next(c for c in r.frames[0].channels if c.measurement.quantity=='simulator:qpos')
  self.assertEqual(q.measurement.unit,'native_model_channel_units');self.assertNotEqual(q.frame.id,'MuJoCo_world')
 def test_raw_observable_frame_has_no_world_claim(self):
  r=read(REAL,0,[10]);raw=[c for c in r.frames[0].channels if c.measurement.quantity.startswith('raw_observation:')]
  self.assertTrue(raw);self.assertTrue(all(c.frame.id=='raw_observable_frame_unverified' for c in raw));self.assertTrue(all(c.measurement.unit=='native_observable_units_and_convention_unverified' for c in raw))
 def test_external_dataset_rejected_before_read(self):
  def change(h):
   g=h['frames/000010/simulator/qpos'];del g['value'];g.create_dataset('value',shape=(65,),dtype=np.float64,external=[('/no_external_source_read.bin',0,h5py.h5f.UNLIMITED)])
  self.f.mutate(change);self.assertEqual(self.result().status,'invalid')
 def test_cli_cannot_write_to_source_tree(self):
  from evaluation.r1_v4.libero_measurement_reader.__main__ import main
  with self.assertRaises(SystemExit):main(['--root',str(REAL),'--episode','4','--output',str(REAL/'forbidden.json')])
  self.assertFalse((REAL/'forbidden.json').exists())
 def test_cli_creates_new_output_and_refuses_overwrite(self):
  from evaluation.r1_v4.libero_measurement_reader.__main__ import main
  dest=self.f.root/'outside-source-output.json'
  self.assertEqual(main(['--root',str(REAL),'--episode','4','--output',str(dest)]),1)
  before=dest.read_bytes()
  with self.assertRaises(FileExistsError):main(['--root',str(REAL),'--episode','4','--output',str(dest)])
  self.assertEqual(dest.read_bytes(),before)
class StateConsistency(unittest.TestCase):
 setUp=Synthetic.setUp
 result=Synthetic.result
 def test_flattened_endpoint_disagreement(self):
  self.f.mutate(lambda h:h['frames/000010/simulator/flattened/value'].__setitem__(1,1));r=self.result();self.assertEqual(r.status,'invalid');self.assertTrue(any(d.code=='flattened_endpoint_state_mismatch' for d in r.diagnostics))
 def test_initial_state_disagreement(self):
  self.f.mutate(lambda h:h['benchmark_initial_state/value'].__setitem__(1,1));self.assertEqual(self.result().status,'invalid')
 def test_reader_code_hash_binding(self):
  from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha
  from evaluation.r1_v4.libero_measurement_reader.reader import HERE
  r=self.result();self.assertEqual(r.reader_binding['files']['reader.py'],sha(HERE/'reader.py'))
 def test_flattened_is_endpoint_phase(self):
  c=next(c for c in self.result().frames[0].channels if c.measurement.quantity=='simulator:flattened');self.assertEqual(c.phase,'endpoint_state')
 def test_unexposed_fields_remain_named(self):
  self.f.mutate(lambda h:h['frames/000010/simulator'].create_group('unimplemented_channel'))
  r=self.result();self.assertEqual(r.status,'verified_measurements');self.assertIn('unimplemented_channel',r.metadata['field_inventory']['unexposed_simulator'])
