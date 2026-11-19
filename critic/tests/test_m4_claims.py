"""Tests for the unsupported absolute safety claim rule (critic/claims.py, Critic 0.5.0, M4 task A3).

    python3 -m unittest critic.tests.test_m4_claims -v

CPU only. Development fixtures only: the Critic cases (synthetic) and the one-pass integration fixture
(known exposure). None of these inputs is a held-out RQ3 case.
"""
import copy
import json
import unittest
from pathlib import Path

from critic import claims as CL, contract as K, llm as L, review

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / 'critic' / 'cases'
FIXTURE = ROOT / 'integration' / 'fixtures' / 'one_pass_20261113' / 'artifacts' / 'models'
GUARANTEE = 'Cream_cheese_1 was guaranteed physically safe throughout this execution.'

FLAGGED = [
    GUARANTEE,
    'The robot is certified safe for this task.',
    'This proves the robot is safe.',
    'Safety was assured throughout.',
    'The object is completely safe.',
    'There is zero risk of a fall.',
    'The object was safe.',
    'Milk_1 remained safe on the table.',
    'R1 remains unresolved, so the object is therefore safe.',
    'No violation was detected, therefore the robot was clearly safe.',
]
NOT_FLAGGED = [
    'There is no guarantee that the object was safe.',
    'Safety cannot be guaranteed from these records.',
    'It is not completely safe.',
    'It is not known whether the object was safe.',
    'Use the configured R1 scope and source limitations; task success does not establish safety.',
    'The checker supports no_violation_observed_within_validated_coverage for object_01.',
    'No validated falling witness or qualified no-violation certificate is available, so neither a violation '
    'nor its absence can be concluded.',
    'R1 remains unresolved for this object across the declared monitoring window.',
    'The plan ensures safe handling.',
    'A fail-safe gripper was used.',
    'Safety requirement R1 applies to five objects.',
    'It is safe to say the checker abstained.',
    # Out of scope by design: an empirical event claim without safety wording is left to other checks.
    'The pose height never dropped, so it never fell.',
]


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def claims(report):
    return [c for c in report['criticisms'] if c['check_id'] == CL.CHECK_ID]


def node(req, object_id, node_id):
    graph = next(g['graph'] for g in req['argument_bundle']['graphs'] if g['object_id'] == object_id)
    return next(n for n in graph['nodes'] if n['id'] == node_id)


class Wording(unittest.TestCase):
    def test_flagged_wording(self):
        for text in FLAGGED:
            with self.subTest(text):
                self.assertTrue(CL.absolute_safety_phrase(text))

    def test_not_flagged_wording(self):
        for text in NOT_FLAGGED:
            with self.subTest(text):
                self.assertIsNone(CL.absolute_safety_phrase(text))

    def test_non_text_is_ignored(self):
        for value in (None, 3, [], {}, ['safe']):
            self.assertIsNone(CL.absolute_safety_phrase(value))

    def test_no_development_statement_without_safety_wording_is_flagged(self):
        """Every statement in the Critic cases and the original one-pass fixture, except the two known ones."""
        known = {'The robot is certified safe for this task'}  # case A, a deliberate unsupported claim
        paths = sorted(CASES.glob('case_*.json')) + [FIXTURE / 'critic.request.json']
        for path in paths:
            req = load(path)
            bundle = req['argument_bundle']
            texts = [bundle['execution_conclusion']['statement']] + [
                n['statement'] for g in bundle['graphs'] for n in g['graph']['nodes']]
            for text in texts:
                clause = CL.absolute_safety_phrase(text)
                with self.subTest(path=path.name, text=text[:60]):
                    self.assertTrue(clause is None or clause in known, clause)


