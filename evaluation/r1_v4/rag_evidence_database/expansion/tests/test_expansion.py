"""Approved development expansion, no physical outcomes or held-out labels."""
import unittest,os
from pathlib import Path
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.libero_measurement_reader.reader import read
from evaluation.r1_v4.rag_evidence_database.expansion.profile import ROOT,NAME,HERE,approved_profile
from evaluation.r1_v4.rag_evidence_database.expansion.build import BASELINE,BASE_SHA

class ExpansionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.db=Store(os.environ.get('RAG_EXPANSION_DB','/disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite'))
  cls.records=cls.db.records();cls.profile=load(HERE/'VALIDATED_SOURCE_PROFILE.json')
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def test_baseline_hash(self):self.assertEqual(sha(BASELINE),BASE_SHA)
 def test_baseline_evidence_preserved(self):
  old=Store(BASELINE)
  try:self.assertTrue({r.id for r in old.records()} <= {r.id for r in self.records})
  finally:old.close()
 def test_exact_development_ids(self):
  split=load(REPO/'reports/fall_review_v2_20261016/proposed_split.json');self.assertEqual({r.execution_id for r in self.records},set(split['development']))
 def test_no_heldout_ids(self):
  frozen={r['run_id'] for r in load(REPO/'evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json')['cases']};self.assertFalse({r.execution_id for r in self.records}&frozen)
 def test_default_reader_still_bounded(self):self.assertEqual(read(ROOT,3,[0]).status,'unsupported')
 def test_real_profile_not_synthetic(self):
  r=read(ROOT,3,[0,10],development_profile=NAME);self.assertEqual(r.status,'verified_measurements');self.assertFalse(r.synthetic);self.assertFalse(r.empirical_admission_enabled);self.assertEqual(r.reader_version,'1.1.0')
 def test_profile_no_injected_contract(self):self.assertNotEqual(read(ROOT,3,[0],development_profile=NAME,expected=[]).status,'verified_measurements')
 def test_unknown_profile_rejected(self):
  with self.assertRaises(ValueError):approved_profile('unapproved',ROOT,3)
 def test_wrong_root_rejected(self):
  with self.assertRaises(ValueError):approved_profile(NAME,ROOT/'other',3)
 def test_frozen_profile_rejected(self):
  split=load(REPO/'reports/fall_review_v2_20261016/proposed_split.json');runs={r['run_id']:r for r in load(REPO/'data/runs.json')['records']};episode=runs[split['held_out'][0]]['episode']
  with self.assertRaises(ValueError):approved_profile(NAME,ROOT,episode)
 def test_sources_verified(self):
  r=load(HERE/'RESTORATION_MANIFEST.json');self.assertEqual(r['freshly_hash_verified'],324);self.assertTrue(all(x['sha256']==x['expected_sha256'] for x in r['files']))
 def test_unique_record_ids(self):self.assertEqual(len(self.records),len({r.id for r in self.records}))
 def test_ai_separate(self):
  ai=[r for r in self.records if r.kind=='ai_reference_judgment'];self.assertEqual(len(ai),10);self.assertTrue(all(r.validation_status=='provisional' for r in ai))
 def test_all_six_types(self):
  for execution in {r.execution_id for r in self.records}:
   self.assertEqual({r.measurement_type for r in self.records if r.execution_id==execution and r.kind=='raw_measurement'},{'contact','object_pose','native_geometry','robot_state','timestamp','camera_reference'})
 def test_new_execution_isolation(self):
  execution=self.profile['executions']['3']['execution_id'];r=search(self.db,Query(execution_id=execution,object_id='cream_cheese_1',evidence_types=('native_geometry',),interval=(10,10)))
  self.assertEqual(r['matching_count'],1);self.assertEqual(r['results'][0]['record']['execution_id'],execution);self.assertFalse(r['safety_claim_verified'])
 def test_gap_after_terminal(self):
  entry=self.profile['executions']['3'];last=entry['frames']-1;r=search(self.db,Query(execution_id=entry['execution_id'],object_id='cream_cheese_1',evidence_types=('contact','object_pose'),interval=(0,last+1),limit=1));self.assertTrue(all(v['missing_intervals']==[[last+1,last+1]] for v in r['coverage'].values()))
 def test_catalog_current_status_overlay(self):
  from evaluation.r1_v4.rag_evidence_database.catalog import catalog_search
  execution=self.profile['executions']['3']['execution_id'];r=catalog_search(self.db,execution)['results'][0]
  self.assertTrue(r['measurement_status_is_historical']);self.assertEqual(r['measurement_status'],'not_indexed');self.assertEqual(r['current_index_job']['status'],'complete');self.assertFalse(r['current_index_job']['source_validation_rechecked_by_catalog'])
