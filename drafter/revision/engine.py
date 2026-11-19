"""Bounded, auditable revision of a GSN argument bundle from one Critic report.

    revise(request, adapter=None)   one round: a validated revised bundle, or an explicit
                                    no-change / unresolved / rejected result
    run_cycle(request, ...)         rounds with re-criticism in between, until a stop reason
    verify_result(request, result)  replay a saved result against its request

A revision edits the argument, never the evidence, the R1 configuration, the
checker results or the stored inputs. It acts only on findings the contract
calls actionable. It does not look for problems itself, so an empty Critic
report gives "no change", which is not evidence that R1 holds.
"""
from copy import deepcopy
import re

from critic import contract as K
from . import adapters as A, contract as C, edits as E, invariants as V

STOP_REASONS = ('no_actionable_findings', 'awaiting_decision', 'no_justified_improvement',
                'insufficient_evidence', 'invalid_input', 'repeated_unchanged_findings', 'round_limit',
                'execution_failure')
OUTCOMES = ('revised', 'no_change', 'unresolved', 'rejected_invalid_input', 'failed')
DISCLAIMER = ('A revision changes the wording and structure of an argument. It does not observe the '
              'execution and makes no physical finding. "No change" and "no remaining finding" mean only '
              'that no actionable Critic finding was left; they do not show that R1 holds or that the robot '
              'was physically safe.')


# Recorded when the adapter does not even declare what it is.
UNKNOWN_ADAPTER = {'name': 'unknown', 'version': '0', 'kind': 'scripted'}


def _skeleton(request, adapter):
    req = request if isinstance(request, dict) else {}

    def pick(key, kind):
        value = req.get(key)
        return value if isinstance(value, kind) and not isinstance(value, bool) else None

    sha = {key: pick(key, str) for key in ('critic_request_sha256', 'critic_report_sha256')}
    try:
        whole = K.digest(request)
    except (ValueError, TypeError, OverflowError, RecursionError):
        whole = None
    return {
        'schema_version': C.RESULT_VERSION, 'revision_id': pick('revision_id', str) or '',
        'round': pick('round', int), 'max_rounds': pick('max_rounds', int),
        'test_fixture': req.get('test_fixture') if isinstance(req.get('test_fixture'), bool) else None,
        'synthetic_findings': None, 'revision_request_sha256': whole, **sha, 'adapter': adapter,
        'outcome': None, 'stop_reason': None, 'status_detail': None, 'request_issues': [],
        'original_argument_bundle_sha256': None, 'revised_argument_bundle': None,
        'revised_argument_bundle_sha256': None, 'recriticism': None, 'proposal': None, 'edits': [],
        'rejected_edits': [], 'diff': [], 'dispositions': [],
        'carried_forward': {'rejected_candidates': [], 'evidence_requests': [], 'unresolved_concerns': []},
        'validators': [], 'manual_review_decisions': [], 'metrics': None, 'disclaimer': DISCLAIMER,
    }


def _metrics(result):
    diff, rows = result['diff'], result['dispositions']

    def count(change):
        return sum(d['change'] == change for d in diff)

    removed_links = sum(d['change'] == 'node_removed' and d['before']['type'] == 'solution' for d in diff)
    new_findings = next((len(v['issues']) for v in result['validators']
                         if v['name'] == 'no_new_rule_findings'), 0)
    graphs = next((v['status'] for v in result['validators'] if v['name'] == 'shared_gsn_validator'), 'not_run')
    return {
        'graphs_valid': {'passed': True, 'failed': False}.get(graphs),
        'nodes_changed': count('node_replaced'), 'nodes_added': count('node_added'),
        'nodes_removed': count('node_removed'), 'edges_added': count('edge_added'),
        'edges_removed': count('edge_removed'), 'object_outcomes_changed': count('object_outcome_changed'),
        'evidence_links_removed': removed_links, 'evidence_links_added': 0,
        'findings_total': len(rows), 'findings_addressed': sum(r['disposition'] == 'edited' for r in rows),
        'findings_remaining': sum(r['disposition'] != 'edited' for r in rows),
        'findings_awaiting_decision': sum(r['classification'] == C.NEEDS_DECISION for r in rows),
        'rejected_candidates': len(result['carried_forward']['rejected_candidates']),
        'evidence_requests': len(result['carried_forward']['evidence_requests']),
        'unresolved_concerns': len(result['carried_forward']['unresolved_concerns']),
        'new_rule_findings': new_findings, 'edits_applied': len(result['edits']),
        'edits_rejected': len(result['rejected_edits']),
        'manual_review_decisions': len(result['manual_review_decisions']),
        'iteration': result['round'],
    }


