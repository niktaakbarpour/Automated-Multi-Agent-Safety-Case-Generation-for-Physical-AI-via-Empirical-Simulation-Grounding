"""Source-grounded references, independent of the target planner and bundle output."""
import json,sqlite3,hashlib,collections
from pathlib import Path
import numpy as np,h5py,xml.etree.ElementTree as ET
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *

def order(k):return hashlib.sha256((SEED+k).encode()).hexdigest()
def scopes(counts,exclude):
 c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);groups=collections.defaultdict(list)
 for e,s,b in c.execute('select execution,suite,body from rag_execution_env order by execution'):
  if e in exclude:continue
  h=json.loads(c.execute('select body from h_execution where execution=?',(e,)).fetchone()[0]);groups[s].append(dict(execution_id=e,binding=json.loads(b),source_path=h['source_path'],source_sha256=h['source_sha256'],frames=len(h['temporal_rows']),suite=s))
 rows=[];variants=set()
 for s,n in counts.items():
  xs=sorted(groups[s],key=lambda x:(x['frames'],order(x['execution_id'])))
  for j in range(n):
   segment=xs[len(xs)*j//n:len(xs)*(j+1)//n];segment=sorted(segment,key=lambda x:order(x['execution_id']));fresh=[x for x in segment if x['binding']['variant_id'] not in variants];x=(fresh or segment)[0];variants.add(x['binding']['variant_id']);rows.append(x)
 return rows

def make(scope,category,template,families,kind='supported',index=0,variant=None):
 b=scope['binding'];ex=scope['execution_id'];mid=scope['frames']//2;action=mid-11;directory=Path(b['xml_path']).parent;scene_path=directory/'semantic_initial_conditions.json';scene=json.loads(scene_path.read_text());ph=next(iter(scene.get('phases',{'legacy':scene}).values()));objects=ph.get('object_initial_poses',ph.get('objects',{}));name=sorted(set(objects)&set(b['objects']))[index%len(b['objects'])];root=objects[name]['root_body'];mapping=json.loads(Path(b['mapping_path']).read_text());mapping=mapping.get('mapping',mapping);assert any(x.get('name')==root for x in ET.parse(b['xml_path']).getroot().iter('body'))
 q=dict(execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],verification_mode='verified_session');frames=[mid];facts={};metadata={};source=scope['source_path'];h=scope['source_sha256'];alias=ph['parsed_bddl_problem']['problem_name']=='libero_tabletop_manipulation';fault=None
 with h5py.File(source,'r') as f:
  assert f.attrs['global_episode_id']==ex;assert len(f['frames'])==scope['frames'];time=float(f[f'frames/{mid:06d}/simulator/time/value'][()]);value=0.
  if kind=='range':frames=[mid-1,mid]
  if kind=='action':frames=[action+10,action+11]
  if kind=='seconds':q['seconds_interval']=[round(time,9)]*2
  if kind=='begin':frames=[0]
  if kind=='end':frames=[scope['frames']-1]
  if kind=='wrong_variant':q['variant_id']=variant
  if kind=='wrong_task':q['task_id']='not_this_task'
  if kind=='unknown_execution':q['execution_id']='phase5k_unknown_execution'
  if kind=='unknown_object':q['object_id']='ambiguous_object'
  if kind=='impossible_time':q['seconds_interval']=[1e9,1e9]
  if kind in ('missing_source','corrupt_source','symlink_source','replace_source','instruction_source'):fault=kind
  if kind=='historical':q['assurance']='historical_producer_attestation'
  if kind=='conditional':q['allow_conditional']=True
  for family in families:
   if family in CHANNELS:
    k=CHANNELS.index(family);rows=[]
    for frame in frames:
     selector=f'/frames/{frame:06d}/'+FIELDS[k];d=f[selector];a=np.asarray(d[()]);rows.append(dict(frame=frame,selector=selector,value=a.tolist(),dtype=str(d.dtype),shape=list(d.shape),units=UNITS[k]));value=float(a.reshape(-1)[0])
    facts[family]=rows
  if 'action_metadata' in families:
   key=f'{action:06d}';metadata['action_metadata']=dict(selector='/policy_steps/'+key,attributes={k:(v.item() if hasattr(v,'item') else v) for k,v in f['policy_steps'][key].attrs.items()})
  if 'inference_metadata' in families:
   key=f'{action:06d}';chunk=int(f['policy_steps'][key].attrs['chunk_id']);metadata['inference_metadata']=dict(selector='/inference_calls/'+f'{chunk:06d}',chunk_id=chunk,step=int(f['inference_calls'][f'{chunk:06d}'].attrs['step']))
  if 'recorded_time' in families:metadata['recorded_time']=dict(simulator_endpoint_seconds=time,wall_ns=int(f[f'frames/{mid:06d}'].attrs['wall_time_ns']),sensor_clock=False)
  if 'geometry_identity' in families:metadata['geometry_identity']=dict(object_id=name,root_body=root,body_id=mapping['body_names'].index(root),collision_geom_ids=[g['native_geom_id'] for g in mapping['geometries'] if g['collision_capable'] and root in g['body_ancestry']])
  if 'main_table_identity' in families:metadata['main_table_identity']=dict(supported=alias,body='table' if alias else None,geom='table_collision' if alias else None)
  text=template.format(frame=frames[0] if len(frames)==1 else mid,start=mid-1,end=mid,action=action,time=round(time,9),object=name,value=repr(value+(1. if index%2 else 0.)))
 refs=[dict(path=source,sha256=h),dict(path=b['xml_path'],sha256=b['xml_sha256']),dict(path=b['mapping_path'],sha256=b['mapping_sha256']),dict(path=str(scene_path),sha256=sha(scene_path))]
 negative=kind in ('unsupported','historical','wrong_variant','wrong_task','unknown_execution','unknown_object','impossible_time','ambiguous','missing_source','corrupt_source','symlink_source','replace_source','instruction_source') or 'main_table_identity' in families and not alias
 return dict(category=category,query=text,request=q,expected_families=families,reference_samples=facts,reference_metadata=metadata,source_artifacts=refs,execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],suite=scope['suite'],frames=scope['frames'],source_path=source,source_sha256=h,reference_frame_indices=frames,action_index=action,kind=kind,critical_abstention=negative,fault=fault,ranking_eligible=bool(families) and not negative,multisource_eligible=category=='C4' and not negative,reference_construction='Independent original HDF5/JSON/XML; no planner/retriever output used',human_reference=False)
