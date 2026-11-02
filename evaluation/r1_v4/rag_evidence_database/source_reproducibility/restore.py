"""Content-bound explicit restore maps; no fallback to original paths."""
import json,shutil,sqlite3
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.retrieve import read_samples
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
from .config import WORK
from .build import enc

def create(database,executions,root):
 root=Path(root);root.mkdir(parents=True,exist_ok=False);(root/'objects').mkdir()
 c=sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True);entries={};v=SourceVerifier()
 for ex in executions:
  if not c.execute("select 1 from rag_scope_status where execution=? and status='indexed'",(ex,)).fetchone():raise SourceError('restore_scope_not_indexed')
  for p,h in c.execute('select distinct a.path,a.sha256 from i_artifacts a join i_scope_nodes s on a.id=s.node where s.execution=?',(ex,)):
   p=str(owned(p));key=p+'#'+h
   if key not in entries:
    dest=root/'objects'/h
    with v.access(p,h,'strict') as (f,att):
     if not dest.exists():
      with dest.open('wb') as out:shutil.copyfileobj(f,out)
    if sha(dest)!=h:raise SourceError('restore_copy_hash_mismatch')
    entries[key]=dict(canonical_path=p,sha256=h,relative_path='objects/'+h,executions=[])
   entries[key]['executions'].append(ex)
 shutil.copyfile(database,root/'database.sqlite')
 manifest=dict(version=1,database_sha256=sha(database),executions=sorted(executions),entries=entries,assurance='verified_source_values_with_bounded_graph_artifacts',historical_reexecution=False)
 (root/'RESTORE.json').write_text(enc(manifest));return dict(manifest_sha256=sha(root/'RESTORE.json'),files=len(entries),unique_bytes=sum(p.stat().st_size for p in (root/'objects').iterdir()))

class RestoredRelease:
 def __init__(self,root,manifest_sha256):
  self.root=Path(root);self.v=SourceVerifier();self.manifest_sha256=manifest_sha256
  with self.v.access(str(self.root/'RESTORE.json'),manifest_sha256,'strict') as (f,a):self.manifest=json.load(f)
  self.v.verify(str(self.root/'database.sqlite'),self.manifest['database_sha256'],'strict')
  self.db=sqlite3.connect('file:'+str(self.root/'database.sqlite')+'?mode=ro',uri=True)
 def access(self,p,h,ex):
  p=str(owned(p));e=self.manifest['entries'].get(p+'#'+h)
  if not e or ex not in e['executions'] or ex not in self.manifest['executions']:raise SourceError('unmapped_restore_source_or_scope')
  rel=Path(e['relative_path'])
  if rel.is_absolute() or '..' in rel.parts or rel.parts!=('objects',h):raise SourceError('invalid_restore_path')
  return self.v.access(str(self.root/rel),h,'strict')
 def verify(self,ex):
  self.v.verify(str(self.root/'RESTORE.json'),self.manifest_sha256,'strict');self.v.verify(str(self.root/'database.sqlite'),self.manifest['database_sha256'],'strict')
  if ex not in self.manifest['executions']:raise SourceError('outside_restored_scope')
  for p,h in self.db.execute('select distinct a.path,a.sha256 from i_artifacts a join i_scope_nodes s on a.id=s.node where s.execution=?',(ex,)):
   with self.access(p,h,ex):pass
 def samples(self,ex,channel,frames):
  self.verify(ex)
  pair=self.db.execute('select r.body,s.body from rag_channel_records r join h_semantics s on r.id=s.raw_id where r.execution=? and r.channel=?',(ex,channel)).fetchone()
  if not pair:raise SourceError('unknown_restored_channel')
  raw,sem=map(json.loads,pair);execution=json.loads(self.db.execute('select body from h_execution where execution=?',(ex,)).fetchone()[0])
  with self.access(raw['source_path'],raw['source_sha256'],ex) as (f,a):return read_samples(f,raw,sem,frames,execution)
