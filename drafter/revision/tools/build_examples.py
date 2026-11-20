"""Rebuild the saved examples with the real Critic and the real revision. No model, no network.

    python3 -m drafter.revision.tools.build_examples                  everything
    python3 -m drafter.revision.tools.build_examples --invalid-only   only examples/invalid/, derived from
                                                                      the saved valid examples

The synthetic Critic reports come from critic.review with a scripted reply, so the
Critic's own screening decides what is accepted or rejected. They are test
inputs, not model results. The saved Qwen reports are wrapped unchanged.

A scripted report records how long the scripted call took (llm.latency_s), so a
rebuild changes that number and every digest that depends on it. The saved files
are consistent with each other; check_examples verifies that.
"""
from copy import deepcopy
from pathlib import Path
import json

import critic
from critic import contract as K, llm as L
from drafter.revision import contract as C, engine as G

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'integration' / 'fixtures' / 'one_pass_20261113' / 'artifacts' / 'models'
OUT = Path(__file__).resolve().parents[1] / 'examples'
CYCLE = 'two_round_cycle'
SYNTHETIC_LABEL = ('Synthetic test input: the Critic report was produced by critic.review with a scripted reply '
                   'written for this test. It is not a model result and not a scientific finding.')
GUARANTEE = 'Cream_cheese_1 was guaranteed physically safe throughout this execution.'

ACTIONABLE_REPLY = {'findings': [{
    'object_id': 'cream_cheese_1', 'node_id': 'cream_cheese_1:G1', 'category': 'C12', 'severity': 'high',
    'explanation': ('The goal states "' + GUARANTEE + '" No admitted checker assessment or other evidence '
                    'in the package supports a guarantee of physical safety.'),
    'evidence_ids': [],
    'suggested_action': 'Remove the guarantee and restore an unresolved R1 goal for cream_cheese_1.',
}]}
REJECTED_REPLY = {'findings': [
    {'object_id': 'ketchup_1', 'node_id': 'ketchup_1:G9', 'category': 'C10', 'severity': 'low',
     'explanation': 'Goal ketchup_1:G9 generalizes beyond the monitored window.', 'evidence_ids': [],
     'suggested_action': 'Narrow the goal to the monitored window.'},
    {'object_id': 'milk_1', 'node_id': 'milk_1:S1', 'category': 'C05', 'severity': 'medium',
     'explanation': 'The strategy infers support from a contact record.',
     'evidence_ids': ['ev:' + '0' * 64], 'suggested_action': 'Remove the support inference.'},
    {'object_id': 'butter_1', 'node_id': 'butter_1:U1', 'category': 'C09', 'severity': 'medium',
     'explanation': 'The unresolved claim may understate the remaining uncertainty about initial support.',
     'evidence_ids': [], 'suggested_action': 'State the remaining uncertainty explicitly.'},
    {'object_id': 'orange_juice_1', 'node_id': 'orange_juice_1:C1', 'category': 'C02', 'severity': 'medium',
     'explanation': 'The context cites no registry record.', 'evidence_ids': [],
     'suggested_action': 'Cite a registry record.'},
]}
# Replies for the two re-criticisms of the cycle example: a second synthetic finding, then none.
CYCLE_REPLIES = [
    {'findings': [{
        'object_id': 'ketchup_1', 'node_id': 'ketchup_1:G1', 'category': 'C06', 'severity': 'medium',
        'explanation': ('Synthetic second-round finding: the goal for ketchup_1 is treated as if it implied a '
                        'safety conclusion the package does not support.'),
        'evidence_ids': [], 'suggested_action': 'State plainly that R1 is unresolved for ketchup_1.'}]},
    {'findings': []},
]
INVALID = 'invalid'
INVALID_LABEL = ('Synthetic invalid test input: a valid example changed on purpose so that the revision must '
                 'refuse it or leave the finding unresolved. Not a model result and not a scientific finding.')
