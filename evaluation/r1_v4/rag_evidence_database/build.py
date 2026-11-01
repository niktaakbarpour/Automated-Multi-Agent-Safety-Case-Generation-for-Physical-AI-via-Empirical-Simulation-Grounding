"""Read-only population, bounded to one validated execution in memory."""
import resource,socket,time,os,csv,json
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.provenance import load,digest,canonical,write_new
from evaluation.r1_v4.libero_measurement_reader.reader import read,MAP
from evaluation.r1_v4.evidence_registry_gsn.builder import ROOT,REPO,sha
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from .store import Store,HERE
EPISODES=(0,1,2,14)
WINDOW=32
POLICY='1.0.0'
LIMITS=('Physical support, fall witnesses and negative certificates remain blocked.','Saved snapshot availability is not continuous physical coverage.','Camera exposure alignment and physical geometry/cache phase uncertainty are unresolved.')

def input_binding(ep):
 sources=[r for r in load(HERE.parent/'libero_measurement_reader/RESTORED_SOURCES.json') if Path(r['restored_path']).parent.name==f'episode_{ep:03d}' or Path(r['restored_path']).name in ('task.bddl','benchmark_initial_states.init')]
 for r in sources:
  if sha(r['restored_path'])!=r['sha256']:raise ValueError('source hash mismatch:'+r['restored_path'])
 return {'sources':sources,'policy':POLICY,'window':WINDOW,'producer_sha256':{n:sha(HERE/n) for n in ('build.py','store.py','search.py','catalog.py','migration.sql','catalog_migration.sql')},'supporting_hashes':{str(p):sha(p) for p in [REPO/'reports/fall_review_v2_20261016/constraints_and_identities.json',HERE.parent/'evidence_review_readiness/AI_REFERENCE_REVIEWS.csv',HERE.parent/'evidence_review_readiness/UPDATED_EVIDENCE_GATES.csv',HERE.parent/'evidence_review_readiness/EMPIRICAL_READINESS.md']},'reader_sha256':sha(HERE.parent/'libero_measurement_reader/reader.py'),'map_sha256':sha(MAP),'requirement_sha256':sha(REPO/'requirements/r1_generalized_v2/R1_V2_SPECIFICATION.md')}

