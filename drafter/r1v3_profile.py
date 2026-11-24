"""R1 v3 source-package profile: drafter-request/0.2.0 and draft-argument/0.2.0.

A versioned path next to the frozen v2 profiles, which it does not change. The configuration is derived from the
frozen v3 files and bound to them by SHA-256. A request carries a source evidence package unchanged (bound by
digest) and states its status: retrieved records keep their own requirement version and are graph-eligible only
under R1 v3, a checker assessment keeps its admission state, and evidence gaps are explicit. No human reference
label may appear.

An object outcome other than insufficient_information is accepted only when it is backed by an admitted checker
assessment of the same classification and at least one graph-eligible citation for that object. No admission
contract exists yet (that is the evidence-registry owner's), so every assessment is not admitted and every outcome
stays insufficient_information until one is registered in ADMISSION_VERIFIERS.

Validators perform no inference and open no file named inside a request. They read only the frozen repository
files listed in FROZEN_SOURCES.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

from jsonschema import Draft202012Validator

from evaluation.r1_v4.provenance import digest

ROOT = Path(__file__).resolve().parents[1]
CONFIG_VERSION = 'r1-v3-drafter-config/1.0.0'
CONFIG_SCHEMA = 'requirements/r1_initial_table_support_v3/R1_V3_DRAFTER_CONFIG_SCHEMA.json'
REQUEST_VERSION = 'drafter-request/0.2.0'
ARGUMENT_VERSION = 'draft-argument/0.2.0'
PROFILE = 'r1v3_source_package'
PACKAGE_SCHEMA = 'source-evidence-package/original-r1-v3-pre-integration-1'
REQUIREMENT_ID = 'R1'
REQUIREMENT_VERSION = 'r1-initial-table-support-v3-20261024'
FROZEN_SOURCES = {
    'checker_config': 'evaluation/r1_v3/config.json',
    'requirement_scope': 'evaluation/r1_v3_generalization/blinded_review/requirement_scope.v3.json',
    'scope_decision': 'evaluation/r1_v3_generalization/blinded_review/REQUIREMENT_SCOPE_DECISION.md',
}
INSUFFICIENT = 'insufficient_information'
OUTCOMES = ('violation', 'no_violation_observed_within_reviewed_coverage', 'not_applicable', INSUFFICIENT)
# The R1 execution aggregation used by critic/contract.py and evaluation/r1_v4/aggregate.py (V > U > N > NA),
# on the v3 vocabulary.
PRECEDENCE = ('violation', INSUFFICIENT, 'no_violation_observed_within_reviewed_coverage', 'not_applicable')
DEFINITE_OUTCOME_RULE = (
    'An object outcome other than insufficient_information requires an admitted R1 v3 checker assessment of the same '
    'classification for that object and at least one graph-eligible evidence citation for that object. Without both, '
    'the outcome is insufficient_information. The execution outcome is the R1 aggregation of the object outcomes '
    '(violation > insufficient_information > no_violation_observed_within_reviewed_coverage > not_applicable).')
ELIGIBILITY_RULE = (
    'A retrieved record is graph-eligible only if it is an original record of this execution and of a protected '
    'object, its requirement is R1 ' + REQUIREMENT_VERSION + ', and its interval lies inside the monitoring scope. '
    'Records of another requirement version are kept as context and never cited, re-versioned or mapped.')
# How the records were selected: the retrieval source, query window and API, as recorded in the package.
RETRIEVAL_FIELDS = ('database_path', 'database_sha256', 'source_commit', 'retrieval_api', 'queried_interval',
                    'indexed_requirement_version', 'record_types_included', 'record_count_included')
SOURCE_LIMITATION = ('Source package fields are checked for internal consistency and bound by digest; the Drafter has '
                     'not opened or replayed source recordings and does not establish physical sufficiency.')
NOT_ADMITTED_REASON = ('No checker-assessment admission contract is available; the assessment is development-only '
                       'and is not admitted.')
# Keys that would carry human reference labels. The package's own note that the human reference is excluded is
# the one allowed occurrence.
FORBIDDEN_KEYS = frozenset({'human_reference', 'human_references', 'human_label', 'human_labels', 'reference_label',
                            'reference_labels', 'gold_label', 'gold_labels', 'adjudicated_label', 'adjudicated_labels',
                            'adjudication', 'expected_outcome', 'reference_answers', 'reference_answer'})
ALLOWED_EXCLUSION_NOTE = ('source_package', 'evidence_semantics', 'human_reference')
CONCLUSION_UNRESOLVED = 'R1 remains unresolved for all protected objects in the declared window.'
# Admission contracts, by name, once the evidence-registry owner provides one: name -> callable(request) -> issues.
ADMISSION_VERIFIERS = {}


def _error(issues):
    from .validation import ContractError
    return ContractError(sorted(set(issues)))


def file_sha256(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


# ------------------------------------------------------------------ configuration

def build_configuration():
    """The R1 v3 Drafter configuration, derived from the frozen v3 files. Raises if they disagree."""
    checker, scope = _read(FROZEN_SOURCES['checker_config']), _read(FROZEN_SOURCES['requirement_scope'])
    issues = []
    if not (checker['requirement_id'] == scope['requirement_id'] == REQUIREMENT_ID):
        issues.append('frozen_sources_requirement_id_mismatch')
    if not (checker['requirement_version'] == scope['requirement_version'] == REQUIREMENT_VERSION):
        issues.append('frozen_sources_requirement_version_mismatch')
    if checker['objects'] != scope['protected_objects']:
        issues.append('frozen_sources_object_roster_mismatch')
    if checker['start_frame'] != scope['interval']['start_saved_frame']:
        issues.append('frozen_sources_start_frame_mismatch')
    if scope['interval']['end'] != 'terminal_recorded_snapshot':
        issues.append('frozen_sources_end_basis_unsupported')
    if issues:
        raise _error(issues)
    return {
        'schema_version': CONFIG_VERSION, 'requirement_id': REQUIREMENT_ID, 'requirement_version': REQUIREMENT_VERSION,
        'requirement_statement': ' '.join(scope['statement'].split()),
        'protected_objects': list(scope['protected_objects']),
        'monitoring_interval': {'axis': 'saved_frame', 'domain': 'frame', 'clock': 'saved_frame_index',
                                'start': checker['start_frame'], 'end_basis': 'terminal_recorded_snapshot',
                                'inclusive': True},
        'frozen_sources': {name: {'path': path, 'sha256': file_sha256(path)} for name, path in FROZEN_SOURCES.items()},
        'checker': {'checker_version': checker['checker_version'],
                    'config_sha256': file_sha256(FROZEN_SOURCES['checker_config'])},
        'outcome_vocabulary': list(OUTCOMES), 'outcome_precedence': list(PRECEDENCE),
        'definite_outcome_rule': DEFINITE_OUTCOME_RULE,
    }


def configuration_issues(config):
    validator = Draft202012Validator(_read(CONFIG_SCHEMA))
    issues = sorted('configuration_schema:' + '/'.join(map(str, e.absolute_path)) + ':' + e.message
                    for e in validator.iter_errors(config))
    if issues:
        return issues
    expected = build_configuration()
    return ['configuration_not_bound_to_frozen_sources:' + key
            for key in sorted(set(expected) | set(config)) if config.get(key) != expected.get(key)]


# ------------------------------------------------------------------ request

def _forbidden_label_paths(value, path=()):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            here = path + (key,)
            if key in FORBIDDEN_KEYS and not (here == ALLOWED_EXCLUSION_NOTE and isinstance(item, str)
                                              and 'excluded' in item):
                found.append('/'.join(map(str, here)))
            found.extend(_forbidden_label_paths(item, here))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_forbidden_label_paths(item, path + (index,)))
    return found


def _eligible(record, config, execution_id, interval):
    span = record.get('interval')
    return (record.get('original') is True and record.get('requirement_id') == config['requirement_id']
            and record.get('requirement_version') == config['requirement_version']
            and record.get('execution_id') == execution_id and record.get('object_id') in config['protected_objects']
            and isinstance(span, list) and len(span) == 2 and interval[0] <= span[0] <= span[1] <= interval[1])


def _gaps(config, records, eligible, coverage, assessments, checker_status, admission_state):
    gaps = []
    for obj in config['protected_objects']:
        mine = [r for r in records if r.get('object_id') == obj]
        if not any(r['id'] in eligible for r in mine):
            versions = sorted({str(r.get('requirement_version')) for r in mine})
            detail = (f'{len(mine)} retrieved record(s) for this object carry requirement version '
                      f'{", ".join(versions)}; none is graph-eligible under R1 {config["requirement_version"]}.'
                      if mine else 'No retrieved record for this object.')
            gaps.append({'object_id': obj, 'gap': 'no_v3_citable_evidence', 'detail': detail})
        found = [a for a in assessments if a.get('object_id') == obj]
        if not found:
            gaps.append({'object_id': obj, 'gap': 'no_checker_assessment',
                         'detail': 'The package has no checker assessment for this object.'})
        elif admission_state != 'admitted':
            a = found[0]
            gaps.append({'object_id': obj, 'gap': 'checker_assessment_not_admitted',
                         'detail': f"The checker classifies this object as {a['classification']} "
                                   f"(applicability {a['applicability']}); the assessment is {checker_status} "
                                   'and its admission state is not_admitted.'})
        unqualified = sorted({q['measurement_type'] for q in coverage if q.get('object_id') == obj
                              and not q.get('coverage', {}).get('physical_coverage_qualified')})
        if unqualified:
            gaps.append({'object_id': obj, 'gap': 'physical_coverage_not_qualified',
                         'detail': 'Coverage of ' + ', '.join(unqualified) + ' is saved-frame availability only, '
                                   'not qualified physical coverage.'})
        missing = [i for q in coverage if q.get('object_id') == obj for i in q.get('coverage', {}).get('missing_intervals', [])]
        if missing:
            gaps.append({'object_id': obj, 'gap': 'missing_saved_frames',
                         'detail': 'Missing saved-frame intervals: ' + json.dumps(missing)})
    return gaps


def not_admitted():
    return {'state': 'not_admitted', 'contract': None, 'reason': NOT_ADMITTED_REASON}


def derived_fields(package, config, admission=None):
    """Every request field that follows from the package, the configuration and the admission state, recomputed the
    same way by the builder and the validator."""
    admission = deepcopy(admission) if admission is not None else not_admitted()
    execution, rag, checker = package['execution'], package['rag_source'], package['checker_assessment']
    interval = list(execution['monitoring_interval_saved_frames_inclusive'])
    records = rag['records']
    eligible = sorted(r['id'] for r in records if _eligible(r, config, execution['execution_id'], interval))
    return {
        'target_execution': {'execution_id': execution['execution_id'],
                             'trajectory_sha256': execution['trajectory_sha256'],
                             'trajectory_path': execution['trajectory_path_hestia'],
                             'source_identity_status': execution['source_identity_status']},
        'monitoring_scope': {'domain': 'frame', 'clock': 'saved_frame_index', 'interval': interval, 'inclusive': True,
                             'end_basis': config['monitoring_interval']['end_basis']},
        'evidence': {'record_ids': [r['id'] for r in records], 'records_sha256': digest(records),
                     'record_sha256': {r['id']: digest(r) for r in records},
                     'retrieval': {key: deepcopy(rag[key]) for key in RETRIEVAL_FIELDS},
                     'record_requirement_versions': sorted({str(r.get('requirement_version')) for r in records}),
                     'graph_eligible_evidence_ids': eligible,
                     'context_only_evidence_ids': sorted(r['id'] for r in records if r['id'] not in eligible),
                     'eligibility_rule': ELIGIBILITY_RULE, 'citation_status': deepcopy(rag['citation_status']),
                     'empirical_admission_enabled': False, 'physical_sufficiency': False},
        'coverage': deepcopy(rag['coverage_queries']),
        'checker_context': {'status': checker['status'], 'checker_version': checker['checker_version'],
                            'config_sha256': checker['config_sha256'], 'predictions_sha256': checker['predictions_sha256'],
                            'seal_sha256': checker['seal_sha256'],
                            'reference_answers_loaded': checker['reference_answers_loaded'],
                            'admission': admission,
                            'assessments': deepcopy(checker['object_assessments'])},
        'evidence_gaps': _gaps(config, records, set(eligible), rag['coverage_queries'], checker['object_assessments'],
                               checker['status'], admission['state']),
        'limitations': list(dict.fromkeys([*package['coverage_and_limitations'], SOURCE_LIMITATION])),
    }


def _package_issues(package, config):
    """The package must describe this requirement and checker, without labels."""
    issues = ['human_reference_label_present:' + p for p in _forbidden_label_paths({'source_package': package})]
    execution, checker, rag = package['execution'], package['checker_assessment'], package['rag_source']
    if (execution['requirement_id'], execution['requirement_version']) != (config['requirement_id'],
                                                                            config['requirement_version']):
        issues.append('package_requirement_mismatch')
    if execution['protected_objects'] != config['protected_objects']:
        issues.append('package_object_roster_mismatch')
    interval = execution['monitoring_interval_saved_frames_inclusive']
    if (not isinstance(interval, list) or len(interval) != 2 or any(type(v) is not int for v in interval)
            or interval[0] != config['monitoring_interval']['start'] or interval[0] > interval[1]):
        issues.append('package_monitoring_interval_mismatch')
    if checker['config_sha256'] != config['checker']['config_sha256']:
        issues.append('checker_config_hash_mismatch')
    if checker['checker_version'] != config['checker']['checker_version']:
        issues.append('checker_version_mismatch')
    if checker['reference_answers_loaded'] is not False:
        issues.append('checker_loaded_reference_answers')
    objects = [a.get('object_id') for a in checker['object_assessments']]
    if sorted(objects) != sorted(config['protected_objects']) or len(set(objects)) != len(objects):
        issues.append('checker_assessment_roster_mismatch')
    for a in checker['object_assessments']:
        if a.get('requirement_version') != config['requirement_version']:
            issues.append('checker_assessment_requirement_mismatch:' + str(a.get('object_id')))
        if a.get('checker_version') != config['checker']['checker_version']:
            issues.append('checker_assessment_version_mismatch:' + str(a.get('object_id')))
        if a.get('classification') not in OUTCOMES:
            issues.append('checker_assessment_unknown_classification:' + str(a.get('object_id')))
    ids = [r.get('id') for r in rag['records']]
    if len(set(ids)) != len(ids):
        issues.append('duplicate_record_id')
    if rag.get('record_count_included') != len(rag['records']):
        issues.append('record_count_mismatch')
    if rag.get('queried_interval') != interval:
        issues.append('retrieval_interval_mismatch')
    for r in rag['records']:
        if r.get('execution_id') != execution['execution_id']:
            issues.append('record_execution_mismatch:' + str(r.get('id')))
        if r.get('object_id') not in config['protected_objects']:
            issues.append('record_object_scope:' + str(r.get('id')))
    return issues


def build_request(package, *, request_id, test_fixture=False, admission=None):
    """A validated drafter-request/0.2.0 for one source evidence package. Raises ContractError when invalid.

    admission stays not_admitted unless an admission record names a contract registered in ADMISSION_VERIFIERS
    and that contract's verifier accepts the request."""
    from .validation import json_value_issues
    if not isinstance(package, dict) or not isinstance(request_id, str) or not request_id.strip():
        raise _error(['r1v3_builder_requires_package_object_and_request_id'])
    problems = json_value_issues(package)
    if problems:
        raise _error(problems)
    config = build_configuration()
    package = deepcopy(package)
    issues = _package_issues(package, config)
    if issues:
        raise _error(issues)
    request = {'schema_version': REQUEST_VERSION, 'input_profile': PROFILE, 'request_id': request_id,
               'test_fixture': test_fixture, 'usage': 'proposed_argument', 'requirement_configuration': config,
               'requirement_configuration_sha256': digest(config), 'source_package': package,
               'source_package_sha256': digest(package), **derived_fields(package, config, admission),
               'human_reference_included': False, 'empirical_admission_enabled': False, 'safety_claim_verified': False}
    validate_request(request)
    return request


