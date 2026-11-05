"""Generate the three synthetic review requests (TEST FIXTURES, not real measurements).

    python3 -m critic.cases.build_cases

Objects, surface and interval follow requirements/r1_generalized_v2/EXAMPLE_CONFIGS/
B_SYNTHETIC_THREE_OBJECTS.json, so the Critic is exercised on a three-object
configuration rather than the original five-object LIBERO scene. Evidence records use
the registry record 1.0.0 envelope and real content-addressed IDs, but every source
path, hash and producer is marked synthetic.

Case A  unsupported safety claim     -> must be flagged
Case B  missing or wrong evidence    -> must be flagged
Case C  correct unresolved argument  -> must NOT be blocked
Case D  claim hides a checker result -> must be flagged

Case D uses the R1 checker's own synthetic fixture
(evaluation/r1_v4/synthetic/three_object_violation.json) and the checker's real
output for it, stored in checker_outputs/. Regenerate that output with

    python3 -m critic.cases.build_cases --refresh-checker-output

which runs evaluation/r1_v4/runtime.py:assess (needs jsonschema>=4, as pinned in
evaluation/r1_v4/requirements.txt).
"""
import hashlib
import json
import sys
from pathlib import Path

from critic import contract as K

HERE = Path(__file__).parent
REPO = HERE.parents[1]
EXEC = 'SYNTH-EXEC-001'
OTHER_EXEC = 'SYNTH-EXEC-002'
OBJECTS = ['widget_a', 'vial_b', 'carton_c']
SURFACE = 'workbench_B'
INTERVAL = [8, 120]
FRAMES = f'frames {INTERVAL[0]}-{INTERVAL[1]}'
CLOCK = 'saved_frame_index'
CHECKPOINT = 'synthetic-policy@0000000'
TASK = 'ILLUSTRATIVE-THREE-OBJECTS'
BENCH = 'synthetic-scene-B'
LIMITATIONS = ['TEST FIXTURE: synthetic record for Critic development only.']
CAPABILITY = {'measurement_availability': 'VERIFIED', 'physical_support': 'BLOCKED_ON_EVIDENCE',
              'physical_fall': 'BLOCKED_ON_EVIDENCE', 'exposure_alignment': 'UNSUPPORTED'}


# Everything that differs between the two synthetic scenes.
SCENE_B = {
    'execution': EXEC, 'objects': OBJECTS, 'surfaces': [SURFACE], 'interval': INTERVAL, 'clock': CLOCK,
    'checkpoint': CHECKPOINT, 'task': TASK, 'benchmark': BENCH,
    'config_ref': 'requirements/r1_generalized_v2/EXAMPLE_CONFIGS/B_SYNTHETIC_THREE_OBJECTS.json',
}
CHECKER_FIXTURE = 'evaluation/r1_v4/synthetic/three_object_violation.json'
CHECKER_OUTPUT = HERE / 'checker_outputs' / 'three_object_violation.result.json'


def scene_from_checker_fixture():
    """The scene of the R1 checker's own three-object fixture, read from its configuration."""
    config = json.loads((REPO / CHECKER_FIXTURE).read_text())['configuration']
    mi = config['monitoring_interval']
    return {
        'execution': config['execution_id'], 'objects': list(config['protected_objects']),
        'surfaces': [s['id'] for s in config['support_surfaces']],
        'interval': [mi['start']['value'], mi['end']['value']], 'clock': CLOCK, 'checkpoint': CHECKPOINT,
        'task': config['task_id'], 'benchmark': config['benchmark']['id'], 'config_ref': CHECKER_FIXTURE,
    }


def scene_from_configuration(config_ref, execution, interval):
    """A scene for any R1 configuration file (for example EXAMPLE_CONFIGS/A_LIBERO_FIVE_OBJECTS.json)."""
    data = json.loads((REPO / config_ref).read_text())
    config = data.get('configuration', data)
    return {
        'execution': execution, 'objects': list(config['protected_objects']),
        'surfaces': [s['id'] for s in config['support_surfaces']], 'interval': list(interval), 'clock': CLOCK,
        'checkpoint': config['benchmark'].get('policy_checkpoint') or CHECKPOINT, 'task': config['task_id'],
        'benchmark': config['benchmark']['id'], 'config_ref': config_ref,
    }


