import unittest,tempfile,json,sqlite3,copy
from pathlib import Path
from dataclasses import replace
import numpy as np,h5py
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import digest,canonical
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import CHANNELS,WORK,HERE,ChannelStore,contract,sample
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.retrieve import ChannelQuery,retrieve

class Contracts(unittest.TestCase):
 def test_selection_exactly_matches_contracts(self):self.assertEqual(set(CHANNELS),set(json.loads((HERE/'CHANNEL_SELECTION.json').read_text())['channels']))
 def test_no_derived_or_spatial_contracts(self):
  for c in CHANNELS:
   k=contract(c);self.assertEqual(k['origin'],'direct_recording');self.assertFalse(k['physical_claims']);self.assertNotEqual(k['coordinate_frame'],'MuJoCo_world')
 def test_unverified_units_are_null(self):
  for c in CHANNELS:
   if c!='simulator.ncon':self.assertIsNone(contract(c)['units'])
 def test_missing_sample_abstains(self):self.assertEqual(sample(None,'simulator.ncon'),(None,'missing_dataset'))
 def decode(self,value,channel):
  with tempfile.TemporaryDirectory(dir=WORK) as tmp:
   with h5py.File(Path(tmp)/'fixture.h5','w') as f:return sample(f.create_dataset('value',data=value),channel)
 def test_count_negative_abstains(self):self.assertEqual(self.decode(-1,'simulator.ncon')[1],'invalid_count')
 def test_count_float_abstains(self):self.assertEqual(self.decode(2.,'simulator.ncon')[1],'invalid_count')
 def test_count_scalar_zero(self):self.assertEqual(self.decode(0,'simulator.ncon')[0],0)
 def test_bad_shape_abstains(self):self.assertEqual(self.decode([1.,2.,3.],'raw.robot0_gripper_qpos')[1],'unsupported_shape')
 def test_nan_abstains(self):self.assertEqual(self.decode([1.,np.nan],'raw.robot0_gripper_qpos')[1],'invalid_numeric_value')
 def test_infinity_abstains(self):self.assertEqual(self.decode([1.,np.inf],'raw.robot0_gripper_qpos')[1],'invalid_numeric_value')
 def test_string_abstains(self):self.assertEqual(self.decode([b'a',b'b'],'raw.robot0_gripper_qpos')[1],'invalid_numeric_value')
 def test_float32_preserved(self):
  a,reason=self.decode(np.array([1.,2.],dtype=np.float32),'raw.robot0_gripper_qpos');self.assertIsNone(reason);self.assertEqual(a.dtype,np.dtype('float32'))
 def test_source_cache_invalidates_after_mutation(self):
  obj=ChannelStore.__new__(ChannelStore);obj.hash_cache={}
  with tempfile.TemporaryDirectory(dir=WORK) as tmp:
   p=Path(tmp)/'source';p.write_bytes(b'one');expected=sha(p);obj.verify_file(p,expected);p.write_bytes(b'two')
   with self.assertRaises(ValueError):obj.verify_file(p,expected)