def validate_request(request):
    """Validate a drafter-request/0.2.0. Returns a summary; raises ContractError listing every problem."""
    from .validation import schema_issues
    issues = schema_issues(request, 'draft_request_r1v3.schema.json')
    if issues:
        raise _error(issues)
    config, package = request['requirement_configuration'], request['source_package']
    issues = configuration_issues(config)
    if issues:
        raise _error(issues)
    if request['requirement_configuration_sha256'] != digest(config):
        issues.append('requirement_configuration_sha256_mismatch')
    if request['source_package_sha256'] != digest(package):
        issues.append('source_package_sha256_mismatch')
    issues += _package_issues(package, config)
    issues += ['human_reference_label_present:' + p
               for p in _forbidden_label_paths({k: v for k, v in request.items() if k != 'source_package'})]
    if issues:
        raise _error(issues)
    admission = request['checker_context']['admission']
    if admission['state'] == 'admitted':
        verifier = ADMISSION_VERIFIERS.get(admission['contract'])
        if verifier is None:
            issues.append('checker_admission_contract_unavailable')
        else:
            issues += ['checker_admission:' + text for text in verifier(request)]
    expected = derived_fields(package, config, admission if admission['state'] == 'admitted' else None)
    for field, value in expected.items():
        if request[field] != value:
            issues.append('derived_field_mismatch:' + field)
    if issues:
        raise _error(issues)
    return {'contract_status': 'valid_r1v3_input', 'input_profile': PROFILE,
            'records': len(request['evidence']['record_ids']),
            'graph_eligible_records': len(request['evidence']['graph_eligible_evidence_ids']),
            'checker_admission': admission['state'], 'evidence_gaps': len(request['evidence_gaps']),
            'source_replay': 'not_performed', 'physical_sufficiency': 'not_evaluated',
            'empirical_admission_enabled': False, 'safety_claim_verified': False, 'model_called': False}


