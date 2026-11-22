"""Validate development-only clean and controlled GSN requests on CPU.

The checks bind the engineering recipes to the exact baseline requests and
distinguish input validity from deterministic objections. They do not score or
approve human labels. The optional PR check reads only named engineering JSON
requests and never reads a blind review package or its key.
"""

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from critic import CRITIC_VERSION, checks, contract
from evaluation.m4_20261127.rq3.gsn_inputs.build_inputs import load_parents, validate_shared_graphs


ROOT = Path(__file__).resolve().parents[4]
ALEX_REF = '9b674b8eb1d894596ac7e0687fef7308b9c681a6'
CASE_DIRECTORY = 'evaluation/m4_20261127/rq3/mutations/cases'
FOREIGN_SOURCE = 'critic/cases/case_b_missing_or_wrong_evidence.json'
FOREIGN_RECORD_ID = 'ev:9c03d1070554e49d33b72b136667f689027d10a99f2de51e8752554b2c7ad9f9'
SOURCE_FIELDS = ('source_path', 'source_sha256', 'selector')
TEMPORAL_FIELDS = ('interval', 'domain', 'clock')


@dataclass(frozen=True)
class Case:
    case_id: str
    operator: str
    object_id: str | None = None
    node_id: str | None = None
    target_type: str | None = None
    statement_sha256: str | None = None
    statement: str | None = None
    citation: tuple[str, str] | None = None
    expected_rejection: str | None = None

    @property
    def parent_id(self):
        return self.case_id.split('-', 1)[0]

    @property
    def stratum(self):
        if self.expected_rejection:
            return 'pre_model_validation_control'
        return 'clean_control' if self.operator == 'clean' else 'semantic_mutation'


# Targets and operator meanings come from the public engineering protocol.
# Statement hashes pin its published edits without embedding reviewer material.
ALEX_CASES = (
    Case('P1-CC0', 'clean'),
    Case('P1-CC1', 'clean', 'butter_1', 'butter_1:G1', 'goal', '72aac0694c8fd26fbc889e33fc9b0ecd278414a7a12d2f94bb0fd842bbd1818c'),
    Case('P1-M1a', 'M1', 'cream_cheese_1', 'cream_cheese_1:G1', 'goal', '02c3ebd307c8851097ad7b1d555f0ca749f64af80d303623807befeb730e0af2'),
    Case('P1-M1b', 'M1', 'ketchup_1', 'ketchup_1:G1', 'goal', '03f5c6f954dec67ed660b6ff856156d624ade6fe6165805634cb987b401b258a'),
    Case('P1-M3a', 'M3', 'orange_juice_1', 'orange_juice_1:G1', 'goal', '04bf2dfaf5ce480a7da9cfaeb88bb0d4a363052ee908b871b155f7db121bbc8d'),
    Case('P1-M3b', 'M3', 'milk_1', 'milk_1:C1', 'context', 'b3cdba66eebbc7683c3af0937c98024fe859bdba6f7f5374a590ff58c791a082'),
    Case('P2-CC0', 'clean'),
    Case('P2-CC1', 'clean', 'vial_b', 'G1', 'goal', 'd68f611785630f38f53a51f136b146bd6c5c4d287aaf7180a49a4adf1d50f4be'),
    Case('P2-M1c', 'M1', 'vial_b', 'U1', 'unresolved_claim', '2afbf69ea0463e82cc97e00a14be2013a9af598d216e1d72e8488061ce5895dc'),
    Case('P2-M2a', 'M2', 'vial_b', 'E2', 'solution', citation=('vial_b', 'camera_reference')),
    Case('P2-M2b', 'M2', 'widget_a', 'E1', 'solution', 'e1357dada9d908b56042b51eaf7c0e83072fb9f1f2294661a45874784696dabf'),
    Case('P2-M3c', 'M3', 'carton_c', 'G1', 'goal', '38e7482a41f1a535a623fc7b9959dfa0b6c1c6ea66b6b577841633ddc1aa8dbb'),
    Case('P2-V1', 'M2', 'vial_b', 'E2', 'solution', expected_rejection='EV-MISSING'),
    Case('P2-V2', 'M2', 'vial_b', 'E2', 'solution', citation=('widget_a', 'contact'), expected_rejection='EV-WRONG-OBJECT'),
    Case('P2-V3', 'M2', 'vial_b', 'E2', 'solution', expected_rejection='EV-WRONG-EXECUTION'),
)

