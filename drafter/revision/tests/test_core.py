"""Core revision scenarios. Run from the repository root:

    python3 -m unittest discover -s drafter/revision/tests -t . -v

No model, no network and no GPU are needed. Critic reports come from the real critic.review.
Findings raised through a scripted reply are synthetic test inputs, never model results.
"""
import unittest

from critic import contract as K
from drafter.revision import contract as C, engine as G
from drafter.revision.adapters import GOAL_TEMPLATE, ScriptedAdapter
from drafter.revision.tests import support as S
from drafter.validation import schema_issues

CASE_A = 'case_a_unsupported_claim.json'
CASE_C = 'case_c_correct_unresolved.json'
CASE_D = 'case_d_claim_hides_checker_result.json'


def broken_link(name=CASE_C, object_index=0, node_ids=('E2',)):
    """A labelled synthetic mutation: the named Solutions cite a record that is not in the package."""
    request = S.case(name)
    for n in request['argument_bundle']['graphs'][object_index]['graph']['nodes']:
        if n['id'] in node_ids:
            n['evidence_id'] = 'ev:' + '0' * 64
    return request


class UnsupportedGuarantee(S.Checks, unittest.TestCase):
    """Core case 1: an approved C12 finding removes the guarantee and keeps everything else."""

    def setUp(self):
        self.request = S.guarantee_request()
        self.result = self.revise(self.request)

    def test_the_guarantee_is_replaced_by_the_unresolved_wording(self):
        self.assertEqual((self.result['outcome'], self.result['stop_reason']), ('revised', None))
        after = S.node(self.result['revised_argument_bundle'], 'cream_cheese_1', 'cream_cheese_1:G1')
        self.assertEqual(after['statement'], GOAL_TEMPLATE.format(object_id='cream_cheese_1'))
        self.assertNotIn('guarantee', after['statement'].lower())
        self.assertEqual((after['type'], after['validation_status'], after['physical_claim']),
                         ('goal', 'unresolved', True))

    def test_only_that_node_changes_and_the_diff_says_so(self):
        diff = self.result['diff']
        self.assertEqual([(d['change'], d['object_id'], d['node_id']) for d in diff],
                         [('node_replaced', 'cream_cheese_1', 'cream_cheese_1:G1')])
        self.assertEqual(diff[0]['before']['statement'], S.GUARANTEE)
        self.assertEqual(diff[0]['before_sha256'], K.digest(diff[0]['before']))
        self.assertEqual(diff[0]['after_sha256'], K.digest(diff[0]['after']))
        self.assertEqual(self.result['edits'][0]['finding_ids'], ['CRIT-001'])
        self.assertIn(S.GUARANTEE, self.result['edits'][0]['justification'])
        m = self.result['metrics']
        self.assertEqual((m['nodes_changed'], m['nodes_added'], m['nodes_removed'], m['evidence_links_added'],
                          m['new_rule_findings'], m['graphs_valid']), (1, 0, 0, 0, 0, True))

    def test_scope_r1_and_interval_are_preserved(self):
        before = S.node(self.request['critic_request']['argument_bundle'], 'cream_cheese_1', 'cream_cheese_1:G1')
        after = S.node(self.result['revised_argument_bundle'], 'cream_cheese_1', 'cream_cheese_1:G1')
        self.assertEqual(after['scope'], before['scope'])
        self.assertEqual(after['scope']['interval'], S.INTERVAL)
        self.assertEqual((after['scope']['requirement_id'], after['scope']['requirement_version']),
                         ('R1', '2.0.0'))
        self.assertEqual(self.result['revised_argument_bundle']['protected_objects'],
                         ['cream_cheese_1', 'ketchup_1', 'orange_juice_1', 'milk_1', 'butter_1'])

    def test_the_edited_node_carries_revision_provenance_and_points_at_the_original(self):
        before = S.node(self.request['critic_request']['argument_bundle'], 'cream_cheese_1', 'cream_cheese_1:G1')
        after = S.node(self.result['revised_argument_bundle'], 'cream_cheese_1', 'cream_cheese_1:G1')
        stamp = after['provenance']
        self.assertEqual(stamp['replaces_node_sha256'], K.digest(before))
        self.assertEqual((stamp['revision_id'], stamp['round'], stamp['finding_ids'], stamp['prose_review']),
                         (self.request['revision_id'], 1, ['CRIT-001'], 'required'))
        self.assertEqual(stamp['critic_report_sha256'], self.request['critic_report_sha256'])
        self.assertEqual(after['origin'], 'unresolved_conclusion')
        self.assertNotEqual(stamp, before['provenance'])

    def test_the_revised_bundle_still_matches_the_drafter_bundle_schema(self):
        self.assertEqual(schema_issues(self.result['revised_argument_bundle'], 'draft_argument.schema.json',
                                       '#/$defs/argument_bundle'), [])

    def test_a_model_proposed_finding_is_edited_but_not_verified(self):
        row = self.result['dispositions'][0]
        self.assertEqual((row['disposition'], row['verified_by_rules'], row['finding_source']),
                         ('edited', None, 'llm_proposed'))
        self.assertEqual(row['decision']['decided_by'], 'synthetic_test_label')
        self.assertTrue(self.result['synthetic_findings']['present'])

    def test_without_a_decision_nothing_changes(self):
        result = self.revise(S.guarantee_request(decide=False))
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'awaiting_decision'))
        self.assertEqual(result['dispositions'][0]['classification'], C.NEEDS_DECISION)
        self.assertEqual(result['metrics']['findings_awaiting_decision'], 1)

    def test_a_declined_finding_is_not_acted_on(self):
        critic_request = S.fixture('critic.controlled-negative.request.json')
        report = S.review(critic_request, [S.guarantee_finding()])
        request = C.build_request('test:declined', critic_request, report, synthetic_label=S.LABEL,
                                  finding_decisions=S.approve(report, decision='declined'))
        result = self.revise(request)
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'no_actionable_findings'))
        self.assertEqual(result['dispositions'][0]['classification'], C.DECLINED)

    def test_a_human_decision_with_a_reviewer_also_works_without_the_synthetic_decision_label(self):
        critic_request = S.fixture('critic.controlled-negative.request.json')
        report = S.review(critic_request, [S.guarantee_finding()])
        decision = {'criticism_id': 'CRIT-001', 'decision': 'approved', 'decided_by': 'human_review',
                    'reviewer': 'Test Reviewer', 'note': 'Test of the human_review path.'}
        request = C.build_request('test:human', critic_request, report, synthetic_label=S.LABEL,
                                  finding_decisions=[decision])
        result = self.revise(request)
        self.assertEqual(result['outcome'], 'revised')
        self.assertEqual(result['manual_review_decisions'], [decision])


