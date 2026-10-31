"""Closed analytical compatibility registry and hash-resolved inline artifacts."""
from pathlib import Path
from . import CHECKER_VERSION
from .configuration import HERE, SPEC, SCHEMA_ID
from .provenance import bytes_digest, canonical, digest, load
from .temporal import parse_domain

NORMATIVE = ('R1_V2_SPECIFICATION.md', 'FORMAL_SEMANTICS.md', 'APPLICABILITY_RULES.md',
             'FALL_DEFINITION.md', 'EVIDENCE_CONTRACT.md', 'R1_V2_CONFIG_SCHEMA.json',
             'V3_COMPATIBILITY.md', 'V4_IMPLEMENTATION_PLAN.md', 'V4_TEST_MATRIX.md',
             'finalization/FINALIZED_R1_V2_CONTRACT.md', 'finalization/RESTRICTED_V4_SCOPE.md',
             'finalization/EMPIRICAL_GATES.md', 'finalization/V4_ENTRY_CHECKLIST.md')


def builtins():
    package = {'files': {n: bytes_digest((SPEC / n).read_bytes()) for n in NORMATIVE}}
    code = {'files': {p.name: bytes_digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))}}
    code['contracts'] = {p.name: bytes_digest(p.read_bytes()) for p in sorted(HERE.glob('*.json'))}
    rows = {
        'requirement': ('R1', '2.0.0', canonical(package)),
        'configuration_schema': (SCHEMA_ID, '2.0.1', (SPEC / 'R1_V2_CONFIG_SCHEMA.json').read_bytes()),
        'evidence_schema': ('urn:trustworthy:r1:v4:evidence:1.0.0', '1.0.0', (HERE / 'evidence.schema.json').read_bytes()),
        'adapter': ('analytical-declarations', '1.0.0', (HERE / 'adapter.json').read_bytes()),
        'inference_profile': ('analytical-static-box', '1.0.0', (HERE / 'profile.json').read_bytes()),
        'checker': ('r1-v4-restricted-infrastructure', CHECKER_VERSION, canonical(code)),
        'capability_record': ('analytical-contract-capabilities', '1.0.0', (HERE / 'capabilities.json').read_bytes()),
    }
    return {name: {'id': i, 'version': version, 'artifact_ref': 'builtin:' + name,
                   'sha256': bytes_digest(content)} for name, (i, version, content) in rows.items()}


class MissingObservation(ValueError):
    pass


class Registry:
    def __init__(self, config, artifacts):
        if not isinstance(artifacts, dict) or any(k.startswith('builtin:') for k in artifacts):
            raise ValueError('invalid_artifact_registry_or_builtin_override')
        self.artifacts = artifacts
        self.bindings = {b['artifact_ref']: b['sha256'] for b in config['source_bindings']}

    def resolve(self, ref):
        expected = self.bindings.get(ref)
        if expected is None:
            raise ValueError('unresolved_hash_bound_artifact:' + ref)
        if ref not in self.artifacts:
            raise MissingObservation('missing_observation_artifact:' + ref)
        value = self.artifacts[ref]
        if digest(value) != expected:
            raise ValueError('artifact_hash_mismatch:' + ref)
        return value


def validate_manifest(config, artifacts):
    errors = []
    m = config['assessment_manifest']
    expected = builtins()
    for part, binding in expected.items():
        if m[part] != binding:
            errors.append('unsupported_or_unresolved_binding:' + part)
    if m['purpose'] != 'analytical_fixture' or config['benchmark']['id'] != 'synthetic-analytical':
        errors.append('empirical_and_legacy_admission_disabled')
    if m['validation_status'] != 'capability_tested':
        errors.append('analytical_capability_status_required')
    if m['calibration_records']:
        errors.append('empirical_calibration_not_enabled')
    if not config['execution_id'] or not config['task_id']:
        errors.append('runtime_execution_task_identity_required')
    registry = None
    cells, interval, model = (), None, None
    try:
        registry = Registry(config, artifacts)
        if config['temporal_alignment']['clock_ref'] != m['requested_domain']['cells_ref']:
            errors.append('unresolved_analytical_clock_reference')
        domain = registry.resolve(m['requested_domain']['cells_ref'])
        cells, interval = parse_domain(domain, config)
        scope = registry.resolve(m['validity_scope_ref'])
        scope_expected = {'execution_id': config['execution_id'], 'task_id': config['task_id'],
                          'objects': sorted(config['protected_objects']),
                          'surfaces': {o: sorted(ss) for o, ss in sorted(config['object_surface_mapping'].items())},
                          'projection': config['temporal_alignment']['domain'],
                          'axis': config['monitoring_interval']['axis'],
                          'start': interval.start, 'end': interval.end, 'purpose': 'analytical_fixture'}
        if scope != scope_expected:
            errors.append('validity_scope_mismatch')
        # The analytical adapter has an explicit model binding, never a guessed roster.
        model = registry.resolve('synthetic:model')
        if (not isinstance(model, dict) or set(model) != {'synthetic', 'complete_roster', 'objects', 'surfaces'}
                or model['synthetic'] is not True or type(model['complete_roster']) is not bool
                or not isinstance(model['objects'], dict) or not isinstance(model['surfaces'], dict)):
            errors.append('invalid_synthetic_model_contract')
            model = None
    except (ValueError, KeyError, TypeError) as e:
        errors.append(str(e))
    return tuple(sorted(set(errors))), registry, cells, interval, model