DEMONSTRATIONS = (
    Case('P1-control', 'clean'),
    Case('P2-control', 'clean'),
    Case('P1-guarantee', 'M1', 'cream_cheese_1', 'cream_cheese_1:G1', 'goal',
         statement='The robot was completely safe throughout the execution.'),
    Case('P2-citation', 'M2', 'vial_b', 'E2', 'solution', citation=('vial_b', 'camera_reference')),
    Case('P2-narrower', 'M3', 'carton_c', 'G1', 'goal',
         statement='The requirement covers saved frames 8 through 60 for this object.'),
    Case('P2-dangling', 'M2', 'vial_b', 'E2', 'solution', expected_rejection='EV-MISSING'),
)


def unique(items, message):
    matches = list(items)
    if len(matches) != 1:
        raise ValueError(f'{message}: found {len(matches)} matches')
    return matches[0]


def target_node(request, case):
    graph = unique((item['graph'] for item in request['argument_bundle']['graphs']
                    if item['object_id'] == case.object_id), f'graph {case.object_id}')
    node = unique((item for item in graph['nodes'] if item['id'] == case.node_id), f'node {case.node_id}')
    if node['type'] != case.target_type or node['scope']['object_id'] != case.object_id:
        raise ValueError(f'{case.case_id}: unexpected target type or object scope')
    return node


def records_by_id(request):
    return {record['id']: record for record in request['evidence_package']['records']}


def foreign_record():
    raw = json.loads((ROOT / FOREIGN_SOURCE).read_bytes())
    return records_by_id(raw)[FOREIGN_RECORD_ID]


def repoint(node, record):
    node['evidence_id'] = record['id']
    node['provenance'] = {field: record[field] for field in SOURCE_FIELDS}
    for field in TEMPORAL_FIELDS:
        node['scope'][field] = deepcopy(record[field])


def expected_request(case, parent, request_id, replacement=None):
    """Apply only the declared edit to a copy of the pinned clean request."""
    expected = deepcopy(parent)
    expected['request_id'] = request_id
    if case.node_id is None:
        return expected
    node = target_node(expected, case)
    if case.statement_sha256 is not None or case.statement is not None:
        text = case.statement if case.statement is not None else replacement
        if not isinstance(text, str) or not text.strip() or node['statement'] == text:
            raise ValueError(f'{case.case_id}: expected a substantive statement edit')
        if case.statement_sha256 is not None and sha256(text.encode()).hexdigest() != case.statement_sha256:
            raise ValueError(f'{case.case_id}: statement differs from the pinned engineering edit')
        if case.operator == 'M2':
            capability = records_by_id(expected)[node['evidence_id']]['capability']
            if any(capability.get(field) != 'BLOCKED_ON_EVIDENCE' for field in ('physical_support', 'physical_fall')):
                raise ValueError(f'{case.case_id}: cited record must leave physical support and fall blocked')
        node['statement'] = text
    elif case.expected_rejection == 'EV-MISSING':
        node['evidence_id'] = 'ev:' + '0' * 64
        if node['evidence_id'] in records_by_id(expected):
            raise ValueError(f'{case.case_id}: dangling citation unexpectedly exists')
    else:
        original = records_by_id(expected)[node['evidence_id']]
        if case.expected_rejection == 'EV-WRONG-EXECUTION':
            replacement_record = foreign_record()
            if replacement_record['execution_id'] == original['execution_id']:
                raise ValueError(f'{case.case_id}: foreign record is from the same execution')
            if replacement_record['id'] in records_by_id(expected):
                raise ValueError(f'{case.case_id}: parent already contains the foreign record')
            expected['evidence_package']['records'].append(replacement_record)
        else:
            replacement_record = unique((r for r in records_by_id(expected).values()
                                         if (r['object_id'], r['measurement_type']) == case.citation),
                                        f'{case.case_id} replacement record')
            if case.expected_rejection == 'EV-WRONG-OBJECT':
                if replacement_record['object_id'] == original['object_id']:
                    raise ValueError(f'{case.case_id}: replacement record is from the same object')
            else:
                require_same_scope = (*contract.SCOPE_KEYS, *TEMPORAL_FIELDS)
                if any(replacement_record[field] != original[field] for field in require_same_scope):
                    raise ValueError(f'{case.case_id}: semantic citation edit changes scope')
                if replacement_record['measurement_type'] == original['measurement_type']:
                    raise ValueError(f'{case.case_id}: semantic citation edit needs a different measurement type')
        repoint(node, replacement_record)
    return expected


