import unittest,tempfile,hashlib,sqlite3
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.evidence_registry_gsn.registry import Registry
from evaluation.r1_v4.evidence_registry_gsn.retrieval import Query,retrieve
from evaluation.r1_v4.evidence_registry_gsn.adapter import assessment
from evaluation.r1_v4.provenance import canonical,strict_loads

class RegistryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir='/disk/1/data/niktakbr');self.root=Path(self.tmp.name)
  self.source=self.root/'synthetic-source.txt';self.source.write_text('synthetic measurement source')
  self.record=Record('1.0.0','R1','2.0.0','synthetic-execution','obj','raw_measurement',str(self.source),hashlib.sha256(self.source.read_bytes()).hexdigest(),'/pose','object_pose','verified_measurement',{'availability':'VERIFIED'},'saved_frame','frame',(1,3),'MuJoCo_world','synthetic-model','synthetic-benchmark','synthetic-task','synthetic-producer',True,uncertainty=('Unknown physical uncertainty',),limitations=('Synthetic fixture; no physical conclusion',),provenance={'synthetic':True,'physical_truth':'U'})
  self.registry=Registry(self.root/'index.sqlite',create=True)
  self.q=Query('G1','R1','2.0.0','synthetic-execution','obj',('object_pose',),(1,3),'frame','saved_frame',{'availability':'VERIFIED'})
 def tearDown(self):self.registry.close();self.tmp.cleanup()
 def add(self,r=None):self.registry.add([r or self.record])
 def query(self,**kw):return retrieve(self.registry,replace(self.q,**kw))
 def test_stable_id_roundtrip(self):self.assertEqual(self.record.id,Record.parse(strict_loads(canonical(self.record.export()).decode())).id)
 def test_changed_scope_changes_id(self):self.assertNotEqual(self.record.id,replace(self.record,object_id='other').id)
 def test_record_version(self):
  with self.assertRaises(ValueError):replace(self.record,schema_version='2').validate()
 def test_requirement_version(self):
  with self.assertRaises(ValueError):replace(self.record,requirement_version='1').validate()
 def test_hash_format(self):
  with self.assertRaises(ValueError):replace(self.record,source_sha256='x').validate()
 def test_physical_event_not_measurement(self):
  with self.assertRaises(ValueError):replace(self.record,measurement_type='fall').validate()
 def test_ai_not_verified_measurement(self):
  with self.assertRaises(ValueError):replace(self.record,kind='ai_reference_judgment').validate()
 def test_truth_not_promoted(self):
  with self.assertRaises(ValueError):replace(self.record,provenance={'physical_truth':'T'}).validate()
 def test_idempotent_insert(self):self.add();self.add();self.assertEqual(len(self.registry.records()),1)
 def test_persistent_readonly(self):
  self.add();r=Registry(self.registry.path)
  try:self.assertEqual(r.export(),self.registry.export())
  finally:r.close()
 def test_readonly_cannot_create(self):
  with self.assertRaises(sqlite3.OperationalError):Registry(self.root/'missing.sqlite')
 def test_database_version(self):
  self.registry.db.execute('PRAGMA user_version=2')
  with self.assertRaises(ValueError):Registry(self.registry.path)
 def test_immutable_update(self):
  self.add()
  with self.assertRaises(sqlite3.IntegrityError):self.registry.db.execute("UPDATE evidence SET kind='document'")
 def test_integrity(self):self.add();self.assertEqual(self.registry.integrity()['sqlite'],'ok')
 def test_hash_mismatch(self):self.add();self.source.write_text('changed');self.assertEqual(self.query()['rejected'][0]['reasons'],['hash_mismatch'])
 def test_missing_file(self):self.add();self.source.unlink();self.assertEqual(self.query()['rejected'][0]['reasons'],['missing_source'])
 def test_exact_query(self):self.add();self.assertEqual(self.query()['matching_evidence_ids'],[self.record.id])
 def test_wrong_execution(self):self.add();self.assertFalse(self.query(execution_id='other')['matching_evidence_ids'])
 def test_wrong_object(self):self.add();self.assertFalse(self.query(object_id='other')['matching_evidence_ids'])
 def test_wrong_version(self):self.add();self.assertFalse(self.query(requirement_version='1')['matching_evidence_ids'])
 def test_reproducible(self):self.add();self.assertEqual(canonical(self.query()),canonical(self.query()))
 def test_no_record_gap(self):self.assertEqual(self.query()['coverage']['object_pose']['missing_intervals'],[[1,3]])
 def test_declared_gap(self):self.add(replace(self.record,missing_intervals=((2,2),)));self.assertEqual(self.query()['coverage']['object_pose']['missing_intervals'],[[2,2]])
 def test_type_specific_gap(self):self.add();self.assertEqual(self.query(evidence_types=('object_pose','contact'))['coverage']['contact']['missing_intervals'],[[1,3]])
 def test_partial_interval(self):self.add();self.assertEqual(self.query(interval=(0,4))['coverage']['object_pose']['missing_intervals'],[[0,0],[4,4]])
 def test_clock_mismatch(self):self.add();self.assertIn('incompatible_clock_or_domain',self.query(clock='camera')['rejected'][0]['reasons'])
 def test_unsupported_geometry(self):self.add(replace(self.record,capability={'geometry':'UNSUPPORTED'}));self.assertFalse(self.query(minimum_capabilities={'geometry':'VERIFIED'})['matching_evidence_ids'])
 def test_unsupported_alignment(self):self.add(replace(self.record,capability={'alignment':'UNSUPPORTED'}));self.assertFalse(self.query(minimum_capabilities={'alignment':'VERIFIED'})['matching_evidence_ids'])
 def test_no_implicit_capability_upgrade(self):self.add(replace(self.record,capability={'availability':'CONDITIONALLY_SUPPORTED'}));self.assertFalse(self.query()['matching_evidence_ids'])
 def test_uncertainty_propagation(self):self.add();self.assertEqual(self.query()['uncertainty'],list(self.record.uncertainty))
 def test_missing_dependency(self):
  with self.assertRaises(ValueError):self.add(replace(self.record,dependencies=('unknown',)))
 def test_dependency_scope(self):
  dep=replace(self.record,execution_id='other')
  with self.assertRaises(ValueError):self.registry.add([dep,replace(self.record,dependencies=(dep.id,))])
 def test_explicit_conflict(self):
  a=self.record;b=replace(a,selector='/other',conflicts=(a.id,));self.registry.add([a,b]);self.assertFalse(self.query()['matching_evidence_ids'])
 def test_invalid_dependency(self):
  dep=replace(self.record,validation_status='invalid')
  with self.assertRaises(ValueError):self.registry.add([dep,replace(self.record,dependencies=(dep.id,))])
 def test_transitive_missing_source(self):
  missing=self.root/'dep';missing.write_text('dep');a=replace(self.record,source_path=str(missing),source_sha256=hashlib.sha256(b'dep').hexdigest());b=replace(self.record,selector='/middle',dependencies=(a.id,));c=replace(self.record,selector='/last',dependencies=(b.id,));self.registry.add([a,b,c]);missing.unlink();self.assertFalse(self.query()['matching_evidence_ids'])
 def test_no_physical_promotion(self):
  self.add();a=assessment(self.query(),{});self.assertEqual(a['claim_status'],'unresolved');self.assertFalse(a['empirical_admission_enabled']);self.assertTrue(a['missing_capability_gates'])
 def test_forged_verified_gates_still_disabled(self):
  from evaluation.r1_v4.evidence_registry_gsn.adapter import PHYSICAL_GATES
  self.assertFalse(assessment(self.query(),dict.fromkeys(PHYSICAL_GATES,'VERIFIED'))['sufficient_for_physical_checking'])
 def test_nonfinite_interval(self):
  with self.assertRaises(ValueError):self.query(interval=(0,float('inf')))
 def test_empty_query_types(self):
  with self.assertRaises(ValueError):self.query(evidence_types=())
 def test_source_provenance_retained(self):self.add();self.assertEqual(self.query()['evidence'][0]['source_sha256'],self.record.source_sha256)
 def test_dependency_conflict_scoped(self):
  a=self.record;b=replace(a,selector='/counter',conflicts=(a.id,));self.registry.add([a,b])
  with self.assertRaises(ValueError):self.add(replace(a,selector='/depends',dependencies=(a.id,)))
  other=replace(a,object_id='unrelated');self.add(other)
  self.assertEqual(self.query(object_id='unrelated')['matching_evidence_ids'],[other.id])
 def test_overlaps_no_double_count(self):
  self.registry.add([self.record,replace(self.record,interval=(2,4))]);self.assertEqual(self.query(interval=(1,5))['coverage']['object_pose']['missing_intervals'],[[5,5]])
 def test_reversed_insert_stable(self):
  b=replace(self.record,selector='/other');self.registry.add([b,self.record]);self.assertEqual(self.query()['matching_evidence_ids'],sorted([b.id,self.record.id]))
 def test_corrupt_id(self):
  bad=self.record.export();bad['id']='ev:wrong'
  with self.assertRaises(ValueError):Record.parse(bad)
 def test_registration_hash_mismatch(self):
  with self.assertRaises(ValueError):self.add(replace(self.record,source_sha256='0'*64))
 def test_unapproved_source(self):
  with self.assertRaises(ValueError):replace(self.record,source_path='/unapproved/source').validate()
 def test_symlink_source(self):
  link=self.root/'link';link.symlink_to(self.source)
  with self.assertRaises(ValueError):replace(self.record,source_path=str(link)).validate()
 def test_dependency_clock(self):
  dep=replace(self.record,clock='other')
  with self.assertRaises(ValueError):self.registry.add([dep,replace(self.record,dependencies=(dep.id,))])
 def test_dependency_provenance_returned(self):
  dep=self.record;child=replace(dep,selector='/child',dependencies=(dep.id,));self.registry.add([dep,child]);self.assertEqual(self.query()['dependency_records'][0]['source_sha256'],dep.source_sha256)