class MissingSupport(S.Checks, unittest.TestCase):
    """Core case 2: a strategy with no support gets an explicit unresolved claim, never a Solution."""

    def setUp(self):
        critic_request = S.fixture('critic.request.json')
        graph = critic_request['argument_bundle']['graphs'][3]['graph']
        graph['edges'] = [e for e in graph['edges'] if e['source'] != 'milk_1:S1']
        critic_request['request_id'] = 'synthetic:missing-support'
        self.request = S.request_for(critic_request)
        self.result = self.revise(self.request)

    def test_an_unresolved_claim_is_added_under_the_strategy(self):
        self.assertEqual(self.request['critic_report']['criticisms'][0]['check_id'], 'GSN-UNSUPPORTED-GOAL')
        self.assertEqual(self.result['outcome'], 'revised')
        self.assertEqual([(d['change'], d['node_id']) for d in self.result['diff']],
                         [('node_added', 'milk_1:R1U1'), ('edge_added', None)])
        added = self.result['diff'][0]['after']
        parent = S.node(self.request['critic_request']['argument_bundle'], 'milk_1', 'milk_1:S1')
        self.assertEqual((added['type'], added['validation_status'], added['physical_claim'],
                          added['evidence_id']), ('unresolved_claim', 'unresolved', True, None))
        self.assertEqual(added['scope'], parent['scope'])
        self.assertEqual(self.result['diff'][1]['after'],
                         {'source': 'milk_1:S1', 'target': 'milk_1:R1U1', 'type': 'supported_by'})

    def test_a_rule_finding_is_verified_by_the_rules(self):
        row = self.result['dispositions'][0]
        self.assertEqual((row['disposition'], row['verified_by_rules'], row['decision']), ('edited', True, None))
        self.assertEqual(S.review(G.recriticism_request(self.request, self.result))['criticisms'], [])