# What each saved invalid payload must lead to. `issue` is a prefix of one entry of request_issues.
INVALID_EXPECTED = {
    'foreign_execution': {
        'change': 'The argument bundle names another execution. The real Critic rejects the input (BUNDLE-EXEC).',
        'issue': None, 'classification': 'not_actionable_validation_phase',
        'outcome': 'rejected_invalid_input', 'stop_reason': 'invalid_input'},
    'unknown_node': {
        'change': ('A model-proposed finding was added by hand to the saved report of the rejected-candidates '
                   'example. It names a node that does not exist.'),
        'issue': None, 'classification': 'not_actionable_target_missing',
        'outcome': 'unresolved', 'stop_reason': 'no_actionable_findings'},
    'nonadmitted_assessment': {
        'change': ('A model-proposed finding was added by hand to the same saved report. It cites a checker '
                   'assessment that is not admitted.'),
        'issue': None, 'classification': 'not_actionable_unknown_evidence',
        'outcome': 'unresolved', 'stop_reason': 'insufficient_evidence'},
    'malformed_history': {
        'change': 'Round 2 of the cycle example with a history item that does not chain to this round.',
        'issue': 'history_chain_mismatch', 'classification': None,
        'outcome': 'rejected_invalid_input', 'stop_reason': 'invalid_input'},
    'report_schema_invalid': {
        'change': 'The Critic report of the actionable example without its review_status field.',
        'issue': 'critic_report_schema:', 'classification': None,
        'outcome': 'rejected_invalid_input', 'stop_reason': 'invalid_input'},
}
DECISION_NOTE = 'Approved only as a labelled synthetic test input for positive revision behaviour.'


def read(name):
    return json.loads((FIXTURE / name).read_text(encoding='utf-8'))


def scripted_report(critic_request, reply, name):
    return critic.review(critic_request, L.ScriptedLLM(json.dumps(reply), name=name))


def approve(report):
    """synthetic_test_label decisions for every criticism of a report that needs a decision."""
    return [{'criticism_id': c['criticism_id'], 'decision': 'approved', 'decided_by': 'synthetic_test_label',
             'reviewer': None, 'note': DECISION_NOTE} for c in report['criticisms']
            if c['phase'] == 'review' and (c['finding_source'] != 'deterministic' or c['human_review_required'])]


def cycle_files(run):
    """Files of the cycle example. Request 1 and its result are the synthetic_actionable example."""
    files = {CYCLE + '/cycle.json': run['cycle'],
             CYCLE + '/final_argument_bundle.json':
                 [r for r in run['results'] if r['outcome'] == 'revised'][-1]['revised_argument_bundle']}
    for index, reply in enumerate(CYCLE_REPLIES, start=1):
        files[f'{CYCLE}/request_{index}.recriticism_scripted_reply.json'] = reply
        files[f'{CYCLE}/request_{index}.recriticism_report.json'] = run['reports'][index - 1]
    for index in range(2, len(run['requests']) + 1):
        files[f'{CYCLE}/request_{index}.revision_request.json'] = run['requests'][index - 1]
        files[f'{CYCLE}/request_{index}.revision_result.json'] = run['results'][index - 1]
    return files


def forged_model_finding(object_id, node_id, evidence_ids):
    """A model-proposed criticism written by hand, as if it had been edited into a report."""
    return {'criticism_id': 'CRIT-001', 'critic_version': critic.CRITIC_VERSION, 'check_id': 'LLM',
            'phase': 'review', 'category': 'C06', 'category_name': K.CATEGORIES['C06'], 'severity': 'high',
            'blocking': False, 'object_id': object_id, 'node_id': node_id,
            'explanation': 'Hand-written test finding, added to a saved report for an invalid-input example.',
            'evidence_ids': list(evidence_ids), 'requirement_refs': [L.PROMPT_VERSION],
            'finding_source': 'llm_proposed', 'suggested_action': 'None; this finding is a test input.',
            'additional_evidence_needed': False, 'human_review_required': True}