# ------------------------------------------------------------------ outcomes and host texts

def aggregate(object_outcomes):
    values = set(object_outcomes.values())
    return next((o for o in PRECEDENCE if o in values), 'not_applicable')


def unresolved_backing(request):
    """The backing every object gets while no admitted assessment and eligible citation exist."""
    return {obj: {'outcome': INSUFFICIENT, 'checker_assessment': None, 'citations': []}
            for obj in request['requirement_configuration']['protected_objects']}


def authoritative_conclusion(object_outcomes):
    outcome = aggregate(object_outcomes)
    if set(object_outcomes.values()) == {INSUFFICIENT}:
        return CONCLUSION_UNRESOLVED
    return (f'Execution outcome {outcome} by R1 aggregation of the object outcomes; each definite object outcome is '
            'backed by an admitted checker assessment and cited evidence: '
            + '; '.join(f'{obj} {value}' for obj, value in object_outcomes.items()) + '.')


def authoritative_summary(request, object_outcomes):
    count = len(request['requirement_configuration']['protected_objects'])
    if set(object_outcomes.values()) == {INSUFFICIENT}:
        return (f'R1 remains unresolved for all {count} protected objects in the declared monitoring window. The '
                'supplied evidence does not establish a verified physical outcome: no checker assessment is admitted '
                'and no evidence record is citable under R1 v3. Model reasoning requires review.')
    return (f'R1 v3 execution outcome {aggregate(object_outcomes)} for {count} protected objects, from admitted checker '
            'assessments and cited evidence. Model reasoning requires review.')


