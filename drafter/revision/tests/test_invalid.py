"""Invalid input and ungrounded revisions fail closed, and the original stays intact.

Three layers are attacked: the revision request (input), the adapter's proposal, and a revised
bundle or saved result that was changed by hand.
"""
from copy import deepcopy
from unittest import mock
import unittest

from critic import contract as K
from drafter.revision import contract as C, edits as E, engine as G, invariants as V
from drafter.revision.adapters import ScriptedAdapter
from drafter.revision.tests import support as S

CASE_A = 'case_a_unsupported_claim.json'
CASE_D = 'case_d_claim_hides_checker_result.json'
GOOD_TEXT = 'R1 stays unresolved for this object; the evidence does not establish an outcome.'


def edit(**fields):
    base = {'op': 'replace_statement', 'object_id': 'cream_cheese_1', 'node_id': 'cream_cheese_1:G1',
            'statement': GOOD_TEXT, 'finding_ids': ['CRIT-001'],
            'justification': 'Answers the approved finding CRIT-001.'}
    base.update(fields)
    return {k: v for k, v in base.items() if v is not None}


def scripted(*edits):
    return ScriptedAdapter({'edits': list(edits), 'declined': []})


class InvalidRequests(S.Checks, unittest.TestCase):
    """Input the Critic rejects, or a wrapper that does not bind, is never revised."""

    def rejected(self, critic_request, check_id):
        request = S.request_for(critic_request)
        self.assertEqual(request['critic_report']['review_status'], 'rejected_invalid_input')
        self.assertIn(check_id, [c['check_id'] for c in request['critic_report']['criticisms']])
        result = self.revise(request)
        self.assertEqual((result['outcome'], result['stop_reason']), ('rejected_invalid_input', 'invalid_input'))
        self.assertIsNone(result['proposal'])  # the adapter was never called
        return result

    def test_wrong_object(self):
        critic_request = S.fixture('critic.request.json')
        critic_request['argument_bundle']['graphs'][0]['graph']['nodes'][0]['scope']['object_id'] = 'milk_1'
        self.rejected(critic_request, 'GSN-NODE-OBJECT')

    def test_foreign_execution(self):
        critic_request = S.fixture('critic.request.json')
        critic_request['argument_bundle']['execution_id'] = 'another_execution'
        self.rejected(critic_request, 'BUNDLE-EXEC')

    def test_altered_r1_version(self):
        critic_request = S.fixture('critic.request.json')
        critic_request['evaluation_context']['requirement_version'] = '2.0.1'
        result = self.rejected(critic_request, 'GSN-NODE-REQ')
        self.assertTrue(all(r['disposition'] == 'not_actionable' for r in result['dispositions']))

    def test_fabricated_solution_in_the_input(self):
        critic_request = S.fixture('critic.request.json')
        graph = critic_request['argument_bundle']['graphs'][0]['graph']
        fake = deepcopy(graph['nodes'][0])
        fake.update(id='cream_cheese_1:E1', type='solution', evidence_id='ev:' + 'a' * 64, physical_claim=False,
                    origin='retrieved_observation', validation_status='verified_measurement')
        graph['nodes'].append(fake)
        graph['edges'].append({'source': 'cream_cheese_1:S1', 'target': 'cream_cheese_1:E1',
                               'type': 'supported_by'})
        self.rejected(critic_request, 'EV-MISSING')

    def test_lost_provenance_in_the_input(self):
        critic_request = S.fixture('critic.request.json')
        critic_request['argument_bundle']['graphs'][0]['graph']['nodes'][0]['provenance'] = {}
        self.rejected(critic_request, 'GSN-NODE-SCOPE')

    def test_request_changed_after_the_review(self):
        for label, change, wanted in (
                ('foreign variant', lambda r: r['evaluation_context'].update(variant_id='xmlenv:other'),
                 'report_request_hash_mismatch'),
                ('altered R1 version', lambda r: r['evaluation_context'].update(requirement_version='9.9.9'),
                 'report_request_hash_mismatch'),
                ('foreign execution', lambda r: r['evaluation_context'].update(execution_id='other'),
                 'report_execution_mismatch')):
            with self.subTest(label):
                request = S.guarantee_request()
                change(request['critic_request'])
                self.assertIn('critic_request_digest_mismatch', C.request_issues(request))
                S.rehash(request)  # a consistent forgery still fails: the report names what it reviewed
                result = self.revise(request)
                self.assertIn(wanted, result['request_issues'])
                self.assertEqual((result['outcome'], result['stop_reason']),
                                 ('rejected_invalid_input', 'invalid_input'))

    def test_finding_for_a_node_that_does_not_exist(self):
        request = S.guarantee_request()
        request['critic_report']['criticisms'][0]['node_id'] = 'cream_cheese_1:G9'
        result = self.revise(S.rehash(request))
        self.assertEqual(result['dispositions'][0]['classification'], C.TARGET_MISSING)
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'no_actionable_findings'))

    def test_finding_that_cites_unknown_evidence(self):
        request = S.guarantee_request()
        request['critic_report']['criticisms'][0]['evidence_ids'] = ['ev:' + 'b' * 64]
        result = self.revise(S.rehash(request))
        self.assertEqual(result['dispositions'][0]['classification'], C.UNKNOWN_EVIDENCE)
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'insufficient_evidence'))

    def test_forged_rule_finding(self):
        request = S.guarantee_request()
        forged = deepcopy(request['critic_report']['criticisms'][0])
        forged.update(criticism_id='CRIT-002', finding_source='deterministic', check_id='CONCL-UNSUPPORTED',
                      category='C06', category_name=K.CATEGORIES['C06'], human_review_required=False)
        request['critic_report']['criticisms'].append(forged)
        result = self.revise(S.rehash(request))
        self.assertIn('report_deterministic_findings_mismatch', result['request_issues'])
        self.assertEqual(result['outcome'], 'rejected_invalid_input')

    def test_altered_rule_finding_or_checker_admission(self):
        """A real rule finding changed by hand, with the digests recomputed, still fails."""
        for label, change in (
                ('other target', lambda c: c.update(object_id='vial_b')),
                ('no longer blocking', lambda c: c.update(blocking=False, severity='low')),
                ('other check', lambda c: c.update(check_id='CONCL-AGGREGATION')),
                ('other text', lambda c: c.update(explanation='Edited by hand.')),
                ('no evidence needed', lambda c: c.update(additional_evidence_needed=False)),
                ('relabelled as model-proposed', lambda c: c.update(finding_source='llm_proposed'))):
            with self.subTest(label):
                request = S.request_for(S.case('case_a_unsupported_claim.json'))
                change(request['critic_report']['criticisms'][0])
                result = self.revise(S.rehash(request))
                self.assertIn('report_deterministic_findings_mismatch', result['request_issues'])
                self.assertEqual(result['outcome'], 'rejected_invalid_input')
        request = S.request_for(S.case('case_d_claim_hides_checker_result.json'))
        request['critic_report']['checker_admission'][0]['admitted'] = False
        result = self.revise(S.rehash(request))
        self.assertIn('report_checker_admission_mismatch', result['request_issues'])

    def test_malformed_requests_never_raise(self):
        good = S.guarantee_request()
        without_field = {k: v for k, v in good.items() if k != 'critic_report'}
        cases = [None, [], 'text', 7, {}, without_field, {**good, 'round': 'one'}, {**good, 'extra': 1},
                 {**good, 'critic_report': {}}, {**good, 'critic_request': {}},
                 {**good, 'history': [{'round': 1}]}, {**good, 'max_rounds': 0},
                 {**good, 'round': float('nan')}]
        for value in cases:
            with self.subTest(repr(value)[:40]):
                result = G.revise(value)
                self.assertEqual(C.schema_problems(result, 'revision_result'), [])
                self.assertEqual((result['outcome'], result['stop_reason']),
                                 ('rejected_invalid_input', 'invalid_input'))
                self.assertTrue(result['request_issues'])
                self.assertIsNone(result['revised_argument_bundle'])

    def test_history_must_chain(self):
        run = G.run_cycle(S.guarantee_request(), review=S.review)
        second = run['requests'][1]
        self.assertEqual(C.request_issues(second), [])
        for label, change, wanted in (
                ('broken chain', lambda r: r['history'][0].update(recriticism_request_sha256='0' * 64),
                 'history_chain_mismatch'),
                ('other revision', lambda r: r['history'][0].update(revision_id='another'),
                 'history_revision_id_mismatch'),
                ('wrong round', lambda r: r['history'][0].update(round=2), 'history_round_sequence'),
                ('missing history', lambda r: r.update(history=[]), 'history_length_must_equal_round_minus_one'),
                ('round too high', lambda r: r.update(round=4), 'round_exceeds_max_rounds')):
            with self.subTest(label):
                request = deepcopy(second)
                change(request)
                self.assertIn(wanted, C.request_issues(request))


