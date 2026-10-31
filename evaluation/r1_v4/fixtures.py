"""Synthetic source declarations only; never reads a simulator, video or prediction."""
import copy
from pathlib import Path
import socket
from .configuration import SPEC
from .manifest import builtins
from .provenance import digest, load, write_new


def record(config, rid, object_id, claim, truth='T', dependencies=(), payload=None,
           interval=None, cells=(), kind='declaration', validity='verified'):
    return {'id': rid, 'kind': kind, 'claim': claim, 'truth': truth, 'validity': validity,
            'object_id': object_id, 'execution_id': config['execution_id'], 'synthetic': True,
            'profile_version': '1.0.0', 'requirement_version': '2.0.0',
            'surfaces': config['object_surface_mapping'].get(object_id, []),
            'interval': [0, 0] if interval is None else interval, 'cells': list(cells),
            'dependencies': list(dependencies), 'source_ref': 'synthetic:source',
            'producer': 'synthetic-constraint-ledger',
            'frame': {'id': config['coordinate_frames']['common_frame'], 'clock': config['temporal_alignment']['clock_ref'],
                      'length_unit': 'm', 'time_unit': 's', 'handedness': 'right_handed'},
            'uncertainty': {'temporal': 0, 'description': []}, 'payload': {} if payload is None else payload}


def seal(bundle):
    """Bind fixtures to their explicit declarations; not empirical certification."""
    config, artifacts = bundle['configuration'], bundle['artifacts']
    artifacts['synthetic:source'] = {'synthetic': True, 'execution_id': config['execution_id'],
                                    'records': {r['id']: copy.deepcopy(r) for r in bundle['evidence']['records']}}
    config['source_bindings'] = [{'artifact_ref': ref, 'sha256': digest(value)} for ref, value in sorted(artifacts.items())]
    config['assessment_manifest']['source_model_bindings'] = copy.deepcopy(config['source_bindings'])
    return bundle


