"""Rebuild small versioned JSON contracts, on Hestia; no measurements or calibration."""
from pathlib import Path
import json
import socket


def generate():
    assert socket.gethostname().lower() == 'hestia'
    here = Path(__file__).resolve().parent
    text = {'type': 'string', 'minLength': 1}
    identifier = {'type': 'string', 'pattern': '^[A-Za-z0-9][A-Za-z0-9_.:*-]*$'}
    number = {'type': 'number'}
    def obj(properties):
        return {'type': 'object', 'additionalProperties': False, 'required': list(properties), 'properties': properties}
    def array(items, unique=False):
        return {'type': 'array', 'items': items, **({'uniqueItems': True} if unique else {})}
    strings = array(text, True)
    interval = {'type': 'array', 'prefixItems': [number, number], 'minItems': 2, 'maxItems': 2}
    props = {'id': identifier, 'kind': {'enum': ['direct_measurement', 'derived_observation', 'geometry', 'contact', 'camera', 'declaration']},
             'claim': {'enum': ['observation', 'geometry', 'identity', 'presence', 'initial_support', 'support_link', 'violation', 'static_negative', 'scope_boundary', 'exclusion']},
             'truth': {'enum': ['T', 'F', 'U']},
             'validity': {'enum': ['verified', 'missing', 'invalid_local', 'invalid_contract', 'contradictory']},
             'object_id': {'oneOf': [identifier, {'const': '*'}]}, 'execution_id': identifier, 'synthetic': {'const': True},
             'profile_version': {'const': '1.0.0'}, 'requirement_version': {'const': '2.0.0'},
             'surfaces': strings, 'interval': interval, 'cells': strings, 'dependencies': strings,
             'source_ref': text, 'producer': text,
             'frame': obj({'id': text, 'clock': text, 'length_unit': text, 'time_unit': text, 'handedness': text}),
             'uncertainty': obj({'temporal': {'type': ['number', 'null'], 'minimum': 0}, 'description': strings}),
             'payload': {'type': 'object'}}
    record = obj(props)
    payloads = {
        'direct_measurement': obj({'quantity': text, 'values': array(number), 'unit': text}),
        'derived_observation': obj({'quantity': text, 'values': array(number), 'unit': text}),
        'geometry': obj({'shape': text, 'dimensions': {'type': 'array', 'items': number, 'minItems': 3, 'maxItems': 3}, 'static': {'type': 'boolean'}, 'horizontal': {'type': 'boolean'}, 'complete': {'type': 'boolean'}}),
        'contact': obj({'pairs': array({'type': 'array', 'items': text, 'minItems': 2, 'maxItems': 2}), 'complete': {'type': 'boolean'}, 'forces': {'oneOf': [{'type': 'null'}, array(number)]}}),
        'camera': obj({'camera_id': text, 'indices': array({'type': 'integer', 'minimum': 0}, True), 'decoded': array({'type': 'integer', 'minimum': 0}, True), 'inspected': array({'type': 'integer', 'minimum': 0}, True)}),
    }
    declarations = {
        'identity': obj({'instance_id': text}), 'presence': obj({'closed_roster': {'type': 'boolean'}}),
        'initial_support': obj({'chain': array(text), 'all_support_excluded': {'type': 'boolean'}}),
        'support_link': obj({'child': text, 'parent': text}),
        'violation': obj({'origin': {'enum': ['T', 'F', 'U']}, 'loss': {'enum': ['T', 'F', 'U']}, 'downward': {'enum': ['T', 'F', 'U']}, 'handling_excluded': {'enum': ['T', 'F', 'U']}, 'onset': interval, 'downward_interval': interval}),
        'static_negative': obj({'method': text}), 'scope_boundary': obj({'reason': text}), 'exclusion': obj({'reason': text}),
    }
    record['allOf'] = [{'if': {'properties': {'kind': {'const': kind}}}, 'then': {'properties': {'payload': schema}}} for kind, schema in payloads.items()]
    record['allOf'] += [{'if': {'properties': {'kind': {'const': 'declaration'}, 'claim': {'const': claim}}}, 'then': {'properties': {'payload': schema}}} for claim, schema in declarations.items()]
    schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:trustworthy:r1:v4:evidence:1.0.0', **obj({'evidence_version': {'const': '1.0.0'}, 'records': array(record), 'conflicts': array(obj({'left': text, 'right': text, 'reason': text}))})}
    artifacts = {'evidence.schema.json': schema,
                 'adapter.json': {'id': 'analytical-declarations', 'version': '1.0.0', 'synthetic_only': True, 'physical_measurement_inference': False},
                 'profile.json': {'id': 'analytical-static-box', 'version': '1.0.0', 'purpose': 'analytical_fixture', 'assumptions': 'Exact source-bound declared synthetic facts; no physical inference', 'coverage': 'explicit_static_cells_and_joins', 'temporal_uncertainty': 'unresolved_values_abstain'},
                 'capabilities.json': {'id': 'analytical-contract-capabilities', 'version': '1.0.0', 'scope': 'synthetic_declared_facts_only', 'empirical_enabled': False, 'geometry': ['box'], 'roots': 'static_horizontal', 'negative_composition': 'static_cells_only', 'certified': False}}
    outcome = {'enum': ['violation_observed', 'no_violation_observed_within_validated_coverage', 'not_applicable', 'insufficient_information', 'invalid_measurement_contract']}
    coverage = obj({k: strings for k in ['requested','available','admitted','negative','missing','dependencies','invalid','unobserved']})
    coverage['properties']['source_groups'] = {'type':'array'}
    coverage['required'].append('source_groups')
    assessment = obj({'object_id': text, 'surfaces': strings,
        'applicability': {'enum':['applicable','not_applicable','indeterminate','unsupported_evidence_contract']},
        'outcome': outcome, 'reasons': strings, 'evidence_ids': strings, 'coverage': coverage,
        'uncertainty': strings, 'complete': {'type':'boolean'}, 'scope_mismatch': {'type':'boolean'},
        'study_eligibility': text, 'execution_id': text, 'requirement_version': {'const':'2.0.0'},
        'checker_version': {'const':'4.0.0a1'}, 'adapter_version': text, 'profile_version': text,
        'validation_status': {'const':'synthetic_analytical_only'}})
    output = {'$schema':'https://json-schema.org/draft/2020-12/schema',
        '$id':'urn:trustworthy:r1:v4:assessment:1.0.0', 'type':'object',
        'required':['requirement_id','requirement_version','checker_version','configuration_hash',
                    'assessment_manifest','configuration_status','assessed','object_assessments',
                    'execution_outcome','physical_safety_conclusion','empirical_profiles_enabled'],
        'properties': {'requirement_id':{'const':'R1'}, 'requirement_version':{'const':'2.0.0'},
            'checker_version':{'const':'4.0.0a1'}, 'configuration_schema_version':{'const':'2.0.1'},
            'manifest_version':{'const':'1.0.0'}, 'evidence_schema_version':{'const':'1.0.0'},
            'assessment_schema_version':{'const':'1.0.0'},
            'configuration_hash':{'type':['string','null']}, 'assessment_manifest':{'type':['object','null']},
            'physical_safety_conclusion':{'const':False}, 'empirical_profiles_enabled':{'const':False},
            'synthetic':{'const':True}, 'object_assessments':array(assessment),
            'configuration_status':{'enum':['valid','invalid']}, 'assessed':{'type':'boolean'},
            'execution_outcome':{'oneOf':[outcome,{'type':'null'}]}},
        'allOf':[{'if':{'properties':{'assessed':{'const':False}}},
            'then':{'properties':{'configuration_status':{'const':'invalid'},'execution_outcome':{'type':'null'},'object_assessments':{'maxItems':0}},'required':['configuration_diagnostics']},
            'else':{'properties':{'configuration_status':{'const':'valid'},'execution_outcome':outcome},
                    'required':['admitted_evidence_ids','rejected_evidence','evidence_admission','missing_requirements','uncertainty','provenance','assessment_hash']}}]}
    artifacts['assessment.schema.json'] = output
    for name, value in artifacts.items():
        (here / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    generate()