def backing_issues(bundle, request):
    """Every definite outcome must be backed; every backing must agree with the request."""
    issues = []
    conclusion = bundle['execution_conclusion']
    outcomes, backing = conclusion['object_outcomes'], conclusion['outcome_backing']
    roster = request['requirement_configuration']['protected_objects']
    if list(outcomes) != roster or list(backing) != roster:
        issues.append('argument_outcome_roster_mismatch')
    eligible = set(request['evidence']['graph_eligible_evidence_ids'])
    records = {r['id']: r for r in request['source_package']['rag_source']['records']}
    context = request['checker_context']
    admitted = context['admission']['state'] == 'admitted'
    assessments = {a['object_id']: a for a in context['assessments']}
    for obj in roster:
        outcome, back = outcomes.get(obj), backing.get(obj)
        if back is None or outcome is None:
            continue
        if back['outcome'] != outcome:
            issues.append('outcome_backing_mismatch:' + obj)
        for cited in back['citations']:
            if cited not in eligible or records.get(cited, {}).get('object_id') != obj:
                issues.append('ineligible_citation:' + obj + ':' + cited)
        claim = back['checker_assessment']
        if outcome == INSUFFICIENT:
            if claim is not None:
                issues.append('unresolved_outcome_with_checker_claim:' + obj)
            continue
        if claim is None:
            issues.append('unbacked_outcome:' + obj)
            continue
        if not admitted:
            issues.append('checker_assessment_not_admitted:' + obj)
        source = assessments.get(obj)
        if (source is None or claim['object_id'] != obj or claim['classification'] != outcome
                or source['classification'] != outcome or claim['checker_version'] != context['checker_version']
                or claim['config_sha256'] != context['config_sha256']
                or claim['admission_contract'] != context['admission']['contract']):
            issues.append('backing_assessment_mismatch:' + obj)
        if not back['citations']:
            issues.append('missing_citations:' + obj)
    if conclusion['claimed_outcome'] != aggregate(outcomes):
        issues.append('execution_outcome_not_r1_aggregation')
    if conclusion['statement'] != authoritative_conclusion(outcomes):
        issues.append('argument_authoritative_conclusion_mismatch')
    return issues