class UngroundedProposals(S.Checks, unittest.TestCase):
    """The adapter is untrusted. One refused edit means nothing is applied."""

    def refused(self, request, adapter, reason):
        bundle = deepcopy(request['critic_request']['argument_bundle'])
        result = self.revise(request, adapter)
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'no_justified_improvement'))
        reasons = [r for x in result['rejected_edits'] for r in x['reasons']]
        self.assertTrue(any(r.startswith(reason) for r in reasons), reasons)
        self.assertEqual(request['critic_request']['argument_bundle'], bundle)
        self.assertTrue(all(r['disposition'] != 'edited' for r in result['dispositions']))
        return result

    def test_wrong_object(self):
        self.refused(S.guarantee_request(), scripted(edit(object_id='milk_1', node_id='milk_1:G1')),
                     'edit_object_differs_from_finding_target')

    def test_nonexistent_node(self):
        self.refused(S.guarantee_request(), scripted(edit(node_id='cream_cheese_1:G9')),
                     'edit_node_differs_from_finding_target')

    def test_another_node_of_the_same_object(self):
        self.refused(S.guarantee_request(), scripted(edit(node_id='cream_cheese_1:S1')),
                     'edit_node_differs_from_finding_target')

    def test_fabricated_solution(self):
        request = S.guarantee_request()
        self.refused(request, scripted({'op': 'add_solution', 'object_id': 'cream_cheese_1',
                                        'evidence_id': 'ev:' + 'a' * 64, 'finding_ids': ['CRIT-001'],
                                        'justification': 'Adds support for the goal.'}), 'unknown_op')
        self.refused(request, scripted(edit(evidence_id='ev:' + 'a' * 64)), 'fields_must_be_exactly')
        self.refused(request, scripted(edit(type='solution')), 'fields_must_be_exactly')

    def test_attempted_loss_or_forgery_of_provenance(self):
        request = S.guarantee_request()
        self.refused(request, scripted(edit(provenance={})), 'fields_must_be_exactly')
        self.refused(request, scripted(edit(origin='retrieved_observation')), 'fields_must_be_exactly')
        self.refused(request, scripted(edit(validation_status='verified_measurement')), 'fields_must_be_exactly')

    def test_new_assurance_wording(self):
        for text in ('Cream_cheese_1 is certified for this task and nothing went wrong.',
                     'The object was safe during the whole window of this run.',
                     'The evidence proves that R1 holds for this object here.'):
            with self.subTest(text):
                self.refused(S.guarantee_request(), scripted(edit(statement=text)),
                             'statement_contains_assurance_wording')

    def test_unusable_or_unchanged_text(self):
        request = S.guarantee_request()
        self.refused(request, scripted(edit(statement='R')), 'statement_unusable_prose')
        self.refused(request, scripted(edit(statement=S.GUARANTEE)), 'statement_contains_assurance_wording')
        self.refused(request, scripted(edit(statement=' ')), 'statement_unusable_prose')

    def test_edit_without_finding_or_justification(self):
        request = S.guarantee_request()
        self.refused(request, scripted(edit(finding_ids=[])), 'finding_ids_must_be')
        self.refused(request, scripted(edit(finding_ids=['CRIT-009'])), 'finding_not_actionable')
        self.refused(request, scripted(edit(justification='  ')), 'justification_required')
        self.refused(request, scripted(edit(justification=None)), 'fields_must_be_exactly')

    def test_finding_that_was_not_approved_cannot_back_an_edit(self):
        request = S.request_for(
            S.fixture('critic.controlled-negative.request.json'),
            [S.guarantee_finding(), S.finding('milk_1', 'milk_1:G1', 'C06', 'The goal implies a conclusion.')],
            decide=False)
        request['finding_decisions'] = S.approve(request['critic_report'], ['CRIT-001'])
        self.refused(request, scripted(edit(), edit(object_id='milk_1', node_id='milk_1:G1',
                                                    finding_ids=['CRIT-002'])), 'finding_not_actionable')

    def test_one_refused_edit_blocks_the_valid_one_too(self):
        request = S.request_for(
            S.fixture('critic.controlled-negative.request.json'),
            [S.guarantee_finding(), S.finding('milk_1', 'milk_1:G1', 'C06', 'The goal implies a conclusion.')])
        result = self.refused(request, scripted(edit(), edit(object_id='milk_1', node_id='milk_1:G9',
                                                             finding_ids=['CRIT-002'])),
                              'edit_node_differs_from_finding_target')
        self.assertEqual([r['reason'] for r in result['dispositions']],
                         ['not_applied_because_another_edit_was_refused', 'edit_rejected'])

    def test_the_same_finding_or_target_cannot_be_used_twice(self):
        self.refused(S.guarantee_request(), scripted(edit(), edit(statement=GOOD_TEXT + ' Again.')),
                     'finding_already_used_by_another_edit')

    def test_wrong_kind_of_edit_for_the_finding(self):
        request = S.guarantee_request()
        self.refused(request, scripted({'op': 'set_object_outcome', 'object_id': 'cream_cheese_1',
                                        'outcome': K.NO_VIOLATION, 'finding_ids': ['CRIT-001'],
                                        'justification': 'Claims an outcome from a wording finding.'}),
                     'finding_does_not_allow_this_edit')
        self.refused(request, scripted({'op': 'remove_solution', 'object_id': 'cream_cheese_1',
                                        'node_id': 'cream_cheese_1:G1', 'finding_ids': ['CRIT-001'],
                                        'justification': 'Tries to delete the goal node.'}),
                     'finding_does_not_allow_this_edit')

    def test_fabricated_checker_verdict(self):
        outcome = {'op': 'set_object_outcome', 'justification': 'Sets an outcome no checker result backs.'}
        self.refused(S.request_for(S.case(CASE_A)),
                     scripted({**outcome, 'object_id': 'widget_a', 'outcome': K.NOT_APPLICABLE,
                               'finding_ids': ['CRIT-001']}),
                     'outcome_not_backed_by_an_admitted_checker_assessment')
        # case D: the admitted assessment reports a violation for object_00, so nothing else may be written
        for value in (K.NO_VIOLATION, K.NOT_APPLICABLE, K.INVALID_CONTRACT):
            with self.subTest(value):
                self.refused(S.request_for(S.case(CASE_D)),
                             scripted({**outcome, 'object_id': 'object_00', 'outcome': value,
                                       'finding_ids': ['CRIT-001']}),
                             'outcome_not_backed_by_an_admitted_checker_assessment')

    def test_adapter_failures_end_the_round_with_nothing_applied(self):
        class Raises:
            name, version, kind = 'raises', '0', 'scripted'

            def propose(self, context):
                raise RuntimeError('boom')

        class Mutates(Raises):
            def propose(self, context):
                context['argument_bundle']['graphs'].clear()
                context['findings'][0]['allowed_ops'].append('set_object_outcome')
                return {'edits': [], 'declined': []}

        request = S.guarantee_request()
        for adapter in (Raises(), ScriptedAdapter(None), ScriptedAdapter({'edits': {}, 'declined': []}),
                        ScriptedAdapter({'edits': [], 'declined': [{'criticism_id': 'CRIT-001'}]}),
                        ScriptedAdapter({'edits': [float('nan')], 'declined': []}), object()):
            with self.subTest(type(adapter).__name__):
                result = self.revise(request, adapter)
                self.assertEqual((result['outcome'], result['stop_reason']), ('failed', 'execution_failure'))
        result = self.revise(request, Mutates())  # the adapter only ever sees a copy
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'no_justified_improvement'))
        self.assertEqual(result['dispositions'][0]['reason'], 'adapter_gave_no_answer')

    def test_malformed_proposals_are_named(self):
        for proposal in (None, [], {'edits': []}, {'edits': {}, 'declined': []},
                         {'edits': [], 'declined': [{'criticism_id': 'CRIT-001'}]},
                         {'edits': [], 'declined': [], 'extra': 1}):
            with self.subTest(repr(proposal)):
                result = G.revise(S.guarantee_request(), ScriptedAdapter(proposal))
                self.assertEqual((result['outcome'], result['stop_reason']), ('failed', 'execution_failure'))
                self.assertIn('malformed', result['status_detail'])
                self.assertIsNone(result['proposal'])

    def test_non_dict_edits_are_refused_not_crashed_on(self):
        for bad in (None, 'replace', 3, [], {'op': ['x']}, {'op': 'replace_statement'}):
            with self.subTest(repr(bad)):
                result = G.revise(S.guarantee_request(), scripted(bad))
                self.assertEqual((result['outcome'], result['stop_reason']),
                                 ('unresolved', 'no_justified_improvement'))


