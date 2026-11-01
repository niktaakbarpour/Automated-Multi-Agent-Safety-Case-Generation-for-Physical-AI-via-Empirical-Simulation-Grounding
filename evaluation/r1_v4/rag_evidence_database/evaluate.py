"""Source-target relevance evaluation, not physical ground truth."""
import statistics,time
from dataclasses import asdict
from .search import Query,search
from .store import Store
from evaluation.r1_v4.provenance import write_new,canonical


def evaluate(path,out):
 db=Store(path);records=db.records();fixtures=[];expected_sources={r.id:(r.source_path,r.source_sha256,r.selector) for r in records}
 executions=sorted({r.execution_id for r in records})
 objects=sorted({r.object_id for r in records if r.kind=='raw_measurement'})
 def target(execution,obj,typ,frame=None):
  return sorted(r.id for r in records if r.execution_id==execution and r.object_id==obj and r.measurement_type==typ and (frame is None or r.interval[0]<=frame<=r.interval[1]))
 for execution in executions:
  fixtures.append({'name':'execution:'+execution,'query':asdict(Query(execution_id=execution,evidence_types=('execution_metadata',))), 'relevant':target(execution,'*','execution_metadata')})
  fixtures.append({'name':'instruction:'+execution,'query':asdict(Query(execution_id=execution,evidence_types=('task_instruction',),text='alphabet soup tomato sauce')), 'relevant':target(execution,'*','task_instruction')})
  for obj in objects:
   for typ,frame,text in [('object_identity',None,obj),('object_pose',33,'pose'),('contact',0,'contact')]:
    fixtures.append({'name':f'{execution}:{obj}:{typ}','query':asdict(Query(execution_id=execution,object_id=obj,evidence_types=(typ,),interval=(frame,frame) if frame is not None else None,text=text)), 'relevant':target(execution,obj,typ,frame)})
 fixtures.append({'name':'unfiltered-task-instructions','query':asdict(Query(evidence_types=('task_instruction',),text='alphabet soup tomato sauce')), 'relevant':sorted(r.id for r in records if r.measurement_type=='task_instruction')})
 rows=[];latencies=[]
 for fixture in fixtures:
  assert fixture['relevant'],fixture['name'];q=Query(**fixture['query']);tick=time.perf_counter();found=search(db,q);latencies.append(time.perf_counter()-tick)
  repeated=search(db,q);assert canonical(found)==canonical(repeated)
  ids=[r['id'] for r in found['results']];relevant=set(fixture['relevant']);hit=set(ids)&relevant
  rank=next((i+1 for i,key in enumerate(ids) if key in relevant),None)
  rows.append({'name':fixture['name'],'precision_at_1':float(bool(ids and ids[0] in relevant)),'recall_at_1':float(bool(ids and ids[0] in relevant))/len(relevant),'recall_at_20':len(hit)/len(relevant),'precision_returned_at_20':len(hit)/len(ids) if ids else 0.,'reciprocal_rank':1/rank if rank else 0.,'returned':len(ids),'expected':len(relevant),'source_attribution_correct':all((r['record']['source_path'],r['record']['source_sha256'],r['record']['selector'])==expected_sources[r['id']] for r in found['results'])})
 # Directly specified development frame coverage and missing-frame target.
 gaps=[]
 for execution in executions:
  terminal=max(r.interval[1] for r in records if r.execution_id==execution and r.kind=='raw_measurement')
  result=search(db,Query(execution_id=execution,object_id='cream_cheese_1',evidence_types=('object_pose','contact'),interval=(0,terminal+1),limit=1))
  assert all(c['missing_intervals']==[[terminal+1,terminal+1]] for c in result['coverage'].values())
  gaps.append({'execution':execution,'terminal_frame':terminal,'reported_missing':[[terminal+1,terminal+1]]})
 db.close()
 report={'schema_version':'1.0.0','queries':len(rows),'queries_with_text':sum(bool(f['query']['text']) for f in fixtures),'macro_precision_at_1':statistics.mean(r['precision_at_1'] for r in rows),'macro_recall_at_1':statistics.mean(r['recall_at_1'] for r in rows),'macro_recall_at_20':statistics.mean(r['recall_at_20'] for r in rows),'macro_precision_returned_at_20':statistics.mean(r['precision_returned_at_20'] for r in rows),'MRR':statistics.mean(r['reciprocal_rank'] for r in rows),'source_attribution_fraction':sum(r['source_attribution_correct'] for r in rows)/len(rows),'temporal_gap_cases_correct':len(gaps),'latency_seconds':{'median':statistics.median(latencies),'p95':sorted(latencies)[int(.95*(len(latencies)-1))],'max':max(latencies)},'relevance_protocol':'Known development source-document/measurement selectors; no physical labels; purposive small one-task corpus, not a semantic-generalization benchmark. Precision-returned uses actual returned results, not fixed 20 denominator.','results':rows,'gap_cases':gaps}
 write_new(out/'QUERY_FIXTURES.json',fixtures);write_new(out/'RETRIEVAL_METRICS.json',report)
 return report
