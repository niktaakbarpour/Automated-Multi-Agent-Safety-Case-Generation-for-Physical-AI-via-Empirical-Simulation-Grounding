"""End-to-end adversarial reads use small synthetic SQLite/HDF5 fixtures only."""
import unittest,tempfile,sqlite3,json,os,copy
from pathlib import Path
import numpy as np,h5py
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import digest,canonical
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.config import WORK
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.store import PhysicalStore
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.retrieve import PhysicalQuery,retrieve

class ApiTampering(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.real=PhysicalStore(WORK/'expanded.sqlite',expected_sha256=json.loads((WORK/'BUILD.json').read_text())['database_sha256'])
 @classmethod
 def tearDownClass(cls):cls.real.close()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=WORK);self.root=Path(self.tmp.name);self.source=self.root/'fixture.h5';self.database=self.root/'fixture.sqlite';real=self.real
  r,s=real.db.execute("select r.body,s.body from rag_channel_records r join h_semantics s on s.raw_id=r.id where s.channel='raw.robot0_joint_pos' order by s.execution limit 1").fetchone();r=json.loads(r);s=json.loads(s);self.e=r['execution_id'];self.binding=real.binding(self.e)
  with h5py.File(self.source,'w') as f:f.attrs['global_episode_id']=self.e;f.create_dataset('/frames/000000/'+r['source_field'],data=np.arange(7,dtype=np.float64))
  r.update(source_path=str(self.source),source_sha256=sha(self.source),valid_indices=[0],frame_keys={'0':'000000'},invalid_samples={});r['id']='channel:'+digest({k:v for k,v in r.items() if k!='id'});s.update(source_path=str(self.source),source_sha256=sha(self.source),raw_record_id=r['id']);s['id']='semantics:'+digest({k:v for k,v in s.items() if k!='id'});execution=json.loads(real.db.execute('select body from h_execution where execution=?',(self.e,)).fetchone()[0]);execution['temporal_rows']=execution['temporal_rows'][:1]
  class Fixture:
   def binding(inner,e):return self.binding
   def check_binding(inner,b,mode):return real.check_binding(b,mode)
  self.store=Fixture();self.store.db=sqlite3.connect(self.database);self.store.db.executescript('create table rag_scope_status(execution,status);create table rag_channel_records(id,body);create table h_semantics(raw_id,execution,channel,body);create table h_execution(execution,body);create table evidence(execution_id,kind,body);')
  c=self.store.db;c.execute('insert into rag_scope_status values(?,?)',(self.e,'indexed'));c.execute('insert into rag_channel_records values(?,?)',(r['id'],canonical(r).decode()));c.execute('insert into h_semantics values(?,?,?,?)',(r['id'],self.e,r['channel_id'],canonical(s).decode()));c.execute('insert into h_execution values(?,?)',(self.e,canonical(execution).decode()));c.execute('insert into evidence values(?,?,?)',(self.e,'raw_measurement',json.dumps(dict(source_path=str(self.source),source_sha256=sha(self.source)))));c.commit()
  self.store.verifier=SourceVerifier();self.store.verifier.verify(str(self.database),sha(self.database));self.store.database_verified=True;self.store.database_path=str(self.database);st=self.database.stat();self.store.database_signature=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns);self.q=PhysicalQuery(self.e,channel_id='raw.robot0_joint_pos',interval=(0,0),verification_mode='verified_session')
 def tearDown(self):self.store.db.close();self.tmp.cleanup()
 def get(self):return retrieve(self.store,self.q)
 def reject(self):
  r=self.get();self.assertEqual(r['status'],'invalid_source_or_contract');self.assertEqual(r['results'],[]);self.assertEqual(r['matching_count'],0)
 def test_verified_fixture(self):self.assertEqual(self.get()['results'][0]['samples'][0]['value'],list(range(7)))
 def test_modified_hdf5_no_stale_value(self):
  self.assertEqual(self.get()['status'],'ok')
  with h5py.File(self.source,'r+') as f:f['/frames/000000/raw_observation/robot0_joint_pos/value'][0]=99
  self.reject()
 def test_replaced_hdf5(self):
  self.assertEqual(self.get()['status'],'ok');other=self.root/'other';other.write_bytes(b'wrong source');os.replace(other,self.source);self.reject()
 def test_missing_hdf5(self):self.source.unlink();self.reject()
 def test_symlink_hdf5(self):
  other=self.root/'other.h5';self.source.rename(other);self.source.symlink_to(other);self.reject()
 def test_recovery_after_source_missing(self):
  original=self.source.read_bytes();self.assertEqual(self.get()['status'],'ok');self.source.unlink();self.reject();self.source.write_bytes(original);r=self.get();self.assertEqual(r['status'],'ok');self.assertEqual(r['results'][0]['samples'][0]['value'],list(range(7)))
 def test_shape_tampering_fails_closed(self):
  with h5py.File(self.source,'r+') as f:
   p='/frames/000000/raw_observation/robot0_joint_pos/value';del f[p];f.create_dataset(p,data=np.ones(8,dtype=np.float64))
  self.reject()
 def test_dtype_tampering_fails_closed(self):
  with h5py.File(self.source,'r+') as f:
   p='/frames/000000/raw_observation/robot0_joint_pos/value';del f[p];f.create_dataset(p,data=np.ones(7,dtype=np.float32))
  self.reject()
 def test_database_change_rejected_before_source(self):
  self.store.db.execute("update h_semantics set body='{}'");self.store.db.commit();r=self.get();self.assertEqual(r['status'],'invalid_database_identity');self.assertEqual(r['results'],[])
 def install_scratch_primary_proof(self):
  self.support=self.root/'support.py';self.support.write_text('primary reference bytes\n');self.proof=self.root/'PRIMARY_SOURCES.json';self.proof.write_text(json.dumps(dict(files=[dict(path=str(self.support),sha256=sha(self.support))])))
  raw,body=self.store.db.execute('select raw_id,body from h_semantics').fetchone();s=json.loads(body);s['traceability']=[p for p in s['traceability'] if not p['path'].endswith('/PRIMARY_SOURCES.json')]+[dict(path=str(self.proof),sha256=sha(self.proof))];s['id']='semantics:'+digest({k:v for k,v in s.items() if k!='id'});self.store.db.execute('update h_semantics set body=?',(canonical(s).decode(),));self.store.db.commit();self.store.verifier.verify(str(self.database),sha(self.database));st=self.database.stat();self.store.database_signature=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
 def test_primary_reference_modification_rejected(self):
  self.install_scratch_primary_proof();self.assertEqual(self.get()['status'],'ok');self.support.write_text('altered reference\n');self.reject()
 def test_missing_primary_reference_rejected(self):
  self.install_scratch_primary_proof();self.assertEqual(self.get()['status'],'ok');self.support.unlink();self.reject()
 def test_cached_proof_manifest_modification_rejected(self):
  self.install_scratch_primary_proof();self.assertEqual(self.get()['status'],'ok');self.proof.write_text('{}');self.reject()
 def test_primary_reference_restoration_reverified(self):
  self.install_scratch_primary_proof();original=self.support.read_bytes();self.assertEqual(self.get()['status'],'ok');self.support.write_bytes(b'changed');self.reject();self.support.write_bytes(original);self.assertEqual(self.get()['status'],'ok')
