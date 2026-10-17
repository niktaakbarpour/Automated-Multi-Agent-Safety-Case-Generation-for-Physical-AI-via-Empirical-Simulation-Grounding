"""Targeted settling/timing/ID investigation. No dynamics steps or event verdicts."""
import argparse,collections,csv,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import h5py,mujoco,numpy as np
from PIL import Image,ImageDraw,ImageFont
from native_geometry_v2 import NativeGeometryIndex,corrected_entity_inventory,SCHEMA

OBJECTS=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']
def load(p):return json.loads(Path(p).read_text())
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def val(g,p):
    x=g[p]
    if isinstance(x,h5py.Dataset):return x[()]
    if 'value' in x:return x['value'][()]
    return json.loads(x.attrs['json'])
def rot(q):
    q=np.asarray(q);w,x,y,z=np.moveaxis(q,-1,0);s=2/np.sum(q*q,axis=-1)
    return np.stack([1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w),s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w),s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)],axis=-1).reshape(q.shape[:-1]+(3,3))
def bounds(m,gp,gr,ids):
    vertices=[]
    for i in ids:
        typ=int(m.geom_type[i]);sz=m.geom_size[i]
        if typ==int(mujoco.mjtGeom.mjGEOM_BOX):
            v=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]])*sz
        elif typ==int(mujoco.mjtGeom.mjGEOM_MESH):
            mid=int(m.geom_dataid[i]);start=int(m.mesh_vertadr[mid]);v=m.mesh_vert[start:start+int(m.mesh_vertnum[mid])]
        else:raise ValueError('Unsupported object primitive in targeted bounds')
        vertices.extend(v@gr[i].T+gp[i])
    v=np.asarray(vertices);return v.min(axis=0),v.max(axis=0)

