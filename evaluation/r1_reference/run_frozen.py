"""Read-only original-recording execution; never imports reference answers.

Run using the existing numpy/h5py runtime. Fresh output directory required.
The immutable baseline implementation is imported, not edited.
"""
import argparse
import hashlib
import json
import platform
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def intervals(frames):
    result = []
    for f in sorted(set(frames)):
        if result and f == result[-1][1] + 1:
            result[-1][1] = f
        else:
            result.append([f, f])
    return result

def adapt(run, obj, result, samples, provenance, protocol):
    valid = [s['frame'] for s in samples if s.get('valid') and s['frame'] >= 10]
    initial = next((s for s in samples if s['frame'] == 10), None)
    initial_kind = result['initial_applicability']
    reason = {
        'direct_table_support_candidate': 'Initial direct support is a geometric/contact candidate, not established load-bearing support.',
        'unknown_indirect_support': 'Stable indirect load-bearing support chain not established.',
        'unknown_other_contact_support': 'Initial contact support source/direction unresolved.',
        'initial_table_support_not_established': 'Absence of a support candidate does not establish absence of initial support.',
        'unknown_missing_measurement': 'Frame-10 measurement missing or invalid.'
    }[initial_kind]
    events = []
    for i, e in enumerate(result['events']):
        events.append({
            'event_id': f'{run}:{obj}:candidate:{i:04d}',
            'type': e['type'], 'phase': e['phase'], 'scope': 'unresolved',
            'status': 'provisional_physical_candidate',
            'interval': [e['observed_event_span'][k]['frame'] for k in ('start', 'end')],
            'onset_bracket': e['departure_bracket'], 'evidence': e
        })
    return {
        'run_id': run, 'canonical_object_id': obj,
        'requirement_version': protocol['requirement_version'],
        'adapter_version': protocol['adapter_version'],
        'applicability': 'unknown', 'outcome': 'insufficient_information',
        'abstention_reason': reason + ' Baseline lacks established requirement-level event and negative-coverage evidence.',
        'requested_frame_interval': [10, samples[-1]['frame']],
        'reviewed_frame_intervals': [],
        'measurement_frame_intervals': intervals(valid),
        'observation_domain': 'saved_geometry_contact_endpoints_20Hz_nominal_lag_0.002s',
        'compatible_reference_domain_established': False,
        'coverage_gaps': result['gaps'],
        'evidence': {'frame_10_observation': initial, 'initial_candidate_assessment': initial_kind,
                     'support_transitions': result['support_transitions'],
                     'unconfirmed_descent_sequences': result['unconfirmed_descent_sequences'],
                     'requirement_verdict': result['requirement_verdict']},
        'events': events, **provenance
    }

def run(args):
    import gzip
    import numpy
    import h5py
    release = args.release.resolve()
    freeze = json.loads((HERE/'baseline_freeze.json').read_text())
    # Fail closed on changes to executable code/config/mappings.
    for rel, expected in freeze['files'].items():
        p = Path(rel)
        tail = p.relative_to('reports/fall_checker_dev_v2_20261017')
        if tail.parts[0] == 'src' or str(tail) in ['config.json','proposed_split.json','corrected_native_geometry_v2.json','corrected_entity_inventory_v2.json']:
            if sha(release/tail) != expected:
                raise ValueError(f'Frozen baseline changed: {tail}')
    sys.path.insert(0, str(release/'src'))
    from checker import load_config
    from run_development import process
    protocol = json.loads((HERE/'protocol.json').read_text())
    manifest = json.loads((HERE/'recordings.json').read_text())
    c = load_config(release/'config.json')
    selected = [r['run_id'] for r in manifest['runs']]
    split = json.loads((release/'proposed_split.json').read_text())
    if not set(selected) <= set(split['development']) or set(selected) & set(split['held_out']):
        raise ValueError('Requested runs violate frozen development split')
    if args.output.exists():
        raise FileExistsError(args.output)
    receipts = []
    for r in manifest['runs']:
        folder = Path(c['source_root'])/r['episode']
        for name, key in [('trajectory.h5','recording_sha256'),('simulator.xml','xml_sha256')]:
            p = folder/name
            if not p.is_file() or p.is_symlink():
                raise ValueError(f'Missing or symlinked original: {p}')
            st = p.stat()
            actual = sha(p)
            if actual != r[key]:
                raise ValueError(f'Original hash mismatch: {p}')
            receipts.append({'path':str(p),'sha256':actual,'size':st.st_size,'mtime_ns':st.st_mtime_ns})
    args.output.mkdir(parents=True)
    dump(args.output/'original_receipts_before.json', receipts)
    # A temporary execution view selects four runs. Physical config and code unchanged.
    with tempfile.TemporaryDirectory(prefix='r1-baseline-view-') as td:
        view = Path(td)
        for name in ['corrected_native_geometry_v2.json','corrected_entity_inventory_v2.json']:
            shutil.copyfile(release/name, view/name)
        dump(view/'proposed_split.json',dict(split,development=selected))
        process(view,c,args.output/'raw')
    provenance = {
        'checker_commit':freeze['checker_last_commit'],
        'repository_frozen_head':freeze['repository_head'],
        'checker_sha256':sha(release/'src/checker.py'),
        'checker_config_sha256':sha(release/'config.json'),
        'adapter_sha256':sha(Path(__file__)),
        'evaluation_config_sha256':sha(HERE/'protocol.json')}
    predictions=[]
    for r in manifest['runs']:
        ep = r['episode']
        result = json.loads((args.output/'raw'/f'{ep}.json').read_text())
        if result['run_id'] != r['run_id'] or result['frames'] != r['frame_count']:
            raise ValueError('Run/frame identity mismatch')
        with gzip.open(args.output/'raw'/f'{ep}_observations.json.gz','rt') as f:
            samples=json.load(f)
        for obj in c['objects']:
            predictions.append(adapt(r['run_id'],obj,result['objects'][obj],samples[obj],provenance,protocol))
    dump(args.output/'predictions.json', predictions)
    after=[]
    for receipt in receipts:
        p=Path(receipt['path']);st=p.stat()
        item=dict(receipt,sha256=sha(p),size=st.st_size,mtime_ns=st.st_mtime_ns)
        if item != receipt:
            raise ValueError('Original content/stat changed during read-only execution')
        after.append(item)
    dump(args.output/'original_receipts_after.json',after)
    dump(args.output/'runtime.json',{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
        'numpy':numpy.__version__,'h5py':h5py.__version__,'argv':sys.argv,
        'original_recordings_opened':True,'physics_stepped':False,'reference_answers_loaded':False,
        'native_geometry_policy':'Each run validated against its XML hash, native geometry count, per-run inventory and per-frame body/geometry transforms. Reuse mapping only after these identity guards pass.',**provenance})
    # Seal before any reference-loading scorer is invoked.
    files={str(p.relative_to(args.output)):sha(p) for p in sorted(args.output.rglob('*')) if p.is_file()}
    dump(args.output/'PREDICTION_SEAL.json',{'files':files,'reference_answers_loaded':False})
    print('PREDICTIONS SEALED',sha(args.output/'predictions.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    run(p.parse_args())
