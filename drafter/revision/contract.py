"""Critic-to-Revision consumer mapping. No inference, no graph edits, no physical checking.

A revision request wraps one unchanged Critic request and the unchanged Critic
report for it. This module checks that pair and says, for every criticism, whether
a revision may act on it. Nothing here treats a schema-valid finding as verified:
a model-proposed finding is actionable only with an explicit recorded decision.
"""
from copy import deepcopy
from pathlib import Path
import json

from jsonschema import Draft202012Validator

from critic import checks, contract as K, schema as SCHEMA
from critic.critic import CRITIC_VERSION
from critic.claims import CHECK_ID as ABSOLUTE_CLAIM_CHECK

REQUEST_VERSION = 'drafter-revision-request/0.1.0'
RESULT_VERSION = 'drafter-revision-result/0.1.0'
CYCLE_VERSION = 'drafter-revision-cycle/0.1.0'
HERE = Path(__file__).resolve().parent
USABLE_REVIEWS = ('completed', 'completed_llm_failed')
# Compared between the report and a fresh rule-based run on the same request.
DETERMINISTIC_KEYS = ('check_id', 'phase', 'category', 'severity', 'blocking', 'object_id', 'node_id',
                      'explanation', 'evidence_ids', 'suggested_action', 'additional_evidence_needed',
                      'human_review_required')
# Proposed list (mapping question 4): the validation-phase citation defects of one Solution node, all
# raised by critic.checks._check_solution. Defects of a registry record itself are never on this list,
# because a revision does not touch source evidence.
LINK_REPAIR_CHECKS = ('EV-MISSING', 'EV-WRONG-EXECUTION', 'EV-WRONG-OBJECT', 'EV-RELATED-CASE',
                      'EV-SCOPE-MISMATCH', 'EV-SOURCE-MISMATCH', 'EV-NO-INTERVAL', 'EV-INTERVAL-MISMATCH',
                      'EV-AUTHORITY')

# Critic versions whose reports may be revised. They share the request and report contracts, the prompt and
# the model screening; 0.5.0 only adds a rule. Because the rule-based findings and the checker admission are
# always recomputed with the current Critic (below), a report from an older listed version is accepted only
# when its rule-based part is exactly what the current Critic finds. A report that misses a finding of a
# newer rule fails with report_deterministic_findings_mismatch.
COMPATIBLE_CRITIC_VERSIONS = ('0.4.0', CRITIC_VERSION)
ACTIONABLE = 'actionable'
ACTIONABLE_LINK_REPAIR = 'actionable_link_repair'
NEEDS_DECISION = 'needs_human_decision'
DECLINED = 'declined'
VALIDATION_PHASE = 'not_actionable_validation_phase'
TARGET_MISSING = 'not_actionable_target_missing'
UNKNOWN_EVIDENCE = 'not_actionable_unknown_evidence'
REPORT_UNUSABLE = 'not_actionable_report_unusable'
ACTIONABLE_STATUSES = (ACTIONABLE, ACTIONABLE_LINK_REPAIR)


def load_schema(name='revision_request'):
    return json.loads((HERE / 'schemas' / (name + '.schema.json')).read_text(encoding='utf-8'))


def schema_problems(value, name):
    """Sorted schema errors of one of this package's schemas."""
    return sorted('schema:' + '/'.join(map(str, e.absolute_path)) + ':' + e.message
                  for e in Draft202012Validator(load_schema(name)).iter_errors(value))


def fresh_review(critic_request):
    """Rule-based findings and admission recomputed here, never read from the report."""
    return checks.run_all(deepcopy(critic_request))


def fingerprint(finding):
    """What makes two findings the same finding across rule runs. criticism_id is only a position."""
    return (finding['check_id'], finding['category'], finding['object_id'], finding['node_id'])


def objection_key(finding):
    """What makes two findings the same objection for repeat detection: category and location.

    The check ID is left out on purpose, so a model objection that repeats a rule objection at the same
    place (or the reverse) counts as the same objection raised again.
    """
    return (finding['category'], finding['object_id'], finding['node_id'])