def make_bundle(states=('V', 'N', 'U'), multiple_surfaces=False):
    c = load(SPEC / 'EXAMPLE_CONFIGS/D_STATIC_TWO_ROOT_BOX.json')
    c['benchmark'] = {'id': 'synthetic-analytical', 'adapter_id': 'analytical-declarations', 'adapter_version': '1.0.0'}
    c['task_id'], c['execution_id'] = 'synthetic-task', 'synthetic-execution'
    c['protected_objects'] = ['object_%02d' % i for i in range(len(states))]
    c['support_surfaces'] = [{'id': root, 'role': 'environment_support', 'geometry_ref': 'synthetic:model',
                              'frame_ref': 'world', 'motion_model': 'stationary'} for root in ('root_A', 'root_B')]
    c['object_surface_mapping'] = {o: (['root_A', 'root_B'] if multiple_surfaces else ['root_A']) for o in c['protected_objects']}
    c['monitoring_interval']['start'] = {'kind': 'explicit_index', 'value': 0}
    c['monitoring_interval']['end'] = {'kind': 'explicit_index', 'value': 2}
    c['initial_support_rules']['boundary_context_offsets'] = []
    c['temporal_alignment']['state_phase_uncertainty_s'] = 0
    c['temporal_alignment']['clock_ref'] = 'synthetic:domain'
    c['geometry_contract']['profile_ref'] = 'builtin:inference_profile'
    c['geometry_contract']['support_inference_ref'] = 'builtin:inference_profile'
    c['coordinate_frames']['gravity_direction_ref'] = 'builtin:inference_profile'
    c['coordinate_frames']['transforms_ref'] = 'builtin:inference_profile'
    c['fall_detection_rules']['numeric_policy']['roundoff_profile_ref'] = 'builtin:inference_profile'
    c['assessment_manifest'].update(builtins())
    c['assessment_manifest'].update(purpose='analytical_fixture', validation_status='capability_tested',
                                     validity_scope_ref='synthetic:scope')
    c['assessment_manifest']['requested_domain'] = {'projection': 'saved_frame_projection',
        'interval_ref': '#/monitoring_interval', 'cells_ref': 'synthetic:domain'}
    domain = {'execution_id': c['execution_id'], 'axis': 'saved_frame', 'start': 0, 'end': 2,
              'anchors': {'recorded_first_policy_boundary': 0, 'terminal_recorded_snapshot': 2},
              'cells': [{'id': 's%d' % i, 'kind': 'snapshot', 'start': i, 'end': i} for i in range(3)] +
                       [{'id': 't%d%d' % (i, i+1), 'kind': 'transition', 'start': i, 'end': i+1} for i in range(2)]}
    model = {'synthetic': True, 'complete_roster': True,
             'objects': {o: 'instance_' + o for o, state in zip(c['protected_objects'], states) if state != 'ABSENT'},
             'surfaces': {root: {'shape': 'box', 'static': True, 'horizontal': True, 'complete': True} for root in ('root_A', 'root_B')}}
    scope = {'execution_id': c['execution_id'], 'task_id': c['task_id'], 'objects': sorted(c['protected_objects']),
             'surfaces': c['object_surface_mapping'], 'projection': 'saved_frame_projection', 'axis': 'saved_frame',
             'start': 0, 'end': 2, 'purpose': 'analytical_fixture'}
    b = {'configuration': c, 'artifacts': {'synthetic:model': model, 'synthetic:domain': domain, 'synthetic:scope': scope},
         'evidence': {'evidence_version': '1.0.0', 'records': [], 'conflicts': []}}
    rows = b['evidence']['records']
    global_record = record(c, 'shared_context', '*', 'observation', interval=[0, 2],
                           kind='derived_observation', payload={'quantity': 'declared_fixture_context', 'values': [], 'unit': 'fixture'})
    rows.append(global_record)
    for o, state in zip(c['protected_objects'], states):
        def add(suffix, claim, **kw):
            r = record(c, o + '_' + suffix, o, claim, **kw); rows.append(r); return r['id']
        if state == 'ABSENT':
            add('presence', 'presence', truth='F', payload={'closed_roster': True})
            continue
        presence = add('presence', 'presence', payload={'closed_roster': True})
        identity = add('identity', 'identity', dependencies=['shared_context'], payload={'instance_id': model['objects'][o]})
        geometry = add('geometry', 'geometry', kind='geometry', interval=[0, 2],
                       payload={'shape': 'box', 'dimensions': [1, 1, 1], 'static': False, 'horizontal': False, 'complete': True})
        link = add('link', 'support_link', payload={'child': o, 'parent': 'root_B' if multiple_surfaces else 'root_A'})
        support = add('support', 'initial_support', truth='F' if state == 'NA' else 'T',
                      dependencies=[presence, identity, geometry, link],
                      payload={'chain': [o, 'root_B' if multiple_surfaces else 'root_A'], 'all_support_excluded': state == 'NA'})
        deps = [support]
        if state == 'IC':
            rows[-1]['validity'] = 'invalid_contract'
        elif state == 'V':
            add('fall', 'violation', dependencies=deps, interval=[1, 2], cells=['s1', 's2', 't12'],
                payload={'origin': 'T', 'loss': 'T', 'downward': 'T', 'handling_excluded': 'F', 'onset': [1, 1], 'downward_interval': [1, 2]})
        elif state == 'N':
            add('clear', 'static_negative', dependencies=deps, interval=[0, 2],
                cells=[row['id'] for row in domain['cells']], payload={'method': 'exact_static_constraint'})
    return seal(b)


def main(argv=None):
    assert socket.gethostname().lower() == 'hestia'
    import argparse
    parser = argparse.ArgumentParser(description='Explicit synthetic declarations only')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent / 'synthetic')
    root = parser.parse_args(argv).output_dir
    root.mkdir(exist_ok=True)
    for name, states, multi in [('three_object_violation', ('V', 'N', 'NA'), False),
                                 ('five_object_uncertain', ('N', 'NA', 'U', 'ABSENT', 'IC'), False),
                                 ('multiple_static_surfaces', ('N', 'N', 'N'), True)]:
        write_new(root / (name + '.json'), make_bundle(states, multi))


if __name__ == '__main__':
    main()
