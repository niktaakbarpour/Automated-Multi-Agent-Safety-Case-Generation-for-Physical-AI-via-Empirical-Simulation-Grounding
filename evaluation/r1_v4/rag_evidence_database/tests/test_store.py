import unittest,tempfile,hashlib,sqlite3
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.evidence_registry_gsn.registry import Registry
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.provenance import canonical

class DatabaseTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='/disk/1/data/niktakbr');self.root=Path(self.tmp.name);self.source=self.root/'synthetic.txt';self.source.write_text('synthetic measurement')
  self.r=Record('1.0.0','R1','2.0.0','synthetic','obj','raw_measurement',str(self.source),hashlib.sha256(self.source.read_bytes()).hexdigest(),'/synthetic/pose','object_pose','verified_measurement',{'availability':'VERIFIED','physical':'BLOCKED_ON_EVIDENCE'},'saved_frame_index','frame',(0,3),'MuJoCo_world','synthetic-model','synthetic-benchmark','task','synthetic-producer',True,missing_intervals=((1,1),),uncertainty=('Uncalibrated alignment',),provenance={'synthetic':True,'physical_truth':'U','input_binding_digest':'input'})
  self.db=Store(self.root/'db.sqlite',create=True)
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def add(self,r=None,text='synthetic pose position'):
  r=r or self.r;self.db.put_execution(r.execution_id,r.provenance['input_binding_digest'],[(r,text,'synthetic-parent')])
 def q(self,**kwargs):return search(self.db,Query(**kwargs))
 def test_legacy_reopen(self):
  self.add();r=Registry(self.db.path)
  try:self.assertEqual(r.records()[0].id,self.r.id)
  finally:r.close()
 def test_migrate_preserves_ids(self):
  p=self.root/'old.sqlite';r=Registry(p,create=True);r.add([self.r]);r.close();s=Store(p,writable=True)
  try:self.assertEqual(s.records()[0].id,self.r.id)
  finally:s.close()
 def test_idempotent(self):self.add();before=self.db.export();self.add();self.assertEqual(before,self.db.export());self.assertEqual(self.db.db.execute('SELECT count(*) FROM rag_fts').fetchone()[0],1)
 def test_resume_marker(self):self.add();self.assertTrue(self.db.finished('synthetic','input'));self.assertFalse(self.db.finished('synthetic','other'))
 def test_reopen(self):
  self.add();r=Store(self.db.path)
  try:self.assertEqual(search(r,Query())['results'][0]['id'],self.r.id)
  finally:r.close()
 def test_rollback(self):
  bad=replace(self.r,source_sha256='0'*64)
  with self.assertRaises(ValueError):self.db.put_execution('synthetic','input',[(self.r,'valid','parent'),(bad,'bad','parent')])
  self.assertEqual(len(self.db.records()),0)
 def test_exact_execution(self):self.add();self.assertEqual(self.q(execution_id='synthetic')['matching_count'],1)
 def test_wrong_execution(self):self.add();self.assertFalse(self.q(execution_id='wrong')['results'])
 def test_wrong_object(self):self.add();self.assertFalse(self.q(object_id='wrong')['results'])
 def test_wrong_task(self):self.add();self.assertFalse(self.q(task_id='wrong')['results'])
 def test_wrong_requirement(self):self.add();self.assertFalse(self.q(requirement_version='1')['results'])
 def test_pose_vs_contact(self):self.add();self.assertFalse(self.q(evidence_types=('contact',))['results'])
 def test_fts(self):self.add();self.assertEqual(self.q(text='pose position')['matching_count'],1)
 def test_fts_miss(self):self.add();self.assertFalse(self.q(text='tomato')['results'])
 def test_text_preserves_filter(self):self.add();self.assertFalse(self.q(text='pose',execution_id='wrong')['results'])
 def test_literal_query(self):self.add();self.assertFalse(self.q(text='pose OR missing')['results'])
 def test_gap(self):self.add();self.assertEqual(self.q(interval=(0,4),evidence_types=('object_pose',))['coverage']['object_pose']['missing_intervals'],[[1,1],[4,4]])
 def test_empty_gap(self):self.assertEqual(self.q(interval=(0,4),evidence_types=('contact',))['coverage']['contact']['missing_intervals'],[[0,4]])
 def test_invalid_source(self):self.add();self.source.write_text('changed');self.assertFalse(self.q()['results']);self.assertTrue(self.q()['rejected'])
 def test_missing_source(self):self.add();self.source.unlink();self.assertFalse(self.q()['results'])
 def test_invalid_measurement(self):self.add(replace(self.r,validation_status='invalid'));self.assertFalse(self.q()['results'])
 def test_capability(self):self.add();self.assertFalse(self.q(capabilities={'physical':'VERIFIED'})['results'])
 def test_uncertainty(self):self.add();self.assertEqual(self.q()['uncertainty'],list(self.r.uncertainty));self.assertTrue(self.q(uncertainty_contains='alignment')['results'])
 def test_never_verdict(self):self.add();x=self.q();self.assertFalse(x['safety_claim_verified']);self.assertFalse(x['empirical_admission_enabled'])
 def test_serialization(self):self.add();self.assertEqual(canonical(self.q()),canonical(self.q()))
 def test_index_integrity(self):self.add();self.assertTrue(self.db.check()['passed'])
 def test_bad_limit(self):
  with self.assertRaises(ValueError):self.q(limit=101)
 def test_bad_temporal_domain(self):
  with self.assertRaises(ValueError):self.q(interval=(0.,1.))
 def test_dependency_source_invalid(self):
  dep=self.r;other=self.root/'other';other.write_text('other');child=replace(self.r,source_path=str(other),source_sha256=hashlib.sha256(b'other').hexdigest(),selector='/child',dependencies=(dep.id,));self.db.put_execution('synthetic','input',[(dep,'root','p'),(child,'child','p')]);self.source.write_text('changed');self.assertFalse(self.q()['results'])
 def test_dependency_missing(self):
  with self.assertRaises(ValueError):self.add(replace(self.r,dependencies=('missing',)))
 def test_conflict(self):
  b=replace(self.r,selector='/counter',conflicts=(self.r.id,));self.db.put_execution('synthetic','input',[(self.r,'a','p'),(b,'b','p')]);self.assertFalse(self.q()['results'])
 def test_source_attribution(self):self.add();self.assertEqual(self.q()['results'][0]['record']['source_sha256'],self.r.source_sha256)
 def test_superseded_input_excluded(self):
  self.add();b=replace(self.r,provenance={**self.r.provenance,'input_binding_digest':'new'});self.add(b);self.assertEqual(self.q()['matching_count'],1);self.assertEqual(self.q()['results'][0]['id'],b.id)
 def test_unknown_migration(self):
  self.db.db.execute("INSERT INTO rag_migrations VALUES('9.0','bad')");self.db.db.commit()
  with self.assertRaises(ValueError):Store(self.db.path)
 def test_failure_logged(self):
  from evaluation.r1_v4.rag_evidence_database.build import populate
  path=self.root/'failure.sqlite'
  with patch('evaluation.r1_v4.rag_evidence_database.build.input_binding',return_value={}),patch('evaluation.r1_v4.rag_evidence_database.build.read',side_effect=ValueError('synthetic interruption')):
   with self.assertRaises(ValueError):populate(path,(0,))
  s=Store(path)
  try:self.assertEqual(s.db.execute('SELECT count(*) FROM rag_failures').fetchone()[0],1);self.assertEqual(len(s.records()),0)
  finally:s.close()
