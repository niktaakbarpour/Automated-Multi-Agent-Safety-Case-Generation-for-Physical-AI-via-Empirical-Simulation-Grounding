"""Bounded variant-aware append; original release and every baseline row retained."""
import sqlite3,time,resource,socket,os
from pathlib import Path
from collections import Counter
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.rag_evidence_database.build import execution_units
from evaluation.r1_v4.libero_measurement_reader.reader import read
from .plan import HERE,WORK,DEST,BASE,BASE_SHA
from .profile import directory,PREFIX
from .registry import VariantStore
from .baseline import initialize

def input_binding(key,e):
 folder=directory(e['execution_id']);p=load(folder/'PROFILE.json')
 for r in p['source_bindings']:
  if sha(r['restored_path'])!=r['sha256']:raise ValueError('changed source:'+r['restored_path'])
 paths=[HERE/'build.py',HERE/'profile.py',HERE/'identity.py',HERE.parent/'build.py',HERE.parent/'store.py',REPO/'evaluation/r1_v4/libero_measurement_reader/reader.py',HERE.parent/'corpus_expansion/task_profile/native.py']
 return {'extraction_version':'phase5f:1.0.0','profile':PREFIX+key,'profile_sha256':sha(folder/'PROFILE.json'),'sources':p['source_bindings'],'variant_id':p['variant_id'],'cohort_sha256':sha(HERE/'COHORT.json'),'source_code_bindings':{str(p.relative_to(REPO)):sha(p) for p in paths},'window_frames':32,'stratum':'corpus_expansion','study_partition':'unclassified_database_use_only'}

def binding_for(key,task,e):
 folder=directory(e['execution_id']);native=load(folder/'NATIVE_PROFILE.json');identity=load(folder/'VARIANT.json');root=DEST/key/f"episode_{e['episode']:03d}"
 return identity,{'execution_id':e['execution_id'],'task_id':task['task']['task_id'],'suite':key.split('/')[0],'partition':key,'variant_id':identity['variant_id'],'xml_path':str(root/'simulator.xml'),'xml_sha256':identity['xml_sha256'],'asset_content_digest':identity['asset_content_digest'],'asset_manifest_path':str(root/'simulator_asset_manifest.json'),'asset_manifest_sha256':sha(root/'simulator_asset_manifest.json'),'mapping_path':str(folder/'NATIVE_PROFILE.json'),'mapping_sha256':sha(folder/'NATIVE_PROFILE.json'),'mapping_version':native['mapping']['schema_version'],'profile_path':str(folder/'PROFILE.json'),'profile_sha256':sha(folder/'PROFILE.json'),'objects':native['objects'],'logical_fixture_bindings':native['logical_fixture_bindings'],'unresolved_logical_fixtures':native['unresolved_logical_fixtures'],'validation_scope':'Read-only source identities, recorded channels and exact native model binding; no physical predicate validity.'}

def populate(path):
 if socket.gethostname().lower()!='hestia' or sha(BASE)!=BASE_SHA:raise ValueError('host/baseline')
 path=Path(path).resolve()
 if not path.is_relative_to(WORK) or path.suffix!='.sqlite':raise ValueError('new owned Phase5F SQLite path required')
 if os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize<500000000000:raise ValueError('disk1 reserve')
 if not path.exists():
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb'):pass
  source=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);target=sqlite3.connect(path);source.backup(target);target.close();source.close()
 db=VariantStore(path,writable=True);initialize(db);cohort=load(HERE/'COHORT.json');admitted=set(load(HERE/'ADMITTED_COHORT.json')['execution_ids']);timings=[];skipped=[];tick=time.perf_counter()
 try:
  for key,task in sorted(cohort['tasks'].items()):
   for e in sorted(task['executions'],key=lambda e:e['episode']):
    if e['execution_id'] not in admitted:
     db.set_status(e['execution_id'],'unsupported_mapping',key,'Source/profile validation rejected; see preserved diagnostics');continue
    start=time.perf_counter();binding=input_binding(key,e);identity,environment=binding_for(key,task,e);db.register(identity,environment);job=digest(binding)
    if db.finished(e['execution_id'],job):skipped.append(e['execution_id']);db.set_status(e['execution_id'],'indexed',key,'Verified completed job');continue
    result=read(DEST,e['episode'],task_profile=PREFIX+key)
    if result.status!='verified_measurements' or result.synthetic:raise ValueError('reader rejection:'+str(result.diagnostics))
    native=load(directory(e['execution_id'])/'NATIVE_PROFILE.json');scope={'mapping_path':environment['mapping_path'],'constraints_path':environment['mapping_path'],'constraints_selector':'/objects/','surface_ids':native['surface_ids'],'surface_roots':native['surface_roots'],'surface_selector':'/mapping/geometries verified static fixture references only','geometry_status':'UNSUPPORTED','development_only':False,'study_partition':'unclassified_database_use_only'}
    units=execution_units(result,binding,source_scope=scope);db.put_execution(e['execution_id'],job,units,stratum='corpus_expansion',independent=True);db.set_status(e['execution_id'],'indexed',key,'Verified completed job')
    timings.append({'execution_id':e['execution_id'],'task':key,'variant_id':identity['variant_id'],'frames':len(result.frames),'records':len(units),'seconds':time.perf_counter()-start});print('Indexed',key,e['episode'],len(units),flush=True);del result,units
  manifest=db.variant_snapshot();assert manifest['bound_executions']==285+len(admitted) and sha(BASE)==BASE_SHA
  return {**manifest,'timings':timings,'skipped':skipped,'elapsed_seconds':time.perf_counter()-tick,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'database_path':str(path),'database_bytes':path.stat().st_size,'new_executions':len(admitted),'baseline_evidence_ids_preserved':67053}
 except Exception as error:
  with db.db:db.db.execute('INSERT INTO rag_failures(execution,reason) VALUES(?,?)',('phase5f',type(error).__name__+':'+str(error)))
  raise
 finally:db.close()
if __name__=='__main__':
 import sys
 write_new(WORK/'BUILD_MANIFEST.json',populate(Path(sys.argv[1]) if len(sys.argv)>1 else WORK/'expanded.sqlite'))