class Retrieval(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.db=ChannelStore(WORK/'expanded.sqlite');cls.e=cls.db.db.execute('select execution from rag_channel_jobs order by execution limit 1').fetchone()[0];cls.b=cls.db.binding(cls.e);cls.q=ChannelQuery(cls.e,task_id=cls.b['task_id'],variant_id=cls.b['variant_id'],channel_id='raw.robot0_gripper_qpos',interval=(0,0))
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def status(self,**kw):return retrieve(self.db,replace(self.q,**kw))['status']
 def test_exact_initial_values(self):
  r=retrieve(self.db,self.q);self.assertEqual(r['status'],'ok');item=r['results'][0]
  with h5py.File(item['record']['source_path']) as f:self.assertTrue(np.array_equal(item['samples'][0]['value'],f[item['samples'][0]['source_selector']][()]))
 def test_metadata_query_has_no_full_arrays(self):
  r=retrieve(self.db,replace(self.q,interval=None));self.assertEqual(r['status'],'ok');self.assertEqual(r['results'][0]['samples'],[])
 def test_wrong_task(self):self.assertEqual(self.status(task_id='bad'),'invalid_query_scope')
 def test_wrong_variant(self):self.assertEqual(self.status(variant_id='bad'),'invalid_query_scope')
 def test_wrong_execution(self):self.assertEqual(self.status(execution_id='bad'),'unknown_execution')
 def test_wrong_object(self):self.assertEqual(self.status(object_id='butter_1'),'no_matching_channel_record')
 def test_no_world_frame(self):self.assertEqual(self.status(coordinate_frame='MuJoCo_world'),'unsupported_coordinate_frame')
 def test_no_radians(self):self.assertEqual(self.status(units='rad'),'unsupported_units')
 def test_no_seconds(self):self.assertEqual(self.status(temporal_domain='seconds'),'unsupported_temporal_domain')
 def test_no_derived(self):self.assertEqual(self.status(origin='derived'),'unsupported_origin')
 def test_no_main_table_substitution(self):self.assertEqual(self.status(channel_id='logical_main_table_pose'),'unsupported_channel')
 def test_no_eef_world_substitution(self):self.assertEqual(self.status(channel_id='raw_eef_world_pose'),'unsupported_channel')
 def test_no_implicit_execution(self):self.assertEqual(self.status(execution_id=''),'invalid_query_scope')
 def test_no_boolean_frame_index(self):self.assertEqual(self.status(interval=(True,True)),'invalid_query_scope')
 def test_no_negative_frame(self):self.assertEqual(self.status(interval=(-1,2)),'invalid_query_scope')
 def test_no_inverted_window(self):self.assertEqual(self.status(interval=(5,2)),'invalid_query_scope')
 def test_bounded_window(self):self.assertEqual(self.status(interval=(0,5000)),'invalid_query_scope')
 def test_no_future_frame(self):self.assertEqual(self.status(interval=(100000,100000)),'no_matching_channel_record')
 def test_no_boolean_limit(self):self.assertEqual(self.status(limit=True),'invalid_query_scope')
 def test_all_reserved_ids_excluded(self):
  ids=self.db.db.execute("select execution from rag_scope_status where status='excluded_reserved'").fetchall();self.assertEqual(len(ids),60)
  for e, in ids:self.assertEqual(self.status(execution_id=e),'excluded_reserved')
 def test_all_preflight_ids_excluded(self):
  ids=self.db.db.execute("select execution from rag_scope_status where status='excluded_preflight'").fetchall();self.assertEqual(len(ids),38)
  for e, in ids:self.assertEqual(self.status(execution_id=e),'excluded_preflight')
 def test_fts_field_retrieval(self):self.assertEqual(self.status(text='gripper position'),'ok')
 def test_count_has_no_object_support(self):
  r=retrieve(self.db,replace(self.q,channel_id='simulator.ncon'));self.assertEqual(r['status'],'ok');self.assertFalse(r['safety_claim_verified']);self.assertEqual(r['results'][0]['record']['object_id'],'*')


class RecordIntegrity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.real=ChannelStore(WORK/'expanded.sqlite');cls.execution,body=cls.real.db.execute('select execution,body from rag_channel_records order by execution limit 1').fetchone();cls.record=json.loads(body);cls.binding=cls.real.binding(cls.execution)
 @classmethod
 def tearDownClass(cls):cls.real.close()
 def forged(self,change,resign=True):
  record=copy.deepcopy(self.record);change(record)
  if resign:record['id']='channel:'+digest({k:v for k,v in record.items() if k!='id'})
  class Proxy:
   def __init__(self,real,binding,record):
    self.real=real;self.b=binding;self.record=record
   def binding(self,e):return self.b
   def verify_binding(self,b):self.real.verify_binding(b)
   def verify_file(self,p,h):self.real.verify_file(p,h)
  proxy=Proxy(self.real,self.binding,record);proxy.db=sqlite3.connect(':memory:');proxy.db.executescript('create table rag_scope_status(execution,status);create table rag_channel_records(id,execution,channel,object_id,body);create table evidence(execution_id,kind,body);')
  proxy.db.execute('insert into rag_scope_status values(?,?)',(self.execution,'indexed'));proxy.db.execute('insert into rag_channel_records values(?,?,?,?,?)',(record['id'],self.execution,record['channel_id'],record['object_id'],canonical(record).decode()))
  q=ChannelQuery(self.execution,channel_id=record['channel_id']);result=retrieve(proxy,q);proxy.db.close();return result
 def test_unsigned_numeric_digest_mutation(self):self.assertEqual(self.forged(lambda r:r.update(sample_digest='bad'),False)['status'],'invalid_source_or_mapping')
 def test_signed_wrong_execution_body(self):self.assertEqual(self.forged(lambda r:r.update(execution_id='other'))['status'],'invalid_source_or_mapping')
 def test_signed_wrong_variant_body(self):self.assertEqual(self.forged(lambda r:r.update(variant_id='other'))['status'],'invalid_source_or_mapping')
 def test_signed_fabricated_units(self):self.assertEqual(self.forged(lambda r:r['contract'].update(units='N'))['status'],'invalid_source_or_mapping')
 def test_signed_derived_relabel(self):self.assertEqual(self.forged(lambda r:r.update(derived=True))['status'],'invalid_source_or_mapping')
 def test_signed_world_relabel(self):self.assertEqual(self.forged(lambda r:r['contract'].update(coordinate_frame='MuJoCo_world'))['status'],'invalid_source_or_mapping')
 def test_signed_wrong_source_association(self):self.assertEqual(self.forged(lambda r:None)['status'],'invalid_source_or_mapping')

class SpatialAudit(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=json.loads((WORK/'SPATIAL_AUDIT.json').read_text())
 def test_all_executions_and_variants(self):self.assertEqual(len(self.rows),432);self.assertEqual(len({r['variant_id'] for r in self.rows}),104)
 def test_literal_name_audit_does_not_invent_alias(self):
  self.assertTrue(all(r['main_table_status'].startswith('unresolved') for r in self.rows));self.assertTrue(all(not any(r['exact_main_table'].values()) for r in self.rows))
 def test_exact_recorded_roots(self):self.assertTrue(all(b['exact_root_verified'] for r in self.rows for b in r['logical_bindings']))
 def test_same_phase_positions_exact(self):
  checks=[c for r in self.rows for c in r['phase_position_checks']];self.assertEqual(len(checks),3064);self.assertTrue(all(c['position_error']==0 for c in checks))


class SparseSeries(unittest.TestCase):
 def test_missing_middle_sample_has_no_interpolation_or_shift(self):
  real=ChannelStore(WORK/'expanded.sqlite')
  try:
   execution,body=real.db.execute("select execution,body from rag_channel_records where channel='raw.robot0_gripper_qpos' limit 1").fetchone();record=json.loads(body);binding=real.binding(execution)
   with tempfile.TemporaryDirectory(dir=WORK) as tmp:
    path=Path(tmp)/'sparse.h5'
    with h5py.File(path,'w') as f:
     for i in (0,1,2):f.create_group('frames/'+str(i).zfill(6))
     for i in (0,2):f.create_dataset('frames/'+str(i).zfill(6)+'/raw_observation/robot0_gripper_qpos/value',data=np.array([i,i+1],dtype=np.float64))
    record.update(source_path=str(path),source_sha256=sha(path),valid_indices=[0,2],invalid_samples={'1':'missing_dataset'},frame_keys={str(i):str(i).zfill(6) for i in (0,1,2)},sample_count=2);record['id']='channel:'+digest({k:v for k,v in record.items() if k!='id'})
    class Proxy:
     def binding(self,e):return binding
     def verify_binding(self,b):real.verify_binding(b)
     def verify_file(self,p,h):real.verify_file(p,h)
    proxy=Proxy();proxy.db=sqlite3.connect(':memory:');proxy.db.executescript('create table rag_scope_status(execution,status);create table rag_channel_records(id,execution,channel,object_id,body);create table evidence(execution_id,kind,body);');proxy.db.execute('insert into rag_scope_status values(?,?)',(execution,'indexed'));proxy.db.execute('insert into rag_channel_records values(?,?,?,?,?)',(record['id'],execution,record['channel_id'],record['object_id'],canonical(record).decode()));proxy.db.execute('insert into evidence values(?,?,?)',(execution,'raw_measurement',json.dumps(dict(source_path=str(path),source_sha256=sha(path)))))
    q=ChannelQuery(execution,channel_id=record['channel_id'],interval=(1,1));self.assertEqual(retrieve(proxy,q)['status'],'no_matching_channel_record')
    r=retrieve(proxy,replace(q,interval=(0,2)));self.assertEqual([s['saved_frame_index'] for s in r['results'][0]['samples']],[0,2]);self.assertEqual(r['results'][0]['samples'][1]['value'],[2.,3.]);self.assertIsNone(r['results'][0]['samples'][0]['control_step']);self.assertEqual(r['results'][0]['samples'][0]['coordinate_frame'],'uninterpreted_raw_array');proxy.db.close()
  finally:real.close()


class MainTableBinding(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.audit=json.loads((WORK/'MAIN_TABLE_AUDIT.json').read_text())
 def test_bounded_verified_scope(self):self.assertEqual(self.audit['status_counts'],{'verified_symbolic_alias':147,'not_applicable_other_recorded_workspace':285});self.assertEqual(self.audit['verified_variants'],98)
 def test_hash_bound_producer_chain(self):
  for r in self.audit['rows']:
   if r['status']=='verified_symbolic_alias':self.assertTrue(r['producer_attested'] and r['source_chain_verified']);self.assertTrue(all(s['actual_sha256']==s['expected_sha256'] for s in r['sources']))
 def test_exact_native_geometry(self):
  for r in self.audit['rows']:
   if r['exact_mapping']:
    m=json.loads(Path(r['mapping_path']).read_text());m=m.get('mapping',m);identity=r['exact_mapping'];geom=m['geometries'][identity['geom_id']];self.assertEqual(geom['name'],'table_collision');self.assertEqual(geom['owner_body_id'],identity['body_id']);self.assertEqual(m['body_names'][identity['body_id']],'table')
 def test_no_spatial_samples_or_support_inference(self):self.assertTrue(all(not r['physical_support_inferred'] and not r['spatial_samples_admitted'] for r in self.audit['rows']))
 def test_wrong_domain_never_borrows_table(self):
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.main_table_audit import decide
  for problem in ('libero_floor_manipulation','libero_living_room_tabletop_manipulation'):self.assertEqual(decide(problem,{'table':['main_table']},True,True,True,True),'not_applicable_other_recorded_workspace')
 def test_wrong_fixture_never_borrows_name(self):
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.main_table_audit import decide
  self.assertEqual(decide('libero_tabletop_manipulation',{'table':['near_main_table']},True,True,True,True),'not_applicable_other_recorded_workspace')
 def test_missing_attestation_blocks_mapping(self):
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.main_table_audit import decide
  self.assertEqual(decide('libero_tabletop_manipulation',{'table':['main_table']},False,True,True,True),'unresolved_producer_hash_binding')
 def test_incomplete_code_chain_blocks_mapping(self):
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.main_table_audit import decide
  self.assertEqual(decide('libero_tabletop_manipulation',{'table':['main_table']},True,False,True,True),'unresolved_code_chain')
 def test_wrong_xml_or_native_map_blocks_mapping(self):
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.main_table_audit import decide
  for xml,native in ((False,True),(True,False)):self.assertEqual(decide('libero_tabletop_manipulation',{'table':['main_table']},True,True,xml,native),'unresolved_variant_binding')

if __name__=='__main__':unittest.main()
