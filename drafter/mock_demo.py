"""Explicit, deterministic mock demonstration; never invokes a model or network.

The source evidence is the unchanged archived metadata package. Fixed reasoning
templates illustrate the interface, not measured language-model performance.
The shared GSN schema and semantic validator still apply to every graph.
"""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
import uuid

from jsonschema import Draft202012Validator
from evaluation.r1_v4.provenance import digest
from .generation import (CHECK_NAMES, REVIEW_LIMITATION, SERIALIZER_VERSION,
                         _plan_schema, _serialize_plan, solution_statement)
from .validation import (ContractError, schema_issues, validate_request,
                         validate_argument_bundle)

GENERATOR_VERSION = 'mock-argument-generator/0.1.0'
MOCK_NOTICE = ('Mock demonstration only. Fixed program rules assembled this example; '
               'no language model was run and no model quality was measured.')
DEPLOYMENT_REASON = ('Live model deployment is deferred for this demonstration. '
                     'No model-server connection is configured or checked in mock '
                     'mode; fixed program rules demonstrate the graph interface.')


def _build_plan(request):
    config, window = request['requirement_configuration'], request['monitoring_scope']
    eligible = set(request['evidence_handling']['graph_eligible_evidence_ids'])
    start, end = window['interval']
    graphs = []
    for obj in config['protected_objects']:
        def node(key, kind, text, evidence_id=None):
            return {'id': obj + ':' + key, 'type': kind, 'statement': text,
                    'evidence_id': evidence_id,
                    'physical_claim': kind in ('goal', 'unresolved_claim')}

        nodes = [
            node('G1', 'goal', f'R1 remains unresolved for {obj} over saved frames {start}-{end}.'),
            node('S1', 'strategy', 'Check initial support and possible falling departures, retaining missing evidence.'),
            node('C1', 'context',
                 f"R1 {config['requirement_version']}; saved frames {start}-{end}, inclusive. "
                 'Designated surfaces: ' + ', '.join(config['object_surface_mapping'][obj]) +
                 '. The input provides archived metadata, not physical verification.'),
            node('G2', 'unresolved_claim',
                 f'Initial load-bearing support for {obj} at saved frame {start} remains unresolved. '
                 'The supplied package cannot establish applicability.'),
            node('G3', 'unresolved_claim',
                 f'A qualifying unsupported downward fall of {obj} in saved frames {start}-{end} '
                 'remains unresolved. No validated checker assessment is supplied.'),
        ]
        gaps = [g for g in request['retrieval_context']['gaps'] if g['object_id'] == obj]
        gap_text = ', '.join(f"{g['interval'][0]}-{g['interval'][1]}" for g in gaps) or 'none listed'
        nodes.append(node('U1', 'unresolved_claim',
                          'Whole-window R1 remains unresolved. Missing metadata intervals: '
                          + gap_text + '. Missing data is not evidence that no fall occurred.'))
        edges = [
            {'source': obj + ':G1', 'target': obj + ':S1', 'type': 'supported_by'},
            {'source': obj + ':G1', 'target': obj + ':C1', 'type': 'in_context_of'},
            *[{'source': obj + ':S1', 'target': obj + ':' + key, 'type': 'supported_by'}
              for key in ('G2', 'G3', 'U1')],
        ]
        records = sorted((r for r in request['evidence_package']['records']
                          if r['id'] in eligible and r['object_id'] == obj),
                         key=lambda r: (r['interval'], r['measurement_type'], r['id']))
        for index, record in enumerate(records, 1):
            key = 'E' + str(index)
            nodes.append(node(key, 'solution', solution_statement(record), record['id']))
            parent = 'G2' if record['interval'][0] == start else 'G3'
            edges.append({'source': obj + ':' + parent, 'target': obj + ':' + key,
                          'type': 'supported_by'})
        graphs.append({'object_id': obj, 'root_id': obj + ':G1', 'nodes': nodes, 'edges': edges})
    return {
        'graphs': graphs,
        'summary': ('Mock demonstration: R1 remains unresolved for all '
                    f"{len(config['protected_objects'])} protected objects. "
                    'The supplied metadata cannot establish initial support or qualifying falls.'),
        'limitations': [MOCK_NOTICE, REVIEW_LIMITATION],
    }