def main(project,out):
    project=Path(project);out=Path(out);parent=project/'reports/fall_review_20261016';runs=load(parent/'runs.json')['runs']
    assert len(runs)==50
    (out/'fixtures').mkdir(exist_ok=True);(out/'examples').mkdir(exist_ok=True)
    ref=Path(runs[0]['source_episode']);m=mujoco.MjModel.from_xml_path(str(ref/'simulator.xml'));xmlhash=sha(ref/'simulator.xml')
    bn=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,i) for i in range(m.nbody)]
    jn=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,i) for i in range(m.njnt)]
    with h5py.File(ref/'trajectory.h5') as h:
        s=h['frames/000000/simulator'];bp=val(s,'body_xpos');br=rot(val(s,'body_xquat'));gp=val(s,'geom_xpos');gr=val(s,'geom_xmat').reshape(-1,3,3)
        runtime_local_r=np.transpose(br[m.geom_bodyid],(0,2,1))@gr
        runtime_local_p=np.einsum('gji,gj->gi',br[m.geom_bodyid],gp-bp[m.geom_bodyid])
    geoms=[];rounding=[];geom_xml={g.get('name'):g for g in ET.parse(ref/'simulator.xml').findall('.//geom') if g.get('name')}
    for i in range(m.ngeom):
        bid=int(m.geom_bodyid[i]);ancestry=[];j=bid
        while j:ancestry.append(bn[j]);j=int(m.body_parentid[j])
        ancestry.append('world');name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i);Rxml=rot(m.geom_quat[i]);delta=Rxml-runtime_local_r[i]
        bound=float(np.linalg.norm(delta,ord='fro')*np.linalg.norm(m.geom_size[i])) if int(m.geom_type[i])==int(mujoco.mjtGeom.mjGEOM_BOX) else None
        geoms.append({'native_geom_id':i,'name':name,'owner_body_id':bid,'owner_body':bn[bid],'body_ancestry':ancestry,'type':mujoco.mjtGeom(int(m.geom_type[i])).name,'size':m.geom_size[i].tolist(),'collision_capable':bool(m.geom_contype[i] or m.geom_conaffinity[i]),'local_position_xml':m.geom_pos[i].tolist(),'local_position_derived_from_recorded_snapshot':runtime_local_p[i].tolist(),'local_rotation_xml':Rxml.tolist(),'local_rotation_derived_from_recorded_snapshot':runtime_local_r[i].tolist(),'xml_runtime_rotation_max_component_difference':float(np.max(np.abs(delta))),'box_corner_displacement_bound_due_to_rotation_serialization_m':bound,'runtime_transform_source':{'run_id':runs[0]['run_id'],'frame':'000000','body_xquat':'frames/000000/simulator/body_xquat/value','geom_xmat':'frames/000000/simulator/geom_xmat/value'}})
        if name in geom_xml and int(m.geom_type[i])==int(mujoco.mjtGeom.mjGEOM_BOX) and 'quat' in geom_xml[name].attrib:
            q=np.empty(4);mujoco.mju_mat2Quat(q,np.ascontiguousarray(runtime_local_r[i]).ravel());sq=np.fromstring(geom_xml[name].get('quat'),sep=' ')
            if q@sq<0:q=-q
            rounded=np.array([float(format(x,'.6g')) if abs(x)>1e-12 else 0. for x in q])
            rounding.append({'id':i,'name':name,'xml_quaternion_tokens':geom_xml[name].get('quat'),'runtime_relative_quaternion':q.tolist(),'six_significant_digit_rounding_matches_xml':bool(np.array_equal(rounded,sq)),'rotation_residual':float(np.max(np.abs(delta))),'corner_displacement_bound_m':bound})
    mapping={'schema_version':SCHEMA,'source_xml_sha256':xmlhash,'native_geom_count':m.ngeom,'validated_run_ids':[r['run_id'] for r in runs],'body_names':bn,'geometries':geoms,'legacy_geom_names_is_not_native_id_order':True,'validation_scope':'Prior all-frame position mapping audit plus this targeted settling/early-policy and selected diagnostic-window transform validation. Recorded transforms are retained; derived local transforms are separate metadata.','numerical_consistency_policy':'512 * binary64 epsilon * max(1, coordinate magnitude) for matrix/vector recomposition; rotation absolute 512*epsilon. Conservative algebraic floating-point operation allowance, not a fall/contact/support tolerance.'}
    save(out/'corrected_native_geometry_v2.json',mapping);save(out/'rotation_serialization_evidence.json',rounding)
    (out/'fixtures/legacy_simulator_index.json').write_bytes((ref/'simulator_index.json').read_bytes())
    originals=[r for r in load(project/'data/runs.json')['records'] if r['task_id']==runs[0]['task_id']]
    save(out/'corrected_entity_inventory_v2.json',corrected_entity_inventory(originals,NativeGeometryIndex(mapping)))
    bid={o:bn.index(o+'_main') for o in OBJECTS};ids={o:[g['native_geom_id'] for g in geoms if g['owner_body']==o+'_main' and g['collision_capable']] for o in OBJECTS}
    constraints={'model_equality_count':m.neq,'integrator':mujoco.mjtIntegrator(int(m.opt.integrator)).name,'physics_timestep':m.opt.timestep,'gravity_world':m.opt.gravity.tolist(),'objects':{}}
    for o,b in bid.items():
        j=int(m.body_jntadr[b]);d=int(m.jnt_dofadr[j]);constraints['objects'][o]={'body_id':b,'joint_name':jn[j],'joint_type':mujoco.mjtJoint(int(m.jnt_type[j])).name,'joint_qpos_address':int(m.jnt_qposadr[j]),'joint_dof_address':d,'joint_limited':bool(m.jnt_limited[j]),'mocap_id':int(m.body_mocapid[b]),'gravity_compensation':float(m.body_gravcomp[b]),'mass':float(m.body_mass[b]),'damping':m.dof_damping[d:d+6].tolist(),'joint_actuators':[int(a) for a in range(m.nu) if int(m.actuator_trnid[a,0])==j],'collision_geom_ids':ids[o]}
    save(out/'constraints_and_identities.json',constraints)
    rows=[];runfindings=[];static_path=out/'static_reconstructions.jsonl';maxcomposep=0.;maxcomposer=0.;maxundop=0.;maxundoq=0.;maxeuler=0.;maxrawprev=0.;rawprev_contactfree=[]
    selection={0:[0,1,5,10,11,13,16,20],2:[0,1,5,8,10,11,12,20],1:[10,20,40,80],14:[270,276,280,283,286,290,300]};example_manifest=[]
    with static_path.open('w') as sf:
      for r in runs:
        ep=Path(r['source_episode']);legacy=load(ep/'simulator_index.json');assert sha(ep/'simulator.xml')==xmlhash and legacy['body_names']==bn and legacy['joint_names']==jn
        with h5py.File(ep/'trajectory.h5') as h:
          selected=set(range(31));exampleframes=selection.get(r['episode'],[])
          if r['episode']==14:selected.update(range(270,min(311,len(h['frames']))))
          selected.update(exampleframes);selected=sorted(f for f in selected if f<len(h['frames']))
          init=val(h,'benchmark_initial_state');flat=val(h['frames/000000/simulator'],'flattened');initial_state_error=float(np.max(np.abs(init-flat)))
          observations={o:[] for o in OBJECTS};laststatic=None
          for fi in selected:
            f=h[f'frames/{fi:06d}'];s=f['simulator'];t=float(val(s,'time'));q=val(s,'qpos');v=val(s,'qvel');a=val(s,'qacc');bp=val(s,'body_xpos');bq=val(s,'body_xquat');br=rot(bq);gp=val(s,'geom_xpos');gr=val(s,'geom_xmat').reshape(-1,3,3);contacts=val(s,'contacts')
            composedp=bp[m.geom_bodyid]+np.einsum('gij,gj->gi',br[m.geom_bodyid],runtime_local_p);composedr=br[m.geom_bodyid]@runtime_local_r
            perr=float(np.max(np.abs(composedp-gp)));rerr=float(np.max(np.abs(composedr-gr)));scale=max(1.,float(np.max(np.abs(bp))),float(np.max(np.abs(gp))));ptol=512*np.finfo(float).eps*scale;rtol=512*np.finfo(float).eps
            assert perr<=ptol and rerr<=rtol,(r['run_id'],fi,perr,rerr)
            maxcomposep=max(maxcomposep,perr);maxcomposer=max(maxcomposer,rerr)
            preq=q.copy()
            if fi>0:mujoco.mj_integratePos(m,preq,v,-m.opt.timestep)
            d=mujoco.MjData(m);d.qpos[:]=preq;mujoco.mj_kinematics(m,d)
            static={'run_id':r['run_id'],'frame':f'{fi:06d}','recorded_sim_time':t,'method':'STATIC undo one Euler configuration increment with recorded endpoint qvel; mj_integratePos(-dt), then mj_kinematics only. No mj_step, collision solve, rendering or replacement trajectory. Initial frame uses original qpos.','hypothesized_derived_pose_time':t-m.opt.timestep if fi else t,'reconstructed_qpos_separate_from_recording':preq.tolist(),'protected_static_positions':{o:d.xpos[b].tolist() for o,b in bid.items()},'not_a_replacement_recording':True};sf.write(json.dumps(static)+'\n')
            for o,b in bid.items():
              j=int(m.body_jntadr[b]);qa=int(m.jnt_qposadr[j]);va=int(m.jnt_dofadr[j]);raw=val(f,'raw_observation/'+o+'_pos');lo,hi=bounds(m,gp,gr,ids[o]);oc=[]
              for c in contacts:
                x,y=int(c['geom1']),int(c['geom2'])
                if x in ids[o] or y in ids[o]:
                    other=y if x in ids[o] else x;oc.append({'self_geom_id':x if x in ids[o] else y,'other_geom_id':other,'other_body':bn[int(m.geom_bodyid[other])],'dist':float(c['dist']),'world_position':c['pos']})
              undo=float(np.max(np.abs(d.xpos[b]-bp[b])));qerr=float(min(np.max(np.abs(d.xquat[b]-bq[b])),np.max(np.abs(d.xquat[b]+bq[b]))));maxundop=max(maxundop,undo);maxundoq=max(maxundoq,qerr)
              euler=float(np.max(np.abs(q[qa:qa+3]-bp[b]-(m.opt.timestep*v[va:va+3] if fi else 0))));maxeuler=max(maxeuler,euler)
              predict_raw=q[qa:qa+3]-2*m.opt.timestep*v[va:va+3]+m.opt.timestep**2*a[va:va+3] if fi else q[qa:qa+3]
              rawerr=float(np.linalg.norm(raw-predict_raw));maxrawprev=max(maxrawprev,rawerr)
              if fi>0 and not oc:rawprev_contactfree.append(rawerr)
              row={'run_id':r['run_id'],'episode':r['episode'],'object':o,'frame':fi,'stage':str(f.attrs['stage']),'control_step':int(f.attrs['control_step']),'sim_time':t,'body_x':float(bp[b,0]),'body_y':float(bp[b,1]),'body_z':float(bp[b,2]),'qvel_world_z':float(v[va+2]),'qacc_world_z':float(a[va+2]),'collision_min_z':float(lo[2]),'collision_max_z':float(hi[2]),'collision_bounds_min':lo.tolist(),'collision_bounds_max':hi.tolist(),'contact_records':oc,'static_undo_body_position_component_residual':undo,'static_undo_quaternion_component_residual':qerr,'raw_two_substep_Euler_hypothesis_residual_m':rawerr,'qpos_body_Euler_translation_identity_residual_m':euler,'recorded_raw_body_discrepancy_m':float(np.linalg.norm(raw-bp[b]))}
              rows.append(row);observations[o].append(row)
          runfindings.append({'run_id':r['run_id'],'episode':r['episode'],'targeted_frames':selected,'saved_selected_initial_state_vs_initial_flattened_max_abs_difference':initial_state_error,'source_initial_state_archive_hash_matches_metadata':sha(ep.parent/'benchmark_initial_states.init')==load(ep/'metadata.json')['initial_states_sha256'],'objects':{o:{'initial_contacts':observations[o][0]['contact_records'],'first_settling_endpoint_vertical_velocity':observations[o][1]['qvel_world_z'],'prepolicy':next(x for x in observations[o] if x['frame']==10),'first_later_contact_after_prepolicy':next(({'frame':x['frame'],'time':x['sim_time'],'owners':sorted({c['other_body'] for c in x['contact_records']})} for x in observations[o] if x['frame']>10 and x['contact_records']),None)} for o in OBJECTS}})
          if r['episode'] in selection:
            font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12);frames=selection[r['episode']];sheet=Image.new('RGB',(len(frames)*256,680),'white');draw=ImageDraw.Draw(sheet)
            draw.text((8,2),r['run_id'],fill='black',font=font)
            draw.text((8,18),'Existing recorded cameras; display rotated 180 degrees; interpretations provisional.',fill='black',font=font)
            entries=[]
            for column,fi in enumerate(frames):
              f=h[f'frames/{fi:06d}'];t=float(val(f,'simulator/time'));stage=str(f.attrs['stage']);step=int(f.attrs['control_step'])
              for ci,cam in enumerate(['agentview_image','robot0_eye_in_hand_image']):
                image=Image.fromarray(val(f,'raw_observation/'+cam)[::-1,::-1].copy());sheet.paste(image,(column*256,82+ci*305));draw.text((column*256+3,39+ci*305),f'f{fi:06d} t={t:.3f}s\n{stage} step={step}\n{cam}',fill='black',font=font)
              entries.append({'run_id':r['run_id'],'frame':f'{fi:06d}','stage':stage,'control_step':step,'simulator_time':t,'image_paths':[f'frames/{fi:06d}/raw_observation/{cam}/value' for cam in ['agentview_image','robot0_eye_in_hand_image']],'trajectory':str(ep/'trajectory.h5'),'host_snapshot_utc':str(f.attrs['utc']),'camera_capture_time_not_independently_recorded':True})
            filename=f'examples/episode_{r["episode"]:03d}_sheet.png';sheet.save(out/filename);example_manifest.append({'example_id':f'recorded-example-{r["episode"]:03d}','sheet':filename,'split':'development','frames':entries,'human_labels_entered':False})
    save(out/'targeted_measurements.json',{'purpose':'Specific initial-support, settling, ID and timing correction; not repeated availability audit or a fall verdict','records':rows})
    save(out/'settling_findings_by_run.json',runfindings);save(out/'example_manifest.json',example_manifest)
    with (out/'targeted_measurements.csv').open('w') as f:
        fields=[k for k in rows[0] if k not in ['contact_records','collision_bounds_min','collision_bounds_max']];w=csv.DictWriter(f,fieldnames=fields+['contact_owner_bodies']);w.writeheader()
        for row in rows:w.writerow({**{k:row[k] for k in fields},'contact_owner_bodies':'|'.join(sorted({c['other_body'] for c in row['contact_records']}))})
    save(out/'targeted_validation.json',{'runs':50,'frames_examined':len(rows)//5,'object_frame_records':len(rows),'all_initial_states_match_saved_selection':all(r['saved_selected_initial_state_vs_initial_flattened_max_abs_difference']==0 for r in runfindings),'all_initial_state_archive_hashes_match':all(r['source_initial_state_archive_hash_matches_metadata'] for r in runfindings),'max_runtime_local_pose_position_recomposition_error_m':maxcomposep,'max_runtime_local_pose_rotation_recomposition_error':maxcomposer,'max_static_undo_protected_body_position_component_error_m':maxundop,'max_static_undo_protected_quaternion_component_error':maxundoq,'max_Euler_qpos_body_translation_identity_residual_m':maxeuler,'max_raw_two_substep_hypothesis_residual_all_m':maxrawprev,'max_raw_two_substep_hypothesis_residual_no_snapshot_contacts_m':max(rawprev_contactfree),'raw_sample_phase_is_hypothesis_not_producer_timestamp':True,'max_xml_rotation_box_corner_bound_m':max(g['box_corner_displacement_bound_due_to_rotation_serialization_m'] or 0 for g in geoms),'six_digit_quaternion_checks':len(rounding),'six_digit_quaternion_matches':sum(x['six_significant_digit_rounding_matches_xml'] for x in rounding),'no_physics_steps':True,'no_event_or_safety_verdicts':True})
    save(out/'source_environment.json',{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'h5py':h5py.__version__,'mujoco':mujoco.__version__,'script_sha256':sha(__file__)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);a=p.parse_args();main(a.project,a.output)
