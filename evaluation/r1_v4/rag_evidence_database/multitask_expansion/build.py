"""One approved batch appended to a copy of the immutable Phase5C release."""
import sqlite3,time,resource,os,socket
from pathlib import Path
from collections import Counter
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.libero_measurement_reader.reader import read
from evaluation.r1_v4.rag_evidence_database.build import execution_units
from evaluation.r1_v4.rag_evidence_database.store import Store
from .plan import HERE,DEST
from .profile import PREFIX,folder,approved_profile
BASE=Path('/disk/1/data/niktakbr/trustworthy-phase5d-working/final-validated/corpus-89.sqlite')
BASE_SHA='dc7baad9b343f67a4dad243419b6fa85723a3410cac2c0a452c7565f7ff91c0e'

def input_binding(task,episode):
 NAME=PREFIX+task
 profile_dir=folder(task)
 profile=approved_profile(NAME,DEST,episode)
 selected=[r for r in profile['bindings'] if Path(r['restored_path']).parent.name==f'episode_{episode:03d}' or Path(r['restored_path']).name in ('task.bddl','benchmark_initial_states.init')]
 assert len(selected)==11
 for row in selected:assert sha(row['restored_path'])==row['sha256']
 paths=[HERE/'build.py',HERE/'profile.py',REPO/'evaluation/r1_v4/rag_evidence_database/corpus_expansion/task_profile/native.py',REPO/'evaluation/r1_v4/libero_measurement_reader/reader.py',REPO/'evaluation/r1_v4/rag_evidence_database/build.py',REPO/'evaluation/r1_v4/rag_evidence_database/store.py',REPO/'evaluation/r1_v4/rag_evidence_database/search.py']
 return {'profile':NAME,'profile_sha256':profile['profile_sha256'],'sources':selected,'window_frames':32,'stratum':'corpus_expansion','study_partition':'unclassified_database_use_only','code_bindings':{str(p.relative_to(REPO)):sha(p) for p in paths}}

def populate(path):
 assert socket.gethostname().lower()=='hestia' and sha(BASE)==BASE_SHA
 path=Path(path).resolve();assert path.is_relative_to('/disk/1/data/niktakbr') and path!=BASE
 assert os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize>500*10**9
 if not path.exists():
  with path.open('xb'):pass
  original=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);dest=sqlite3.connect(path);original.backup(dest);original.close();dest.close()
 db=Store(path,writable=True);old=Store(BASE)
 old_ids={r.id for r in old.records()};old.close();assert len(old_ids)==21791
 plan=load(HERE/'SOURCE_PLAN.json');timings=[];skipped=[];tick=time.perf_counter()
 try:
  for task,entry in [(k,e) for k,t in sorted(plan['tasks'].items()) for e in sorted(t['executions'],key=lambda e:e['episode'])]:
   NAME=PREFIX+task;profile_dir=folder(task);native=load(profile_dir/'NATIVE_PROFILE.json')
   scope={'mapping_path':str(profile_dir/'NATIVE_PROFILE.json'),'constraints_path':str(profile_dir/'NATIVE_PROFILE.json'),'constraints_selector':'/objects/','surface_ids':native['surface_ids'],'surface_roots':native['surface_roots'],'surface_selector':'/mapping/geometries native static fixtures','geometry_status':'UNSUPPORTED','development_only':False,'study_partition':'unclassified_database_use_only'}
   start=time.perf_counter();episode=entry['episode'];execution=entry['execution_id']
   try:
    bindings=input_binding(task,episode);key=digest(bindings)
    if db.finished(execution,key):skipped.append(episode);continue
    result=read(DEST,episode,task_profile=NAME)
    if result.status!='verified_measurements' or result.synthetic:raise ValueError('source compatibility rejected:'+str(result.diagnostics))
    if any(len(s.camera_references)!=2 for s in result.frames):raise ValueError('configured camera references incomplete')
    units=execution_units(result,bindings,source_scope=scope);db.put_execution(execution,key,units,stratum='corpus_expansion',independent=True)
    timings.append({'task':task,'episode':episode,'execution_id':execution,'frames':len(result.frames),'records':len(units),'seconds':time.perf_counter()-start,'field_inventory':result.metadata['field_inventory'],'unsupported_fields':sorted({d.code for d in result.diagnostics})})
    print('Indexed',task,episode,len(result.frames),len(units),flush=True);del result,units
   except Exception as error:
    with db.db:db.db.execute('INSERT INTO rag_failures(execution,reason) VALUES(?,?)',(execution,type(error).__name__+': '+str(error)))
    raise
  all_records=db.records();assert old_ids<={r.id for r in all_records}
  report=db.snapshot();assert len(report['executions'])==285
  assert sha(BASE)==BASE_SHA
  return {**report,'task_profiles':sorted(plan['tasks']),'baseline_ids_preserved':21791,'baseline_executions_preserved':89,'new_executions':196,'timings':timings,'skipped_episodes':skipped,'elapsed_seconds':time.perf_counter()-tick,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'database_path':str(path),'database_bytes':path.stat().st_size,'baseline_sha256':BASE_SHA,'record_types':dict(Counter(r.measurement_type for r in all_records)),'stratum_counts':dict(db.db.execute('SELECT stratum,count(*) FROM rag_units GROUP BY stratum'))}
 finally:db.close()
if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));out=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working')
 write_new(out/'BUILD_MANIFEST.json',populate(out/'corpus-285.sqlite'))
