import unittest,copy,tempfile,sqlite3,os
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.plan import HERE,WORK,BASE,BASE_SHA
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.registry import VariantStore,validate_mapping
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.identity import identify
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.retrieval import VariantQuery,retrieve

class VariantTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.db=VariantStore(WORK/'expanded.sqlite');cls.cohort=load(HERE/'COHORT.json');cls.e=cls.cohort['tasks']['goal/task_07']['executions'][0]['execution_id'];cls.b=cls.db.binding(cls.e);cls.q=VariantQuery(execution_id=cls.e,variant_id=cls.b['variant_id'],object_id='akita_black_bowl_1',evidence_types=('object_pose',),interval=(0,0))
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def status(self,q):return retrieve(self.db,q)['status']
 def test_baseline_hash(self):self.assertEqual(sha(BASE),BASE_SHA)
 def test_432_executions(self):self.assertEqual(self.db.db.execute('SELECT count(*) FROM rag_jobs').fetchone()[0],432)
 def test_104_content_variants(self):self.assertEqual(self.db.db.execute('SELECT count(*) FROM rag_env_variants').fetchone()[0],104)
 def test_unique_evidence_ids(self):self.assertEqual(*self.db.db.execute('SELECT count(*),count(DISTINCT id) FROM evidence').fetchone())
 def test_old_migrations_unchanged(self):self.assertEqual(self.db.db.execute('SELECT version FROM rag_migrations ORDER BY version').fetchall(),[('1.0.0',),('1.1.0',)])
 def test_normalized_schema_version(self):self.assertEqual(self.db.db.execute('SELECT version FROM rag_variant_schema').fetchone()[0],'1.0.0')
 def test_exact_query(self):self.assertEqual(self.status(self.q),'ok')
 def test_wrong_variant(self):
  other=self.db.db.execute('SELECT id FROM rag_env_variants WHERE id!=? LIMIT 1',(self.b['variant_id'],)).fetchone()[0];self.assertEqual(self.status(replace(self.q,variant_id=other)),'invalid_query_scope')
 def test_wrong_task(self):self.assertEqual(self.status(replace(self.q,task_id='wrong')),'invalid_query_scope')
 def test_wrong_execution(self):self.assertEqual(self.status(replace(self.q,execution_id='not-recorded')),'unknown_execution')
 def test_unresolved_variant(self):self.assertEqual(self.status(replace(self.q,variant_id='xmlenv:unknown')),'unresolved_variant')
 def test_unindexed_execution(self):
  e=self.db.db.execute("SELECT execution FROM rag_scope_status WHERE status='unindexed_profile_pending' LIMIT 1").fetchone()[0];self.assertEqual(self.status(replace(self.q,execution_id=e)),'unindexed_execution')
 def test_reserved_exclusion(self):
  e=self.db.db.execute("SELECT execution FROM rag_scope_status WHERE status='excluded_reserved' LIMIT 1").fetchone()[0];self.assertEqual(self.status(VariantQuery(execution_id=e)),'excluded_reserved')
 def test_preflight_exclusion(self):
  e=self.db.db.execute("SELECT execution FROM rag_scope_status WHERE status='excluded_preflight' LIMIT 1").fetchone()[0];self.assertEqual(self.status(VariantQuery(execution_id=e)),'excluded_preflight')
 def test_unknown_object_no_substitution(self):self.assertEqual(self.status(replace(self.q,object_id='not-this-object')),'no_matching_indexed_record')
 def test_missing_field(self):self.assertEqual(self.status(replace(self.q,field_name='contact_force')),'unsupported_field')
 def test_absent_timestamp(self):self.assertEqual(self.status(replace(self.q,field_name='camera_exposure_timestamp')),'unavailable_timestamp')
 def test_unverified_spatial(self):self.assertEqual(self.status(replace(self.q,field_name='raw_eef_world_pose')),'unsupported_spatial_field')
 def test_unresolved_logical_alias(self):self.assertEqual(self.status(replace(self.q,field_name='logical_main_table_pose')),'unsupported_mapping')
 def test_field_family_conflict(self):self.assertEqual(self.status(replace(self.q,field_name='ctrl')),'invalid_query_scope')
 def test_field_type_invalid(self):self.assertEqual(self.status(replace(self.q,field_name=[])),'invalid_query_scope')
 def test_unsupported_clock(self):self.assertEqual(self.status(replace(self.q,time_interval=(0.,1.))),'unsupported_temporal_domain')
 def test_no_implicit_comparison(self):self.assertEqual(self.status(VariantQuery()),'invalid_query_scope')
 def test_shared_variant_not_shared_execution(self):
  r=retrieve(self.db,VariantQuery(variant_id=self.b['variant_id'],comparative=True,evidence_types=('execution_metadata',)));self.assertEqual(len(r['groups']),2);self.assertFalse(r['coverage_composed_across_executions']);self.assertTrue(all(item['record']['execution_id']==g['execution_id'] for g in r['groups'] for item in g['result']['results']))
 def test_geometry_contract_blocked(self):self.assertEqual(self.status(replace(self.q,evidence_types=('native_geometry',),capabilities={'geometry_admission':'VERIFIED'})),'invalid_or_insufficient_evidence')
 def test_missing_frame_not_negative(self):
  r=retrieve(self.db,replace(self.q,interval=(99999,99999)));self.assertEqual(r['status'],'no_matching_indexed_record');self.assertFalse(r['safety_claim_verified']);self.assertEqual(r['groups'][0]['result']['coverage']['object_pose']['missing_intervals'],[[99999,99999]])
 def test_timestamp_not_spatial(self):
  r=retrieve(self.db,replace(self.q,evidence_types=('timestamp',)));self.assertEqual(r['groups'][0]['result']['results'][0]['record']['coordinate_frame'],'not_applicable_timestamp')
 def test_corrupt_body_map_rejected(self):
  b=copy.deepcopy(self.b);b['objects']['akita_black_bowl_1']['body_id']+=1
  with self.assertRaises(ValueError):validate_mapping(b)
 def test_variant_triggers_immutable(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fresh.sqlite';db=VariantStore(p,create=True,writable=True);identity=load(WORK/'profiles'/self.e/'VARIANT.json');db.register(identity,self.b)
   with self.assertRaises(sqlite3.IntegrityError):db.db.execute('UPDATE rag_env_variants SET xml_sha256=?',('0'*64,))
   db.close()
 def test_source_hash_mismatch_rejected(self):
  from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.retrieval import guard
  b=copy.deepcopy(self.b);b['xml_sha256']='0'*64
  with self.assertRaises(ValueError):guard(self.db,b,{})
 def test_no_physical_claim(self):
  r=retrieve(self.db,self.q);self.assertFalse(r['safety_claim_verified']);self.assertFalse(r['sufficient_for_physical_checking']);self.assertFalse(r['empirical_admission_enabled'])

class IdentityTests(unittest.TestCase):
 def fixture(self,root):
  asset=root/'mesh.dat';asset.write_bytes(b'synthetic asset A');xml=root/'model.xml';xml.write_text('<mujoco><asset><mesh name="x" file="'+str(asset)+'"/></asset></mujoco>');manifest=root/'assets.json';write_new(manifest,{'synthetic':True,'assets':[{'path':str(asset),'sha256':sha(asset),'bytes':asset.stat().st_size,'kind':'mesh','name':'x'}]});return xml,manifest,asset
 def test_xml_path_not_variant_identity(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);xml,manifest,asset=self.fixture(root);other=root/'copy.xml';other.write_bytes(xml.read_bytes());self.assertEqual(identify(xml,manifest)['variant_id'],identify(other,manifest)['variant_id'])
 def test_same_xml_different_asset_changes_variant(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);xml,manifest,asset=self.fixture(root);first=identify(xml,manifest);asset.write_bytes(b'synthetic asset B');second=root/'new_assets.json';write_new(second,{'synthetic':True,'assets':[{'path':str(asset),'sha256':sha(asset),'bytes':asset.stat().st_size}]});self.assertNotEqual(first['variant_id'],identify(xml,second)['variant_id'])
 def test_valid_named_asset_aliases_deduplicate_file(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);xml,manifest,asset=self.fixture(root);row=load(manifest)['assets'][0];alias={**row,'name':'second_named_reference'};other=root/'aliases.json';write_new(other,{'synthetic':True,'assets':[row,alias]});self.assertEqual(identify(xml,manifest)['variant_id'],identify(xml,other)['variant_id']);self.assertEqual(len(identify(xml,other)['asset_aliases']),2)
 def test_conflicting_asset_alias_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);xml,manifest,asset=self.fixture(root);row=load(manifest)['assets'][0];other=root/'conflict.json';write_new(other,{'synthetic':True,'assets':[row,{**row,'sha256':'0'*64}]})
   with self.assertRaises(ValueError):identify(xml,other)
 def test_unmanifested_dependency_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);xml,manifest,asset=self.fixture(root);other=root/'empty.json';write_new(other,{'synthetic':True,'assets':[]})
   with self.assertRaises(ValueError):identify(xml,other)
 def test_nested_include_explicitly_unsupported(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);xml,manifest,asset=self.fixture(root);xml.write_text('<mujoco><include file="another.xml"/></mujoco>')
   with self.assertRaises(ValueError):identify(xml,manifest)