def _finish(result, outcome, stop_reason, detail=None):
    result.update(outcome=outcome, stop_reason=stop_reason, status_detail=detail)
    result['metrics'] = _metrics(result)
    return result


def _failed(request, adapter, detail):
    return _finish(_skeleton(request, adapter), 'failed', 'execution_failure', detail)


def recriticism_request_id(request):
    """ID of the Critic request for the revised bundle: the first reviewed ID plus ':rev<round>'."""
    base = re.sub(r':rev[0-9]+$', '', str(request['critic_request']['request_id']))
    return f"{base}:rev{request['round']}"


def recriticism_request(request, result):
    """The Critic request for the revised bundle. It differs from the reviewed one only in
    argument_bundle and request_id. Raises ValueError when the result holds no revised bundle."""
    if result.get('outcome') != 'revised':
        raise ValueError('only a revised result has a re-criticism request')
    critic_request = deepcopy(request['critic_request'])
    critic_request['argument_bundle'] = deepcopy(result['revised_argument_bundle'])
    critic_request['request_id'] = recriticism_request_id(request)
    return critic_request


def history_item(request, result):
    """The record of one revised round that the next round's request carries in `history`."""
    if result.get('outcome') != 'revised':
        raise ValueError('only a revised result becomes history')
    by_id = {c['criticism_id']: c for c in request['critic_report']['criticisms']}
    return {
        'round': request['round'], 'revision_id': request['revision_id'],
        'revision_request_sha256': K.digest(request),
        'critic_request_sha256': request['critic_request_sha256'],
        'critic_report_sha256': request['critic_report_sha256'], 'result_sha256': K.digest(result),
        'original_argument_bundle_sha256': result['original_argument_bundle_sha256'],
        'revised_argument_bundle_sha256': result['revised_argument_bundle_sha256'],
        'recriticism_request_sha256': result['recriticism']['request_sha256'],
        'addressed': [{'criticism_id': r['criticism_id'], 'check_id': r['check_id'], 'category': r['category'],
                       'object_id': by_id[r['criticism_id']]['object_id'],
                       'node_id': by_id[r['criticism_id']]['node_id']}
                      for r in result['dispositions'] if r['disposition'] == 'edited'],
    }


def build_context(request, classification, info):
    """What an adapter is given. All of it is a copy."""
    critic_request = request['critic_request']
    context = critic_request['evaluation_context']
    return {
        'revision_id': request['revision_id'], 'round': request['round'], 'max_rounds': request['max_rounds'],
        'requirement_id': context['requirement_id'], 'requirement_version': context['requirement_version'],
        'execution_id': context['execution_id'], 'protected_objects': deepcopy(context['protected_objects']),
        'monitored_interval': deepcopy(context['monitored_interval']),
        'argument_bundle': deepcopy(critic_request['argument_bundle']),
        'findings': E.finding_context(request, classification, info),
        'evidence_requests': deepcopy(classification['evidence_requests']),
        'history': deepcopy(request['history']),
    }


def _dispositions(request, classification):
    decisions = {d['criticism_id']: d for d in request['finding_decisions']}
    rows = []
    for row in classification['findings']:
        actionable = row['status'] in C.ACTIONABLE_STATUSES
        rows.append({
            'criticism_id': row['criticism_id'], 'check_id': row['check_id'], 'category': row['category'],
            'finding_source': row['finding_source'], 'phase': row['phase'], 'blocking': row['blocking'],
            'target': deepcopy(row['target']), 'classification': row['status'],
            'disposition': 'unresolved' if actionable else 'not_actionable',
            'reason': 'not_processed' if actionable else row['status'], 'edit_indexes': [],
            'verified_by_rules': None, 'additional_evidence_needed': row['additional_evidence_needed'],
            'human_review_required': row['human_review_required'],
            'decision': deepcopy(decisions.get(row['criticism_id'])), 'note': None,
        })
    return rows


