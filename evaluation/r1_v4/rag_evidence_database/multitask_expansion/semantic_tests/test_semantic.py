import os,unittest,sqlite3,tempfile
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.provenance import load,canonical
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder,SemanticIndex,integrity,descriptor
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.plan import HERE

class SemanticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.db=Store(os.environ['RAG_MULTITASK_DB']);cls.encoder=Encoder();cls.sidecar=Path(os.environ['RAG_SEMANTIC_DB']);cls.index=SemanticIndex(cls.sidecar,cls.db,cls.encoder);plan=load(HERE/'SOURCE_PLAN.json');task=next(iter(plan['tasks'].values()));cls.execution=task['executions'][0]['execution_id'];cls.obj=task['objects'][0];cls.query=Query(execution_id=cls.execution,object_id=cls.obj,evidence_types=('object_pose','contact','native_geometry','robot_state','timestamp','camera_reference'),interval=(10,10),stratum='corpus_expansion')
 @classmethod
 def tearDownClass(cls):cls.index.close();cls.db.close()
 def test_integrity(self):self.assertTrue(integrity(self.index)['passed'])
 def test_cpu_only(self):self.assertEqual(self.encoder.binding['device'],'cpu')
 def test_encoder_reproducible(self):self.assertEqual(self.encoder.encode(['object position']).tobytes(),self.encoder.encode(['object position']).tobytes())
 def test_metadata_filters_retained(self):
  r=self.index.retrieve(self.query,'where is object located');self.assertTrue(all(i['record']['execution_id']==self.execution and i['record']['object_id']==self.obj for i in r['results']))
 def test_provenance_unchanged(self):
  core={i['id']:i['record'] for i in search(self.db,self.query)['results']};r=self.index.retrieve(self.query,'which bodies touch');self.assertTrue(all(i['record']==core[i['id']] for i in r['results']))
 def test_no_physical_claims(self):
  r=self.index.retrieve(self.query,'is object safe');self.assertFalse(r['safety_claim_verified']);self.assertFalse(r['empirical_admission_enabled']);self.assertFalse(r['sufficient_for_physical_checking'])
 def test_empty_query_rejected(self):
  with self.assertRaises(ValueError):self.index.retrieve(self.query,'')
 def test_fts_not_conflated(self):
  with self.assertRaises(ValueError):self.index.retrieve(replace(self.query,text='pose'),'location')
 def test_reproducible_rank(self):self.assertEqual(canonical(self.index.retrieve(self.query,'object location')),canonical(self.index.retrieve(self.query,'object location')))
 def test_missing_execution_empty(self):self.assertFalse(self.index.retrieve(replace(self.query,execution_id='missing'),'object position')['results'])
 def test_physical_capability_gate(self):self.assertFalse(self.index.retrieve(replace(self.query,capabilities={'physical_checking':'VERIFIED'}),'object position')['results'])
 def test_broad_query_rejected(self):
  with self.assertRaises(ValueError):self.index.retrieve(Query(execution_id=self.execution),'object position')
 def test_geometry_uncalibrated_preserved(self):
  r=self.index.retrieve(self.query,'geometry');self.assertTrue(all(i['record']['capability']['geometry_admission']=='UNSUPPORTED' for i in r['results'] if i['record']['measurement_type']=='native_geometry'))
 def test_unembedded_document_not_retrieved(self):
  q=Query(execution_id=self.execution,evidence_types=('execution_metadata',));r=self.index.retrieve(q,'execution metadata');self.assertFalse(r['evidence_retrieved']);self.assertTrue(r['source_filter_evidence_retrieved']);self.assertEqual(r['matching_count'],0);self.assertEqual(len(r['unindexed_evidence_ids']),1)
 def test_distinct_query_ids(self):self.assertNotEqual(self.index.retrieve(self.query,'position')['query_id'],self.index.retrieve(self.query,'contact')['query_id'])
 def test_source_version_mismatch(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'copy.sqlite';source=sqlite3.connect(self.sidecar);target=sqlite3.connect(p);source.backup(target);source.close();body=load_json(target.execute('SELECT body FROM meta').fetchone()[0]);body['source_database_sha256']='0'*64
   with target:target.execute('UPDATE meta SET body=?',(canonical(body).decode(),))
   target.close()
   with self.assertRaises(ValueError):SemanticIndex(p,self.db,self.encoder)

def load_json(s):
 from evaluation.r1_v4.provenance import strict_loads
 return strict_loads(s)
