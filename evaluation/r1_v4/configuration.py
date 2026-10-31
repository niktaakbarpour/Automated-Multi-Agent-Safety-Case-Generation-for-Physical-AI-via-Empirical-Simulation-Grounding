"""Versioned structural and semantic config checks, before evidence parsing."""
from pathlib import Path
import jsonschema
from .provenance import canonical, load

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SPEC = REPO / 'requirements/r1_generalized_v2'
SCHEMA_ID = 'urn:trustworthy:r1:generalized:configuration:2.0.1'


def validate_configuration(value):
    try:
        canonical(value)
    except (ValueError, TypeError) as e:
        return ['invalid_json:' + str(e)]
    validator = jsonschema.Draft202012Validator(load(SPEC / 'R1_V2_CONFIG_SCHEMA.json'))
    errors = sorted(('schema:' + '/'.join(map(str, e.absolute_path)) + ':' + e.message
                     for e in validator.iter_errors(value)))
    if errors:
        return errors
    objects = value['protected_objects']
    surfaces = [s['id'] for s in value['support_surfaces']]
    mapping = value['object_surface_mapping']
    if len(set(surfaces)) != len(surfaces):
        errors.append('duplicate_surface_id')
    if set(objects) & set(surfaces):
        errors.append('object_surface_role_collision')
    if set(objects) != set(mapping):
        errors.append('object_mapping_keys_mismatch')
    if any(s not in surfaces for ss in mapping.values() for s in ss):
        errors.append('dangling_surface_id')
    interval = value['monitoring_interval']
    a, b = interval['start'], interval['end']
    expected = 'explicit_index' if interval['axis'] == 'saved_frame' else 'explicit_time'
    if a['kind'] == 'terminal_recorded_snapshot' or b['kind'] == 'recorded_first_policy_boundary':
        errors.append('invalid_anchor_role')
    if any(x['kind'].startswith('explicit_') and x['kind'] != expected for x in (a, b)):
        errors.append('axis_boundary_mismatch')
    if a['value'] is not None and b['value'] is not None and a['value'] > b['value']:
        errors.append('reversed_interval')
    m = value['assessment_manifest']
    comparisons = [('requirement', 'id', value['requirement_id']),
                   ('requirement', 'version', value['requirement_version']),
                   ('configuration_schema', 'id', SCHEMA_ID),
                   ('configuration_schema', 'version', '2.0.1'),
                   ('adapter', 'id', value['benchmark']['adapter_id']),
                   ('adapter', 'version', value['benchmark']['adapter_version'])]
    for part, key, expected_value in comparisons:
        if m[part][key] != expected_value:
            errors.append('manifest_mismatch:' + part + '.' + key)
    if m['source_model_bindings'] != value['source_bindings']:
        errors.append('manifest_source_mismatch')
    if m['requested_domain']['projection'] != value['temporal_alignment']['domain']:
        errors.append('manifest_projection_mismatch')
    refs = [b['artifact_ref'] for b in value['source_bindings']]
    if len(set(refs)) != len(refs):
        errors.append('duplicate_source_binding')
    support = value['initial_support_rules']
    if support['profile'] == 'legacy_v3_static_stencil' and support['boundary_context_offsets'] != [-1, 0, 1]:
        errors.append('legacy_stencil_drift')
    return sorted(errors)


def unsupported_for_object(config, object_id):
    """Well-formed deferred capabilities are scoped IC, not input rejection."""
    reasons = []
    mapped = set(config['object_surface_mapping'][object_id])
    if any(s['motion_model'] != 'stationary' for s in config['support_surfaces'] if s['id'] in mapped):
        reasons.append('unsupported_dynamic_surface')
    if set(config['geometry_contract']['required_shape_capabilities']) != {'box'}:
        reasons.append('unsupported_geometry_profile')
    if config['temporal_alignment']['domain'] != 'saved_frame_projection':
        reasons.append('unsupported_continuous_domain')
    if config['initial_support_rules']['profile'] != 'validated_boundary_support':
        reasons.append('unsupported_legacy_inference')
    profile_ref = config['assessment_manifest']['inference_profile']['artifact_ref']
    needed_refs = [config['geometry_contract']['profile_ref'], config['geometry_contract']['support_inference_ref'],
                   config['coordinate_frames']['gravity_direction_ref'], config['coordinate_frames']['transforms_ref'],
                   config['fall_detection_rules']['numeric_policy']['roundoff_profile_ref']]
    if any(ref != profile_ref for ref in needed_refs):
        reasons.append('unsupported_or_unresolved_inference_reference')
    for surface in config['support_surfaces']:
        if surface['id'] in mapped and (surface['geometry_ref'] != 'synthetic:model' or
                surface['frame_ref'] != config['coordinate_frames']['common_frame']):
            reasons.append('unsupported_surface_geometry_or_frame_reference')
    if config['initial_support_rules']['boundary_context_offsets']:
        reasons.append('boundary_context_inference_not_implemented')
    numeric = config['fall_detection_rules']['numeric_policy']
    if any(numeric[k] is not None for k in ('physical_distance_uncertainty_m', 'persistence_window_s', 'hysteresis_m')):
        reasons.append('empirical_calibration_not_enabled')
    return reasons
