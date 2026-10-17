"""Read-only full-sequence measurement audit. No event checker or safety verdicts."""
import argparse, collections, csv, hashlib, json, platform, sys, time
from pathlib import Path
import h5py
import mujoco
import numpy as np

TASK = '2448c758145ae5ad500f'
OBJECTS = ['cream_cheese_1', 'ketchup_1', 'orange_juice_1', 'milk_1', 'butter_1']

def load(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def save(p, d): Path(p).write_text(json.dumps(d, indent=2, allow_nan=False)+'\n')
def value(g, p):
    v=g[p]
    if isinstance(v,h5py.Dataset):return v[()]
    if 'value' in v:return v['value'][()]
    if 'json' in v.attrs:return json.loads(v.attrs['json'])
    raise ValueError('Unsupported recorded value '+v.name)
def rotation(q):
    q=np.asarray(q); w,x,y,z=np.moveaxis(q,-1,0); s=2/np.sum(q*q,axis=-1)
    return np.stack([1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w),s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w),s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)],axis=-1).reshape(q.shape[:-1]+(3,3))
def descendants(model,bid):
    ids=[]
    for i in range(model.nbody):
        j=i
        while j and j!=bid:j=int(model.body_parentid[j])
        if j==bid:ids.append(i)
    return ids
def array_status(g,path,shape=None):
    if path+'/value' not in g:return 'absent',None
    a=np.asarray(value(g,path))
    if shape is not None and a.shape!=shape:return 'wrong_shape',a
    if not np.isfinite(a).all():return 'nonfinite',a
    return 'finite',a