def _mark(rows, ids, reason, note=None):
    for row in rows:
        if row['criticism_id'] in ids and row['disposition'] != 'not_actionable':
            row.update(disposition='unresolved', reason=reason, note=note)


def _validator(name, issues, skipped=None):
    status = 'failed' if issues else 'passed'
    return {'name': name, 'status': status, 'issues': list(issues),
            'note': None if not skipped else 'not run for: ' + ', '.join(skipped)}


def _revise(request, adapter, adapter_info):
    result = _skeleton(request, adapter_info)
    issues = C.request_issues(request)
    if issues:
        result['request_issues'] = issues
        result['validators'].append(_validator('request_contract', issues))
        return _finish(result, 'rejected_invalid_input', 'invalid_input',
                       'The revision request is not usable; nothing was read from the Critic report.')
    result['validators'].append(_validator('request_contract', []))
    frozen = K.digest(request)
    critic_request, report = request['critic_request'], request['critic_report']
    original = critic_request['argument_bundle']
    classification = C.classify(request)
    findings_before, info = C.fresh_review(critic_request)
    rows = _dispositions(request, classification)
    result.update(
        synthetic_findings=deepcopy(request['synthetic_findings']),
        original_argument_bundle_sha256=K.digest(original), dispositions=rows,
        manual_review_decisions=deepcopy(request['finding_decisions']),
        carried_forward={'rejected_candidates': deepcopy(report['rejected_llm_findings']),
                         'evidence_requests': deepcopy(report['evidence_requests']),
                         'unresolved_concerns': list(report['unresolved_concerns'])})
    actionable = set(classification['actionable'])

    if not classification['report_usable'] and not classification['link_repair']:
        return _finish(result, 'rejected_invalid_input', 'invalid_input',
                       f"The Critic report is {report['review_status']}, so no finding in it is revised.")
    if request['history']:
        addressed = {C.objection_key(a) for a in request['history'][-1]['addressed']}
        repeated = {c['criticism_id'] for c in report['criticisms'] if C.objection_key(c) in addressed}
        if repeated:
            _mark(rows, repeated, 'repeated_after_previous_edit')
            return _finish(result, 'unresolved', 'repeated_unchanged_findings',
                           'The Critic raised again a finding the previous round edited for: '
                           + ', '.join(sorted(repeated)) + '.')
    if not actionable:
        statuses = {row['classification'] for row in rows}
        if not rows:
            return _finish(result, 'no_change', 'no_actionable_findings',
                           'The Critic report has no criticism. Nothing was changed. '
                           f"{len(report['rejected_llm_findings'])} rejected candidate(s) and "
                           f"{len(report['unresolved_concerns'])} unresolved concern(s) stay open.")
        stop = ('awaiting_decision' if C.NEEDS_DECISION in statuses else
                'insufficient_evidence' if C.UNKNOWN_EVIDENCE in statuses else 'no_actionable_findings')
        return _finish(result, 'unresolved', stop, 'No criticism may be acted on. Nothing was changed.')
    if request['round'] > request['max_rounds']:
        _mark(rows, actionable, 'round_limit_reached')
        return _finish(result, 'unresolved', 'round_limit',
                       f"The limit of {request['max_rounds']} revision rounds is reached. Nothing was changed.")

    context = build_context(request, classification, info)
    findings = {e['criticism']['criticism_id']: e for e in context['findings']}
    try:
        proposal = adapter.propose(deepcopy(context))
        K.canonical(proposal)
    except Exception as error:  # the adapter is untrusted code: any failure ends the round, nothing applied
        return _finish(result, 'failed', 'execution_failure',
                       f'The adapter failed with {type(error).__name__}; nothing was applied.')
    if K.digest(request) != frozen:
        return _finish(result, 'failed', 'execution_failure', 'The request changed during the adapter call.')
    problems = E.proposal_issues(proposal)
    if problems:
        return _finish(result, 'failed', 'execution_failure',
                       'The adapter answer is malformed: ' + '; '.join(problems) + '.')
    result['proposal'] = deepcopy(proposal)

    accepted, taken = [], {'findings': set(), 'targets': set()}
    for index, edit in enumerate(proposal['edits']):
        reasons = E.edit_issues(edit, findings, original, taken)
        if reasons:
            result['rejected_edits'].append({'index': index, 'edit': deepcopy(edit), 'reasons': reasons})
        else:
            accepted.append(deepcopy(edit))
    declined = {d['criticism_id']: d for d in proposal['declined'] if d['criticism_id'] in actionable}
    for cid, d in declined.items():
        _mark(rows, {cid}, 'adapter_' + d['reason'], d['note'])
    cited = {i for edit in proposal['edits'] if isinstance(edit, dict)
             for i in (edit.get('finding_ids') if isinstance(edit.get('finding_ids'), list) else [])
             if isinstance(i, str)}
    _mark(rows, actionable - cited - set(declined), 'adapter_gave_no_answer')
    if result['rejected_edits']:
        refused = {i for x in result['rejected_edits'] if isinstance(x['edit'], dict)
                   for i in (x['edit'].get('finding_ids') if isinstance(x['edit'].get('finding_ids'), list)
                             else []) if isinstance(i, str)}
        _mark(rows, cited - refused, 'not_applied_because_another_edit_was_refused')
        _mark(rows, refused, 'edit_rejected')
        return _finish(result, 'unresolved', 'no_justified_improvement',
                       f"{len(result['rejected_edits'])} proposed edit(s) were refused, so no edit of this "
                       'round was applied. The original bundle is unchanged.')
    if not accepted:
        reasons = {d['reason'] for d in declined.values()}
        stop = 'insufficient_evidence' if reasons == {'insufficient_evidence'} else 'no_justified_improvement'
        return _finish(result, 'unresolved', stop, 'No edit could be justified. Nothing was changed.')

    revised, by = E.apply(request, accepted, adapter_info)
    diff = V.attribute(V.compare(original, revised), by)
    revised_request = deepcopy(critic_request)
    revised_request.update(argument_bundle=revised, request_id=recriticism_request_id(request))
    by_id = {c['criticism_id']: c for c in report['criticisms']}
    cited_rules = [by_id[i] for edit in accepted for i in edit['finding_ids']
                   if by_id[i]['finding_source'] == 'deterministic']
    findings_after, info_after = C.fresh_review(revised_request)
    invalid, new, stuck = V.rule_issues(findings_before, findings_after, info_after, cited_rules)
    graph_problems, skipped = V.gsn_issues(revised_request, revised)
    checks = [
        _validator('frozen_inputs', V.frozen_issues(critic_request, revised_request)),
        _validator('diff_rules', V.diff_rule_issues(request, revised, diff, accepted, info)),
        _validator('critic_input_checks', invalid),
        _validator('no_new_rule_findings', new),
        _validator('cited_rule_findings_cleared', stuck),
        _validator('shared_gsn_validator', graph_problems, skipped),
        _validator('drafter_structure_rules', V.structure_issues(original, revised)),
    ]
    result['validators'].extend(checks)
    if K.digest(request) != frozen:
        return _finish(result, 'failed', 'execution_failure', 'The request changed during the revision.')
    if any(v['status'] == 'failed' for v in checks):
        _mark(rows, cited, 'validation_failed')
        return _finish(result, 'unresolved', 'no_justified_improvement',
                       'The edited bundle failed validation, so it was discarded. The original bundle is '
                       'unchanged.')

    for index, edit in enumerate(accepted):
        for row in rows:
            if row['criticism_id'] in edit['finding_ids']:
                row.update(disposition='edited', reason=None, edit_indexes=[index], note=None,
                           verified_by_rules=True if row['finding_source'] == 'deterministic' else None)
    result.update(
        edits=accepted, diff=diff, revised_argument_bundle=revised,
        revised_argument_bundle_sha256=K.digest(revised),
        recriticism={'request_id': revised_request['request_id'], 'request_sha256': K.digest(revised_request)})
    return _finish(result, 'revised', None,
                   'The bundle was revised and validated. Rule findings were re-checked here. A model-proposed '
                   'finding counts as addressed only after the Critic has reviewed the revised bundle again.')