class InvalidEvidenceLink(S.Checks, unittest.TestCase):
    """Core case 3: a broken citation is removed only on request, and nothing is cited in its place."""

    def test_without_the_option_invalid_input_stops_the_revision(self):
        result = self.revise(S.request_for(broken_link()))
        self.assertEqual((result['outcome'], result['stop_reason']), ('rejected_invalid_input', 'invalid_input'))
        self.assertEqual(result['dispositions'][0]['classification'], C.VALIDATION_PHASE)

    def test_with_the_option_the_solution_is_removed_and_the_request_becomes_valid(self):
        request = S.request_for(broken_link(), repair_invalid_evidence_links=True)
        self.assertEqual(request['critic_report']['review_status'], 'rejected_invalid_input')
        result = self.revise(request)
        self.assertEqual(result['outcome'], 'revised')
        self.assertEqual([(d['change'], d['node_id'] or d['before']) for d in result['diff']],
                         [('node_removed', 'E2'),
                          ('edge_removed', {'source': 'S1', 'target': 'E2', 'type': 'supported_by'})])
        self.assertEqual(result['dispositions'][0]['classification'], C.ACTIONABLE_LINK_REPAIR)
        m = result['metrics']
        self.assertEqual((m['evidence_links_removed'], m['evidence_links_added'], m['nodes_added']), (1, 0, 0))
        self.assertEqual(result['carried_forward']['evidence_requests'],
                         request['critic_report']['evidence_requests'])
        self.assertEqual(S.review(G.recriticism_request(request, result))['review_status'], 'completed')

    def test_a_strategy_left_without_support_gets_an_unresolved_claim(self):
        request = S.request_for(broken_link(CASE_A, node_ids=('E1', 'E2')), repair_invalid_evidence_links=True)
        result = self.revise(request)
        self.assertEqual(result['outcome'], 'revised')
        changes = [(d['change'], d['node_id']) for d in result['diff']]
        self.assertEqual(changes.count(('node_removed', 'E1')) + changes.count(('node_removed', 'E2')), 2)
        added = [d for d in result['diff'] if d['change'] == 'node_added']
        self.assertEqual(len(added), 1)
        self.assertEqual((added[0]['after']['type'], added[0]['after']['provenance']['author']),
                         ('unresolved_claim', 'host_template'))
        # the provisional review findings of the rejected report are not acted on in this round
        self.assertEqual({r['classification'] for r in result['dispositions'] if r['phase'] == 'review'},
                         {C.REPORT_UNUSABLE})

    def test_any_other_input_problem_keeps_the_request_unusable(self):
        critic_request = broken_link()
        critic_request['argument_bundle']['graphs'][1]['graph']['nodes'][0]['scope']['object_id'] = 'widget_a'
        result = self.revise(S.request_for(critic_request, repair_invalid_evidence_links=True))
        self.assertEqual((result['outcome'], result['stop_reason']), ('rejected_invalid_input', 'invalid_input'))


