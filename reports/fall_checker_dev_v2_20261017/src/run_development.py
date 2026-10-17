"""Read-only HDF5 adapter. Held-out paths rejected before opening any recording."""
import argparse, hashlib, json, itertools, csv, sys, re
from pathlib import Path
import numpy as np
import h5py
from checker import load_config, analyze, time_guard
from native_geometry_v2 import NativeGeometryIndex

def value(g,p):
    x=g[p]
    if isinstance(x,h5py.Dataset):return x[()]
    if 'value' in x:return x['value'][()]
    return json.loads(x.attrs['json'])

def corners(index,gid,gp,gr):
    g=index.by_id(gid)
    if g['type']!='mjGEOM_BOX':raise ValueError('Non-box protected/table geometry unsupported')
    xyz=np.array(list(itertools.product([-1,1],repeat=3)))*np.array(g['size'])
    return xyz@gr[gid].T+gp[gid]

def observations(index,entity,gp,gr,contacts,c):
    ids={i for i in entity['native_geom_ids'] if index.by_id(i)['collision_capable']}
    vertices=np.concatenate([corners(index,i,gp,gr) for i in ids]);lo=vertices.min(0);hi=vertices.max(0)
    patches={i:corners(index,i,gp,gr) for i in c['table_geom_ids']}
    top=max(float(v[:,2].max()) for v in patches.values())
    other=[];support=[];side=[];grip=[];indirect=[]
    for ct in contacts:
        index.contact_pair(ct) # validates *all* native contact IDs, even unrelated objects
        a,b=ct['geom1'],ct['geom2']
        if a not in ids and b not in ids:continue
        j=b if a in ids else a
        if j in ids:continue
        p=np.array(ct['pos']);d=float(ct['dist'])
        if not np.isfinite(p).all() or not np.isfinite(d):raise ValueError('Nonfinite contact')
        other.append(j)
        if j in c['gripper_left_ids']+c['gripper_right_ids']:grip.append(j)
        if j in patches:
            v=patches[j];vmin=v.min(0);vmax=v.max(0);band=c['contact_face_band_m']
            # This model's upper faces are horizontal; fail rather than assume for another model.
            zaxis=np.abs(gr[j][2]);axis=int(zaxis.argmax())
            if abs(zaxis[axis]-1)>1e-10:raise ValueError('Nonhorizontal table patch requires explicit polygon support implementation')
            on_top=abs(p[2]-vmax[2])<=band and all(vmin[k]-band<=p[k]<=vmax[k]+band for k in [0,1])
            bottom_matches=abs(lo[2]-vmax[2])<=band*2
            if on_top and bottom_matches and d>=-band*2:support.append(j)
            else:side.append(j)
        elif j not in c['floor_geom_ids'] and j not in c['gripper_left_ids']+c['gripper_right_ids']:
            indirect.append(j) # A contact graph is only a possible support path; no force direction.
    return {'valid':True,'direct_support':bool(support),'support_candidates':sorted(set(support)),
      'side_or_unresolved_table_contacts':sorted(set(side)),'indirect_candidate':bool(indirect),
      'indirect_support_contacts':sorted(set(indirect)),'other_contacts':sorted(set(other)),
      'gripper_contacts':sorted(set(grip)),'bilateral_gripper':bool(set(grip)&set(c['gripper_left_ids'])) and bool(set(grip)&set(c['gripper_right_ids'])),
      'outside_table_support_projection':not any(all(hi[k]>=v[:,k].min() and lo[k]<=v[:,k].max() for k in [0,1]) for v in patches.values()),
      'whole_collision_below_tabletop':bool(hi[2]<top-c['contact_face_band_m']),
      'bottom_z':float(lo[2]),'top_z':float(hi[2]),'center_z':float((lo[2]+hi[2])/2),'table_top_z':top,
      'collision_bounds_m':[lo.tolist(),hi.tolist()]}

def allowed_run(run,split):
    if run not in split['development'] or run in split['held_out']:raise ValueError('Held-out/unknown run forbidden before recording access')

def build_frame_observations(ref,index,entities,gp,gr,contacts,profiles,objects,observation_fn=observations):
    """Atomic frame transaction: calculate every object/profile before committing.

    Any calculation/validation failure invalidates this frame across profiles.
    No destination lists are mutated here.
    """
    try:
        staged={profile:{} for profile,_ in profiles}
        for name in objects:
            for profile,pc in profiles:
                obs=observation_fn(index,entities[name],gp,gr,contacts,pc)
                if not obs.get('valid'):raise ValueError('Observation producer returned invalid result')
                for key in ['center_z','bottom_z','table_top_z']:
                    if not np.isfinite(obs[key]):raise ValueError('Nonfinite derived observation')
                staged[profile][name]=dict(ref,**obs)
        return staged,None
    except (KeyError,ValueError,TypeError,IndexError,ArithmeticError) as exc:
        return {profile:{name:dict(ref,valid=False,error=str(exc)) for name in objects} for profile,_ in profiles},str(exc)

def commit_frame_observations(destinations,staged,frame):
    """Validate the entire transaction before any append; exactly one per frame."""
    for profile,objects in destinations.items():
        if set(objects)!=set(staged[profile]):raise ValueError('Object set mismatch')
        for name,records in objects.items():
            if staged[profile][name]['frame']!=frame or (records and records[-1]['frame']>=frame):raise ValueError('Duplicate or out-of-order observation frame')
    for profile,objects in destinations.items():
        for name,records in objects.items():records.append(staged[profile][name])

