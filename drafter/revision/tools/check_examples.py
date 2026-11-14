"""Verify the saved examples. No model, no network, nothing is written.

    python3 -m drafter.revision.tools.check_examples

Exit code 0 only if every check passes.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

from jsonschema import Draft202012Validator

from critic import checks, contract as K
from drafter.revision import contract as C, edits as E, engine as G
from drafter.revision.tools import build_examples as B

EXPECTED = {
    'synthetic_actionable.revision_request.json': {
        'review_status': 'completed', 'actionable': ['CRIT-001'], 'statuses': {'CRIT-001': C.ACTIONABLE},
        'targets': {'CRIT-001': {'kind': 'node', 'object_id': 'cream_cheese_1', 'node_id': 'cream_cheese_1:G1'}},
        'rejected': 0, 'synthetic': True, 'backend': 'scripted', 'outcome': ('revised', None)},
    'synthetic_rejected_unresolved.revision_request.json': {
        'review_status': 'completed', 'actionable': [], 'statuses': {}, 'targets': {},
        'rejected': 4, 'synthetic': True, 'backend': 'scripted',
        'outcome': ('no_change', 'no_actionable_findings')},
    'saved_zero_finding.revision_request.json': {
        'review_status': 'completed', 'actionable': [], 'statuses': {}, 'targets': {},
        'rejected': 0, 'synthetic': False, 'backend': 'openai_compatible',
        'outcome': ('no_change', 'no_actionable_findings')},
    'saved_zero_finding_controlled_negative.revision_request.json': {
        'review_status': 'completed', 'actionable': [], 'statuses': {}, 'targets': {},
        'rejected': 0, 'synthetic': False, 'backend': 'openai_compatible',
        'outcome': ('no_change', 'no_actionable_findings')},
}
REJECTION_STARTS = ("node 'ketchup_1:G9' does not exist", 'cites evidence IDs that are not in the package',
                    'C09_UNRESOLVED:', 'category C02 is decided by the rule-based checks only')
FAILED = []


def check(name, passed, detail=''):
    print(('PASS  ' if passed else 'FAIL  ') + name + (('  ' + detail) if detail and not passed else ''))
    if not passed:
        FAILED.append(name)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def without_latency(report):
    value = deepcopy(report)
    value['llm']['latency_s'] = None
    return value


def check_requests(original, mutated, rebuilt):
    report_schema = load(B.ROOT / 'critic' / 'schemas' / 'critic_report.schema.json')
    request_schema = C.load_schema()
    Draft202012Validator.check_schema(request_schema)
    saved = {'saved_zero_finding.revision_request.json': (original, B.read('critic.qwen.report.json')),
             'saved_zero_finding_controlled_negative.revision_request.json':
                 (mutated, B.read('critic.controlled-negative.qwen.report.json'))}
    for name, expected in EXPECTED.items():
        request = load(B.OUT / name)
        report, critic_request = request['critic_report'], request['critic_request']
        check(name + ': wrapper matches its JSON schema',
              not list(Draft202012Validator(request_schema).iter_errors(request)))
        check(name + ': Critic report matches critic_report.schema.json (jsonschema library)',
              not list(Draft202012Validator(report_schema).iter_errors(report)))
        check(name + ': Critic request passes the Critic input checks',
              checks.run_all(critic_request)[1]['input_valid'])
        issues = C.request_issues(request)
        check(name + ': no binding issue', issues == [], '; '.join(issues))
        check(name + ': digests recomputed', K.digest(critic_request) == request['critic_request_sha256']
              and K.digest(report) == request['critic_report_sha256'])
        check(name + ': embedded Critic request equals a fixture request', critic_request in (original, mutated))
        check(name + ': synthetic label and backend',
              request['synthetic_findings']['present'] is expected['synthetic']
              and report['llm']['backend'] == expected['backend'])
        result = C.classify(request)
        check(name + ': review status', result['review_status'] == expected['review_status'])
        check(name + ': actionable findings', result['actionable'] == expected['actionable'], str(result['actionable']))
        check(name + ': finding statuses and targets',
              {f['criticism_id']: f['status'] for f in result['findings']} == expected['statuses']
              and {f['criticism_id']: f['target'] for f in result['findings']} == expected['targets'])
        check(name + ': rejected candidates', len(result['rejected_candidates']) == expected['rejected'])
        check(name + ': unresolved concerns carried unchanged',
              result['unresolved_concerns'] == report['unresolved_concerns'])
        if name in saved:
            check(name + ': embeds the saved fixture request and report unchanged',
                  (critic_request, report) == saved[name] and report['criticisms'] == [])
        else:
            check(name + ': regenerated from the real Critic (latency ignored)',
                  without_latency(rebuilt[name]['critic_report']) == without_latency(report)
                  and without_latency(load(B.OUT / name.replace('revision_request', 'critic_report')))
                  == without_latency(report))

    rejected = load(B.OUT / 'synthetic_rejected_unresolved.revision_request.json')
    reasons = [x['reason'] for x in rejected['critic_report']['rejected_llm_findings']]
    check('rejected example: the four expected rejection reasons, in order',
          len(reasons) == 4 and all(r.startswith(s) for r, s in zip(reasons, REJECTION_STARTS)), str(reasons))
    check('rejected example: the deferred C09 is also an unresolved concern',
          sum(u.startswith('C09_UNRESOLVED:') for u in rejected['critic_report']['unresolved_concerns']) == 1)


def check_fail_closed(original):
    """Each change to a valid request must produce the named issue."""
    base = load(B.OUT / 'synthetic_actionable.revision_request.json')

    def tampered(edit):
        value = deepcopy(base)
        edit(value)
        return value

    def rehash(value):
        value['critic_report_sha256'] = K.digest(value['critic_report'])
        value['critic_request_sha256'] = K.digest(value['critic_request'])

    def forge_deterministic(value):
        forged = deepcopy(value['critic_report']['criticisms'][0])
        forged.update(criticism_id='CRIT-002', finding_source='deterministic', check_id='CONCL-UNSUPPORTED',
                      category='C06', category_name=K.CATEGORIES['C06'], human_review_required=False, blocking=True)
        value['critic_report']['criticisms'].append(forged)
        rehash(value)

    def other_request(value):
        value['critic_request'] = deepcopy(original)
        rehash(value)

    def drop_label(value):
        value['synthetic_findings'] = {'present': False, 'label': None}
        value['finding_decisions'][0].update(decided_by='human_review', reviewer='A reviewer')

    cases = {
        'report edited without re-hashing': (
            lambda v: v['critic_report']['criticisms'][0].update(severity='low'), 'critic_report_digest_mismatch'),
        'forged deterministic finding, re-hashed': (forge_deterministic, 'report_deterministic_findings_mismatch'),
        'report paired with a different request, re-hashed': (other_request, 'report_request_id_mismatch'),
        'scripted report without the synthetic label': (drop_label, 'scripted_report_requires_synthetic_label'),
        'decision for a criticism that is not in the report': (
            lambda v: v['finding_decisions'][0].update(criticism_id='CRIT-009'),
            'decision_for_unknown_criticism:CRIT-009'),
        'human decision without a reviewer': (
            lambda v: v['finding_decisions'][0].update(decided_by='human_review'),
            'human_decision_requires_reviewer:CRIT-001'),
        'round above max_rounds + 1': (lambda v: v.update(round=4), 'round_exceeds_max_rounds'),
        'unknown wrapper field': (lambda v: v.update(extra=1), 'schema::'),
    }
    for name, (edit, wanted) in cases.items():
        issues = C.request_issues(tampered(edit))
        check('fail closed: ' + name, any(i.startswith(wanted) for i in issues), str(issues))

    for name, decisions, wanted in (
            ('no decision', [], C.NEEDS_DECISION),
            ('declined', [{**base['finding_decisions'][0], 'decision': 'declined'}], C.DECLINED)):
        value = tampered(lambda v: v.update(finding_decisions=decisions))
        result = C.classify(value)
        check('model-proposed finding with ' + name + ' is not actionable',
              C.request_issues(value) == [] and result['actionable'] == []
              and result['findings'][0]['status'] == wanted)


def check_results():
    """Every saved result is exactly what the revision returns for its saved request."""
    result_schema = C.load_schema('revision_result')
    Draft202012Validator.check_schema(result_schema)
    for name, expected in EXPECTED.items():
        request = load(B.OUT / name)
        label = name.replace('revision_request', 'revision_result')
        result = load(B.OUT / label)
        check(label + ': matches its JSON schema',
              not list(Draft202012Validator(result_schema).iter_errors(result)))
        check(label + ': outcome and stop reason',
              (result['outcome'], result['stop_reason']) == expected['outcome'], str(result['outcome']))
        check(label + ': equals a fresh run on the saved request', G.revise(request) == result)
        issues = G.verify_result(request, result)
        check(label + ': replays', issues == [], '; '.join(issues))
        check(label + ': bound to its request', result['revision_request_sha256'] == K.digest(request)
              and result['critic_report_sha256'] == request['critic_report_sha256'])
        check(label + ': synthetic label carried', result['synthetic_findings'] == request['synthetic_findings'])

    request = load(B.OUT / 'synthetic_actionable.revision_request.json')
    result = load(B.OUT / 'synthetic_actionable.revision_result.json')
    diff = result['diff']
    check('complete example: one node replaced, the guarantee is gone',
          [(d['change'], d['node_id']) for d in diff] == [('node_replaced', 'cream_cheese_1:G1')]
          and diff[0]['before']['statement'] == B.GUARANTEE and 'guarantee' not in diff[0]['after']['statement'])
    check('complete example: every validator passed',
          len(result['validators']) == 8 and all(v['status'] == 'passed' for v in result['validators']))
    check('complete example: the edit names its finding and a justification',
          result['edits'][0]['finding_ids'] == ['CRIT-001'] and B.GUARANTEE in result['edits'][0]['justification'])
    before, after = request['critic_request'], G.recriticism_request(request, result)
    check('complete example: only the bundle and the request ID differ in the re-criticism request',
          {k for k in before if before[k] != after[k]} == {'argument_bundle', 'request_id'}
          and K.digest(after) == result['recriticism']['request_sha256'])
    changed = [(o['object_id'], n['id']) for o, p in zip(before['argument_bundle']['graphs'],
                                                         after['argument_bundle']['graphs'])
               for n, m in zip(o['graph']['nodes'], p['graph']['nodes']) if n != m]
    check('complete example: 19 of 20 nodes are byte-identical', changed == [('cream_cheese_1', 'cream_cheese_1:G1')])
    for name in ('saved_zero_finding', 'saved_zero_finding_controlled_negative'):
        result = load(B.OUT / (name + '.revision_result.json'))
        check(name + ': the real zero-finding report gives no change and is not labelled synthetic',
              result['outcome'] == 'no_change' and result['revised_argument_bundle'] is None
              and result['proposal'] is None and result['synthetic_findings']['present'] is False)


def check_cycle():
    """The saved two-round cycle replays from its saved reports and decisions."""
    folder = B.OUT / B.CYCLE
    cycle = load(folder / 'cycle.json')
    cycle_schema = C.load_schema('revision_cycle')
    Draft202012Validator.check_schema(cycle_schema)
    check('cycle: summary matches its JSON schema', not list(Draft202012Validator(cycle_schema).iter_errors(cycle)))
    requests = [load(B.OUT / 'synthetic_actionable.revision_request.json'),
                load(folder / 'request_2.revision_request.json'), load(folder / 'request_3.revision_request.json')]
    results = [load(B.OUT / 'synthetic_actionable.revision_result.json'),
               load(folder / 'request_2.revision_result.json'), load(folder / 'request_3.revision_result.json')]
    reports = [load(folder / f'request_{i}.recriticism_report.json') for i in (1, 2)]
    check('cycle: two revision rounds, then nothing actionable',
          (cycle['revision_rounds'], cycle['stop_reason'], cycle['final_outcome'])
          == (2, 'no_actionable_findings', 'revised')
          and [r['outcome'] for r in results] == ['revised', 'revised', 'no_change'])
    check('cycle: every finding is labelled synthetic',
          cycle['synthetic_findings']['present'] and all(r['synthetic_findings']['present'] for r in results)
          and all(r['llm']['backend'] == 'scripted' for r in reports))
    pending = deepcopy(reports)
    run = G.run_cycle(requests[0], review=lambda critic_request: pending.pop(0),
                      decide=lambda report, round_number: requests[round_number - 1]['finding_decisions'])
    check('cycle: replays from the saved reports and decisions',
          run['cycle'] == cycle and run['requests'] == requests and run['results'] == results)
    for index, (request, result) in enumerate(zip(requests, results), start=1):
        issues = C.request_issues(request) + G.verify_result(request, result)
        check(f'cycle: request {index} is usable and its result replays', issues == [], '; '.join(issues))
        check(f'cycle: request {index} has {index - 1} history item(s)', len(request['history']) == index - 1)
    for index, reply in enumerate(B.CYCLE_REPLIES, start=1):
        check(f'cycle: scripted reply {index} is the one in the builder',
              load(folder / f'request_{index}.recriticism_scripted_reply.json') == reply)
        again = B.scripted_report(G.recriticism_request(requests[index - 1], results[index - 1]), reply,
                                  'synthetic-scripted-cycle')
        check(f'cycle: re-criticism report {index} regenerated from the real Critic (latency ignored)',
              without_latency(again) == without_latency(reports[index - 1]))
    final = load(folder / 'final_argument_bundle.json')
    check('cycle: final bundle is the round-2 revised bundle',
          final == results[1]['revised_argument_bundle']
          and K.digest(final) == cycle['final_argument_bundle_sha256'])
    statements = {o: E.node_of(final, o, o + ':G1')['statement'] for o in ('cream_cheese_1', 'ketchup_1')}
    check('cycle: both edited goals carry the unresolved wording',
          all('remains unresolved' in s and 'guarantee' not in s.lower() for s in statements.values()))
    check('cycle: the concerns the Critic cannot settle are still open at the end',
          bool(cycle['final_review']['carried_forward']['unresolved_concerns'])
          and cycle['final_review']['reviewed_final_bundle'])


def main():
    FAILED.clear()
    fixture_root = B.FIXTURE.parents[1]
    manifest = load(fixture_root / 'MANIFEST.json')
    for artifact in manifest['artifacts']:
        data = (fixture_root / artifact['file']).read_bytes()
        check('fixture file unchanged: ' + artifact['file'],
              hashlib.sha256(data).hexdigest() == artifact['sha256'] and len(data) == artifact['bytes'])
    original, mutated = B.read('critic.request.json'), B.read('critic.controlled-negative.request.json')
    rebuilt = B.build()
    check_requests(original, mutated, rebuilt)
    check_fail_closed(original)
    check_results()
    check_cycle()
    print()
    print('FAILED: ' + ', '.join(FAILED) if FAILED else 'All checks passed.')
    return 1 if FAILED else 0


if __name__ == '__main__':
    raise SystemExit(main())