# ------------------------------------------------------------------ argument

def validate_argument_bundle(bundle, request):
    from .argument_checks import graph_structure_issues
    from .validation import schema_issues
    from evaluation.r1_v4.evidence_registry_gsn.gsn import Graph, Node, Edge
    validate_request(request)
    issues = schema_issues(bundle, 'draft_argument_r1v3.schema.json', '#/$defs/argument_bundle')
    if issues:
        raise _error(issues)
    config, scope, target = request['requirement_configuration'], request['monitoring_scope'], request['target_execution']
    roster = config['protected_objects']
    if bundle['execution_id'] != target['execution_id'] or bundle['protected_objects'] != roster:
        issues.append('argument_execution_or_roster_mismatch')
    if [item['object_id'] for item in bundle['graphs']] != roster:
        issues.append('argument_graph_roster_mismatch')
    issues += backing_issues(bundle, request)
    eligible = set(request['evidence']['graph_eligible_evidence_ids'])

    class NoRecords:  # no record is citable under R1 v3 yet; a Solution therefore cannot validate
        def records(self):
            return ()

    global_ids = set()
    for item in bundle['graphs']:
        object_id, value = item['object_id'], item['graph']
        issues.extend(graph_structure_issues(value, object_id))
        if len(value['nodes']) > 24 or len(value['edges']) > 80:
            issues.append('argument_graph_too_large:' + object_id)
            continue
        ids = {node['id'] for node in value['nodes']}
        if ids & global_ids:
            issues.append('argument_global_node_identity:' + object_id)
        global_ids |= ids
        for node in value['nodes']:
            nscope = node.get('scope', {})
            if (nscope.get('requirement_id'), nscope.get('requirement_version'), nscope.get('execution_id'),
                    nscope.get('object_id')) != (config['requirement_id'], config['requirement_version'],
                                                 target['execution_id'], object_id):
                issues.append('argument_node_scope:' + node['id'])
            if nscope.get('domain') != scope['domain'] or nscope.get('clock') != scope['clock'] or 'interval' not in nscope:
                issues.append('argument_node_temporal_scope:' + node['id'])
            elif node['type'] != 'solution' and nscope['interval'] != scope['interval']:
                issues.append('argument_reasoning_window_mismatch:' + node['id'])
            if node['type'] == 'solution' and node.get('evidence_id') not in eligible:
                issues.append('argument_ineligible_solution:' + node['id'])
            if node['type'] != 'solution':
                provenance = node.get('provenance', {})
                if (provenance.get('request_sha256') != digest(request) or provenance.get('prose_review') != 'required'
                        or provenance.get('role') != 'proposed_reasoning_not_verified_physical_evidence'):
                    issues.append('argument_reasoning_provenance_binding:' + node['id'])
        try:
            graph = Graph(tuple(Node(**n) for n in value['nodes']), tuple(Edge(**e) for e in value['edges']),
                          value['schema_version'])
            graph.validate(NoRecords())
            if not any(n.physical_claim and n.type in ('goal', 'unresolved_claim') and n.validation_status == 'unresolved'
                       for n in graph.nodes):
                issues.append('missing_unresolved_physical_claim:' + object_id)
        except (ValueError, TypeError, KeyError) as error:
            issues.append('graph:' + object_id + ':' + str(error))
    if issues:
        raise _error(issues)
    return {'contract_status': 'valid_argument_bundle', 'physical_sufficiency': 'not_evaluated',
            'safety_claim_verified': False, 'model_called': False}


