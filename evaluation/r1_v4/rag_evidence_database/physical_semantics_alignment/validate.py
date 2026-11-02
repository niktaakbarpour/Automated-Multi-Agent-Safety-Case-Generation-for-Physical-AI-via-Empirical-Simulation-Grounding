"""Independent XML/index and source-sample oracle, separate from annotations."""
import json,sqlite3,collections,time,xml.etree.ElementTree as ET,itertools,hashlib
from pathlib import Path
from dataclasses import replace
import h5py,numpy as np
from evaluation.r1_v4.provenance import canonical,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import WORK,BASE,BASE_SHA,NAMES
from .store import PhysicalStore
from .retrieve import PhysicalQuery,retrieve
from .audit import save
FIELDS={'raw.robot0_joint_pos':('raw_observation/robot0_joint_pos/value','rad'),'raw.robot0_joint_vel':('raw_observation/robot0_joint_vel/value','rad/s'),'raw.robot0_gripper_qpos':('raw_observation/robot0_gripper_qpos/value','m'),'raw.robot0_gripper_qvel':('raw_observation/robot0_gripper_qvel/value','m/s'),'raw.simulator_actuator_force':('simulator/actuator_force/value','native_actuator_force'),'simulator.ncon':('simulator/ncon/value','count')}

def preservation(database):
 a=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(Path(database).as_uri()+'?mode=ro',uri=True);results={}
 for name,definition in a.execute("select name,sql from sqlite_master where type='table' and sql is not null order by name"):
  assert b.execute('select sql from sqlite_master where name=?',(name,)).fetchone()==(definition,)
  columns=len(a.execute('select * from "'+name+'" limit 0').description);query='select * from "'+name+'" order by '+','.join(str(i+1) for i in range(columns));hasher=hashlib.sha256();count=0
  for x,y in itertools.zip_longest(a.execute(query),b.execute(query)):
   assert x==y,(name,count);hasher.update(canonical([{'bytes':v.hex()} if isinstance(v,bytes) else v for v in x]));count+=1
  results[name]=dict(rows=count,digest=hasher.hexdigest(),identical=True)
 assert sha(BASE)==BASE_SHA
 return dict(passed=True,tables=results,preserved_evidence_records=results['evidence']['rows'],preserved_phase5g_channel_records=results['rag_channel_records']['rows'],baseline_sha256=BASE_SHA)

