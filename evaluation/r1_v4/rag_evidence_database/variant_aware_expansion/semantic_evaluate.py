"""Pinned local encoder reused unchanged, behind variant/execution guards."""
import time,statistics
from dataclasses import replace
from collections import defaultdict
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder,SemanticIndex,build,integrity,DESCRIPTIONS
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic_evaluate import PROBES
from .plan import HERE,WORK
from .registry import VariantStore
from .retrieval import VariantQuery,retrieve

def run():
 db=VariantStore(WORK/'expanded.sqlite');before=sha(WORK/'expanded.sqlite');encoder=Encoder();manifest=build(db,WORK/'semantic.sqlite',encoder);write_new(WORK/'SEMANTIC_BUILD.json',manifest);index=SemanticIndex(WORK/'semantic.sqlite',db,encoder);write_new(WORK/'SEMANTIC_INTEGRITY.json',integrity(index));cohort=load(HERE/'COHORT.json');rows=[];negative=[]
 try:
  for key,task in cohort['tasks'].items():
   for e in sorted(task['executions'],key=lambda e:e['episode']):
    obj=task['objects'][(e['episode']-1)%len(task['objects'])];b=db.binding(e['execution_id']);q=VariantQuery(execution_id=e['execution_id'],variant_id=b['variant_id'],task_id=b['task_id'],object_id=obj,evidence_types=tuple(DESCRIPTIONS),interval=(10,10),stratum='corpus_expansion',limit=20)
    candidates=retrieve(db,q);assert candidates['status']=='ok';targets={i['record']['measurement_type']:i['id'] for i in candidates['groups'][0]['result']['results']};assert len(targets)==6
    for typ,texts in PROBES.items():
     for text in texts:
      for method in ('fts5','semantic'):
       tick=time.perf_counter();r=retrieve(db,replace(q,text=text)) if method=='fts5' else retrieve(db,q,semantic_index=index,semantic_text=text);elapsed=time.perf_counter()-tick;items=[i for g in r['groups'] for i in g['result']['results']];ids=[i['id'] for i in items];target=targets[typ];rank=ids.index(target)+1 if target in ids else None
       assert all(i['record']['execution_id']==e['execution_id'] and i['record']['object_id']==obj for i in items) and all(g['variant_id']==b['variant_id'] for g in r['groups']) and not r['safety_claim_verified']
       rows.append({'task':key,'execution_id':e['execution_id'],'variant_id':b['variant_id'],'object_id':obj,'text':text,'target_type':typ,'target_id':target,'method':method,'precision_at_1':float(rank==1),'recall_at_20':float(rank is not None),'reciprocal_rank':1/rank if rank else 0.,'seconds':elapsed})
    other=db.db.execute('SELECT id FROM rag_env_variants WHERE id!=? LIMIT 1',(b['variant_id'],)).fetchone()[0]
    for name,bad,expected in [('variant',replace(q,variant_id=other),'invalid_query_scope'),('execution',replace(q,execution_id='missing:'+e['execution_id']),'unknown_execution'),('field',replace(q,field_name='camera_exposure_timestamp'),'unavailable_timestamp')]:
     r=retrieve(db,bad,semantic_index=index,semantic_text='object location');assert r['status']==expected and not r['matching_count'];negative.append({'execution_id':e['execution_id'],'case':name,'status':r['status']})
    if e['episode']%10==0:print('Semantic scopes',key,e['episode'],flush=True)
  # A valid registry document excluded from the semantic sidecar must stay unreturned.
  e=next(iter(cohort['tasks'].values()))['executions'][0]['execution_id'];r=retrieve(db,VariantQuery(execution_id=e,evidence_types=('execution_metadata',)),semantic_index=index,semantic_text='task metadata');assert r['status']=='unindexed_semantic_family' and not r['matching_count']
  def metrics(values):return {'query_instances':len(values),**{k:statistics.mean(r[k] for r in values) for k in ('precision_at_1','recall_at_20','reciprocal_rank')},'median_seconds':statistics.median(r['seconds'] for r in values)}
  report={'passed':True,'unique_linguistic_probes':len({r['text'] for r in rows}),'unique_objects':len({r['object_id'] for r in rows}),'source_execution_scopes':len({r['execution_id'] for r in rows}),'source_variants':len({r['variant_id'] for r in rows}),'aggregate':{m:metrics([r for r in rows if r['method']==m]) for m in ('fts5','semantic')},'per_task':{t:{m:metrics([r for r in rows if r['method']==m and r['task']==t]) for m in ('fts5','semantic')} for t in cohort['tasks']},'negative_scope_cases':negative,'invalid_cross_scope_retrievals':0,'unembedded_document_excluded':True,'qualification':'Twelve fixed source-field paraphrases reused from Phase5E; rotating objects fixed by episode modulo object count. Query instances are repetitions across source contexts, not independent natural-language judgments or physical ground truth. Recall@20 has six candidates. No descriptor/model/probe tuning.','results':rows}
  write_new(WORK/'SEMANTIC_EVALUATION.json',report);assert sha(WORK/'expanded.sqlite')==before
  return report
 finally:index.close();db.close()
if __name__=='__main__':print(run()['aggregate'])