def validate_argument(argument, request):
    """Validate a draft-argument/0.2.0 against its request. Raises ContractError listing every problem."""
    from .argument_checks import authoritative_limitations, model_review_issues
    from .validation import schema_issues
    validate_request(request)
    issues = schema_issues(argument, 'draft_argument_r1v3.schema.json')
    if issues:
        raise _error(issues)
    issues += ['human_reference_label_present:' + p for p in _forbidden_label_paths(argument)]
    for field, expected in (('request_id', request['request_id']), ('request_sha256', digest(request)),
                            ('requirement_configuration_sha256', request['requirement_configuration_sha256']),
                            ('source_package_sha256', request['source_package_sha256']),
                            ('test_fixture', request['test_fixture'])):
        if argument[field] != expected:
            issues.append('argument_input_binding:' + field)
    if argument['generation_status'] != 'accepted':
        if issues:
            raise _error(issues)
        return {'contract_status': 'valid_failure_contract', 'physical_sufficiency': 'not_evaluated',
                'safety_claim_verified': False, 'model_called': False}
    outcomes = argument['argument_bundle']['execution_conclusion']['object_outcomes']
    if argument['summary'] != authoritative_summary(request, outcomes):
        issues.append('argument_authoritative_summary_mismatch')
    if argument['limitations'] != authoritative_limitations(request):
        issues.append('argument_authoritative_limitations_mismatch')
    issues.extend(model_review_issues(argument))
    if issues:
        raise _error(issues)
    validate_argument_bundle(argument['argument_bundle'], request)
    return {'contract_status': 'valid_output_contract', 'physical_sufficiency': 'not_evaluated',
            'safety_claim_verified': False, 'model_called': False, 'reasoning_review': 'required'}
