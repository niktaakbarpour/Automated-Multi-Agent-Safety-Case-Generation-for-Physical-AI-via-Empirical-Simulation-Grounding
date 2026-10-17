"""Summarize audit evidence; no event detection or safety classification."""
import collections, csv, hashlib, json
from pathlib import Path
import h5py, mujoco, numpy as np
from audit_recordings import OBJECTS, load, save, sha, value

def main(out,project):
    out=Path(out);project=Path(project);runs=load(out/'runs.json')['runs'];assert len(runs)==50 and load(out/'status.json')['stage']=='complete'
    m=mujoco.MjModel.from_xml_path(runs[0]['files_inspected']['simulator.xml']['path'])
    evidence=[];initial_rows=[]
    for r in runs:
      with h5py.File(r['trajectory']['path'],'r') as h:
        f=h['frames'][r['timing']['initial_support_frame']];s=f['simulator'];gp=value(s,'geom_xpos');gr=value(s,'geom_xmat').reshape(-1,3,3)
        surfaces=[]
        for i in r['geometry_mapping']['table_collision_geom_ids']:
            if int(m.geom_type[i])==int(mujoco.mjtGeom.mjGEOM_BOX):
                ext=np.abs(gr[i])@m.geom_size[i];p=gp[i]
                surfaces.append({'geom_id':i,'world_aabb_min':(p-ext).tolist(),'world_aabb_max':(p+ext).tolist(),'upper_world_z_face_candidate':float(p[2]+ext[2]),'qualification':'Geometric bound/face candidate only; not an approved support face or threshold.'})
        objs={}
        for o in OBJECTS:
            vs=[];collision_ids=[]
            for i in r['initial_support_evidence'][o]['object_geom_ids']:
                if not (m.geom_contype[i] or m.geom_conaffinity[i]):continue
                collision_ids.append(i);typ=int(m.geom_type[i]);size=m.geom_size[i]
                if typ==int(mujoco.mjtGeom.mjGEOM_BOX):
                    corners=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]])*size
                    vs.extend(corners@gr[i].T+gp[i])
                elif typ==int(mujoco.mjtGeom.mjGEOM_MESH):
                    mid=int(m.geom_dataid[i]);start=int(m.mesh_vertadr[mid]);count=int(m.mesh_vertnum[mid]);vs.extend(m.mesh_vert[start:start+count]@gr[i].T+gp[i])
                else:raise ValueError('Unsupported initial object collision primitive')
            arr=np.asarray(vs);bid=r['initial_support_evidence'][o]['body_id'];cs=r['initial_support_evidence'][o]['table_contact_records']
            obj={'body_id':bid,'root_body_position_world_m':r['initial_support_evidence'][o]['body_position_world'],'body_inertial_position_local_m':m.body_ipos[bid].tolist(),'collision_geom_ids':collision_ids,'collision_world_aabb_min':arr.min(axis=0).tolist(),'collision_world_aabb_max':arr.max(axis=0).tolist(),'initial_table_contact_count':len(cs),'initial_contact_geom_pairs':sorted({(int(c['geom1']),int(c['geom2'])) for c in cs}),'support_status':'pending_independent_geometric_and_contact_review','no_contact_is_not_verified_non_support':True}
            objs[o]=obj;initial_rows.append({'run_id':r['run_id'],'episode':r['episode'],'object':o,'initial_frame':r['timing']['initial_support_frame'],'sim_time':r['timing']['initial_support_sim_time'],'table_contact_count':len(cs),'collision_min_z_world_m':float(arr[:,2].min()),'collision_max_z_world_m':float(arr[:,2].max()),'support_status':obj['support_status']})
        evidence.append({'run_id':r['run_id'],'frame':r['timing']['initial_support_frame'],'gravity_world':m.opt.gravity.tolist(),'table_collision_bounds':surfaces,'floor_geoms':[{'geom_id':i,'type':mujoco.mjtGeom(int(m.geom_type[i])).name,'position_world':gp[i].tolist(),'rotation_world':gr[i].tolist(),'size':m.geom_size[i].tolist()} for i in range(m.ngeom) if mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i)=='floor'],'objects':objs})
    save(out/'initial_geometry_evidence.json',{'no_support_or_fall_verdicts':True,'runs':evidence})
    with (out/'initial_support_inventory.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(initial_rows[0]));w.writeheader();w.writerows(initial_rows)
    summary={'task_id':runs[0]['task_id'],'runs':len(runs),'seed_range':[min(r['seed'] for r in runs),max(r['seed'] for r in runs)],'frames':sum(r['timing']['frame_count'] for r in runs),'control_actions':sum(r['timing']['control_action_count'] for r in runs),'control_action_count_range':[min(r['timing']['control_action_count'] for r in runs),max(r['timing']['control_action_count'] for r in runs)],'stages':dict(sum((collections.Counter(r['timing']['stages']) for r in runs),collections.Counter())),'objects':{},'timing_issues':[(r['run_id'],r['timing']['issues']) for r in runs if r['timing']['issues']],'transition_alignment_issues':[(r['run_id'],r['timing']['transition_alignment_issues']) for r in runs if r['timing']['transition_alignment_issues']],'contact_issues':[(r['run_id'],r['contacts']['issues']) for r in runs if r['contacts']['issues']],'contact_records':sum(r['contacts']['record_count'] for r in runs),'max_geom_position_component_residual_m':max(r['geometry_mapping']['max_recorded_vs_body_composed_geom_position_component_error_m'] for r in runs),'max_geom_rotation_component_residual':max(r['geometry_mapping']['max_recorded_vs_body_composed_geom_rotation_component_error'] for r in runs),'max_table_pose_change':max(r['geometry_mapping']['max_recorded_table_geom_pose_change'] for r in runs),'body_joint_mapping_matches_all_runs':all(r['geometry_mapping']['body_names_match_compiler_ids'] and r['geometry_mapping']['joint_names_match_compiler_ids'] and r['geometry_mapping']['joint_qpos_addresses_match'] for r in runs),'unique_xml_hashes':sorted({r['geometry_mapping']['source_xml_sha256'] for r in runs}),'model_assets_verified':all(r['asset_validation']['missing']==0 and r['asset_validation']['hash_mismatches']==0 for r in runs),'max_sim_cadence_numerical_error_s':max(r['timing']['max_frame_sim_dt_error_from_control_period'] for r in runs),'per_run_termination_sim_time_range_s':[min(r['timing']['simulator_time_range'][1] for r in runs),max(r['timing']['simulator_time_range'][1] for r in runs)],'max_wall_snapshot_gap_s':max(r['timing']['frame_wall_dt_max_seconds'] for r in runs),'full_file_hashes_recomputed':False,'safety_verdicts_assigned':False}
    for o in OBJECTS:
        summary['objects'][o]={'position_counts':dict(sum((collections.Counter(r['objects'][o]['position']) for r in runs),collections.Counter())),'orientation_counts':dict(sum((collections.Counter(r['objects'][o]['orientation']) for r in runs),collections.Counter())),'runs_with_initial_table_contacts':sum(bool(r['initial_support_evidence'][o]['table_contact_records']) for r in runs),'episodes_without_initial_table_contacts':[r['episode'] for r in runs if not r['initial_support_evidence'][o]['table_contact_records']],'max_raw_body_distance_m':max(r['objects'][o]['max_raw_body_distance_m'] for r in runs),'max_qpos_body_position_distance_m':max(r['objects'][o]['max_qpos_body_position_distance_m'] for r in runs),'max_raw_vs_body_quaternion_component_difference':max(r['objects'][o]['max_quaternion_component_difference'] for r in runs)}
    save(out/'summary.json',summary)
    before=load(out/'pilot_preservation_before.json');after={}
    for name,files in before.items():
        root=project/'data/requirement_pilots'/name;after[name]={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()};assert after[name]==files,name
    save(out/'pilot_preservation_after.json',{'all_unchanged':True,'file_counts':{k:len(v) for k,v in after.items()},'sha256':after})
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);a=p.parse_args();main(a.output,a.project)