def _mock_provenance(plan):
    return {'generator_version': GENERATOR_VERSION, 'serializer_version': SERIALIZER_VERSION,
            'template_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'plan_sha256': digest(plan), 'plan': plan}


def validate_mock_demo(demo, request):
    """Validate an explicit mock without granting it live-model acceptance."""
    validate_request(request)
    issues = schema_issues(demo, 'mock_demo.schema.json')
    if issues:
        raise ContractError(issues)
    for field, expected in (
        ('request_id', request['request_id']), ('request_sha256', digest(request)),
        ('requirement_configuration_sha256', request['requirement_configuration_sha256']),
        ('evidence_package_sha256', request['evidence_package_sha256']),
    ):
        if demo[field] != expected:
            issues.append('mock_input_binding:' + field)
    expected_plan = _build_plan(request)
    provenance = _mock_provenance(expected_plan)
    if demo['mock_provenance'] != provenance:
        issues.append('mock_plan_or_generator_binding')
    expected_bundle = _serialize_plan(expected_plan, request, provenance, mock=True)
    if demo['argument_bundle'] != expected_bundle:
        issues.append('mock_argument_plan_binding')
    if demo['deployment_reason'] != DEPLOYMENT_REASON or demo['summary'] != expected_plan['summary']:
        issues.append('mock_description_binding')
    required_limits = {MOCK_NOTICE, REVIEW_LIMITATION, *request['limitations']}
    if not required_limits <= set(demo['limitations']):
        issues.append('mock_missing_limitations')
    if issues:
        raise ContractError(issues)
    validate_argument_bundle(demo['argument_bundle'], request)
    return {'contract_status': 'valid_mock_demonstration', 'model_called': False,
            'live_model_result': False, 'physical_sufficiency': 'not_assessed',
            'safety_claim_verified': False}


def run_mock_demo(request):
    """Exercise the graph interface using fixed rules; never select a model."""
    started = time.monotonic()
    report = {
        'schema_version': 'drafter-mock-run/0.1.0', 'mode': 'mock_demonstration',
        'status': 'rejected', 'run_id': str(uuid.uuid4()),
        'started_at': datetime.now(timezone.utc).isoformat(),
        'deployment_status': 'blocked', 'deployment_reason': DEPLOYMENT_REASON,
        'model_called': False, 'live_model_result': False, 'project_evidence_sent': False,
        'argument_generated': False, 'argument': None, 'diagnostics': [],
        'empirical_admission_enabled': False, 'safety_claim_verified': False,
    }
    try:
        validate_request(request)
        plan = _build_plan(request)
        errors = list(Draft202012Validator(_plan_schema(request)).iter_errors(plan))
        if errors:
            raise ContractError(['mock_plan_schema:' + '/'.join(map(str, e.absolute_path)) for e in errors])
        provenance = _mock_provenance(plan)
        argument = {
            'schema_version': 'drafter-mock-demo/0.1.0', 'mode': 'mock_demonstration',
            'generation_status': 'mock_demonstration', 'deployment_status': 'blocked',
            'deployment_reason': DEPLOYMENT_REASON, 'run_id': report['run_id'],
            'request_id': request['request_id'], 'test_fixture': True,
            'request_sha256': digest(request),
            'requirement_configuration_sha256': request['requirement_configuration_sha256'],
            'evidence_package_sha256': request['evidence_package_sha256'],
            'model_called': False, 'live_model_result': False, 'model_id': None,
            'prompt_sha256': None, 'mock_provenance': provenance,
            'argument_bundle': _serialize_plan(plan, request, provenance, mock=True),
            'summary': plan['summary'],
            'limitations': list(dict.fromkeys([
                MOCK_NOTICE, 'The archived-package limitations below describe the supplied input.',
                *request['limitations'], REVIEW_LIMITATION])),
            'validation': {**{key: 'passed' for key in CHECK_NAMES},
                           'physical_sufficiency': 'not_assessed'},
            'empirical_admission_enabled': False, 'safety_claim_verified': False,
        }
        validate_mock_demo(argument, request)
        report.update(status='mock_demonstration', argument=argument, argument_generated=True)
    except (ContractError, ValueError, TypeError, OSError, RecursionError) as error:
        issues = error.issues if isinstance(error, ContractError) else [str(error)]
        report['diagnostics'] = [{'code': 'mock_rejected', 'path': 'mock_demo', 'message': issue}
                                 for issue in issues]
    report['elapsed_seconds'] = round(time.monotonic() - started, 6)
    return report