def request_issues(request):
    """Every reason this revision request cannot be used; an empty list means usable.

    Order: this wrapper's schema, the two embedded Critic contracts, then the
    bindings between wrapper, request, report and history.
    """
    try:
        K.canonical(request)
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        return ['invalid_json:' + str(error)]
    problems = schema_problems(request, 'revision_request')
    if problems:
        return problems
    critic_request, report = request['critic_request'], request['critic_report']
    issues = ['critic_report_schema:' + text
              for text in SCHEMA.errors(report, SCHEMA.load('report'), limit=5)]
    findings, info = fresh_review(critic_request)
    if info['fatal']:
        issues.append('critic_request_unreadable')
    if issues:
        return issues

    if K.digest(critic_request) != request['critic_request_sha256']:
        issues.append('critic_request_digest_mismatch')
    if K.digest(report) != request['critic_report_sha256']:
        issues.append('critic_report_digest_mismatch')
    if report['critic_version'] not in COMPATIBLE_CRITIC_VERSIONS:
        issues.append('critic_version_mismatch')
    # The same derivations critic.review uses, so a rejected-input report still binds.
    context = critic_request.get('evaluation_context')
    context = context if isinstance(context, dict) else {}
    if report['request_id'] != str(critic_request.get('request_id', '')):
        issues.append('report_request_id_mismatch')
    if report['execution_id'] != str(context.get('execution_id', '')):
        issues.append('report_execution_mismatch')
    if (report['test_fixture'] != bool(critic_request.get('test_fixture'))
            or request['test_fixture'] != report['test_fixture']):
        issues.append('test_fixture_mismatch')
    # Only a report whose model step ran records the request hash.
    recorded = report['llm']['request_sha256']
    if recorded is not None and recorded != K.digest(critic_request):
        issues.append('report_request_hash_mismatch')
    if report['input_valid'] != info['input_valid']:
        issues.append('report_input_validity_mismatch')
    if (report['review_status'] == 'rejected_invalid_input') != (not info['input_valid']):
        issues.append('report_review_status_mismatch')
    if report['review_status'] != 'internal_error':
        claimed = [{k: c[k] for k in DETERMINISTIC_KEYS} for c in report['criticisms']
                   if c['finding_source'] == 'deterministic']
        if claimed != [{k: f[k] for k in DETERMINISTIC_KEYS} for f in findings]:
            issues.append('report_deterministic_findings_mismatch')
        if report['checker_admission'] != info['checker_admission']:
            issues.append('report_checker_admission_mismatch')

    synthetic = request['synthetic_findings']['present']
    if report['llm']['backend'] == 'scripted' and not synthetic:
        issues.append('scripted_report_requires_synthetic_label')
    known = [c['criticism_id'] for c in report['criticisms']]
    if len(known) != len(set(known)):
        issues.append('duplicate_criticism_id')
    decided = [d['criticism_id'] for d in request['finding_decisions']]
    if len(decided) != len(set(decided)):
        issues.append('duplicate_finding_decision')
    for decision in request['finding_decisions']:
        if decision['criticism_id'] not in known:
            issues.append('decision_for_unknown_criticism:' + decision['criticism_id'])
        if decision['decided_by'] == 'synthetic_test_label' and not synthetic:
            issues.append('synthetic_decision_without_synthetic_label:' + decision['criticism_id'])
        if decision['decided_by'] == 'human_review' and not (decision['reviewer'] or '').strip():
            issues.append('human_decision_requires_reviewer:' + decision['criticism_id'])
    issues.extend(_history_issues(request))
    return sorted(set(issues))


def _history_issues(request):
    """Round bookkeeping. Round max_rounds + 1 is the final review: it is reported, never edited."""
    issues, history = [], request['history']
    if request['round'] > request['max_rounds'] + 1:
        issues.append('round_exceeds_max_rounds')
    if len(history) != request['round'] - 1:
        issues.append('history_length_must_equal_round_minus_one')
        return issues
    for index, item in enumerate(history):
        if item['round'] != index + 1:
            issues.append('history_round_sequence')
        if item['revision_id'] != request['revision_id']:
            issues.append('history_revision_id_mismatch')
        following = history[index + 1]['critic_request_sha256'] if index + 1 < len(history) \
            else request['critic_request_sha256']
        if item['recriticism_request_sha256'] != following:
            issues.append('history_chain_mismatch')
    return issues


def _graph_index(critic_request):
    """{object_id: {node_id: node type}}, or None when the graphs cannot be indexed safely."""
    out = {}
    try:
        for item in critic_request['argument_bundle']['graphs']:
            object_id, nodes = item['object_id'], {}
            for node in item['graph']['nodes']:
                if not isinstance(node['id'], str) or node['id'] in nodes:
                    return None
                nodes[node['id']] = node.get('type')
            if not isinstance(object_id, str) or object_id in out:
                return None
            out[object_id] = nodes
    except (KeyError, TypeError, AttributeError):
        return None
    return out


def _target(criticism, graphs):
    """(kind, object_id, node_id) or None when the named object or node does not exist uniquely."""
    object_id, node_id = criticism['object_id'], criticism['node_id']
    if object_id is not None and object_id not in graphs:
        return None
    if node_id is None:
        return ('object', object_id, None) if object_id is not None else ('execution', None, None)
    holders = [o for o, nodes in graphs.items() if node_id in nodes and (object_id is None or o == object_id)]
    return ('node', holders[0], node_id) if len(holders) == 1 else None


