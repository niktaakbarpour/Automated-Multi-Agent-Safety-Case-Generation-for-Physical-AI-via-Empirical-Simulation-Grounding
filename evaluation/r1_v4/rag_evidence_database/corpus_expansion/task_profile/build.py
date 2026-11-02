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
from .profile import NAME,approved_profile
BASE=Path('/disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite')
BASE_SHA='e5dc6aadd9444d945abe9aeb1c54461b0cd6ad5308b43c6fdc40fac65c8d07ca'

def input_binding(episode):
 profile=approved_profile(NAME,DEST,episode)
 selected=[r for r in profile['bindings'] if Path(r['restored_path']).parent.name==f'episode_{episode:03d}' or Path(r['restored_path']).name in ('task.bddl','benchmark_initial_states.init')]
 assert len(selected)==11
 for row in selected:assert sha(row['restored_path'])==row['sha256']
 paths=[HERE/'build.py',HERE/'profile.py',HERE/'native.py',REPO/'evaluation/r1_v4/libero_measurement_reader/reader.py',REPO/'evaluation/r1_v4/rag_evidence_database/build.py',REPO/'evaluation/r1_v4/rag_evidence_database/store.py',REPO/'evaluation/r1_v4/rag_evidence_database/search.py']
 return {'profile':NAME,'profile_sha256':profile['profile_sha256'],'sources':selected,'window_frames':32,'stratum':'corpus_expansion','study_partition':'unclassified_database_use_only','code_bindings':{str(p.relative_to(REPO)):sha(p) for p in paths}}

def populate(path):
 assert socket.gethostname().lower()=='hestia' and sha(BASE)==BASE_SHA
 path=Path(path).resolve();assert path.is_relative_to('/disk/1/data/niktakbr') and path!=BASE
 assert os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize>500*10**9
 if not path.exists():
  with path.open('xb'):pass
  original=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);dest=sqlite3.connect(path);original.backup(dest);original.close();dest.close()
 db=Store(path,writable=True);old=Store(BASE)
 old_ids={r.id for r in old.records()};old.close();assert len(old_ids)==11830
 plan=load(HERE/'SOURCE_PLAN.json');native=load(HERE/'NATIVE_PROFILE.json');timings=[];skipped=[];tick=time.perf_counter()
 scope={'mapping_path':str(HERE/'NATIVE_PROFILE.json'),'constraints_path':str(HERE/'NATIVE_PROFILE.json'),'constraints_selector':'/objects/','surface_ids':native['surface_ids'],'surface_roots':native['surface_roots'],'surface_selector':'/mapping/geometries native static fixture IDs '+str(native['surface_ids']),'geometry_status':'UNSUPPORTED','development_only':False,'study_partition':'unclassified_database_use_only'}
 try:
  for entry in sorted(plan['executions'],key=lambda r:r['episode']):
   start=time.perf_counter();episode=entry['episode'];execution=entry['execution_id']
   try:
    bindings=input_binding(episode);key=digest(bindings)
    if db.finished(execution,key):skipped.append(episode);continue
    result=read(DEST,episode,task_profile=NAME)
    if result.status!='verified_measurements' or result.synthetic:raise ValueError('source compatibility rejected:'+str(result.diagnostics))
    if any(len(s.camera_references)!=2 for s in result.frames):raise ValueError('configured camera references incomplete')
    units=execution_units(result,bindings,source_scope=scope);db.put_execution(execution,key,units,stratum='corpus_expansion',independent=True)
    timings.append({'episode':episode,'execution_id':execution,'frames':len(result.frames),'records':len(units),'seconds':time.perf_counter()-start,'field_inventory':result.metadata['field_inventory'],'unsupported_fields':sorted({d.code for d in result.diagnostics})})
    print('Indexed object/task02',episode,len(result.frames),len(units),flush=True);del result,units
   except Exception as error:
    with db.db:db.db.execute('INSERT INTO rag_failures(execution,reason) VALUES(?,?)',(execution,type(error).__name__+': '+str(error)))
    raise
  all_records=db.records();assert old_ids<={r.id for r in all_records}
  report=db.snapshot();assert len(report['executions'])==89
  assert sha(BASE)==BASE_SHA
  return {**report,'task_profile':NAME,'baseline_ids_preserved':11830,'baseline_executions_preserved':40,'new_executions':49,'timings':timings,'skipped_episodes':skipped,'elapsed_seconds':time.perf_counter()-tick,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'database_path':str(path),'database_bytes':path.stat().st_size,'baseline_sha256':BASE_SHA,'record_types':dict(Counter(r.measurement_type for r in all_records)),'stratum_counts':dict(db.db.execute('SELECT stratum,count(*) FROM rag_units GROUP BY stratum'))}
 finally:db.close()
if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));out=Path('/disk/1/data/niktakbr/trustworthy-phase5d-working')
 write_new(out/'BUILD_MANIFEST.json',populate(out/'corpus-89.sqlite'))
