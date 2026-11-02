"""Recorded clock labels are not sensor clocks; no reconstructed timestamps are recorded as raw."""
import json,sqlite3,datetime,collections
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
from .config import WORK,BASE
from .inventory import save

DEFINITIONS={
 'saved_frame_index':dict(kind='INDEX',units='index',epoch='Execution-local saved index zero',status='RECORDED_INDEX',source='/frames/{key}',physical_instant=False),
 'simulator_endpoint_label':dict(kind='SIMULATOR_TIME',units='s',epoch='Recorded state clock starts at zero in admitted recordings',status='RECORDED_CLOCK_LABEL',source='/frames/{key}/simulator/time/value',physical_instant=False),
 'recorder_host_wall_ns':dict(kind='RECORDER_HOST_TIME',units='ns',epoch='POSIX epoch defined by time.time_ns API; actual host synchronization unattested',status='RECORDED_CLOCK_LABEL',source='/frames/{key}/@wall_time_ns',physical_instant=False),
 'recorder_host_monotonic_ns':dict(kind='RECORDER_HOST_TIME',units='ns',epoch=None,status='RECORDED_CLOCK_LABEL',source='/frames/{key}/@monotonic_ns',physical_instant=False),
 'recorder_utc':dict(kind='RECORDER_HOST_TIME',units='ISO8601 UTC text',epoch='Host UTC API convention, not independent timestamp authority',status='RECORDED_CLOCK_LABEL',source='/frames/{key}/@utc',physical_instant=False),
 'action_transition_simulator_label':dict(kind='ACTION_POST_CALL_TIME',units='s',epoch='Same recorded simulator state clock',status='RECORDED_CLOCK_LABEL',source='/transitions/{step}/simulator_time/value',physical_instant=False),
 'action_transition_host_wall_ns':dict(kind='ACTION_POST_CALL_TIME',units='ns',epoch='Host POSIX API convention',status='RECORDED_CLOCK_LABEL',source='/transitions/{step}/wall_time_ns/value',physical_instant=False),
 'action_transition_host_monotonic_ns':dict(kind='ACTION_POST_CALL_TIME',units='ns',epoch=None,status='RECORDED_CLOCK_LABEL',source='/transitions/{step}/monotonic_ns/value',physical_instant=False),
 'policy_step_utc':dict(kind='ACTION_SCHEDULING_LABEL',units='ISO8601 UTC text',epoch='Host UTC API convention',status='RECORDED_CLOCK_LABEL',source='/policy_steps/{step}/@utc',physical_instant=False),
 'inference_utc':dict(kind='INFERENCE_RECORDING_LABEL',units='ISO8601 UTC text',epoch='Host UTC API convention',status='RECORDED_CLOCK_LABEL',source='/inference_calls/{chunk}/@utc',physical_instant=False),
 'inference_elapsed':dict(kind='HOST_ELAPSED_DURATION',units='s',epoch=None,status='RECORDED_DURATION',source='/inference_calls/{chunk}/@inference_elapsed_s',physical_instant=False),
 'joint_sensor_clock':dict(kind='SENSOR_TIME',units=None,epoch=None,status='UNAVAILABLE',source=None,physical_instant=False),
 'gripper_sensor_clock':dict(kind='SENSOR_TIME',units=None,epoch=None,status='UNAVAILABLE',source=None,physical_instant=False),
 'actuator_sensor_clock':dict(kind='SENSOR_TIME',units=None,epoch=None,status='UNAVAILABLE',source=None,physical_instant=False),
 'contact_sensor_clock':dict(kind='SENSOR_TIME',units=None,epoch=None,status='UNAVAILABLE',source=None,physical_instant=False),
 'camera_sensor_clock':dict(kind='SENSOR_TIME',units=None,epoch=None,status='UNAVAILABLE',source=None,physical_instant=False),
 'resource_host_clock':dict(kind='RESOURCE_RECORDING_TIME',units=None,epoch=None,status='PAYLOAD_NOT_RESTORED',source='resources.csv recorded hash exists; payload not locally available',physical_instant=False)}

