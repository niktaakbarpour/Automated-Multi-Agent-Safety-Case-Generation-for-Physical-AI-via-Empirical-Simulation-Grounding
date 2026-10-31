"""Label-free preserved-evidence inventory. Run research processing on Hestia only."""
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

PACKAGE = Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_1_R1_20')
ASSIGNMENTS = PACKAGE.parents[1] / 'COORDINATOR_ASSIGNMENTS.json'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def runs(values):
    result = []
    for i, value in enumerate(values):
        if result and result[-1]['value'] == value:
            result[-1]['end'] = i
        else:
            result.append(dict(start=i, end=i, value=value))
    return result


def bounds(record, native):
    i = int(native['native_geom_id'])
    pos = record['geom_xpos'][i]
    mat = record['geom_xmat'][i]
    half = json.loads(native['half_size_xyz'])
    ext = [sum(abs(mat[3 * a + b]) * half[b] for b in range(3)) for a in range(3)]
    return [[pos[a] - ext[a], pos[a] + ext[a]] for a in range(3)]


def main(out):
    if socket.gethostname().lower() != 'hestia':
        raise RuntimeError('Research processing must run on Hestia')
    out.mkdir(exist_ok=False)
    os.environ['HOME'] = '/tmp'
    os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
    cases = json.loads(ASSIGNMENTS.read_text())['cases']
    native = rows(PACKAGE / 'native_geometry.csv')
    checked = []
    for line in (PACKAGE / 'SHA256SUMS.txt').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = name.lstrip('*')
        if sha(PACKAGE / name) != expected:
            raise ValueError('Package checksum mismatch: ' + name)
        checked.append(name)
    report = dict(source_package=str(PACKAGE), package_files_verified=len(checked),
                  assignment_sha256=sha(ASSIGNMENTS), previous_judgments_read=False, cases=[])
    for c in cases:
        case = c['case_id']
        d = PACKAGE / 'evidence' / case
        frames = rows(d / 'frame_references.csv')
        poses = rows(d / 'object_poses.csv')
        contacts = rows(d / 'contacts.csv')
        geometry = json.loads(gzip.decompress((d / 'recorded_geometry.json.gz').read_bytes()))
        n = c['frame_count']
        if [int(x['frame']) for x in frames] != list(range(n)):
            raise ValueError('Noncontiguous source frames')
        if [int(x['frame']) for x in geometry] != list(range(n)):
            raise ValueError('Noncontiguous source geometry')
        times = [float(x['simulator_time_s']) for x in frames]
        if any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError('Nonmonotonic source times')
        target = [x for x in poses if x['object_id'] == c['object_id']]
        if [int(x['frame']) for x in target] != list(range(n)):
            raise ValueError('Incomplete assigned-object poses')
        geoms = [x for x in native if x['owner_body'] == c['object_id'] + '_main' and x['collision_capable'] == 'True']
        if not geoms or any(x['type'] != 'mjGEOM_BOX' for x in geoms):
            raise ValueError('Unresolved assigned collision geometry')
        gids = {int(x['native_geom_id']) for x in geoms}
        table = [x for x in native if x['owner_body'] == 'living_room_table_col' and x['collision_capable'] == 'True']
        contacts_by_frame = [[] for _ in frames]
        for x in contacts:
            a, b = int(x['geom1']), int(x['geom2'])
            if a in gids or b in gids:
                contacts_by_frame[int(x['frame'])].append(x)
        sample = []
        for i in range(n):
            other = sorted({x['owner2'] if int(x['geom1']) in gids else x['owner1'] for x in contacts_by_frame[i]})
            bb = [bounds(geometry[i], g) for g in geoms]
            lower = min(b[2][0] for b in bb)
            table_top = max(bounds(geometry[i], g)[2][1] for g in table)
            sample.append(dict(frame=i, time=times[i], xyz=json.loads(target[i]['xyz_m']),
                quat_wxyz=json.loads(target[i]['quat_wxyz']),
                collision_bottom_z=lower, table_top_z=table_top,
                other_contact_owners=other, contact_rows=contacts_by_frame[i]))
        (out / (case + '_measurements.json')).write_text(json.dumps(sample, indent=2) + '\n')
        videos = {}
        for view in ['agentview', 'wrist']:
            video = d / (case + '_' + view + '_full_1x.mp4')
            result = subprocess.run(['/bin/ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                '-show_entries', 'stream=nb_read_frames,r_frame_rate,width,height', '-of', 'json', str(video)],
                capture_output=True, text=True, check=True)
            meta = json.loads(result.stdout)['streams'][0]
            if int(meta['nb_read_frames']) != n or meta['r_frame_rate'] != '20/1':
                raise ValueError('Camera frame mismatch')
            videos[view] = dict(path=str(video), sha256=sha(video), **meta)
        rec = dict(case_id=case, object_id=c['object_id'], frame_count=n,
            first_time=times[0], last_time=times[-1],
            timestep_min=min(b-a for a,b in zip(times,times[1:])),
            timestep_max=max(b-a for a,b in zip(times,times[1:])),
            frame9_10_11=[sample[i] for i in [9,10,11]],
            contact_owner_runs=runs([x['other_contact_owners'] for x in sample]),
            initial_and_terminal_xyz=[sample[0]['xyz'],sample[-1]['xyz']],
            z_range=[min(x['xyz'][2] for x in sample),max(x['xyz'][2] for x in sample)],
            videos=videos, measurement_file=str(out / (case + '_measurements.json')),
            source_files={str(p):sha(p) for p in sorted(d.iterdir()) if p.is_file()},
            raw_hdf5_present=False, raw_state_alignment_independently_verified=False,
            image_exposure_alignment_verified=False, support_force_measured=False)
        report['cases'].append(rec)
        print(case, 'complete', flush=True)
    (out / 'MEASUREMENT_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'NUMERIC_LEDGER_SHA256.json').write_text(json.dumps(
        {p.name:sha(p) for p in out.glob('*.json')}, indent=2) + '\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
