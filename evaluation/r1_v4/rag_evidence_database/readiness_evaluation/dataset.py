"""Independent HDF5/XML references; never calls a target retrieval function."""
import json,sqlite3,hashlib,collections,xml.etree.ElementTree as ET
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
from .config import *
from .questions import CATALOG
CH=['raw.robot0_gripper_qpos','raw.robot0_gripper_qvel','raw.robot0_joint_pos','raw.robot0_joint_vel','raw.simulator_actuator_force','simulator.ncon']
FIELD=['raw_observation/robot0_gripper_qpos/value','raw_observation/robot0_gripper_qvel/value','raw_observation/robot0_joint_pos/value','raw_observation/robot0_joint_vel/value','simulator/actuator_force/value','simulator/ncon/value']
UNITS=['m','m/s','rad','rad/s','native_actuator_force','count']
def key(s):return hashlib.sha256((SEED+':'+s).encode()).hexdigest()
def write_json(n,d):
 with (HERE/n).open('x') as f:json.dump(d,f,sort_keys=True,indent=2)
def select(c):
 groups=collections.defaultdict(list)
 for e,s,b in c.execute('select execution,suite,body from rag_execution_env order by execution'):
  x=json.loads(b);h=json.loads(c.execute('select body from h_execution where execution=?',(e,)).fetchone()[0]);groups[s].append(dict(execution=e,suite=s,binding=x,frames=len(h['temporal_rows']),source_path=h['source_path'],source_sha256=h['source_sha256']))
 rows=[];variants=set()
 for suite,n in [('goal',6),('long',5),('object',6),('spatial',5)]:
  g=sorted(groups[suite],key=lambda x:(x['frames'],key(x['execution'])))
  for i in range(n):
   candidates=g[len(g)*i//n:len(g)*(i+1)//n];ordered=sorted(candidates,key=lambda x:key(x['execution']));fresh=[x for x in ordered if x['binding']['variant_id'] not in variants];x=dict((fresh or ordered)[0]);variants.add(x['binding']['variant_id']);x['split']='development' if i==0 else 'final';x['length_stratum']=i;rows.append(x)
 return rows

def source_ref(path,selector,expected=None):return dict(path=str(path),sha256=expected or sha(path),selector=selector)
def build():
 assert (HERE/'FROZEN_EVALUATION_CONFIGURATION.json').exists();c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);selected=select(c);verifier=SourceVerifier();cases=[]
 for j,e in enumerate(selected):
  ex=e['execution'];b=e['binding'];directory=Path(b['xml_path']).parent;scene_path=directory/'semantic_initial_conditions.json';scene=json.loads(scene_path.read_text());ph=next(iter(scene.get('phases',{'legacy':scene}).values()));objects=ph.get('object_initial_poses',ph.get('objects',{}));obj=sorted(set(objects)&set(b['objects']))[j%len(set(objects)&set(b['objects']))];root=objects[obj]['root_body'];mapping=json.loads(Path(b['mapping_path']).read_text());mapping=mapping.get('mapping',mapping);xml=ET.parse(b['xml_path']).getroot();assert any(x.get('name')==root for x in xml.iter('body'));bid=mapping['body_names'].index(root);geoms=[x['native_geom_id'] for x in mapping['geometries'] if x['collision_capable'] and root in x['body_ancestry']];problem=ph['parsed_bddl_problem']['problem_name'];alias=problem=='libero_tabletop_manipulation' and 'main_table' in ph['parsed_bddl_problem'].get('fixtures',{}).get('table',[])
  if alias:assert any(x.get('name')=='table' for x in xml.iter('body')) and any(x.get('name')=='table_collision' for x in xml.iter('geom'))
  rawrows={ch:(rid,json.loads(body)) for rid,ch,body in c.execute('select id,channel,body from rag_channel_records where execution=?',(ex,))};source=e['source_path'];expected=e['source_sha256'];mid=e['frames']//2;lo=mid-1;hi=mid;action=mid-11
  with verifier.access(source,expected,'strict') as (fd,att):
   with h5py.File(fd,'r') as f:
    assert f.attrs['global_episode_id']==ex;framekeys=sorted(f['frames']);assert len(framekeys)==e['frames'];tlo=float(f['frames'][framekeys[lo]]['simulator/time/value'][()]);thi=float(f['frames'][framekeys[hi]]['simulator/time/value'][()])
    for cat,formulations in CATALOG.items():
     case=dict(id=f'{cat}-{j:02d}',category=cat,split=e['split'],execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],suite=e['suite'],recording_frames=e['frames'],endpoint='physical',request=dict(execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],interval=[mid,mid],verification_mode='verified_session',limit=20),channels=[CH[j%6]],required_facets=[],expected_status='SUFFICIENT',abstention_required=False,ambiguity=None,difficulty='routine',fault=None,reference_method='Independent h5py source indexing and XML/native-map inspection; no retriever output',reference_artifacts=[source_ref(source,'/frames',expected)],expert_judgment=False,physical_safety_sufficiency='NOT_EVALUATED')
     q=case['request'];facets=[];extra=[];frames=[mid];claim=None;literal_missing=None
     if cat=='C1':
      if j in (8,13,16):frames=[0]
      if j in (9,11,14,15,17,18,19):frames=[e['frames']-1]
     elif cat=='C2':
      case['channels']=[CH[k] for k in [[2],[0],[3],[1],[4],[5],[2],[0],[3],[1],[4],[5],[2],[0],[3],[1],[4],[5],[2],[0],[3],[0]][j]]
      frames=[lo,hi]
      if j==8:frames=[0,1]
      if j in (9,11):frames=[e['frames']-2,e['frames']-1]
      if j==12:frames=[0]
      if j in (5,6,13,18):frames=[mid]
      if j==16:frames=[hi]
      if j==19:frames=[lo]
      if j in (4,5,6,12,13,14,15):
       times=[float(f['frames'][framekeys[k]]['simulator/time/value'][()]) for k in frames];q.pop('interval');q.update(clock_domain='simulator_endpoint_label',seconds_interval=[times[0],times[-1]])
       if j in (14,15):
        t=1e9 if j==15 else (tlo+thi)/2;q['seconds_interval']=[t,t];case.update(expected_status='UNAVAILABLE',abstention_required=True);frames=[]
      if j==20:q['alignment']='same_physical_instant';case.update(expected_status='INVALID',abstention_required=True)
      if j==21:q.update(required_properties=['cache_offset_seconds'],allow_conditional=True);case['expected_status']='CONDITIONALLY_SUFFICIENT';frames=[mid]
     elif cat=='C3':
      case.update(endpoint='legacy',channels=[]);q.clear();q.update(execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],object_id=obj,interval=[mid,mid],limit=20,evidence_types=['native_geometry','object_identity'])
      extra=['geometry_identity'];case['reference_artifacts']+=[source_ref(scene_path,'/phases/*/object_initial_poses/'+obj),source_ref(b['mapping_path'],'/geometries',b['mapping_sha256']),source_ref(b['xml_path'],'//body[@name="'+root+'"]',b['xml_sha256'])];case['geometry_reference']=dict(object_id=obj,root_body=root,body_id=bid,collision_geom_ids=geoms)
      if j in (0,3,6,9,18):
       q.update(object_id='main_table',evidence_types=['support_surface_identity','native_geometry']);extra=['main_table_alias'];case['geometry_reference'].update(alias_supported=alias,alias_identity=dict(body='table',geom='table_collision') if alias else None);case['expected_status']='INSUFFICIENT' if alias else 'UNAVAILABLE'
       if not alias:case['abstention_required']=True
      if j==12:q['field_name']='logical_main_table_pose';case.update(expected_status='INVALID',abstention_required=True)
      if j in (15,20):q['field_name']='physical_support_event';case.update(expected_status='INVALID',abstention_required=True)
      if j==16:q['interval']=[e['frames']-1,e['frames']-1]
      if j==17:q['interval']=[0,0]
      if j==19:q['evidence_types']=['object_identity','native_geometry'];extra=['geometry_identity','identity_document']
     elif cat=='C4':
      combos=[[0,2],[2,3],[0,1],[4,5],[0,3,4],[0,1,2,3,4,5],[2],[0],[3],[0],[2,3,4],[0,1,5],[2,4],[5],[0],[3],[0,1,2,3],[4,3,5],[0],[2],[0,1,2,3,4,5],[2]]
      case['channels']=[CH[k] for k in combos[j]]
      extras={6:['action_metadata'],7:['action_metadata'],8:['camera_exposure_timestamp'],9:['historical_binary'],13:['contact_pairs_and_force'],14:['recorder_host_timestamp'],15:['inference_metadata'],18:['geometry_identity'],19:['simulator_time_label'],21:['action_metadata','sensor_clock_calibration']};extra=extras.get(j,[])
      if extra:case['expected_status']='INSUFFICIENT'
      if j in (1,2,3,6,7,12,20,21):frames=[lo,hi]
     elif cat=='C5':
      case.update(expected_status='UNAVAILABLE',abstention_required=True,channels=[]);literal_missing=['tactile_pressure','wrist_force_torque','camera_exposure_time','sensor_clock_sync','actuator_temperature','hardware_accelerometer','camera_calibration_certificate','microphone_audio','external_load_cell','finger_taxels','contact_force_world','sensor_timestamp_uncertainty','physical_metrology_certificate','support_sensor','collision_impulse','calibrated_depth','encoder_calibration','packet_capture_times','applied_control_series','action_chunk_metadata','measured_friction','physical_support_event'][j];q['channel_id']='unindexed.'+literal_missing;extra=[literal_missing]
      if j in (18,19):case['source_available_but_endpoint_unsupported']=True;case['reference_artifacts'].append(source_ref(source,'/transitions' if j==18 else '/policy_steps',expected))
      elif j not in (6,12,16,20,21):
       assert literal_missing not in f['frames'][framekeys[mid]]['raw_observation'] and literal_missing not in f['frames'][framekeys[mid]]['simulator']
       case['absence_scope']='Explicit named raw/simulator fields at the selected saved snapshot; no hidden physical meaning inferred from generic arrays'
     elif cat=='C6':
      case['channels']=[CH[[0,3,0,2,0,4,4,2,2,0,5,0,0,3,4,2,2,0,0,2,4,1][j]]]
      if j in (0,1):q['coordinate_frame']='world';case.update(expected_status='INVALID',abstention_required=True)
      elif j in (2,19):q['alignment']='same_physical_instant';case.update(expected_status='INVALID',abstention_required=True)
      elif j in (3,8,17):q.update(required_properties=['cache_offset_seconds'],allow_conditional=True);case['expected_status']='CONDITIONALLY_SUFFICIENT'
      elif j==4:q['required_properties']=['cache_offset_seconds'];case.update(expected_status='INVALID',abstention_required=True)
      elif j in (5,14):q['transformation']='contact_force' if j==5 else 'generalized_joint_force';case.update(expected_status='INVALID',abstention_required=True)
      elif j==6:q['required_properties']=['si_component_units'];case.update(expected_status='INVALID',abstention_required=True)
      elif j in (7,11):q['required_properties']=['physical_calibration'];case.update(expected_status='UNAVAILABLE',abstention_required=True)
      elif j in (10,16):extra=['physical_support' if j==10 else 'continuous_physical_coverage'];case['expected_status']='INSUFFICIENT'
      elif j==12:q['transformation']='endpoint_shift';case.update(expected_status='INVALID',abstention_required=True)
      elif j==13:q['coordinate_frame']='inspection_frame';case.update(expected_status='INVALID',abstention_required=True)
      elif j==18:q['channel_id']='logical_main_table_pose';case.update(expected_status='INVALID',abstention_required=True)
     elif cat=='C7':
      case['channels']=[CH[2 if j%2==0 else 0]]
      if j in (0,3,5,7,9,16,18):q['assurance']='historical_producer_attestation';case.update(expected_status='UNAVAILABLE',abstention_required=True)
      if j in (4,17):q.update(assurance='provenance_complete',provenance_scope='release-evidence-graph-v1');extra=['provenance_report']
      if j==8:q.update(assurance='provenance_complete',provenance_scope='complete_historical_environment');case.update(expected_status='INVALID',abstention_required=True)
      if j in (1,10):extra=['source_hash']
      if j==6:extra=['producer_version_declaration'];case['expected_status']='INSUFFICIENT'
      if j==20:extra=['checkpoint_declaration'];case['expected_status']='INSUFFICIENT'
      if j in (13,14,15):case['fault']=['missing','corrupt','symlink'][j-13];case.update(expected_status='UNAVAILABLE',abstention_required=True)
      if j in (2,11,12,19,21):q['assurance']='verified_source_values'
     elif cat=='C8':
      case['channels']=[CH[2 if j%2==0 else 0]];case.update(expected_status='INVALID',abstention_required=True,difficulty='adversarial')
      if j==0:q['execution_id']='phase5j_unknown_execution'
      elif j==1:q['task_id']='phase5j_incompatible_task'
      elif j==2:q['variant_id']=next(x['binding']['variant_id'] for x in selected if x['binding']['variant_id']!=b['variant_id'])
      elif j==3:q['object_id']='object';case['ambiguity']='Generic object name does not identify a body or robot'
      elif j==4:q['interval']=[e['frames']+5,e['frames']+5];case['expected_status']='UNAVAILABLE'
      elif j==5:q['interval']=[hi,lo]
      elif j==6:q['clock_domain']='joint_sensor_clock'
      elif j==7:q['transformation']='world_transform'
      elif j==8:q.pop('interval');extra=['exact_temporal_scope'];case.update(expected_status='AMBIGUOUS',abstention_required=False,ambiguity='Exact instant demanded but none supplied')
      elif j==9:q['object_id']='robot'
      elif j==10:q['source_sha256']='0'*64
      elif j==11:q.pop('interval');q.update(clock_domain='simulator_endpoint_label',seconds_interval=[(tlo+thi)/2]*2);case['expected_status']='UNAVAILABLE';frames=[]
      elif j==12:case['channels']=[CH[3]];q['units']='m/s'
      elif j==13:q['assurance']='historical_producer_attestation';case['expected_status']='UNAVAILABLE'
      elif j in (14,15,16,17,18):case['fault']=['missing','corrupt','symlink','replace','instruction_tamper'][j-14];case['expected_status']='UNAVAILABLE'
      elif j==19:q['channel_id']='logical_main_table_pose';case['ambiguity']='Logical table identity is not a pose contract'
      elif j==20:q['assurance']='guaranteed_safe_everywhere'
      elif j==21:case.update(expected_status='SUFFICIENT',abstention_required=False);case['channels']=[CH[2]]
     elif cat=='C9':
      if j<12 or j>=18:
       if j==8:frames=[0]
       if j in (9,11):frames=[e['frames']-1]
       ch=case['channels'][0];idx=CH.index(ch);value=np.asarray(f['frames'][framekeys[frames[0]]][FIELD[idx]][()]);component=1 if j==1 else 0;truth=float(value.reshape(-1)[component]);claim=truth if j%2==0 else truth+1.;case['factual_claim']=dict(component=component,proposed_value=claim,actual_value=truth,claim_true=truth==claim,comparison='Exact float64 identity; counterexample differs by fixed 1, not fitted tolerance')
      elif j==12:case['channels']=[CH[2]]
      elif j==13:case['channels']=[CH[0],CH[2]];extra=['same_execution']
      elif j==14:
       case.update(endpoint='legacy',channels=[],expected_status='INSUFFICIENT' if alias else 'UNAVAILABLE',abstention_required=not alias);q.clear();q.update(execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],object_id='main_table',evidence_types=['support_surface_identity'],interval=[mid,mid],limit=20);extra=['main_table_alias'];case['geometry_reference']=dict(alias_supported=alias,alias_identity=dict(body='table',geom='table_collision') if alias else None);case['reference_artifacts'].extend([source_ref(scene_path,'/phases/*/parsed_bddl_problem'),source_ref(b['xml_path'],'//body[@name="table"]',b['xml_sha256'])])
      elif j==15:case['channels']=[];q['channel_id']='camera_exposure_timestamp';case.update(expected_status='UNAVAILABLE',abstention_required=True);extra=['camera_exposure_timestamp']
      elif j==16:case['channels']=[CH[5]];extra=['physical_support'];case['expected_status']='INSUFFICIENT'
      elif j==17:case['channels']=[CH[0]];extra=['source_hash'];case['expected_status']='SUFFICIENT'
     if case['endpoint']=='physical':
      if 'seconds_interval' not in q and 'interval' in q and cat!='C8':q['interval']=[min(frames),max(frames)] if frames else q['interval']
      case['exact_channel']=case['channels'][0] if len(case['channels'])==1 else None
      if 'channel_id' in q:case['explicit_channel_constraint']=True
      case['required_facets']=case['channels']+extra
     else:case['required_facets']=extra
     references=[];relevant=[];numeric=[]
     for ch in case['channels']:
      rid,raw=rawrows[ch];assert raw['source_sha256']==expected;relevant.append(rid);idx=CH.index(ch)
      for fi in frames:
       if fi<0 or fi>=len(framekeys):continue
       selector='/frames/'+framekeys[fi]+'/'+FIELD[idx];assert selector in f;d=f[selector];value=np.asarray(d[()]);numeric.append(dict(channel=ch,frame=fi,selector=selector,dtype=str(d.dtype),shape=list(d.shape),value=value.tolist(),units=UNITS[idx],source_sha256=expected));references.append(source_ref(source,selector,expected))
     if case['endpoint']=='legacy':
      for rid,body in c.execute('select id,body from evidence where execution_id=? and object_id=?',(ex,q.get('object_id',obj))):
       rr=json.loads(body)
       if rr['measurement_type'] in q.get('evidence_types',[]) and rr['interval'][0]<=q['interval'][1] and rr['interval'][1]>=q['interval'][0]:relevant.append(rid)
     if extra:
      if any(x in extra for x in ('action_metadata','inference_metadata')):references.append(source_ref(source,'/policy_steps/'+f'{action:06d}',expected));assert f'{action:06d}' in f['policy_steps']
      if any(x in extra for x in ('recorder_host_timestamp','simulator_time_label')):references.append(source_ref(source,'/frames/'+framekeys[mid],expected))
      if any(x in extra for x in ('producer_version_declaration','checkpoint_declaration')):references.append(source_ref(directory/'run_metadata.json','/versions' if 'producer_version_declaration' in extra else '/checkpoint_weight_sha256'))
     case['reference_artifacts']+=references;case['expected_source_ids']=sorted(set(relevant));case['reference_samples']=numeric;case['temporal_reference']=dict(saved_indices=frames,alignment='saved_snapshot_association',same_physical_instant=False,action_index=action,pre_action_saved_index=lo,post_action_saved_index=hi,cache_offset_status='CONDITIONAL')
     case['natural_language_query']=formulations[j].format(execution=ex,frame=frames[0] if len(frames)==1 else mid,lo=lo,hi=hi,action=action,tlo=repr(tlo),thi=repr(thi),time=repr(thi),object=obj,claim_value=repr(claim) if claim is not None else 'not_applicable');case['formulation_id']=f'{cat}-formulation-{j:02d}';case['reference_supports_safety_claim']=False
     if case['abstention_required']:case['reference_unavailability_reason']='Explicit source/interface/interpretation/assurance constraint cannot establish requested evidence; see request and required facets'
     cases.append(case)
 assert len(cases)==198 and len({x['natural_language_query'] for x in cases})==198
 assert collections.Counter(x['split'] for x in cases)==dict(development=36,final=162)
 selection=[{k:v for k,v in x.items() if k!='binding'}|dict(task_id=x['binding']['task_id'],variant_id=x['binding']['variant_id']) for x in selected]
 (WORK/'SELECTION_DRAFT.json').write_text(json.dumps(selection,sort_keys=True,indent=2))
 with (WORK/'DATASET_DRAFT.jsonl').open('x') as out:
  for case in sorted(cases,key=lambda x:x['id']):out.write(json.dumps(case,sort_keys=True,allow_nan=False)+'\n')
 print('DATASET DRAFT',len(cases),'selected executions',len(selected),'variants',len({x['binding']['variant_id'] for x in selected}),flush=True)
if __name__=='__main__':build()
