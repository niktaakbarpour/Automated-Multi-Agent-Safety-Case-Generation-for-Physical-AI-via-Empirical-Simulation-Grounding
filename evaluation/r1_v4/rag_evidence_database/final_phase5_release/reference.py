"""Original-source reference construction. No production API/parser imports."""
import json,copy,sqlite3,hashlib
from pathlib import Path
import numpy as np,h5py
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.reference import scopes
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.references import excluded_scopes
from .config import *

def selection():
 excluded=excluded_scopes();old=Path('/disk/1/data/niktakbr/trustworthy-phase5k1-working')
 for name in ('DEVELOPMENT_SELECTION.json','FINAL_SELECTION.json','FINAL_SELECTION_V2.json'):
  excluded|={r['execution_id'] for r in json.loads((old/name).read_text())}
 return scopes(dict(goal=4,long=4,object=4,spatial=4),excluded)
def base(scope):
 b=scope['binding'];return dict(schema_version=VERSION,execution_id=scope['execution_id'],task_id=b['task_id'],variant_id=b['variant_id'],assurance='verified_source_values',provenance=dict(level='source_identity'),obligations=[])
def obligation(q,oid,family,frame=None,mandatory=True,**kw):
 o=dict(id=oid,execution_id=q['execution_id'],family=family,field=REGISTRY[family],mandatory=mandatory)
 if frame is not None:o['selector']=dict(kind='frames',start=frame[0],end=frame[1])
 o.update(kw);q['obligations'].append(o);return o

