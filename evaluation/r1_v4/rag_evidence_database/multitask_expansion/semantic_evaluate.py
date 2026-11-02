"""Prospective source-field paraphrases; no physical-event relevance labels."""
import time,statistics
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from .semantic import Encoder,SemanticIndex,build,DESCRIPTIONS,integrity
from .plan import HERE
PROBES={
 'object_pose':['where is the object located','item translation and quaternion'],
 'contact':['which collision bodies touch','separation distances at contact points'],
 'native_geometry':['collision shape spatial layout','native geometry world rotation'],
 'robot_state':['joint configuration angles and velocities','robot control inputs'],
 'timestamp':['recorded observation time in seconds','saved endpoint timestamp'],
 'camera_reference':['linked images from the wrist camera','external agentview frame references']}

def evaluate(path,out):
 db=Store(path);encoder=Encoder();sidecar=out/'semantic.sqlite';manifest=build(db,sidecar,encoder);write_new(out/'SEMANTIC_BUILD.json',manifest);index=SemanticIndex(sidecar,db,encoder);plan=load(HERE/'SOURCE_PLAN.json');rows=[];write_new(out/'SEMANTIC_INTEGRITY.json',integrity(index))
 try:
  for task,data in plan['tasks'].items():
   for episode in (1,25,49):
    e=next(e for e in data['executions'] if e['episode']==episode);obj=data['objects'][0];q=Query(execution_id=e['execution_id'],object_id=obj,evidence_types=tuple(DESCRIPTIONS),interval=(10,10),stratum='corpus_expansion',limit=20)
    candidates=search(db,q);assert candidates['matching_count']==6
    targets={item['record']['measurement_type']:item['id'] for item in candidates['results']}
    for typ,probes in PROBES.items():
     for text in probes:
      expected=targets[typ]
      for method in ('fts5','semantic'):
       tick=time.perf_counter()
       if method=='fts5':
        from dataclasses import replace
        result=search(db,replace(q,text=text))
       else:result=index.retrieve(q,text)
       elapsed=time.perf_counter()-tick;ids=[r['id'] for r in result['results']];rank=ids.index(expected)+1 if expected in ids else None
       assert not result['safety_claim_verified'] and not result['empirical_admission_enabled']
       rows.append({'task':task,'execution_id':e['execution_id'],'object_id':obj,'text':text,'target_type':typ,'target_id':expected,'method':method,'precision_at_1':float(rank==1),'recall_at_20':float(rank is not None),'reciprocal_rank':1/rank if rank else 0.,'latency_seconds':elapsed})
  def metrics(values):
   return {**{k:statistics.mean(r[k] for r in values) for k in ('precision_at_1','recall_at_20','reciprocal_rank')},'queries':len(values),'median_latency_seconds':statistics.median(r['latency_seconds'] for r in values)}
  report={'qualification':'Source-field paraphrase probes over six valid measurement candidates, metadata constrained. Descriptions use source field semantics; hand-written templates, not independently human-labeled natural queries or physical safety understanding. Recall@20 is weak with only six candidates.','aggregate':{m:metrics([r for r in rows if r['method']==m]) for m in ('fts5','semantic')},'per_task':{t:{m:metrics([r for r in rows if r['method']==m and r['task']==t]) for m in ('fts5','semantic')} for t in plan['tasks']},'results':rows}
  write_new(out/'SEMANTIC_EVALUATION.json',report);return report
 finally:index.close();db.close()
