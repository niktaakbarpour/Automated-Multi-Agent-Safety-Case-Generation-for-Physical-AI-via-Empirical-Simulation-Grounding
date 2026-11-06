"""Generate an unresolved fixture argument and validate the final shared GSN.

The model chooses a compact graph plan. A deterministic serializer attaches
authoritative scope and source metadata; it never repairs missing graph structure
or invents an evidence reference. Accepted is structural acceptance only.
"""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
import uuid

from jsonschema import Draft202012Validator
from evaluation.r1_v4.provenance import canonical, digest
from .llm import ConfigError, LocalModelClient
from .validation import ContractError, read_json, validate_request, validate_argument
from .argument_checks import (authoritative_summary, authoritative_limitations,
                              authoritative_conclusion, REVIEW_WARNING,
                              graph_structure_issues, solution_statement)
from .plan_schema import build_plan_schema, validate_plan_prose

PROMPT_VERSION = 'draft-argument-prompt/0.2.1'
SERIALIZER_VERSION = 'graph-plan-to-gsn/0.2.0'
HERE = Path(__file__).resolve().parent
CHECK_NAMES = ('input_schema', 'input_semantics', 'output_schema',
               'graph_semantics', 'evidence_references')
REVIEW_LIMITATION = ('Graph and reference checks do not verify the scientific correctness '
                     'of proposed reasoning. Review the statements before submission.')


def _model_input(request):
    eligible = set(request['evidence_handling']['graph_eligible_evidence_ids'])
    fields = ('id', 'kind', 'measurement_type', 'requirement_id', 'requirement_version',
              'execution_id', 'object_id', 'interval', 'clock', 'domain',
              'source_path', 'source_sha256', 'selector', 'validation_status',
              'capability', 'limitations', 'uncertainty')
    catalogue = []
    for record in request['evidence_package']['records']:
        if record['id'] in eligible:
            item = {key: deepcopy(record[key]) for key in fields}
            item['solution_statement'] = solution_statement(record)
            catalogue.append(item)
    payload = {
        'request_id': request['request_id'], 'request_sha256': digest(request),
        'requirement_configuration': deepcopy(request['requirement_configuration']),
        'target_execution': deepcopy(request['target_execution']),
        'monitoring_scope': deepcopy(request['monitoring_scope']),
        'eligible_evidence_catalogue': catalogue,
        'context_only_evidence_ids': request['evidence_handling']['context_only_evidence_ids'],
        'retrieval_context': deepcopy(request['retrieval_context']),
        'checker_context': deepcopy(request['checker_context']),
        'limitations': list(request['limitations']),
        'physical_outcome': 'insufficient_information',
    }
    if request.get('structured_evidence'):
        from .phase5_adapter import evidence_context
        payload['structured_evidence'] = evidence_context(request)
    return payload


def _plan_schema(request):
    return build_plan_schema(request)


