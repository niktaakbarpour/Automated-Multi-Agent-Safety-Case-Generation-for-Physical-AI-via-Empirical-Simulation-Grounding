"""Generate a draft-argument/0.2.0 for an R1 v3 source-package request (drafter-request/0.2.0).

The same flow as generation.py, with v3 inputs. The model chooses a compact graph plan under the existing plan
schema; the host attaches scope and provenance, never repairs structure and never invents a citation. The model
never decides an outcome: the host computes each object's outcome from the request (an admitted checker assessment
plus graph-eligible evidence the plan cites, otherwise insufficient_information), states it to the model in
host_outcomes, and writes the outcomes and their backing itself. Accepted is structural acceptance only.

generation.generate_argument dispatches here for 0.2.0 requests, so `python -m drafter --generate` is unchanged.
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
from . import r1v3_profile as P
from .argument_checks import REVIEW_WARNING, authoritative_limitations, graph_structure_issues, solution_statement
from .llm import ConfigError, LocalModelClient
from .plan_schema import build_plan_schema, validate_plan_prose
from .validation import ContractError

PROMPT_VERSION = 'draft-argument-r1v3-prompt/0.1.0'
SERIALIZER_VERSION = P.SERIALIZER_VERSION
PROMPT_PATH = Path(__file__).resolve().parent / 'prompts' / 'draft_argument_r1v3_v1.md'
CHECK_NAMES = ('input_schema', 'input_semantics', 'output_schema', 'graph_semantics', 'evidence_references',
               'outcome_backing')


def _records(request):
    return {r['id']: r for r in request['source_package']['rag_source']['records']}


def plan_view(request):
    """The three fields the existing plan-schema builder reads, taken from a v3 request."""
    return {'requirement_configuration': {'protected_objects': request['requirement_configuration']['protected_objects']},
            'evidence_package': {'records': request['source_package']['rag_source']['records']},
            'evidence_handling': {'graph_eligible_evidence_ids': request['evidence']['graph_eligible_evidence_ids']}}


def plan_schema(request):
    """The full plan schema. The host validates every model reply against it."""
    return build_plan_schema(plan_view(request))


ID_LENGTH = '{1,128}$'
DECODER_RELAXATION = ('Sent to the model server: the full plan schema without text maxLength, without minItems/maxItems '
                      'on the node, edge and limitation arrays, and with node IDs bounded by + instead of {1,128}. Outlines compiles counted repetitions into a regex '
                      'automaton and timed out on the full schema; XGrammar compiles both. The host still validates '
                      'every reply against the full schema, so no reply that breaks a removed bound is accepted.')


def decoder_schema(schema):
    """The schema sent to the server for constrained decoding: the full schema minus bounds the host re-checks.

    Kept: every identifier pattern (its length bound {1,128} becomes +), the object roster and order, node types, physical-claim and evidence-ID
    constraints, required keys, no additional properties, and text minLength (it stops the one-character
    statements seen under XGrammar). Removed: string maxLength, the identifier length bound, and minItems/maxItems on arrays of repeated items.
    The graph roster array (fixed prefixItems) keeps its bounds."""
    def strip(value):
        if isinstance(value, list):
            return [strip(v) for v in value]
        if not isinstance(value, dict):
            return value
        out = {k: strip(v) for k, v in value.items()}
        if out.get('type') == 'string':
            out.pop('maxLength', None)
            if out.get('pattern', '').endswith(ID_LENGTH):
                out['pattern'] = out['pattern'][:-len(ID_LENGTH)] + '+$'
        if 'items' in out and 'prefixItems' not in out:
            out.pop('minItems', None)
            out.pop('maxItems', None)
        return out
    return strip(schema)


def host_backing(request, cited=None):
    """Each object's outcome and backing as the host decides it. cited: {object: [eligible IDs the plan cites]}.
    Without citations (before the model runs) an object counts as backed if it has any eligible record, which is the
    outcome the host will record when the plan cites that evidence, as the plan schema and serializer require."""
    context, records = request['checker_context'], _records(request)
    eligible = request['evidence']['graph_eligible_evidence_ids']
    admitted = context['admission']['state'] == 'admitted'
    assessments = {a['object_id']: a for a in context['assessments']}
    backing = {}
    for obj in request['requirement_configuration']['protected_objects']:
        available = sorted(i for i in eligible if records[i]['object_id'] == obj)
        citations = sorted(cited.get(obj, [])) if cited is not None else available
        a = assessments.get(obj)
        if admitted and a is not None and a['classification'] != P.INSUFFICIENT and citations:
            backing[obj] = {'outcome': a['classification'], 'citations': citations, 'checker_assessment': {
                'object_id': obj, 'classification': a['classification'], 'checker_version': context['checker_version'],
                'config_sha256': context['config_sha256'], 'admission_contract': context['admission']['contract']}}
        else:
            backing[obj] = {'outcome': P.INSUFFICIENT, 'checker_assessment': None,
                            'citations': citations if cited is not None else []}
    return backing


def model_input(request):
    """Everything the model may see. No human reference label is part of a request."""
    config, records = request['requirement_configuration'], _records(request)
    eligible = request['evidence']['graph_eligible_evidence_ids']
    catalogue = []
    for key in eligible:
        record = records[key]
        item = {k: deepcopy(record.get(k)) for k in ('id', 'kind', 'measurement_type', 'requirement_id',
                                                       'requirement_version', 'execution_id', 'object_id', 'interval',
                                                       'clock', 'domain', 'capability', 'limitations')}
        item['solution_statement'] = solution_statement(record)
        catalogue.append(item)
    context_only = {}
    for key in request['evidence']['context_only_evidence_ids']:
        r = records[key]
        entry = context_only.setdefault(r['object_id'], {'records': 0, 'requirement_versions': set(),
                                                         'measurement_types': set()})
        entry['records'] += 1
        entry['requirement_versions'].add(str(r.get('requirement_version')))
        entry['measurement_types'].add(str(r.get('measurement_type')))
    outcomes = {obj: b['outcome'] for obj, b in host_backing(request).items()}
    return {
        'request_id': request['request_id'], 'request_sha256': digest(request),
        'requirement': {'id': config['requirement_id'], 'version': config['requirement_version'],
                        'statement': config['requirement_statement'], 'protected_objects': config['protected_objects']},
        'target_execution': deepcopy(request['target_execution']),
        'monitoring_scope': deepcopy(request['monitoring_scope']),
        'eligible_evidence_catalogue': catalogue,
        'context_only_evidence': {obj: {'records': v['records'], 'requirement_versions': sorted(v['requirement_versions']),
                                        'measurement_types': sorted(v['measurement_types'])}
                                  for obj, v in context_only.items()},
        'coverage': deepcopy(request['coverage']),
        'checker_context': {
            'status': request['checker_context']['status'],
            'checker_version': request['checker_context']['checker_version'],
            'admission': deepcopy(request['checker_context']['admission']),
            'assessments': [{k: deepcopy(a.get(k)) for k in ('object_id', 'classification', 'applicability',
                                                               'checker_support_class', 'measurement_complete')}
                            for a in request['checker_context']['assessments']]},
        'evidence_gaps': deepcopy(request['evidence_gaps']),
        'limitations': list(request['limitations']),
        'host_outcomes': outcomes,
        'host_execution_outcome': P.aggregate(outcomes),
    }


def messages(request):
    return [{'role': 'system', 'content': PROMPT_PATH.read_text(encoding='utf-8')},
            {'role': 'user', 'content': canonical(model_input(request)).decode('utf-8')}]


def serialize_plan(plan, request, provenance):
    """Attach authoritative fields and the host outcomes; reject structural omissions, never repair."""
    config, target, window = request['requirement_configuration'], request['target_execution'], request['monitoring_scope']
    roster = config['protected_objects']
    if [g['object_id'] for g in plan['graphs']] != roster:
        raise ContractError(['plan_object_roster_or_order'])
    records, eligible = _records(request), set(request['evidence']['graph_eligible_evidence_ids'])
    graphs, global_ids, cited = [], set(), {}
    for value in plan['graphs']:
        object_id = value['object_id']
        ids = [n['id'] for n in value['nodes']]
        if len(ids) != len(set(ids)) or global_ids.intersection(ids) or any(not k.startswith(object_id + ':') for k in ids):
            raise ContractError(['plan_node_identity:' + object_id])
        global_ids.update(ids)
        shape = graph_structure_issues(value, object_id, prefix='plan')
        if shape:
            raise ContractError(shape)
        nodes = []
        for n in value['nodes']:
            node = deepcopy(n)
            if node['physical_claim'] != (node['type'] in ('goal', 'unresolved_claim')):
                raise ContractError(['plan_physical_claim_type:' + node['id']])
            node['scope'] = {'requirement_id': config['requirement_id'], 'requirement_version': config['requirement_version'],
                             'execution_id': target['execution_id'], 'object_id': object_id,
                             'domain': window['domain'], 'clock': window['clock'], 'interval': list(window['interval'])}
            node['origin'] = 'llm_proposal'
            node['validation_status'] = 'unresolved' if node['physical_claim'] else 'proposed'
            node['provenance'] = {'run_id': provenance['run_id'], 'prompt_sha256': provenance['prompt_sha256'],
                                  'request_sha256': digest(request), 'serializer_version': SERIALIZER_VERSION,
                                  'role': P.REASONING_ROLE, 'prose_review': 'required'}
            if node['type'] == 'solution':
                record = records.get(node['evidence_id'])
                if node['evidence_id'] not in eligible or record is None or record['object_id'] != object_id:
                    raise ContractError(['plan_ineligible_solution:' + node['id']])
                if node['statement'] != solution_statement(record):
                    raise ContractError(['plan_solution_statement_mismatch:' + node['id']])
                cited.setdefault(object_id, set()).add(record['id'])
                node['scope'].update(interval=list(record['interval']), domain=record['domain'], clock=record['clock'])
                node['provenance'] = {k: deepcopy(record[k]) for k in ('source_path', 'source_sha256', 'selector')}
                node['provenance']['registry_record'] = deepcopy(record)
                node['origin'] = 'retrieved_observation'
                node['validation_status'] = record['validation_status']
            elif node['evidence_id'] is not None:
                raise ContractError(['plan_evidence_id_only_on_solution:' + node['id']])
            nodes.append(node)
        available = {k for k in eligible if records[k]['object_id'] == object_id}
        if available and not cited.get(object_id):
            raise ContractError(['plan_missing_available_evidence:' + object_id])
        graphs.append({'object_id': object_id, 'graph': {'schema_version': '1.0.0', 'nodes': nodes,
                                                         'edges': deepcopy(value['edges']),
                                                         'empirical_admission_enabled': False}})
    backing = host_backing(request, {k: sorted(v) for k, v in cited.items()})
    outcomes = {obj: b['outcome'] for obj, b in backing.items()}
    return {'execution_id': target['execution_id'], 'protected_objects': list(roster), 'graphs': graphs,
            'execution_conclusion': {'claimed_outcome': P.aggregate(outcomes),
                                     'statement': P.authoritative_conclusion(outcomes),
                                     'object_outcomes': outcomes, 'outcome_backing': backing}}


def envelope(request, run_id):
    return {
        'schema_version': P.ARGUMENT_VERSION, 'request_id': request['request_id'], 'test_fixture': request['test_fixture'],
        'request_sha256': digest(request), 'requirement_configuration_sha256': request['requirement_configuration_sha256'],
        'source_package_sha256': request['source_package_sha256'], 'generation_status': 'failed', 'argument_bundle': None,
        'summary': 'No accepted argument was generated.', 'limitations': authoritative_limitations(request),
        'diagnostics': [], 'validation': {**{name: 'not_run' for name in CHECK_NAMES}, 'physical_sufficiency': 'not_assessed'},
        'generation_provenance': {'backend': 'not_run', 'model_id': None, 'model_revision': None, 'prompt_version': None,
                                  'prompt_sha256': None, 'run_id': run_id, 'raw_output_sha256': None},
        'empirical_admission_enabled': False, 'safety_claim_verified': False}


def generate_argument(request, config):
    """One explicit model attempt for a valid R1 v3 request; no retries or fallback. Returns a run report holding a
    draft-argument/0.2.0 (also a valid failure envelope). Invalid input triggers no network call."""
    started, run_id = time.monotonic(), str(uuid.uuid4())
    report = {
        'schema_version': 'drafter-generation-run/0.1.0', 'run_id': run_id,
        'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'failed', 'configuration': None,
        'configuration_sha256': None, 'request_sha256': None, 'argument': None, 'diagnostics': [],
        'trace': {'serializer_version': SERIALIZER_VERSION, 'prompt_version': PROMPT_VERSION, 'messages': None,
                  'prompt_sha256': None, 'json_schema': None, 'validation_schema_sha256': None,
                  'decoder_relaxation': None, 'discovery': None, 'completion': None},
        'model_called': False, 'completion_attempted': False, 'argument_generated': False,
        'project_evidence_sent': False, 'empirical_admission_enabled': False, 'safety_claim_verified': False}
    stage, argument = 'input', None
    try:
        P.validate_request(request)
        report['request_sha256'] = digest(request)
        argument = envelope(request, run_id)
        argument['validation'].update(input_schema='passed', input_semantics='passed')
        report['argument'] = argument
        stage = 'configuration'
        client = LocalModelClient(config)
        report['configuration'] = config.public_settings()
        report['configuration_sha256'] = digest(report['configuration'])
        schema, sent = plan_schema(request), messages(request)
        decoding = decoder_schema(schema)
        report['trace'].update(messages=sent, prompt_sha256=digest(sent), json_schema=decoding,
                               validation_schema_sha256=digest(schema), decoder_relaxation=DECODER_RELAXATION)
        argument['generation_provenance'].update(model_id=config.model_id, model_revision=config.model_revision,
                                                 prompt_version=PROMPT_VERSION, prompt_sha256=digest(sent))
        stage = 'discovery'
        discovery = client.discover_models()
        report['trace']['discovery'] = asdict(discovery)
        if discovery.status != 'ok' or not discovery.configured_model_available:
            raise ConfigError(discovery.error_code or 'configured_model_unavailable',
                              discovery.message or 'The selected model is unavailable; no fallback selected.')
        stage = 'completion'
        report['completion_attempted'] = True
        report['model_called'] = report['project_evidence_sent'] = None
        completion = client.complete(sent, decoding, schema_name='drafter_graph_plan')
        report['trace']['completion'] = asdict(completion)
        if isinstance(completion.raw_response, dict) and isinstance(completion.raw_response.get('choices'), list):
            report['model_called'] = report['project_evidence_sent'] = True
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
        bundle = serialize_plan(completion.parsed_json, request, argument['generation_provenance'])
        outcomes = bundle['execution_conclusion']['object_outcomes']
        candidate = deepcopy(argument)
        candidate.update(generation_status='accepted', argument_bundle=bundle,
                         summary=P.authoritative_summary(request, outcomes),
                         reasoning_review={'status': 'required', 'warning': REVIEW_WARNING,
                                           'summary': completion.parsed_json['summary'],
                                           'limitations': deepcopy(completion.parsed_json['limitations'])})
        candidate['validation'].update({name: 'passed' for name in CHECK_NAMES})
        stage = 'graph_validation'
        P.validate_argument(candidate, request)
        report.update(status='accepted', argument=candidate, argument_generated=True)
    except (ContractError, ConfigError, ValueError, TypeError, OSError, RecursionError) as error:
        rejected = stage in ('input', 'plan', 'serialization', 'graph_validation')
        report['status'] = 'rejected' if rejected else 'failed'
        codes = error.issues if isinstance(error, ContractError) else [getattr(error, 'code', 'generation_error')]
        report['diagnostics'] = [{'code': code, 'path': stage,
                                  'message': code if isinstance(error, ContractError) else str(error)} for code in codes]
        if argument is not None:
            argument['generation_status'] = report['status']
            argument['diagnostics'] = deepcopy(report['diagnostics'])
            if stage == 'plan':
                argument['validation']['output_schema'] = 'failed'
            if stage in ('serialization', 'graph_validation'):
                evidence_error = any(part in code for code in codes for part in (
                    'ineligible_solution', 'solution_statement_mismatch', 'evidence_id_only_on_solution',
                    'missing_available_evidence', 'citation'))
                argument['validation']['evidence_references' if evidence_error else 'graph_semantics'] = 'failed'
            report['argument'] = argument
        report['failure_stage'] = stage
    report['elapsed_seconds'] = round(time.monotonic() - started, 6)
    return report