def invalid_requests(actionable_request, rejected_request, cycle_request_2, original):
    """{name: revision request}: one deliberate change each to a valid, saved input."""
    def with_finding(name, object_id, node_id, evidence_ids):
        def edit(request):
            request['critic_report']['criticisms'].append(forged_model_finding(object_id, node_id, evidence_ids))
            request['finding_decisions'] = [{'criticism_id': 'CRIT-001', 'decision': 'approved',
                                             'decided_by': 'synthetic_test_label', 'reviewer': None,
                                             'note': 'Approved only so that the stated defect is the reason.'}]
        return changed(rejected_request, name, edit)

    def changed(base, name, edit):
        request = deepcopy(base)
        request['revision_id'] = 'example:invalid-' + name.replace('_', '-')
        request['synthetic_findings'] = {'present': True, 'label': INVALID_LABEL}
        edit(request)
        request['critic_report_sha256'] = K.digest(request['critic_report'])
        return request

    foreign = deepcopy(original)
    foreign['request_id'] = 'synthetic:invalid-foreign-execution'
    foreign['argument_bundle']['execution_id'] = 'foreign_execution_0000'
    return {
        'foreign_execution': C.build_request('example:invalid-foreign-execution', foreign, critic.review(foreign),
                                             synthetic_label=INVALID_LABEL),
        'unknown_node': with_finding('unknown_node', 'milk_1', 'milk_1:G9', []),
        'nonadmitted_assessment': with_finding('nonadmitted_assessment', 'milk_1', 'milk_1:G1', ['ca:' + '0' * 64]),
        'malformed_history': changed(cycle_request_2, 'malformed_history', lambda r: r['history'][0]
                                     .update(recriticism_request_sha256='0' * 64)),
        'report_schema_invalid': changed(actionable_request, 'report_schema_invalid',
                                         lambda r: r['critic_report'].pop('review_status')),
    }


def invalid_files(actionable_request, rejected_request, cycle_request_2, original):
    files = {INVALID + '/EXPECTED.json': INVALID_EXPECTED}
    for name, request in invalid_requests(actionable_request, rejected_request, cycle_request_2,
                                          original).items():
        files[f'{INVALID}/{name}.revision_request.json'] = request
        files[f'{INVALID}/{name}.revision_result.json'] = G.revise(request)
    return files


def build():
    """Return {file name: JSON value} for every example."""
    original, mutated = read('critic.request.json'), read('critic.controlled-negative.request.json')
    actionable = scripted_report(mutated, ACTIONABLE_REPLY, 'synthetic-scripted-actionable')
    rejected = scripted_report(original, REJECTED_REPLY, 'synthetic-scripted-rejected')
    files = {
        'synthetic_actionable.scripted_reply.json': ACTIONABLE_REPLY,
        'synthetic_actionable.critic_report.json': actionable,
        'synthetic_actionable.revision_request.json': C.build_request(
            'example:synthetic-actionable-c12', mutated, actionable,
            finding_decisions=approve(actionable), synthetic_label=SYNTHETIC_LABEL),
        'synthetic_rejected_unresolved.scripted_reply.json': REJECTED_REPLY,
        'synthetic_rejected_unresolved.critic_report.json': rejected,
        'synthetic_rejected_unresolved.revision_request.json': C.build_request(
            'example:synthetic-rejected-unresolved', original, rejected, synthetic_label=SYNTHETIC_LABEL),
        'saved_zero_finding.revision_request.json': C.build_request(
            'example:saved-qwen-zero-finding', original, read('critic.qwen.report.json')),
        'saved_zero_finding_controlled_negative.revision_request.json': C.build_request(
            'example:saved-qwen-zero-finding-controlled-negative', mutated,
            read('critic.controlled-negative.qwen.report.json'), check=False),
    }
    for name in [n for n in files if n.endswith('.revision_request.json')]:
        files[name.replace('revision_request', 'revision_result')] = G.revise(files[name])
    replies = list(CYCLE_REPLIES)
    run = G.run_cycle(
        files['synthetic_actionable.revision_request.json'],
        review=lambda critic_request: scripted_report(critic_request, replies.pop(0), 'synthetic-scripted-cycle'),
        decide=lambda report, round_number: approve(report))
    files.update(cycle_files(run))
    files.update(invalid_files(files['synthetic_actionable.revision_request.json'],
                               files['synthetic_rejected_unresolved.revision_request.json'], run['requests'][1],
                               original))
    return files


def build_invalid_only():
    """The invalid payloads, derived from the saved valid examples without rebuilding those."""
    def saved(name):
        return json.loads((OUT / name).read_text(encoding='utf-8'))
    return invalid_files(saved('synthetic_actionable.revision_request.json'),
                         saved('synthetic_rejected_unresolved.revision_request.json'),
                         saved(CYCLE + '/request_2.revision_request.json'), read('critic.request.json'))


def main(argv=None):
    import sys
    arguments = sys.argv[1:] if argv is None else argv
    if arguments not in ([], ['--invalid-only']):
        raise SystemExit('usage: python3 -m drafter.revision.tools.build_examples [--invalid-only]')
    for name, value in (build_invalid_only() if arguments else build()).items():
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('wrote', name)


if __name__ == '__main__':
    main()
