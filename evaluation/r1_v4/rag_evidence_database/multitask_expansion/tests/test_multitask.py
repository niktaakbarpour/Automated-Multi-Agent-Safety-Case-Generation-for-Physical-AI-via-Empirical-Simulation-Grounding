import unittest,os
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.provenance import load,canonical
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.plan import HERE,DEST
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.profile import PREFIX,folder,approved_profile
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.build import BASE,BASE_SHA
from evaluation.r1_v4.libero_measurement_reader.reader import read

class MultiTaskTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.db=Store(os.environ['RAG_MULTITASK_DB']);cls.plan=load(HERE/'SOURCE_PLAN.json');cls.records=cls.db.records();cls.tasks=sorted(cls.plan['tasks']);cls.ids={r.id for r in cls.records}
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def each(self):
  for task in self.tasks:
   data=self.plan['tasks'][task];entry=data['executions'][0];yield task,data,entry
 def test_four_independent_profiles(self):self.assertEqual(len(self.tasks),4);self.assertEqual(len({sha(folder(t)/'NATIVE_PROFILE.json') for t in self.tasks}),4)
 def test_source_count(self):self.assertEqual(len(self.plan['files']),1772)
 def test_batch_count(self):self.assertEqual(sum(len(t['executions']) for t in self.plan['tasks'].values()),196)
 def test_reserved_exclusion(self):self.assertFalse({e['execution_id'] for t in self.plan['tasks'].values() for e in t['executions']} & set(self.plan['excluded_ids']))
 def test_total_executions(self):self.assertEqual(len({r.execution_id for r in self.records}),285)
 def test_unique_records(self):self.assertEqual(len(self.ids),len(self.records))
 def test_baseline_retained(self):
  old=Store(BASE)
  try:self.assertTrue({r.id for r in old.records()}<=self.ids);self.assertEqual(sha(BASE),BASE_SHA)
  finally:old.close()
 def test_native_ids_complete(self):
  for task,data,e in self.each():
   native=load(folder(task)/'NATIVE_PROFILE.json');self.assertEqual([g['native_geom_id'] for g in native['mapping']['geometries']],list(range(native['mapping']['native_geom_count'])))
 def test_unknown_task_denied(self):
  with self.assertRaises(ValueError):approved_profile(PREFIX+'object/task_99',DEST,1)
 def test_wrong_root_denied(self):
  with self.assertRaises(ValueError):approved_profile(PREFIX+self.tasks[0],DEST/'other',1)
 def test_reserved_zero_denied(self):
  for task in self.tasks:
   with self.assertRaises(ValueError):approved_profile(PREFIX+task,DEST,0)
 def test_new_profiles_real(self):
  for task,data,e in self.each():
   result=read(DEST,1,[0,10],task_profile=PREFIX+task);self.assertEqual(result.status,'verified_measurements');self.assertFalse(result.synthetic);self.assertFalse(result.empirical_admission_enabled);self.assertEqual(result.reader_version,'1.3.0')
 def test_reject_synthetic_injection(self):self.assertNotEqual(read(DEST,1,[0],task_profile=PREFIX+self.tasks[0],synthetic=True).status,'verified_measurements')
 def test_queries_correct(self):
  for task,data,e in self.each():
   result=search(self.db,Query(execution_id=e['execution_id'],object_id=data['objects'][0],evidence_types=('object_pose',),interval=(10,10),stratum='corpus_expansion'));self.assertEqual(result['matching_count'],1);self.assertFalse(result['safety_claim_verified'])
 def test_wrong_task_isolated(self):
  for task,data,e in self.each():self.assertFalse(search(self.db,Query(execution_id=e['execution_id'],task_id='not-this-task'))['results'])
 def test_wrong_object_isolated(self):
  for task,data,e in self.each():self.assertFalse(search(self.db,Query(execution_id=e['execution_id'],object_id='nonexistent_object'))['results'])
 def test_development_stratum_separate(self):
  for task,data,e in self.each():self.assertFalse(search(self.db,Query(execution_id=e['execution_id'],stratum='development'))['results'])
 def test_geometry_not_admitted(self):
  for task,data,e in self.each():self.assertFalse(search(self.db,Query(execution_id=e['execution_id'],evidence_types=('native_geometry',),capabilities={'geometry_admission':'VERIFIED'}))['results'])
 def test_camera_alignment_unsupported(self):
  for task,data,e in self.each():self.assertFalse(search(self.db,Query(execution_id=e['execution_id'],evidence_types=('camera_reference',),capabilities={'exposure_alignment':'VERIFIED'}))['results'])
 def test_missing_frames_preserved(self):
  for task,data,e in self.each():
   result=search(self.db,Query(execution_id=e['execution_id'],object_id=data['objects'][0],evidence_types=('contact','object_pose'),interval=(0,e['frames'])));self.assertTrue(all(v['missing_intervals']==[[e['frames'],e['frames']]] for v in result['coverage'].values()))
 def test_no_physical_labels(self):self.assertTrue(all(r.provenance.get('physical_truth') in (None,'U') for r in self.records))
 def test_no_human_claims(self):self.assertFalse(any(r.kind=='human_reference_judgment' for r in self.records))
 def test_new_data_use_explicit(self):
  new={e['execution_id'] for t in self.plan['tasks'].values() for e in t['executions']};self.assertTrue(all(r.provenance['development_only'] is False for r in self.records if r.execution_id in new))
 def test_query_reproducible(self):
  e=self.plan['tasks'][self.tasks[0]]['executions'][0];q=Query(execution_id=e['execution_id'],evidence_types=('execution_metadata',));self.assertEqual(canonical(search(self.db,q)),canonical(search(self.db,q)))
 def test_missing_measurement_type_preserved(self):
  for task,data,e in self.each():
   r=search(self.db,Query(execution_id=e['execution_id'],object_id=data['objects'][0],evidence_types=('contact_force',),interval=(10,10)));self.assertEqual(r['coverage']['contact_force']['missing_intervals'],[[10,10]]);self.assertFalse(r['measurement_records_valid']);self.assertFalse(r['safety_claim_verified'])
 def test_timestamp_frame_not_spatial(self):
  for task,data,e in self.each():
   r=search(self.db,Query(execution_id=e['execution_id'],object_id=data['objects'][0],evidence_types=('timestamp',),interval=(10,10)));self.assertEqual(r['results'][0]['record']['coordinate_frame'],'not_applicable_timestamp')
 def test_initial_support_gate_not_available(self):
  for task,data,e in self.each():self.assertFalse(search(self.db,Query(execution_id=e['execution_id'],evidence_types=('contact',),capabilities={'initial_support':'VERIFIED'}))['results'])
 def test_baseline_rows_preserved_exactly(self):
  from evaluation.r1_v4.provenance import digest
  old=Store(BASE)
  try:
   for table,key in [('evidence','id'),('rag_units','id'),('rag_catalog','execution'),('rag_jobs','execution')]:
    expected={r[0]:digest(r) for r in old.db.execute('SELECT '+key+',* FROM '+table)};actual={r[0]:digest(r) for r in self.db.db.execute('SELECT '+key+',* FROM '+table) if r[0] in expected};self.assertEqual(actual,expected)
  finally:old.close()
 def test_task_instruction_sources_distinct(self):
  from evaluation.r1_v4.rag_evidence_database.multitask_expansion.task_declarations import validate
  report=validate();self.assertTrue(report['passed']);self.assertTrue(all(not t['literal_language_match'] and not t['text_equivalence_verified'] for t in report['tasks']))
 def test_every_new_raw_unit_has_task_specific_mapping(self):
  scope={e['execution_id']:(task,e) for task,data in self.plan['tasks'].items() for e in data['executions']};native={task:load(folder(task)/'NATIVE_PROFILE.json') for task in self.tasks};hashes={task:sha(folder(task)/'NATIVE_PROFILE.json') for task in self.tasks}
  for r in self.records:
   if r.kind!='raw_measurement' or r.execution_id not in scope:continue
   task,e=scope[r.execution_id];identity=native[task]['objects'][r.object_id];self.assertEqual(r.provenance['body_id'],identity['body_id']);self.assertEqual(r.provenance['collision_geom_ids'],identity['collision_geom_ids']);self.assertEqual(r.provenance['native_map_sha256'],hashes[task]);self.assertEqual(r.task_id,self.plan['tasks'][task]['task']['task_id']);self.assertEqual(r.source_path,str(DEST/task/f"episode_{e['episode']:03d}"/'trajectory.h5'));self.assertLess(r.interval[1],e['frames']);self.assertEqual(r.capability['physical_checking'],'BLOCKED_ON_EVIDENCE')
 def test_read_only_cli_query(self):
  import tempfile,subprocess,sys
  from evaluation.r1_v4.provenance import write_new,strict_loads
  e=self.plan['tasks'][self.tasks[0]]['executions'][0]
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'query.json';write_new(path,{'execution_id':e['execution_id'],'evidence_types':['execution_metadata']});p=subprocess.run([sys.executable,'-S','-m','evaluation.r1_v4.rag_evidence_database.multitask_expansion.cli','query','--database',os.environ['RAG_MULTITASK_DB'],'--query',str(path)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);value=strict_loads(p.stdout);self.assertEqual(value['matching_count'],1);self.assertFalse(value['safety_claim_verified'])
 def test_cli_rejects_ignored_text_flag(self):
  import subprocess,sys
  p=subprocess.run([sys.executable,'-S','-m','evaluation.r1_v4.rag_evidence_database.multitask_expansion.cli','check','--database',os.environ['RAG_MULTITASK_DB'],'--text','ignored'],capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertIn('--text is semantic only',p.stderr)
