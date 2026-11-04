import json,sqlite3,hashlib
from pathlib import Path
import mujoco,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
w=Path('/disk/1/data/niktakbr/trustworthy-phase5h-working');out=w/'models';out.mkdir(exist_ok=True);assert mujoco.__version__=='3.8.1'
c=sqlite3.connect('file:/disk/1/data/niktakbr/trustworthy-phase5g-working/expanded.sqlite?mode=ro',uri=True);by={}
for execution,body in c.execute('select execution,body from rag_execution_env order by execution'):
 b=json.loads(body);by.setdefault(b['variant_id'],[]).append(b)
for variant,bindings in by.items():
 p=out/(variant.replace(':','_')+'.json')
 if p.exists():continue
 b=bindings[0]
 for a in json.loads(c.execute('select body from rag_env_variants where id=?',(variant,)).fetchone()[0])['assets']:assert sha(owned(a['path']))==a['sha256']
 assert sha(b['xml_path'])==b['xml_sha256'];m=mujoco.MjModel.from_xml_path(b['xml_path']);name=lambda t,i:mujoco.mj_id2name(m,t,i)
 joints=[dict(id=i,name=name(mujoco.mjtObj.mjOBJ_JOINT,i),type=int(m.jnt_type[i]),body_id=int(m.jnt_bodyid[i]),body_name=name(mujoco.mjtObj.mjOBJ_BODY,int(m.jnt_bodyid[i])),qpos_address=int(m.jnt_qposadr[i]),qvel_address=int(m.jnt_dofadr[i]),axis_body_local=m.jnt_axis[i].tolist(),anchor_body_local=m.jnt_pos[i].tolist()) for i in range(m.njnt)]
 actuators=[dict(id=i,name=name(mujoco.mjtObj.mjOBJ_ACTUATOR,i),transmission_type=int(m.actuator_trntype[i]),joint_id=int(m.actuator_trnid[i,0]),gear=m.actuator_gear[i].tolist(),gain_type=int(m.actuator_gaintype[i]),bias_type=int(m.actuator_biastype[i]),gain=m.actuator_gainprm[i].tolist(),bias=m.actuator_biasprm[i].tolist(),dyn_type=int(m.actuator_dyntype[i])) for i in range(m.nu)]
 rows=[]
 for b in bindings:
  meta=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(b['execution_id'],)).fetchone()[0];index=Path(meta).parent/'simulator_index.json';d=json.load(index.open());assert d['joint_names']==[j['name'] for j in joints] and d['jnt_qposadr']==[j['qpos_address'] for j in joints] and d['jnt_dofadr']==[j['qvel_address'] for j in joints];rows.append(dict(execution_id=b['execution_id'],index_path=str(index),index_sha256=sha(index)))
 r=dict(version='physical-native-map-1.0.0',variant_id=variant,xml_path=b['xml_path'],xml_sha256=b['xml_sha256'],mujoco_version=mujoco.__version__,timestep=float(m.opt.timestep),integrator=int(m.opt.integrator),dimensions=dict(nq=m.nq,nv=m.nv,nu=m.nu),joints=joints,actuators=actuators,executions=rows,simulation_steps=0,mjdata_created=False,compiler_record_path=str(Path(mujoco.__file__).parent.parent/'mujoco-3.8.1.dist-info/RECORD'))
 r['compiler_record_sha256']=sha(r['compiler_record_path'])
 with p.open('x') as f:json.dump(r,f,sort_keys=True,indent=2)
 print('Compiled identity',len(list(out.glob('*.json'))),len(bindings),flush=True)
print('NATIVE MAPS COMPLETE',flush=True)
