import sqlite3,json,h5py,numpy as np,mujoco
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
w=Path('/disk/1/data/niktakbr/trustworthy-phase5h-working');c=sqlite3.connect('file:/disk/1/data/niktakbr/trustworthy-phase5g-working/expanded.sqlite?mode=ro',uri=True)
b=json.loads(c.execute('select body from rag_execution_env order by execution limit 1').fetchone()[0]);p=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and kind='raw_measurement' limit 1",(b['execution_id'],)).fetchone()[0];m=mujoco.MjModel.from_xml_path(b['xml_path']);d=mujoco.MjData(m);M=np.empty((m.nv,m.nv));rows=[]
print(mujoco.mj_fullM.__doc__,flush=True)
with h5py.File(p) as f:
 for k in list(f['frames'])[1:5]:
  g=f['frames/'+k];q=g['simulator/qpos/value'][()];v=g['simulator/qvel/value'][()];a=g['simulator/qacc/value'][()];pre=q.copy();mujoco.mj_integratePos(m,pre,v,-m.opt.timestep);d.qpos[:]=pre;mujoco.mj_fwdPosition(m,d);mujoco.mj_fullM(m,M,d.qM)
  D=np.diag(m.dof_damping);dv=m.opt.timestep*np.linalg.solve(M+m.opt.timestep*D,M@a);vp=v-dv;raw=np.concatenate([g['raw_observation/robot0_joint_vel/value'][()],g['raw_observation/robot0_gripper_qvel/value'][()]]);error=np.max(abs(vp[:9]-raw));bound=512*np.finfo(float).eps*np.linalg.cond(M+m.opt.timestep*D)*(1+np.linalg.norm(v)+m.opt.timestep*np.linalg.norm(a));rows.append(dict(frame=k,max_error=float(error),roundoff_bound=float(bound),endpoint_difference=float(np.max(abs(v[:9]-raw)))))
with (w/'VELOCITY_PILOT.json').open('x') as f:json.dump(dict(rows=rows,equation='v_pre=v_end-h*(M(q_pre)+hD)^-1*M(q_pre)*qacc_saved',steps_run=0,kinematic_position_evaluations=len(rows)),f,indent=2)
print(rows,flush=True)
