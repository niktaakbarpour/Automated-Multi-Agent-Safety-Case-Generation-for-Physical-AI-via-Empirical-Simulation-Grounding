"""Read-only targeted audit of the four existing recordings; private outputs only.

Reuses original recording/XML hashes from the existing evidence manifest. No
experiments, detectors, environments or original files are changed. The output
directory must be new. Small tables and compressed contact sheets stay private.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def main(recordings,package,out):
    import h5py
    import numpy as np
    from PIL import Image,ImageDraw
    manifest=json.loads((package/'evidence_manifest.json').read_text())
    with (package/'supporting_measurements/native_geometry.csv').open(encoding='utf-8-sig',newline='') as f:geos=list(csv.DictReader(f))
    protected=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']
    out.mkdir(parents=True,exist_ok=False)
    records=[];rows=[]
    for run in manifest['runs']:
        ep=run['episode'];root=recordings/ep;path=root/'trajectory.h5';before=path.stat()
        assert before.st_uid==32484,'read only niktakbr recordings'
        assert sha(root/'simulator.xml')==run['xml_sha256']==manifest['runs'][0]['xml_sha256'],'per-run native mapping changed'
        assert sha(path)==run['recording_sha256'],'recording changed from independent-review source'
        tree=ET.parse(root/'simulator.xml').getroot();bodies=[('world',0)];geomowners=[]
        def walk(node,owner):
            if node.tag=='body':
                owner=node.get('name','');bodies.append((owner,len(bodies)))
            if node.tag=='geom':geomowners.append(owner)
            for c in node:walk(c,owner)
        walk(tree.find('worldbody'),'world')
        ids={name:index for name,index in bodies}
        own_geos={obj:[g for g in geos if g['owner_body']==obj+'_main' and g['type']=='mjGEOM_BOX' and g['collision_capable']=='True'] for obj in protected}
        table=[g for g in geos if g['owner_body']=='living_room_table_col' and g['native_geom_id']=='10'][0]
        with h5py.File(path,'r') as h:
            assert len(geomowners)==len(h['frames/000000/simulator/geom_xpos/value'])
            assert len(bodies)==len(h['frames/000000/simulator/body_xpos/value'])
            previous={}
            for frame in range(run['last_frame']+1):
                prefix=f'frames/{frame:06d}';g=h[prefix];s=g['simulator'];time_s=float(s['time/value'][()])
                contacts=json.loads(s['contacts'].attrs['json']);pos=s['geom_xpos/value'][()];mat=s['geom_xmat/value'][()].reshape(-1,3,3)
                def bounds(geo):
                    i=int(geo['native_geom_id']);half=np.array([float(x) for x in geo['half_size_xyz_m'].split(';')]);ext=np.abs(mat[i])@half
                    return pos[i]-ext,pos[i]+ext
                tlo,thi=bounds(table)
                for obj in protected:
                    xyz=g[f'raw_observation/{obj}_pos/value'][()].tolist();quat=g[f'raw_observation/{obj}_quat/value'][()].tolist()
                    cc=[dict(index=i,**c,owner1=geomowners[c['geom1']],owner2=geomowners[c['geom2']]) for i,c in enumerate(contacts) if obj+'_main' in [geomowners[c['geom1']],geomowners[c['geom2']]]]
                    other=sorted(set(c['owner2'] if c['owner1']==obj+'_main' else c['owner1'] for c in cc))
                    lohi=[bounds(geo) for geo in own_geos[obj]];minz=min(float(lo[2]) for lo,hi in lohi);maxz=max(float(hi[2]) for lo,hi in lohi)
                    prev=previous.get(obj)
                    row=dict(episode=ep,run_id=run['run_id'],object_id=obj,native_body_id=ids[obj+'_main'],frame=frame,simulator_time_s=time_s,
                        recorded_phase=str(g.attrs['stage']),x_m=xyz[0],y_m=xyz[1],z_m=xyz[2],quat_xyzw=json.dumps(quat),
                        derived_delta_z_m='' if prev is None else xyz[2]-prev[0][2],
                        derived_delta_xy_m='' if prev is None else float(np.linalg.norm(np.array(xyz[:2])-np.array(prev[0][:2]))),
                        contact_owners=json.dumps(other),table_contact=any('living_room_table' in x for x in other),
                        floor_contact=any('floor' in x for x in other),left_finger_contact=any('leftfinger' in x or 'finger_joint1_tip' in x for x in other),
                        right_finger_contact=any('rightfinger' in x or 'finger_joint2_tip' in x for x in other),
                        contact_indices=json.dumps([c['index'] for c in cc]),contact_distances_m=json.dumps([c['dist'] for c in cc]),
                        derived_box_min_z_m=minz,derived_box_max_z_m=maxz,derived_tabletop_top_z_m=float(thi[2]),
                        derived_min_z_minus_tabletop_m=minz-float(thi[2]),
                        observation_source=f'{ep}/trajectory.h5:{prefix}/raw_observation/{obj}_pos/value;{obj}_quat/value',
                        contact_source=f'{ep}/trajectory.h5:{prefix}/simulator/contacts@json',
                        geometry_source=f'{ep}/trajectory.h5:{prefix}/simulator/geom_xpos/value;geom_xmat/value')
                    rows.append(row);previous[obj]=(xyz,time_s)
            windows=[(13,30)] if ep=='episode_002' else [(57,65),(230,265),(266,285)] if ep=='episode_014' else []
            for lo,hi in windows:
                for camera in ['agentview_image','robot0_eye_in_hand_image']:
                    frames=list(range(lo,hi+1));sheet=Image.new('RGB',(5*256,((len(frames)+4)//5)*280),'white');draw=ImageDraw.Draw(sheet)
                    for j,frame in enumerate(frames):
                        raw=h[f'frames/{frame:06d}/raw_observation/{camera}/value'][()];x=(j%5)*256;y=(j//5)*280
                        sheet.paste(Image.fromarray(raw[::-1,::-1]),(x,y+24));draw.text((x+3,y+3),f'{ep} frame {frame}',fill='black')
                    sheet.save(out/f'{ep}_{lo:03d}-{hi:03d}_{camera}.jpg',quality=88,optimize=True)
        logs={}
        for name in ['metrics.csv','resources.csv','metadata.json','completion.json','integrity_manifest.json']:
            p=root/name;logs[name]=dict(sha256=sha(p),bytes=p.stat().st_size)
            if name.endswith('.csv'):
                with p.open(newline='') as f:
                    reader=csv.DictReader(f);logs[name]['fields']=reader.fieldnames
                    if name=='metrics.csv':logs[name]['recorded_rows']=list(reader)
        after=path.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
        records.append(dict(episode=ep,run_id=run['run_id'],trajectory_sha256=run['recording_sha256'],xml_sha256=run['xml_sha256'],
            frames=run['frame_count'],source_fingerprint=[before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns],
            source_unchanged=True,recording_fresh_hash_verified=True,logs=logs,
            native_body_ids={o:ids[o+'_main'] for o in protected}))
    with (out/'sample_audit.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    receipt=dict(schema_version='r1-complete-evidence-audit-v1',records=records,rows=len(rows),
        limitations=['Coordinates metres in world frame; raw observations are endpoint samples.',
            'Contact/geometry arrays may lag endpoint nominally 0.002 s; camera exposure not independently verified.',
            'Derived AABB and finite differences are measurements, not fall/support/cause labels.',
            'Geometric contacts are not identified per-contact load-bearing forces; cfrc_ext/actuator fields are not used as such.',
            'JPEG contact sheets are compressed sampled source frames, not continuous between-frame observations.'],
        outputs={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    (out/'audit_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--recordings',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.recordings,a.package,a.out)
