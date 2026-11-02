"""Original-source targets at middle/end windows and window boundaries."""
import statistics,time
from collections import defaultdict
from evaluation.r1_v4.provenance import load,write_new,canonical
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from .plan import HERE,DEST

def evaluate(path,out):
 plan=load(HERE/'SOURCE_PLAN.json');db=Store(path);index=defaultdict(dict);fixtures=[];rows=[];latencies=[]
 for r in db.records():index[(r.execution_id,r.object_id,r.measurement_type)][tuple(r.interval)]=r
 fields={'object_pose':'body_xpos,body_xquat','contact':'contacts','native_geometry':'geom_xpos,geom_xmat'}
 for task,data in plan['tasks'].items():
  for e in data['executions']:
   obj=data['objects'][0];source=next(r for r in plan['files'] if r['execution_id']==e['execution_id'] and r['restored_path'].endswith('/trajectory.h5'));points=[('middle',(e['frames']//2,)*2),('last',(e['frames']-1,)*2)]
   for name,scope in points+[('boundary',(31,32))]:
    for typ in fields if name!='boundary' else ('object_pose','contact'):
     expected=[]
     for start in range(0,e['frames'],32):
      stop=min(start+31,e['frames']-1)
      if start>scope[1] or stop<scope[0]:continue
      r=index[(e['execution_id'],obj,typ)][(start,stop)];assert r.source_path==source['restored_path'] and r.source_sha256==source['expected_sha256'];assert r.selector==f'/frames/{start:06d}..{stop:06d}/simulator/'+fields[typ];expected.append(r.id)
     fixtures.append({'task':task,'execution_id':e['execution_id'],'object_id':obj,'type':typ,'interval':scope,'window_case':name,'expected':expected})
 write_new(out/'TEMPORAL_QUERY_FIXTURES.json',fixtures)
 for i,f in enumerate(fixtures):
  q=Query(execution_id=f['execution_id'],object_id=f['object_id'],evidence_types=(f['type'],),interval=tuple(f['interval']),stratum='corpus_expansion');tick=time.perf_counter();r=search(db,q);latencies.append(time.perf_counter()-tick);ids=[v['id'] for v in r['results']];assert set(ids)==set(f['expected']) and r['matching_count']==len(ids);assert not r['safety_claim_verified'] and all(not v['missing_intervals'] for v in r['coverage'].values())
  if i%196==0:assert canonical(r)==canonical(search(db,q))
  rows.append({'task':f['task'],'case':f['window_case'],'precision_at_1':1.,'recall_at_20':1.,'reciprocal_rank':1.})
 missing=0;isolated=0;tasks=list(plan['tasks'])
 for task,data in plan['tasks'].items():
  wrong=plan['tasks'][tasks[(tasks.index(task)+1)%len(tasks)]]['task']['task_id']
  for e in data['executions']:
   point=e['frames']//2;q=Query(execution_id=e['execution_id'],object_id=data['objects'][0],evidence_types=('contact_normal',),interval=(point,point));r=search(db,q);assert not r['results'] and r['coverage']['contact_normal']['missing_intervals']==[[point,point]] and not r['safety_claim_verified'];missing+=1
   r=search(db,Query(execution_id=e['execution_id'],task_id=wrong,evidence_types=('object_pose',),interval=(point,point)));assert not r['results'];isolated+=1
 db.close();report={'passed':True,'queries':len(rows),'precision_at_1':1.,'recall_at_20':1.,'MRR':1.,'source_attribution_fraction':1.,'per_task':{task:{'queries':sum(r['task']==task for r in rows),'precision_at_1':1.,'recall_at_20':1.,'MRR':1.} for task in tasks},'missing_type_queries':missing,'wrong_task_queries':isolated,'latency_seconds':{'median':statistics.median(latencies),'p95':sorted(latencies)[int(.95*(len(latencies)-1))],'max':max(latencies)},'qualification':'Exact original-source frame-window lookup; middle, terminal and boundary intervals. Missing normals are missing fields, not negative physical evidence. No safety/event labels.'}
 write_new(out/'TEMPORAL_RETRIEVAL_METRICS.json',report);return report
if __name__=='__main__':
 from pathlib import Path
 out=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/final-validated');print(evaluate(out/'corpus-285.sqlite',out))