def _serialize_plan(plan, request, provenance, *, mock=False):
    """Attach authoritative fields; reject structural omissions, never repair."""
    config, target, window = (request['requirement_configuration'], request['target_execution'],
                              request['monitoring_scope'])
    roster = config['protected_objects']
    objects = [g['object_id'] for g in plan['graphs']]
    if objects != roster:
        raise ContractError(['plan_object_roster_or_order'])
    records = {r['id']: r for r in request['evidence_package']['records']}
    eligible = set(request['evidence_handling']['graph_eligible_evidence_ids'])
    graphs, global_ids = [], set()
    for value in plan['graphs']:
        object_id = value['object_id']
        ids = [n['id'] for n in value['nodes']]
        if (len(ids) != len(set(ids)) or global_ids.intersection(ids)
                or any(not key.startswith(object_id + ':') for key in ids)):
            raise ContractError(['plan_node_identity:' + object_id])
        global_ids.update(ids)
        shape_issues = graph_structure_issues(value, object_id, prefix='plan')
        if shape_issues:
            raise ContractError(shape_issues)
        nodes, cited = [], set()
        for n in value['nodes']:
            node = deepcopy(n)
            if node['physical_claim'] != (node['type'] in ('goal', 'unresolved_claim')):
                raise ContractError(['plan_physical_claim_type:' + node['id']])
            node['scope'] = {
                'requirement_id': config['requirement_id'],
                'requirement_version': config['requirement_version'],
                'execution_id': target['execution_id'], 'object_id': object_id,
                'domain': window['domain'], 'clock': window['clock'],
                'interval': list(window['interval']),
            }
            node['origin'] = 'unresolved_conclusion' if mock else 'llm_proposal'
            node['validation_status'] = 'unresolved' if node['physical_claim'] else 'proposed'
            node['provenance'] = ({
                'generator_version': provenance['generator_version'],
                'template_sha256': provenance['template_sha256'],
                'plan_sha256': provenance['plan_sha256'], 'request_sha256': digest(request),
                'serializer_version': SERIALIZER_VERSION, 'role': 'deterministic_mock',
                'model_called': False,
            } if mock else {
                'run_id': provenance['run_id'], 'prompt_sha256': provenance['prompt_sha256'],
                'request_sha256': digest(request), 'serializer_version': SERIALIZER_VERSION,
                'role': 'proposed_reasoning_not_verified_physical_evidence',
                'prose_review': 'required',
            })
            if node['type'] == 'solution':
                record = records.get(node['evidence_id'])
                if (node['evidence_id'] not in eligible or record is None
                        or record['object_id'] != object_id):
                    raise ContractError(['plan_ineligible_solution:' + node['id']])
                if node['statement'] != solution_statement(record):
                    raise ContractError(['plan_solution_statement_mismatch:' + node['id']])
                cited.add(record['id'])
                node['scope'].update(interval=list(record['interval']),
                                     domain=record['domain'], clock=record['clock'])
                node['provenance'] = {k: deepcopy(record[k]) for k in
                                      ('source_path', 'source_sha256', 'selector')}
                # Preserve the original metadata, capabilities and interpretation limits.
                node['provenance']['registry_record'] = deepcopy(record)
                node['origin'] = 'retrieved_observation'
                node['validation_status'] = record['validation_status']
            elif node['evidence_id'] is not None:
                raise ContractError(['plan_evidence_id_only_on_solution:' + node['id']])
            else:
                node['provenance']['prose_review'] = 'required'
            nodes.append(node)
        available = {key for key in eligible if records[key]['object_id'] == object_id}
        if available and not cited:
            raise ContractError(['plan_missing_available_evidence:' + object_id])
        graphs.append({'object_id': object_id, 'graph': {
            'schema_version': '1.0.0', 'nodes': nodes, 'edges': deepcopy(value['edges']),
            'empirical_admission_enabled': False,
        }})
    return {'execution_id': target['execution_id'], 'protected_objects': list(roster),
            'graphs': graphs, 'execution_conclusion': {
                'claimed_outcome': 'insufficient_information',
                'statement': authoritative_conclusion(),
                'object_outcomes': {obj: 'insufficient_information' for obj in roster},
            }}


def _envelope(request, run_id):
    return {
        'schema_version': 'draft-argument/0.1.0', 'request_id': request['request_id'],
        'test_fixture': request['test_fixture'], 'request_sha256': digest(request),
        'requirement_configuration_sha256': request['requirement_configuration_sha256'],
        'evidence_package_sha256': request['evidence_package_sha256'],
        'generation_status': 'failed', 'argument_bundle': None,
        'summary': 'No accepted argument was generated.',
        'limitations': list(dict.fromkeys([*request['limitations'], REVIEW_LIMITATION])),
        'diagnostics': [], 'validation': {
            **{name: 'not_run' for name in CHECK_NAMES}, 'physical_sufficiency': 'not_assessed'},
        'generation_provenance': {
            'backend': 'not_run', 'model_id': None, 'model_revision': None,
            'prompt_version': None, 'prompt_sha256': None, 'run_id': run_id,
            'raw_output_sha256': None},
        'empirical_admission_enabled': False, 'safety_claim_verified': False,
    }


