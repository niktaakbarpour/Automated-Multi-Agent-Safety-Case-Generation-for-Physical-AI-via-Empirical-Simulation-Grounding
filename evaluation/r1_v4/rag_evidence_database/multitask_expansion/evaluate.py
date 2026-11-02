"""Independent source-selector relevance, never physical-event relevance."""
import time,statistics
from dataclasses import asdict
from evaluation.r1_v4.provenance import load,write_new,canonical
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from .plan import HERE,DEST
from .profile import folder
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def evaluate(path,out):
 db=Store(path);records=db.records();plan=load(HERE/'SOURCE_PLAN.json');by_scope={};expected_hashes={};fixtures=[];rows=[];latency=[]
 for r in records:by_scope.setdefault((r.execution_id,r.object_id,r.measurement_type),[]).append(r)
 def add(name,query):
  q=Query(**query);candidates=by_scope[(q.execution_id,q.object_id,q.evidence_types[0])]
  relevant=[r for r in candidates if q.interval is None or r.interval[0]<=q.interval[0]<=r.interval[1]];assert len(relevant)==1
  target=relevant[0]
  task,data,entry=next((k,t,e) for k,t in plan['tasks'].items() for e in t['executions'] if e['execution_id']==q.execution_id)
  root=DEST/task/f"episode_{entry['episode']:03d}"
  if q.evidence_types[0] in ('execution_metadata','task_instruction'):
   assert target.source_path==str(root/'run_metadata.json') and target.selector==('/' if q.evidence_types[0]=='execution_metadata' else '/instruction')
  elif q.evidence_types[0]=='object_identity':
   assert target.source_path==str(folder(task)/'NATIVE_PROFILE.json') and target.selector=='/objects/'+q.object_id
  else:
   fields={'object_pose':'body_xpos,body_xquat','contact':'contacts','native_geometry':'geom_xpos,geom_xmat','robot_state':'qpos,qvel,ctrl','timestamp':'time','camera_reference':'agentview_image,robot0_eye_in_hand_image'}
   assert target.source_path==str(root/'trajectory.h5') and tuple(target.interval)==(0,min(31,entry['frames']-1))
   assert target.selector=='/frames/000000..'+str(min(31,entry['frames']-1)).zfill(6)+'/'+('raw_observation/' if q.evidence_types[0]=='camera_reference' else 'simulator/')+fields[q.evidence_types[0]]
  if target.source_path not in expected_hashes:expected_hashes[target.source_path]=sha(target.source_path)
  assert target.source_sha256==expected_hashes[target.source_path]
  fixtures.append({'name':name,'query':asdict(q),'relevant':[target.id],'source_path':target.source_path,'source_sha256':target.source_sha256,'source_selector':target.selector})
 for task,entry in [(k,e) for k,t in sorted(plan['tasks'].items()) for e in t['executions']]:
  execution=entry['execution_id'];common={'execution_id':execution,'stratum':'corpus_expansion'}
  add(execution+':metadata',{**common,'object_id':'*','evidence_types':('execution_metadata',)})
  add(execution+':instruction',{**common,'object_id':'*','evidence_types':('task_instruction',),'text':'basket'})
  objects=sorted({r.object_id for r in records if r.execution_id==execution and r.kind=='raw_measurement'})
  for obj in objects:
   for typ,text in [('object_identity',obj),('object_pose','pose'),('contact','contact'),('native_geometry','geometry')]:
    add(execution+':'+obj+':'+typ,{**common,'object_id':obj,'evidence_types':(typ,),'interval':None if typ=='object_identity' else (10,10),'text':text})
  for typ,text in [('robot_state','robot state'),('timestamp','timestamp'),('camera_reference','camera reference')]:
   add(execution+':'+typ,{**common,'object_id':objects[0],'evidence_types':(typ,),'interval':(10,10),'text':text})
 write_new(out/'QUERY_FIXTURES.json',fixtures)
 for query_index,fixture in enumerate(fixtures):
  q=Query(**fixture['query']);tick=time.perf_counter();result=search(db,q);latency.append(time.perf_counter()-tick);
  if query_index%100==0:assert canonical(result)==canonical(search(db,q));print('Retrieval probe',query_index,'of',len(fixtures),flush=True)
  returned=result['results'];expected=set(fixture['relevant']);hit=bool(returned and returned[0]['id'] in expected)
  assert hit and result['matching_count']==1 and not result['safety_claim_verified']
  assert (returned[0]['record']['source_path'],returned[0]['record']['source_sha256'],returned[0]['record']['selector'])==(fixture['source_path'],fixture['source_sha256'],fixture['source_selector'])
  rows.append({'name':fixture['name'],'precision_at_1':1.,'recall_at_20':1.,'reciprocal_rank':1.})
 gaps=[];isolation=[]
 for task,entry in [(k,e) for k,t in sorted(plan['tasks'].items()) for e in t['executions']]:
  result=search(db,Query(execution_id=entry['execution_id'],object_id=plan['tasks'][task]['objects'][0],evidence_types=('object_pose','contact','native_geometry','robot_state','timestamp','camera_reference'),interval=(0,entry['frames']),limit=1,stratum='corpus_expansion'))
  assert all(c['missing_intervals']==[[entry['frames'],entry['frames']]] for c in result['coverage'].values());gaps.append(entry['execution_id'])
  assert not search(db,Query(execution_id=entry['execution_id'],stratum='development'))['results'];isolation.append(entry['execution_id'])
 db.close()
 metrics={'schema_version':'1.0.0','queries':len(fixtures),'text_queries':sum(bool(f['query'].get('text')) for f in fixtures),'precision_at_1':1.,'recall_at_20':1.,'MRR':1.,'source_attribution_fraction':1.,'gap_cases':len(gaps),'gap_measurement_type_checks':len(gaps)*6,'stratum_isolation_cases':len(isolation),'latency_seconds':{'median':statistics.median(latency),'p95':sorted(latency)[int(.95*(len(latency)-1))],'max':max(latency)},'qualification':'Exact source-target relevance over new nonreserved corpus; templates and metadata filters, not physical safety accuracy or an independent semantic/paraphrase benchmark.','results':rows,'per_task':{task:{'queries':sum(f['query']['execution_id'] in {e['execution_id'] for e in data['executions']} for f in fixtures),'precision_at_1':1.,'recall_at_20':1.,'MRR':1.} for task,data in plan['tasks'].items()}}
 write_new(out/'RETRIEVAL_METRICS.json',metrics);return metrics
