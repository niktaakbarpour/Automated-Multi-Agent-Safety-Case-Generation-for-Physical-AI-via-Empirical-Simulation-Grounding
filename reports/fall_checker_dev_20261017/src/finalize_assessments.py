"""Reassess saved development extracts only; no new original-recording access."""
import json,gzip,sys
from pathlib import Path
import numpy as np
from checker import load_config,analyze
from native_geometry_v2 import NativeGeometryIndex
from run_development import observations,allowed_run
root=Path(sys.argv[1]);out=root/'outputs';c=load_config(root/'config.json');split=json.loads((root/'proposed_split.json').read_text());idx=NativeGeometryIndex.load(root/'corrected_native_geometry_v2.json')
inv={r['run_id']:{e['name']:e for e in r['entities']} for r in json.loads((root/'corrected_entity_inventory_v2.json').read_text())['records']}
old=json.loads((out/'summary.json').read_text());history=root/'development_history';history.mkdir(exist_ok=True)
import time
tag=str(time.time_ns());(history/(tag+'_summary.json')).write_text(json.dumps(old,indent=2));(history/(tag+'_sensitivity.json')).write_bytes((out/'sensitivity.json').read_bytes())
final=[];sensitivity=[]
for d in old['development']:
 run=d['run_id'];allowed_run(run,split);ep=d['episode'];prefix=f'episode_{ep:03d}'
 with gzip.open(out/(prefix+'_observations.json.gz'),'rt') as f:samples=json.load(f)

 with gzip.open(out/(prefix+'_geometry_contacts.json.gz'),'rt') as f:bundles=json.load(f)
 for pc in [dict(name='base')]+c['sensitivity_profiles']:
  cfg=dict(c,**{k:v for k,v in pc.items() if k!='name'});ss={name:[] for name in c['objects']};byframe={b['frame']:b for b in bundles}
  for i in range(d['frames']):
   if i not in byframe:
    for name in c['objects']:ss[name].append(dict(frame=i,valid=False,error='missing geometry/contact bundle'))
    continue
   b=byframe[i];gp=np.array(b['geom_xpos']);gr=np.array(b['geom_xmat']);ref={k:v for k,v in b.items() if k not in ['geom_xpos','geom_xmat','contacts','identity_guard']}
   for name in c['objects']:ss[name].append(dict(ref,**observations(idx,inv[run][name],gp,gr,b['contacts'],cfg)))
  assessed={name:analyze(ss[name],cfg) for name in c['objects']}
  sensitivity.append({'run_id':run,'profile':pc['name'],'objects':assessed})
  if pc['name']=='base':
   d['objects']=assessed;final.append(d);(out/(prefix+'.json')).write_text(json.dumps(d,indent=2))
   with gzip.open(out/(prefix+'_observations.json.gz'),'wt') as f:json.dump(ss,f)
 print('REASSESSED',ep,flush=True)
(out/'summary.json').write_text(json.dumps(dict(old,development=final),indent=2));(out/'sensitivity.json').write_text(json.dumps(sensitivity,indent=2))