class InjectedGuarantee(unittest.TestCase):
    """The negative control from the one-pass fixture: a goal that guarantees physical safety."""

    @classmethod
    def setUpClass(cls):
        cls.req = load(FIXTURE / 'critic.controlled-negative.request.json')
        cls.report = review(cls.req)

    def test_one_correctly_scoped_unsupported_claim_objection(self):
        found = claims(self.report)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual((c['object_id'], c['node_id'], c['category'], c['phase'], c['finding_source']),
                         ('cream_cheese_1', 'cream_cheese_1:G1', 'C12', 'review', 'deterministic'))
        self.assertEqual((c['severity'], c['blocking'], c['human_review_required'], c['additional_evidence_needed']),
                         ('high', True, True, True))
        self.assertIn(GUARANTEE, c['explanation'])
        self.assertIn('No admitted checker assessment is supplied', c['explanation'])
        self.assertIn(CL.RULE_VERSION, c['requirement_refs'])
        self.assertEqual(self.report['review_status'], 'completed')

    def test_it_asks_for_admitted_evidence_and_declares_no_violation(self):
        c = claims(self.report)[0]
        self.assertIn('does not say a violation occurred', c['suggested_action'])
        request = [r for r in self.report['evidence_requests'] if r['criticism_id'] == c['criticism_id']]
        self.assertEqual(request, [{'object_id': 'cream_cheese_1', 'measurement_type': 'checker_assessment',
                                    'interval': [10, 257], 'reason': request[0]['reason'],
                                    'criticism_id': c['criticism_id']}])
        # no fabricated verdict: no other finding, and no outcome is changed or asserted
        self.assertEqual(len(self.report['criticisms']), 1)
        self.assertNotIn(K.VIOLATION, json.dumps(self.report['criticisms']))
        summary = self.report['summary']
        self.assertEqual((summary['claimed_execution_outcome'], summary['accepted_execution_outcome']),
                         (K.INSUFFICIENT, K.INSUFFICIENT))

    def test_the_unmodified_original_is_a_clean_control(self):
        report = review(load(FIXTURE / 'critic.request.json'))
        self.assertEqual((report['review_status'], report['criticisms']), ('completed', []))

    def test_a_model_objection_on_the_same_node_is_not_counted_twice(self):
        reply = {'findings': [{'object_id': 'cream_cheese_1', 'node_id': 'cream_cheese_1:G1', 'category': 'C12',
                               'severity': 'high', 'explanation': 'The goal states "' + GUARANTEE + '"',
                               'evidence_ids': [], 'suggested_action': 'Remove the guarantee.'}]}
        report = review(self.req, L.ScriptedLLM(json.dumps(reply)))
        self.assertEqual(len(claims(report)), 1)
        self.assertEqual([c['finding_source'] for c in report['criticisms']], ['deterministic'])
        self.assertEqual(report['rejected_llm_findings'][0]['reason'], 'duplicate of a deterministic finding')

    def test_the_execution_conclusion_is_checked_too(self):
        req = copy.deepcopy(self.req)
        req['argument_bundle']['execution_conclusion']['statement'] = 'The robot is certified safe for this task.'
        found = claims(review(req))
        self.assertEqual([(c['object_id'], c['node_id']) for c in found],
                         [('cream_cheese_1', 'cream_cheese_1:G1'), (None, None)])
        self.assertIn('No admitted checker assessment is supplied', found[1]['explanation'])


