"""Prospective original-source targets; all task/variant attribution is explicit."""
import time,statistics
from collections import defaultdict,Counter
from dataclasses import asdict,replace
from evaluation.r1_v4.provenance import load,write_new,canonical
from .registry import VariantStore
from .retrieval import VariantQuery,retrieve
from .plan import HERE,WORK
FIELDS={'object_pose':'body_xpos,body_xquat','contact':'contacts','native_geometry':'geom_xpos,geom_xmat','robot_state':'qpos,qvel,ctrl','timestamp':'time','camera_reference':'agentview_image,robot0_eye_in_hand_image'}
TEXT={'object_pose':'pose','contact':'contact','native_geometry':'geometry','robot_state':'robot state','timestamp':'timestamp','camera_reference':'camera reference'}

def run():
 db=VariantStore(WORK/'expanded.sqlite');cohort=load(HERE/'COHORT.json');entries={e['execution_id']:(k,t,e) for k,t in cohort['tasks'].items() for e in t['executions']};by=defaultdict(list)
 for r in db.records():by[(r.execution_id,r.object_id,r.measurement_type)].append(r)
 fixtures=[]
 def add(execution,obj,kind,scope,text,case):
  b=db.binding(execution);records=by[(execution,obj,kind)];targets=[r for r in records if scope is None or r.interval[0]<=scope[1] and r.interval[1]>=scope[0]];assert targets
  if kind in FIELDS and execution in entries:
   k,t,e=entries[execution];source=next(f for f in cohort['files'] if f['execution_id']==execution and f['restored_path'].endswith('/trajectory.h5'))
   starts=range((scope[0]//32)*32,(scope[1]//32)*32+1,32);windows={(start,min(start+31,e['frames']-1)) for start in starts};assert {tuple(r.interval) for r in targets}==windows
   for r in targets:
    assert r.source_path==source['restored_path'] and r.source_sha256==source['expected_sha256'];assert r.selector==f'/frames/{r.interval[0]:06d}..{r.interval[1]:06d}/'+('raw_observation/' if kind=='camera_reference' else 'simulator/')+FIELDS[kind]
  q=VariantQuery(execution_id=execution,task_id=b['task_id'],variant_id=b['variant_id'],object_id=obj,evidence_types=(kind,),interval=scope,text=text,stratum='corpus_expansion' if execution in entries else None,field_name=FIELDS[kind].split(',')[0] if kind in FIELDS else None)
  fixtures.append({'case':case,'query':asdict(q),'expected':sorted(r.id for r in targets),'source_targets':[{'path':r.source_path,'sha256':r.source_sha256,'selector':r.selector} for r in targets],'variant_id':b['variant_id'],'task_id':b['task_id']})
 for execution,(key,task,e) in entries.items():
  obj=task['objects'][0]
  for name,point in [('initial',0),('middle',e['frames']//2),('terminal',e['frames']-1)]:
   for typ in FIELDS:add(execution,obj,typ,(point,point),TEXT[typ],name)
  for typ in ('object_pose','contact'):add(execution,obj,typ,(31,32),None,'boundary')
  add(execution,'*','execution_metadata',None,None,'metadata');add(execution,'*','task_instruction',None,None,'instruction')
  for obj in task['objects']:add(execution,obj,'object_identity',None,obj,'object_identity')
 # Old task behavior is checked with exact source-attributed metadata; no baseline data rewritten.
 old_tasks={}
 for execution,task in db.db.execute('SELECT execution,task_id FROM rag_execution_env ORDER BY execution'):
  if execution not in entries:old_tasks.setdefault(task,execution)
 baseline_counts={r['execution_id']:r['frames'] for r in load(HERE.parent/'multitask_expansion/validation/INDEXED_CORPUS.json')['per_execution']}
 for execution in old_tasks.values():
  add(execution,'*','execution_metadata',None,None,'baseline')
  obj=sorted({key[1] for key in by if key[0]==execution and key[2]=='object_pose'})[0]
  for point in (0,baseline_counts[execution]//2,baseline_counts[execution]-1):
   for typ in FIELDS:add(execution,obj,typ,(point,point),None,'baseline_raw')
 write_new(WORK/'QUERY_FIXTURES.json',fixtures);rows=[];latencies=[]
 for i,f in enumerate(fixtures):
  q=VariantQuery(**f['query']);tick=time.perf_counter();r=retrieve(db,q);latencies.append(time.perf_counter()-tick);assert r['status']=='ok' and len(r['groups'])==1
  group=r['groups'][0];items=group['result']['results'];assert {m['id'] for m in items}==set(f['expected']);assert group['execution_id']==q.execution_id and group['task_id']==f['task_id'] and group['variant_id']==f['variant_id'];assert not r['safety_claim_verified']
  actual={(m['record']['source_path'],m['record']['source_sha256'],m['record']['selector']) for m in items};assert actual=={(m['path'],m['sha256'],m['selector']) for m in f['source_targets']}
  if i%200==0:assert canonical(r)==canonical(retrieve(db,q));print('Validated source query',i,'/',len(fixtures),flush=True)
  rows.append({'task_id':group['task_id'],'variant_id':group['variant_id'],'execution_id':q.execution_id,'case':f['case'],'precision_at_1':1.,'recall_at_20':1.,'MRR':1.})
 def summary(values):return {'queries':len(values),'precision_at_1':1.,'recall_at_20':1.,'MRR':1.,'source_attribution':1.,'task_attribution':1.,'execution_attribution':1.,'variant_attribution':1.,'temporal_correctness':1.,'invalid_cross_scope_retrievals':0}
 metrics={**summary(rows),'per_task':{t:summary([r for r in rows if r['task_id']==t]) for t in sorted({r['task_id'] for r in rows})},'per_variant':{v:summary([r for r in rows if r['variant_id']==v]) for v in sorted({r['variant_id'] for r in rows})},'latency_seconds':{'median':statistics.median(latencies),'p95':sorted(latencies)[int(.95*(len(latencies)-1))],'max':max(latencies)},'qualification':'Exact source-target lookup under metadata and variant constraints. Not independent natural-language relevance or physical safety accuracy.','results':rows}
 write_new(WORK/'RETRIEVAL_METRICS.json',metrics);db.close();return metrics
if __name__=='__main__':print(run()['queries'])
