import unittest,tempfile,json,sqlite3,os,hashlib
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.config import WORK
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.model import claim,validate_claim
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.restore import RestoredRelease
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.retrieve import ProvenanceQuery,retrieve
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceError

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Attestation(unittest.TestCase):
 def setUp(self):self.c=claim('e','revision','abc','HISTORICAL_RECORD',{'path':'p','sha256':'f'*64},'revision','recorded metadata')
 def test_record_is_declaration_only(self):self.assertEqual(self.c['historical_attestation'],'RECORDED_DECLARATION_ONLY')
 def test_no_attestation_escalation(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,historical_attestation='VERIFIED_HISTORICAL'))
 def test_no_current_as_historical(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,source_origin='CURRENT_ARTIFACT'))
 def test_no_retroactive_historical(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,category='RETROSPECTIVE_ARTIFACT'))
 def test_no_trusted_creation_date(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,independently_verified_creation_date='2026-10-01'))
 def test_no_unknown_category(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,category='TRUST_ME'))
 def test_requires_limitations(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,limitations=''))
 def test_requires_basis(self):
  with self.assertRaises(ValueError):validate_claim(dict(self.c,basis=''))
class Guards(unittest.TestCase):
 def test_historical_request_no_downgrade(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',assurance='historical_producer_attestation'))['status'],'unattested_historical_producer')
 def test_complete_requires_explicit_scope(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',assurance='provenance_complete'))['status'],'unsupported_provenance_scope')
 def test_no_full_history_alias(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',assurance='provenance_complete',provenance_scope='full_history'))['status'],'unsupported_provenance_scope')
 def test_no_unknown_assurance(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',assurance='best_effort'))['status'],'unsupported_assurance')
 def test_no_sensor_clock(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',clock_domain='joint_sensor_clock'))['status'],'unsupported_clock')
 def test_no_host_to_sim_mapping(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',clock_domain='host_wall_ns'))['status'],'unsupported_clock')
 def test_no_seconds_as_index(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',seconds_interval=(0,1)))['status'],'invalid_clock_query')
 def test_no_label_without_window(self):self.assertEqual(retrieve(None,ProvenanceQuery('e',clock_domain='simulator_endpoint_label'))['status'],'invalid_clock_query')
class RestoreIntegrity(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=WORK);self.root=Path(self.tmp.name);(self.root/'objects').mkdir();self.original=str(self.root/'canonical.h5');self.data=b'bound-evidence';self.h=hashlib.sha256(self.data).hexdigest();self.p=self.root/'objects'/self.h;self.p.write_bytes(self.data)
  c=sqlite3.connect(self.root/'database.sqlite');c.executescript('create table i_artifacts(id,path,sha256);create table i_scope_nodes(execution,node);');c.execute('insert into i_artifacts values(?,?,?)',('a',self.original,self.h));c.execute('insert into i_scope_nodes values(?,?)',('e','a'));c.commit();c.close()
  self.m=dict(database_sha256=sha(self.root/'database.sqlite'),executions=['e'],entries={self.original+'#'+self.h:dict(canonical_path=self.original,sha256=self.h,relative_path='objects/'+self.h,executions=['e'])});self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  (self.root/'RESTORE.json').write_text(json.dumps(self.m));self.mh=sha(self.root/'RESTORE.json')
 def release(self):return RestoredRelease(self.root,self.mh)
 def test_valid_bounded_restore(self):self.release().verify('e')
 def test_missing_scope(self):
  with self.assertRaises(SourceError):self.release().verify('other')
 def test_no_original_fallback(self):
  Path(self.original).write_bytes(self.data);self.p.unlink()
  with self.assertRaises(SourceError):self.release().verify('e')
 def test_manifest_modified(self):
  (self.root/'RESTORE.json').write_text('{}')
  with self.assertRaises(SourceError):self.release()
 def test_database_modified(self):
  with (self.root/'database.sqlite').open('ab') as f:f.write(b'bad')
  with self.assertRaises(SourceError):self.release()
 def test_wrong_execution_mapping(self):
  self.m['entries'][self.original+'#'+self.h]['executions']=['wrong'];self.save()
  with self.assertRaises(SourceError):self.release().verify('e')
 def test_path_traversal(self):
  self.m['entries'][self.original+'#'+self.h]['relative_path']='../canonical.h5';self.save()
  with self.assertRaises(SourceError):self.release().verify('e')
 def test_symlink_redirect(self):
  other=self.root/'other';self.p.rename(other);self.p.symlink_to(other)
  with self.assertRaises(SourceError):self.release().verify('e')
 def test_invalid_incomplete_restore(self):
  self.m['entries']={};self.save()
  with self.assertRaises(SourceError):self.release().verify('e')
 def test_matching_restoration(self):
  r=self.release();self.p.write_bytes(b'bad')
  with self.assertRaises(SourceError):r.verify('e')
  self.p.write_bytes(self.data);r.verify('e')
 def test_stale_cache(self):
  r=self.release();r.verify('e');self.p.write_bytes(b'bad')
  with self.assertRaises(SourceError):r.verify('e')
def role_tamper(role):
 def test(self):
  r=self.release();r.verify('e');self.p.write_bytes(('altered '+role).encode())
  with self.assertRaises(SourceError):r.verify('e')
 return test
for role in ('hdf5','xml','geometry_asset','producer_code','dependency_binary','interpretation_contract','clock_evidence'):
 setattr(RestoreIntegrity,'test_modified_'+role,role_tamper(role))
class ReleaseAPI(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from evaluation.r1_v4.rag_evidence_database.source_reproducibility.store import ProvenanceStore
  build=json.loads((WORK/'BUILD.json').read_text());cls.store=ProvenanceStore(WORK/'expanded.sqlite',expected_sha256=build['database_sha256']);cls.ex=cls.store.db.execute('select execution from i_jobs order by execution limit 1').fetchone()[0];cls.q=ProvenanceQuery(cls.ex,channel_id='raw.robot0_joint_pos',interval=(0,0),verification_mode='verified_session')
 @classmethod
 def tearDownClass(cls):cls.store.close()
 def test_raw_not_blocked_by_missing_historical_binary(self):self.assertEqual(retrieve(self.store,self.q)['status'],'ok')
 def test_physical_requires_verified_properties(self):self.assertEqual(retrieve(self.store,replace(self.q,assurance='verified_physical_interpretation'))['status'],'ok')
 def test_conditional_cannot_satisfy_physical_assurance(self):self.assertFalse(retrieve(self.store,replace(self.q,assurance='verified_physical_interpretation',allow_conditional=True,required_properties=('cache_offset_seconds',)))['results'])
 def test_exact_simulator_label(self):
  q=replace(self.q,interval=None,clock_domain='simulator_endpoint_label',seconds_interval=(0.,0.));r=retrieve(self.store,q);self.assertEqual([s['saved_frame_index'] for s in r['results'][0]['samples']],[0])
 def test_no_invented_between_labels(self):self.assertFalse(retrieve(self.store,replace(self.q,interval=None,clock_domain='simulator_endpoint_label',seconds_interval=(.001,.002)))['results'])
 def test_malformed_seconds(self):self.assertEqual(retrieve(self.store,replace(self.q,interval=None,clock_domain='simulator_endpoint_label',seconds_interval=1))['status'],'invalid_clock_query')
 def test_historical_unavailable_even_raw_available(self):self.assertFalse(retrieve(self.store,replace(self.q,assurance='historical_producer_attestation'))['results'])
 def test_world_transform_unavailable(self):self.assertFalse(retrieve(self.store,replace(self.q,transformation='world_pose'))['results'])
 def test_wrong_source_never_downgrades(self):self.assertFalse(retrieve(self.store,replace(self.q,source_sha256='0'*64))['results'])
 def test_wrong_variant_never_downgrades(self):self.assertFalse(retrieve(self.store,replace(self.q,variant_id='wrong'))['results'])
 def test_metadata_only_not_source_verified(self):
  self.assertFalse(self.store.db.execute("select 1 from i_claims where historical_attestation not in ('RECORDED_DECLARATION_ONLY','NOT_ATTESTED','NOT_APPLICABLE')").fetchone())
class ReleaseManifest(unittest.TestCase):
 def setUp(self):
  from evaluation.r1_v4.rag_evidence_database.source_reproducibility.check_release import verify
  self.verify=verify;self.tmp=tempfile.TemporaryDirectory(dir=WORK);self.root=Path(self.tmp.name);self.p=self.root/'source';self.p.write_bytes(b'evidence');self.mp=self.root/'manifest.json';self.row=dict(path=str(self.p),sha256=sha(self.p),bytes=8,required_for='metadata');self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):self.mp.write_text(json.dumps(dict(artifacts=[self.row])));self.mh=sha(self.mp)
 def test_pinned_release(self):self.assertTrue(self.verify(self.mp,self.mh)['passed'])
 def test_manifest_tamper(self):
  self.mp.write_text('{}')
  with self.assertRaises(SourceError):self.verify(self.mp,self.mh)
 def test_artifact_tamper(self):
  self.p.write_bytes(b'different')
  with self.assertRaises(SourceError):self.verify(self.mp,self.mh)
 def test_artifact_missing(self):
  self.p.unlink()
  with self.assertRaises(SourceError):self.verify(self.mp,self.mh)
 def test_size_contract(self):
  self.row['bytes']=99;self.save()
  with self.assertRaises(SourceError):self.verify(self.mp,self.mh)
 def test_unknown_scope(self):
  with self.assertRaises(ValueError):self.verify(self.mp,self.mh,'best_effort')
 def test_symlink(self):
  other=self.root/'other';self.p.rename(other);self.p.symlink_to(other)
  with self.assertRaises(SourceError):self.verify(self.mp,self.mh)
 def test_source_scope_not_silently_downgraded(self):
  self.row['required_for']='sources';self.save();self.p.write_bytes(b'changed')
  self.assertTrue(self.verify(self.mp,self.mh,'metadata')['passed'])
  with self.assertRaises(SourceError):self.verify(self.mp,self.mh,'sources')