def build(scope,index):
 q0=base(scope);b=scope['binding'];mid=scope['frames']//2;last=scope['frames']-1;ex=scope['execution_id'];db=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);h=json.loads(db.execute('select body from h_execution where execution=?',(ex,)).fetchone()[0]);model=json.loads(Path(h['model_map_path']).read_text());joint=model['joints'][0]['name'];obj=sorted(b['objects'])[0];alias=json.loads(Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/MAIN_TABLE_AUDIT.json').read_text());alias=next(r for r in alias['rows'] if r['execution_id']==ex);rows=[]
 def emit(kind,q,status,fault=None):rows.append(dict(id=f'FINAL-{index:02d}-{kind}',kind=kind,request=q,expected_status=status,fault=fault,execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],source_path=scope['source_path'],source_sha256=scope['source_sha256'],suite=scope['suite']))
 q=copy.deepcopy(q0)
 for j,family in enumerate(CHANNELS):obligation(q,'initial-'+str(j),family,(0,0))
 emit('initial_six',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0)
 for j,family in enumerate((CHANNELS[0],CHANNELS[2],CHANNELS[3])):obligation(q,'middle-'+str(j),family,(mid,mid))
 emit('middle_multi',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0);obligation(q,'terminal',CHANNELS[5],(last-1,last));emit('terminal_window',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0);obligation(q,'component',CHANNELS[2],(mid,mid),component=joint,interpretation='verified_physical');emit('verified_component',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0);obligation(q,'geometry','geometry_identity',object_id=obj);obligation(q,'source','source_provenance');obligation(q,'declarations','execution_metadata');emit('geometry_and_provenance',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0);obligation(q,'alias','main_table_identity',object_id='main_table');emit('symbolic_table',q,'COMPLETE WITHIN VERIFIED CONTRACT' if alias['status']=='verified_symbolic_alias' else 'UNSUPPORTED')
 q=copy.deepcopy(q0);obligation(q,'observed',CHANNELS[0],(mid,mid));obligation(q,'not_recorded','action_metadata',(0,0));emit('partial_missing_action',q,'PARTIAL')
 q=copy.deepcopy(q0);obligation(q,'wrong',CHANNELS[0],(mid,mid));q['execution_id']='not-an-indexed-execution';q['obligations'][0]['execution_id']=q['execution_id'];emit('wrong_execution',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'wrong',CHANNELS[0],(mid,mid));q['task_id']='wrong-task';emit('wrong_task',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'wrong',CHANNELS[0],(mid,mid));q['variant_id']='xmlenv:'+'0'*64;emit('wrong_variant',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'wrong',CHANNELS[2],(mid,mid),component='robot0_joint999');emit('wrong_component',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);o=obligation(q,'wrong',CHANNELS[0],(mid,mid));o['field']='raw_observation/wrist_force/value';emit('missing_field_contract',q,'UNSUPPORTED')
 q=copy.deepcopy(q0);obligation(q,'world',CHANNELS[0],(mid,mid),coordinate_frame='world');emit('unsupported_world',q,'UNSUPPORTED')
 q=copy.deepcopy(q0);obligation(q,'historical',CHANNELS[0],(mid,mid));q['assurance']='historical_producer_attestation';emit('historical_attestation',q,'UNSUPPORTED')
 for fault in ('missing','modified'):
  q=copy.deepcopy(q0);obligation(q,'source_check',CHANNELS[2],(mid,mid));emit(fault+'_source',q,'UNAVAILABLE',fault)
 q=copy.deepcopy(q0);obligation(q,'conditional',CHANNELS[2],(mid,mid),interpretation='conditional',allow_conditional=True,required_properties=['cache_offset_seconds']);emit('conditional_cache',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 with h5py.File(scope['source_path'],'r') as f:
  time=float(f[f'frames/{mid:06d}/simulator/time/value'][()]);assert time==db.execute('select sim_time from i_clock_labels where execution=? and frame=?',(ex,mid)).fetchone()[0]
 q=copy.deepcopy(q0);o=obligation(q,'label',CHANNELS[2]);o['selector']=dict(kind='simulator_labels',start=time,end=time);emit('recorded_time_label',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0);obligation(q,'graph',CHANNELS[2],(mid,mid));q.update(assurance='provenance_complete',provenance=dict(level='release_graph',scope=PROVENANCE_SCOPE));emit('bounded_provenance',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 emit('empty_obligations',copy.deepcopy(q0),'INVALID SCOPE')
 q=copy.deepcopy(q0);o=obligation(q,'scope',CHANNELS[2],(mid,mid));o['execution_id']='another-execution';emit('cross_obligation_scope',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'required',CHANNELS[2],(mid,mid));obligation(q,'optional','action_metadata',(0,0),mandatory=False);emit('optional_absence',q,'COMPLETE WITHIN VERIFIED CONTRACT')
 q=copy.deepcopy(q0)
 for family in ('recorded_time','action_metadata','inference_metadata','camera_references','contact_references'):obligation(q,family,family,(mid,mid))
 indexed=True
 for typ in ('contact','camera_reference'):
  bodies=[json.loads(r[0]) for r in db.execute("select body from evidence where execution_id=? and json_extract(body,'$.measurement_type')=?",(ex,typ))]
  indexed=indexed and any(r['interval'][0]<=mid<=r['interval'][1] for r in bodies)
 emit('timed_metadata_set',q,'COMPLETE WITHIN VERIFIED CONTRACT' if indexed else 'PARTIAL')
 q=copy.deepcopy(q0);obligation(q,'object','geometry_identity',object_id='nonexistent-object');emit('wrong_object',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'assurance',CHANNELS[2],(mid,mid));q['assurance']='safety_guaranteed';emit('invalid_assurance',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'source',CHANNELS[2],(mid,mid),source_sha256='0'*64);emit('wrong_source_identity',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'time',CHANNELS[2]);emit('missing_selector',q,'INVALID SCOPE')
 q=copy.deepcopy(q0);obligation(q,'missing_frame',CHANNELS[2],(scope['frames'],scope['frames']));emit('unavailable_frame',q,'UNAVAILABLE')
 for row in rows:row['source_references']=references(row,scope,db)
 db.close();return rows

def references(case,scope,db):
 refs={};b=scope['binding'];ex=scope['execution_id'];m=json.loads(Path(b['mapping_path']).read_text());m=m.get('mapping',m)
 with h5py.File(scope['source_path'],'r') as f:
  assert f.attrs['global_episode_id']==ex
  def attrs(g):return {k:(v.item() if hasattr(v,'item') else v.decode() if isinstance(v,bytes) else v) for k,v in g.attrs.items() if isinstance(v,(str,bytes,int,float,bool,np.integer,np.floating,np.bool_))}
  for o in case['request']['obligations']:
   family=o['family'];s=o.get('selector');frames=[]
   if s:
    frames=list(range(s['start'],s['end']+1)) if s['kind']=='frames' else [i for i,t in enumerate(scope['_times']) if s['start']<=t<=s['end']]
    frames=[i for i in frames if 0<=i<scope['frames']]
   r=dict(family=family,frames=frames,samples=[],metadata=[],source_sha256=scope['source_sha256'])
   if family in CHANNELS:
    row=db.execute('select id from rag_channel_records where execution=? and channel=?',(ex,family)).fetchone();r['original_id']=row[0]
    for i in frames:
     selector=f'/frames/{i:06d}/'+FIELDS[CHANNELS.index(family)];d=f[selector];r['samples'].append(dict(frame=i,selector=selector,value=np.asarray(d[()]).tolist(),dtype=str(d.dtype),shape=list(d.shape),units=UNITS[CHANNELS.index(family)]))
    if o.get('component') and case['kind']!='wrong_component':
     native=json.loads(Path(json.loads(db.execute('select body from h_execution where execution=?',(ex,)).fetchone()[0])['model_map_path']).read_text());assert native['joints'][0]['name']==o['component'];r['component_index']=0;r['component_name']=o['component']
   elif family=='geometry_identity' and o.get('object_id') in b['objects']:
    obj=o['object_id'];r['geometry']=dict(object_id=obj,root_body=m['body_names'][b['objects'][obj]['body_id']],body_id=b['objects'][obj]['body_id'],collision_geom_ids=b['objects'][obj]['collision_geom_ids'])
   elif family=='recorded_time':
    for i in frames:
     g=f['frames'][f'{i:06d}'];r['metadata'].append(dict(saved_frame_index=i,simulator_endpoint_seconds=float(g['simulator/time/value'][()]),recorder_host_wall_ns=int(g.attrs['wall_time_ns']),recorder_host_monotonic_ns=int(g.attrs['monotonic_ns']),recorder_utc=g.attrs['utc']))
   elif family in ('action_metadata','inference_metadata'):
    actions=[i-11 for i in frames if i>=11];seen=set()
    for action in actions:
     key=f'{action:06d}'
     if key not in f['policy_steps']:continue
     p=f['policy_steps'][key]
     if family=='action_metadata':r['metadata'].append(dict(policy_step=action,policy_attributes=attrs(p)))
     else:
      chunk=int(p.attrs['chunk_id']);ck=f'{chunk:06d}'
      if chunk in seen or ck not in f['inference_calls']:continue
      seen.add(chunk);call=f['inference_calls'][ck];r['metadata'].append(dict(chunk_id=chunk,recorded_attributes=attrs(call),policy_input_saved_frame=10+int(call.attrs['step'])))
   elif family in ('camera_references','contact_references'):
    for i in frames:
     selectors=[f'/frames/{i:06d}/simulator/contacts'] if family=='contact_references' else [f'/frames/{i:06d}/raw_observation/'+name+'/value' for name in ('agentview_image','robot0_eye_in_hand_image')]
     for selector in selectors:
      assert selector in f;r['metadata'].append(dict(saved_frame_index=i,selector=selector,reference_only=True))
   elif family=='execution_metadata':
    original=json.loads(Path(json.loads(db.execute('select body from h_execution where execution=?',(ex,)).fetchone()[0])['metadata_path']).read_text());r['execution_metadata']={k:original.get(k) for k in ('source_commit','versions','python','platform','checkpoint_revision','checkpoint_weight_sha256','control_frequency_hz','settling_steps')}
   if family=='geometry_identity':r['artifact_sha256']=b['mapping_sha256']
   elif family=='main_table_identity':
    audit_path=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/MAIN_TABLE_AUDIT.json');r['artifact_sha256']=sha(audit_path);audit=json.loads(audit_path.read_text());row=next(x for x in audit['rows'] if x['execution_id']==ex);r['alias_mapping']=row.get('exact_mapping')
   elif family=='execution_metadata':r['artifact_sha256']=json.loads(db.execute('select body from h_execution where execution=?',(ex,)).fetchone()[0])['metadata_sha256']
   else:r['artifact_sha256']=scope['source_sha256']
   refs[o['id']]=r
 return refs

def run():
 selected=selection();rows=[]
 for i,s in enumerate(selected):
  with h5py.File(s['source_path'],'r') as f:s['_times']=[float(f['frames'][f'{j:06d}']['simulator/time/value'][()]) for j in range(s['frames'])]
  assert sha(Path(s['source_path']))==s['source_sha256'];rows+=build(s,i)
  print('Reference execution',i+1,'/',len(selected),flush=True)
 assert len(rows)==448
 (HERE/'FINAL_EVALUATION_DATASET.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,allow_nan=False)+'\n' for r in rows));(WORK/'FINAL_SELECTION.json').write_text(json.dumps([{k:v for k,v in s.items() if k!='_times'} for s in selected],sort_keys=True,indent=2));print('FROZEN REFERENCES',len(rows),'cases',flush=True)
if __name__=='__main__':run()