class CheckerContradiction(S.Checks, unittest.TestCase):
    """Core case 4: an outcome is corrected only to what an admitted checker assessment says."""

    def test_the_hidden_violation_is_reported_after_an_explicit_decision(self):
        request = S.request_for(S.case(CASE_D))
        finding = request['critic_report']['criticisms'][0]
        self.assertEqual((finding['check_id'], finding['human_review_required']), ('CONCL-HIDES-VIOLATION', True))
        result = self.revise(request)
        self.assertEqual(result['outcome'], 'revised')
        conclusion = result['revised_argument_bundle']['execution_conclusion']
        self.assertEqual(conclusion['object_outcomes']['object_00'], K.VIOLATION)
        self.assertEqual(conclusion['claimed_outcome'], K.VIOLATION)
        self.assertIn('violation_observed by R1 aggregation', conclusion['statement'])
        self.assertIn('not a physical finding', conclusion['statement'])
        self.assertEqual([d['change'] for d in result['diff']],
                         ['object_outcome_changed', 'execution_outcome_changed', 'execution_statement_changed'])
        self.assertEqual(result['metrics']['nodes_changed'], 0)

    def test_a_checker_based_outcome_is_outside_the_drafter_bundle_schema(self):
        # Recorded so the gap is visible: the Drafter schema allows only insufficient_information, so a
        # bundle corrected to an admitted checker result cannot be a Drafter bundle. See the README.
        result = self.revise(S.request_for(S.case(CASE_D)))
        issues = schema_issues(result['revised_argument_bundle'], 'draft_argument.schema.json',
                               '#/$defs/argument_bundle')
        self.assertTrue(any('object_outcomes/object_00' in i for i in issues), issues)

    def test_the_goal_itself_stays_unresolved(self):
        request = S.request_for(S.case(CASE_D))
        result = self.revise(request)
        goal = S.node(result['revised_argument_bundle'], 'object_00', 'G1')
        self.assertEqual(goal, S.node(request['critic_request']['argument_bundle'], 'object_00', 'G1'))
        self.assertEqual(goal['validation_status'], 'unresolved')

    def test_without_a_decision_the_contradiction_waits(self):
        result = self.revise(S.request_for(S.case(CASE_D), decide=False))
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'awaiting_decision'))

    def test_a_wrong_claim_is_matched_to_the_checker_not_to_something_safer(self):
        critic_request = S.case(CASE_D)
        outcomes = critic_request['argument_bundle']['execution_conclusion']['object_outcomes']
        outcomes['object_00'] = K.NO_VIOLATION
        critic_request['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NO_VIOLATION
        request = S.request_for(critic_request)
        self.assertIn('CONCL-CONTRADICTION', [c['check_id'] for c in request['critic_report']['criticisms']])
        result = self.revise(request)
        self.assertEqual(result['outcome'], 'revised')
        self.assertEqual(result['revised_argument_bundle']['execution_conclusion']['object_outcomes']['object_00'],
                         K.VIOLATION)


class CautiousNoChange(S.Checks, unittest.TestCase):
    """Core case 5: the real saved zero-finding reports change nothing. That is not a safety result."""

    def test_the_saved_qwen_report_gives_no_change(self):
        request = S.example('saved_zero_finding.revision_request.json')
        self.assertEqual(request['critic_report'], S.fixture('critic.qwen.report.json'))
        self.assertFalse(request['synthetic_findings']['present'])
        result = self.revise(request)
        self.assertEqual((result['outcome'], result['stop_reason']), ('no_change', 'no_actionable_findings'))
        self.assertIsNone(result['proposal'])
        self.assertEqual(result['carried_forward']['unresolved_concerns'],
                         request['critic_report']['unresolved_concerns'])
        self.assertIn('do not show that R1 holds', result['disclaimer'])

    def test_the_missed_guarantee_is_left_alone(self):
        request = S.example('saved_zero_finding_controlled_negative.revision_request.json')
        self.assertEqual(request['critic_report'], S.fixture('critic.controlled-negative.qwen.report.json'))
        result = self.revise(request)
        self.assertEqual((result['outcome'], result['stop_reason']), ('no_change', 'no_actionable_findings'))
        goal = S.node(request['critic_request']['argument_bundle'], 'cream_cheese_1', 'cream_cheese_1:G1')
        self.assertEqual(goal['statement'], S.GUARANTEE)  # a revision does not look for problems itself

    def test_rejected_candidates_and_concerns_are_carried_and_never_edited(self):
        request = S.example('synthetic_rejected_unresolved.revision_request.json')
        result = self.revise(request)
        self.assertEqual((result['outcome'], result['stop_reason']), ('no_change', 'no_actionable_findings'))
        self.assertEqual(len(result['carried_forward']['rejected_candidates']), 4)
        self.assertEqual(result['carried_forward']['rejected_candidates'],
                         request['critic_report']['rejected_llm_findings'])
        self.assertEqual(result['metrics']['unresolved_concerns'], 5)


class InsufficientInformation(S.Checks, unittest.TestCase):
    """Core case 6: a claim beyond the evidence becomes insufficient_information; requests stay open."""

    def setUp(self):
        self.request = S.request_for(S.case(CASE_A))
        self.result = self.revise(self.request)

    def test_unsupported_outcomes_become_insufficient_information(self):
        self.assertEqual([c['check_id'] for c in self.request['critic_report']['criticisms']],
                         ['CONCL-UNSUPPORTED'] * 3)
        conclusion = self.result['revised_argument_bundle']['execution_conclusion']
        self.assertEqual(set(conclusion['object_outcomes'].values()), {K.INSUFFICIENT})
        self.assertEqual(conclusion['claimed_outcome'], K.INSUFFICIENT)
        self.assertEqual(conclusion['statement'],
                         'R1 remains unresolved for all protected objects in the declared window.')
        self.assertTrue(all(r['disposition'] == 'edited' and r['verified_by_rules'] for r in
                            self.result['dispositions']))

    def test_no_solution_is_fabricated_and_the_evidence_requests_stay_open(self):
        self.assertEqual(self.result['metrics']['evidence_links_added'], 0)
        self.assertEqual(self.result['metrics']['nodes_added'], 0)
        self.assertEqual(len(self.result['carried_forward']['evidence_requests']), 3)
        self.assertEqual(self.result['carried_forward']['evidence_requests'],
                         self.request['critic_report']['evidence_requests'])

    def test_an_adapter_that_lacks_evidence_leaves_the_objection_unresolved(self):
        declined = {'edits': [], 'declined': [{'criticism_id': c, 'reason': 'insufficient_evidence',
                                               'note': 'No admitted evidence supports an edit.'}
                                              for c in ('CRIT-001', 'CRIT-002', 'CRIT-003')]}
        result = self.revise(self.request, ScriptedAdapter(declined))
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'insufficient_evidence'))
        self.assertEqual({r['reason'] for r in result['dispositions']}, {'adapter_insufficient_evidence'})


