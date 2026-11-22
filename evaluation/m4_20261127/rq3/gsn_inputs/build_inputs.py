"""Reproduce the two clean, development-only RQ3 parents on a CPU."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

from jsonschema import Draft202012Validator

from critic import checks, contract
from critic.critic import CRITIC_VERSION
from evaluation.r1_v4.evidence_registry_gsn.gsn import Edge, Graph, Node
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.provenance import canonical, digest, strict_loads


ROOT = Path(__file__).resolve().parents[4]
BASELINE_COMMIT = '20cec80bd44d19c6f58168132f366cbe38bd74e9'
BENCHMARK_COMMIT = '9b674b8eb1d894596ac7e0687fef7308b9c681a6'
MANIFEST_VERSION = 'm4-rq3-clean-fixtures/1.0.0'
ARCHIVE = 'integration/fixtures/one_pass_20261113'
SOURCE_INVENTORY = 'evaluation/m4_20261127/shared/CASE_SOURCE_INVENTORY.csv'
V3_SCOPE = 'human_review_package/requirement_scope.v3.json'
V2_SCHEMA = 'requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json'
REGISTRY = 'evaluation/r1_v4/evidence_registry_gsn'
SOURCES = {
    'P1': {
        'path': f'{ARCHIVE}/artifacts/models/critic.request.json',
        'commit': 'b66c24a18a6239933c96d71dedc9f0bfeaa86425',
        'sha256': 'fb84dec4a8e690277bd2d835dd52d64e44c6386ee23176a19596b1c8cf2ca3cc',
        'execution_id': 'libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db',
        'canonical_group_id': 'original_reviewed:libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db',
        'scope': [10, 257],
        'scope_origin': 'Archived request has explicit frame bounds. The archived start agrees with the reviewed v3 scope.',
        'evidence_role': 'archived_real_retrieval_in_analytical_fixture',
        'source_eligibility': 'EXCLUDED',
        'exposure': 'Previously used in development, human review and checker evaluation.',
        'registry_boundary': 'No registry rows. Frozen Phase 5 retrieval is retained as structured evidence.',
    },
    'P2': {
        'path': 'critic/cases/case_c_correct_unresolved.json',
        'commit': '33a9ab470b1860a253a0e7afcccd839c52d5ecdc',
        'sha256': 'd5ab3c2f932497222370f633b690183879ee46178c55bd519a99e560a70b3839',
        'execution_id': 'SYNTH-EXEC-001',
        'canonical_group_id': 'synthetic:critic_case_c:SYNTH-EXEC-001',
        'scope': [8, 120],
        'scope_origin': 'Case C has a fixture-specific start and a synthetic terminal boundary certificate.',
        'evidence_role': 'synthetic_critic_development_fixture',
        'source_eligibility': 'SYNTHETIC_DEVELOPMENT_ONLY',
        'exposure': 'Used to develop Critic rules and prompts.',
        'registry_boundary': 'Case C records are synthetic. They are accepted by Critic fixture validation and are outside the production registry source scope.',
    },
}

# These inputs and certificates were inspected on the baseline checkout. The
# manifest also records hashes of the actual validation code and schema files.
SOURCE_CHECKSUMS = {
    f'{ARCHIVE}/MANIFEST.json': '1b764993287f04b9f94ad8099764ebe138d77f457b9dceab823b9fb648f052d8',
    SOURCE_INVENTORY: '88698f1577c7c8ee6526ca7ff5945f5afd7bb1169d67eb0cdb7dfd8661c74707',
    V3_SCOPE: '97fd2e026993658db8cb4c46910a5ef3fd00af5e6d966fae4506c62e80319ea7',
    V2_SCHEMA: 'b7bf5a3c56e805951fcc99d518c3c09eadd0fede5ed02710e6672e44e19c1377',
}
AUDITED_FILES = (
    'critic/critic.py', 'critic/checks.py', 'critic/claims.py', 'critic/contract.py', 'critic/retrieval.py',
    'critic/phase5_request.py', 'critic/schemas/critic_request.schema.json',
    'drafter/validation.py', 'drafter/request_profiles.py', 'drafter/phase5_adapter.py',
    'drafter/revision/contract.py', 'integration/handoff.py', f'{REGISTRY}/gsn.py',
    f'{REGISTRY}/models.py', f'{REGISTRY}/gsn_graph.schema.json',
    f'{REGISTRY}/registry_record.schema.json', 'evaluation/r1_v4/configuration.py',
    'requirements/r1_generalized_v2/FORMAL_SEMANTICS.md',
)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _pinned_bytes(path, expected_sha256):
    raw = (ROOT / path).read_bytes()
    if _sha256(raw) != expected_sha256:
        raise ValueError(f'{path} does not match the pinned source bytes')
    return raw


def validate_shared_graphs(request):
    """Check shared graph schema, typed links, and the bound record metadata."""
    records, findings = checks.index_records(request)
    if findings:
        ids = ', '.join(finding['check_id'] for finding in findings)
        raise ValueError(f'Invalid registry records: {ids}')

    evidence = []
    for record in records.values():
        path = PurePosixPath(record['source_path'])
        if (request['test_fixture'] is True and record['provenance'].get('synthetic') is True
                and path.is_relative_to('/synthetic')):
            # index_records has validated the schema, fixture source boundary and
            # content ID. This graph view keeps the synthetic namespace separate.
            evidence.append(SimpleNamespace(**record))
        else:
            evidence.append(Record.parse(record))
    registry = SimpleNamespace(records=lambda: tuple(evidence))
    graph_schema = strict_loads((ROOT / REGISTRY / 'gsn_graph.schema.json').read_bytes())
    validator = Draft202012Validator(graph_schema)
    for item in request['argument_bundle']['graphs']:
        value = item['graph']
        problems = list(validator.iter_errors(value))
        if problems:
            raise ValueError(f"{item['object_id']} fails shared GSN schema: {problems[0].message}")
        graph = Graph(tuple(Node(**node) for node in value['nodes']),
                      tuple(Edge(**edge) for edge in value['edges']), value['schema_version'])
        graph.validate(registry)


def _validate_clean(parent_id, request, review_scope):
    source = SOURCES[parent_id]
    findings, info = checks.run_all(request)
    if not info['input_valid'] or findings:
        ids = ', '.join(finding['check_id'] for finding in findings)
        raise ValueError(f'{parent_id} did not pass the current Critic clean baseline checks: {ids}')
    validate_shared_graphs(request)

    context = request['evaluation_context']
    config = context['r1_configuration']
    bundle = request['argument_bundle']
    objects = context['protected_objects']
    interval = context['monitored_interval']
    conclusion = bundle['execution_conclusion']
    outcome = contract.INSUFFICIENT
    if request['test_fixture'] is not True or context['execution_id'] != source['execution_id']:
        raise ValueError(f'{parent_id} changed fixture classification or execution identity')
    if interval['interval'] != source['scope'] or interval['domain'] != 'frame' or interval['clock'] != 'saved_frame_index':
        raise ValueError(f'{parent_id} changed recorded-frame scope')
    if (objects != config['protected_objects'] or objects != bundle['protected_objects']
            or objects != [item['object_id'] for item in bundle['graphs']]):
        raise ValueError(f'{parent_id} changed the full ordered protected-object vector')
    if parent_id == 'P1' and (objects != review_scope['protected_objects']
                              or interval['interval'][0] != review_scope['interval']['start_saved_frame']):
        raise ValueError('P1 no longer agrees with the v3 review scope at the opening boundary')
    if request['checker_assessments'] or info['admitted'] or info['checker_admission']:
        raise ValueError(f'{parent_id} has checker evidence in the development baseline')
    if (conclusion['claimed_outcome'] != outcome or info['expected_outcome'] != outcome
            or conclusion['object_outcomes'] != dict.fromkeys(objects, outcome)):
        raise ValueError(f'{parent_id} no longer retains unresolved R1 for all objects')
    return info


def _sources_and_manifest():
    support = {path: _pinned_bytes(path, checksum) for path, checksum in SOURCE_CHECKSUMS.items()}
    archive = strict_loads(support[f'{ARCHIVE}/MANIFEST.json'])
    inventory = [row for row in csv.DictReader(support[SOURCE_INVENTORY].decode().splitlines())
                 if row['run_id'] == SOURCES['P1']['execution_id']]
    if len(inventory) != 1 or inventory[0]['eligibility_status'] != SOURCES['P1']['source_eligibility']:
        raise ValueError('P1 is not uniquely identified with the expected source inventory disposition')
    grouped_id = f"{inventory[0]['execution_group_id']}:{inventory[0]['run_id']}"
    if grouped_id != SOURCES['P1']['canonical_group_id']:
        raise ValueError('P1 canonical source group differs from the eligibility inventory')
    review_scope = strict_loads(support[V3_SCOPE])

    parents, raw_files, fixtures = {}, {}, []
    for parent_id, source in SOURCES.items():
        filename = f'{parent_id}.clean.critic_request.json'
        raw = _pinned_bytes(source['path'], source['sha256'])
        if parent_id == 'P1':
            ready = [entry for entry in archive['artifacts']
                     if f"{ARCHIVE}/{entry['file']}" == source['path']]
            if len(ready) != 1 or (ready[0]['bytes'], ready[0]['sha256']) != (len(raw), source['sha256']):
                raise ValueError('P1 does not match the archived integration receipt')
        request = strict_loads(raw)
        info = _validate_clean(parent_id, request, review_scope)
        context = request['evaluation_context']
        graphs = request['argument_bundle']['graphs']
        records = request['evidence_package']['records']
        parents[parent_id] = request
        raw_files[filename] = raw
        fixtures.append({
            'parent_id': parent_id,
            'file': filename,
            'sha256': _sha256(raw),
            'canonical_request_sha256': digest(request),
            'source': dict(source),
            'data_role': 'development_only',
            'independent_scoring_eligible': False,
            'requirement': {'id': context['requirement_id'], 'version': context['requirement_version'],
                            'configuration_sha256': context['r1_configuration_sha256']},
            'monitored_interval': context['monitored_interval'],
            'protected_objects': context['protected_objects'],
            'graph_summary': [{'object_id': item['object_id'], 'node_ids': [node['id'] for node in item['graph']['nodes']],
                               'edge_count': len(item['graph']['edges'])} for item in graphs],
            'evidence_record_ids': [record['id'] for record in records],
            'structured_evidence_count': len(request.get('structured_evidence', [])),
            'checker_assessments_admitted': sum(map(len, info['admitted'].values())),
            'execution_outcome': info['expected_outcome'],
            'critic_input_valid': info['input_valid'],
            'deterministic_findings': [],
            'shared_gsn_validation': 'passed',
        })
    manifest = {
        'schema_version': MANIFEST_VERSION,
        'validation_baseline_revision': BASELINE_COMMIT,
        'alex_mutation_protocol_revision': BENCHMARK_COMMIT,
        'data_role': 'development_only',
        'independent_scoring_groups': 0,
        'model_inference_performed': False,
        'underlying_measurement_bytes_replayed': False,
        'physical_checker_admission_established': False,
        'condition_c_for_physical_claims': 'unavailable',
        'contracts': {
            'critic': CRITIC_VERSION,
            'critic_request': contract.REQUEST_SCHEMA_VERSION,
            'gsn': contract.GSN_SCHEMA_VERSION,
            'registry_record': contract.RECORD_SCHEMA_VERSION,
            'r1_v2_configuration_schema': strict_loads(support[V2_SCHEMA])['$id'],
            'r1_v3_review_scope': review_scope['requirement_version'],
            'phase5_interface': contract.PHASE5_VERSION,
            'r1_v2_outcome_precedence': list(contract.OUTCOME_PRECEDENCE),
        },
        'pinned_reference_sha256': SOURCE_CHECKSUMS,
        'audited_file_sha256': {path: _sha256((ROOT / path).read_bytes()) for path in AUDITED_FILES},
        'parents': fixtures,
    }
    return parents, raw_files, manifest


def load_parents():
    """Load the exact pinned clean requests after CPU contract checks."""
    parents, _, _ = _sources_and_manifest()
    return parents


def build_inputs():
    """Return the validated parents and their reproducible provenance manifest."""
    parents, _, manifest = _sources_and_manifest()
    return parents, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--out', type=Path, metavar='DIR', help='Write exact clean copies and the manifest.')
    modes.add_argument('--check', type=Path, metavar='DIR', help='Verify previously generated files byte for byte.')
    args = parser.parse_args(argv)
    try:
        _, files, manifest = _sources_and_manifest()
        files['CLEAN_FIXTURE_MANIFEST.json'] = canonical(manifest) + b'\n'
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            collisions = [name for name in files if (args.out / name).exists()]
            if collisions:
                raise ValueError('Choose an unused output directory or use --check for existing files: ' + ', '.join(collisions))
            for name, raw in files.items():
                (args.out / name).write_bytes(raw)
            print(f'Wrote two validated development-only parents and a manifest to {args.out}')
        else:
            changed = [name for name, raw in files.items()
                       if not (args.check / name).is_file() or (args.check / name).read_bytes() != raw]
            if changed:
                raise ValueError('Output is missing or differs from a fresh build: ' + ', '.join(changed))
            print(f'Verified two clean parents and their manifest in {args.check}')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'{exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