def _link_repair_open(request, report, info, graphs):
    """True when the caller asked for link repair and broken Solution citations are the only reason
    the input was rejected. Any other validation problem keeps the whole request unusable."""
    if not request.get('repair_invalid_evidence_links') or info['fatal'] or graphs is None:
        return False
    if report['review_status'] != 'rejected_invalid_input':
        return False
    blocking = [c for c in report['criticisms'] if c['phase'] == 'validation']
    for c in blocking:
        target = _target(c, graphs)
        if (c['check_id'] not in LINK_REPAIR_CHECKS or c['finding_source'] != 'deterministic'
                or target is None or target[0] != 'node' or graphs[target[1]][target[2]] != 'solution'):
            return False
    return bool(blocking)


def classify(request):
    """Status of every criticism, rejected candidate and concern in a usable request.

    Call request_issues first; this function assumes it returned no issue.
    """
    critic_request, report = request['critic_request'], request['critic_report']
    _, info = fresh_review(critic_request)
    usable = report['review_status'] in USABLE_REVIEWS and info['input_valid']
    graphs = None if info['fatal'] else _graph_index(critic_request)
    repair = _link_repair_open(request, report, info, graphs)
    evidence = set(info['records']) | {a['assessment_id'] for a in info['checker_admission'] if a['admitted']}
    decisions = {d['criticism_id']: d for d in request['finding_decisions']}
    findings = []
    for c in report['criticisms']:
        decision = decisions.get(c['criticism_id'])
        target = _target(c, graphs) if graphs is not None and (usable or repair) else None
        needs_decision = c['finding_source'] != 'deterministic' or c['human_review_required']
        if repair and c['phase'] == 'validation':
            status = ACTIONABLE_LINK_REPAIR
        elif c['phase'] == 'validation':
            status = VALIDATION_PHASE
        elif not usable:
            status = REPORT_UNUSABLE
        elif target is None:
            status = TARGET_MISSING
        elif any(e not in evidence for e in c['evidence_ids']):
            status = UNKNOWN_EVIDENCE
        elif decision is not None and decision['decision'] == 'declined':
            status = DECLINED
        elif needs_decision and decision is None:
            status = NEEDS_DECISION
        else:
            status = ACTIONABLE
        findings.append({
            'criticism_id': c['criticism_id'], 'status': status,
            'target': None if target is None else dict(zip(('kind', 'object_id', 'node_id'), target)),
            'node_type': graphs[target[1]][target[2]] if target is not None and target[0] == 'node' else None,
            'check_id': c['check_id'], 'phase': c['phase'],
            'category': c['category'], 'finding_source': c['finding_source'], 'blocking': c['blocking'],
            'additional_evidence_needed': c['additional_evidence_needed'],
            'human_review_required': c['human_review_required'],
            'decided_by': None if decision is None else decision['decided_by'],
        })
    return {
        'review_status': report['review_status'], 'report_usable': usable, 'link_repair': repair,
        'findings': findings,
        'actionable': [f['criticism_id'] for f in findings if f['status'] in ACTIONABLE_STATUSES],
        'rejected_candidates': [{'index': i, 'reason': x['reason']}
                                for i, x in enumerate(report['rejected_llm_findings'])],
        'evidence_requests': deepcopy(report['evidence_requests']),
        'unresolved_concerns': list(report['unresolved_concerns']),
    }


def build_request(revision_id, critic_request, critic_report, *, finding_decisions=(), synthetic_label=None,
                  round_number=1, max_rounds=2, history=(), repair_invalid_evidence_links=False, check=True):
    """Wrap independent copies; raise ValueError listing every issue if the result is unusable.

    check=False returns the wrapper even when it is unusable. It exists only to save examples of requests the
    revision must refuse; revise() still checks every request it is given.
    """
    request = {
        'schema_version': REQUEST_VERSION, 'revision_id': revision_id,
        'test_fixture': bool(critic_request.get('test_fixture')) if isinstance(critic_request, dict) else False,
        'synthetic_findings': {'present': synthetic_label is not None, 'label': synthetic_label},
        'round': round_number, 'max_rounds': max_rounds,
        'critic_request': deepcopy(critic_request), 'critic_request_sha256': K.digest(critic_request),
        'critic_report': deepcopy(critic_report), 'critic_report_sha256': K.digest(critic_report),
        'finding_decisions': deepcopy(list(finding_decisions)), 'history': deepcopy(list(history)),
    }
    if repair_invalid_evidence_links:
        request['repair_invalid_evidence_links'] = True
    issues = request_issues(request) if check else []
    if issues:
        raise ValueError('; '.join(issues))
    return request