def execution_units(result,binding,*,source_scope=None):
 scope=source_scope or {};map_path=Path(scope.get('mapping_path',MAP));constraint_path=Path(scope.get('constraints_path',REPO/'reports/fall_review_v2_20261016/constraints_and_identities.json'));surface_ids=scope.get('surface_ids',list(range(10,16)))
 meta=result.metadata;count=len(result.frames);h5=result.source_hashes['trajectory.h5'];run=result.source_hashes['run_metadata.json']
 common=dict(schema_version='1.0.0',requirement_id='R1',requirement_version='2.0.0',execution_id=result.execution_id,object_id='*',kind='document',source_path=run['path'],source_sha256=run['sha256'],selector='/',measurement_type='execution_metadata',validation_status='verified_source',capability={'source_identity':'VERIFIED'},clock='saved_frame_index',domain='frame',interval=(0,count-1),coordinate_frame='not_applicable_document',model_checkpoint=meta['checkpoint']+'@'+meta['checkpoint_revision'],benchmark=meta['task_suite'],task_id=meta['task_configuration_id'],producer='rag-evidence-database:'+POLICY,original=True,uncertainty=LIMITS,limitations=LIMITS,provenance={'development_only':scope.get('development_only',True),'study_partition':scope.get('study_partition','development'),'object_scope_kind':'source_declared_inventory_not_R1_configuration' if source_scope else 'existing_restricted_measurement_scope','prior_calibration_report_not_extended':bool(source_scope),'physical_truth':'U','input_binding_digest':digest(binding),'reader_binding':result.reader_binding,'temporal_semantics':'Saved endpoint time and last-forward caches are not identical physical instants.'})
 def document(kind,path,selector,text,obj='*',deps=()):
  r=Record(**{**common,'object_id':obj,'source_path':str(path),'source_sha256':sha(path),'selector':selector,'measurement_type':kind,'dependencies':deps,'original':str(path)==run['path'] or 'requirements/r1_generalized_v2' in str(path)}).validate()
  return (r,text,'execution:'+result.execution_id+('/object:'+obj if obj!='*' else ''))
 units=[]
 units.append(document('execution_metadata',run['path'],'/',f"Execution {result.execution_id}; model {meta['checkpoint']} revision {meta['checkpoint_revision']}; task {meta['task_name']}; {count} discrete saved frames. Development only."))
 units.append(document('task_instruction',run['path'],'/instruction',meta['instruction']))
 units.append(document('requirement_definition',REPO/'requirements/r1_generalized_v2/R1_V2_SPECIFICATION.md','/', (REPO/'requirements/r1_generalized_v2/R1_V2_SPECIFICATION.md').read_text()))
 units.append(document('calibration_provenance',HERE.parent/'evidence_review_readiness/UPDATED_EVIDENCE_GATES.csv','CSV all twelve gates',(HERE.parent/'evidence_review_readiness/UPDATED_EVIDENCE_GATES.csv').read_text()))
 units.append(document('evidence_limitations',HERE.parent/'evidence_review_readiness/EMPIRICAL_READINESS.md','/', (HERE.parent/'evidence_review_readiness/EMPIRICAL_READINESS.md').read_text()))
 for obj,identity in sorted(result.native_geometry['objects'].items()):
  constraints=constraint_path
  root=document('object_identity',constraints,scope.get('constraints_selector','/objects/')+obj,f"Object {obj}; native body {identity['body_id']}; collision geometry IDs {identity['collision_geom_ids']}; complete native mapping retained.",obj);units.append(root)
  surface=document('support_surface_identity',map_path,scope.get('surface_selector','/geometries native IDs 10:16'),f"Static source fixture references for {obj}; roots {scope.get('surface_roots',['living_room_table'])}; native collision IDs {surface_ids}; load-bearing relationship not established.",obj);units.append(surface)
  for start in range(0,count,WINDOW):
   snapshots=result.frames[start:start+WINDOW];stop=snapshots[-1].index
   for typ,fields in [('object_pose','body_xpos,body_xquat'),('contact','contacts'),('native_geometry','geom_xpos,geom_xmat'),('robot_state','qpos,qvel,ctrl'),('timestamp','time'),('camera_reference','agentview_image,robot0_eye_in_hand_image')]:
    cap={'measurement_availability':'VERIFIED','physical_checking':'BLOCKED_ON_EVIDENCE'}
    if typ=='camera_reference':cap['exposure_alignment']='UNSUPPORTED'
    if typ=='native_geometry':cap['geometry_admission']=scope.get('geometry_status','CONDITIONALLY_SUPPORTED')
    prov={**common['provenance'],'body_id':identity['body_id'],'collision_geom_ids':identity['collision_geom_ids'],'surface_ids':surface_ids,'saved_indices':[s.index for s in snapshots],'endpoint_time_range':[snapshots[0].endpoint_time,snapshots[-1].endpoint_time],'camera_ids':['agentview_image','robot0_eye_in_hand_image'] if typ=='camera_reference' else [],'camera_capture_times':None,'native_map_sha256':sha(map_path),'source_metadata_ref':units[0][0].id,'raw_values_stored':False}
    selector=f'/frames/{start:06d}..{stop:06d}/'+('raw_observation/' if typ=='camera_reference' else 'simulator/')+fields
    record=Record(**{**common,'object_id':obj,'kind':'raw_measurement','source_path':h5['path'],'source_sha256':h5['sha256'],'selector':selector,'measurement_type':typ,'validation_status':'verified_measurement','capability':cap,'interval':(start,stop),'coordinate_frame':'unverified_camera_pixel_frame' if typ=='camera_reference' else 'MuJoCo_native_mixed_units' if typ=='robot_state' else 'MuJoCo_world','dependencies':(root[0].id,surface[0].id),'provenance':prov}).validate()
    text=f"{typ.replace('_',' ')} measurements for {obj}; execution {result.execution_id}; saved frames {start} through {stop}; fields {fields}; endpoint seconds {snapshots[0].endpoint_time} through {snapshots[-1].endpoint_time}. Values remain in hash-bound original source. No physical event or safety label."
    units.append((record,text,f'execution:{result.execution_id}/object:{obj}/window:{start}:{stop}'))
 reviews=HERE.parent/'evidence_review_readiness/AI_REFERENCE_REVIEWS.csv'
 for row in csv.DictReader(reviews.open()):
  if row['execution_id']!=result.execution_id:continue
  frames=json.loads(row['numerical_frames_actually_inspected'])
  if not frames:continue
  obj=row['object_id'];record=Record(**{**common,'object_id':obj,'kind':'ai_reference_judgment','source_path':str(reviews),'source_sha256':sha(reviews),'selector':'CSV candidate_id='+row['candidate_id'],'measurement_type':'ai_reference_interpretation','validation_status':'provisional','original':False,'producer':'phase2b4_exposed_AI_review','interval':(min(frames),max(frames)),'capability':{'independent_physical_reference':'BLOCKED_ON_EVIDENCE'},'provenance':{**common['provenance'],'human_ground_truth':False,'independent_human_confirmation':False}}).validate()
  units.append((record,'Provisional AI interpretation '+row['candidate_id']+': '+row['proposed_AI_classification']+'. '+row['outstanding_uncertainty'], 'execution:'+result.execution_id+'/object:'+obj+'/AI_review'))
 return units

def populate(path,episodes=EPISODES):
 if socket.gethostname().lower()!='hestia':raise RuntimeError('Hestia only')
 if any(ep not in EPISODES for ep in episodes):raise ValueError('Outside verified development contract')
 if os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize<500*10**9:raise RuntimeError('disk1 reserve insufficient')
 store=Store(path,create=not Path(path).exists(),writable=True);start=time.perf_counter();timings=[];skipped=[]
 try:
  for ep in episodes:
   tick=time.perf_counter();execution=f'libero_long_openvla_oft_task00_seed{1000+ep}_trial{ep:03d}_cfafd9ddc3db'
   try:
    binding=input_binding(ep);key=digest(binding)
    if store.finished(execution,key):skipped.append(ep);continue
    result=read(ROOT,ep)
    if result.status!='verified_measurements':raise ValueError('reader:'+str(result.diagnostics))
    units=execution_units(result,binding);store.put_execution(execution,key,units)
    timings.append({'episode':ep,'frames':len(result.frames),'records':len(units),'seconds':time.perf_counter()-tick})
    del result,units
   except Exception as e:
    with store.db:store.db.execute('INSERT INTO rag_failures(execution,reason) VALUES(?,?)',(execution,type(e).__name__+': '+str(e)))
    raise
  catalog_count=0
  if store.db.execute("SELECT count(*) FROM rag_jobs WHERE status='complete'").fetchone()[0]==4:
   from .catalog import populate_catalog
   catalog_count=populate_catalog(store,load(HERE/'SOURCE_COVERAGE_MANIFEST.json'))
  build=store.snapshot()
  return {**build,'catalog_count':catalog_count,'timings':timings,'skipped_episodes':skipped,'elapsed_seconds':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'database_path':str(Path(path).resolve()),'database_bytes':Path(path).stat().st_size}
 finally:store.close()