def process(root,c,out):
    split=json.loads((root/'proposed_split.json').read_text());index=NativeGeometryIndex.load(root/'corrected_native_geometry_v2.json')
    inv=json.loads((root/'corrected_entity_inventory_v2.json').read_text())['records'];inventory={r['run_id']:r for r in inv}
    out.mkdir(exist_ok=False);access=[];summaries=[];sensitivity=[]
    profiles=[('base',c)]+[(p['name'],dict(c,**{k:v for k,v in p.items() if k!='name'})) for p in c['sensitivity_profiles']]
    for run in split['development']:
        allowed_run(run,split);ep=int(re.search(r'trial(\d+)',run)[1]);folder=Path(c['source_root'])/f'episode_{ep:03d}'
        xmlhash=hashlib.sha256((folder/'simulator.xml').read_bytes()).hexdigest();path=folder/'trajectory.h5'
        access.append({'run_id':run,'path':str(path),'mode':'r','size':path.stat().st_size,'mtime_ns':path.stat().st_mtime_ns,'xml_sha256':xmlhash})
        entities={e['name']:e for e in inventory[run]['entities']};samples={name:[] for name in c['objects']};bundles=[];errors=[];profile_samples={p:{name:[] for name in c['objects']} for p,_ in profiles[1:]}
        with h5py.File(path,'r') as f:
            if str(f.attrs['global_episode_id'])!=run or str(f.attrs['task_configuration_id'])!=c['task_id']:raise ValueError('Run/task identity mismatch')
            frames=list(f['frames']);n=len(frames);actions=len(f['transitions'])
            if n!=actions+11 or frames!=[f'{i:06d}' for i in range(n)]:raise ValueError('Interval/record count inconsistent')
            for fi in range(n):
                g=f[f'frames/{fi:06d}'];ref={'run_id':run,'frame':fi,'hdf5_frame':f'{fi:06d}','time':float(value(g,'simulator/time')),'stage':str(g.attrs['stage']),'control_step':int(g.attrs['control_step']),'host_snapshot_utc':str(g.attrs['utc'])}
                ref['geometry_nominal_time']=ref['time']-c['geometry_phase_lag_s'] if fi else 0.
                try:
                    expected='before_settling' if fi==0 else ('settling' if fi<=10 else ('terminal' if fi==n-1 else 'control'))
                    # Terminal stage may be control when producer tags the last snapshot before termination decision.
                    if fi<=10 and ref['stage']!=expected:raise ValueError('Setup/interval boundary stage mismatch')
                    if fi>10:
                        ti=fi-11;tr=f[f'transitions/{ti:06d}']
                        if int(value(tr,'step'))!=ti or abs(float(value(tr,'simulator_time'))-ref['time'])>c['time_arithmetic_allowance_s']:raise ValueError('Action/snapshot timing mismatch')
                    gp=np.asarray(value(g,'simulator/geom_xpos'));gr=np.asarray(value(g,'simulator/geom_xmat')).reshape(-1,3,3)
                    index.validate_recording(run,xmlhash,len(gp));guard=index.validate_snapshot_transforms(value(g,'simulator/body_xpos'),value(g,'simulator/body_xquat'),gp,gr)
                    contacts=value(g,'simulator/contacts')
                    if len(contacts)!=int(value(g,'simulator/ncon')):raise ValueError('Contact count mismatch')
                    staged,frame_error=build_frame_observations(ref,index,entities,gp,gr,contacts,profiles,c['objects'])
                    if frame_error is not None:errors.append(dict(ref,error=frame_error))
                    else:bundles.append(dict(ref,geom_xpos=gp.tolist(),geom_xmat=gr.tolist(),contacts=contacts,identity_guard=guard))
                except (KeyError,ValueError,TypeError,IndexError,ArithmeticError) as e:
                    errors.append(dict(ref,error=str(e)))
                    staged={profile:{name:dict(ref,valid=False,error=str(e)) for name in c['objects']} for profile,_ in profiles}
                commit_frame_observations(dict(base=samples,**profile_samples),staged,fi)
                if fi%100==0:print(f'{ep:03d} frame {fi}/{n}',flush=True)
                if fi==0:pass
            result={'run_id':run,'episode':ep,'recording':str(path),'frames':n,'policy_actions':actions,'interval':[10,n-1],'nominal_interval_s':[.5, .05*(n-1)],'errors':errors,'objects':{name:analyze(samples[name],c) for name in c['objects']}}
        (out/f'episode_{ep:03d}.json').write_text(json.dumps(result,indent=2))
        import gzip
        with gzip.open(out/f'episode_{ep:03d}_observations.json.gz','wt') as h:json.dump(samples,h)
        with gzip.open(out/f'episode_{ep:03d}_geometry_contacts.json.gz','wt') as h:json.dump(bundles,h)
        for profile,pc in profiles:
            ss=samples if profile=='base' else profile_samples[profile]
            sensitivity.append({'run_id':run,'profile':profile,'objects':{name:analyze(ss[name],pc) for name in c['objects']}})
        summaries.append(result);print('FINISHED',ep,flush=True)
    (out/'access_log.json').write_text(json.dumps(access,indent=2))
    (out/'sensitivity.json').write_text(json.dumps(sensitivity,indent=2))
    (out/'summary.json').write_text(json.dumps({'status':'PROVISIONAL_UNVALIDATED','development':summaries,'held_out':[{'run_id':r,'status':'not_processed_no_event_outcomes_inspected'} for r in split['held_out']]},indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();cfg=load_config(args.root/'config.json')
    # Initialized separately for each run in process, before any samples.
    process(args.root,cfg,args.output)
