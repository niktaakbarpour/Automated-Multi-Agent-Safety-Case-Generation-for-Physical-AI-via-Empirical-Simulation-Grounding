"""Compile verified saved MJCF for identities only. Never create data or step physics."""
import importlib.metadata
from pathlib import Path
import numpy as np
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.libero_measurement_reader.reader import native_index

def rotations(q):
 q=np.asarray(q);w,x,y,z=q.T;s=2/np.sum(q*q,axis=1)
 return np.stack([1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w),s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w),s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)],axis=-1).reshape(-1,3,3)

def compile_profile(xml,assets,index,snapshot,object_names,execution_ids,fixture_names):
 import mujoco
 verified_assets=[];cache={}
 for row in load(assets)['assets']:
  p=Path(row['path']).resolve()
  if not any(p.is_relative_to(root) for root in ('/local/home/niktakbr','/disk/0/home/niktakbr','/disk/1/data/niktakbr')):raise ValueError('asset outside approved local storage')
  if str(p) not in cache:cache[str(p)]=sha(p)
  if cache[str(p)]!=row['sha256'] or p.stat().st_size!=row['bytes']:raise ValueError('asset provenance failed')
  verified_assets.append({'path':str(p),'sha256':cache[str(p)],'bytes':row['bytes']})
 model=mujoco.MjModel.from_xml_path(str(xml))
 # No MjData, mj_step, mj_forward, rollout, camera rendering or model inference.
 name=lambda kind,i:mujoco.mj_id2name(model,kind,i)
 bodies=[name(mujoco.mjtObj.mjOBJ_BODY,i) for i in range(model.nbody)]
 geoms=[name(mujoco.mjtObj.mjOBJ_GEOM,i) for i in range(model.ngeom)]
 legacy=load(index)
 if bodies!=legacy['body_names'] or [n for n in geoms if n is not None]!=legacy['geom_names']:raise ValueError('compiled complete native identities disagree with recorded name projection')
 if list(map(int,model.jnt_qposadr))!=legacy['jnt_qposadr'] or list(map(int,model.jnt_dofadr))!=legacy['jnt_dofadr']:raise ValueError('joint address mapping mismatch')
 if any(n is None for n in bodies):raise ValueError('unnamed bodies require explicit new contract')
 bp=snapshot['body_xpos'];br=rotations(snapshot['body_xquat']);gp=snapshot['geom_xpos'];gr=snapshot['geom_xmat'].reshape(-1,3,3)
 if bp.shape!=(model.nbody,3) or gp.shape!=(model.ngeom,3):raise ValueError('compiled native dimensions differ from saved arrays')
 pairs=set(int(x) for x in model.pair_geom1)|set(int(x) for x in model.pair_geom2);rows=[]
 for i in range(model.ngeom):
  owner=int(model.geom_bodyid[i]);anc=[];bid=owner;moving=False
  while True:
   anc.append(bodies[bid]);moving=moving or bool(model.body_jntnum[bid]) or int(model.body_mocapid[bid])>=0
   if not bid:break
   bid=int(model.body_parentid[bid])
  rows.append({'native_geom_id':i,'name':geoms[i],'owner_body':bodies[owner],'owner_body_id':owner,'body_ancestry':anc,'type':mujoco.mjtGeom(int(model.geom_type[i])).name.removeprefix('mjGEOM_').lower(),'size':model.geom_size[i].tolist(),'collision_capable':bool(model.geom_contype[i] or model.geom_conaffinity[i] or i in pairs),'static':not moving,'local_position_derived_from_recorded_snapshot':(br[owner].T@(gp[i]-bp[owner])).tolist(),'local_rotation_derived_from_recorded_snapshot':(br[owner].T@gr[i]).tolist(),'compiled_declared_local_position':model.geom_pos[i].tolist(),'physical_uncertainty_calibrated':False})
 mapping={'schema_version':'native-geometry-index-v2','source_xml_sha256':sha(xml),'native_geom_count':model.ngeom,'body_names':bodies,'validated_run_ids':execution_ids,'geometries':rows,'compiler_version':mujoco.__version__,'compiler_record_sha256':sha(Path(mujoco.__file__).parent.parent/f'mujoco-{mujoco.__version__}.dist-info/RECORD'),'verification':'MJCF compiled IDs, complete body/name projections and joint addresses; snapshot-derived rigid local coordinates, not physical calibration','simulation_steps':0}
 native_index(mapping).validate_snapshot_transforms(bp,snapshot['body_xquat'],gp,snapshot['geom_xmat'])
 objects={}
 for obj in sorted(object_names):
  root=obj+'_main'
  if root not in bodies:raise ValueError('missing declared object root:'+root)
  bid=bodies.index(root);ids=[r['native_geom_id'] for r in rows if root in r['body_ancestry'] and r['collision_capable']]
  if not ids:raise ValueError('no verified collision references:'+obj)
  objects[obj]={'body_id':bid,'root_body':root,'collision_geom_ids':ids,'geometry_types':sorted({rows[i]['type'] for i in ids})}
 surfaces=[r['native_geom_id'] for r in rows if any(name in r['body_ancestry'] for name in fixture_names) and r['static'] and r['collision_capable']]
 if not surfaces:raise ValueError('no verified configured static fixture geometry')
 nq,nv,nb,ng,nu=map(int,(model.nq,model.nv,model.nbody,model.ngeom,model.nu))
 shapes={'time':[],'qpos':[nq],'qvel':[nv],'ctrl':[nu],'flattened':[1+nq+nv],'body_xpos':[nb,3],'body_xquat':[nb,4],'geom_xpos':[ng,3],'geom_xmat':[ng,9],'ncon':[]}
 optional={'qacc':[nv],'act':[int(model.na)],'sensordata':[int(model.nsensordata)],'actuator_force':[nu],'cfrc_ext':[nb,6],'cvel':[nb,6]}
 return {'mapping':mapping,'objects':objects,'surface_ids':surfaces,'surface_roots':fixture_names,'shapes':shapes,'optional_shapes':optional,'verified_assets':verified_assets,'bounds_and_support_admission':False}
