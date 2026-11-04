"""Fixed prospective channel paraphrases; numerical validation is separate."""
from dataclasses import replace
import json,statistics,collections
from .channels import WORK,CHANNELS,ChannelStore,contract
from .retrieve import retrieve,ChannelQuery
from .validate import save
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder
# Frozen before evaluation. No tuning based on outcomes.
PROBES={
 'raw.robot0_gripper_qpos':('finger opening position readings','gripper joint configuration values'),
 'raw.robot0_gripper_qvel':('finger motion speed readings','gripper joint velocity samples'),
 'raw.robot0_joint_pos':('robot arm joint angle readings','arm joint configuration values'),
 'raw.robot0_joint_vel':('robot arm joint speed readings','arm joint velocity samples'),
 'raw.simulator_actuator_force':('motor actuator force readings','simulator actuator effort array'),
 'simulator.ncon':('number of saved contact entries','simulator contact count'),
}
def run():
 db=ChannelStore(WORK/'expanded.sqlite');encoder=Encoder();results=[];negatives=0
 executions=db.db.execute('select execution,task_id,variant_id from rag_execution_env order by execution').fetchall()
 for i,(e,t,v) in enumerate(executions):
  q=ChannelQuery(e,task_id=t,variant_id=v)
  for channel,texts in PROBES.items():
   for text in texts:
    for method in ('fts5','semantic'):
     r=retrieve(db,replace(q,text=text)) if method=='fts5' else retrieve(db,q,encoder=encoder,semantic_text=text)
     assert all(x['record']['execution_id']==e and x['record']['task_id']==t and x['record']['variant_id']==v for x in r['results'])
     ids=[x['record']['channel_id'] for x in r['results']];rank=ids.index(channel)+1 if channel in ids else None
     results.append(dict(execution=e,task=t,variant=v,channel=channel,text=text,method=method,precision_at_1=float(rank==1),recall_at_20=float(rank is not None),MRR=1/rank if rank else 0.))
  for bad,status in ((replace(q,execution_id='missing:'+e),'unknown_execution'),(replace(q,task_id='wrong'),'invalid_query_scope'),(replace(q,variant_id='wrong'),'invalid_query_scope'),(replace(q,object_id='wrong-object'),'no_matching_channel_record'),(replace(q,coordinate_frame='world'),'unsupported_coordinate_frame'),(replace(q,origin='derived'),'unsupported_origin')):
   r=retrieve(db,bad,encoder=encoder,semantic_text='robot position');assert r['status']==status and not r['results'];negatives+=1
  if i%50==0:print('Channel semantic scopes',i,flush=True)
 for e,status in db.db.execute("select execution,status from rag_scope_status where status in ('excluded_reserved','excluded_preflight')"):
  r=retrieve(db,ChannelQuery(e),encoder=encoder,semantic_text='robot position');assert r['status']==status and not r['results'];negatives+=1
 def metrics(rows):return dict(instances=len(rows),**{k:statistics.mean(r[k] for r in rows) for k in ('precision_at_1','recall_at_20','MRR')})
 report=dict(passed=True,unique_probes=len({t for ts in PROBES.values() for t in ts}),execution_scopes=len(executions),candidate_channels=6,aggregate={m:metrics([r for r in results if r['method']==m]) for m in ('fts5','semantic')},per_channel={c:{m:metrics([r for r in results if r['method']==m and r['channel']==c]) for m in ('fts5','semantic')} for c in CHANNELS},negative_controls=negatives,cross_scope_leakage=0,encoder=encoder.binding,probes=PROBES,qualification='Twelve fixed paraphrases repeated across 432 execution contexts. Six candidates per scope. No independent natural language dataset; no numeric or physical accuracy inference.',results=results)
 save('CHANNEL_SEMANTIC_EVALUATION.json',report);db.close();print(report['aggregate'],flush=True)
if __name__=='__main__':run()
