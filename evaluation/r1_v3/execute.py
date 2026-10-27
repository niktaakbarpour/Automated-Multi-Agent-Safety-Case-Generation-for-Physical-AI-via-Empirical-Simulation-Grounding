"""Read-only Hestia execution of frozen v3; no human-answer inputs."""
import argparse
import gzip
import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path

from r1_checker import evaluate, arithmetic

HERE=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def save(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def extract_frame(g, fi, index, inventory, physical, config):
    import numpy as np
    # These imports are frozen baseline measurement utilities, not its verdict logic.
    from run_development import value, corners
    gp=np.asarray(value(g,'simulator/geom_xpos'));gr=np.asarray(value(g,'simulator/geom_xmat')).reshape(-1,3,3)
    index.validate_snapshot_transforms(value(g,'simulator/body_xpos'),value(g,'simulator/body_xquat'),gp,gr)
    contacts=value(g,'simulator/contacts')
    if len(contacts)!=int(value(g,'simulator/ncon')):raise ValueError('Incomplete contact bundle')
    for ct in contacts:
        index.contact_pair(ct)
        if not all(math.isfinite(float(x)) for x in list(ct['pos'])+[ct['dist']]):raise ValueError('Nonfinite contact')
    tableids=physical['table_geom_ids']
    id_owner={};ids={}
    for name,e in inventory.items():
        ids[name]=[i for i in e['native_geom_ids'] if index.by_id(i)['collision_capable']]
        for i in ids[name]:id_owner[i]=name
    for geom in index.geometries:
        i=geom['native_geom_id'];ancestry=geom['body_ancestry']+[geom['owner_body']]
        if 'living_room_table' in ancestry:id_owner[i]='living_room_table'
        elif i in physical['floor_geom_ids']:id_owner[i]='floor'
        elif any(s.startswith(('robot0_','gripper0_')) for s in ancestry):id_owner[i]='robot'
    boxes={i:corners(index,i,gp,gr) for name in ids for i in ids[name]}
    boxes.update({i:corners(index,i,gp,gr) for i in tableids})
    bounds={i:(v.min(0),v.max(0)) for i,v in boxes.items()}
    table_vertices=np.concatenate([boxes[i] for i in tableids])
    tablelo=table_vertices.min(0);tablehi=table_vertices.max(0)
    objects={}
    for name,geomids in ids.items():
        vs=np.concatenate([boxes[i] for i in geomids]);lo=vs.min(0);hi=vs.max(0)
        tol=arithmetic(lo.tolist()+hi.tolist()+tablelo.tolist()+tablehi.tolist(),config)
        separated=all(any(hi[k]<bounds[i][0][k]-tol or lo[k]>bounds[i][1][k]+tol for k in range(3)) for i in tableids)
        objects[name]=dict(valid=True,vertices=vs.tolist(),bounds=[lo.tolist(),hi.tolist()],
            pose=np.concatenate([np.concatenate([gp[i].ravel(),gr[i].ravel()]) for i in geomids]).tolist(),
            contact_native_ids=[],contact_entities=[],support_parents=[],supported_children=[],support_contacts=[],
            table_contact=False,table_separated=bool(separated),bilateral_gripper=False,
            finger_z={side:float(np.mean(gp[physical[f'gripper_{side}_ids'],2])) for side in ['left','right']})
    for ct in contacts:
        a,b=ct['geom1'],ct['geom2']
        for child,lower in [(a,b),(b,a)]:
            name=id_owner.get(child)
            if name not in objects or id_owner.get(lower)==name:continue
            if lower not in id_owner:raise ValueError('Unmapped contact owner')
            o=objects[name];parent=id_owner[lower]
            o['contact_native_ids'].append(lower);o['contact_entities'].append(parent)
            o['table_contact']|=parent=='living_room_table'
            if lower not in boxes or parent in ['robot','floor']:continue
            # Only an actual horizontal BOX upper face can form an upward edge.
            plo,phi=bounds[lower];clo,chi=bounds[child]
            olow=o['bounds'][0][2];p=ct['pos'];d=float(ct['dist'])
            tol=arithmetic(list(plo)+list(phi)+list(clo)+list(chi)+p+[d],config)
            horizontal=abs(max(abs(x) for x in gr[lower][2])-1.)<=tol
            overlap=all(max(plo[k],clo[k])-tol<=p[k]<=min(phi[k],chi[k])+tol for k in [0,1])
            # Signed native distance and contact midpoint must agree with the
            # actual two collision faces. No new contact-height band is used.
            if horizontal and overlap and d<=tol and abs((clo[2]-phi[2])-d)<=tol and abs(2*p[2]-clo[2]-phi[2])<=tol and abs(olow-clo[2])<=tol:
                o['support_parents'].append(parent)
                if parent in objects:objects[parent]['supported_children'].append(name)
                o['support_contacts'].append(dict(child_native_geom=child,parent_native_geom=lower,
                    parent_entity=parent,position=p,recorded_signed_distance=d,face_consistency_arithmetic_allowance=tol))
    for o in objects.values():
        o['contact_native_ids']=sorted(set(o['contact_native_ids']))
        o['contact_entities']=sorted(set(o['contact_entities']))
        o['support_parents']=sorted(set(o['support_parents']))
        o['supported_children']=sorted(set(o['supported_children']))
        touched=set(o['contact_native_ids'])
        o['bilateral_gripper']=bool(touched & set(physical['gripper_left_ids'])) and bool(touched & set(physical['gripper_right_ids']))
    return dict(frame=fi,time=float(value(g,'simulator/time')),valid=True,contacts_complete=True,mapping_valid=True,
                table_pose=np.concatenate([np.concatenate([gp[i].ravel(),gr[i].ravel()]) for i in tableids]).tolist(),objects=objects)


def execute(args):
    import numpy,h5py
    config=json.loads((HERE/'config.json').read_text())
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for name,digest in freeze['implementation_files'].items():
        if sha(HERE/name)!=digest:raise ValueError('V3 implementation changed after freeze: '+name)
    sys.path.insert(0,str(args.release/'src'))
    from native_geometry_v2 import NativeGeometryIndex
    physical=json.loads((args.release/'config.json').read_text())
    manifest=json.loads((HERE.parent/'r1_reference/recordings.json').read_text())
    baseline=json.loads((HERE.parent/'r1_reference/baseline_freeze.json').read_text())
    for name,digest in baseline['files'].items():
        tail=Path(name).relative_to('reports/fall_checker_dev_v2_20261017')
        if tail.parts[0]=='src' or str(tail) in ['config.json','corrected_native_geometry_v2.json','corrected_entity_inventory_v2.json']:
            if sha(args.release/tail)!=digest:raise ValueError('Baseline measurement dependency drift: '+str(tail))
    index=NativeGeometryIndex.load(args.release/'corrected_native_geometry_v2.json')
    inventories={r['run_id']:r for r in json.loads((args.release/'corrected_entity_inventory_v2.json').read_text())['records']}
    if args.output.exists():raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    receipts=[];predictions=[];errors=[]
    for run in manifest['runs']:
        folder=Path(physical['source_root'])/run['episode']
        receipt=[]
        for name,field in [('trajectory.h5','recording_sha256'),('simulator.xml','xml_sha256')]:
            p=folder/name
            if not p.is_file() or p.is_symlink() or sha(p)!=run[field]:raise ValueError('Missing/mismatched/symlinked original: '+str(p))
            st=p.stat();receipt.append(dict(path=str(p),sha256=run[field],size=st.st_size,mtime_ns=st.st_mtime_ns))
        inventory=inventories[run['run_id']]
        if inventory['source_xml_sha256']!=run['xml_sha256']:raise ValueError('Per-recording inventory mismatch')
        entities={e['name']:e for e in inventory['entities']}
        frames=[]
        with h5py.File(folder/'trajectory.h5','r') as h:
            if str(h.attrs['global_episode_id'])!=run['run_id'] or str(h.attrs['task_configuration_id'])!=manifest['task_id']:raise ValueError('Run/task identity mismatch')
            if list(h['frames'])!=[f'{i:06d}' for i in range(run['frame_count'])] or len(h['transitions'])!=run['policy_action_count']:raise ValueError('Frame coverage mismatch')
            previous_time=None
            for fi in range(run['frame_count']):
                g=h[f'frames/{fi:06d}']
                try:
                    from run_development import value
                    index.validate_recording(run['run_id'],run['xml_sha256'],len(value(g,'simulator/geom_xpos')))
                    fact=extract_frame(g,fi,index,entities,physical,config)
                    if not math.isfinite(fact['time']):raise ValueError('Nonfinite simulator time')
                    if previous_time is not None and abs(fact['time']-previous_time-config['sample_period_s'])>config['time_arithmetic_allowance_s']:raise ValueError('Timing mismatch')
                    if fi==10 and str(g.attrs['stage'])!='settling':raise ValueError('Frame 10 not pre-policy settling boundary')
                    if fi>10:
                        transition=h[f'transitions/{fi-11:06d}']
                        if int(value(transition,'step'))!=fi-11 or abs(float(value(transition,'simulator_time'))-fact['time'])>config['time_arithmetic_allowance_s']:raise ValueError('Transition timing mismatch')
                    previous_time=fact['time']
                except (ValueError,KeyError,TypeError,IndexError,ArithmeticError) as exc:
                    fact=dict(frame=fi,valid=False,contacts_complete=False,mapping_valid=False,objects={},error=str(exc))
                    errors.append(dict(run_id=run['run_id'],frame=fi,error=str(exc)));previous_time=None
                frames.append(fact)
        # Full derived facts stay in the execution directory, not in the git source tree.
        with gzip.open(args.output/f'{run["episode"]}_facts.json.gz','wt') as f:json.dump(frames,f)
        for name in config['objects']:
            p=evaluate(frames,name,run['run_id'],config)
            p.update(recording_sha256=run['recording_sha256'],source_commit=freeze['source_commit'],
                     configuration_sha256=sha(HERE/'config.json'),implementation_freeze_sha256=sha(HERE/'FREEZE.json'),
                     facts_sha256=sha(args.output/f'{run["episode"]}_facts.json.gz'))
            predictions.append(p)
        for item in receipt:
            p=Path(item['path']);st=p.stat()
            after=dict(path=str(p),sha256=sha(p),size=st.st_size,mtime_ns=st.st_mtime_ns)
            if after!=item:raise ValueError('Original changed during read-only execution')
            receipts.append(dict(before=item,after=after))
        print('PROCESSED',run['episode'],flush=True)
    save(args.output/'predictions.json',predictions)
    save(args.output/'receipts.json',receipts)
    save(args.output/'errors.json',errors)
    save(args.output/'runtime.json',dict(python=sys.version,executable=sys.executable,numpy=numpy.__version__,h5py=h5py.__version__,platform=platform.platform(),argv=sys.argv,
        source_commit=freeze['source_commit'],reference_answers_loaded=False,previous_reference_exposure=config['exposure_disclosure'],original_recordings_opened=True,physics_stepped=False))
    save(args.output/'PREDICTION_SEAL.json',dict(files={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file()},reference_answers_loaded=False))
    print('SEALED',sha(args.output/'predictions.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    execute(p.parse_args())