class TamperedRevisions(S.Checks, unittest.TestCase):
    """A revised bundle changed by hand breaks a named rule, and a changed result does not replay."""

    @classmethod
    def setUpClass(cls):
        cls.request = S.guarantee_request()
        cls.result = G.revise(cls.request)

    def issues(self, change):
        bundle = deepcopy(self.result['revised_argument_bundle'])
        change(bundle)
        return S.rule_issues(self.request, self.result, bundle)

    def edited(self, bundle):
        return S.node(bundle, 'cream_cheese_1', 'cream_cheese_1:G1')

    def expect(self, change, wanted):
        issues = self.issues(change)
        self.assertTrue(any(i.startswith(wanted) for i in issues), issues)

    def test_the_untampered_bundle_passes(self):
        self.assertEqual(self.issues(lambda b: None), [])

    def test_wrong_object_or_foreign_execution_on_the_edited_node(self):
        self.expect(lambda b: self.edited(b)['scope'].update(object_id='milk_1'), 'protected_node_field_changed')
        self.expect(lambda b: self.edited(b)['scope'].update(execution_id='other'), 'protected_node_field_changed')

    def test_altered_r1_version_or_interval_on_the_edited_node(self):
        self.expect(lambda b: self.edited(b)['scope'].update(requirement_version='2.0.1'),
                    'protected_node_field_changed')
        self.expect(lambda b: self.edited(b)['scope'].update(interval=[10, 100]), 'protected_node_field_changed')

    def test_promotion_of_the_edited_node(self):
        self.expect(lambda b: self.edited(b).update(validation_status='verified_measurement'),
                    'protected_node_field_changed')
        self.expect(lambda b: self.edited(b).update(physical_claim=False), 'protected_node_field_changed')
        self.expect(lambda b: self.edited(b).update(evidence_id='ev:' + 'a' * 64), 'protected_node_field_changed')

    def test_loss_or_forgery_of_provenance(self):
        self.expect(lambda b: self.edited(b).update(provenance={}), 'written_node_provenance_shape')
        self.expect(lambda b: self.edited(b)['provenance'].update(finding_ids=['CRIT-007']),
                    'written_node_provenance_binding')
        self.expect(lambda b: self.edited(b)['provenance'].update(replaces_node_sha256='0' * 64),
                    'written_node_does_not_reference_the_node_it_replaces')
        original = S.node(self.request['critic_request']['argument_bundle'], 'cream_cheese_1',
                          'cream_cheese_1:G1')
        self.expect(lambda b: self.edited(b).update(provenance=deepcopy(original['provenance'])),
                    'written_node_provenance_shape')  # the generation run did not write this text
        self.expect(lambda b: self.edited(b).update(origin='retrieved_observation'), 'written_node_origin')

    def test_change_to_a_node_no_finding_names(self):
        self.expect(lambda b: S.node(b, 'milk_1', 'milk_1:G1').update(statement='Milk_1 stayed on the table.'),
                    'change_without_finding_and_justification')
        self.expect(lambda b: S.node(b, 'milk_1', 'milk_1:C1')['provenance'].update(run_id='x'),
                    'change_without_finding_and_justification')

    def test_fabricated_solution_or_other_added_node(self):
        def add_solution(bundle):
            graph = bundle['graphs'][0]['graph']
            fake = deepcopy(graph['nodes'][1])
            fake.update(id='cream_cheese_1:E1', type='solution', evidence_id='ev:' + 'a' * 64)
            graph['nodes'].append(fake)
            graph['edges'].append({'source': 'cream_cheese_1:S1', 'target': fake['id'], 'type': 'supported_by'})
        self.expect(add_solution, 'change_without_finding_and_justification')

    def test_removed_node_or_edge(self):
        def drop_node(bundle):
            graph = bundle['graphs'][2]['graph']
            graph['nodes'] = graph['nodes'][:-1]
        self.expect(drop_node, 'change_without_finding_and_justification')
        self.expect(lambda b: b['graphs'][2]['graph']['edges'].pop(), 'change_without_finding_and_justification')

    def test_object_roster_order_execution_and_graph_flags(self):
        self.expect(lambda b: b['protected_objects'].reverse(), 'unauthorised_change')
        self.expect(lambda b: b['graphs'].reverse(), 'unauthorised_change')
        self.expect(lambda b: b['graphs'].pop(), 'unauthorised_change')
        self.expect(lambda b: b.update(execution_id='other'), 'unauthorised_change')
        self.expect(lambda b: b['graphs'][0]['graph'].update(empirical_admission_enabled=True),
                    'unauthorised_change')
        self.expect(lambda b: b['graphs'][0]['graph']['nodes'].reverse(), 'unauthorised_change')

    def test_unsupported_outcome_or_conclusion_text(self):
        self.expect(lambda b: b['execution_conclusion']['object_outcomes'].update(milk_1=K.NO_VIOLATION),
                    'change_without_finding_and_justification')
        self.expect(lambda b: b['execution_conclusion'].update(claimed_outcome=K.NO_VIOLATION),
                    'change_without_finding_and_justification')
        self.expect(lambda b: b['execution_conclusion'].update(statement='R1 was satisfied in this run.'),
                    'change_without_finding_and_justification')

    def test_frozen_request_fields(self):
        original = self.request['critic_request']
        base = G.recriticism_request(self.request, self.result)
        self.assertEqual(V.frozen_issues(original, base), [])
        for label, change, wanted in (
                ('R1 version', lambda r: r['evaluation_context'].update(requirement_version='2.0.1'),
                 'frozen_context_changed:requirement_version'),
                ('R1 configuration', lambda r: r['evaluation_context']['r1_configuration'].update(extra=1),
                 'r1_configuration_digest_mismatch'),
                ('variant', lambda r: r['evaluation_context'].update(variant_id='other'),
                 'frozen_context_changed:variant_id'),
                ('task', lambda r: r['evaluation_context'].update(task_id='other'),
                 'frozen_context_changed:task_id'),
                ('object order', lambda r: r['evaluation_context']['protected_objects'].reverse(),
                 'frozen_context_changed:protected_objects'),
                ('interval', lambda r: r['evaluation_context']['monitored_interval'].update(interval=[10, 99]),
                 'frozen_context_changed:monitored_interval'),
                ('checker results', lambda r: r['checker_assessments'].append({}),
                 'frozen_field_changed:checker_assessments'),
                ('evidence', lambda r: r['evidence_package']['records'].append({}),
                 'frozen_field_changed:evidence_package'),
                ('retrieval', lambda r: r['retrieval_context'].update(complete_within_requested_scope=True),
                 'frozen_field_changed:retrieval_context')):
            with self.subTest(label):
                revised = deepcopy(base)
                change(revised)
                self.assertIn(wanted, V.frozen_issues(original, revised))

    def test_a_modified_source_record_is_caught(self):
        request = S.request_for(S.case('case_a_unsupported_claim.json'))
        result = G.revise(request)
        revised = G.recriticism_request(request, result)
        revised['evidence_package']['records'][0]['limitations'].append('edited')
        self.assertIn('frozen_field_changed:evidence_package',
                      V.frozen_issues(request['critic_request'], revised))

    def test_a_changed_result_does_not_replay(self):
        def with_change(change):
            result = deepcopy(self.result)
            change(result)
            return G.verify_result(self.request, result)

        self.assertEqual(with_change(lambda r: None), [])
        for label, change in (
                ('statement', lambda r: self.edited(r['revised_argument_bundle']).update(statement='Other text.')),
                ('provenance', lambda r: self.edited(r['revised_argument_bundle'])['provenance'].update(round=5)),
                ('digest', lambda r: r.update(revised_argument_bundle_sha256='0' * 64)),
                ('diff', lambda r: r['diff'][0].update(before_sha256='0' * 64)),
                ('disposition', lambda r: r['dispositions'][0].update(verified_by_rules=True)),
                ('validators', lambda r: r['validators'].pop()),
                ('metrics', lambda r: r['metrics'].update(nodes_changed=0)),
                ('other node', lambda r: S.node(r['revised_argument_bundle'], 'milk_1', 'milk_1:G1').update(
                    statement='Milk_1 stayed on the table the whole time.')),
                ('proposal', lambda r: r['proposal']['edits'][0].update(statement=GOOD_TEXT))):
            with self.subTest(label):
                issues = with_change(change)
                self.assertTrue(issues and issues[0].startswith('result_does_not_replay'), issues)
        self.assertTrue(with_change(lambda r: r.update(outcome='no_change'))[0].startswith('schema:'))
        other = S.guarantee_request(name='other')
        self.assertTrue(G.verify_result(other, self.result))  # a result holds only for its own request

    def test_the_shared_gsn_validator_rejects_what_it_should(self):
        critic_request = self.request['critic_request']
        bundle = deepcopy(self.result['revised_argument_bundle'])
        self.assertEqual(V.gsn_issues(critic_request, bundle), ([], []))
        self.edited(bundle).update(validation_status='verified_measurement')
        issues, _ = V.gsn_issues(critic_request, bundle)
        self.assertTrue(issues and 'goal promotion disabled' in issues[0], issues)
        bundle = deepcopy(self.result['revised_argument_bundle'])
        bundle['graphs'][0]['graph']['edges'].append(
            {'source': 'cream_cheese_1:S1', 'target': 'cream_cheese_1:G1', 'type': 'supported_by'})
        self.assertTrue(V.gsn_issues(critic_request, bundle)[0])

    def test_a_revision_that_would_add_a_rule_finding_is_discarded(self):
        # Removing the only supported_by edge of a goal is not an edit the host offers, so the rule is
        # exercised directly: the comparison of rule findings before and after must flag the new one.
        critic_request = S.fixture('critic.request.json')
        before, _ = C.fresh_review(critic_request)
        graph = critic_request['argument_bundle']['graphs'][0]['graph']
        graph['edges'] = [e for e in graph['edges'] if e['source'] != 'cream_cheese_1:S1']
        after, info = C.fresh_review(critic_request)
        invalid, new, stuck = V.rule_issues(before, after, info, [])
        self.assertEqual((invalid, stuck), ([], []))
        self.assertEqual(new, ['GSN-UNSUPPORTED-GOAL:C01:cream_cheese_1:cream_cheese_1:S1'])