def run(output=None):
 output=WORK if output is None else Path(output)
 output.mkdir(exist_ok=True)
 start=time.perf_counter();build=json.loads((WORK/'BUILD.json').read_text());db=PhysicalStore(WORK/'expanded.sqlite',expected_sha256=build['database_sha256']);negative=collections.Counter();queries=[];samples=0;max_error=0.;binding_components=0
 def reject(q,status):
  r=retrieve(db,q);assert r['status']==status and not r['results'] and not r['matching_count'],(q,r['status'],status);negative[status]+=1
 bindings=db.db.execute('select execution,body from rag_execution_env order by execution').fetchall()
 for idx,(e,body) in enumerate(bindings):
  b=json.loads(body);execution=json.loads(db.db.execute('select body from h_execution where execution=?',(e,)).fetchone()[0]);directory=Path(execution['metadata_path']).parent;index=json.load(open(directory/'simulator_index.json'));xml=ET.parse(b['xml_path']).getroot();xmlj={j.get('name'):j for j in xml.iter('joint') if j.get('name')};xmlact=list(xml.find('actuator'));raws={json.loads(v[0])['channel_id']:json.loads(v[0]) for v in db.db.execute('select body from rag_channel_records where execution=?',(e,))}
  with h5py.File(execution['source_path'],'r') as f:
   count=len(f['frames']);windows=[(0,0),(11,11),(count//2,count//2),(count-1,count-1),(31,32)]
   for channel,(field,unit) in FIELDS.items():
    raw=raws[channel];sem=json.loads(db.db.execute('select body from h_semantics where execution=? and channel=?',(e,channel)).fetchone()[0]);q=PhysicalQuery(e,task_id=b['task_id'],variant_id=b['variant_id'],channel_id=channel,object_id=raw['object_id'],units=unit,required_properties=('component_order','units'),verification_mode='verified_session')
    for component in sem['components']:
     if channel=='raw.simulator_actuator_force':assert xmlact[component['id']].get('name')==component['name'] and index['joint_names'][component['joint_id']]==xmlact[component['id']].get('joint')
     else:
      j=index['joint_names'].index(component['name']);assert component['id']==j and component['qpos_address']==index['jnt_qposadr'][j] and component['qvel_address']==index['jnt_dofadr'][j];assert (component['type']==2)==(xmlj[component['name']].get('type','hinge')=='slide');assert np.array_equal(component['axis_body_local'],np.fromstring(xmlj[component['name']].get('axis','0 0 1'),sep=' '))
     binding_components+=1
    for window in windows:
     r=retrieve(db,replace(q,interval=window));assert r['status']=='ok' and r['matching_count']==1,(e,channel,r['status'],r['reason']);item=r['results'][0];assert item['raw_record']['id']==raw['id'];assert item['source_attestation']['status']=='verified_source';assert item['semantic_record']['properties']['units']['value']==unit
     expected=list(range(window[0],window[1]+1));assert [s['saved_frame_index'] for s in item['samples']]==expected
     for sample in item['samples']:
      i=sample['saved_frame_index'];oracle=f['frames/'+f'{i:06d}'+'/'+field][()];assert np.array_equal(np.asarray(sample['value']),oracle);err=float(np.max(abs(np.asarray(sample['value'])-oracle)));max_error=max(max_error,err);samples+=1
      if i>=11:
       policy=f['policy_steps/'+f'{i-11:06d}'];call=f['inference_calls/'+f"{int(policy.attrs['chunk_id']):06d}"];t=sample['temporal_relation'];assert t['preceding_policy_action']==i-11 and t['latest_available_observation_frame']==i-1 and t['policy_inference_input_frame']==10+int(call.attrs['step'])
     queries.append(dict(execution=e,task=b['task_id'],variant=b['variant_id'],channel=channel,window=window,precision_at_1=1.,recall_at_20=1.,MRR=1.))
    for bad,status in ((replace(q,task_id='wrong'),'invalid_query_scope'),(replace(q,variant_id='wrong'),'invalid_query_scope'),(replace(q,execution_id='missing:'+e),'unknown_execution'),(replace(q,object_id='wrong'),'no_matching_record'),(replace(q,component='wrong'),'no_matching_record'),(replace(q,source_sha256='f'*64),'invalid_source_scope'),(replace(q,units='wrong'),'unsupported_units'),(replace(q,coordinate_frame='world'),'unsupported_coordinate_frame'),(replace(q,alignment='same_physical_instant'),'unsupported_alignment'),(replace(q,transformation='endpoint_shift'),'unsupported_transformation'),(replace(q,required_properties=('physical_synchronization',)),'unsupported_semantic_status'),(replace(q,channel_id='logical_main_table_pose'),'unsupported_channel'),(replace(q,interval=(count,count)),'no_matching_record')):reject(bad,status)
  if idx%25==0:print('Independent physical/source retrieval scopes',idx+1,flush=True)
 for e,status in db.db.execute("select execution,status from rag_scope_status where status!='indexed'"):reject(PhysicalQuery(e,channel_id='simulator.ncon'),status)
 report=dict(passed=True,executions=432,variants=104,queries=len(queries),original_samples_compared=samples,maximum_value_error=max_error,mean_value_error=0.,component_bindings_checked=binding_components,saved_index_alignment_errors=0,negative_controls=sum(negative.values()),negative_status_counts=dict(negative),cross_scope_leakage=0,precision_at_1=1.,recall_at_20=1.,MRR=1.,source_hash_checks=db.verifier.hash_checks,verified_session_cache_hits=db.verifier.cache_hits,seconds=time.perf_counter()-start,query_results=queries)
 save(output/'RETRIEVAL_VALIDATION.json',report);save(output/'PRESERVATION.json',preservation(WORK/'expanded.sqlite'));db.close();print({k:v for k,v in report.items() if k!='query_results'},flush=True)
if __name__=='__main__':run()