class FiveValuedSemantics(unittest.TestCase):
    """A qualified negative is not a guarantee, and insufficient evidence is never safety."""

    CASE_D = CASES / 'case_d_claim_hides_checker_result.json'

    def test_a_qualified_negative_backed_by_an_admitted_checker_is_not_flagged(self):
        report = review(load(self.CASE_D))
        self.assertEqual(claims(report), [])
        self.assertEqual(load(self.CASE_D)['argument_bundle']['execution_conclusion']['object_outcomes']['object_01'],
                         K.NO_VIOLATION)

    def test_a_guarantee_is_flagged_even_with_an_admitted_no_violation_result(self):
        req = load(self.CASE_D)
        node(req, 'object_01', 'G1')['statement'] = 'object_01 was guaranteed safe during frames 0-2.'
        found = claims(review(req))
        self.assertEqual([(c['object_id'], c['node_id']) for c in found], [('object_01', 'G1')])
        self.assertIn('admitted checker assessment(s) are supplied', found[0]['explanation'])
        self.assertIn('not a guarantee', found[0]['explanation'])

    def test_insufficient_information_stated_as_safety_is_flagged(self):
        req = load(FIXTURE / 'critic.request.json')
        node(req, 'milk_1', 'milk_1:U1')['statement'] = ('Initial support cannot be established from the supplied '
                                                         'evidence, so milk_1 was therefore safe.')
        found = claims(review(req))
        self.assertEqual([(c['object_id'], c['node_id']) for c in found], [('milk_1', 'milk_1:U1')])

    def test_honest_unresolved_arguments_are_left_alone(self):
        for path in (CASES / 'case_c_correct_unresolved.json', FIXTURE / 'critic.request.json'):
            with self.subTest(path.name):
                self.assertEqual(review(load(path))['criticisms'], [])


class OtherInputsWithTheControlPresent(unittest.TestCase):
    """The new rule does not weaken the existing input checks (A3: malformed numbers, wrong execution scope,
    wrong evidence namespace, unsupported citations)."""

    def control(self):
        return load(FIXTURE / 'critic.controlled-negative.request.json')

    def assert_rejected(self, req, check_id):
        report = review(req)
        self.assertEqual(report['review_status'], 'rejected_invalid_input')
        self.assertIn(check_id, [c['check_id'] for c in report['criticisms'] if c['phase'] == 'validation'])
        self.assertFalse(report['llm']['called'])
        return report

    def test_malformed_numeric_evidence(self):
        req = self.control()
        req['argument_bundle']['graphs'][0]['graph']['nodes'][0]['provenance']['weight'] = 10 ** 1000
        report = review(req)
        self.assertEqual(report['review_status'], 'rejected_invalid_input')
        self.assertFalse(report['llm']['called'])

    def test_wrong_execution_scope(self):
        req = self.control()
        req['argument_bundle']['execution_id'] = 'another_execution'
        report = self.assert_rejected(req, 'BUNDLE-EXEC')
        # the guarantee is still reported, as a provisional review finding of a rejected input
        self.assertEqual([c['phase'] for c in claims(report)], ['review'])

    def test_wrong_evidence_namespace_and_missing_citation(self):
        for evidence_id in ('citation:' + '0' * 64, 'ev:' + '0' * 64):
            with self.subTest(evidence_id[:9]):
                req = self.control()
                graph = req['argument_bundle']['graphs'][1]['graph']
                fake = copy.deepcopy(graph['nodes'][0])
                fake.update(id='ketchup_1:E1', type='solution', evidence_id=evidence_id, physical_claim=False,
                            origin='retrieved_observation', validation_status='verified_measurement')
                graph['nodes'].append(fake)
                graph['edges'].append({'source': 'ketchup_1:S1', 'target': 'ketchup_1:E1', 'type': 'supported_by'})
                self.assert_rejected(req, 'EV-MISSING')

    def test_unsupported_model_citation_is_rejected(self):
        reply = {'findings': [{'object_id': 'milk_1', 'node_id': 'milk_1:G1', 'category': 'C06', 'severity': 'high',
                               'explanation': 'The goal overstates the evidence.', 'evidence_ids': ['ev:' + '1' * 64],
                               'suggested_action': 'Qualify it.'}]}
        report = review(self.control(), L.ScriptedLLM(json.dumps(reply)))
        self.assertEqual(report['rejected_llm_findings'][0]['reason'],
                         'cites evidence IDs that are not in the package (possible invention)')
        self.assertEqual(len(claims(report)), 1)


if __name__ == '__main__':
    unittest.main()
