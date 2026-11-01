"""Development integration has known source targets, not safety labels."""
import unittest,os,tempfile
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.rag_evidence_database.catalog import catalog_search
from evaluation.r1_v4.rag_evidence_database.build import populate
from evaluation.r1_v4.evidence_registry_gsn.registry import Registry

class RealDevelopmentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=None;cls.path=os.environ.get('RAG_TEST_DB')
  if not cls.path:
   cls.tmp=tempfile.TemporaryDirectory(dir='/disk/1/data/niktakbr');cls.path=str(Path(cls.tmp.name)/'dev.sqlite');populate(cls.path)
  cls.db=Store(cls.path);cls.execution='libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db'
 @classmethod
 def tearDownClass(cls):
  cls.db.close()
  if cls.tmp:cls.tmp.cleanup()
 def test_all_four_indexed(self):self.assertEqual(self.db.db.execute('SELECT count(*) FROM rag_jobs').fetchone()[0],4)
 def test_record_count(self):self.assertEqual(len(self.db.records()),1360)
 def test_full_saved_frames(self):
  for execution,terminal in [(self.execution,257),('libero_long_openvla_oft_task00_seed1014_trial014_cfafd9ddc3db',530)]:
   r=search(self.db,Query(execution_id=execution,object_id='cream_cheese_1',evidence_types=('object_pose','contact'),interval=(0,terminal+1),limit=1))
   self.assertTrue(all(c['missing_intervals']==[[terminal+1,terminal+1]] for c in r['coverage'].values()))
 def test_task_instruction_search(self):
  r=search(self.db,Query(execution_id=self.execution,evidence_types=('task_instruction',),text='alphabet soup tomato sauce'));self.assertEqual(r['matching_count'],1)
 def test_no_execution_leak(self):
  r=search(self.db,Query(execution_id=self.execution,object_id='ketchup_1',evidence_types=('contact',),interval=(10,10)));self.assertEqual(r['matching_count'],1);self.assertTrue(all(m['record']['execution_id']==self.execution for m in r['results']))
 def test_ai_not_human(self):
  ai=[r for r in self.db.records() if r.kind=='ai_reference_judgment'];self.assertEqual(len(ai),10);self.assertTrue(all(r.validation_status=='provisional' and not r.provenance['human_ground_truth'] for r in ai));self.assertFalse(any(r.kind=='human_reference_judgment' for r in self.db.records()))
 def test_historical_catalog(self):
  self.assertEqual(self.db.db.execute('SELECT count(*) FROM rag_catalog').fetchone()[0],2000)
  result=catalog_search(self.db,self.execution);self.assertEqual(result['results'][0]['status'],'historical_inventory_metadata');self.assertFalse(result['valid_measurements_implied'])
 def test_catalog_text(self):self.assertTrue(catalog_search(self.db,text='alphabet soup')['results'])
 def test_integrity(self):self.assertTrue(self.db.check()['passed'])
 def test_5a_reopens(self):
  r=Registry(self.path)
  try:self.assertEqual(len(r.records()),1360)
  finally:r.close()
