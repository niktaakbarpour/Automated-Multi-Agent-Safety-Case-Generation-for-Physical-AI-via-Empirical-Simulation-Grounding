import json,sqlite3,xml.etree.ElementTree as ET,h5py,numpy as np
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
c=sqlite3.connect('file:/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite?mode=ro',uri=True);rows=[]
for execution,body in c.execute('select execution,body from rag_execution_env order by execution'):
 b=json.loads(body);meta=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(execution,)).fetchone()[0];directory=Path(meta).parent
 xml=ET.parse(b['xml_path']).getroot();named={kind:[v.get('name') for v in xml.iter(kind) if v.get('name')] for kind in ('body','geom','site')};mapping=json.load(open(b['mapping_path']));mapping=mapping.get('mapping',mapping);scene=directory/'semantic_initial_conditions.json';s=json.load(scene.open());phases=s.get('phases',{'legacy':s});bindings=[];checks=[];natives=mapping['body_names']
 with h5py.File(directory/'trajectory.h5') as f:
  stages={}
  for k in f['frames']:
   stage=str(f['frames'][k].attrs.get('stage',''));stages.setdefault(stage,k)
  for phase,data in phases.items():
   objects=data.get('object_initial_poses',data.get('objects',{}));fixtures=data.get('fixture_initial_poses',data.get('fixtures',{}))
   for name,info in (objects|fixtures).items():
    root=info.get('root_body');resolved=root in natives and root in named['body'];bindings.append(dict(phase=phase,logical=name,root_body=root,exact_root_verified=resolved,category='fixture' if name in fixtures else 'object'))
    if resolved and phase in stages and info.get('initial_position_world_m') is not None:
     frame=stages[phase];val=f['frames/'+frame+'/simulator/body_xpos/value'][natives.index(root)];err=float(np.max(np.abs(val-np.asarray(info['initial_position_world_m']))));checks.append(dict(phase=phase,frame=int(frame),logical=name,position_error=err))
  first=next(iter(f['frames']));sim=f['frames/'+first+'/simulator'];raw=f['frames/'+first+'/raw_observation'];raw_shapes={k:str(v['value'].shape) for k,v in raw.items() if 'value' in v and any(t in k for t in ('pos','quat'))}
 rows.append(dict(execution_id=execution,task_id=b['task_id'],variant_id=b['variant_id'],xml_path=b['xml_path'],xml_sha256=sha(b['xml_path']),mapping_path=b['mapping_path'],mapping_sha256=sha(b['mapping_path']),semantic_path=str(scene),semantic_sha256=sha(scene),coordinate_declarations={p:v.get('coordinate_system') for p,v in phases.items()},exact_main_table={k:'main_table' in names for k,names in named.items()},logical_bindings=bindings,phase_position_checks=checks,raw_shapes=raw_shapes,main_table_status='unresolved_no_explicit_alias_to_body_or_geom',frame_alignment='Only identical phase-labelled snapshot comparisons; endpoint state and caches remain distinct.'))
print('spatial',len(rows),'checks',sum(len(r['phase_position_checks']) for r in rows),flush=True)
p=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/SPATIAL_AUDIT.json')
with p.open('x') as f:json.dump(rows,f,sort_keys=True)
