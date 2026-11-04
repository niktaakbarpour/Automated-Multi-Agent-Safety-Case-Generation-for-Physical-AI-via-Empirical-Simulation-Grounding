"""Independent inverse Euler consistency oracle. Kinematic mass evaluation only, no stepping."""
import json,sqlite3,time
import numpy as np,h5py,mujoco
from .config import WORK,BASE,NAMES
from .audit import save

def run():
 assert mujoco.__version__=='3.8.1';start=time.perf_counter();c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);rows=[];models={};eps=np.finfo(float).eps
 for execution,body in c.execute('select execution,body from rag_execution_env order by execution'):
  b=json.loads(body);variant=b['variant_id']
  if variant not in models:models[variant]=mujoco.MjModel.from_xml_path(b['xml_path'])
  m=models[variant];d=mujoco.MjData(m);M=np.zeros((m.nv,m.nv));h=m.opt.timestep;D=np.diag(m.dof_damping);ids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n) for n in NAMES];adrs=[int(m.jnt_dofadr[i]) for i in ids]
  path=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and kind='raw_measurement' limit 1",(execution,)).fetchone()[0];errors=[];arm=[];gripper=[];position_arm=[];position_gripper=[];bounds=[];failures=[];maxcond=0
  with h5py.File(path) as f:
   for i,k in enumerate(f['frames']):
    g=f['frames/'+k];q=g['simulator/qpos/value'][()];v=g['simulator/qvel/value'][()];acc=g['simulator/qacc/value'][()];raw=np.concatenate([g['raw_observation/robot0_joint_vel/value'][()],g['raw_observation/robot0_gripper_qvel/value'][()]])
    if not i:pred=v;bound=0.
    else:
     pre=q.copy();mujoco.mj_integratePos(m,pre,v,-h);d.qpos[:]=pre;mujoco.mj_fwdPosition(m,d);mujoco.mj_fullM(m,M,d.qM);A=M+h*D;cond=float(np.linalg.cond(A));maxcond=max(cond,maxcond);pred=v-h*np.linalg.solve(A,M@acc);bound=float(512*eps*cond*(1+np.linalg.norm(v)+h*np.linalg.norm(acc)))
    error=abs(pred[adrs]-raw);errors.extend(error.tolist());arm.extend(error[:7].tolist());gripper.extend(error[7:].tolist());bounds.append(bound)
    qadr=[int(m.jnt_qposadr[j]) for j in ids];rawq=np.concatenate([g['raw_observation/robot0_joint_pos/value'][()],g['raw_observation/robot0_gripper_qpos/value'][()]]);qp=q[qadr] if not i else q[qadr]-h*v[adrs];qe=abs(qp-rawq);position_arm.extend(qe[:7].tolist());position_gripper.extend(qe[7:].tolist())
    if max(error)>bound:failures.append(dict(frame=i,error=float(max(error)),roundoff_bound=bound))
  rows.append(dict(execution_id=execution,variant_id=variant,samples=len(bounds),components=len(errors),maximum_error=max(errors),mean_error=sum(errors)/len(errors),by_channel={k:dict(maximum_error=max(xs),mean_error=sum(xs)/len(xs),components=len(xs),units=u) for k,xs,u in (('raw.robot0_joint_vel',arm,'rad/s'),('raw.robot0_gripper_qvel',gripper,'m/s'),('raw.robot0_joint_pos',position_arm,'rad'),('raw.robot0_gripper_qpos',position_gripper,'m'))},maximum_roundoff_bound=max(bounds),maximum_condition_number=maxcond,failures=failures))
  if len(rows)%25==0:print('Inverse Euler velocity validation',len(rows),flush=True)
 result=dict(passed=not any(r['failures'] for r in rows),equation='v_pre = v_endpoint - h solve(M(q_pre)+h diag(dof_damping), M(q_pre) qacc_saved)',configuration_inverse='mj_integratePos(model,q_endpoint,v_endpoint,-h); no interpolated samples are produced',tolerance='512*float64_eps*cond(M+hD)*(1+norm(v_endpoint)+h*norm(qacc_saved)), frozen in pilot before full validation',executions=len(rows),variants=len(models),samples=sum(r['samples'] for r in rows),maximum_error=max(r['maximum_error'] for r in rows),mean_error=sum(r['mean_error']*r['components'] for r in rows)/sum(r['components'] for r in rows),simulation_steps=0,kinematic_mass_evaluations=sum(r['samples']-1 for r in rows),seconds=time.perf_counter()-start,rows=rows,qualification='Model algebraic consistency. Does not attest recording-time binary, observed sensor cache clock or a physical common instant. No shifted/derived values are indexed.')
 save(WORK/'VELOCITY_BY_CHANNEL.json',result);assert result['passed'];print('VELOCITY COMPLETE',result['maximum_error'],flush=True)
if __name__=='__main__':run()
