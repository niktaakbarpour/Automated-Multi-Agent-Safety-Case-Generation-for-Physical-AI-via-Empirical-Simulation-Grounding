"""Mutation/metamorphic audit uses original questions, never retrieved answers."""
import json,copy
from dataclasses import asdict
from .config import *
from .retrieve import Retriever,BundleRequest
from .intent import derive
from .validator import validate

def run():
 r=Retriever();ex=r.catalogue.execute('select execution from catalogue order by execution limit 1').fetchone()[0];c=json.loads(r.catalogue.execute('select body from catalogue where execution=?',(ex,)).fetchone()[0]);records=[]
 texts=['Arm and gripper configurations at frame 20.','Gripper state and actuator output at frame 20.','Joint positions and velocities at simulator time 2.5.','Joint configurations before action 4.','All six measurement channels at frame 20.','Give the source hash and execution metadata.']
 for text in texts:
  q=BundleRequest(text,ex);m=derive(text,asdict(q),c)
  for family in m['families']:
   altered=copy.deepcopy(m);altered['obligations']=[o for o in altered['obligations'] if family not in o['required_families']];plan=[f for f in m['families'] if f!=family];check=validate(text,asdict(q),altered,plan,c);records.append(dict(question=text,mutation='remove model obligation AND plan family',removed=family,detected=not check['passed']))
  for mode in ('scope','temporal'):
   altered=copy.deepcopy(m)
   for o in altered['obligations']:
    if mode=='scope':o['scope']['execution_id']='wrong'
    if mode=='temporal' and o['type']=='measurement':o['required_temporal_scope']=[]
   applicable=mode=='scope' or any(o['type']=='measurement' and o['required_temporal_scope'] for o in m['obligations'])
   if applicable:records.append(dict(question=text,mutation=mode,detected=not validate(text,asdict(q),altered,m['families'],c)['passed']))
 forms=['At frame 20, joint positions and velocities.','Joint positions and velocities at frame 20.','At frame 20, velocities and positions of the arm.'];sets=[]
 for text in forms:
  q=BundleRequest(text,ex);m=derive(text,asdict(q),c);sets.append(sorted(o['target'] for o in m['obligations'] if o['type']=='measurement'))
 assert all(x==sets[0] for x in sets);assert all(x['detected'] for x in records);r.close();result=dict(passed=True,mutation_trials=len(records),detected=sum(x['detected'] for x in records),records=records,metamorphic_forms=forms,measurement_sets=sets);(WORK/'MUTATION_METAMORPHIC_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('Mutations',len(records),'all detected',flush=True)
if __name__=='__main__':run()