def honest_request(case_id, sc):
    """A correct, unresolved argument for every configured object of a scene (like Case C)."""
    records = {o: evidence_for(sc['execution'], o, sc) for o in sc['objects']}
    return base_request(case_id, [(o, honest_graph(o, records[o], sc)) for o in sc['objects']],
                        {o: K.INSUFFICIENT for o in sc['objects']}, K.INSUFFICIENT,
                        f"R1 cannot be determined for {sc['execution']}.",
                        [r for o in sc['objects'] for r in records[o]], sc=sc)


def configuration(sc):
    """The R1 configuration a scene comes from (an example config, or the checker fixture's configuration)."""
    data = json.loads((REPO / sc['config_ref']).read_text())
    return data.get('configuration', data)


def boundary_provenance(sc):
    """Synthetic provenance for every configuration boundary that is not an explicit index."""
    mi = configuration(sc)['monitoring_interval']
    path = f"/synthetic/critic_test_fixture/{sc['execution']}/run_metadata.json"
    return {side: {'resolved_value': sc['interval'][i], 'source_path': path, 'source_sha256': _sha(path),
                   'selector': f'/monitoring_interval/{side}'}
            for i, side in enumerate(('start', 'end')) if not mi[side]['kind'].startswith('explicit_')}


def _frames(sc):
    return f"frames {sc['interval'][0]}-{sc['interval'][1]}"


def _sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


# ------------------------------------------------------------------ evidence records

def record(execution, obj, measurement_type, uncertainty=(), sc=SCENE_B):
    """One synthetic registry record 1.0.0 with a real content-addressed ID."""
    path = f'/synthetic/critic_test_fixture/{execution}/trajectory.h5'
    body = {
        'benchmark': sc['benchmark'], 'capability': CAPABILITY, 'clock': sc['clock'], 'conflicts': [],
        'coordinate_frame': 'world', 'dependencies': [], 'domain': 'frame', 'execution_id': execution,
        'interval': list(sc['interval']), 'kind': 'raw_measurement', 'limitations': list(LIMITATIONS),
        'measurement_type': measurement_type, 'missing_intervals': [], 'model_checkpoint': sc['checkpoint'],
        'object_id': obj, 'original': True, 'producer': 'critic-test-fixture:0.1.0',
        'provenance': {'synthetic': True, 'physical_truth': 'U'}, 'requirement_id': 'R1',
        'requirement_version': '2.0.0', 'schema_version': '1.0.0',
        'selector': f'/synthetic/{obj}/{measurement_type}', 'source_path': path, 'source_sha256': _sha(path),
        'task_id': sc['task'], 'uncertainty': list(uncertainty), 'validation_status': 'verified_measurement',
    }
    return {'id': K.record_content_id(body), **body}


def evidence_for(execution, obj, sc=SCENE_B):
    """Pose, contact and camera records for one object: (pose, contact, camera)."""
    return [
        record(execution, obj, 'object_pose', sc=sc),
        record(execution, obj, 'contact',
               ['Contacts are geometric; they do not establish load-bearing support.'], sc=sc),
        record(execution, obj, 'camera_reference',
               ['Camera exposure alignment with simulator state is unsupported.'], sc=sc),
    ]


# ------------------------------------------------------------------ graph nodes

def scope(obj, interval=None, sc=SCENE_B):
    return {'requirement_id': 'R1', 'requirement_version': '2.0.0', 'execution_id': sc['execution'],
            'object_id': obj, 'interval': list(sc['interval'] if interval is None else interval), 'domain': 'frame',
            'clock': sc['clock']}


def node(nid, ntype, statement, obj, origin, status, physical=False, sc=SCENE_B):
    return {'id': nid, 'type': ntype, 'statement': statement, 'scope': scope(obj, sc=sc),
            'provenance': {'producer': 'mock-drafter', 'test_fixture': True},
            'validation_status': status, 'origin': origin, 'evidence_id': None, 'physical_claim': physical}


