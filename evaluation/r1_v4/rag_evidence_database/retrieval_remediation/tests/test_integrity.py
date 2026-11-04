import json,unittest,tempfile,os,shutil
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.config import WORK,DATABASE_SHA
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.store import VerifiedReferences,SourceError
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import Retriever,BundleRequest
class IntegrityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=WORK);self.d=Path(self.tmp.name);self.p=self.d/'recorded';self.p.write_bytes(b'known original evidence');self.h=sha(self.p);self.v=VerifiedReferences();self.v.verify(str(self.p),self.h,'verified_session')
 def tearDown(self):self.tmp.cleanup()
 def denied(self):
  with self.assertRaises((SourceError,OSError)):self.v.verify(str(self.p),self.h,'verified_session')
 def test_modified_with_restored_mtime(self):
  s=self.p.stat();self.p.write_bytes(b'altered original bytes');os.utime(self.p,ns=(s.st_atime_ns,s.st_mtime_ns));self.denied()
 def test_atomic_replacement(self):
  p=self.d/'new';p.write_bytes(b'wrong');os.replace(p,self.p);self.denied()
 def test_deleted(self):self.p.unlink();self.denied()
 def test_hash_identical_symlink(self):
  p=self.d/'original';self.p.rename(p);self.p.symlink_to(p);self.denied()
 def test_parent_symlink(self):
  (self.d/'alias').symlink_to(self.d,target_is_directory=True)
  with self.assertRaises(SourceError):self.v.verify(str(self.d/'alias'/'recorded'),self.h)
 def test_matching_recovery(self):
  self.p.write_bytes(b'wrong');self.denied();self.p.write_bytes(b'known original evidence');self.assertEqual(self.v.verify(str(self.p),self.h)['status'],'verified_source')
 def manifest(self,**changes):
  body=dict(database_sha256=DATABASE_SHA,entries={str(self.p)+'#'+self.h:dict(relative_path='copy',executions=['e'],variants=['v'])});body.update(changes);p=self.d/'restore.json';p.write_text(json.dumps(body));v=VerifiedReferences(p,sha(p));v.execution='e';v.variant='v';return p,v
 def test_restore_hash_matching(self):
  (self.d/'copy').write_bytes(self.p.read_bytes());p,v=self.manifest();self.assertTrue(v.verify(str(self.p),self.h)['restoration_verified'])
 def test_restore_missing_no_fallback(self):
  p,v=self.manifest()
  with self.assertRaises((SourceError,OSError)):v.verify(str(self.p),self.h)
 def test_restore_wrong_scope(self):
  (self.d/'copy').write_bytes(self.p.read_bytes());p,v=self.manifest();v.execution='other'
  with self.assertRaises(SourceError):v.verify(str(self.p),self.h)
 def test_restore_wrong_variant(self):
  (self.d/'copy').write_bytes(self.p.read_bytes());p,v=self.manifest();v.variant='other'
  with self.assertRaises(SourceError):v.verify(str(self.p),self.h)
 def test_restore_manifest_modified(self):
  p,v=self.manifest();p.write_text('{}')
  with self.assertRaises(SourceError):v.verify(str(self.p),self.h)
 def test_restore_traversal(self):
  p,v=self.manifest();b=json.loads(p.read_text());next(iter(b['entries'].values()))['relative_path']='../recorded';p.write_text(json.dumps(b));v=VerifiedReferences(p,sha(p));v.execution='e';v.variant='v'
  with self.assertRaises(SourceError):v.verify(str(self.p),self.h)
 def test_catalogue_mutation_invalidates_cached_snapshot(self):
  p=self.d/'catalogue.sqlite';shutil.copyfile(WORK/'catalogue.sqlite',p);r=Retriever(p,sha(p))
  try:
   with p.open('ab') as f:f.write(b'mutated')
   self.assertEqual(r.retrieve(BundleRequest('Finger positions at frame 20.','unknown'))['completeness_status'],'UNAVAILABLE')
  finally:r.close()
