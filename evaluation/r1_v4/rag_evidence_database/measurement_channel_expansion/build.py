"""Separate additive database, immutable series references, transactional resume."""
import json,time,sqlite3,hashlib,os
from pathlib import Path
import h5py
from evaluation.r1_v4.provenance import canonical,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .channels import HERE,WORK,BASE,BASE_SHA,VERSION,CHANNELS,contract,sample,ChannelStore,execution_sources,require_hestia

def producers():return {n:sha(HERE/n) for n in ('channels.py','build.py','schema.sql','CHANNEL_SELECTION.json','EVIDENCE_CONTRACTS.md')}

def make_records(store,execution,path,source_sha,producer):
 b=store.binding(execution);store.verify_binding(b);store.verify_file(path,source_sha);records=[]
 with h5py.File(path,'r') as f:
  keys={int(k):k for k in f['frames']}
  if len(keys)!=len(f['frames']):raise ValueError('ambiguous numeric frame keys')
  for channel in CHANNELS:
   c=contract(channel);valid=[];invalid={};shapes={};hasher=hashlib.sha256()
   for i,key in sorted(keys.items()):
    selector='/frames/'+key+'/'+c['field'];a,reason=sample(f.get(selector),channel)
    if reason:invalid[str(i)]=reason;continue
    valid.append(i);shapes[str(a.dtype)+' '+str(tuple(a.shape))]=shapes.get(str(a.dtype)+' '+str(tuple(a.shape)),0)+1
    hasher.update(canonical({'frame':i,'selector':selector,'dtype':str(a.dtype),'shape':list(a.shape)}));hasher.update(a.tobytes(order='C'))
   r=dict(version=VERSION,execution_id=execution,task_id=b['task_id'],variant_id=b['variant_id'],channel_id=channel,object_id=c['object_id'],source_path=path,source_sha256=source_sha,source_field=c['field'],xml_path=b['xml_path'],xml_sha256=b['xml_sha256'],mapping_path=b['mapping_path'],mapping_sha256=b['mapping_sha256'],contract=c,contract_sha256=digest(c),producer=producer,valid_indices=valid,invalid_samples=invalid,frame_keys={str(i):k for i,k in sorted(keys.items())},dtype_shapes=shapes,sample_count=len(valid),sample_digest=hasher.hexdigest(),origin='direct_recording',derived=False,spatial_observation=False,empirical_admission_enabled=False)
   r['id']='channel:'+digest(r);records.append(r)
 return records

def populate(path):
 require_hestia();path=Path(path);assert path!=BASE and path.resolve().is_relative_to(WORK)
 assert sha(BASE)==BASE_SHA
 assert json.loads((HERE/'CHANNEL_SELECTION.json').read_text())['frozen_before_extraction']
 started=time.perf_counter();producer=producers()
 if not path.exists():
  # SQLite backup copies database pages only; no recording corpus is duplicated.
  with sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(path) as target:source.backup(target)
 store=ChannelStore(path,writable=True);inserted=skipped=0
 try:
  for execution,p,h in execution_sources(store):
   binding=store.binding(execution);key=digest(dict(source=p,sha256=h,binding=binding,producer=producer))
   old=store.db.execute('select input_digest,record_digest,status from rag_channel_jobs where execution=?',(execution,)).fetchone()
   if old:
    current=[json.loads(r[0]) for r in store.db.execute('select body from rag_channel_records where execution=? order by channel',(execution,))]
    if old!=(key,digest(current),'complete'):raise ValueError('immutable producer/input/job content changed')
    store.verify_file(p,h);store.verify_binding(binding);skipped+=1;continue
   records=make_records(store,execution,p,h,producer);records.sort(key=lambda r:r['channel_id'])
   with store.db:
    for r in records:
     store.db.execute('insert into rag_channel_records values(?,?,?,?,?,?,?)',(r['id'],execution,r['task_id'],r['variant_id'],r['channel_id'],r['object_id'],canonical(r).decode()))
     store.db.execute('insert into rag_channel_fts values(?,?)',(r['id'],r['contract']['description']))
    store.db.execute('insert into rag_channel_jobs values(?,?,?,?)',(execution,key,digest(records),'complete'))
   inserted+=len(records)
   if (inserted//6)%25==0:print('Channel executions',inserted//6,'skipped',skipped,flush=True)
  assert store.db.execute('pragma integrity_check').fetchall()==[('ok',)] and not store.db.execute('pragma foreign_key_check').fetchall()
  snapshot=store.channel_snapshot();return dict(**snapshot,inserted=inserted,skipped=skipped,seconds=time.perf_counter()-started,database_path=str(path),database_bytes=path.stat().st_size,database_sha256=sha(path),producer=producer)
 finally:store.close()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('database',type=Path);p.add_argument('--report',required=True,type=Path);a=p.parse_args();r=populate(a.database)
 with a.report.open('x') as f:json.dump(r,f,sort_keys=True,indent=2)
 print(r,flush=True)
