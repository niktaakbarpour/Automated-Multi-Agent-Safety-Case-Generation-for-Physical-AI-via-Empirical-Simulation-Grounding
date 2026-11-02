import unittest,tempfile,os,hashlib,json
from pathlib import Path
import numpy as np,h5py
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.retrieve import read_samples
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.config import WORK

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class SourceIntegrity(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=WORK);self.root=Path(self.tmp.name);self.p=self.root/'data';self.p.write_bytes(b'original');self.expected=sha(self.p);self.v=SourceVerifier(roots=(self.root,))
 def tearDown(self):self.tmp.cleanup()
 def test_strict_hashes_both_boundaries(self):self.v.verify(self.p,self.expected);self.assertEqual(self.v.hash_checks,2)
 def test_session_starts_with_hash(self):self.v.verify(self.p,self.expected,'verified_session');self.assertEqual(self.v.hash_checks,1)
 def test_session_reuses_only_verified_identity(self):
  self.v.verify(self.p,self.expected,'verified_session');self.v.verify(self.p,self.expected,'verified_session');self.assertEqual(self.v.hash_checks,1);self.assertEqual(self.v.cache_hits,1)
 def test_modified_bytes_rejected(self):
  self.v.verify(self.p,self.expected,'verified_session');self.p.write_bytes(b'modified')
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'verified_session')
 def test_preserved_mtime_is_not_proof(self):
  self.v.verify(self.p,self.expected,'verified_session');s=self.p.stat();self.p.write_bytes(b'modified');os.utime(self.p,ns=(s.st_atime_ns,s.st_mtime_ns))
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'verified_session')
 def test_replaced_different_bytes_rejected(self):
  self.v.verify(self.p,self.expected,'verified_session');other=self.root/'other';other.write_bytes(b'modified');os.replace(other,self.p)
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'verified_session')
 def test_replaced_matching_bytes_rehash(self):
  self.v.verify(self.p,self.expected,'verified_session');other=self.root/'other';other.write_bytes(b'original');os.replace(other,self.p);self.v.verify(self.p,self.expected,'verified_session');self.assertEqual(self.v.hash_checks,2)
 def test_missing_source(self):
  self.p.unlink()
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected)
 def test_final_symlink_even_matching_rejected(self):
  other=self.root/'other';self.p.rename(other);self.p.symlink_to(other)
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected)
 def test_parent_symlink_rejected(self):
  real=self.root/'real';real.mkdir();(real/'f').write_bytes(b'original');link=self.root/'link';link.symlink_to(real,target_is_directory=True)
  with self.assertRaises(SourceError):self.v.verify(link/'f',self.expected)
 def test_stale_cache_after_symlink_swap(self):
  self.v.verify(self.p,self.expected,'verified_session');other=self.root/'other';self.p.rename(other);self.p.symlink_to(other)
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'verified_session')
 def test_change_during_read(self):
  with self.assertRaises(SourceError):
   with self.v.access(self.p,self.expected,'verified_session'):self.p.write_bytes(b'modified')
 def test_path_replacement_during_read(self):
  with self.assertRaises(SourceError):
   with self.v.access(self.p,self.expected):
    other=self.root/'other';other.write_bytes(b'original');os.replace(other,self.p)
 def test_matching_restoration_after_rejection(self):
  self.v.verify(self.p,self.expected,'verified_session');self.p.write_bytes(b'modified')
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'verified_session')
  self.p.write_bytes(b'original');self.assertEqual(self.v.verify(self.p,self.expected,'verified_session')['status'],'verified_source');self.assertEqual(self.v.hash_checks,3)
 def test_missing_then_restored(self):
  self.v.verify(self.p,self.expected,'verified_session');self.p.unlink()
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'verified_session')
  self.p.write_bytes(b'original');self.v.verify(self.p,self.expected,'verified_session');self.assertEqual(self.v.hash_checks,2)
 def test_expected_hash_part_of_cache_key(self):
  self.v.verify(self.p,self.expected,'verified_session')
  with self.assertRaises(SourceError):self.v.verify(self.p,'f'*64,'verified_session')
 def test_no_unverified_mode(self):
  with self.assertRaises(SourceError):self.v.verify(self.p,self.expected,'unverified')
 def test_no_missing_hash(self):
  with self.assertRaises(SourceError):self.v.verify(self.p,None)
 def test_outside_namespace_root(self):
  with self.assertRaises(SourceError):self.v.verify(WORK/'BUILD.json',self.expected)
 def test_no_parent_traversal(self):
  with self.assertRaises(SourceError):self.v.verify(str(self.root)+'/../x',self.expected)
 def test_directory_not_source(self):
  with self.assertRaises(SourceError):self.v.verify(self.root,self.expected)
 def test_namespace_separates_verification_state(self):
  self.v.verify(self.p,self.expected,'verified_session');other=SourceVerifier(roots=(self.root,),namespace='other-host');other.verify(self.p,self.expected,'verified_session');self.assertEqual(other.hash_checks,1);self.assertEqual(other.cache_hits,0)

