"""Independent source-selector relevance, never physical-event relevance."""
import time,statistics
from dataclasses import asdict
from evaluation.r1_v4.provenance import load,write_new,canonical
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from .plan import HERE

def evaluate(path,out):
 db=Store(path);records=db.records();plan=load(HERE/'SOURCE_PLAN.json');by_scope={};fixtures=[];rows=[];latency=[]
 for r in records:by_scope.setdefault((r.execution_id,r.object_id,r.measurement_type),[]).append(r)
 def add(name,query):
  q=Query(**query);candidates=by_scope[(q.execution_id,q.object_id,q.evidence_types[0])]
  relevant=[r for r in candidates if q.interval is None or r.interval[0]<=q.interval[0]<=r.interval[1]];assert len(relevant)==1
  target=relevant[0];fixtures.append({'name':name,'query':asdict(q),'relevant':[target.id],'source_path':target.source_path,'source_sha256':target.source_sha256,'source_selector':target.selector})
 for entry in plan['executions']:
  execution=entry['execution_id'];common={'execution_id':execution,'stratum':'corpus_expansion'}
  add(execution+':metadata',{**common,'object_id':'*','evidence_types':('execution_metadata',)})
  add(execution+':instruction',{**common,'object_id':'*','evidence_types':('task_instruction',),'text':'salad dressing basket'})
  objects=sorted({r.object_id for r in records if r.execution_id==execution and r.kind=='raw_measurement'})
  for obj in objects:
   for typ,text in [('object_identity',obj),('object_pose','pose'),('contact','contact'),('native_geometry','geometry')]:
    add(execution+':'+obj+':'+typ,{**common,'object_id':obj,'evidence_types':(typ,),'interval':None if typ=='object_identity' else (10,10),'text':text})
  for typ,text in [('robot_state','robot state'),('timestamp','timestamp'),('camera_reference','camera reference')]:
   add(execution+':'+typ,{**common,'object_id':'salad_dressing_1','evidence_types':(typ,),'interval':(10,10),'text':text})
 for fixture in fixtures:
  q=Query(**fixture['query']);tick=time.perf_counter();result=search(db,q);latency.append(time.perf_counter()-tick);assert canonical(result)==canonical(search(db,q))
  returned=result['results'];expected=set(fixture['relevant']);hit=bool(returned and returned[0]['id'] in expected)
  assert hit and result['matching_count']==1 and not result['safety_claim_verified']
  assert (returned[0]['record']['source_path'],returned[0]['record']['source_sha256'],returned[0]['record']['selector'])==(fixture['source_path'],fixture['source_sha256'],fixture['source_selector'])
  rows.append({'name':fixture['name'],'precision_at_1':1.,'recall_at_20':1.,'reciprocal_rank':1.})
 gaps=[];isolation=[]
 for entry in plan['executions']:
  result=search(db,Query(execution_id=entry['execution_id'],object_id='salad_dressing_1',evidence_types=('object_pose','contact','native_geometry','robot_state','timestamp','camera_reference'),interval=(0,entry['frames']),limit=1,stratum='corpus_expansion'))
  assert all(c['missing_intervals']==[[entry['frames'],entry['frames']]] for c in result['coverage'].values());gaps.append(entry['execution_id'])
  assert not search(db,Query(execution_id=entry['execution_id'],stratum='development'))['results'];isolation.append(entry['execution_id'])
 db.close();write_new(out/'QUERY_FIXTURES.json',fixtures)
 metrics={'schema_version':'1.0.0','queries':len(fixtures),'text_queries':sum(bool(f['query'].get('text')) for f in fixtures),'precision_at_1':1.,'recall_at_20':1.,'MRR':1.,'source_attribution_fraction':1.,'gap_cases':len(gaps),'gap_measurement_type_checks':len(gaps)*6,'stratum_isolation_cases':len(isolation),'latency_seconds':{'median':statistics.median(latency),'p95':sorted(latency)[int(.95*(len(latency)-1))],'max':max(latency)},'qualification':'Exact source-target relevance over new nonreserved corpus; templates and metadata filters, not physical safety accuracy or an independent semantic/paraphrase benchmark.','results':rows}
 write_new(out/'RETRIEVAL_METRICS.json',metrics);return metrics
