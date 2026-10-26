"""Export only disputed box geometry from existing HDF5; no simulation or labels."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main(recordings,package,out):
    import h5py
    import numpy as np
    inventory=json.loads((package/'evidence_manifest.json').read_text())['runs']
    with (package/'supporting_measurements/native_geometry.csv').open(encoding='utf-8-sig',newline='') as f:
        geoms=list(csv.DictReader(f))
    rows=[]
    for ep,frames in [('episode_002',range(0,2)),('episode_014',range(240,251))]:
        root=recordings/ep; run=next(r for r in inventory if r['episode']==ep)
        assert hashlib.sha256((root/'simulator.xml').read_bytes()).hexdigest()==run['xml_sha256']
        # All selected XML hashes must match the geometry inventory's source XML;
        # a different XML requires a new native mapping, not integer-ID reuse.
        assert run['xml_sha256']==inventory[0]['xml_sha256']
        path=root/'trajectory.h5';before=path.stat()
        with h5py.File(path,'r') as h:
            for frame in frames:
                sim=h[f'frames/{frame:06d}/simulator']
                for g in geoms:
                    if g['type']!='mjGEOM_BOX' or not g['owner_body'].startswith(('orange_juice_1','cream_cheese_1','living_room_table')):continue
                    index=int(g['native_geom_id']);center=sim['geom_xpos/value'][index]
                    rotation=sim['geom_xmat/value'][index].reshape(3,3)
                    half=np.array([float(x) for x in g['half_size_xyz_m'].split(';')])
                    extent=np.abs(rotation)@half
                    rows.append(dict(episode=ep,run_id=run['run_id'],frame=frame,
                        simulator_time_s=float(sim['time/value'][()]),native_geom_id=index,owner_body=g['owner_body'],
                        center_xyz_m=json.dumps(center.tolist()),rotation_row_major=json.dumps(rotation.reshape(-1).tolist()),
                        aabb_min_xyz_m=json.dumps((center-extent).tolist()),aabb_max_xyz_m=json.dumps((center+extent).tolist()),
                        source=f'{ep}/trajectory.h5:frames/{frame:06d}/simulator/geom_xpos/value;geom_xmat/value',
                        xml_sha256=run['xml_sha256'],trajectory_sha256=run['recording_sha256']))
        after=path.stat()
        assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
    with out.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--recordings',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.recordings,a.package,a.out)