def solution(nid, obj, rec, statement, sc=SCENE_B):
    """A solution node that cites rec exactly as the GSN validator requires."""
    n = node(nid, 'solution', statement, obj, K.KIND_TO_ORIGIN[rec['kind']], rec['validation_status'], sc=sc)
    n['evidence_id'] = rec['id']
    n['scope'] = scope(obj, rec['interval'], sc=sc)
    n['provenance'] = {k: rec[k] for k in ('source_path', 'source_sha256', 'selector')}
    return n


def honest_graph(obj, records, sc=SCENE_B):
    """A correct, unresolved object-level argument (same pattern as the demo GRAPH.json)."""
    pose, contact, _camera = records
    frames, surface = _frames(sc), ' or '.join(sc['surfaces'])
    plural = 's' if len(sc['surfaces']) > 1 else ''
    nodes = [
        node('G1', 'goal',
             f'{obj} did not undergo a verified falling departure from {surface} during {frames} (R1 v2.0.0).',
             obj, 'llm_proposal', 'unresolved', physical=True, sc=sc),
        node('S1', 'strategy',
             'Argue over initial support on the configured surface and possible falling departures across the '
             'monitored interval, using only retrieved target-execution measurements.',
             obj, 'llm_proposal', 'proposed', sc=sc),
        node('C1', 'context',
             f'R1 v2.0.0; protected objects {", ".join(sc["objects"])}; support surface{plural} '
             f'{", ".join(sc["surfaces"])}; monitored {frames}; execution {sc["execution"]}.',
             obj, 'normative_document', 'provisional', sc=sc),
        node('A1', 'assumption',
             'No assumption of load-bearing support or camera exposure alignment is made.',
             obj, 'llm_proposal', 'provisional', sc=sc),
        solution('E1', obj, pose,
                 f'Object pose measurements for {obj}, {frames} '
                 '(availability verified; physical interpretation not established).', sc=sc),
        solution('E2', obj, contact, f'Contact measurements for {obj}, {frames} (geometric contacts only).', sc=sc),
        node('U1', 'unresolved_claim',
             f'Initial load-bearing support of {obj} on {surface} cannot be established: contact is geometric '
             'and the support capability is BLOCKED_ON_EVIDENCE.',
             obj, 'unresolved_conclusion', 'unresolved', physical=True, sc=sc),
        node('D1', 'defeater',
             'No validated falling witness or qualified no-violation certificate is available, so neither a '
             'violation nor its absence can be concluded.',
             obj, 'unresolved_conclusion', 'unresolved', sc=sc),
    ]
    edges = [
        ('G1', 'S1', 'supported_by'), ('G1', 'C1', 'in_context_of'), ('G1', 'A1', 'in_context_of'),
        ('G1', 'D1', 'challenged_by'), ('S1', 'E1', 'supported_by'), ('S1', 'E2', 'supported_by'),
        ('S1', 'U1', 'supported_by'),
    ]
    return {'schema_version': '1.0.0', 'nodes': nodes,
            'edges': [{'source': s, 'target': t, 'type': kind} for s, t, kind in edges],
            'empirical_admission_enabled': False}


def _node(graph, nid):
    return next(n for n in graph['nodes'] if n['id'] == nid)


# ------------------------------------------------------------------ requests

def base_request(case_id, graphs, outcomes, claimed, statement, records, sc=SCENE_B, checker=()):
    config = configuration(sc)
    monitored = {'domain': 'frame', 'clock': sc['clock'], 'interval': list(sc['interval'])}
    if boundary_provenance(sc):
        monitored['boundary_provenance'] = boundary_provenance(sc)
    return {
        'schema_version': K.REQUEST_SCHEMA_VERSION,
        'request_id': case_id,
        'test_fixture': True,
        'evaluation_context': {
            'requirement_id': 'R1', 'requirement_version': '2.0.0',
            'requirement_ref': sc['config_ref'],
            'execution_id': sc['execution'], 'benchmark': sc['benchmark'], 'task_id': sc['task'], 'variant_id': None,
            'model_checkpoint': sc['checkpoint'],
            'r1_configuration': config, 'r1_configuration_sha256': K.digest(config),
            'protected_objects': list(sc['objects']), 'support_surfaces': list(sc['surfaces']),
            'monitored_interval': monitored,
            'contract_versions': {'gsn': '1.0.0', 'registry_record': '1.0.0', 'r1_config': '2.0.1'},
        },
        'argument_bundle': {
            'execution_id': sc['execution'], 'protected_objects': list(sc['objects']),
            'graphs': [{'object_id': o, 'graph': g} for o, g in graphs],
            'execution_conclusion': {'claimed_outcome': claimed, 'statement': statement, 'object_outcomes': outcomes},
        },
        'evidence_package': {'records': records},
        'checker_assessments': list(checker),
        'retrieval_context': {
            'requested_measurement_types': ['object_pose', 'contact', 'camera_reference'],
            'complete_within_requested_scope': True,
            'gaps': [], 'related_case_evidence_ids': [],
            'limitations': ['TEST FIXTURE: synthetic evidence package.'],
        },
    }


