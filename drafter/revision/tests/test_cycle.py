"""Bounded iteration: every stop reason, complete history, deterministic and resumable.

Re-criticism in these tests is the real critic.review, with rule checks only or with a scripted
reply. A scripted second-round finding is a synthetic test input, labelled like the first.
"""
from copy import deepcopy
import unittest

from critic import contract as K
from drafter.revision import contract as C, engine as G
from drafter.revision.tests import support as S
from drafter.revision.tests.test_core import CASE_A, broken_link


def scripted_reviews(*replies):
    """review(critic_request) that answers with the given scripted findings in turn, then rules only."""
    pending = list(replies)
    return lambda critic_request: S.review(critic_request, pending.pop(0) if pending else None)


def decide(report, round_number):
    return S.approve(report)


class Cycles(unittest.TestCase):
    def check_cycle(self, run, first):
        """Bindings that must hold for every cycle."""
        cycle, requests, results, reports = (run[k] for k in ('cycle', 'requests', 'results', 'reports'))
        self.assertEqual(C.schema_problems(cycle, 'revision_cycle'), [])
        self.assertEqual(requests[0], first)
        self.assertEqual(len(requests), len(results))
        self.assertEqual(len(reports), len(results) - 1)
        self.assertLessEqual(cycle['revision_rounds'], cycle['max_rounds'])
        self.assertEqual(results[-1]['stop_reason'], cycle['stop_reason'])
        for index, (request, result) in enumerate(zip(requests, results)):
            self.assertEqual(G.revise(request), result, 'a round is not deterministic')
            self.assertEqual(request['round'], index + 1)
            self.assertEqual(len(request['history']), index)
            self.assertEqual(cycle['rounds'][index]['result_sha256'], K.digest(result))
            if index + 1 < len(requests):
                self.assertEqual(result['outcome'], 'revised')
                following = requests[index + 1]
                # resumable: the next request can be rebuilt from the saved pieces alone
                rebuilt = C.build_request(
                    request['revision_id'], G.recriticism_request(request, result), reports[index],
                    finding_decisions=following['finding_decisions'],
                    synthetic_label=following['synthetic_findings']['label'], round_number=index + 2,
                    max_rounds=request['max_rounds'], history=request['history'] + [G.history_item(request, result)],
                    repair_invalid_evidence_links=bool(request.get('repair_invalid_evidence_links')))
                self.assertEqual(rebuilt, following)
                self.assertEqual(following['history'][-1]['recriticism_request_sha256'],
                                 following['critic_request_sha256'])
                self.assertEqual(following['critic_request']['argument_bundle'],
                                 result['revised_argument_bundle'])
        revised = [r for r in results if r['outcome'] == 'revised']
        final = revised[-1]['revised_argument_bundle'] if revised else first['critic_request']['argument_bundle']
        self.assertEqual(cycle['final_argument_bundle_sha256'], K.digest(final))
        self.assertEqual(cycle['initial_argument_bundle_sha256'],
                         K.digest(first['critic_request']['argument_bundle']))
        return cycle

    def test_two_round_synthetic_cycle_ends_with_complete_history(self):
        """Round 1 answers a synthetic C12, round 2 a synthetic C06 on another object, then nothing is left."""
        first = S.guarantee_request()
        second_finding = S.finding('ketchup_1', 'ketchup_1:G1', 'C06', 'The goal implies a safety conclusion.')
        run = G.run_cycle(first, review=scripted_reviews([second_finding], []), decide=decide)
        cycle = self.check_cycle(run, first)
        self.assertEqual((cycle['revision_rounds'], cycle['stop_reason'], cycle['final_outcome']),
                         (2, 'no_actionable_findings', 'revised'))
        self.assertEqual([r['outcome'] for r in run['results']], ['revised', 'revised', 'no_change'])
        self.assertEqual([r['round'] for r in cycle['rounds']], [1, 2, 3])
        self.assertEqual([r['critic_backend'] for r in cycle['rounds']], ['scripted'] * 3)
        self.assertTrue(cycle['synthetic_findings']['present'])
        self.assertTrue(all(r['synthetic_findings']['present'] for r in run['results']))
        last = run['requests'][-1]
        self.assertEqual([h['round'] for h in last['history']], [1, 2])
        self.assertEqual([h['addressed'][0]['node_id'] for h in last['history']],
                         ['cream_cheese_1:G1', 'ketchup_1:G1'])
        final = run['results'][1]['revised_argument_bundle']
        for object_id in ('cream_cheese_1', 'ketchup_1'):
            self.assertIn('remains unresolved', S.node(final, object_id, object_id + ':G1')['statement'])
        # objects no finding named are exactly as the Drafter wrote them
        original = first['critic_request']['argument_bundle']
        self.assertEqual(final['graphs'][2:], original['graphs'][2:])
        # the concerns the Critic cannot settle are still there at the end
        self.assertTrue(cycle['final_review']['carried_forward']['unresolved_concerns'])
        self.assertTrue(cycle['final_review']['reviewed_final_bundle'])

    def test_two_rule_only_rounds_repair_then_downgrade(self):
        """No model at all: round 1 removes a broken citation, round 2 answers the rule findings."""
        first = S.request_for(broken_link(CASE_A), repair_invalid_evidence_links=True)
        run = G.run_cycle(first)
        cycle = self.check_cycle(run, first)
        self.assertEqual((cycle['revision_rounds'], cycle['stop_reason']), (2, 'no_actionable_findings'))
        self.assertEqual([r['critic_backend'] for r in cycle['rounds']], ['none'] * 3)
        self.assertEqual([c['check_id'] for c in run['requests'][1]['critic_report']['criticisms']],
                         ['CONCL-UNSUPPORTED'] * 3 + ['CLAIM-ABSOLUTE-SAFETY'])
        outcomes = run['results'][1]['revised_argument_bundle']['execution_conclusion']['object_outcomes']
        self.assertEqual(set(outcomes.values()), {K.INSUFFICIENT})
        self.assertEqual(cycle['final_review']['open_findings'], [])

    def test_repeated_finding_stops_the_cycle(self):
        """Core case 7: the Critic raises the same objection again after the edit."""
        first = S.guarantee_request()
        run = G.run_cycle(first, review=scripted_reviews([S.guarantee_finding()]), decide=decide)
        cycle = self.check_cycle(run, first)
        self.assertEqual((cycle['revision_rounds'], cycle['stop_reason'], cycle['final_outcome']),
                         (1, 'repeated_unchanged_findings', 'revised'))
        last = run['results'][-1]
        self.assertEqual((last['outcome'], last['dispositions'][0]['reason']),
                         ('unresolved', 'repeated_after_previous_edit'))
        self.assertIsNone(last['proposal'])  # no second attempt at the same edit
        self.assertEqual(len(cycle['final_review']['open_findings']), 1)

    def test_repeat_is_detected_even_without_a_new_decision(self):
        first = S.guarantee_request()
        run = G.run_cycle(first, review=scripted_reviews([S.guarantee_finding()]))
        self.assertEqual(self.check_cycle(run, first)['stop_reason'], 'repeated_unchanged_findings')

    def test_round_limit(self):
        first = S.request_for(broken_link(CASE_A), repair_invalid_evidence_links=True, max_rounds=1)
        run = G.run_cycle(first)
        cycle = self.check_cycle(run, first)
        self.assertEqual((cycle['revision_rounds'], cycle['stop_reason'], cycle['final_outcome']),
                         (1, 'round_limit', 'revised'))
        last_request, last = run['requests'][-1], run['results'][-1]
        self.assertEqual((last_request['round'], last_request['max_rounds']), (2, 1))
        self.assertEqual({r['reason'] for r in last['dispositions']}, {'round_limit_reached', 'needs_human_decision'})
        self.assertEqual(len(cycle['final_review']['open_findings']), 4)
        self.assertIsNone(last['proposal'])

    def test_later_findings_wait_for_a_decision(self):
        first = S.guarantee_request()
        second_finding = S.finding('ketchup_1', 'ketchup_1:G1', 'C06', 'The goal implies a safety conclusion.')
        run = G.run_cycle(first, review=scripted_reviews([second_finding]))
        cycle = self.check_cycle(run, first)
        self.assertEqual((cycle['revision_rounds'], cycle['stop_reason']), (1, 'awaiting_decision'))
        # resume: the same round with a decision added goes on
        waiting = run['requests'][-1]
        resumed = deepcopy(waiting)
        resumed['finding_decisions'] = S.approve(waiting['critic_report'])
        self.assertEqual(C.request_issues(resumed), [])
        self.assertEqual(G.revise(resumed)['outcome'], 'revised')

    def test_no_change_cycle_for_the_saved_zero_finding_report(self):
        first = S.example('saved_zero_finding.revision_request.json')
        run = G.run_cycle(first)
        cycle = self.check_cycle(run, first)
        self.assertEqual((cycle['revision_rounds'], cycle['stop_reason'], cycle['final_outcome']),
                         (0, 'no_actionable_findings', 'no_change'))
        self.assertEqual(run['reports'], [])
        self.assertEqual(cycle['final_argument_bundle_sha256'], cycle['initial_argument_bundle_sha256'])
        self.assertEqual(cycle['rounds'][0]['critic_backend'], 'openai_compatible')

    def test_invalid_input_cycle(self):
        run = G.run_cycle({'not': 'a request'})
        self.assertEqual(C.schema_problems(run['cycle'], 'revision_cycle'), [])
        self.assertEqual((run['cycle']['stop_reason'], run['cycle']['final_outcome']),
                         ('invalid_input', 'rejected_invalid_input'))

    def test_failed_recriticism_is_an_execution_failure_and_keeps_the_revised_bundle(self):
        def broken(critic_request):
            raise ConnectionError('no Critic service')

        first = S.guarantee_request()
        run = G.run_cycle(first, review=broken)
        cycle = run['cycle']
        self.assertEqual(C.schema_problems(cycle, 'revision_cycle'), [])
        self.assertEqual((cycle['stop_reason'], cycle['revision_rounds'], cycle['final_outcome']),
                         ('execution_failure', 1, 'revised'))
        self.assertFalse(cycle['final_review']['reviewed_final_bundle'])
        self.assertIn('ConnectionError', cycle['status_detail'])
        self.assertEqual(cycle['final_argument_bundle_sha256'],
                         run['results'][0]['revised_argument_bundle_sha256'])

    def test_a_report_for_another_request_ends_the_cycle(self):
        other = S.fixture('critic.request.json')
        first = S.guarantee_request()
        run = G.run_cycle(first, review=lambda critic_request: S.review(other))
        self.assertEqual(run['cycle']['stop_reason'], 'execution_failure')
        self.assertIn('report_request_id_mismatch', run['cycle']['status_detail'])

    def test_the_input_request_is_never_modified(self):
        first = S.guarantee_request()
        before = K.digest(first)
        G.run_cycle(first, review=scripted_reviews([S.guarantee_finding()]), decide=decide)
        self.assertEqual(K.digest(first), before)

    def test_recriticism_request_differs_only_in_bundle_and_id(self):
        first = S.guarantee_request()
        result = G.revise(first)
        revised = G.recriticism_request(first, result)
        changed = {k for k in first['critic_request'] if first['critic_request'][k] != revised[k]}
        self.assertEqual(changed, {'argument_bundle', 'request_id'})
        self.assertEqual(revised['request_id'], first['critic_request']['request_id'] + ':rev1')
        second = G.run_cycle(first, review=scripted_reviews(
            [S.finding('ketchup_1', 'ketchup_1:G1', 'C06', 'The goal implies a safety conclusion.')], []),
            decide=decide)
        self.assertEqual(second['requests'][2]['critic_request']['request_id'],
                         first['critic_request']['request_id'] + ':rev2')
        with self.assertRaises(ValueError):
            G.recriticism_request(first, G.revise(S.example('saved_zero_finding.revision_request.json')))


if __name__ == '__main__':
    unittest.main()
