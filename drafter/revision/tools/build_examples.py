"""Rebuild the saved examples with the real Critic and the real revision. No model, no network.

    python3 -m drafter.revision.tools.build_examples

The synthetic Critic reports come from critic.review with a scripted reply, so the
Critic's own screening decides what is accepted or rejected. They are test
inputs, not model results. The saved Qwen reports are wrapped unchanged.

A scripted report records how long the scripted call took (llm.latency_s), so a
rebuild changes that number and every digest that depends on it. The saved files
are consistent with each other; check_examples verifies that.
"""
from pathlib import Path
import json

import critic
from critic import llm as L
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
            read('critic.controlled-negative.qwen.report.json')),
    }
    for name in [n for n in files if n.endswith('.revision_request.json')]:
        files[name.replace('revision_request', 'revision_result')] = G.revise(files[name])
    replies = list(CYCLE_REPLIES)
    run = G.run_cycle(
        files['synthetic_actionable.revision_request.json'],
        review=lambda critic_request: scripted_report(critic_request, replies.pop(0), 'synthetic-scripted-cycle'),
        decide=lambda report, round_number: approve(report))
    files.update(cycle_files(run))
    return files


def main():
    for name, value in build().items():
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('wrote', name)


if __name__ == '__main__':
    main()
