"""Additive physical contracts over preserved Phase 5G tables."""
import json
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import ChannelStore,owned
from evaluation.r1_v4.provenance import digest,canonical
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import HERE,VERSION
from .source_integrity import SourceVerifier,SourceError

def producers():return {n:sha(HERE/n) for n in ('config.py','semantics.py','schema.sql','build.py','EVIDENCE_CONTRACTS.md','source_integrity.py','store.py')}

class PhysicalStore(ChannelStore):
 def __init__(self,path,writable=False,expected_sha256=None):
  import socket
  if socket.gethostname()!='hestia':raise RuntimeError('Research access requires Hestia')
  self.verifier=SourceVerifier();fd=self.verifier.open_fd(path)
  import os
  self.database_path=str(path);self.database_signature=tuple((os.fstat(fd).st_dev,os.fstat(fd).st_ino,os.fstat(fd).st_size,os.fstat(fd).st_mtime_ns,os.fstat(fd).st_ctime_ns));os.close(fd)
  self.database_verified=False
  if expected_sha256 is not None:
   self.verifier.verify(str(path),expected_sha256,'strict');self.database_verified=True
  super().__init__(path,writable=writable);self.binding_cache={}
  exists=self.db.execute("select 1 from sqlite_master where name='h_meta'").fetchone()
  if not exists:
   if not writable:raise ValueError('physical migration missing')
   self.db.executescript((HERE/'schema.sql').read_text())
   with self.db:self.db.executemany('insert into h_meta values(?,?)',[('version',VERSION),('producer',canonical(producers()).decode())])
  if dict(self.db.execute('select key,value from h_meta'))!={'version':VERSION,'producer':canonical(producers()).decode()}:raise ValueError('physical schema/producer mismatch')
 def check_binding(self,b,mode):
  generation=(self.db.execute('pragma data_version').fetchone()[0],self.db.total_changes);key=(digest(b),generation)
  v=json.loads(self.db.execute('select body from rag_env_variants where id=?',(b['variant_id'],)).fetchone()[0]);paths=[(b[k+'_path'],b[k+'_sha256']) for k in ('xml','asset_manifest','mapping')]+[(a['path'],a['sha256']) for a in v['assets']]
  if b.get('profile_path'):paths.append((b['profile_path'],b['profile_sha256']))
  for p,h in paths:self.verifier.verify(str(owned(p)),h,mode)
  if key not in self.binding_cache:super().verify_binding(b);self.binding_cache[key]=True
 def snapshot(self):
  tables=('h_meta','h_models','h_execution','h_semantics','h_jobs');values={t:self.db.execute('select * from '+t+' order by 1').fetchall() for t in tables}
  return dict(version=VERSION,logical_digest=digest(values),contracts=len(values['h_semantics']),executions=len(values['h_jobs']),variants=len(values['h_models']))