def run():
 c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);v=SourceVerifier();rows=[];checked=0
 sensors=('raw_observation/robot0_joint_pos','raw_observation/robot0_joint_vel','raw_observation/robot0_gripper_qpos','raw_observation/robot0_gripper_qvel','raw_observation/agentview_image','raw_observation/robot0_eye_in_hand_image','simulator/actuator_force','simulator/ncon')
 for e,body in c.execute('select execution,body from rag_execution_env order by execution'):
  b=json.loads(body);source,expected=c.execute("select json_extract(body,'$.source_path'),json_extract(body,'$.source_sha256') from rag_channel_records where execution=? limit 1",(e,)).fetchone();samples=[];actions=[];policies=[];inferences=[];sensor_timestamp_fields=[]
  with v.access(source,expected,'verified_session') as (file,_):
   with h5py.File(file) as f:
    for key,g in f['frames'].items():
     i=int(key);sim=float(g['simulator/time/value'][()]);wall=int(g.attrs['wall_time_ns']);mono=int(g.attrs['monotonic_ns']);utc=str(g.attrs['utc']);samples.append(dict(frame=i,simulator_endpoint_label=sim,recorder_host_wall_ns=wall,recorder_host_monotonic_ns=mono,recorder_utc=utc));assert abs(sim-i*.05)<=64*np.finfo(float).eps*(1+i*25)*(1+abs(sim))
     for name in sensors:
      group=g[name];checked+=1
      for target in (group,group.get('value')):
       if target is None:continue
       for attr in target.attrs:
        if any(s in attr.lower() for s in ('timestamp','capture_time','sample_time','clock')):sensor_timestamp_fields.append('/frames/'+key+'/'+name+'/@'+attr)
    for key,g in f['transitions'].items():
     step=int(g['step/value'][()]);sim=float(g['simulator_time/value'][()]);assert sim==samples[step+11]['simulator_endpoint_label'];actions.append(dict(step=step,frame=step+11,simulator_label=sim,wall_ns=int(g['wall_time_ns/value'][()]),monotonic_ns=int(g['monotonic_ns/value'][()])))
    for key,g in f['policy_steps'].items():policies.append(dict(step=int(key),utc=str(g.attrs['utc']),chunk_id=int(g.attrs['chunk_id']),chunk_offset=int(g.attrs['chunk_offset'])))
    for key,g in f['inference_calls'].items():inferences.append(dict(chunk_id=int(key),step=int(g.attrs['step']),utc=str(g.attrs['utc']),elapsed_s=float(g.attrs['inference_elapsed_s'])))
  assert not sensor_timestamp_fields
  assert all(samples[j]['recorder_host_monotonic_ns']>=samples[j-1]['recorder_host_monotonic_ns'] for j in range(1,len(samples)))
  deltas=[s['recorder_host_wall_ns']-s['recorder_host_monotonic_ns'] for s in samples]
  rows.append(dict(execution_id=e,task_id=b['task_id'],variant_id=b['variant_id'],source_path=source,source_sha256=expected,samples=samples,actions=actions,policy_records=policies,inference_records=inferences,per_sensor_timestamp_fields=sensor_timestamp_fields,host_wall_minus_monotonic_observed_ns=dict(min=min(deltas),max=max(deltas),span=max(deltas)-min(deltas),classification='SEPARATE_API_READ_DIFFERENCE; not a calibrated clock offset or drift'),cache_offset=dict(seconds=-.002,status='CONDITIONAL',physical_synchronization='UNRESOLVED'),hardware_clock_attestation='UNATTESTED'))
  if len(rows)%25==0:print('Clock audit',len(rows),flush=True)
 save('CLOCK_AUDIT.json',dict(executions=len(rows),variants=len({r['variant_id'] for r in rows}),saved_frames=sum(len(r['samples']) for r in rows),action_labels=sum(len(r['actions']) for r in rows),sensor_groups_checked=checked,definitions=DEFINITIONS,rows=rows,qualification='Only directly recorded labels/durations are stored. No sensor timestamps, clock origin, synchronization or interpolated samples are fabricated.'))
 print('CLOCK AUDIT COMPLETE',len(rows),checked,flush=True)
if __name__=='__main__':run()