def generate_argument(request, config):
    """One explicit model attempt for a valid archived fixture; no retries/fallback.

    Returns a trace report containing a DraftArgument for valid input, including
    valid failure envelopes. Invalid input has no argument and triggers no network.
    Model prose remains proposed reasoning requiring review even when accepted.
    """
    started = time.monotonic()
    run_id = str(uuid.uuid4())
    report = {
        'schema_version': 'drafter-generation-run/0.1.0', 'run_id': run_id,
        'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'failed',
        'configuration': None, 'configuration_sha256': None,
        'request_sha256': None, 'argument': None, 'diagnostics': [],
        'trace': {'serializer_version': SERIALIZER_VERSION, 'prompt_version': PROMPT_VERSION,
                  'messages': None, 'prompt_sha256': None, 'json_schema': None,
                  'discovery': None, 'completion': None},
        'model_called': False, 'completion_attempted': False,
        'argument_generated': False, 'project_evidence_sent': False,
        'empirical_admission_enabled': False, 'safety_claim_verified': False,
    }
    stage = 'input'
    argument = None
    try:
        validate_request(request)
        report['request_sha256'] = digest(request)
        argument = _envelope(request, run_id)
        argument['validation'].update(input_schema='passed', input_semantics='passed')
        report['argument'] = argument
        stage = 'configuration'
        client = LocalModelClient(config)
        report['configuration'] = config.public_settings()
        report['configuration_sha256'] = digest(report['configuration'])
        schema = _plan_schema(request)
        messages = [
            {'role': 'system', 'content': (HERE / 'prompts' / 'draft_argument_v1.md').read_text(encoding='utf-8')},
            {'role': 'user', 'content': canonical(_model_input(request)).decode('utf-8')},
        ]
        report['trace'].update(messages=messages, prompt_sha256=digest(messages), json_schema=schema)
        argument['generation_provenance'].update(
            model_id=config.model_id, model_revision=config.model_revision,
            prompt_version=PROMPT_VERSION, prompt_sha256=digest(messages))
        stage = 'discovery'
        discovery = client.discover_models()
        report['trace']['discovery'] = asdict(discovery)
        if discovery.status != 'ok' or not discovery.configured_model_available:
            raise ConfigError(discovery.error_code or 'configured_model_unavailable',
                              discovery.message or 'The selected model is unavailable; no fallback selected.')
        stage = 'completion'
        report['completion_attempted'] = True
        report['model_called'] = None
        report['project_evidence_sent'] = None
        completion = client.complete(messages, schema, schema_name='drafter_graph_plan')
        report['trace']['completion'] = asdict(completion)
        received = (isinstance(completion.raw_response, dict)
                    and isinstance(completion.raw_response.get('choices'), list))
        if received:
            report['model_called'] = True
            report['project_evidence_sent'] = True
            argument['generation_provenance']['backend'] = 'local_llm'
        if completion.text is not None:
            argument['generation_provenance']['raw_output_sha256'] = hashlib.sha256(completion.text.encode()).hexdigest()
        if completion.status != 'ok':
            raise ConfigError(completion.error_code or 'completion_failed',
                              completion.message or 'The model did not return a complete JSON object.')
        if completion.response_redacted:
            raise ConfigError('redacted_completion', 'The response required redaction; no graph was accepted.')
        stage = 'plan'
        errors = list(Draft202012Validator(schema).iter_errors(completion.parsed_json))
        if errors:
            raise ContractError(['plan_schema:' + '/'.join(map(str, e.absolute_path)) for e in errors])
        argument['validation']['output_schema'] = 'passed'
        stage = 'serialization'
        validate_plan_prose(completion.parsed_json)
        bundle = _serialize_plan(completion.parsed_json, request, argument['generation_provenance'])
        candidate = deepcopy(argument)
        candidate.update(
            generation_status='accepted', argument_bundle=bundle,
            summary=authoritative_summary(request),
            limitations=authoritative_limitations(request),
            reasoning_review={'status': 'required', 'warning': REVIEW_WARNING,
                              'summary': completion.parsed_json['summary'],
                              'limitations': deepcopy(completion.parsed_json['limitations'])})
        candidate['validation'].update({name: 'passed' for name in CHECK_NAMES})
        if request.get('structured_evidence'):
            from .phase5_adapter import evidence_context
            candidate['evidence_context'] = evidence_context(request)
        stage = 'graph_validation'
        validate_argument(candidate, request)
        report.update(status='accepted', argument=candidate, argument_generated=True)
    except (ContractError, ConfigError, ValueError, TypeError, OSError, RecursionError) as error:
        rejected = stage in ('input', 'plan', 'serialization', 'graph_validation')
        report['status'] = 'rejected' if rejected else 'failed'
        codes = error.issues if isinstance(error, ContractError) else [getattr(error, 'code', 'generation_error')]
        report['diagnostics'] = [{'code': code, 'path': stage,
                                  'message': str(error) if not isinstance(error, ContractError) else code}
                                 for code in codes]
        if argument is not None:
            argument['generation_status'] = report['status']
            argument['diagnostics'] = deepcopy(report['diagnostics'])
            if stage == 'plan':
                argument['validation']['output_schema'] = 'failed'
            if stage in ('serialization', 'graph_validation'):
                evidence_error = any(any(part in code for part in (
                    'ineligible_solution', 'solution_statement_mismatch',
                    'evidence_id_only_on_solution', 'missing_available_evidence')) for code in codes)
                argument['validation']['evidence_references' if evidence_error else 'graph_semantics'] = 'failed'
            report['argument'] = argument
        report['failure_stage'] = stage
    report['elapsed_seconds'] = round(time.monotonic() - started, 6)
    return report