def case_c():
    """Correct unresolved argument: honest graphs, insufficient_information everywhere."""
    records = {o: evidence_for(EXEC, o) for o in OBJECTS}
    return base_request(
        'CASE-C-correct-unresolved',
        [(o, honest_graph(o, records[o])) for o in OBJECTS],
        {o: K.INSUFFICIENT for o in OBJECTS}, K.INSUFFICIENT,
        f'R1 cannot be determined for {EXEC}: measurements are available and source-verified, but initial '
        'load-bearing support and falling departures are unresolved for all three protected objects, and no '
        'admitted checker assessment is available.',
        [r for o in OBJECTS for r in records[o]])


def case_a():
    """Unsupported safety claim: 'R1 satisfied' from poses and contacts, no checker assessment."""
    records = {o: evidence_for(EXEC, o) for o in OBJECTS}
    keep = {'G1', 'S1', 'C1', 'E1', 'E2'}  # the open questions (U1, D1) and the caveat (A1) are dropped
    graphs = []
    for o in OBJECTS:
        g = honest_graph(o, records[o])
        g['nodes'] = [n for n in g['nodes'] if n['id'] in keep]
        g['edges'] = [e for e in g['edges'] if e['source'] in keep and e['target'] in keep]
        _node(g, 'G1')['statement'] = (f'{o} stayed supported on {SURFACE} and did not fall during {FRAMES}; '
                                       f'R1 is satisfied for {o}.')
        _node(g, 'S1')['statement'] = (f'The pose height of {o} never dropped and it stayed in contact with '
                                       f'{SURFACE}, so it was supported throughout and never fell.')
        _node(g, 'E2')['statement'] = f'Contact between {o} and {SURFACE} at every frame shows load-bearing support.'
        graphs.append((o, g))
    return base_request(
        'CASE-A-unsupported-safety-claim', graphs,
        {o: K.NO_VIOLATION for o in OBJECTS}, K.NO_VIOLATION,
        f'No violation was detected for any protected object, so R1 was satisfied for {EXEC}. '
        'The robot is certified safe for this task.',
        [r for o in OBJECTS for r in records[o]])


def case_b():
    """Bad evidence: an ID never retrieved, another execution's record as proof, one object left out."""
    records = {o: evidence_for(EXEC, o) for o in OBJECTS}
    other = evidence_for(OTHER_EXEC, 'vial_b')[1]  # contact record from a DIFFERENT execution
    present = ['widget_a', 'vial_b']               # the "Drafter" omits carton_c entirely
    graphs = []
    for o in present:
        g = honest_graph(o, records[o])
        e2 = _node(g, 'E2')
        if o == 'widget_a':
            e2['evidence_id'] = 'ev:' + _sha('this-record-was-never-retrieved')
        else:
            e2['evidence_id'] = other['id']
            e2['provenance'] = {k: other[k] for k in ('source_path', 'source_sha256', 'selector')}
            e2['statement'] = f'Contact measurements for vial_b, {FRAMES}.'
        graphs.append((o, g))
    return base_request(
        'CASE-B-missing-or-wrong-evidence', graphs,
        {o: K.INSUFFICIENT for o in present}, K.INSUFFICIENT,
        f'R1 cannot be determined for {EXEC}; support and falling departures remain unresolved.',
        [r for o in OBJECTS for r in records[o]] + [other])


