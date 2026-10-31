"""Stage only receipt-listed regular files, with mandatory fresh SHA256 checks.

Run on an authorized CPU allocation, not a login node. No original is written.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import tarfile


def main(selection, destination):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('CPU allocation required')
    destination.mkdir(exist_ok=False)
    fields = ['case_id', 'execution_id', 'archive', 'member', 'expected_sha256',
              'staged_path', 'fresh_sha256', 'bytes', 'verified']
    with (destination / 'STAGING_MANIFEST.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        groups = {}
        for case in json.loads(selection.read_text()):
            groups.setdefault(case['archive'], []).append(case)
        for archive, cases in groups.items():
            with tarfile.open(archive, 'r:') as tf:
                members = {m.name: m for m in tf.getmembers()}
                for case in cases:
                    folder = destination / case['case_id']
                    folder.mkdir(exist_ok=False)
                    for expected in case['members']:
                        m = members[expected['name']]
                        if not m.isfile() or m.size != expected['size']:
                            raise ValueError('Unexpected archive member type/size')
                        target = folder / Path(m.name).name
                        digest = hashlib.sha256()
                        count = 0
                        with tf.extractfile(m) as src, target.open('xb') as dst:
                            while True:
                                block = src.read(1024 * 1024)
                                if not block:
                                    break
                                digest.update(block)
                                count += len(block)
                                dst.write(block)
                        actual = digest.hexdigest()
                        valid = actual == expected['sha256'] and count == m.size
                        writer.writerow(dict(case_id=case['case_id'], execution_id=case['run_id'],
                            archive=archive, member=m.name, expected_sha256=expected['sha256'],
                            staged_path=str(target), fresh_sha256=actual, bytes=count, verified=valid))
                        stream.flush()
                        if not valid:
                            raise ValueError('Fresh payload hash mismatch: ' + m.name)
    (destination / 'STAGING_COMPLETE.json').write_text(json.dumps(dict(
        complete=True, job_id=os.environ['SLURM_JOB_ID'],
        selection_sha256=hashlib.sha256(selection.read_bytes()).hexdigest()), indent=2) + '\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