def revise(request, adapter=None):
    """One revision round. Never raises and never changes `request`.

    request: dict following schemas/revision_request.schema.json
    adapter: DeterministicAdapter (default), ScriptedAdapter or a model adapter (see adapters.py)
    returns: dict following schemas/revision_result.schema.json

    outcome says what happened:
      revised                 edits were applied and the revised bundle passed every validator;
                              stop_reason is null and `recriticism` names the next Critic request
      no_change               the Critic report has no criticism
      unresolved              criticisms remain and nothing was changed (see stop_reason, dispositions)
      rejected_invalid_input  the request or the Critic report is not usable
      failed                  the adapter or this module failed; nothing was applied
    """
    adapter = adapter if adapter is not None else A.DeterministicAdapter()
    try:
        adapter_info = A.describe(adapter)
    except ValueError as error:
        return _failed(request, dict(UNKNOWN_ADAPTER), str(error))
    try:
        result = _revise(request, adapter, adapter_info)
        problems = C.schema_problems(result, 'revision_result')
    except Exception as error:  # a bug here must not look like a revision
        return _failed(request, adapter_info, f'The revision raised {type(error).__name__}; this is a bug.')
    if problems:
        return _failed(request, adapter_info, 'The result failed its own schema: ' + '; '.join(problems[:5]))
    return result