def render_review(report):
    """Plain review copy; the JSON graph and trace remain the primary artifacts."""
    is_mock = report.get('mode') == 'mock_demonstration'
    heading = '# Drafter mock demonstration' if is_mock else '# Drafter review'
    model = ('No model was run (mock demonstration)' if is_mock else
             (report.get('configuration') or {}).get('model_id', 'not run'))
    lines = [heading, '', f"Run: {report.get('run_id', 'not started')}",
             f"Result: {report.get('status', report.get('contract_status', 'rejected'))}",
             f"Model: {model}",
             '', 'Passing the graph checks does not establish physical safety.', '']
    if is_mock:
        lines += ['This example uses fixed program rules. It does not measure model performance.',
                  '', report['deployment_reason'], '']
    argument = report.get('argument')
    if argument is None or argument['argument_bundle'] is None:
        lines += ['No argument was accepted.', '']
        lines += ['- ' + (d['code'] + ': ' + d['message'] if isinstance(d, dict) else str(d))
                  for d in report['diagnostics']]
        return '\n'.join(lines) + '\n'
    lines += [argument['summary'], '']
    if argument.get('reasoning_review'):
        review = argument['reasoning_review']
        lines += ['## Model-written reasoning — review required', '', review['warning'],
                  '', 'Model summary: ' + review['summary'], '', 'Model limitations:']
        lines += ['- ' + text for text in review['limitations']]
        lines += ['', 'All model-written graph statements below require the same review.', '']
    for item in argument['argument_bundle']['graphs']:
        lines += ['## ' + item['object_id'], '', 'Outcome: unresolved.', '']
        for node in item['graph']['nodes']:
            lines += [f"- {node['id']} ({node['type']}): {node['statement']}"]
            if node['evidence_id']:
                lines += ['  Evidence: ' + node['evidence_id']]
        lines += ['', 'Connections:', '']
        lines += [f"- {e['source']} → {e['target']} ({e['type']})" for e in item['graph']['edges']]
        lines += ['']
    lines += ['## Limitations', '']
    lines += ['- ' + text for text in argument['limitations']]
    return '\n'.join(lines) + '\n'