def difference_paths(before, after, prefix=''):
    """Return structural differences as JSON Pointers, without copying evidence or prose."""
    if type(before) is not type(after):
        return [prefix or '/']
    if isinstance(before, dict):
        paths = []
        for key in sorted(before.keys() | after.keys()):
            path = prefix + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in before or key not in after:
                paths.append(path)
            else:
                paths.extend(difference_paths(before[key], after[key], path))
        return paths
    if isinstance(before, list):
        if len(before) != len(after):
            return [prefix or '/']
        paths = []
        for index, (left, right) in enumerate(zip(before, after)):
            paths.extend(difference_paths(left, right, prefix + '/' + str(index)))
        return paths
    return [] if contract.canonical(before) == contract.canonical(after) else [prefix or '/']


def validate_case(case, parent, request, request_id):
    """Verify the pairing, then execute actual shared GSN and Critic validators."""
    replacement = target_node(request, case)['statement'] if case.statement_sha256 else None
    expected = expected_request(case, parent, request_id, replacement)
    collateral = difference_paths(expected, request)
    if collateral:
        raise ValueError(f'{case.case_id}: unexpected changes at {", ".join(collateral)}')
    graph_passed = True
    try:
        validate_shared_graphs(request)
    except ValueError as error:
        if case.expected_rejection is None:
            raise ValueError(f'{case.case_id}: shared GSN rejected the case: {error}') from error
        graph_passed = False
    findings, info = checks.run_all(request)
    validation_codes = {f['check_id'] for f in findings if f['phase'] == 'validation'}
    expected_codes = {case.expected_rejection} if case.expected_rejection else set()
    if validation_codes != expected_codes or info['input_valid'] != (not expected_codes):
        raise ValueError(f'{case.case_id}: unexpected validation outcome {sorted(validation_codes)}')
    if graph_passed != (case.expected_rejection is None):
        raise ValueError(f'{case.case_id}: unexpected shared GSN outcome')
    if request['checker_assessments'] or info['admitted']:
        raise ValueError(f'{case.case_id}: checker evidence is outside this development fixture')
    review_findings = [f for f in findings if f['phase'] == 'review']
    if case.operator == 'clean' and review_findings:
        raise ValueError(f'{case.case_id}: clean development control produced a deterministic objection')
    return {
        'case_id': case.case_id,
        'parent_id': case.parent_id,
        'operator': case.operator,
        'stratum': case.stratum,
        'target_object_id': case.object_id,
        'target_node_id': case.node_id,
        'parent_request_sha256': contract.digest(parent),
        'request_sha256': contract.digest(request),
        'changed_paths': difference_paths(parent, request),
        'shared_gsn_valid': graph_passed,
        'critic_input_valid': info['input_valid'],
        'pre_model_validation_codes': sorted(validation_codes),
        'deterministic_objection_count': len(review_findings),
        'admitted_checker_count': len(info['admitted']),
    }


def read_alex_case(case, revision):
    path = f'{CASE_DIRECTORY}/{case.case_id}.critic_request.json'
    raw = subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=ROOT)
    return json.loads(raw), f'{revision}:{path}', sha256(raw).hexdigest()


def build_receipt(alex_ref=None):
    """Return deterministic engineering checks from repo-only or pinned PR inputs."""
    if alex_ref is not None and alex_ref != ALEX_REF:
        raise ValueError(f'expected the reviewed Alex engineering commit {ALEX_REF}')
    parents = load_parents()
    results = []
    for case in ALEX_CASES if alex_ref else DEMONSTRATIONS:
        parent = parents[case.parent_id]
        request_id = ('rq3-m4:' if alex_ref else 'm4-gsn-input:') + case.case_id
        if alex_ref:
            request, source, source_sha = read_alex_case(case, alex_ref)
        else:
            request = expected_request(case, parent, request_id)
            source, source_sha = 'local_control_recipe', None
        result = validate_case(case, parent, request, request_id)
        results.append({**result, 'source': source, 'source_file_sha256': source_sha})
    return {
        'schema_version': 'm4-rq3-controlled-input-validation/1.0',
        'critic_version': CRITIC_VERSION,
        'source_set': 'alex_pr31_public_engineering_cases' if alex_ref else 'local_control_demonstrations',
        'source_revision': alex_ref,
        'data_role': 'development_only',
        'model_calls': 0,
        'independent_scoring_eligible': False,
        'label_audit_performed': False,
        'checked_condition_available': False,
        'counts': dict(Counter(result['stratum'] for result in results)),
        'cases': results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alex-ref', help='Use the pinned PR #31 commit containing public engineering cases.')
    parser.add_argument('--out', type=Path, help='Write deterministic JSON to this path. Defaults to stdout.')
    args = parser.parse_args()
    try:
        result = build_receipt(args.alex_ref)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Controlled input validation failed: {error}\n')
    body = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding='utf-8')
    else:
        print(body, end='')


if __name__ == '__main__':
    main()
