"""Copy immutable baseline, then append only new approved development executions."""
import sqlite3,socket,time,resource,os
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.libero_measurement_reader.reader import read
from evaluation.r1_v4.rag_evidence_database.build import execution_units
from evaluation.r1_v4.rag_evidence_database.store import Store
from .profile import HERE,ROOT,NAME,approved_profile
BASELINE=Path('/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite')
BASE_SHA='998827e38863e9dca7fd8fd21d8a77a50802a049ead11e2dad19081f580c7e9f'

def binding(episode):
 p=approved_profile(NAME,ROOT,episode)
 sources=[r for r in p['bindings'] if Path(r['restored_path']).parent.name==f'episode_{episode:03d}' or Path(r['restored_path']).name in ('task.bddl','benchmark_initial_states.init')]
 assert len(sources)==11
 for row in sources:assert sha(row['restored_path'])==row['sha256']
 return {'profile':NAME,'profile_sha256':p['profile_sha256'],'sources':sources,'window_frames':32,'code_bindings':{str(p.relative_to(REPO)):sha(p) for p in [HERE/'build.py',HERE/'profile.py',REPO/'evaluation/r1_v4/rag_evidence_database/build.py',REPO/'evaluation/r1_v4/libero_measurement_reader/reader.py']}}

def populate(path):
 assert socket.gethostname().lower()=='hestia';assert sha(BASELINE)==BASE_SHA
 path=Path(path).resolve();assert path.is_relative_to('/disk/1/data/niktakbr') and path!=BASELINE
 assert os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize>500*10**9
 if not path.exists():
  with path.open('xb'):pass
  original=sqlite3.connect(BASELINE.as_uri()+'?mode=ro',uri=True);copy=sqlite3.connect(path)
  original.backup(copy);original.close();copy.close()
 db=Store(path,writable=True);old_ids={r.id for r in db.records() if r.execution_id in {r['execution'] for r in load(HERE.parent/'validation/BUILD_MANIFEST.json')['executions']}}
 assert len(old_ids)==1360
 db.db.execute("CREATE INDEX IF NOT EXISTS rag_conflicts_present ON evidence(json_array_length(body,'$.conflicts'))")
 profile=load(HERE/'VALIDATED_SOURCE_PROFILE.json');timings=[];skipped=[];tick=time.perf_counter()
 try:
  for ep in sorted(map(int,profile['executions'])):
   start=time.perf_counter();entry=profile['executions'][str(ep)];execution=entry['execution_id']
   try:
    inputs=binding(ep);key=digest(inputs)
    if db.finished(execution,key):skipped.append(ep);continue
    result=read(ROOT,ep,development_profile=NAME)
    if result.status!='verified_measurements' or result.synthetic:raise ValueError('production source rejected:'+str(result.diagnostics))
    units=execution_units(result,inputs);db.put_execution(execution,key,units)
    timings.append({'episode':ep,'execution_id':execution,'frames':len(result.frames),'records':len(units),'seconds':time.perf_counter()-start})
    print('Indexed',ep,len(result.frames),len(units),flush=True)
    del result,units
   except Exception as e:
    with db.db:db.db.execute('INSERT INTO rag_failures(execution,reason) VALUES(?,?)',(execution,type(e).__name__+': '+str(e)))
    raise
  assert old_ids<={r.id for r in db.records()}
  manifest=db.snapshot();assert len(manifest['executions'])==40
  assert sha(BASELINE)==BASE_SHA
  return {**manifest,'expansion_profile':NAME,'baseline_evidence_ids_preserved':1360,'new_execution_count':36,'timings':timings,'skipped_episodes':skipped,'elapsed_seconds':time.perf_counter()-tick,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'database_path':str(path),'database_bytes':path.stat().st_size,'baseline_sha256':BASE_SHA}
 finally:db.close()

if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
 out=Path('/disk/1/data/niktakbr/trustworthy-phase5c-working')
 write_new(out/'BUILD_MANIFEST.json',populate(out/'development-40.sqlite'))