class OtherRuleFindings(S.Checks, unittest.TestCase):
    def test_a_wrong_execution_outcome_is_recomputed_by_aggregation(self):
        critic_request = S.fixture('critic.request.json')
        critic_request['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NO_VIOLATION
        critic_request['request_id'] = 'synthetic:aggregation'
        request = S.request_for(critic_request)
        self.assertEqual(request['critic_report']['criticisms'][0]['check_id'], 'CONCL-AGGREGATION')
        result = self.revise(request)
        self.assertEqual([(d['change'], d['before'], d['after']) for d in result['diff']],
                         [('execution_outcome_changed', K.NO_VIOLATION, K.INSUFFICIENT)])

    def test_a_missing_object_outcome_becomes_insufficient_information(self):
        critic_request = S.fixture('critic.request.json')
        del critic_request['argument_bundle']['execution_conclusion']['object_outcomes']['milk_1']
        critic_request['request_id'] = 'synthetic:object-outcome-missing'
        result = self.revise(S.request_for(critic_request))
        self.assertEqual([(d['change'], d['object_id'], d['before'], d['after']) for d in result['diff']],
                         [('object_outcome_changed', 'milk_1', None, K.INSUFFICIENT)])


class UnresolvedWording(S.Checks, unittest.TestCase):
    """An approved finding the templates cannot answer stays open; the bundle is not touched."""

    def test_a_strategy_objection_is_left_unresolved(self):
        critic_request = S.fixture('critic.request.json')
        finding = S.finding('milk_1', 'milk_1:S1', 'C05', 'The strategy infers support without a measurement.')
        request = S.request_for(critic_request, [finding])
        self.assertEqual(request['critic_report']['criticisms'][0]['node_id'], 'milk_1:S1')
        result = self.revise(request)
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'no_justified_improvement'))
        row = result['dispositions'][0]
        self.assertEqual((row['classification'], row['disposition'], row['reason']),
                         (C.ACTIONABLE, 'unresolved', 'adapter_no_justified_edit'))

    def test_a_model_adapter_may_reword_it_and_the_text_is_marked_as_a_proposal(self):
        critic_request = S.fixture('critic.request.json')
        finding = S.finding('milk_1', 'milk_1:S1', 'C05', 'The strategy infers support without a measurement.')
        request = S.request_for(critic_request, [finding])
        edit = {'op': 'replace_statement', 'object_id': 'milk_1', 'node_id': 'milk_1:S1',
                'statement': 'List the missing support and falling observations without inferring either.',
                'finding_ids': ['CRIT-001'], 'justification': 'Removes the support inference named in CRIT-001.'}
        result = self.revise(request, ScriptedAdapter({'edits': [edit], 'declined': []}))
        self.assertEqual(result['outcome'], 'revised')
        after = S.node(result['revised_argument_bundle'], 'milk_1', 'milk_1:S1')
        self.assertEqual((after['origin'], after['provenance']['prose_review'], after['validation_status']),
                         ('llm_proposal', 'required', 'proposed'))
        self.assertEqual(result['adapter']['kind'], 'scripted')


if __name__ == '__main__':
    unittest.main()