class _Replay:
    """Feeds a saved proposal back through the engine."""

    def __init__(self, result):
        self.name, self.version, self.kind = (result['adapter'][k] for k in ('name', 'version', 'kind'))
        self.proposal = result['proposal']

    def propose(self, context):
        if self.proposal is None:
            raise RuntimeError('the saved result records no proposal')
        return deepcopy(self.proposal)


def verify_result(request, result):
    """Issues found when a saved result is replayed against its request; an empty list means it holds.

    The engine is deterministic once the adapter's proposal is fixed, and the result stores that
    proposal. Running the same request with the stored proposal must give the same result, field for
    field. A result with outcome 'failed' cannot be verified this way.
    """
    try:
        problems = C.schema_problems(result, 'revision_result')
    except (TypeError, ValueError, RecursionError) as error:
        return ['result_unreadable:' + type(error).__name__]
    if problems:
        return problems
    if result['outcome'] == 'failed':
        return ['failed_results_cannot_be_replayed']
    expected = revise(request, _Replay(result))
    if expected == result:
        return []
    return ['result_does_not_replay:' + ','.join(sorted(k for k in set(expected) | set(result)
                                                         if expected.get(k) != result.get(k)))]


def _backend(request):
    """How the embedded Critic report was produced: 'none' means rule checks only, no model."""
    try:
        return str(request['critic_report']['llm']['backend'])
    except (KeyError, TypeError):
        return None


def _round_summary(request, result, report_after):
    return {
        'round': result['round'], 'critic_backend': _backend(request),
        'revision_request_sha256': result['revision_request_sha256'],
        'critic_request_sha256': result['critic_request_sha256'],
        'critic_report_sha256': result['critic_report_sha256'], 'result_sha256': K.digest(result),
        'outcome': result['outcome'], 'stop_reason': result['stop_reason'],
        'edits_applied': len(result['edits']),
        'edited_findings': [r['criticism_id'] for r in result['dispositions'] if r['disposition'] == 'edited'],
        'open_findings': [r['criticism_id'] for r in result['dispositions'] if r['disposition'] != 'edited'],
        'revised_argument_bundle_sha256': result['revised_argument_bundle_sha256'],
        'recriticism_request_sha256': None if result['recriticism'] is None
        else result['recriticism']['request_sha256'],
        'recriticism_report_sha256': None if report_after is None else K.digest(report_after),
    }