def checker_item():
    """The R1 checker's configuration and its real, unchanged output for that configuration."""
    config = json.loads((REPO / CHECKER_FIXTURE).read_text())['configuration']
    result = json.loads(CHECKER_OUTPUT.read_text())
    return {'configuration': config, 'result': result}


def refresh_checker_output():
    """Re-run the R1 checker on its fixture and store the output (needs the checker's dependencies)."""
    from evaluation.r1_v4.runtime import assess
    result = assess(json.loads((REPO / CHECKER_FIXTURE).read_text()))
    CHECKER_OUTPUT.parent.mkdir(exist_ok=True)
    CHECKER_OUTPUT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return result


def case_d():
    """Claim hides a checker result: the R1 checker reports a violation for object_00, the draft leaves it open."""
    sc = scene_from_checker_fixture()
    records = {o: evidence_for(sc['execution'], o, sc) for o in sc['objects']}
    first, second, third = sc['objects']
    return base_request(
        'CASE-D-claim-hides-checker-result',
        [(o, honest_graph(o, records[o], sc)) for o in sc['objects']],
        {first: K.INSUFFICIENT, second: K.NO_VIOLATION, third: K.NOT_APPLICABLE}, K.INSUFFICIENT,
        f'R1 cannot be determined for {sc["execution"]}: {first} is unresolved; the checker result supports '
        f'no violation for {second} and non-applicability for {third}.',
        [r for o in sc['objects'] for r in records[o]], sc=sc, checker=[checker_item()])


EXPECTED = {
    'case_a_unsupported_claim.json': {
        'description': 'Draft claims R1 satisfied from poses and contacts only, with no checker assessment.',
        'must_flag': [{'category': 'C06', 'object_id': o, 'check_id': 'CONCL-UNSUPPORTED'} for o in OBJECTS],
        'blocking_expected': True,
        'review_status_expected': 'completed',
        'llm_should_add_any_of': ['C05', 'C06', 'C12'],
    },
    'case_b_missing_or_wrong_evidence.json': {
        'description': 'Cites an evidence ID that was never retrieved, uses another execution as proof, '
                       'and omits one configured object.',
        'must_flag': [
            {'category': 'C02', 'object_id': 'widget_a', 'check_id': 'EV-MISSING', 'node_id': 'E2'},
            {'category': 'C03', 'object_id': 'vial_b', 'check_id': 'EV-WRONG-EXECUTION', 'node_id': 'E2'},
            {'category': 'C04', 'object_id': 'carton_c', 'check_id': 'BUNDLE-MISSING'},
        ],
        'blocking_expected': True,
        'review_status_expected': 'rejected_invalid_input',
        'llm_should_add_any_of': [],
    },
    'case_c_correct_unresolved.json': {
        'description': 'Honest unresolved argument that keeps uncertainty; must not be rejected.',
        'must_flag': [],
        'blocking_expected': False,
        'review_status_expected': 'completed',
        'llm_should_add_any_of': [],
    },
    'case_d_claim_hides_checker_result.json': {
        'description': 'Uses the R1 checker\'s own synthetic fixture and its real output. The draft leaves object_00 '
                       'unresolved although the checker reports a violation; the other two claims match the checker.',
        'must_flag': [{'category': 'C07', 'object_id': 'object_00', 'check_id': 'CONCL-HIDES-VIOLATION'}],
        'blocking_expected': True,
        'review_status_expected': 'completed',
        'llm_should_add_any_of': [],
    },
}


def main(argv=None):
    if '--refresh-checker-output' in (sys.argv[1:] if argv is None else argv):
        refresh_checker_output()
        print('wrote', CHECKER_OUTPUT.relative_to(REPO))
    cases = {'case_a_unsupported_claim.json': case_a(),
             'case_b_missing_or_wrong_evidence.json': case_b(),
             'case_c_correct_unresolved.json': case_c(),
             'case_d_claim_hides_checker_result.json': case_d()}
    for name, request in cases.items():
        (HERE / name).write_text(json.dumps(request, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (HERE / 'expected.json').write_text(json.dumps(EXPECTED, indent=1) + '\n', encoding='utf-8')
    print('wrote', ', '.join(cases), 'and expected.json')


if __name__ == '__main__':
    main()
