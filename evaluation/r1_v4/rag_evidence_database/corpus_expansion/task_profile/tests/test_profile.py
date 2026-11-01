import os,unittest,tempfile
from pathlib import Path
from dataclasses import replace,asdict
from evaluation.r1_v4.provenance import load,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.libero_measurement_reader.reader import read
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.profile import NAME,approved_profile
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.plan import HERE,DEST
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.build import BASE,BASE_SHA

class NewTaskTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.path=os.environ['RAG_NEW_TASK_DB'];cls.db=Store(cls.path);cls.records=cls.db.records();cls.plan=load(HERE/'SOURCE_PLAN.json');cls.native=load(HERE/'NATIVE_PROFILE.json');cls.execution=cls.plan['executions'][0]['execution_id']
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def test_new_task_is_explicit(self):self.assertEqual(self.plan['task']['partition'],'object/task_02');self.assertEqual(len(self.plan['executions']),49)
 def test_reservation_exclusion(self):self.assertFalse({r['execution_id'] for r in self.plan['executions']} & set(self.plan['excluded_ids']))
 def test_correct_new_dimensions(self):self.assertEqual(self.native['shapes']['qpos'],[58]);self.assertEqual(self.native['shapes']['body_xpos'],[26,3]);self.assertNotEqual(self.native['surface_ids'],list(range(10,16)))
 def test_complete_native_mapping(self):self.assertEqual([r['native_geom_id'] for r in self.native['mapping']['geometries']],list(range(161)));self.assertNotEqual(self.native['objects']['cream_cheese_1']['body_id'],22)
 def test_source_profile_real(self):
  r=read(DEST,1,[0,10],task_profile=NAME);self.assertEqual(r.status,'verified_measurements');self.assertFalse(r.synthetic);self.assertFalse(r.empirical_admission_enabled);self.assertEqual(r.reader_version,'1.2.0')
 def test_no_synthetic_injection(self):self.assertNotEqual(read(DEST,1,task_profile=NAME,synthetic=True).status,'verified_measurements')
 def test_old_default_rejects_new_task(self):self.assertNotEqual(read(DEST,1,[0]).status,'verified_measurements')
 def test_excluded_pilot_zero_denied(self):
  with self.assertRaises(ValueError):approved_profile(NAME,DEST,0)
 def test_unknown_profile(self):
  with self.assertRaises(ValueError):approved_profile('other',DEST,1)
 def test_wrong_source_root(self):
  with self.assertRaises(ValueError):approved_profile(NAME,DEST/'other',1)
 def test_eighty_nine_executions(self):self.assertEqual(len({r.execution_id for r in self.records}),89)
 def test_no_duplicate_ids(self):self.assertEqual(len(self.records),len({r.id for r in self.records}));self.assertEqual(len(self.records),21791)
 def test_baseline_preserved(self):
  self.assertEqual(sha(BASE),BASE_SHA);old=Store(BASE)
  try:self.assertTrue({r.id for r in old.records()} <= {r.id for r in self.records})
  finally:old.close()
 def test_strata_separated(self):
  rows=dict(self.db.db.execute('SELECT stratum,count(*) FROM rag_units GROUP BY stratum'));self.assertEqual(rows,{'development':11830,'corpus_expansion':9961})
  self.assertTrue(all(r.provenance['development_only'] is False for r in self.records if r.execution_id==self.execution))
 def test_source_query(self):
  result=search(self.db,Query(execution_id=self.execution,object_id='salad_dressing_1',evidence_types=('object_pose',),interval=(10,10),stratum='corpus_expansion'));self.assertEqual(result['matching_count'],1);self.assertFalse(result['safety_claim_verified'])
 def test_stratum_filter_blocks_leak(self):
  self.assertFalse(search(self.db,Query(execution_id=self.execution,stratum='development'))['results'])
 def test_geometry_not_physical(self):
  result=search(self.db,Query(execution_id=self.execution,evidence_types=('native_geometry',),capabilities={'geometry_admission':'VERIFIED'}));self.assertFalse(result['results'])
 def test_task_instruction(self):
  result=search(self.db,Query(execution_id=self.execution,evidence_types=('task_instruction',),text='salad dressing basket'));self.assertEqual(result['matching_count'],1)
 def test_missing_terminal(self):
  entry=self.plan['executions'][0];last=entry['frames']-1;r=search(self.db,Query(execution_id=self.execution,object_id='salad_dressing_1',evidence_types=('contact','object_pose'),interval=(0,last+1),limit=1));self.assertTrue(all(c['missing_intervals']==[[last+1,last+1]] for c in r['coverage'].values()))
 def test_old_query_id_compatible(self):
  q=Query(execution_id=self.execution,evidence_types=('execution_metadata',));value=asdict(q);value.pop('stratum');self.assertEqual(search(self.db,q)['query_id'],'query:'+digest(value))
 def test_no_ai_promotions(self):self.assertEqual(sum(r.kind=='ai_reference_judgment' for r in self.records),10);self.assertFalse(any(r.kind=='human_reference_judgment' for r in self.records))
