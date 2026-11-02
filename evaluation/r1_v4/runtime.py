"""Restricted assessment entry point. All empirical admission is disabled."""
import jsonschema
from . import CHECKER_VERSION, EVIDENCE_VERSION
from .admission import parse_evidence, admit
from .aggregate import aggregate
from .applicability import assess_object
from .configuration import validate_configuration
from .manifest import validate_manifest, builtins
from .provenance import canonical, digest, primitive


def assess(bundle):
    try:
        input_hash = digest(bundle)
    except (ValueError, TypeError):
        input_hash = None
    config = bundle.get('configuration') if isinstance(bundle, dict) else None
    errors = validate_configuration(config)
    try:
        config_hash = digest(config)
    except (ValueError, TypeError):
        config_hash = None
    common = {'requirement_id': 'R1', 'requirement_version': '2.0.0',
              'configuration_schema_version': '2.0.1', 'manifest_version': '1.0.0',
              'checker_id': 'r1-v4-restricted-infrastructure', 'checker_version': CHECKER_VERSION,
              'evidence_schema_version': EVIDENCE_VERSION, 'assessment_schema_version': '1.0.0',
              'validation_status': 'analytical_infrastructure_only', 'synthetic': True,
              'physical_safety_conclusion': False, 'empirical_profiles_enabled': False,
              'configuration_hash': config_hash,
              'assessment_manifest': config.get('assessment_manifest') if isinstance(config, dict) and config_hash is not None else None}
    if errors:
        return {**common, 'configuration_status': 'invalid', 'assessed': False,
                'object_assessments': [], 'execution_outcome': None,
                'configuration_diagnostics': errors, 'input_rejection_count': 1}
    runtime_errors, registry, cells, interval, model = validate_manifest(config, bundle.get('artifacts', {}))
    if input_hash is None:
        runtime_errors = tuple(sorted(set(runtime_errors) | {'invalid_nonfinite_or_nonjson_evidence'}))
    records, admissions, conflicts = (), {}, ()
    if not runtime_errors:
        try:
            evidence_input = bundle.get('evidence', {})
            records = parse_evidence(evidence_input)
            admissions, conflicts = admit(config, evidence_input, records, registry, cells, interval, model)
        except (ValueError, TypeError, KeyError, AttributeError, jsonschema.ValidationError) as e:
            runtime_errors = ('invalid_evidence_contract:' + str(e).split('\n')[0],)
            records, admissions = (), {}
    objects = tuple(assess_object(config, o, records, admissions, cells, model, runtime_errors)
                    for o in sorted(config['protected_objects']))
    result = {**common, 'configuration_status': 'valid', 'configuration_diagnostics': [],
              'assessed': True, 'input_rejection_count': 0,
              'object_assessments': primitive(objects), **aggregate(objects),
              'admitted_evidence_ids': sorted(rid for rid, a in admissions.items() if a.status.value == 'verified'),
              'rejected_evidence': primitive(tuple(a for _, a in sorted(admissions.items()) if a.status.value != 'verified')),
              'evidence_admission': primitive(tuple(a for _, a in sorted(admissions.items()))),
              'conflicts': primitive(conflicts),
              'missing_requirements': sorted(set(runtime_errors) | {o.object_id + ':' + reason for o in objects
                                        for reason in o.reasons if o.outcome.value in ('insufficient_information', 'invalid_measurement_contract')}),
              'uncertainty': sorted({u for o in objects for u in o.uncertainty}),
              'evidence_records': primitive(records),
              'provenance': {'requested_purpose': config['assessment_manifest']['purpose'],
                             'admitted_purpose': None if runtime_errors else 'analytical_fixture', 'execution_id': config['execution_id'],
                             'task_id': config['task_id'], 'runtime_bindings': builtins(),
                             'source_bindings': config['source_bindings'], 'input_hash': input_hash,
                             'source_independence': 'not_inferred_from_producers_or_filenames'},
              'excluded_events': [r.id for r in records if r.claim == 'exclusion'],
              'study_eligibility': 'pending_protocol_decision' if any(o.scope_mismatch for o in objects) else 'not_decided_by_checker'}
    result['assessment_hash'] = digest(result)
    return result
