"""All-source semantic and temporal audit; no replay, stepping or interpolation."""
import json,sqlite3,collections,hashlib,time
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import CHANNELS,owned
from .config import WORK,HERE,BASE,NAMES,TOLERANCE_POLICY

def save(path,v):
 with Path(path).open('x') as f:json.dump(v,f,sort_keys=True,indent=2)
def run():
 c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);maps={json.load(p.open())['variant_id']:(p,json.load(p.open())) for p in (WORK/'models').glob('*.json')};assert len(maps)==104
 rows=[];sources={};eps=np.finfo(np.float64).eps
 local=Path('/disk/0/home/niktakbr/rdt-1b-libero/.venv/lib/python3.12/site-packages/robosuite')
 references=[REPO/'reports/fall_review_v2_20261016/source_evidence'/n for n in ('recording_base.py','run_oft.py','robosuite__environments__base.py','robosuite__utils__binding_utils.py','robosuite__utils__observables.py','robosuite__macros.py')]
 references += [local/n for n in ('robots/robot.py','robots/single_arm.py','models/grippers/panda_gripper.py','models/robots/robot_model.py','models/base.py','utils/observables.py')]
 references += list((WORK/'primary').glob('*.c'))+list((WORK/'primary').glob('*.h'))
 for p in references:sources[str(p)]=sha(p)
 for execution,binding in c.execute('select execution,body from rag_execution_env order by execution'):
  b=json.loads(binding);mapp,m=maps[b['variant_id']];joints={r['name']:r for r in m['joints']};js=[joints[n] for n in NAMES];assert [j['type'] for j in js]==[3]*7+[2]*2
  assert len(m['actuators'])==9 and all(a['transmission_type']==0 and a['gear']==[1.,0.,0.,0.,0.,0.] for a in m['actuators'])
  assert [a['joint_id'] for a in m['actuators']]==[j['id'] for j in js]
  assert m['integrator']==0 and m['timestep']==.002
  metadata=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(execution,)).fetchone()[0];meta=json.load(open(metadata));directory=Path(metadata).parent;hdf=directory/'trajectory.h5';assert meta['control_frequency_hz']==20 and meta['settling_steps']==10
  for name in ('recording_base.py','run_oft.py'):
   path=REPO/'reports/fall_review_v2_20261016/source_evidence'/name;assert meta['source_files_sha256'][name]==sha(path)
  assert meta['versions']['mujoco']=='3.8.1' and meta['versions']['robosuite']=='1.4.0'
  qa=[j['qpos_address'] for j in js];va=[j['qvel_address'] for j in js];h=m['timestep'];cfgerr=[];forceerr=[];timeerr=[];rawendpoint=[];velocityendpoint=[];failures=[];frame_rows=[];count_checks=action_checks=0;states=collections.Counter()
  with h5py.File(hdf,'r') as f:
   keys=list(f['frames']);assert [int(k) for k in keys]==list(range(len(keys)));assert f.attrs['global_episode_id']==execution
   for i,key in enumerate(keys):
    g=f['frames/'+key];stage=str(g.attrs['stage']);states[stage]+=1;sim=g['simulator'];obs=g['raw_observation'];t=float(sim['time/value'][()]);q=sim['qpos/value'][()][qa];v=sim['qvel/value'][()][va];rawq=np.concatenate([obs['robot0_joint_pos/value'][()],obs['robot0_gripper_qpos/value'][()]]);rawv=np.concatenate([obs['robot0_joint_vel/value'][()],obs['robot0_gripper_qvel/value'][()]])
    assert rawq.dtype==np.dtype('float64') and rawv.dtype==np.dtype('float64')
    pre=q if i==0 else q-h*v;error=abs(rawq-pre);bound=64*eps*(1+abs(q)+abs(h*v));cfgerr.extend(error.tolist());rawendpoint.extend(abs(rawq-q).tolist());velocityendpoint.extend(abs(rawv-v).tolist())
    if not np.all(error<=bound):failures.append(dict(frame=i,property='configuration_preintegration_identity',max_error=float(max(error)),bound=float(max(bound))))
    time_error=abs(t-i*.05);timeerr.append(time_error);assert time_error<=64*eps*(1+i*25)*(1+abs(t))
    force=sim['actuator_force/value'][()];ctrl=sim['ctrl/value'][()];pred=[];fb=[]
    for a,j,qp in zip(m['actuators'],js,rawq):
     assert a['dyn_type']==0 and a['gain_type']==0 and a['bias_type'] in (0,1)
     gain=a['gain'][0];bias=a['bias'];val=gain*ctrl[a['id']]+(bias[0]+bias[1]*qp if a['bias_type']==1 else 0.)
     if a['id']>=7:val=np.clip(val,-20.,20.)
     pred.append(val);fb.append(64*eps*(1+abs(gain*ctrl[a['id']])+abs(bias[1]*qp)))
    fe=abs(force-np.asarray(pred));forceerr.extend(fe.tolist())
    if not np.all(fe<=fb):failures.append(dict(frame=i,property='actuator_force_equation',max_error=float(max(fe)),bound=float(max(fb))))
    contacts=sim['contacts'];n=len(json.loads(contacts.attrs['json'])) if 'json' in contacts.attrs else len(contacts['value']);assert int(sim['ncon/value'][()])==n;count_checks+=1
    if i==0:assert stage=='before_settling'
    elif i<=10:assert stage=='settling'
    else:
     step=i-11;tr=f['transitions/'+f'{step:06d}'];policy=f['policy_steps/'+f'{step:06d}'];assert int(g.attrs['control_step'])==step and int(tr['step/value'][()])==step and float(tr['simulator_time/value'][()])==t
     assert np.array_equal(tr['executed_action/value'][()],policy['executed_action/value'][()]);assert int(tr['monotonic_ns/value'][()])>=int(g.attrs['monotonic_ns']);action_checks+=1
    frame_rows.append(dict(saved_frame=i,stage=stage,simulator_endpoint_seconds=t,preceding_policy_action=i-11 if i>=11 else None,policy_input_frame=i-1 if i>=11 else None,raw_configuration_relation='initial_endpoint' if i==0 else 'Euler_preintegration_identity',synchronized_physical_instant=False))
   assert len(f['transitions'])==len(keys)-11 and stage=='terminal'
  def stats(xs):return dict(max=max(xs),mean=sum(xs)/len(xs),components=len(xs))
  row=dict(execution_id=execution,task_id=b['task_id'],variant_id=b['variant_id'],model_map_path=str(mapp),model_map_sha256=sha(mapp),source_path=str(hdf),source_sha256=sha(hdf),metadata_path=metadata,metadata_sha256=sha(metadata),frames=len(keys),joints=js,actuators=m['actuators'],timestep=h,action_interval=.05,configuration_identity_error=stats(cfgerr),actuator_equation_error=stats(forceerr),timestamp_error=stats(timeerr),raw_endpoint_difference=stats(rawendpoint),velocity_endpoint_difference=stats(velocityendpoint),contact_count_comparisons=count_checks,action_alignment_comparisons=action_checks,stage_counts=dict(states),contract_failures=failures,temporal_rows=frame_rows,producer_binary_attestation=False)
  rows.append(row)
  if len(rows)%25==0:print('Audited semantics/time',len(rows),flush=True)
 save(WORK/'PRIMARY_SOURCES.json',dict(files=[dict(path=p,sha256=h) for p,h in sources.items()],qualifier='Recorder/run hashes match execution metadata. Installed robosuite sources are version-matched references, not recording-time binary attestations. Official MuJoCo 3.8.1 source is pinned in FETCH_MANIFEST.'))
 save(WORK/'SEMANTIC_AUDIT.json',dict(executions=len(rows),variants=len(maps),samples=sum(r['frames'] for r in rows),tolerance_policy=TOLERANCE_POLICY,contract_failures=sum(len(r['contract_failures']) for r in rows),rows=rows))
 print('AUDIT COMPLETE',len(rows),'failures',sum(len(r['contract_failures']) for r in rows),flush=True)
if __name__=='__main__':run()