class DatasetContract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=WORK);self.p=Path(self.tmp.name)/'source.h5';self.raw={'frame_keys':{'0':'000000'}};self.sem=dict(source_field='raw_observation/value',expected_shape=[2],expected_dtype='float64',channel_id='raw.robot0_gripper_qpos');self.execution=dict(execution_id='fixture',temporal_rows=[dict(saved_frame=0)])
 def tearDown(self):self.tmp.cleanup()
 def write(self,value,episode='fixture',field=True):
  with h5py.File(self.p,'w') as f:
   f.attrs['global_episode_id']=episode
   if field:f.create_dataset('/frames/000000/raw_observation/value',data=value)
 def read(self):
  verifier=SourceVerifier(roots=(Path(self.tmp.name),))
  with verifier.access(self.p,sha(self.p)) as (file,_):return read_samples(file,self.raw,self.sem,[0],self.execution)
 def test_original_values_exact(self):self.write(np.array([1.,2.]));self.assertEqual(self.read()[0]['value'],[1.,2.])
 def test_shape_changed_even_with_new_hash(self):
  self.write(np.array([1.,2.,3.]))
  with self.assertRaisesRegex(SourceError,'shape'):self.read()
 def test_dtype_changed_even_with_new_hash(self):
  self.write(np.array([1.,2.],dtype=np.float32))
  with self.assertRaisesRegex(SourceError,'dtype'):self.read()
 def test_missing_dataset(self):
  self.write(None,field=False)
  with self.assertRaisesRegex(SourceError,'missing_source_dataset'):self.read()
 def test_wrong_execution(self):
  self.write(np.array([1.,2.]),episode='other')
  with self.assertRaisesRegex(SourceError,'execution'):self.read()
 def test_nonfinite_values(self):
  self.write(np.array([1.,np.nan]))
  with self.assertRaisesRegex(SourceError,'numeric'):self.read()
 def test_no_stale_decoded_values(self):
  self.write(np.array([1.,2.]));self.assertEqual(self.read()[0]['value'],[1.,2.]);self.write(np.array([3.,4.]));self.assertEqual(self.read()[0]['value'],[3.,4.])
 def test_sparse_window_retains_indices(self):
  with h5py.File(self.p,'w') as f:
   f.attrs['global_episode_id']='fixture'
   for i in (0,2):f.create_dataset('/frames/'+str(i).zfill(6)+'/raw_observation/value',data=np.array([i,i+1.]))
  self.raw['frame_keys']['2']='000002';self.execution['temporal_rows']=[dict(saved_frame=i) for i in range(3)]
  with self.p.open('rb') as file:r=read_samples(file,self.raw,self.sem,[0,2],self.execution)
  self.assertEqual([s['saved_frame_index'] for s in r],[0,2]);self.assertEqual(r[1]['value'],[2.,3.])
