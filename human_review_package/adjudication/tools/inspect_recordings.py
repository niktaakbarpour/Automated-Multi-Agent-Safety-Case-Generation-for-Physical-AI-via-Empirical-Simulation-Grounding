"""Read only the four pinned development recordings; export small review evidence.

Run with the existing Hestia h5py/numpy/Pillow environment. No simulation/checker.
Outputs must be a new directory. No source data or original annotations are changed.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def main(recordings, out):
    import h5py
    import numpy as np
    from PIL import Image, ImageDraw
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for ep in ['episode_000', 'episode_001', 'episode_002', 'episode_014']:
        root = recordings / ep
        path = root / 'trajectory.h5'
        before = path.stat()
        xml = ET.fromstring((root / 'simulator.xml').read_bytes())
        # MuJoCo assigns world body 0 and depth-first body/geom indices. Anonymous
        # geometries MUST occupy an index; never index the lossy geom_names list.
        bodies = [{'id': 0, 'name': 'world'}]
        geoms = []
        def walk(node, owner):
            if node.tag == 'body':
                owner = node.get('name', '')
                bodies.append({'id': len(bodies), 'name': owner})
            if node.tag == 'geom':
                geoms.append({'id': len(geoms), 'name': node.get('name', ''),
                              'owner': owner, 'type': node.get('type', 'inherited'),
                              'size': node.get('size', '')})
            for child in node:
                walk(child, owner)
        walk(xml.find('worldbody'), 'world')
        with h5py.File(path, 'r') as h:
            assert len(geoms) == len(h['frames/000000/simulator/geom_xpos/value'])
            assert len(bodies) == len(h['frames/000000/simulator/body_xpos/value'])
            windows = [(0, 30)] if ep != 'episode_014' else [(0, 30), (57, 285)]
            sampled = []
            for lo, hi in windows:
                for frame in range(lo, hi + 1):
                    g = h[f'frames/{frame:06d}']
                    sim = g['simulator']
                    contacts = json.loads(sim['contacts'].attrs['json'])
                    contacts = [dict(c, contact_index=i,
                                     owner1=geoms[c['geom1']]['owner'],
                                     owner2=geoms[c['geom2']]['owner'])
                                for i, c in enumerate(contacts)]
                    positions = {name: g[f'raw_observation/{name}_pos/value'][()].tolist()
                                 for name in ['cream_cheese_1', 'orange_juice_1',
                                              'milk_1', 'ketchup_1', 'butter_1']}
                    sampled.append(dict(frame=frame, time_s=float(sim['time/value'][()]),
                                        positions=positions, contacts=contacts))
            # Contact sheets include every frame in important short intervals;
            # continuous videos remain the primary human review evidence.
            intervals = [(0, 16)] if ep != 'episode_014' else [(0, 16), (269, 285), (240, 250)]
            for lo, hi in intervals:
                for camera in ['agentview_image', 'robot0_eye_in_hand_image']:
                    frames = list(range(lo, hi + 1))
                    sheet = Image.new('RGB', (5 * 256, ((len(frames) + 4)//5) * 280), 'white')
                    draw = ImageDraw.Draw(sheet)
                    for j, frame in enumerate(frames):
                        raw = h[f'frames/{frame:06d}/raw_observation/{camera}/value'][()]
                        x, y = (j % 5)*256, (j//5)*280
                        sheet.paste(Image.fromarray(raw[::-1, ::-1]), (x, y+24))
                        draw.text((x+3, y+3), f'{ep} frame {frame}', fill='black')
                    sheet.save(out / f'{ep}_{lo:03d}-{hi:03d}_{camera}.png')
        supporting = {}
        for name in ['simulator.xml', 'simulator_index.json', 'metadata.json',
                     'metrics.csv', 'resources.csv', 'completion.json']:
            p = root / name
            supporting[name] = dict(sha256=sha(p), bytes=p.stat().st_size)
            if name.endswith('.csv'):
                with p.open(newline='') as f:
                    supporting[name]['header'] = next(csv.reader(f))
        after = path.stat()
        assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
        records.append(dict(episode=ep, trajectory_sha256=sha(path),
                            trajectory_bytes=before.st_size, simulator_xml_sha256=sha(root/'simulator.xml'),
                            source_stat_unchanged=True, source_directory=str(root),
                            native_bodies=bodies, native_geometries=geoms,
                            supporting=supporting, samples=sampled))
    (out/'recorded_evidence.json').write_text(json.dumps(dict(
        schema_version='r1-recorded-evidence-v1', records=records,
        limitations=['Endpoint samples 0.05 s apart; cached contacts may lag endpoint by nominal 0.002 s.',
                     'Geometric contact is not load-bearing force or causation.',
                     'No numerical support or carrying threshold is introduced.']), indent=2)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--recordings', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    main(a.recordings, a.out)
