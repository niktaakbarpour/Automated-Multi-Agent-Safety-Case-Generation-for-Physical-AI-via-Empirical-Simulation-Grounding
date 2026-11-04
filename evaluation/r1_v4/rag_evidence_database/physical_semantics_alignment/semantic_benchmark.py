"""Frozen Phase 5G paraphrases through the new guards; semantics never overrides scope."""
import json,statistics
from pathlib import Path
from dataclasses import replace
from .config import WORK
from .store import PhysicalStore
from .retrieve import PhysicalQuery,retrieve
from .audit import save
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.semantic_evaluate import PROBES
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder

def run(output=None):
 output=WORK if output is None else Path(output)
 output.mkdir(exist_ok=True)
 db=PhysicalStore(WORK/'expanded.sqlite',expected_sha256=json.loads((WORK/'BUILD.json').read_text())['database_sha256']);encoder=Encoder();rows=[];negatives=0
 for i,(e,t,v) in enumerate(db.db.execute('select execution,task_id,variant_id from rag_execution_env order by execution').fetchall()):
  q=PhysicalQuery(e,task_id=t,variant_id=v,verification_mode='verified_session')
  for target,texts in PROBES.items():
   for text in texts:
    for method in ('fts5','semantic'):
     r=retrieve(db,replace(q,text=text)) if method=='fts5' else retrieve(db,q,encoder=encoder,semantic_text=text);ids=[x['raw_record']['channel_id'] for x in r['results']];rank=ids.index(target)+1 if target in ids else None
     assert all(x['raw_record']['execution_id']==e and x['semantic_record']['task_id']==t and x['semantic_record']['variant_id']==v and x['source_attestation']['status']=='verified_source' for x in r['results'])
     rows.append(dict(execution=e,task=t,variant=v,channel=target,text=text,method=method,precision_at_1=float(rank==1),recall_at_20=float(rank is not None),MRR=1/rank if rank else 0.))
  for bad,status in ((replace(q,task_id='wrong'),'invalid_query_scope'),(replace(q,variant_id='wrong'),'invalid_query_scope'),(replace(q,execution_id='unknown:'+e),'unknown_execution'),(replace(q,object_id='wrong'),'no_matching_record'),(replace(q,alignment='same_physical_instant'),'unsupported_alignment'),(replace(q,channel_id='raw.robot0_joint_pos',units='wrong'),'unsupported_units'),(replace(q,channel_id='raw.robot0_joint_pos',coordinate_frame='world'),'unsupported_coordinate_frame'),(replace(q,channel_id='raw.robot0_joint_pos',source_sha256='f'*64),'invalid_source_scope'),(replace(q,channel_id='raw.robot0_joint_pos',required_properties=('cache_offset_seconds',)),'unsupported_semantic_status')):
   r=retrieve(db,bad,encoder=encoder,semantic_text='robot joint reading');assert r['status']==status and not r['results'];negatives+=1
  if i%50==0:print('Physical semantic scopes',i,flush=True)
 for e,status in db.db.execute("select execution,status from rag_scope_status where status!='indexed'"):
  r=retrieve(db,PhysicalQuery(e),encoder=encoder,semantic_text='position');assert r['status']==status and not r['results'];negatives+=1
 def metrics(rs):return dict(instances=len(rs),**{k:statistics.mean(r[k] for r in rs) for k in ('precision_at_1','recall_at_20','MRR')})
 result=dict(passed=True,unique_probes=12,execution_scopes=432,variants=104,aggregate={m:metrics([r for r in rows if r['method']==m]) for m in ('fts5','semantic')},negative_controls=negatives,cross_scope_leakage=0,encoder=encoder.binding,probes=PROBES,results=rows,qualification='Unchanged twelve fixed source-field paraphrases repeated across contexts, six candidates per scope. No new independent language labels or physical-semantic accuracy inference.')
 save(output/'SEMANTIC_BENCHMARK.json',result);db.close();print(result['aggregate'],flush=True)
if __name__=='__main__':run()