def run_cycle(request, *, adapter=None, review=None, decide=None, synthetic_label=None):
    """Revise, have the Critic review the revised bundle, and repeat until a stop reason.

    request:  the round-1 revision request
    adapter:  as for revise()
    review:   callable(critic_request) -> Critic report. Default: critic.review with rule checks only.
              Pass a function that calls a model to re-criticise with live inference.
    decide:   callable(report, round_number) -> finding_decisions for that report. Default: none, so a
              later report whose findings need a decision stops the cycle with 'awaiting_decision'.
    synthetic_label: label for later rounds; defaults to the label of `request`.

    Returns {'cycle': summary following schemas/revision_cycle.schema.json,
             'requests': [...], 'results': [...], 'reports': [...]}.
    requests[i] and results[i] belong to the same round; reports[i] is the Critic report on the bundle
    results[i] revised, and is embedded in requests[i + 1]. Nothing is written to disk here.

    The last request always holds the latest Critic report on the final bundle. A final report with no
    criticism ends the cycle with 'no_actionable_findings'. That is not evidence that R1 holds. With the
    default rule-only review it also does not show that a model-proposed finding is gone: the rules
    cannot raise that kind of finding. critic_backend in the summary says how each report was made.
    """
    if review is None:
        import critic
        review = critic.review
    requests, results, reports = [], [], []
    current, stop, detail = deepcopy(request), None, None
    while True:
        result = revise(current, adapter)
        requests.append(current)
        results.append(result)
        if result['stop_reason'] is not None:
            stop, detail = result['stop_reason'], result['status_detail']
            break
        try:
            critic_request = recriticism_request(current, result)
            report = review(deepcopy(critic_request))
            decisions = list(decide(deepcopy(report), current['round'] + 1)) if decide is not None else []
            label = synthetic_label if synthetic_label is not None else current['synthetic_findings']['label']
            following = C.build_request(
                current['revision_id'], critic_request, report, finding_decisions=decisions,
                synthetic_label=label, round_number=current['round'] + 1, max_rounds=current['max_rounds'],
                history=current['history'] + [history_item(current, result)],
                repair_invalid_evidence_links=bool(current.get('repair_invalid_evidence_links')))
        except Exception as error:  # re-criticism is outside this module: fail closed, keep what exists
            stop = 'execution_failure'
            detail = f'Re-criticism after round {current["round"]} failed: {type(error).__name__}: {error}'
            break
        reports.append(report)
        current = following

    revised = [r for r in results if r['outcome'] == 'revised']
    first = requests[0].get('critic_request') if isinstance(requests[0], dict) else None
    initial = first.get('argument_bundle') if isinstance(first, dict) else None
    final = revised[-1]['revised_argument_bundle'] if revised else initial
    last = results[-1]

    def digest_or_none(value):
        try:
            return None if value is None else K.digest(value)
        except (ValueError, TypeError, OverflowError, RecursionError):
            return None

    cycle = {
        'schema_version': C.CYCLE_VERSION, 'revision_id': last['revision_id'],
        'test_fixture': last['test_fixture'], 'synthetic_findings': results[0]['synthetic_findings'],
        'max_rounds': last['max_rounds'], 'revision_rounds': len(revised),
        'stop_reason': stop, 'status_detail': detail,
        'final_outcome': 'revised' if revised else last['outcome'],
        'initial_argument_bundle_sha256': digest_or_none(initial),
        'final_argument_bundle_sha256': digest_or_none(final),
        'rounds': [_round_summary(requests[i], results[i], reports[i] if i < len(reports) else None)
                   for i in range(len(results))],
        'final_review': {
            'critic_request_sha256': last['critic_request_sha256'],
            'critic_report_sha256': last['critic_report_sha256'], 'critic_backend': _backend(requests[-1]),
            'open_findings': [deepcopy(r) for r in last['dispositions'] if r['disposition'] != 'edited'],
            'carried_forward': deepcopy(last['carried_forward']),
            'reviewed_final_bundle': last['outcome'] != 'revised',
        },
        'disclaimer': DISCLAIMER,
    }
    return {'cycle': cycle, 'requests': requests, 'results': results, 'reports': reports}
