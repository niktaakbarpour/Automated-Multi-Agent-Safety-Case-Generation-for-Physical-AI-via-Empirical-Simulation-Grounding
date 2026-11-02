"""Expanded source-retrieval targets; no physical relevance labels."""
import statistics,time
from dataclasses import asdict
from evaluation.r1_v4.rag_evidence_database.evaluate import evaluate as base_evaluate
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from evaluation.r1_v4.provenance import load,write_new,canonical
from .profile import HERE

def evaluate(path,out):
 base=base_evaluate(path,out);db=Store(path);records=db.records();profile=load(HERE/'VALIDATED_SOURCE_PROFILE.json');queries=[];rows=[];latencies=[]
 for entry in profile['executions'].values():
  for typ,text in [('native_geometry','geometry'),('robot_state','robot state'),('timestamp','timestamp'),('camera_reference','camera reference')]:
   q=Query(execution_id=entry['execution_id'],object_id='cream_cheese_1',evidence_types=(typ,),interval=(10,10),text=text)
   relevant=[r for r in records if r.execution_id==entry['execution_id'] and r.object_id=='cream_cheese_1' and r.measurement_type==typ and r.interval[0]<=10<=r.interval[1]];assert len(relevant)==1
   tick=time.perf_counter();result=search(db,q);latencies.append(time.perf_counter()-tick);assert canonical(result)==canonical(search(db,q))
   returned=result['results'];expected=relevant[0];hit=bool(returned and returned[0]['id']==expected.id)
   assert hit and result['matching_count']==1 and not result['safety_claim_verified']
   assert (returned[0]['record']['source_path'],returned[0]['record']['source_sha256'],returned[0]['record']['selector'])==(expected.source_path,expected.source_sha256,expected.selector)
   queries.append({'query':asdict(q),'expected_id':expected.id,'source_sha256':expected.source_sha256,'source_selector':expected.selector});rows.append({'precision_at_1':float(hit),'recall_at_20':float(hit),'reciprocal_rank':float(hit)})
 db.close();write_new(out/'ADDITIONAL_QUERY_FIXTURES.json',queries)
 n=base['queries'];m=len(rows)
 report={'schema_version':'1.0.0','base_queries':n,'additional_queries':m,'total_queries':n+m,'text_queries':base['queries_with_text']+m,'macro_precision_at_1':(base['macro_precision_at_1']*n+sum(r['precision_at_1'] for r in rows))/(n+m),'macro_recall_at_1':(base['macro_recall_at_1']*n+m)/(n+m),'macro_recall_at_20':(base['macro_recall_at_20']*n+sum(r['recall_at_20'] for r in rows))/(n+m),'MRR':(base['MRR']*n+sum(r['reciprocal_rank'] for r in rows))/(n+m),'source_attribution_fraction':1.,'terminal_gap_cases_correct':len(base['gap_cases']),'base_latency_seconds':base['latency_seconds'],'additional_latency_seconds':{'median':statistics.median(latencies),'p95':sorted(latencies)[int(.95*(len(latencies)-1))],'max':max(latencies)},'qualification':'Known source selectors and exact scoped text; not physical safety understanding or independent semantic/paraphrase evaluation. Unfiltered shared instruction query has forty relevant documents; top-20 recall is bounded by k.'}
 write_new(out/'EXPANDED_RETRIEVAL_METRICS.json',report);return report
