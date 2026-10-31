"""Phase 1 document/configuration QA only. No event checker or V4 implementation.

Execute on Hestia with jsonschema. This tool does not open trajectories or produce
new physical labels, predictions or calibration values.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import socket
import sys
from urllib.parse import unquote

import jsonschema

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE = '30b4ac9cc8e2a1d0e83f72ee74d31f77829e62c1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path):
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result:
                raise ValueError('Duplicate JSON key: '+k)
            result[k] = v
        return result
    def invalid(value):
        raise ValueError('Nonstandard JSON constant: '+value)
    return json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def lint_example(value, validator):
    """Test-only specification linting; never admits a measurement contract."""
    errors = [e.message for e in validator.iter_errors(value)]
    if errors:
        return errors
    objects = value['protected_objects']
    mapping = value['object_surface_mapping']
    surfaces = [s['id'] for s in value['support_surfaces']]
    if len(set(surfaces)) != len(surfaces):
        errors.append('Duplicate surface identifiers')
    if set(objects) != set(mapping):
        errors.append('Protected objects and mapping keys differ')
    if any(s not in surfaces for targets in mapping.values() for s in targets):
        errors.append('Dangling designated surface')
    if any(o in targets for o,targets in mapping.items()):
        errors.append('Object cannot designate itself as support root')
    if any(x != x.strip() for x in objects+surfaces+list(mapping)):
        errors.append('Whitespace in identifier')
    interval = value['monitoring_interval']
    a,b = interval['start'],interval['end']
    if a['kind'] == 'terminal_recorded_snapshot' or b['kind'] == 'recorded_first_policy_boundary':
        errors.append('Invalid boundary role')
    expected = 'explicit_index' if interval['axis']=='saved_frame' else 'explicit_time'
    if any(x['kind'].startswith('explicit_') and x['kind']!=expected for x in [a,b]):
        errors.append('Boundary axis mismatch')
    if a['kind']==b['kind']==expected and a['value']>b['value']:
        errors.append('Reversed explicit interval')
    support=value['initial_support_rules']
    if support['profile']=='legacy_v3_static_stencil' and support['boundary_context_offsets']!=[-1,0,1]:
        errors.append('Legacy stencil must remain -1,0,+1')
    manifest=value['assessment_manifest']
    if manifest['requirement']['id']!=value['requirement_id'] or manifest['requirement']['version']!=value['requirement_version']:
        errors.append('Manifest requirement mismatch')
    if manifest['configuration_schema']['id']!='urn:trustworthy:r1:generalized:configuration:2.0.1' or manifest['configuration_schema']['version']!='2.0.1':
        errors.append('Manifest configuration schema mismatch')
    if manifest['adapter']['id']!=value['benchmark']['adapter_id'] or manifest['adapter']['version']!=value['benchmark']['adapter_version']:
        errors.append('Manifest adapter mismatch')
    if manifest['requested_domain']['projection']!=value['temporal_alignment']['domain']:
        errors.append('Manifest observation domain mismatch')
    if manifest['source_model_bindings']!=value['source_bindings']:
        errors.append('Manifest source bindings mismatch')
    return errors


def main(output):
    if socket.gethostname().lower() != 'hestia':
        raise RuntimeError('Run Phase 1 research QA on Hestia')
    checks = []
    errors = []
    required = ['README.md','CURRENT_R1_AUDIT.md','R1_V2_SPECIFICATION.md','FORMAL_SEMANTICS.md',
        'APPLICABILITY_RULES.md','FALL_DEFINITION.md','EVIDENCE_CONTRACT.md','R1_V2_CONFIG_SCHEMA.json',
        'V3_COMPATIBILITY.md','V4_IMPLEMENTATION_PLAN.md','V4_TEST_MATRIX.md','VALIDITY_THREATS.md','OPEN_DECISIONS.md']
    for n in required:
        if not (HERE/n).is_file():
            errors.append('Missing deliverable '+n)
    checks.append('Required Phase 1 deliverables exist')
    schema = strict_json(HERE/'R1_V2_CONFIG_SCHEMA.json')
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    checks.append('Draft 2020-12 schema meta-validation')
    examples = sorted((HERE/'EXAMPLE_CONFIGS').glob('*.json'))
    if len(examples)<3:
        errors.append('Need at least three illustrative examples')
    for p in examples:
        example = strict_json(p)
        issues = lint_example(example,validator)
        if issues:
            errors.extend(p.name+': '+x for x in issues)
        if example['validation_status']!='illustrative_unvalidated':
            errors.append('Example claims validated evidence')
        numeric = example['fall_detection_rules']['numeric_policy']
        if any(numeric[k] is not None for k in ['physical_distance_uncertainty_m','persistence_window_s','hysteresis_m','calibration_ref']):
            errors.append('Example invents calibration')
    checks.append('All illustrative examples pass schema and semantic-reference linting')
    seed = strict_json(examples[0])
    mutation_tests = []
    def check(name, value, valid):
        issues=lint_example(value,validator)
        passed=(not issues)==valid
        mutation_tests.append(dict(name=name,passed=passed,expected='accept_structure_only' if valid else 'reject'))
        if not passed:
            errors.append('Configuration fixture failed: '+name)
    for count in [0,1,3,5]:
        v=copy.deepcopy(seed)
        v['protected_objects']=v['protected_objects'][:count]
        v['object_surface_mapping']={o:v['object_surface_mapping'][o] for o in v['protected_objects']}
        if count==0:
            v['support_surfaces']=[]
        check('cardinality_'+str(count),v,True)
    def mutated(name, edit):
        v=copy.deepcopy(seed)
        edit(v)
        check(name,v,False)
    first=seed['protected_objects'][0]
    mutated('duplicate_object',lambda v:v['protected_objects'].append(first))
    mutated('duplicate_surface',lambda v:v['support_surfaces'].append(copy.deepcopy(v['support_surfaces'][0])))
    mutated('missing_mapping',lambda v:v['object_surface_mapping'].pop(first))
    mutated('extra_mapping',lambda v:v['object_surface_mapping'].update({'UNKNOWN_OBJECT':['living_room_table']}))
    mutated('empty_surface_set',lambda v:v['object_surface_mapping'].update({first:[]}))
    mutated('dangling_surface',lambda v:v['object_surface_mapping'].update({first:['UNKNOWN_SURFACE']}))
    mutated('wrong_axis',lambda v:v['monitoring_interval'].update({'axis':'simulator_time'}))
    mutated('reversed_interval',lambda v:v['monitoring_interval'].update({'end':{'kind':'explicit_index','value':9}}))
    mutated('negative_frame',lambda v:v['monitoring_interval']['start'].update({'value':-1}))
    mutated('wrong_start_anchor',lambda v:v['monitoring_interval'].update({'start':{'kind':'terminal_recorded_snapshot','value':None}}))
    mutated('unjustified_physical_tolerance',lambda v:v['fall_detection_rules']['numeric_policy'].update({'hysteresis_m':0.001}))
    mutated('false_validated_contract',lambda v:v.update({'validation_status':'validated_contract'}))
    mutated('intersample_claim',lambda v:v['temporal_alignment'].update({'claim_intersample_observation':True}))
    mutated('missing_as_negative',lambda v:v['uncertainty_policy'].update({'missing_is_negative':True}))
    mutated('missing_as_nonapplicable',lambda v:v['uncertainty_policy'].update({'missing_is_nonapplicable':True}))
    mutated('unknown_property',lambda v:v.update({'unreviewed_override':True}))
    mutated('unsupported_version',lambda v:v.update({'requirement_version':'3.0.0'}))
    mutated('robot_surface_role',lambda v:v['support_surfaces'][0].update({'role':'robot_gripper'}))
    mutated('legacy_stencil_drift',lambda v:v['initial_support_rules'].update({'profile':'legacy_v3_static_stencil','boundary_context_offsets':[0]}))
    mutated('missing_manifest',lambda v:v.pop('assessment_manifest'))
    mutated('manifest_unknown_version',lambda v:v['assessment_manifest'].update(manifest_version='2.0.0'))
    mutated('manifest_requirement_mismatch',lambda v:v['assessment_manifest']['requirement'].update(version='1.0.0'))
    mutated('manifest_config_mismatch',lambda v:v['assessment_manifest']['configuration_schema'].update(version='2.0.0'))
    mutated('manifest_adapter_mismatch',lambda v:v['assessment_manifest']['adapter'].update(version='wrong'))
    mutated('manifest_domain_mismatch',lambda v:v['assessment_manifest']['requested_domain'].update(projection='validated_continuous'))
    mutated('manifest_source_mismatch',lambda v:v['assessment_manifest'].update(source_model_bindings=[]))
    mutated('manifest_bad_hash',lambda v:v['assessment_manifest']['checker'].update(sha256='not-a-hash'))
    mutated('manifest_unknown_purpose',lambda v:v['assessment_manifest'].update(purpose='certified'))
    mutated('manifest_missing_checker',lambda v:v['assessment_manifest'].pop('checker'))
    checks.append('Analytical configuration acceptance/rejection fixtures only; no V4 event tests executed')
    link_count=0
    for p in HERE.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('https:','http:','mailto:')):
                continue
            name, _, anchor = target.partition('#')
            f=(p.parent/unquote(name)).resolve() if name else p
            if not f.is_file():
                errors.append('Broken reference '+str(p.relative_to(HERE))+' -> '+target)
            elif re.fullmatch(r'L\d+',anchor) and int(anchor[1:])>len(f.read_text().splitlines()):
                errors.append('Source line anchor beyond EOF '+target)
            link_count+=1
    checks.append('Internal relative links and source-line anchor bounds')
    bindings = strict_json(HERE/'AUDIT_SOURCE_BINDINGS.json')
    for n,digest in bindings['files'].items():
        if sha(REPO/n)!=digest:
            errors.append('Audited baseline source changed: '+n)
    checks.append('Audited source snapshots match baseline hashes')
    spec=(HERE/'R1_V2_SPECIFICATION.md').read_text()
    formal=(HERE/'FORMAL_SEMANTICS.md').read_text()
    for outcome in ['violation_observed','no_violation_observed_within_validated_coverage',
                    'not_applicable','insufficient_information','invalid_measurement_contract']:
        if outcome not in spec or outcome not in formal:
            errors.append('Outcome vocabulary mismatch: '+outcome)
    for i in range(1,12):
        if '| D%02d |'%i not in (HERE/'OPEN_DECISIONS.md').read_text():
            errors.append('Missing decision D%02d'%i)
    checks.append('Normative outcome vocabulary and D01-D11 register consistency')
    live={}
    paths={
        '/disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3/r1_checker.py':'d2914d64596f585a60021f426eb761439d604907450ebf318ca48590db0fc94f',
        '/disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3/execute.py':'e94ad1c34c47826a6e8a2a1b4b90543268a19d41045611c17a45287c45497cbc',
        '/disk/1/data/niktakbr/r1-checker-v3-20261027/evaluation/r1_v3/config.json':'fd3464dc0ee0ac44ee81c325e951832896eab489517aeed0a715f8e4d0088375',
        '/disk/1/data/niktakbr/r1-v3-generalization-20261027/execution/predictions.json':'0ef93ece9c3d0cb02a49a450979315a4e3be3d5f127aa48105970321f5b34984'}
    for n,digest in paths.items():
        if Path(n).is_file():
            actual=sha(Path(n));live[n]=dict(sha256=actual,matches=actual==digest)
            if actual!=digest:
                errors.append('Frozen Hestia artifact changed: '+n)
        else:
            live[n]=dict(accessible=False)
            errors.append('Expected accessible Hestia artifact missing: '+n)
    for folder,name,expected in [('assessment','AI_EVALUATOR_3_SEAL.json','52d84dc7440ba256b87e9f5a59f1df201da291c04fedf368da4474ebb5711c73'),
                                 ('comparison','AI_REFERENCE_SEAL.json','6351e474de196fb7d0c801989921765b9e66686c54c003e0b15372db4e7cca4b')]:
        d=Path('/disk/1/data/niktakbr/trustworthy-ai3-preserved-20261030')/folder
        seal=d/name
        if sha(seal)!=expected:
            errors.append('Historical seal changed '+name)
        contents=strict_json(seal)
        for n,digest in contents['files'].items():
            if sha(d/n)!=digest:
                errors.append('Historical sealed file changed '+n)
        live[str(seal)]=dict(sha256=sha(seal),members_verified=len(contents['files']))
    review=Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027')
    protected=strict_json(review/'SCORING_FREEZE.json')['files']
    if any(sha(review/n)!=h for n,h in protected.items()):
        errors.append('Human-scoring protected file changed')
    checks.append('Live Hestia V3 artifacts, historical seals and eight human-scoring protected files')
    report=dict(passed=not errors,errors=errors,checks=checks,configuration_fixtures=mutation_tests,
        configuration_fixture_count=len(mutation_tests),examples_checked=len(examples),relative_links_checked=link_count,
        audited_source_files=len(bindings['files']),baseline_commit=BASE,host=socket.gethostname(),
        checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_package_sha256={str(p.relative_to(HERE)):sha(p) for p in HERE.rglob('*') if p.is_file() and p.suffix in ['.md','.json','.py']},
        frozen_hestia_checks=live,human_scoring_protected_files_verified=len(protected),
        V4_implemented=False,V4_physical_tests_run=False,new_empirical_evaluation_run=False,
        semantic_review='Manual review of proposed definitions/precedence and open decisions; automated checks do not prove physical semantics.')
    if output.exists():
        raise FileExistsError('Choose a new QA output file')
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','errors','configuration_fixture_count','examples_checked','relative_links_checked','audited_source_files']},indent=2))
    if errors:
        raise SystemExit(1)


if __name__=='__main__':
    main(Path(sys.argv[1]))