class ValidatorsStopABrokenApply(unittest.TestCase):
    """Defence in depth: if the code that applies edits were wrong, the validators must stop the result.

    The apply step is replaced by one that damages the bundle after the real edit. The host cannot
    produce these bundles itself, so this is the only way to reach the validators with them.
    """

    def broken(self, damage, validator):
        request = S.guarantee_request()
        before, real = K.digest(request), E.apply

        def apply(*args):
            bundle, by = real(*args)
            damage(bundle)
            return bundle, by

        with mock.patch.object(E, 'apply', apply):
            result = G.revise(request)
        self.assertEqual(K.digest(request), before)
        self.assertEqual(C.schema_problems(result, 'revision_result'), [])
        self.assertEqual((result['outcome'], result['stop_reason']), ('unresolved', 'no_justified_improvement'))
        self.assertIn(validator, [v['name'] for v in result['validators'] if v['status'] == 'failed'])
        self.assertIsNone(result['revised_argument_bundle'])
        self.assertIsNone(result['recriticism'])
        self.assertEqual((result['edits'], result['diff']), ([], []))
        self.assertEqual(result['dispositions'][0]['reason'], 'validation_failed')
        self.assertEqual(result['metrics']['findings_addressed'], 0)
        return result

    def test_promoted_goal_is_stopped_by_the_shared_gsn_validator(self):
        result = self.broken(lambda b: S.node(b, 'cream_cheese_1', 'cream_cheese_1:G1').update(
            validation_status='verified_measurement'), 'shared_gsn_validator')
        failed = {v['name'] for v in result['validators'] if v['status'] == 'failed'}
        self.assertLessEqual({'shared_gsn_validator', 'critic_input_checks', 'diff_rules'}, failed)
        self.assertIs(result['metrics']['graphs_valid'], False)

    def test_new_rule_finding_is_stopped(self):
        def unsupport(bundle):
            graph = bundle['graphs'][3]['graph']
            graph['edges'] = [e for e in graph['edges'] if e['source'] != 'milk_1:S1']
        result = self.broken(unsupport, 'no_new_rule_findings')
        self.assertEqual(result['metrics']['new_rule_findings'], 1)

    def test_disconnected_node_is_stopped_by_the_drafter_structure_rules(self):
        def disconnect(bundle):
            graph = bundle['graphs'][1]['graph']
            graph['edges'] = [e for e in graph['edges'] if e['type'] != 'in_context_of']
        self.broken(disconnect, 'drafter_structure_rules')

    def test_fabricated_solution_is_stopped(self):
        def add_solution(bundle):
            graph = bundle['graphs'][0]['graph']
            fake = deepcopy(graph['nodes'][1])
            fake.update(id='cream_cheese_1:E1', type='solution', evidence_id='ev:' + 'a' * 64)
            graph['nodes'].append(fake)
            graph['edges'].append({'source': 'cream_cheese_1:S1', 'target': fake['id'], 'type': 'supported_by'})
        result = self.broken(add_solution, 'shared_gsn_validator')
        failed = {v['name'] for v in result['validators'] if v['status'] == 'failed'}
        self.assertLessEqual({'critic_input_checks', 'diff_rules'}, failed)

    def test_reordered_objects_and_foreign_execution_are_stopped(self):
        self.broken(lambda b: b['protected_objects'].reverse(), 'diff_rules')
        self.broken(lambda b: b.update(execution_id='another_execution'), 'critic_input_checks')

    def test_structure_rules_count_only_new_issues(self):
        original = S.fixture('critic.request.json')['argument_bundle']
        revised = deepcopy(original)
        graph = revised['graphs'][0]['graph']
        graph['edges'] = [e for e in graph['edges'] if e['type'] != 'in_context_of']
        self.assertEqual(V.structure_issues(original, revised), ['argument_disconnected_nodes:cream_cheese_1'])
        self.assertEqual(V.structure_issues(revised, revised), [])
        # the Critic's synthetic cases use unprefixed node IDs, an issue the original already has
        synthetic = S.case('case_c_correct_unresolved.json')['argument_bundle']
        self.assertEqual(V.structure_issues(synthetic, synthetic), [])


if __name__ == '__main__':
    unittest.main()
