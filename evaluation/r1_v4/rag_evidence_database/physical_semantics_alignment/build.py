"""Copy-only migration with immutable annotation transactions and idempotent resume."""
import json,sqlite3,time,socket
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import canonical,digest
from .config import BASE,BASE_SHA,WORK
from .store import PhysicalStore,producers
from .semantics import make

def populate(path):
 assert socket.gethostname()=='hestia';path=Path(path);assert path.resolve().is_relative_to(WORK) and path!=BASE and sha(BASE)==BASE_SHA
 start=time.perf_counter();audit=json.loads((WORK/'AUDIT_FINAL.json').read_text());velocity=json.loads((WORK/'VELOCITY_VALIDATION.json').read_text());proofs=json.loads((WORK/'PRIMARY_SOURCES.json').read_text())
 proofs['validation_artifacts']=[dict(path=str(WORK/n),sha256=sha(WORK/n)) for n in ('AUDIT_FINAL.json','VELOCITY_VALIDATION.json','PRIMARY_SOURCES.json')]
 assert audit['contract_failures']==0 and audit['executions']==432 and audit['variants']==104 and velocity['passed']
 assert json.loads((WORK/'BASELINE_VERIFIED.json').read_text())['passed']
 if not path.exists():
  with sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(path) as b:a.backup(b)
 db=PhysicalStore(path,writable=True);by={r['execution_id']:r for r in audit['rows']};vp={r['execution_id']:r for r in velocity['rows']};inserted=skipped=0
 try:
  for proof in proofs['files']+proofs['validation_artifacts']:db.verifier.verify(proof['path'],proof['sha256'],'verified_session')
  for file in sorted((WORK/'models').glob('*.json')):
   m=json.loads(file.read_text());value=canonical(m).decode();old=db.db.execute('select body from h_models where variant=?',(m['variant_id'],)).fetchone()
   if old and old[0]!=value:raise ValueError('immutable model changed')
   with db.db:db.db.execute('insert or ignore into h_models values(?,?)',(m['variant_id'],value))
  for e,r in sorted(by.items()):
   key=digest(dict(base=BASE_SHA,producer=producers(),execution=r,velocity=vp[e],proofs=proofs));old=db.db.execute('select input_digest,row_digest,status from h_jobs where execution=?',(e,)).fetchone();raw=[json.loads(v[0]) for v in db.db.execute('select body from rag_channel_records where execution=? order by channel',(e,))];assert len(raw)==6
   db.verifier.verify(r['source_path'],r['source_sha256'],'verified_session');db.verifier.verify(r['model_map_path'],r['model_map_sha256'],'verified_session');db.verifier.verify(r['metadata_path'],r['metadata_sha256'],'verified_session')
   if old:
    assert db.db.execute('select body from h_execution where execution=?',(e,)).fetchone()[0]==canonical(r).decode()
    current=[json.loads(v[0]) for v in db.db.execute('select body from h_semantics where execution=? order by channel',(e,))];assert old==(key,digest(current),'complete');skipped+=1;continue
   db.verifier.verify(r['source_path'],r['source_sha256'],'verified_session');db.verifier.verify(r['model_map_path'],r['model_map_sha256'],'verified_session');annotations=[make(x,r,vp[e],proofs) for x in raw]
   with db.db:
    db.db.execute('insert into h_execution values(?,?)',(e,canonical(r).decode()))
    for a in annotations:db.db.execute('insert into h_semantics values(?,?,?,?)',(a['raw_record_id'],e,a['channel_id'],canonical(a).decode()))
    db.db.execute('insert into h_jobs values(?,?,?,?)',(e,key,digest(annotations),'complete'))
   inserted+=len(annotations)
   if inserted//6%50==0:print('Interpretation executions',inserted//6,flush=True)
  assert db.db.execute('pragma integrity_check').fetchall()==[('ok',)] and not db.db.execute('pragma foreign_key_check').fetchall()
  return dict(**db.snapshot(),inserted=inserted,skipped=skipped,seconds=time.perf_counter()-start,database_path=str(path),database_bytes=path.stat().st_size,database_sha256=sha(path),base_sha256=BASE_SHA)
 finally:db.close()
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('database',type=Path);p.add_argument('--report',required=True,type=Path);a=p.parse_args();r=populate(a.database)
 with a.report.open('x') as f:json.dump(r,f,sort_keys=True,indent=2)
 print(r,flush=True)