def main(project,out):
    project=Path(project);out=Path(out);out.mkdir(exist_ok=True)
    source=Path(load(project/'config/project.json')['source_results']).resolve()
    runs=[r for r in load(project/'data/runs.json')['records'] if r['task_id']==TASK]
    assert len(runs)==50
    task=next(t for t in load(project/'data/tasks.json')['records'] if t['task_id']==TASK)
    assert set(task['run_ids'])=={r['run_id'] for r in runs}
    results=[];models={};asset_checks={};model_records={};started=time.time()
    pos_fields=['run_id','frame','stage','control_step','sim_time','object','raw_status','body_status','quat_status','raw_x','raw_y','raw_z','body_x','body_y','body_z','raw_body_distance','object_table_contact_count']
    time_fields=['run_id','frame','stage','control_step','sim_time','utc','monotonic_ns','wall_time_ns']
    with (out/'position_coverage.csv').open('w') as fp,(out/'timeline.csv').open('w') as ft:
      pw=csv.DictWriter(fp,fieldnames=pos_fields);pw.writeheader()
      tw=csv.DictWriter(ft,fieldnames=time_fields);tw.writeheader()
      for number,run in enumerate(runs):
        ep=source/Path(run['evidence']['trajectory']['source_relative_path']).parent
        metadata=load(ep/'metadata.json');sem=load(ep/'semantic_initial_conditions.json');idx=load(ep/'simulator_index.json');ev=load(ep/'evaluation.json');integrity=load(ep/'integrity_manifest.json')
        assert metadata['task_configuration_id']==TASK and metadata['global_episode_id']==run['run_id']
        assert sem['global_episode_id']==run['run_id']
        files={n:{'path':str(ep/n),'bytes':(ep/n).stat().st_size,'sha256':sha(ep/n)} for n in ['metadata.json','semantic_initial_conditions.json','simulator_index.json','simulator.xml','simulator_asset_manifest.json','evaluator_version.json','completion.json','integrity_manifest.json']}
        for n,f in files.items():
            if n in integrity['files']:assert f['sha256']==integrity['files'][n]['sha256'],str(ep/n)
        xhash=files['simulator.xml']['sha256']
        if xhash not in models:models[xhash]=mujoco.MjModel.from_xml_path(str(ep/'simulator.xml'))
        m=models[xhash];bn=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,i) for i in range(m.nbody)]
        jn=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,i) for i in range(m.njnt)]
        gn=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) for i in range(m.ngeom)]
        bid={o:bn.index(sem['phases']['before_first_action']['object_initial_poses'][o]['root_body']) for o in OBJECTS}
        table_bids=descendants(m,bn.index('living_room_table'))
        table_geoms={i for i in range(m.ngeom) if int(m.geom_bodyid[i]) in table_bids and bool(m.geom_contype[i] or m.geom_conaffinity[i])}
        object_geoms={o:{i for i in range(m.ngeom) if int(m.geom_bodyid[i]) in descendants(m,bid[o])} for o in OBJECTS}
        if xhash not in model_records:
            rec={'source_xml_sha256':xhash,'body_names':bn,'geom_count':m.ngeom,'saved_geom_name_list_length':len(idx['geom_names']),'gravity':m.opt.gravity.tolist(),'physics_timestep_seconds':m.opt.timestep,'geometries':[]}
            for i in range(m.ngeom):
                rec['geometries'].append({'id':i,'name':gn[i],'owner_body_id':int(m.geom_bodyid[i]),'owner_body':bn[int(m.geom_bodyid[i])],'type':mujoco.mjtGeom(int(m.geom_type[i])).name,'size':m.geom_size[i].tolist(),'local_position':m.geom_pos[i].tolist(),'local_quaternion_wxyz':m.geom_quat[i].tolist(),'contype':int(m.geom_contype[i]),'conaffinity':int(m.geom_conaffinity[i]),'mesh_id':int(m.geom_dataid[i]) if int(m.geom_type[i])==int(mujoco.mjtGeom.mjGEOM_MESH) else None})
            model_records[xhash]=rec
        assets=load(ep/'simulator_asset_manifest.json')['assets'];asset_results=[]
        for a in assets:
            key=(a['path'],a.get('sha256'))
            if key not in asset_checks:
                ap=Path(a['path']);asset_checks[key]={'path':str(ap),'exists':ap.is_file(),'sha256_matches':sha(ap)==a['sha256'] if ap.is_file() and a.get('sha256') else None}
            asset_results.append(asset_checks[key])
        issues=[];obj={o:{'position':collections.Counter(),'orientation':collections.Counter(),'bad_frames':[],'max_raw_body_distance_m':0.,'raw_body_exact_equal_frames':0,'max_quaternion_component_difference':0.,'max_qpos_body_position_distance_m':0.} for o in OBJECTS}
        field_counts=collections.Counter();stages=collections.Counter();times=[];monos=[];steps=[];frame_ids=[];control=[];initial={};numeric_hash=hashlib.sha256();max_geom_p=0.;max_geom_r=0.;contacts_total=0;contact_bad=[];table_pose_first=None;table_pose_max_change=0.;image_presence=collections.Counter()
        hp=ep/'trajectory.h5';stat_before=hp.stat()
        with h5py.File(hp,'r') as h:
          assert h.attrs['global_episode_id']==run['run_id'] and h.attrs['task_configuration_id']==TASK
          for fn in sorted(h['frames']):
            f=h['frames'][fn];s=f['simulator'];stage=str(f.attrs['stage']);step=int(f.attrs['control_step']);t=float(value(s,'time'));times.append(t);monos.append(int(f.attrs['monotonic_ns']));steps.append(step);frame_ids.append(int(fn));stages[stage]+=1
            tw.writerow({'run_id':run['run_id'],'frame':fn,'stage':stage,'control_step':step,'sim_time':t,'utc':f.attrs['utc'],'monotonic_ns':f.attrs['monotonic_ns'],'wall_time_ns':f.attrs['wall_time_ns']})
            state={}
            for field in ['qpos','qvel','qacc','act','ctrl','flattened','body_xpos','body_xquat','geom_xpos','geom_xmat','site_xpos','site_xmat','ncon','cvel','cfrc_ext','actuator_force','sensordata']:
                status,a=array_status(s,field);field_counts[field+':'+status]+=1
                if a is not None:state[field]=a;numeric_hash.update((fn+'/'+field).encode());numeric_hash.update(a.tobytes())
            bp=state.get('body_xpos');bq=state.get('body_xquat');gp=state.get('geom_xpos');gr=state.get('geom_xmat')
            if bp is not None and bq is not None and gp is not None and gr is not None:
                br=rotation(bq);expectp=bp[m.geom_bodyid]+np.einsum('gij,gj->gi',br[m.geom_bodyid],m.geom_pos);expectr=br[m.geom_bodyid]@rotation(m.geom_quat)
                max_geom_p=max(max_geom_p,float(np.max(np.abs(gp-expectp))));max_geom_r=max(max_geom_r,float(np.max(np.abs(gr.reshape(-1,3,3)-expectr))))
                tp=np.concatenate([gp[sorted(table_geoms)].ravel(),gr[sorted(table_geoms)].ravel()])
                if table_pose_first is None:table_pose_first=tp.copy()
                table_pose_max_change=max(table_pose_max_change,float(np.max(np.abs(tp-table_pose_first))))
            try:
                cg=s['contacts'];cs=json.loads(cg.attrs['json']) if 'json' in cg.attrs else value(s,'contacts').tolist()
                assert isinstance(cs,list)
                contacts_total+=len(cs)
                if len(cs)!=int(state['ncon']):contact_bad.append([fn,'ncon_count_mismatch'])
                for c in cs:
                    if not all(0<=int(c[k])<m.ngeom for k in ['geom1','geom2']):contact_bad.append([fn,'geom_id_out_of_range'])
                    if not np.isfinite([c['dist'],*c['pos']]).all():contact_bad.append([fn,'nonfinite_contact'])
                numeric_hash.update(json.dumps(cs,sort_keys=True).encode());field_counts['contacts:read']+=1
            except Exception as e:cs=[];contact_bad.append([fn,type(e).__name__+':'+str(e)])
            if stage in ['control','terminal']:control.append((fn,step,t))
            for cam in ['agentview_image','robot0_eye_in_hand_image']:
                if 'raw_observation/'+cam+'/value' in f:
                    a=f['raw_observation/'+cam+'/value'];image_presence[cam+':'+str(a.shape)+':'+str(a.dtype)]+=1
            for o in OBJECTS:
                ps,p=array_status(f,'raw_observation/'+o+'_pos',(3,));qs,q=array_status(f,'raw_observation/'+o+'_quat',(4,));obj[o]['position'][ps]+=1;obj[o]['orientation'][qs]+=1
                if ps!='finite' or qs!='finite':obj[o]['bad_frames'].append({'frame':fn,'position':ps,'orientation':qs})
                b=bp[bid[o]] if bp is not None else None;bs='finite' if b is not None and np.isfinite(b).all() else 'absent_or_nonfinite'
                dist=None
                if ps=='finite' and bs=='finite':
                    dist=float(np.linalg.norm(p-b));obj[o]['max_raw_body_distance_m']=max(obj[o]['max_raw_body_distance_m'],dist);obj[o]['raw_body_exact_equal_frames']+=int(np.array_equal(p,b))
                if qs=='finite' and bq is not None:
                    qb=bq[bid[o]][[1,2,3,0]];err=min(np.max(np.abs(q-qb)),np.max(np.abs(q+qb)));obj[o]['max_quaternion_component_difference']=max(obj[o]['max_quaternion_component_difference'],float(err))
                if 'qpos' in state and b is not None:
                    j=int(m.body_jntadr[bid[o]]);adr=int(m.jnt_qposadr[j]);delta=float(np.linalg.norm(state['qpos'][adr:adr+3]-b));obj[o]['max_qpos_body_position_distance_m']=max(obj[o]['max_qpos_body_position_distance_m'],delta)
                oc=[c for c in cs if (int(c['geom1']) in object_geoms[o] and int(c['geom2']) in table_geoms) or (int(c['geom2']) in object_geoms[o] and int(c['geom1']) in table_geoms)]
                row={'run_id':run['run_id'],'frame':fn,'stage':stage,'control_step':step,'sim_time':t,'object':o,'raw_status':ps,'body_status':bs,'quat_status':qs,'raw_body_distance':dist,'object_table_contact_count':len(oc)}
                if ps=='finite':row.update(zip(['raw_x','raw_y','raw_z'],p.tolist()))
                if bs=='finite':row.update(zip(['body_x','body_y','body_z'],b.tolist()))
                pw.writerow(row)
                if p is not None:numeric_hash.update((fn+'/'+o+'_pos').encode());numeric_hash.update(p.tobytes())
                if q is not None:numeric_hash.update(q.tobytes())
                if stage=='settling':
                    initial[o]={'frame':fn,'sim_time':t,'body_id':bid[o],'body_position_world':b.tolist() if b is not None else None,'semantic_before_first_action_matches_body_exactly':bool(np.array_equal(b,sem['phases']['before_first_action']['object_initial_poses'][o]['initial_position_world_m'])),'object_geom_ids':sorted(object_geoms[o]),'table_contact_records':oc,'support_conclusion':'not_adjudicated_contact_is_not_proof_of_support'}
          transition_issues=[];action_deltas=[];trtimes=[];termination=[]
          for n in sorted(h['transitions']):
            tr=h['transitions'][n];i=int(value(tr,'step'));tt=float(value(tr,'simulator_time'));trtimes.append(tt)
            if int(n)!=i:transition_issues.append([n,'step_label_mismatch'])
            if i>=len(control) or control[i][1]!=i or control[i][2]!=tt:transition_issues.append([n,'after_action_frame_alignment_mismatch'])
            if n not in h['policy_steps']:transition_issues.append([n,'missing_policy_step'])
            else:action_deltas.append(float(np.max(np.abs(value(tr,'executed_action')-value(h['policy_steps'][n],'executed_action')))))
            if bool(value(tr,'terminated')) or bool(value(tr,'truncated')):termination.append({'step':i,'terminated':bool(value(tr,'terminated')),'truncated':bool(value(tr,'truncated')),'sim_time':tt,'utc':str(value(tr,'utc'))})
          controlsteps=[x[1] for x in control]
          if frame_ids!=list(range(len(frame_ids))):issues.append('noncontiguous_frame_ids')
          if controlsteps!=list(range(len(controlsteps))):issues.append('noncontiguous_control_steps')
          if len(control)!=len(h['transitions']) or len(control)!=len(h['policy_steps']) or len(control)!=ev['steps']:issues.append('count_mismatch')
          if not all(np.diff(times)>0):issues.append('nonincreasing_simulator_times')
          if not all(np.diff(monos)>0):issues.append('nonincreasing_monotonic_times')
          if len(termination)!=1 or termination[0]['step']!=len(control)-1:issues.append('termination_marker_not_unique_last_step')
          terminal_stage=str(h['frames'][f'{frame_ids[-1]:06d}'].attrs['stage'])
          if terminal_stage!='terminal':issues.append('last_frame_not_terminal')
          for o in OBJECTS:initial[o]['relation_to_first_action']='last recorded settling frame immediately before first policy control action; settling excluded from proposed control-phase interval'
          timing={'frame_count':len(frame_ids),'stages':dict(stages),'control_action_count':len(control),'settling_action_count':len(h['settling_actions']),'frame_id_range':[frame_ids[0],frame_ids[-1]],'control_step_range':[controlsteps[0],controlsteps[-1]],'first_after_action_frame':control[0][0],'initial_support_frame':next(iter(initial.values()))['frame'],'initial_support_sim_time':next(iter(initial.values()))['sim_time'],'first_after_action_sim_time':control[0][2],'termination':termination,'last_stage':terminal_stage,'simulator_time_range':[times[0],times[-1]],'frame_sim_dt_min':float(np.min(np.diff(times))),'frame_sim_dt_max':float(np.max(np.diff(times))),'max_frame_sim_dt_error_from_control_period':float(np.max(np.abs(np.diff(times)-1/metadata['control_frequency_hz']))),'frame_wall_dt_max_seconds':float(np.max(np.diff(monos))/1e9),'per_sensor_capture_timestamps_present':False,'issues':issues,'transition_alignment_issues':transition_issues,'max_policy_transition_action_difference':max(action_deltas,default=None)}
        stat_after=hp.stat();assert (stat_before.st_size,stat_before.st_mtime_ns)==(stat_after.st_size,stat_after.st_mtime_ns)
        actual_lib_hashes=load(ep/'evaluator_version.json')['implementation_files_sha256']
        source_checks={}
        for path,expected in actual_lib_hashes.items():
            if path.endswith(('bddl_base_domain.py','env_wrapper.py','libero_living_room_tabletop_manipulation.py')):
                pp=Path(path);source_checks[path]={'exists':pp.is_file(),'matches_producer_sha256':sha(pp)==expected if pp.is_file() else None,'expected_sha256':expected}
        result={'run_id':run['run_id'],'task_id':TASK,'seed':metadata['seed'],'episode':metadata['episode'],'source_episode':str(ep),'files_inspected':files,'trajectory':{'path':str(hp),'bytes':stat_after.st_size,'producer_sha256':integrity['files']['trajectory.h5']['sha256'],'size_matches_producer':stat_after.st_size==integrity['files']['trajectory.h5']['bytes'],'full_file_sha256_recomputed':False,'selected_numeric_content_sha256':numeric_hash.hexdigest(),'mtime_unchanged_during_audit':True,'scope':'Every frame: protected positions/quaternions, simulator state arrays, contact records, timeline; every transition and executed policy action. Images checked for dataset presence/shape/dtype only; no image/video content adjudication.'},'timing':timing,'objects':obj,'initial_support_evidence':initial,'state_field_coverage':dict(field_counts),'image_dataset_presence':dict(image_presence),'contacts':{'record_count':contacts_total,'issues':contact_bad,'not_recorded':['per-contact normal/frame','per-contact force/impulse','persistent contact IDs','all intermediate physics-substep contacts']},'geometry_mapping':{'source_xml_sha256':xhash,'body_names_match_compiler_ids':idx['body_names']==bn,'joint_names_match_compiler_ids':idx['joint_names']==jn,'joint_qpos_addresses_match':idx['jnt_qposadr']==m.jnt_qposadr.tolist(),'saved_geom_names_length':len(idx['geom_names']),'compiled_geom_count':m.ngeom,'saved_geom_names_equal_id_order':idx['geom_names']==gn,'saved_geom_names_equal_last_name_to_id_wrapper_projection':idx['geom_names']==[gn[i] for i in sorted({n:i for i,n in enumerate(gn)}.values())],'table_collision_geom_ids':sorted(table_geoms),'max_recorded_vs_body_composed_geom_position_component_error_m':max_geom_p,'max_recorded_vs_body_composed_geom_rotation_component_error':max_geom_r,'max_recorded_table_geom_pose_change':table_pose_max_change,'support_binding_review_status':'pending'},'asset_validation':{'total_entries':len(assets),'missing':sum(not a['exists'] for a in asset_results),'hash_mismatches':sum(a['sha256_matches'] is False for a in asset_results)},'environment_source_checks':source_checks,'producer_recorder_source_hashes':{k:v for k,v in metadata['source_files_sha256'].items() if k in ['run_oft.py','recording_base.py','semantic_scene.py']}}
        results.append(result);save(out/'runs.json',{'task_id':TASK,'audit_kind':'measurement_availability_and_consistency_only_no_safety_verdicts','runs':results});save(out/'status.json',{'runs_done':len(results),'runs_total':len(runs),'frames_inspected':sum(r['timing']['frame_count'] for r in results),'elapsed_seconds':time.time()-started});print('AUDITED',number+1,run['run_id'],timing['frame_count'],flush=True)
    save(out/'compiled_geometry_mappings.json',model_records);save(out/'asset_checks.json',list(asset_checks.values()))
    save(out/'audit_environment.json',{'python':sys.version,'executable':sys.executable,'mujoco':mujoco.__version__,'h5py':h5py.__version__,'numpy':np.__version__,'platform':platform.platform(),'audit_script_sha256':sha(__file__),'no_simulation_steps':True,'no_requirement_verdicts':True,'no_model_generation':True})
    save(out/'status.json',{'stage':'complete','runs_done':len(results),'runs_total':len(runs),'frames_inspected':sum(r['timing']['frame_count'] for r in results),'elapsed_seconds':time.time()-started})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.project,a.output)
