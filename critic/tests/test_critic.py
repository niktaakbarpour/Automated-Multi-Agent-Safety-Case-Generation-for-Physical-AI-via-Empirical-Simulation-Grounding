"""Critic tests. Run from the repository root:

    python3 -m unittest discover -s critic/tests -t . -v

No network, no GPU and no LLM service are needed.
"""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from critic import assessments as A, checks, contract as K, llm as L, retrieval as R, review
from critic.cases import build_cases as B, phase5 as P
from critic.tests import oracles as O

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / 'critic' / 'cases'
EXPECTED = json.loads((CASES / 'expected.json').read_text())
GSN_DIR = ROOT / 'evaluation' / 'r1_v4' / 'evidence_registry_gsn'

O.install()  # the team's modules, used as oracles, also load on Python 3.9 (see oracles.py)
jsonschema = O.jsonschema
from evaluation.r1_v4.evidence_registry_gsn.gsn import Graph, Node, Edge  # noqa: E402  teammate's validator


def load(name):
    return json.loads((CASES / name).read_text())


def flagged(report, **want):
    return [c for c in report['criticisms'] if all(c.get(k) == v for k, v in want.items())]


CASE_D = 'case_d_claim_hides_checker_result.json'


def checker_request(*items, test_fixture=True, claims=None):
    """Case D (the R1 checker's own fixture) with the given checker entries and claimed outcomes."""
    req = load(CASE_D)
    req['test_fixture'] = test_fixture
    if items:
        req['checker_assessments'] = [copy.deepcopy(i) for i in items]
    for oid, claim in (claims or {}).items():
        req['argument_bundle']['execution_conclusion']['object_outcomes'][oid] = claim
    return req


def forged(change):
    """The real checker entry, changed by change(item), with both hashes recomputed (a consistent forgery)."""
    item = copy.deepcopy(B.checker_item())
    change(item)
    return A.rehash(item)


def check_ids(report):
    return {c['check_id'] for c in report['criticisms']}


def admitted_objects(report):
    return {a['object_id'] for a in report['checker_admission'] if a['admitted']}


class Cases(unittest.TestCase):
    def test_expected_findings(self):
        for name, exp in EXPECTED.items():
            with self.subTest(case=name):
                report = review(load(name))
                for want in exp['must_flag']:
                    self.assertTrue(flagged(report, **want), f'{name}: missing {want}')
                self.assertEqual(report['summary']['blocking_defects'], exp['blocking_expected'], name)
                self.assertEqual(report['review_status'], exp['review_status_expected'], name)

    def test_correct_unresolved_argument_is_not_criticised(self):
        report = review(load('case_c_correct_unresolved.json'))
        self.assertEqual(report['criticisms'], [])
        self.assertIn('not as "no violation"', ' '.join(report['unresolved_concerns']))

    def test_reports_match_schema(self):
        report_schema = json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text())
        request_schema = json.loads((ROOT / 'critic/schemas/critic_request.schema.json').read_text())
        graph_schema = json.loads((GSN_DIR / 'gsn_graph.schema.json').read_text())
        record_schema = json.loads((GSN_DIR / 'registry_record.schema.json').read_text())
        for name in EXPECTED:
            req = load(name)
            O.validate(req, request_schema)
            for item in req['argument_bundle']['graphs']:
                O.validate(item['graph'], graph_schema)
            for rec in req['evidence_package']['records']:
                O.validate(rec, record_schema)
            for backend in (L.NullLLM(), L.ScriptedLLM((CASES / 'scripted_replies' / f'{name[:6]}.txt').read_text())):
                O.validate(review(req, backend), report_schema)

    def test_cases_are_reproducible(self):
        from critic.cases import build_cases
        self.assertEqual(build_cases.case_a(), load('case_a_unsupported_claim.json'))
        self.assertEqual(build_cases.case_b(), load('case_b_missing_or_wrong_evidence.json'))
        self.assertEqual(build_cases.case_c(), load('case_c_correct_unresolved.json'))
        self.assertEqual(build_cases.case_d(), load(CASE_D))


def with_configuration(req, change):
    """Change the request's R1 configuration, re-hash it, and copy its objects and surfaces into the context."""
    ctx = req['evaluation_context']
    change(ctx['r1_configuration'])
    ctx['r1_configuration_sha256'] = K.digest(ctx['r1_configuration'])
    ctx['protected_objects'] = list(ctx['r1_configuration']['protected_objects'])
    ctx['support_surfaces'] = [s['id'] for s in ctx['r1_configuration']['support_surfaces']]
    req['argument_bundle']['protected_objects'] = list(ctx['protected_objects'])
    return req


def set_objects(objects):
    def change(config):
        surfaces = [s['id'] for s in config['support_surfaces']]
        config['protected_objects'] = list(objects)
        config['object_surface_mapping'] = {o: surfaces[:1] for o in objects}
    return change


class GeneralizedConfiguration(unittest.TestCase):
    """R1 is configurable: no fixed object list, no fixed surface, but always the configuration's own list."""

    def test_extra_configured_object_is_reported_missing(self):
        req = with_configuration(load('case_c_correct_unresolved.json'),
                                 set_objects(['widget_a', 'vial_b', 'carton_c', 'flask_d']))
        report = review(req)
        self.assertTrue(flagged(report, check_id='BUNDLE-MISSING', object_id='flask_d'))
        self.assertEqual(report['summary']['objects_missing'], ['flask_d'])
        self.assertFalse(check_ids(report) & {'CONFIG-OBJECTS', 'CONFIG-HASH'})

    def test_fewer_configured_objects_are_not_demanded(self):
        req = with_configuration(load('case_c_correct_unresolved.json'), set_objects(['widget_a']))
        req['argument_bundle']['graphs'] = req['argument_bundle']['graphs'][:1]
        req['argument_bundle']['execution_conclusion']['object_outcomes'] = {'widget_a': K.INSUFFICIENT}
        req['evidence_package']['records'] = [r for r in req['evidence_package']['records']
                                              if r['object_id'] == 'widget_a']
        report = review(req)
        self.assertEqual(report['review_status'], 'completed')
        self.assertFalse(report['summary']['blocking_defects'], report['criticisms'])

    def test_audit_probe_unauthorized_reduction(self):
        # The audit's I6 probe: context and bundle both shrink to one object; the configuration still has three.
        req = load('case_c_correct_unresolved.json')
        req['evaluation_context']['protected_objects'] = ['widget_a']
        req['argument_bundle']['protected_objects'] = ['widget_a']
        req['argument_bundle']['graphs'] = req['argument_bundle']['graphs'][:1]
        req['argument_bundle']['execution_conclusion']['object_outcomes'] = {'widget_a': K.INSUFFICIENT}
        report = review(req)
        self.assertIn('CONFIG-OBJECTS', check_ids(report))
        self.assertEqual(report['review_status'], 'rejected_invalid_input')

    def test_graph_for_unconfigured_object(self):
        req = with_configuration(load('case_c_correct_unresolved.json'), set_objects(['widget_a', 'vial_b']))
        report = review(req)
        self.assertTrue(flagged(report, check_id='BUNDLE-EXTRA', object_id='carton_c'))


class ConclusionsAndAggregation(unittest.TestCase):
    def test_precedence(self):
        agg = K.execution_outcome
        self.assertEqual(agg([K.NO_VIOLATION, K.INSUFFICIENT, K.VIOLATION]), K.VIOLATION)
        self.assertEqual(agg([K.NO_VIOLATION, K.INVALID_CONTRACT, K.INSUFFICIENT]), K.INVALID_CONTRACT)
        self.assertEqual(agg([K.NO_VIOLATION, K.INSUFFICIENT]), K.INSUFFICIENT)
        self.assertEqual(agg([K.NO_VIOLATION, K.NOT_APPLICABLE]), K.NO_VIOLATION)
        self.assertEqual(agg([K.NOT_APPLICABLE]), K.NOT_APPLICABLE)

    def test_wrong_aggregation_is_flagged(self):
        req = load('case_c_correct_unresolved.json')
        req['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NO_VIOLATION
        found = flagged(review(req), check_id='CONCL-AGGREGATION')
        self.assertEqual(found[0]['suggested_action'],
                         'Set the execution outcome to insufficient_information, or fix the object outcomes.')

    def test_checker_contradiction(self):
        report = review(checker_request(claims={'object_01': K.VIOLATION}))  # the checker reports no violation
        self.assertTrue(flagged(report, check_id='CONCL-CONTRADICTION', object_id='object_01', category='C07'))

    def test_matching_checker_supports_claim(self):
        report = review(checker_request())  # object_01 no violation and object_02 not applicable, as the checker says
        for oid in ('object_01', 'object_02'):
            self.assertFalse(flagged(report, object_id=oid))

    def test_not_applicable_needs_evidence(self):
        req = load('case_c_correct_unresolved.json')
        req['argument_bundle']['execution_conclusion']['object_outcomes']['vial_b'] = K.NOT_APPLICABLE
        self.assertTrue(flagged(review(req), object_id='vial_b', category='C08'))

    def test_tampered_record_is_detected(self):
        req = load('case_c_correct_unresolved.json')
        req['evidence_package']['records'][0]['validation_status'] = 'verified_source'
        self.assertTrue(flagged(review(req), check_id='EV-HASH'))

    def test_insufficient_claim_cannot_hide_a_checker_violation(self):
        report = review(checker_request())
        self.assertTrue(flagged(report, check_id='CONCL-HIDES-VIOLATION', object_id='object_00', category='C07'))

    def test_invalid_contract_claim_needs_a_checker(self):
        req = load('case_c_correct_unresolved.json')
        req['argument_bundle']['execution_conclusion']['object_outcomes']['widget_a'] = K.INVALID_CONTRACT
        req['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.INVALID_CONTRACT
        self.assertTrue(flagged(review(req), check_id='CONCL-UNSUPPORTED', object_id='widget_a'))

    def test_no_violation_claim_over_a_retrieval_gap(self):
        req = checker_request()
        req['retrieval_context']['gaps'] = [
            {'object_id': 'object_01', 'measurement_type': 'contact', 'interval': [1, 2]},
            {'object_id': 'object_01', 'measurement_type': 5, 'interval': 'bad', 'reason': []}]  # malformed on purpose
        report = review(req)
        self.assertEqual(len(flagged(report, check_id='CONCL-GAP', object_id='object_01')), 2)
        requests = [r for r in report['evidence_requests'] if r['object_id'] == 'object_01']
        self.assertIn({'object_id': 'object_01', 'measurement_type': 'contact', 'interval': [1, 2]},
                      [{k: r[k] for k in ('object_id', 'measurement_type', 'interval')} for r in requests])
        O.validate(report, json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text()))

    def test_unknown_outcome_value(self):
        req = load('case_c_correct_unresolved.json')
        req['argument_bundle']['execution_conclusion']['object_outcomes']['vial_b'] = 'safe'
        self.assertTrue(flagged(review(req), check_id='CONCL-BAD-VALUE', object_id='vial_b', category='C01'))

    def test_missing_object_is_reported_once(self):
        report = review(load('case_b_missing_or_wrong_evidence.json'))
        self.assertEqual(len(flagged(report, object_id='carton_c')), 1)

    def test_related_case_misuse(self):
        req = load('case_b_missing_or_wrong_evidence.json')
        target = req['evaluation_context']['execution_id']
        other = [r['id'] for r in req['evidence_package']['records'] if r['execution_id'] != target]
        req['retrieval_context']['related_case_evidence_ids'] = other
        self.assertTrue(flagged(review(req), check_id='EV-RELATED-CASE', category='C11'))


class CheckerAdmission(unittest.TestCase):
    """Audit I1: a checker result is used only after the Critic validates it (critic/assessments.py)."""

    def test_real_checker_output_is_admitted_in_a_fixture(self):
        report = review(load(CASE_D))
        self.assertEqual(admitted_objects(report), {'object_00', 'object_01', 'object_02'})
        self.assertEqual({a['route'] for a in report['checker_admission']}, {A.ROUTE_SYNTHETIC})
        hidden = flagged(report, check_id='CONCL-HIDES-VIOLATION', object_id='object_00')
        self.assertEqual(len(hidden), 1)
        self.assertIn('synthetic', hidden[0]['explanation'])
        self.assertNotIn('validated', hidden[0]['explanation'])
        self.assertEqual(hidden[0]['evidence_ids'], [A.assessment_id(B.checker_item()['result'], 'object_00')])
        # the two claims that match the checker are not criticised
        self.assertFalse(flagged(report, object_id='object_01'))
        self.assertFalse(flagged(report, object_id='object_02'))
        self.assertIn('synthetic test-fixture', ' '.join(report['unresolved_concerns']))

    def test_stored_checker_output_is_what_the_checker_produces(self):
        # The checker itself needs jsonschema (evaluation/r1_v4/requirements.txt); on 3.9 see oracles.py.
        O.require(self, O.has_jsonschema4(), 'the R1 checker needs jsonschema>=4')
        from evaluation.r1_v4.runtime import assess
        fixture = json.loads((ROOT / B.CHECKER_FIXTURE).read_text())
        self.assertEqual(assess(fixture), B.checker_item()['result'])

    def test_audit_probe_self_asserted_label(self):
        # The audit's probe: a caller-written 'validated_checker' label with a made-up ID and wrong scope.
        probe = {'assessment_id': 'made-up', 'authority': 'validated_checker', 'checker_version': 'test',
                 'requirement_id': 'R999', 'requirement_version': '999', 'execution_id': 'synthetic-execution',
                 'task_id': 'wrong-task', 'variant_id': 'wrong-variant', 'object_id': 'object_00',
                 'applicability': 'applicable', 'outcome': K.VIOLATION, 'interval': [10000, 10001]}
        report = review(checker_request(probe))
        self.assertFalse(flagged(report, category='C07'))
        self.assertIn('CHK-SHAPE', check_ids(report))
        self.assertEqual(admitted_objects(report), set())

    def test_audit_probe_consistent_forgery_out_of_scope(self):
        # The same wrong scope inside a real checker result whose hashes were recomputed.
        def change(item):
            cfg, prov = item['configuration'], item['result']['provenance']
            cfg['requirement_id'] = 'R999'
            cfg['task_id'] = prov['task_id'] = 'wrong-task'
            cfg['monitoring_interval']['start']['value'] = 10000
            cfg['monitoring_interval']['end']['value'] = 10001
        report = review(checker_request(forged(change)))
        self.assertFalse(flagged(report, category='C07'))
        self.assertTrue({'CHK-REQUIREMENT', 'CHK-TASK', 'CHK-CONFIGURATION'} <= check_ids(report))
        self.assertFalse(check_ids(report) & {'CHK-HASH', 'CHK-CONFIG-HASH'})
        self.assertEqual(admitted_objects(report), set())

    def test_audit_probe_synthetic_result_in_real_request(self):
        report = review(checker_request(test_fixture=False))
        self.assertFalse(flagged(report, category='C07'))
        self.assertIn('CHK-ADMISSION', check_ids(report))
        self.assertEqual(admitted_objects(report), set())
        # and it cannot support a claim either
        report = review(checker_request(test_fixture=False, claims={'object_00': K.VIOLATION}))
        self.assertTrue(flagged(report, check_id='CONCL-UNSUPPORTED', object_id='object_00'))
        self.assertTrue(flagged(report, check_id='CONCL-UNSUPPORTED', object_id='object_01'))

    def test_empirical_admission_is_disabled(self):
        self.assertEqual(A.EMPIRICAL_ADMITTED_STATUSES, frozenset())
        for fixture in (True, False):
            report = review(checker_request(forged(lambda i: i['result'].update(synthetic=False)),
                                            test_fixture=fixture))
            self.assertEqual(admitted_objects(report), set())
            text = ' '.join(c['explanation'] for c in flagged(report, check_id='CHK-ADMISSION'))
            self.assertIn('empirical admission is disabled', text)

    def test_edited_result_or_configuration_fails_its_hash(self):
        item = B.checker_item()
        item['result']['object_assessments'][0]['outcome'] = K.INSUFFICIENT
        report = review(checker_request(item))
        # reported once, against the whole result, not once per object
        hashes = flagged(report, check_id='CHK-HASH')
        self.assertEqual(len(hashes), 1)
        result_id = f"ca:{item['result']['assessment_hash']}"
        self.assertEqual((hashes[0]['object_id'], hashes[0]['evidence_ids']), (None, [result_id]))
        self.assertEqual({tuple(a['problems']) for a in report['checker_admission']}, {('CHK-HASH',)})
        item = B.checker_item()
        item['configuration']['protected_objects'].append('object_03')
        report = review(checker_request(item))
        self.assertIn('CHK-CONFIG-HASH', check_ids(report))
        self.assertEqual(admitted_objects(report), set())

    def test_run_the_checker_refused_is_not_used(self):
        report = review(checker_request(forged(lambda i: i['result']['provenance'].update(admitted_purpose=None))))
        self.assertIn('CHK-ADMISSION', check_ids(report))
        self.assertFalse(flagged(report, category='C07'))

    def test_configuration_must_match_the_review(self):
        # The checker must have run on the review's own configuration; objects, surfaces and interval follow.
        def template(i):  # a template configuration is not tied to any execution
            i['configuration']['execution_id'] = None
            i['result']['provenance']['execution_id'] = None
        cases = {
            ('CHK-EXECUTION', 'CHK-CONFIGURATION'): lambda i: i['configuration'].update(execution_id='other'),
            ('CHK-CONFIGURATION',): lambda i: i['configuration']['protected_objects'].pop(),
            ('CHK-CONFIGURATION', ''): lambda i: i['configuration']['monitoring_interval'].update(
                end={'kind': 'terminal_recorded_snapshot', 'value': None}),
            ('CHK-EXECUTION', 'CHK-CONFIGURATION', ''): template,
            ('CHK-PRODUCER',): lambda i: i['result'].update(checker_version='9.9.9'),
        }
        for expected, change in cases.items():
            with self.subTest(expected):
                report = review(checker_request(forged(change)))
                self.assertTrue(set(e for e in expected if e) <= check_ids(report), check_ids(report))
                self.assertEqual(admitted_objects(report), set())
                self.assertFalse(flagged(report, category='C07'))

    def test_clock_must_match(self):
        req = checker_request()
        req['evaluation_context']['monitored_interval']['clock'] = 'simulation_time_s'
        report = review(req)
        self.assertIn('CONFIG-INTERVAL', check_ids(report))  # the context no longer matches its configuration
        self.assertEqual(report['review_status'], 'rejected_invalid_input')

    def test_missing_surface_list_fails_closed(self):
        req = checker_request()
        del req['evaluation_context']['support_surfaces']
        report = review(req)
        self.assertTrue({'SCHEMA-REQUEST', 'CONFIG-SURFACES'} <= check_ids(report))
        self.assertEqual(report['review_status'], 'rejected_invalid_input')

    def _object_change(self, change, obj='object_00'):
        def edit(item):
            oa = next(o for o in item['result']['object_assessments'] if o['object_id'] == obj)
            change(oa, item['result'])
        return review(checker_request(forged(edit)))

    def test_object_evidence(self):
        cases = {
            'not one of the checker records': lambda oa, r: oa['evidence_ids'].append('made_up_record'),
            'another object\'s record': lambda oa, r: oa['evidence_ids'].append('object_01_clear'),
            'evidence the checker did not admit': lambda oa, r: r['admitted_evidence_ids'].remove('object_00_fall'),
            'no evidence at all': lambda oa, r: oa.update(evidence_ids=[]),
        }
        for name, change in cases.items():
            with self.subTest(name):
                report = self._object_change(change)
                self.assertIn('CHK-EVIDENCE', check_ids(report))
                self.assertNotIn('object_00', admitted_objects(report))
                self.assertIn('object_01', admitted_objects(report))  # other objects are unaffected
                self.assertFalse(flagged(report, category='C07'))

    def test_object_consistency_rules(self):
        cases = {
            'violation without applicability': lambda oa, r: oa.update(applicability='indeterminate'),
            'no-violation with missing coverage': lambda oa, r: (oa.update(outcome=K.NO_VIOLATION),
                                                                 oa['coverage']['missing'].append('cell')),
            'not-applicable while applicable': lambda oa, r: oa.update(outcome=K.NOT_APPLICABLE),
        }
        for name, change in cases.items():
            with self.subTest(name):
                report = self._object_change(change)
                self.assertIn('CHK-CONSISTENCY', check_ids(report))
                self.assertNotIn('object_00', admitted_objects(report))

    def test_object_scope_and_shape(self):
        cases = {
            'CHK-OBJECT': lambda oa, r: oa.update(object_id='object_99'),
            'CHK-EXECUTION': lambda oa, r: oa.update(execution_id='other-execution'),
            'CHK-REQUIREMENT': lambda oa, r: oa.update(requirement_version='9.9.9'),
            'CHK-SURFACES': lambda oa, r: oa.update(surfaces=['root_B']),  # configured, but not mapped to object_00
            'CHK-ADMISSION': lambda oa, r: oa.update(validation_status='validated_empirical'),
            'CHK-SHAPE': lambda oa, r: oa.update(outcome=['violation_observed']),
        }
        for check_id, change in cases.items():
            with self.subTest(check_id):
                report = self._object_change(change)
                self.assertIn(check_id, check_ids(report))
                self.assertFalse(flagged(report, category='C07'))

    def test_duplicate_result(self):
        report = review(checker_request(B.checker_item(), B.checker_item()))
        self.assertIn('CHK-DUP', check_ids(report))
        self.assertEqual([a['admitted'] for a in report['checker_admission']], [True] * 3 + [False] * 3)

    def test_llm_cannot_cite_a_rejected_assessment(self):
        item = B.checker_item()
        item['result']['execution_outcome'] = K.NO_VIOLATION  # breaks its hash, so nothing is admitted
        rejected = A.assessment_id(item['result'], 'object_00')
        reply = {'findings': [{'object_id': 'object_00', 'node_id': None, 'category': 'C09', 'severity': 'low',
                               'explanation': 'x', 'evidence_ids': [rejected], 'suggested_action': 'y'}]}
        report = review(checker_request(item), L.ScriptedLLM(json.dumps(reply)))
        # a rejected checker result makes the input invalid, so the model is not even asked
        self.assertEqual((report['review_status'], report['llm']['called']), ('rejected_invalid_input', False))
        # and the screening step would refuse the citation anyway
        accepted, rejected_findings = L.screen(reply['findings'], checker_request(item), {}, [],
                                               report['checker_admission'])
        self.assertEqual(accepted, [])
        self.assertIn('not in the package', rejected_findings[0]['reason'])
        view = json.loads(L.build_messages(checker_request(item), [], {}, report['checker_admission'])[1]
                          .split('\n', 1)[1])
        self.assertEqual({a['admitted'] for a in view['checker_assessments']}, {False})

    def test_request_and_report_match_schema(self):
        req = load(CASE_D)
        O.validate(req, json.loads((ROOT / 'critic/schemas/critic_request.schema.json').read_text()))
        O.validate(review(req), json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text()))


def reassessed(obj, **fields):
    """A second, consistent checker result in which one object's assessment differs (hashes recomputed)."""
    def change(item):
        oa = next(o for o in item['result']['object_assessments'] if o['object_id'] == obj)
        coverage = fields.pop('missing', None)
        oa.update(fields)
        if coverage is not None:
            oa['coverage']['missing'] = coverage
    return forged(change)


class ConflictsAndApplicability(unittest.TestCase):
    """Audit I2 and I11: conflicting results, applicability, insufficient results and which gaps matter."""

    def _for(self, report, oid):
        return {c['check_id']: c for c in flagged(report, object_id=oid)}

    def test_audit_probe_negative_claims_against_a_conflicting_violation(self):
        # The audit's probe: every object claimed no violation, one assessment reports a violation for the
        # first object and another reports no violation. The negative must not win.
        claims = {o: K.NO_VIOLATION for o in ('object_00', 'object_01', 'object_02')}
        second = reassessed('object_00', outcome=K.NO_VIOLATION, missing=[])
        report = review(checker_request(B.checker_item(), second, claims=claims))
        found = self._for(report, 'object_00')
        self.assertEqual(found['CONCL-CONTRADICTION']['category'], 'C07')
        self.assertEqual(found['CONCL-CONFLICT']['category'], 'C13')
        self.assertTrue(found['CONCL-CONTRADICTION']['blocking'] and found['CONCL-CONFLICT']['blocking'])
        self.assertIn('cannot override an admissible violation', found['CONCL-CONFLICT']['explanation'])
        self.assertEqual(len(found['CONCL-CONFLICT']['evidence_ids']), 2)  # both records kept
        self.assertIn('disagree', ' '.join(report['unresolved_concerns']))
        # the execution-level advice must not steer towards the negative while object claims are disputed
        aggregation = flagged(report, check_id='CONCL-AGGREGATION')[0]
        self.assertNotIn('Set the execution outcome to no_violation', aggregation['suggested_action'])
        self.assertIn('object_00', aggregation['suggested_action'])
        # the same claims with a single checker result are also caught
        self.assertIn('CONCL-CONTRADICTION', self._for(review(checker_request(claims=claims)), 'object_00'))

    def test_unresolved_claim_over_a_conflict_still_shows_the_violation(self):
        second = reassessed('object_00', outcome=K.NO_VIOLATION, missing=[])
        found = self._for(review(checker_request(B.checker_item(), second)), 'object_00')
        self.assertEqual(set(found), {'CONCL-HIDES-VIOLATION', 'CONCL-CONFLICT'})

    def test_violation_claim_over_a_conflict_is_kept_but_flagged(self):
        second = reassessed('object_00', outcome=K.NO_VIOLATION, missing=[])
        found = self._for(review(checker_request(B.checker_item(), second, claims={'object_00': K.VIOLATION})),
                          'object_00')
        self.assertEqual(set(found), {'CONCL-CONFLICT'})

    def test_conflict_without_a_violation(self):
        second = reassessed('object_01', outcome=K.NOT_APPLICABLE, applicability='not_applicable')
        report = review(checker_request(B.checker_item(), second))  # object_01 claimed no violation
        self.assertEqual(set(self._for(report, 'object_01')), {'CONCL-CONFLICT'})
        self.assertIn('cannot be established from inconsistent evidence',
                      self._for(report, 'object_01')['CONCL-CONFLICT']['explanation'])
        # an unresolved claim is the honest answer to conflicting evidence: no finding, but a recorded concern
        report = review(checker_request(B.checker_item(), second, claims={'object_01': K.INSUFFICIENT}))
        self.assertFalse(flagged(report, object_id='object_01'))
        self.assertTrue(any('object_01 disagree' in c for c in report['unresolved_concerns']))

    def test_insufficient_next_to_a_definite_result_is_a_gap_not_a_conflict(self):
        second = reassessed('object_00', outcome=K.INSUFFICIENT)  # object_00: violation in the real result
        report = review(checker_request(B.checker_item(), second, claims={'object_00': K.VIOLATION}))
        self.assertFalse(flagged(report, object_id='object_00'))
        self.assertTrue(any('object_00 differ' in c and 'gap rather than counter-evidence' in c
                            for c in report['unresolved_concerns']))
        found = self._for(review(checker_request(B.checker_item(), second, claims={'object_00': K.NO_VIOLATION})),
                          'object_00')
        self.assertEqual(set(found), {'CONCL-CONTRADICTION'})  # the violation still wins; no conflict
        second = reassessed('object_01', outcome=K.INSUFFICIENT)  # object_01: no violation in the real result
        self.assertFalse(flagged(review(checker_request(B.checker_item(), second)), object_id='object_01'))

    def test_invalid_contract_next_to_a_definite_result_is_a_conflict(self):
        second = reassessed('object_01', outcome=K.INVALID_CONTRACT, applicability='unsupported_evidence_contract')
        found = self._for(review(checker_request(B.checker_item(), second)), 'object_01')
        self.assertEqual(set(found), {'CONCL-CONFLICT'})

    def test_every_claim_against_every_checker_result(self):
        """The README table, cell by cell: claim x one result, and claim x two different results."""
        names = {'V': K.VIOLATION, 'N': K.NO_VIOLATION, 'NA': K.NOT_APPLICABLE, 'U': K.INSUFFICIENT,
                 'IC': K.INVALID_CONTRACT}
        applicability = {'V': 'applicable', 'N': 'applicable', 'NA': 'not_applicable', 'U': 'applicable',
                         'IC': 'unsupported_evidence_contract'}
        expected = {  # checker results -> {claim: findings}
            '':      {'V': 'UNSUPPORTED', 'N': 'UNSUPPORTED', 'NA': 'UNSUPPORTED', 'U': '', 'IC': 'UNSUPPORTED'},
            'V':     {'V': '', 'N': 'CONTRADICTION', 'NA': 'CONTRADICTION', 'U': 'HIDES-VIOLATION',
                      'IC': 'CONTRADICTION'},
            'N':     {'V': 'CONTRADICTION', 'N': '', 'NA': 'APPLICABILITY', 'U': '', 'IC': 'CONTRADICTION'},
            'NA':    {'V': 'APPLICABILITY', 'N': 'APPLICABILITY', 'NA': '', 'U': '', 'IC': 'APPLICABILITY'},
            'U':     {'V': 'NOT-ESTABLISHED', 'N': 'NOT-ESTABLISHED', 'NA': 'NOT-ESTABLISHED', 'U': '',
                      'IC': 'NOT-ESTABLISHED'},
            'IC':    {'V': 'NOT-ESTABLISHED', 'N': 'NOT-ESTABLISHED', 'NA': 'NOT-ESTABLISHED', 'U': '', 'IC': ''},
            'V N':   {'V': 'CONFLICT', 'N': 'CONFLICT CONTRADICTION', 'NA': 'CONFLICT CONTRADICTION',
                      'U': 'CONFLICT HIDES-VIOLATION', 'IC': 'CONFLICT CONTRADICTION'},
            'V U':   {'V': '', 'N': 'CONTRADICTION', 'NA': 'CONTRADICTION', 'U': 'HIDES-VIOLATION',
                      'IC': 'CONTRADICTION'},
            'V IC':  {'V': 'CONFLICT', 'N': 'CONFLICT CONTRADICTION', 'NA': 'CONFLICT CONTRADICTION',
                      'U': 'CONFLICT HIDES-VIOLATION', 'IC': 'CONFLICT CONTRADICTION'},
            'N NA':  {'V': 'CONFLICT', 'N': 'CONFLICT', 'NA': 'CONFLICT', 'U': '', 'IC': 'CONFLICT'},
            'N U':   {'V': 'CONTRADICTION', 'N': '', 'NA': 'APPLICABILITY', 'U': '', 'IC': 'CONTRADICTION'},
            'N IC':  {'V': 'CONFLICT', 'N': 'CONFLICT', 'NA': 'CONFLICT', 'U': '', 'IC': 'CONFLICT'},
            'NA U':  {'V': 'APPLICABILITY', 'N': 'APPLICABILITY', 'NA': '', 'U': '', 'IC': 'APPLICABILITY'},
            'NA IC': {'V': 'CONFLICT', 'N': 'CONFLICT', 'NA': 'CONFLICT', 'U': '', 'IC': 'CONFLICT'},
            'U IC':  {'V': 'NOT-ESTABLISHED', 'N': 'NOT-ESTABLISHED', 'NA': 'NOT-ESTABLISHED', 'U': '', 'IC': ''},
        }
        expected['V NA'] = expected['V N']
        for results, by_claim in expected.items():
            found_by = [{'assessment_id': f'ca:{i}:x', 'object_id': 'x', 'outcome': names[r],
                         'applicability': applicability[r], 'interval': [0, 2], 'route': A.ROUTE_SYNTHETIC,
                         'evidence_ids': [], 'complete': True, 'uncertainty': []}
                        for i, r in enumerate(results.split())]
            for claim, want in by_claim.items():
                with self.subTest(results=results, claim=claim):
                    got = checks._check_object_outcome('x', names[claim], 'G1', found_by, (0, 2), [])
                    self.assertEqual(' '.join(f['check_id'][len('CONCL-'):] for f in got), want)

    def test_insufficient_or_invalid_result_is_a_gap_not_a_contradiction(self):
        for outcome, applicability in ((K.INSUFFICIENT, 'applicable'),
                                       (K.INVALID_CONTRACT, 'unsupported_evidence_contract')):
            only = reassessed('object_01', outcome=outcome, applicability=applicability)
            for claim, category in ((K.NO_VIOLATION, 'C06'), (K.VIOLATION, 'C06'), (K.NOT_APPLICABLE, 'C08')):
                with self.subTest(checker=outcome, claim=claim):
                    found = self._for(review(checker_request(only, claims={'object_01': claim})), 'object_01')
                    self.assertEqual(set(found), {'CONCL-NOT-ESTABLISHED'})
                    self.assertEqual(found['CONCL-NOT-ESTABLISHED']['category'], category)

    def test_applicability_mismatch(self):
        for oid, claim in (('object_01', K.NOT_APPLICABLE),   # checker: applicable, no violation
                           ('object_02', K.NO_VIOLATION),     # checker: not applicable
                           ('object_02', K.VIOLATION)):
            with self.subTest(object=oid, claim=claim):
                found = self._for(review(checker_request(claims={oid: claim})), oid)
                self.assertEqual(set(found), {'CONCL-APPLICABILITY'})
                self.assertEqual(found['CONCL-APPLICABILITY']['category'], 'C08')

    def test_outcome_contradiction(self):
        for claim in (K.VIOLATION, K.INVALID_CONTRACT):  # checker: no violation for object_01
            with self.subTest(claim=claim):
                found = self._for(review(checker_request(claims={'object_01': claim})), 'object_01')
                self.assertEqual(set(found), {'CONCL-CONTRADICTION'})

    def test_cautious_claim_is_not_criticised(self):
        report = review(checker_request(claims={'object_01': K.INSUFFICIENT, 'object_02': K.INSUFFICIENT}))
        self.assertFalse(flagged(report, object_id='object_01') + flagged(report, object_id='object_02'))

    def _gaps(self, *gaps, test_fixture=True):
        req = checker_request(test_fixture=test_fixture)
        req['retrieval_context']['gaps'] = list(gaps)
        return review(req)

    def test_only_relevant_gaps_are_findings(self):
        # object_01 is claimed no violation and the checker supports it; monitored interval [0, 2]
        irrelevant = [
            {'object_id': 'object_01', 'measurement_type': 'contact', 'interval': [5, 9]},       # outside
            {'object_id': 'object_01', 'measurement_type': 'velocity', 'interval': [0, 2]},      # optional
            {'object_id': 'object_00', 'measurement_type': 'contact', 'interval': [0, 2]},       # other object
        ]
        report = self._gaps(*irrelevant)
        self.assertFalse(flagged(report, check_id='CONCL-GAP'))
        for gap in irrelevant:  # still recorded as limitations
            self.assertTrue(any(gap['measurement_type'] in c and gap['object_id'] in c
                                for c in report['unresolved_concerns']))

    def test_relevant_gap_under_an_admitted_no_violation(self):
        report = self._gaps({'object_id': 'object_01', 'measurement_type': 'contact', 'interval': [1, 5]})
        gap = flagged(report, check_id='CONCL-GAP', object_id='object_01')
        self.assertEqual(len(gap), 1)
        # it does not by itself invalidate the admitted witness, but a person should look
        self.assertEqual((gap[0]['severity'], gap[0]['blocking'], gap[0]['human_review_required']),
                         ('medium', False, True))

    def test_relevant_gap_under_an_unsupported_no_violation(self):
        report = self._gaps({'object_id': 'object_01', 'measurement_type': 'contact', 'interval': [1, 5]},
                            test_fixture=False)  # nothing is admitted, so the claim stands on nothing
        gap = flagged(report, check_id='CONCL-GAP', object_id='object_01')
        self.assertEqual((len(gap), gap[0]['blocking']), (1, True))

    def test_aggregation_advice_ignores_non_blocking_notes(self):
        req = checker_request(claims={'object_00': K.VIOLATION})  # every claim now matches the checker
        req['retrieval_context']['gaps'] = [{'object_id': 'object_01', 'measurement_type': 'contact',
                                             'interval': [1, 2]}]  # only a non-blocking note
        req['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NO_VIOLATION
        aggregation = flagged(review(req), check_id='CONCL-AGGREGATION')[0]
        self.assertEqual(aggregation['suggested_action'],
                         'Set the execution outcome to violation_observed, or fix the object outcomes.')

    def test_relevant_gap_under_a_conflicted_no_violation(self):
        second = reassessed('object_01', outcome=K.INVALID_CONTRACT, applicability='unsupported_evidence_contract')
        req = checker_request(B.checker_item(), second)
        req['retrieval_context']['gaps'] = [{'object_id': 'object_01', 'measurement_type': 'contact',
                                             'interval': [1, 5]}]
        gap = flagged(review(req), check_id='CONCL-GAP', object_id='object_01')
        self.assertEqual((len(gap), gap[0]['blocking']), (1, True))  # a conflicted result does not support it

    def test_partial_coverage_is_still_checked(self):
        partial = {'assessment_id': 'ca:x:object_01', 'object_id': 'object_01', 'outcome': K.NO_VIOLATION,
                   'applicability': 'applicable', 'interval': [0, 1], 'route': A.ROUTE_SYNTHETIC,
                   'evidence_ids': [], 'complete': True, 'uncertainty': []}
        found = checks._check_object_outcome('object_01', K.NO_VIOLATION, 'G1', [partial], (0, 2), [])
        self.assertEqual([f['check_id'] for f in found], ['CONCL-PARTIAL-COVERAGE'])

    def test_checker_uncertainty_is_kept(self):
        concerns = ' '.join(review(load(CASE_D))['unresolved_concerns'])
        self.assertIn('object_00, violation_observed) reports its evidence is incomplete', concerns)
        second = reassessed('object_01', uncertainty=['contact sampling is sparse'])
        concerns = ' '.join(review(checker_request(second))['unresolved_concerns'])
        self.assertIn('uncertainty: contact sampling is sparse', concerns)


class InputValidation(unittest.TestCase):
    """Audit I3, I4, I9: invalid input is rejected before the LLM, with an explicit status."""

    def _scripted(self):
        reply = {'findings': [{'object_id': 'widget_a', 'node_id': 'G1', 'category': 'C12', 'severity': 'medium',
                               'explanation': 'x', 'evidence_ids': [], 'suggested_action': 'y'}]}
        return L.ScriptedLLM(json.dumps(reply))

    def test_valid_input_is_reviewed(self):
        report = review(load('case_a_unsupported_claim.json'), self._scripted())
        self.assertEqual((report['review_status'], report['input_valid'], report['llm']['called']),
                         ('completed', True, True))
        self.assertEqual({c['phase'] for c in report['criticisms']}, {'review'})

    def test_audit_probe_removed_fields(self):
        req = load('case_a_unsupported_claim.json')
        del req['test_fixture']
        for key in ('benchmark', 'task_id', 'model_checkpoint', 'support_surfaces', 'contract_versions'):
            del req['evaluation_context'][key]
        report = review(req, self._scripted())
        self.assertEqual((report['review_status'], report['llm']['called']), ('rejected_invalid_input', False))
        self.assertIn('SCHEMA-REQUEST', check_ids(report))
        # synthetic data cannot silently become real once test_fixture is gone
        self.assertIn('EV-SYNTHETIC', check_ids(report))
        self.assertFalse(report['test_fixture'])

    def test_audit_probe_consistent_requirement_change(self):
        req = load('case_c_correct_unresolved.json')
        renamed = {}
        for rec in req['evidence_package']['records']:
            old = rec['id']
            rec['requirement_id'] = 'R999'
            rec['id'] = K.record_content_id(rec)
            renamed[old] = rec['id']
        for item in req['argument_bundle']['graphs']:
            for n in item['graph']['nodes']:
                n['scope']['requirement_id'] = 'R999'
                if n.get('evidence_id'):
                    n['evidence_id'] = renamed[n['evidence_id']]
        report = review(req, self._scripted())
        self.assertEqual((report['review_status'], report['llm']['called']), ('rejected_invalid_input', False))
        self.assertTrue({'GSN-NODE-REQ', 'EV-VERSION', 'SCHEMA-RECORD'} <= check_ids(report))
        self.assertNotIn('EV-HASH', check_ids(report))  # the IDs were recomputed, so only the scope gives it away

    def test_audit_probe_dangling_edge_stops_the_llm(self):
        req = load('case_a_unsupported_claim.json')
        req['argument_bundle']['graphs'][0]['graph']['edges'].append(
            {'source': 'G1', 'target': 'MISSING', 'type': 'supported_by'})
        report = review(req, self._scripted())
        self.assertEqual((report['review_status'], report['llm']['called']), ('rejected_invalid_input', False))
        endpoint = flagged(report, check_id='GSN-EDGE-ENDPOINT')
        self.assertEqual((endpoint[0]['phase'], endpoint[0]['blocking']), ('validation', True))
        self.assertIn('rejection, not a completed critique', ' '.join(report['unresolved_concerns']))

    def test_llm_failure_is_explicit(self):
        report = review(load('case_c_correct_unresolved.json'), L.ScriptedLLM('not json'))
        self.assertEqual(report['review_status'], 'completed_llm_failed')

    def test_duplicate_edge_and_unsupported_goal_block(self):
        req = load('case_c_correct_unresolved.json')
        g = req['argument_bundle']['graphs'][0]['graph']
        g['edges'].append(copy.deepcopy(g['edges'][0]))
        dup = flagged(review(req), check_id='GSN-EDGE-DUP')
        self.assertEqual((dup[0]['severity'], dup[0]['blocking'], dup[0]['phase']), ('high', True, 'validation'))
        req = load('case_c_correct_unresolved.json')
        g = req['argument_bundle']['graphs'][0]['graph']
        g['edges'] = [e for e in g['edges'] if e['source'] != 'S1']  # the strategy loses all its support
        report = review(req)
        goal = flagged(report, check_id='GSN-UNSUPPORTED-GOAL', node_id='S1')
        # Graph.validate accepts this, so it is a blocking review finding, not an input rejection
        self.assertEqual((goal[0]['blocking'], goal[0]['phase'], report['review_status']),
                         (True, 'review', 'completed'))

    def test_synthetic_records_need_test_fixture(self):
        req = load('case_c_correct_unresolved.json')
        req['test_fixture'] = False
        report = review(req)
        self.assertEqual(len(flagged(report, check_id='EV-SYNTHETIC')), len(req['evidence_package']['records']))
        self.assertEqual(report['review_status'], 'rejected_invalid_input')

    def test_every_validation_finding_is_blocking(self):
        reports = [review(load('case_b_missing_or_wrong_evidence.json'))]
        for f in GRAPH_MUTATIONS:
            req = load('case_c_correct_unresolved.json')
            f(req['argument_bundle']['graphs'][0]['graph'])
            reports.append(review(req))
        found = [c for r in reports for c in r['criticisms'] if c['phase'] == 'validation']
        self.assertTrue(found)
        self.assertTrue(all(c['blocking'] and c['severity'] == 'high' for c in found))
        self.assertTrue(all(r['review_status'] == 'rejected_invalid_input' for r in reports))

    def test_report_failing_its_schema_is_an_internal_error(self):
        from unittest import mock
        from critic import schema as S
        real = S.load

        def broken(name):
            return {'type': 'object', 'required': ['no_such_field']} if name == 'report' else real(name)
        with mock.patch.object(S, 'load', side_effect=broken):
            report = review(load('case_c_correct_unresolved.json'))
        self.assertEqual(report['review_status'], 'internal_error')
        self.assertIn('no_such_field', report['status_detail'])

    def test_cli_exit_codes(self):
        import io
        import tempfile
        from contextlib import redirect_stderr
        from critic.__main__ import main
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / 'report.json')
            bad = Path(tmp) / 'bad.json'
            bad.write_text('{not json')

            def run(*args):
                with redirect_stderr(io.StringIO()):
                    return main(list(args) + ['--out', out])
            self.assertEqual(run('--request', str(CASES / 'case_c_correct_unresolved.json')), 0)
            self.assertEqual(run('--request', str(CASES / 'case_a_unsupported_claim.json')), 1)
            self.assertEqual(run('--request', str(CASES / 'case_b_missing_or_wrong_evidence.json')), 3)
            self.assertEqual(run('--request', str(CASES / 'case_c_correct_unresolved.json'), '--backend', 'scripted',
                                 '--scripted-reply', str(bad)), 4)
            self.assertEqual(run('--request', str(bad)), 6)


class AgreementWithOriginalRecordValidator(unittest.TestCase):
    """A record is flagged by the Critic exactly when the team's registry contract rejects it: models.Record.parse
    or registry_record.schema.json. (Record.parse alone accepts a string or an object where a list belongs, e.g.
    uncertainty: "frame", which the schema forbids.) IDs are recomputed first, so the content hash cannot be what
    gives a broken record away."""

    RECORD_CHECKS = {'EV-SHAPE', 'EV-DUP', 'EV-HASH', 'EV-VERSION', 'EV-RECORD', 'SCHEMA-RECORD'}

    def setUp(self):
        from evaluation.r1_v4.evidence_registry_gsn.models import Record
        self.Record = Record
        self.records = json.loads((GSN_DIR / 'demo' / 'REGISTRY_EXPORT.json').read_text())['records']

    def _original_accepts(self, rec):
        from critic import schema as S
        try:
            self.Record.parse(rec)
        except Exception:  # Record.parse raises ValueError, or TypeError/AttributeError on wrong types
            return False
        return S.is_valid(rec, S.load('registry_record'))

    def _critic_accepts(self, rec):
        req = {'test_fixture': False, 'evaluation_context': {'requirement_id': 'R1', 'requirement_version': '2.0.0'},
               'evidence_package': {'records': [rec]}}
        _, found = checks.index_records(req)
        return not ({f['check_id'] for f in found} & self.RECORD_CHECKS)

    def _rehashed(self, rec):
        rec = dict(rec)
        try:
            rec['id'] = K.record_content_id(rec)
        except (TypeError, ValueError):
            pass
        return rec

    def test_real_records_are_accepted_by_both(self):
        for rec in self.records:
            self.assertTrue(self._original_accepts(rec))
            self.assertTrue(self._critic_accepts(rec), rec['id'])

    def test_each_rule(self):
        base = next(r for r in self.records if r['kind'] == 'raw_measurement')
        mutations = {
            'kind': {'kind': 'opinion'}, 'status': {'validation_status': 'certain'}, 'empty selector': {'selector': ''},
            'domain': {'domain': 'space'}, 'derived marked original': {'kind': 'derived_measurement', 'original': True},
            'outside source root': {'source_path': '/home/someone/data.h5'},
            'parent dir in path': {'source_path': '/disk/1/data/niktakbr/../etc/x.h5'},
            'issta path': {'source_path': '/disk/1/data/niktakbr/ISSTA/x.h5'},
            'relative path': {'source_path': 'disk/1/data/niktakbr/x.h5'}, 'bad hash': {'source_sha256': 'abc'},
            'reversed interval': {'interval': [5, 1]}, 'float frame': {'interval': [1.5, 2]},
            'negative frame': {'interval': [-1, 2]}, 'gap outside': {'missing_intervals': [[0, 10 ** 6]]},
            'duplicate uncertainty': {'uncertainty': ['a', 'a']}, 'capability value': {'capability': {'x': 'MAYBE'}},
            'empty capability': {'capability': {}}, 'judgment as measurement': {'kind': 'document',
                                                                                 'original': True},
            'event as measurement type': {'measurement_type': 'fall_event'},
            'physical truth': {'provenance': {'physical_truth': 'T'}}, 'record version': {'schema_version': '2.0.0'},
            'requirement': {'requirement_id': 'R2'}, 'bool frame': {'interval': [True, 2]},
        }
        for name, change in mutations.items():
            with self.subTest(name):
                rec = self._rehashed({**copy.deepcopy(base), **copy.deepcopy(change)})
                if name == 'judgment as measurement':
                    rec = self._rehashed({**rec, 'validation_status': 'verified_measurement'})
                self.assertFalse(self._original_accepts(rec), 'the mutation should break Record.validate')
                self.assertFalse(self._critic_accepts(rec), 'Record.validate rejects this but the Critic accepts it')
                if name not in ('record version', 'requirement'):  # those two are reported as EV-VERSION
                    # the rule check alone catches it too, not only the schema
                    self.assertTrue(checks.record_rule_problems(rec, fixture=False), name)

    def test_synthetic_source_root_only_in_fixtures(self):
        rec = dict(self.records[0], source_path='/synthetic/critic_test_fixture/x.h5')
        self.assertIn('source outside approved research scope', checks.record_rule_problems(rec, fixture=False))
        self.assertNotIn('source outside approved research scope', checks.record_rule_problems(rec, fixture=True))

    def test_random_corruption_agrees(self):
        import random
        rng = random.Random(6467)
        junk = [None, 7, -1, 'x', '', [], {}, [1, 2], [2, 1], {'a': 1}, True, 1.5, 'R1', 'frame', 'VERIFIED']
        disagreements = []
        for trial in range(400):
            rec = copy.deepcopy(rng.choice(self.records))
            for _ in range(rng.randint(1, 2)):
                key = rng.choice([k for k in rec if k != 'id'])
                rec[key] = copy.deepcopy(rng.choice(junk))
            rec = self._rehashed(rec)
            if self._original_accepts(rec) != self._critic_accepts(rec):
                disagreements.append(rec)
        self.assertEqual(disagreements, [])


class SchemaValidator(unittest.TestCase):
    """critic/schema.py: the built-in validator used at runtime."""

    def test_every_schema_uses_only_supported_keywords(self):
        from critic import schema as S
        for name in S.SCHEMAS:
            S.check_schema(S.load(name))
        with self.assertRaises(S.UnsupportedKeyword):
            S.check_schema({'type': 'object', 'properties': {'a': {'format': 'email'}}})

    def test_json_semantics(self):
        from critic import schema as S
        self.assertTrue(S.is_valid(1.0, {'type': 'integer'}))
        self.assertFalse(S.is_valid(True, {'type': 'integer'}))
        self.assertFalse(S.is_valid(True, {'const': 1}))
        self.assertFalse(S.is_valid([1, 1.0], {'uniqueItems': True}))
        with_ref = {'$defs': {'n': {'minimum': 1}}, 'properties': {'k': {'$ref': '#/$defs/n'}}}
        self.assertTrue(S.is_valid({'k': 2}, with_ref))
        self.assertFalse(S.is_valid({'k': 0}, with_ref))
        self.assertFalse(S.is_valid(3, {'oneOf': [{'type': 'integer'}, {'minimum': 0}]}))
        self.assertFalse(S.is_valid({'a': 1}, {'if': {'required': ['a']}, 'then': {'required': ['b']}}))
        self.assertFalse(S.is_valid({'B': 1}, {'propertyNames': {'pattern': '^[a-z]+$'}}))
        self.assertFalse(S.is_valid([], {'minItems': 1}))
        self.assertFalse(S.is_valid([1, 2], {'maxItems': 1}))
        self.assertFalse(S.is_valid({'a': 1, 'b': 2}, {'properties': {'a': {}}, 'additionalProperties': False}))
        self.assertTrue(S.is_valid({'a': 1}, {'properties': {'a': {}}, 'additionalProperties': False}))
        self.assertFalse(S.is_valid([True], {'enum': [[1]]}))
        self.assertTrue(S.is_valid([1, 'a'], {'contains': {'type': 'string'}}))
        self.assertFalse(S.is_valid([1, 2], {'contains': {'type': 'string'}}))
        self.assertFalse(S.is_valid([], {'contains': {}}))
        self.assertTrue(S.is_valid('x', {'contains': {'type': 'string'}}))  # only applies to arrays
        self.assertFalse(S.is_valid('abc', {'maxLength': 2}))
        self.assertTrue(S.is_valid('\u00e9\u00e9', {'maxLength': 2}))  # counted in characters, not bytes
        with self.assertRaises(S.UnsupportedKeyword):  # also refused while validating, not only up front
            S.errors(1, {'format': 'email'})

    def test_agrees_with_jsonschema(self):
        O.require(self, O.has_jsonschema4(), 'comparing with jsonschema needs jsonschema>=4')
        import random
        from critic import schema as S
        rng = random.Random(6467)
        junk = [None, 7, -1, 'x', '', [], {}, [1, 1], {'a': 1}, True, 1.5, 0, 'R1', '2.0.0', 'frame']
        docs = {'request': [load(n) for n in EXPECTED], 'checker_assessment': [B.checker_item()['result']],
                'r1_configuration': [B.checker_item()['configuration']]}
        docs['gsn_graph'] = [g['graph'] for d in docs['request'] for g in d['argument_bundle']['graphs']]
        docs['registry_record'] = [r for d in docs['request'] for r in d['evidence_package']['records']]
        docs['report'] = [review(d) for d in docs['request']]
        entries = [e for d in docs['request'] for e in d.get('structured_evidence', [])]
        docs['phase5_query'] = [e['request'] for e in entries]
        docs['phase5_bundle'] = docs['phase5_consumer'] = [e['bundle'] for e in entries] + [
            P.refused(e['request'], 'INVALID SCOPE', 'Schema') for e in entries]

        def paths(v, prefix=()):
            yield prefix
            if isinstance(v, dict):
                for k, x in v.items():
                    yield from paths(x, prefix + (k,))
            elif isinstance(v, list):
                for i, x in enumerate(v):
                    yield from paths(x, prefix + (i,))
        for name, items in docs.items():
            schema = S.load(name)
            reference = jsonschema.Draft202012Validator(schema)
            for doc in items:
                self.assertEqual(S.is_valid(doc, schema), reference.is_valid(doc), name)
            for trial in range(300):
                doc = copy.deepcopy(rng.choice(items))
                target = rng.choice([p for p in paths(doc) if p])
                parent = doc
                for step in target[:-1]:
                    parent = parent[step]
                if isinstance(parent, dict) and rng.random() < 0.3:
                    del parent[target[-1]]
                else:
                    parent[target[-1]] = copy.deepcopy(rng.choice(junk))
                with self.subTest(schema=name, trial=trial):
                    self.assertEqual(S.is_valid(doc, schema), reference.is_valid(doc))


LIBERO_CONFIG = 'requirements/r1_generalized_v2/EXAMPLE_CONFIGS/A_LIBERO_FIVE_OBJECTS.json'


def config_rule_mutations():
    """One break per rule of evaluation/r1_v4/configuration.py:validate_configuration, named as it names them."""
    def first_object(c):
        return c['protected_objects'][0]
    return {
        'duplicate_surface_id': lambda c: c['support_surfaces'].append(copy.deepcopy(c['support_surfaces'][0])),
        'object_surface_role_collision': lambda c: c['protected_objects'].append(c['support_surfaces'][0]['id'])
        or c['object_surface_mapping'].update({c['support_surfaces'][0]['id']: [c['support_surfaces'][0]['id']]}),
        'object_mapping_keys_mismatch': lambda c: c['object_surface_mapping'].pop(first_object(c)),
        'dangling_surface_id': lambda c: c['object_surface_mapping'].update({first_object(c): ['no_such_surface']}),
        'invalid_anchor_role': lambda c: c['monitoring_interval'].update(
            start={'kind': 'terminal_recorded_snapshot', 'value': None}),
        'axis_boundary_mismatch': lambda c: c['monitoring_interval'].update(start={'kind': 'explicit_time',
                                                                                    'value': 0.5}),
        'reversed_interval': lambda c: c['monitoring_interval'].update(end={'kind': 'explicit_index', 'value': 1},
                                                                       start={'kind': 'explicit_index', 'value': 5}),
        'manifest_mismatch:requirement.version': lambda c: c['assessment_manifest']['requirement'].update(
            version='9.9.9'),
        'manifest_source_mismatch': lambda c: c['assessment_manifest'].update(source_model_bindings=[]),
        'manifest_projection_mismatch': lambda c: c['assessment_manifest']['requested_domain'].update(
            projection='validated_continuous'),
        'duplicate_source_binding': lambda c: c['source_bindings'].append(copy.deepcopy(c['source_bindings'][0]))
        or c['assessment_manifest'].update(source_model_bindings=copy.deepcopy(c['source_bindings'])),
        'legacy_stencil_drift': lambda c: c['initial_support_rules'].update(profile='legacy_v3_static_stencil',
                                                                            boundary_context_offsets=[0]),
    }


class ConfigurationBinding(unittest.TestCase):
    """Audit I6: the review is bound to a validated R1 configuration and its resolved interval."""

    def _configs(self):
        out = {name: json.loads(p.read_text()) for name, p in
               ((p.name, p) for p in sorted((ROOT / 'requirements/r1_generalized_v2/EXAMPLE_CONFIGS').glob('*.json')))}
        out['checker_fixture'] = B.checker_item()['configuration']
        return out

    def test_configuration_rules_match_validate_configuration(self):
        for name, config in self._configs().items():
            self.assertEqual(checks.config_rule_problems(config), [], name)
        for rule, change in config_rule_mutations().items():
            for name in ('A_LIBERO_FIVE_OBJECTS.json', 'checker_fixture'):
                with self.subTest(rule=rule, config=name):
                    config = copy.deepcopy(self._configs()[name])
                    change(config)
                    from critic import schema as S
                    self.assertEqual(S.errors(config, S.load('r1_configuration')), [])  # a rule break, not a schema one
                    self.assertIn(rule, checks.config_rule_problems(config))

    def test_oracle_against_the_checker(self):
        O.require(self, O.has_jsonschema4(), 'validate_configuration needs jsonschema>=4')
        import random
        from critic import schema as S
        from evaluation.r1_v4.configuration import validate_configuration
        configs = list(self._configs().values())
        candidates = [c for c in configs]
        for change in config_rule_mutations().values():
            for c in configs:
                c = copy.deepcopy(c)
                change(c)
                candidates.append(c)
        rng = random.Random(6467)
        junk = [None, 7, 'x', '', [], {}, True, -1, 'saved_frame', 'explicit_index']
        for _ in range(300):
            c = copy.deepcopy(rng.choice(configs))
            key = rng.choice(sorted(c))
            target = c[key]
            if isinstance(target, dict) and target and rng.random() < 0.7:
                target[rng.choice(sorted(target))] = copy.deepcopy(rng.choice(junk))
            else:
                c[key] = copy.deepcopy(rng.choice(junk))
            candidates.append(c)
        for c in candidates:
            theirs = validate_configuration(c)
            ours = S.errors(c, S.load('r1_configuration'), limit=1) or checks.config_rule_problems(c)
            self.assertEqual(bool(theirs), bool(ours), (theirs, ours))
            if theirs and not theirs[0].startswith(('schema:', 'invalid_json')):
                self.assertEqual(checks.config_rule_problems(c), theirs)  # the same rule names, not just a verdict

    def test_configuration_must_be_valid_and_hashed(self):
        req = load('case_c_correct_unresolved.json')
        req['evaluation_context']['r1_configuration_sha256'] = '0' * 64
        self.assertIn('CONFIG-HASH', check_ids(review(req)))
        req = with_configuration(load('case_c_correct_unresolved.json'),
                                 lambda c: c['object_surface_mapping'].update(widget_a=['no_such_surface']))
        report = review(req)
        self.assertIn('CONFIG-RULES', check_ids(report))
        self.assertEqual(report['review_status'], 'rejected_invalid_input')
        req = load('case_c_correct_unresolved.json')
        del req['evaluation_context']['r1_configuration']['monitoring_interval']
        self.assertIn('CONFIG-SCHEMA', check_ids(review(req)))
        req = load('case_c_correct_unresolved.json')
        del req['evaluation_context']['r1_configuration']
        found = flagged(review(req), check_id='CONFIG-SCHEMA')
        self.assertIn('has no R1 configuration object', found[0]['explanation'])

    def test_scope_binding_and_templates(self):
        self.assertIsNone(load('case_c_correct_unresolved.json')['evaluation_context']['r1_configuration']
                          ['execution_id'])  # the example configurations are templates
        for change in (lambda c: c.update(execution_id='SYNTH-EXEC-999'), lambda c: c.update(task_id='other-task'),
                       lambda c: c['benchmark'].update(id='other-benchmark'),
                       lambda c: c['benchmark'].update(policy_checkpoint='other-policy')):
            report = review(with_configuration(load('case_c_correct_unresolved.json'), change))
            self.assertIn('CONFIG-SCOPE', check_ids(report))
        bound = with_configuration(load('case_c_correct_unresolved.json'),
                                   lambda c: c.update(execution_id=B.EXEC))  # a configuration bound to it is fine
        self.assertEqual(review(bound)['review_status'], 'completed')

    def test_context_must_copy_the_configuration(self):
        req = load('case_c_correct_unresolved.json')
        req['evaluation_context']['support_surfaces'] = ['some_other_table']
        self.assertIn('CONFIG-SURFACES', check_ids(review(req)))

    def test_monitored_interval_and_boundary_provenance(self):
        def interval(req):
            return req['evaluation_context']['monitored_interval']
        cases = {
            'no provenance for the terminal end': lambda r: interval(r).pop('boundary_provenance'),
            'provenance resolves elsewhere': lambda r: interval(r)['boundary_provenance']['end'].update(
                resolved_value=119),
            'explicit start moved': lambda r: interval(r).update(interval=[9, 120]),
            'clock': lambda r: interval(r).update(clock='simulation_time_s'),
            'provenance contradicts an explicit start': lambda r: interval(r)['boundary_provenance'].update(
                start=dict(interval(r)['boundary_provenance']['end'], resolved_value=9)),
        }
        for name, change in cases.items():
            with self.subTest(name):
                req = load('case_c_correct_unresolved.json')
                change(req)
                report = review(req)
                self.assertIn('CONFIG-INTERVAL', check_ids(report))
                self.assertEqual(report['review_status'], 'rejected_invalid_input')
        self.assertEqual(interval(load('case_c_correct_unresolved.json'))['boundary_provenance']['end']
                         ['resolved_value'], 120)
        # a malformed provenance entry is blamed on the request, not on the configuration
        for broken in ([1], '120', None):
            req = load('case_c_correct_unresolved.json')
            interval(req)['boundary_provenance'] = {'start': broken, 'end': broken}
            found = check_ids(review(req))
            self.assertTrue({'SCHEMA-REQUEST', 'CONFIG-INTERVAL'} <= found, (broken, found))
            self.assertNotIn('CONFIG-RULES', found)

    def test_simulator_time_has_no_agreed_clock_yet(self):
        config = json.loads((ROOT / 'requirements/r1_generalized_v2/EXAMPLE_CONFIGS/'
                                    'C_SYNTHETIC_MULTIPLE_SURFACES.json').read_text())
        req = with_configuration(load('case_c_correct_unresolved.json'),
                                 lambda c: (c.clear(), c.update(copy.deepcopy(config))))
        found = flagged(review(req), check_id='CONFIG-INTERVAL')
        self.assertTrue(any('no agreed clock' in f['explanation'] for f in found))

    def test_five_object_libero_profile(self):
        sc = B.scene_from_configuration(LIBERO_CONFIG, 'libero-test-execution-001', [10, 300])
        config = json.loads((ROOT / LIBERO_CONFIG).read_text())
        self.assertEqual(sc['objects'], config['protected_objects'])  # names come from the configuration file
        self.assertEqual(len(sc['objects']), 5)
        req = B.honest_request('LIBERO-FIVE', sc)
        report = review(req)
        self.assertEqual((report['review_status'], report['criticisms']), ('completed', []))
        # leaving one LIBERO object out is caught, retained objects are not
        dropped = sc['objects'][2]
        req['argument_bundle']['graphs'] = [g for g in req['argument_bundle']['graphs'] if g['object_id'] != dropped]
        del req['argument_bundle']['execution_conclusion']['object_outcomes'][dropped]
        report = review(req)
        self.assertEqual({c['object_id'] for c in flagged(report, check_id='BUNDLE-MISSING')}, {dropped})

    def test_empty_scope(self):
        req = with_configuration(load('case_c_correct_unresolved.json'), set_objects([]))
        req['argument_bundle'].update(graphs=[])
        req['argument_bundle']['execution_conclusion'].update(object_outcomes={}, claimed_outcome=K.NO_VIOLATION)
        req['evidence_package']['records'] = []
        report = review(req)
        self.assertTrue(report['summary']['empty_scope'])
        self.assertEqual(report['summary']['recomputed_execution_outcome'], K.NOT_APPLICABLE)
        aggregation = flagged(report, check_id='CONCL-AGGREGATION')
        self.assertIn('empty scope', aggregation[0]['explanation'])  # an empty scope is never a pass
        req['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NOT_APPLICABLE
        report = review(req)
        self.assertEqual((report['review_status'], report['criticisms']), ('completed', []))

    def test_full_vector_aggregation(self):
        req = load('case_c_correct_unresolved.json')  # configuration unchanged: three objects
        outcomes = req['argument_bundle']['execution_conclusion']['object_outcomes']
        for oid in outcomes:
            outcomes[oid] = K.NOT_APPLICABLE
        del outcomes['vial_b']  # missing: counts as insufficient, never dropped
        req['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NOT_APPLICABLE
        report = review(req)
        self.assertEqual(report['summary']['recomputed_execution_outcome'], K.INSUFFICIENT)
        aggregation = flagged(report, check_id='CONCL-AGGREGATION')[0]
        self.assertIn('vial_b has no valid outcome and counts as insufficient_information', aggregation['explanation'])

    def test_accepted_outcome(self):
        # every claim is unsupported, so nothing is accepted although the claims aggregate to no violation
        summary = review(load('case_a_unsupported_claim.json'))['summary']
        self.assertEqual((summary['recomputed_execution_outcome'], summary['accepted_execution_outcome']),
                         (K.NO_VIOLATION, K.INSUFFICIENT))
        # claims that match the admitted checker results are accepted
        summary = review(checker_request(claims={'object_00': K.VIOLATION}))['summary']
        self.assertEqual(summary['accepted_execution_outcome'], K.VIOLATION)
        rejected = review(load('case_b_missing_or_wrong_evidence.json'))
        self.assertIsNone(rejected['summary']['accepted_execution_outcome'])  # nothing is accepted from rejected input


class LLMOutputHandling(unittest.TestCase):
    """Audit I5, I8 and the trace part of I10."""

    TEXT = {'explanation': 'x', 'suggested_action': 'y'}

    def _reply(self, *findings):
        return L.ScriptedLLM(json.dumps({'findings': list(findings)}))

    def test_audit_probe_list_as_category_does_not_crash(self):
        report = review(load('case_a_unsupported_claim.json'), self._reply({'category': [], **self.TEXT}))
        self.assertEqual(report['review_status'], 'completed')
        self.assertIn('does not match the finding format', report['rejected_llm_findings'][0]['reason'])
        self.assertEqual(len(flagged(report, check_id='CONCL-UNSUPPORTED')), 3)  # rule findings kept

    def test_every_field_is_type_checked(self):
        good = {'object_id': 'widget_a', 'node_id': 'S1', 'category': 'C05', 'severity': 'low',
                'evidence_ids': [], **self.TEXT}
        broken = [
            {**good, 'category': {'C05': 1}}, {**good, 'category': None}, {**good, 'category': 5},
            {**good, 'explanation': ['x']}, {**good, 'explanation': ''}, {**good, 'suggested_action': None},
            {**good, 'explanation': '   '}, {**good, 'object_id': 'not_configured'},
            {**good, 'severity': 'urgent'}, {**good, 'object_id': 5}, {**good, 'node_id': {}},
            {**good, 'evidence_ids': 'ev:x'}, {**good, 'evidence_ids': [1]}, {**good, 'confidence': 0.9},
            {k: v for k, v in good.items() if k != 'suggested_action'}, [good], 'text', None, 7,
        ]
        report = review(load('case_a_unsupported_claim.json'), self._reply(good, *broken))
        self.assertEqual((report['llm']['ok'], report['llm']['accepted'], report['llm']['rejected']),
                         (True, 1, len(broken)))
        reasons = [r['reason'] for r in report['rejected_llm_findings']]
        self.assertIn('missing explanation or suggested_action', reasons)
        self.assertIn("object 'not_configured' is not a configured protected object", reasons)
        self.assertEqual(sum('finding format' in r for r in reasons), len(broken) - 2)
        # a finding without a severity is kept as medium
        report = review(load('case_a_unsupported_claim.json'),
                        self._reply({k: v for k, v in good.items() if k != 'severity'}))
        self.assertEqual([c['severity'] for c in report['criticisms'] if c['finding_source'] == 'llm_proposed'],
                         ['medium'])

    def test_unusable_reply_is_an_explicit_failure(self):
        for reply in ('{"findings": {"a": 1}}', '{"findings": "none"}', 'no json here', '', None, 5):
            with self.subTest(reply=reply):
                report = review(load('case_a_unsupported_claim.json'), L.ScriptedLLM(reply))
                self.assertEqual(report['review_status'], 'completed_llm_failed')
                self.assertFalse(report['llm']['ok'])
                self.assertTrue(report['llm']['error'])
                self.assertEqual(len(flagged(report, check_id='CONCL-UNSUPPORTED')), 3)
                if not isinstance(reply, str):
                    self.assertIn('not text', report['llm']['error'])

    def test_failures_anywhere_in_the_model_step_are_contained(self):
        from unittest import mock
        for target in ('build_messages', 'screen', 'extract_json'):
            with self.subTest(target=target), mock.patch.object(L, target, side_effect=RuntimeError('boom')):
                report = review(load('case_a_unsupported_claim.json'), self._reply())
                self.assertEqual(report['review_status'], 'completed_llm_failed')
                self.assertIn('boom', report['llm']['error'])

    def test_rule_only_categories_are_rejected(self):
        for category in ('C01', 'C02', 'C03', 'C04', 'C11'):
            with self.subTest(category=category):
                report = review(load('case_a_unsupported_claim.json'),
                                self._reply({'object_id': 'widget_a', 'category': category, **self.TEXT}))
                self.assertIn('rule-based checks only', report['rejected_llm_findings'][0]['reason'])

    def test_audit_probe_ungrounded_contradiction(self):
        req = load(CASE_D)
        item = B.checker_item()['result']
        own, other = A.assessment_id(item, 'object_00'), A.assessment_id(item, 'object_01')
        record = next(r['id'] for r in req['evidence_package']['records'] if r['object_id'] == 'object_00')
        c07 = {'object_id': 'object_00', 'category': 'C07', 'severity': 'high', **self.TEXT}
        rejected = {
            'no evidence (the audit probe)': {**c07, 'evidence_ids': []},
            'a measurement, not an assessment': {**c07, 'evidence_ids': [record]},
            "another object's assessment": {**c07, 'evidence_ids': [other]},
            'no object': {**c07, 'object_id': None, 'evidence_ids': [own]},
        }
        for name, f in rejected.items():
            with self.subTest(name):
                report = review(load(CASE_D), self._reply(f))
                self.assertEqual(report['llm']['accepted'], 0, report['rejected_llm_findings'])
        report = review(load(CASE_D), self._reply({**c07, 'evidence_ids': [own]}))
        self.assertEqual(report['llm']['accepted'], 1)
        llm = [c for c in report['criticisms'] if c['finding_source'] == 'llm_proposed'][0]
        self.assertEqual((llm['blocking'], llm['human_review_required']), (False, True))

    def test_citations_must_match_object_and_execution(self):
        req = load('case_a_unsupported_claim.json')
        vial = next(r['id'] for r in req['evidence_package']['records'] if r['object_id'] == 'vial_b')
        other_run = B.evidence_for(B.OTHER_EXEC, 'widget_a')[0]
        req['evidence_package']['records'].append(other_run)  # in the package, but from another execution
        cases = {'another object': {'object_id': 'widget_a', 'evidence_ids': [vial]},
                 'another execution': {'object_id': 'widget_a', 'evidence_ids': [other_run['id']]},
                 'another execution, no object': {'object_id': None, 'evidence_ids': [other_run['id']]}}
        for name, f in cases.items():
            with self.subTest(name):
                report = review(copy.deepcopy(req), self._reply({'category': 'C09', **f, **self.TEXT}))
                self.assertEqual(report['review_status'], 'completed')
                self.assertIn('not the finding', report['rejected_llm_findings'][0]['reason'])
        report = review(copy.deepcopy(req), self._reply({'category': 'C09', 'object_id': None,
                                                         'evidence_ids': [vial], **self.TEXT}))
        self.assertEqual(report['llm']['accepted'], 1)  # no object named: any object of this execution

    def test_trace(self):
        req = load('case_a_unsupported_claim.json')
        reply = (CASES / 'scripted_replies' / 'case_a.txt').read_text()
        backend = L.ScriptedLLM(reply)
        report = review(req, backend)
        t = report['llm']
        deterministic, info = checks.run_all(req)
        system, user = L.build_messages(req, deterministic, info['records'], info['checker_admission'])
        def sha(text):
            return hashlib.sha256(text.encode()).hexdigest()
        self.assertEqual(t['prompt_sha256'], sha(L.PROMPT_PATH.read_text(encoding='utf-8')))
        self.assertEqual(t['input_sha256'], K.digest(backend.messages(system, user)))
        self.assertEqual(t['request_sha256'], K.digest(req))
        self.assertEqual((t['raw_response'], t['response_sha256'], t['raw_response_truncated']),
                         (reply, sha(reply), False))
        self.assertEqual(t['settings'], {'scripted_reply_sha256': sha(reply)})
        self.assertEqual((t['accepted'], t['rejected']), (2, 2))

    def test_long_reply_is_cut_but_hashed_in_full(self):
        reply = json.dumps({'findings': []}) + ' ' * (L.RAW_RESPONSE_LIMIT + 10)
        t = review(load('case_c_correct_unresolved.json'), L.ScriptedLLM(reply))['llm']
        self.assertEqual((len(t['raw_response']), t['raw_response_truncated']), (L.RAW_RESPONSE_LIMIT, True))
        self.assertEqual(t['response_sha256'], hashlib.sha256(reply.encode()).hexdigest())

    def test_no_trace_without_a_model_call(self):
        for req, backend in ((load('case_b_missing_or_wrong_evidence.json'), self._reply()),
                             (load('case_c_correct_unresolved.json'), L.NullLLM())):
            t = review(req, backend)['llm']
            self.assertEqual((t['called'], t['input_sha256'], t['raw_response']), (False, None, None))


class LLMStep(unittest.TestCase):
    def test_scripted_reply_is_screened(self):
        req = load('case_a_unsupported_claim.json')
        reply = (CASES / 'scripted_replies' / 'case_a.txt').read_text()
        report = review(req, L.ScriptedLLM(reply))
        llm = [c for c in report['criticisms'] if c['finding_source'] == 'llm_proposed']
        self.assertEqual({c['category'] for c in llm}, {'C05', 'C12'})
        self.assertTrue(all(c['human_review_required'] and not c['blocking'] for c in llm))
        reasons = ' '.join(r['reason'] for r in report['rejected_llm_findings'])
        self.assertIn('not in the package', reasons)   # invented evidence ID rejected
        self.assertIn('does not exist', reasons)        # invented node rejected
        self.assertEqual(len(report['rejected_llm_findings']), 2)

    def test_bad_model_output_does_not_break_review(self):
        req = load('case_b_missing_or_wrong_evidence.json')
        report = review(req, L.ScriptedLLM('Sorry, I cannot help with that.'))
        self.assertFalse(report['llm']['ok'])
        self.assertTrue(report['llm']['error'])
        self.assertTrue(flagged(report, check_id='EV-MISSING'))  # deterministic findings survive

    def test_duplicate_of_rule_finding_is_dropped(self):
        req = load('case_a_unsupported_claim.json')
        dup = {'findings': [{'object_id': 'widget_a', 'node_id': 'G1', 'category': 'C06', 'severity': 'high',
                             'explanation': 'same as rule', 'evidence_ids': [], 'suggested_action': 'x'}]}
        report = review(req, L.ScriptedLLM(json.dumps(dup)))
        self.assertEqual(report['rejected_llm_findings'][0]['reason'], 'duplicate of a deterministic finding')

    def test_openai_compatible_client_against_local_fake_server(self):
        """Exercise the real HTTP client against a tiny vLLM-shaped server on localhost."""
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        seen, received = {}, {}
        reply = (CASES / 'scripted_replies' / 'case_a.txt').read_text()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                seen.update(path=self.path, model=body['model'], roles=[m['role'] for m in body['messages']])
                received.update(messages=body['messages'], auth=self.headers['Authorization'])
                out = json.dumps({'choices': [{'message': {'role': 'assistant', 'content': reply}}]}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            def log_message(self, *args):
                pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            # a gpt-oss name picks that model card's preset, which changes the system message
            client = L.OpenAICompatibleLLM(base_url=f'http://127.0.0.1:{server.server_port}/v1',
                                           model='fake-gpt-oss', api_key='SECRET-TEST-KEY')
            report = review(load('case_a_unsupported_claim.json'), client)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(seen, {'path': '/v1/chat/completions', 'model': 'fake-gpt-oss', 'roles': ['system', 'user']})
        self.assertTrue(report['llm']['ok'])
        self.assertEqual(report['llm']['model'], 'fake-gpt-oss')
        self.assertTrue(received['messages'][0]['content'].endswith('Reasoning: medium'))
        self.assertEqual(len([c for c in report['criticisms'] if c['finding_source'] == 'llm_proposed']), 2)
        # the trace matches what the server actually received, and the key is sent but never recorded
        self.assertEqual(report['llm']['input_sha256'], K.digest(received['messages']))
        self.assertEqual(received['auth'], 'Bearer SECRET-TEST-KEY')
        self.assertNotIn('SECRET-TEST-KEY', json.dumps(report))
        self.assertEqual((report['llm']['settings']['model'], report['llm']['settings']['system_suffix']),
                         ('fake-gpt-oss', '\nReasoning: medium'))

    def test_credentials_in_the_server_url_are_not_recorded(self):
        for url, kept in (('http://user:S3CRET@host:8001/v1', 'http://host:8001/v1'),
                          ('https://S3CRET@h.example/v1?x=1', 'https://h.example/v1?x=1'),
                          ('http://u:S3CRET@[::1]:8000/v1', 'http://[::1]:8000/v1'),
                          ('http://localhost:8000/v1', 'http://localhost:8000/v1')):
            settings = L.OpenAICompatibleLLM(base_url=url, model='m').settings()
            self.assertEqual(settings['base_url'], kept)
            self.assertNotIn('S3CRET', json.dumps(settings))

    def test_model_comparison_runner(self):
        """critic.compare_models end to end against a fake vLLM server."""
        import io
        import tempfile
        import threading
        from contextlib import redirect_stdout
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from critic import compare_models

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                out = json.dumps({'choices': [{'message': {'content': '{"findings": []}'}}]}).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            def log_message(self, *args):
                pass

        server = HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
                out = Path(tmp) / 'comparison.md'
                compare_models.main(['--model', f'fake=http://127.0.0.1:{server.server_port}/v1',
                                     '--repeats', '1', '--out', str(out)])
                rows = json.loads(out.with_suffix('.json').read_text())
                text = out.read_text()
        finally:
            server.shutdown()
            server.server_close()
        cases = {r['case'] for r in rows}
        self.assertNotIn('case_b_missing_or_wrong_evidence.json', cases)  # rejected input: no model is asked
        self.assertEqual(len(cases), len(EXPECTED) - 1)
        self.assertTrue(all(r['json_ok'] and r['review_status'] == 'completed' for r in rows))
        self.assertTrue(all(r['trace']['response_sha256'] and r['trace']['settings']['model'] == 'fake'
                            for r in rows))
        self.assertIn(f'({len(cases)} synthetic cases)', text)

    def test_malformed_model_findings_are_rejected_not_crashing(self):
        req = load('case_a_unsupported_claim.json')
        text = {'explanation': 'x', 'suggested_action': 'y'}
        weird = {'findings': [
            {'object_id': ['widget_a'], 'node_id': 'G1', 'category': 'C05', **text},   # object id is a list
            {'object_id': 'widget_a', 'node_id': 'S1', 'category': 'C05', 'evidence_ids': [['nested']], **text},
            {'object_id': 'widget_a', 'node_id': 'S1', 'category': 'C99', **text},     # unknown category
            'not an object']}
        report = review(req, L.ScriptedLLM(json.dumps(weird)))
        self.assertTrue(report['llm']['ok'])
        self.assertEqual(len(report['rejected_llm_findings']), 4)

    def test_empty_model_reply(self):
        report = review(load('case_c_correct_unresolved.json'), L.ScriptedLLM(None))
        self.assertFalse(report['llm']['ok'])
        self.assertIsNotNone(report['llm']['latency_s'])

    def test_extract_json_variants(self):
        self.assertEqual(L.extract_json('<think>x {"a":1}</think>```json\n{"findings": []}\n```'), {'findings': []})
        with self.assertRaises(ValueError):
            L.extract_json('{"other": 1}')


# Graph mutations that evaluation/r1_v4/evidence_registry_gsn/gsn.py:Graph.validate rejects (on the Case C graph).
def _nodes(g):
    return {n['id']: n for n in g['nodes']}


def m_fake_evidence(g): _nodes(g)['E1']['evidence_id'] = 'ev:' + '0' * 64
def m_goal_promoted(g): _nodes(g)['G1']['validation_status'] = 'verified_measurement'
def m_physical_strategy(g): _nodes(g)['S1']['physical_claim'] = True
def m_bad_edge_type(g): g['edges'].append({'source': 'E1', 'target': 'G1', 'type': 'supported_by'})
def m_dangling_edge(g): g['edges'].append({'source': 'G1', 'target': 'NOPE', 'type': 'supported_by'})
def m_cycle(g): g['edges'].append({'source': 'S1', 'target': 'G1', 'type': 'supported_by'})
def m_interval_stretch(g): _nodes(g)['E1']['scope']['interval'] = [8, 200]
def m_source_mismatch(g): _nodes(g)['E2']['provenance']['selector'] = '/elsewhere'
def m_evidence_on_goal(g): _nodes(g)['G1']['evidence_id'] = _nodes(g)['E1']['evidence_id']
def m_status_mismatch(g): _nodes(g)['E1']['validation_status'] = 'verified_source'
def m_duplicate_node(g): g['nodes'].append(copy.deepcopy(_nodes(g)['A1']))
def m_duplicate_edge(g): g['edges'].append(copy.deepcopy(g['edges'][0]))


GRAPH_MUTATIONS = [m_fake_evidence, m_goal_promoted, m_physical_strategy, m_bad_edge_type, m_dangling_edge, m_cycle,
                   m_interval_stretch, m_source_mismatch, m_evidence_on_goal, m_status_mismatch, m_duplicate_node,
                   m_duplicate_edge]


class AgreementWithOriginalGraphValidator(unittest.TestCase):
    """Every graph the original Graph.validate rejects must also be flagged here,
    and valid graphs must get no structural findings."""

    GRAPH_CHECKS = ('GSN-', 'EV-')

    def _original_rejects(self, graph, records):
        as_objects = [SimpleNamespace(**{**r, 'interval': tuple(r['interval'])}) for r in records]
        reg = SimpleNamespace(records=lambda: as_objects)
        try:
            Graph(tuple(Node(**n) for n in graph['nodes']), tuple(Edge(**e) for e in graph['edges'])).validate(reg)
            return None
        except ValueError as exc:
            return str(exc)

    def _ours(self, req, item):
        records, _ = checks.index_records(req)
        return [f for f in checks.check_graph(req, item, records)
                if f['check_id'].startswith(self.GRAPH_CHECKS) and f['check_id'] != 'GSN-UNSUPPORTED-GOAL']

    def test_real_demo_graph_is_accepted(self):
        graph = json.loads((GSN_DIR / 'demo' / 'GRAPH.json').read_text())
        records = json.loads((GSN_DIR / 'demo' / 'REGISTRY_EXPORT.json').read_text())['records']
        n0 = graph['nodes'][0]['scope']
        req = {'evaluation_context': {'execution_id': n0['execution_id'], 'requirement_id': 'R1',
                                      'requirement_version': '2.0.0', 'protected_objects': [n0['object_id']]},
               'evidence_package': {'records': records}, 'retrieval_context': {}}
        self.assertIsNone(self._original_rejects(graph, records))
        self.assertEqual(self._ours(req, {'object_id': n0['object_id'], 'graph': graph}), [])

    def test_mutations(self):
        req = load('case_c_correct_unresolved.json')
        records = req['evidence_package']['records']
        base = req['argument_bundle']['graphs'][0]['graph']

        self.assertIsNone(self._original_rejects(base, records))
        self.assertEqual(self._ours(req, {'object_id': 'widget_a', 'graph': base}), [])
        for mutate in GRAPH_MUTATIONS:
            with self.subTest(mutation=mutate.__name__):
                g = copy.deepcopy(base)
                mutate(g)
                original = self._original_rejects(g, records)
                ours = self._ours(req, {'object_id': 'widget_a', 'graph': g})
                self.assertIsNotNone(original, 'mutation should be invalid for the original validator')
                self.assertTrue(ours, f'original rejected ({original}) but the Critic found nothing')
                self.assertTrue(all(f['phase'] == 'validation' for f in ours))
                full = copy.deepcopy(req)
                full['argument_bundle']['graphs'][0]['graph'] = g
                self.assertEqual(review(full)['review_status'], 'rejected_invalid_input')

CASE_E = 'case_e_partial_structured_retrieval.json'


def e_scope(req=None):
    ctx = (req or load(CASE_E))['evaluation_context']
    return P.scope_of(ctx['execution_id'], ctx['task_id'], ctx['variant_id'])


def e_request(*entries, claims=None, checker=True, complete_claim=False):
    """Case E (claims match the checker) with the given structured_evidence entries."""
    req = load(CASE_E)
    if entries:
        req['structured_evidence'] = [copy.deepcopy(e) for e in entries]
    if not checker:
        req['checker_assessments'] = []
    for oid, claim in (claims or {}).items():
        req['argument_bundle']['execution_conclusion']['object_outcomes'][oid] = claim
    if claims:
        vector = req['argument_bundle']['execution_conclusion']['object_outcomes'].values()
        req['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.execution_outcome(vector)
    req['retrieval_context']['complete_within_requested_scope'] = complete_claim
    return req


def e_entry():
    return copy.deepcopy(load(CASE_E)['structured_evidence'][0])


def one_obligation(o, result=None, scope=None):
    """A bundle for a single obligation, evaluated (result given) or left UNAVAILABLE, plus a mandatory
    joint-position obligation that is AVAILABLE so the bundle is not empty."""
    scope = scope or e_scope()
    joints = P.obligation('joint_positions', 'raw.robot0_joint_pos', scope, frames=(0, 1))
    q = P.request(scope, [o, joints])
    results = {'joint_positions': ('AVAILABLE', [P.channel_item(scope, 'raw.robot0_joint_pos', (0, 1))], 'ok')}
    if result is not None:
        results[o['id']] = result
    return P.entry(q, P.evaluated(q, results))


def recite(bundle):
    """Recompute every citation ID from its (possibly edited) basis: a consistent forgery of the IDs."""
    for g in bundle['groups']:
        for item in g['items']:
            item['citation_id'] = R.CITATION_PREFIX + K.digest(item['citation_basis'])
    return bundle


def requery(entry):
    entry['bundle']['query_id'] = 'query:' + K.digest(entry['request'])
    entry['bundle']['requested_obligations'] = copy.deepcopy(entry['request']['obligations'])
    return entry


def ret_ids(report):
    return {c for c in check_ids(report) if c.startswith('RET-')}


def group(entry, oid):
    return next(g for g in entry['bundle']['groups'] if g['obligation_id'] == oid)


def first_item(entry, oid='joint_positions'):
    return group(entry, oid)['items'][0]


def _upgrade(e):
    b = e['bundle']
    b['completeness_status'] = K.PHASE5_COMPLETE
    b['assurance_status']['satisfied'] = True
    b['independent_validation']['mandatory_fulfilled'] = True


def _unvalidated(e):
    b = e['bundle']
    b['independent_validation'] = {'passed': False, 'reason': 'Request not accepted'}
    b['completeness_status'] = 'UNVERIFIED PLAN'


def _drop_missing(e):
    e['bundle']['missing_obligations'] = [m for m in e['bundle']['missing_obligations']
                                          if m['obligation_id'] != 'contacts_object_01']


def _sample_outside(e):
    sample = first_item(e)['samples'][0]
    sample['saved_frame_index'] = 99
    sample['source_selector'] = '/frames/000099/' + K.PHASE5_REGISTRY['raw.robot0_joint_pos']
    first_item(e)['citation_basis']['selectors'][0] = sample['source_selector']
    recite(e['bundle'])


def _drop_sample(e):
    item = first_item(e)
    item['samples'].pop()
    item['citation_basis']['selectors'] = [x['source_selector'] for x in item['samples']]
    recite(e['bundle'])


def _request_level_group(e):
    group(e, 'camera_frames')['status'] = 'UNVERIFIED PLAN'
    next(m for m in e['bundle']['missing_obligations'] if m['obligation_id'] == 'camera_frames')['status'] = \
        'UNVERIFIED PLAN'


def _rename_reference(e):
    item = first_item(e, 'geometry_object_01')
    item['id'] = item['citation_basis']['record_id'] = 'source-ref:' + '0' * 64
    recite(e['bundle'])


# Each edit of Case E's entry and the RET check that must catch it. IDs are recomputed where the point is
# that the content is wrong, not the hash.
STRUCTURED_TAMPERING = {
    'citation ID edited': ('RET-CITATION', lambda e: first_item(e).update(citation_id=R.CITATION_PREFIX + '0' * 64)),
    'basis selector edited, ID recomputed': ('RET-CITATION', lambda e: (
        first_item(e)['citation_basis'].update(selectors=['/frames/000000/other']), recite(e['bundle']))),
    'basis database edited, ID recomputed': ('RET-CITATION', lambda e: (
        first_item(e)['citation_basis'].update(database_sha256='0' * 64), recite(e['bundle']))),
    'basis interpretation edited, ID recomputed': ('RET-CITATION', lambda e: (
        first_item(e)['citation_basis'].update(interpretation='verified_physical'), recite(e['bundle']))),
    'item source hash edited': ('RET-CITATION', lambda e: first_item(e)['source_artifact'].update(sha256='1' * 64)),
    'request edited after retrieval': ('RET-QUERY-ID', lambda e: e['request'].update(request_id='other')),
    'requested obligations edited': ('RET-QUERY-ID', lambda e: e['bundle']['requested_obligations'][0].update(
        mandatory=False)),
    'group digest edited': ('RET-OBLIGATIONS', lambda e: group(e, 'contacts_object_01').update(
        request_digest='0' * 64)),
    'group marked optional': ('RET-OBLIGATIONS', lambda e: group(e, 'contacts_object_01').update(mandatory=False)),
    'group family edited': ('RET-OBLIGATIONS', lambda e: group(e, 'contacts_object_01').update(
        family='camera_references')),
    'group removed': ('RET-OBLIGATIONS', lambda e: e['bundle']['groups'].pop(1)),
    'groups reordered': ('RET-OBLIGATIONS', lambda e: e['bundle']['groups'].reverse()),
    'interpretation edited': ('RET-OBLIGATIONS', lambda e: group(e, 'joint_positions').update(
        requested_interpretation='verified_physical')),
    'missing obligation dropped': ('RET-MISSING', _drop_missing),
    'missing obligation marked optional': ('RET-MISSING', lambda e: e['bundle']['missing_obligations'][0].update(
        mandatory=False)),
    'missing reason rewritten': ('RET-MISSING', lambda e: e['bundle']['missing_obligations'][0].update(
        reason='fine')),
    'conditional assumption not reported': ('RET-CONDITIONAL', lambda e: group(e, 'joint_positions').update(
        conditional_assumptions=['cache_offset_seconds'])),
    'status upgraded to complete': ('RET-STATUS', _upgrade),
    'status downgraded': ('RET-STATUS', lambda e: e['bundle'].update(completeness_status='UNAVAILABLE')),
    'unvalidated bundle with evidence': ('RET-STATUS', _unvalidated),
    'optional obligation satisfied without evidence': ('RET-STATUS', lambda e: e['bundle'][
        'independent_validation']['obligations'][3].update(satisfied=True)),
    'validation of an obligation dropped': ('RET-STATUS', lambda e: e['bundle']['independent_validation'][
        'obligations'].pop()),
    'evaluated group with a request-level status': ('RET-STATUS', _request_level_group),
    'validation passed with errors': ('RET-STATUS', lambda e: e['bundle']['independent_validation'].update(
        errors=['cross_scope_evidence'])),
    'assurance marked satisfied': ('RET-STATUS', lambda e: e['bundle']['assurance_status'].update(satisfied=True)),
    'values marked unverified': ('RET-STATUS', lambda e: e['bundle']['assurance_status'].update(
        returned_values_verified=False)),
    'bundle for another execution': ('RET-SCOPE', lambda e: e['bundle']['resolved_scope'].update(
        execution_id='other-execution')),
    'bundle for another variant': ('RET-SCOPE', lambda e: e['bundle']['resolved_scope'].update(variant_id='v-2')),
    'request without a variant': ('RET-SCOPE', lambda e: (e['request'].pop('variant_id'), requery(e))),
    'obligation for another task': ('RET-SCOPE', lambda e: (e['request']['obligations'][0].update(task_id='t-2'),
                                                            requery(e))),
    'item from another variant': ('RET-ITEM', lambda e: (first_item(e).update(variant_id='v-2'),
                                                         first_item(e)['citation_basis'].update(variant_id='v-2'),
                                                         recite(e['bundle']))),
    'item in the wrong group': ('RET-ITEM', lambda e: (first_item(e).update(family='raw.robot0_joint_vel'))),
    'item outside the requested window': ('RET-ITEM', _sample_outside),
    'item not source-verified': ('RET-ITEM', lambda e: first_item(e).update(integrity_status='unverified')),
    'channel samples do not cover the window': ('RET-ITEM', _drop_sample),
    'channel item not its own record': ('RET-ITEM', lambda e: first_item(e).update(original_evidence_ids=['ev:x'])),
    'reference item ID edited, citation recomputed': ('RET-ITEM', _rename_reference),
    'requested assurance edited': ('RET-STATUS', lambda e: e['bundle']['assurance_status'].update(
        requested='verified_physical_interpretation')),
    'limitation dropped': ('RET-LIMITATIONS', lambda e: e['bundle']['limitations'].pop()),
    'sample not source-verified': ('RET-ITEM', lambda e: first_item(e)['samples'][0].update(source_status='cached')),
    'origin changed to a checker': ('RET-ITEM', lambda e: first_item(e).update(origin='checker_assessment')),
    'reference origin changed': ('RET-ITEM', lambda e: first_item(e, 'geometry_object_01').update(
        origin='direct_recording')),
    'identity promoted to physical support': ('RET-ITEM', lambda e: first_item(e, 'geometry_object_01')['value']
                                              .update(physical_support_inferred=True)),
    'sample units changed': ('RET-ITEM', lambda e: first_item(e)['samples'][0].update(value_units='deg')),
    'item units changed': ('RET-ITEM', lambda e: first_item(e).update(units={'status': 'VERIFIED', 'value': 'deg'})),
    'experimental route': ('RET-BUNDLE-SCHEMA', lambda e: e['bundle'].update(route='experimental_natural_language')),
    'safety claim verified': ('RET-BUNDLE-SCHEMA', lambda e: e['bundle'].update(safety_claim_verified=True)),
    'empirical admission on': ('RET-BUNDLE-SCHEMA', lambda e: e['bundle'].update(empirical_admission_enabled=True)),
    'historical runtime attested': ('RET-BUNDLE-SCHEMA', lambda e: e['bundle']['assurance_status'].update(
        historical_runtime_attested=True)),
    'other release': ('RET-BUNDLE-SCHEMA', lambda e: e['bundle'].update(schema_version='phase5-structured-2.0.0')),
    'physical instant claimed': ('RET-BUNDLE-SCHEMA', lambda e: first_item(e).update(
        synchronized_physical_instant=True)),
    'citation basis with extra field': ('RET-BUNDLE-SCHEMA', lambda e: first_item(e)['citation_basis'].update(
        verified=True)),
    'not a request/bundle pair': ('RET-SHAPE', lambda e: e.pop('bundle')),
}


class StructuredEvidence(unittest.TestCase):
    """Phase 5 structured retrieval (audit I7): bundles are checked, kept whole, and only add concerns."""

    def test_case_e_bundle_is_admitted_and_kept_whole(self):
        req = load(CASE_E)
        report = review(req)
        self.assertEqual(ret_ids(report), set())
        row = report['structured_retrieval'][0]
        bundle = req['structured_evidence'][0]['bundle']
        self.assertTrue(row['accepted'])
        self.assertEqual(row['query_id'], bundle['query_id'])
        self.assertEqual(row['bundle_sha256'], K.digest(bundle))
        self.assertEqual(row['completeness_status'], 'PARTIAL')
        self.assertEqual(row['limitations'], bundle['limitations'])
        self.assertEqual(row['assurance_status'], bundle['assurance_status'])
        self.assertEqual({c['citation_id'] for c in row['citations']},
                         {i['citation_id'] for g in bundle['groups'] for i in g['items']})
        self.assertEqual({(m['obligation_id'], m['mandatory'], m['status']) for m in row['missing_obligations']},
                         {('contacts_object_01', True, 'UNAVAILABLE'), ('camera_frames', False, 'UNAVAILABLE')})
        concerns = ' '.join(report['unresolved_concerns'])
        for text in ('is PARTIAL', 'mandatory obligation contacts_object_01', 'optional obligation camera_frames',
                     'not physical events', 'could not open the database'):
            self.assertIn(text, concerns)

    def test_missing_mandatory_obligation_under_an_admitted_checker_result(self):
        report = review(load(CASE_E))
        found = flagged(report, check_id='CONCL-OBLIGATION-MISSING')
        self.assertEqual([(f['object_id'], f['severity'], f['blocking']) for f in found],
                         [('object_01', 'medium', False)])  # the optional camera obligation adds nothing
        self.assertTrue(found[0]['human_review_required'])
        request = next(r for r in report['evidence_requests'] if r['criticism_id'] == found[0]['criticism_id'])
        self.assertEqual((request['measurement_type'], request['interval']), ('contact_references', [0, 2]))

    def test_missing_mandatory_obligation_without_checker_support_blocks(self):
        req = e_request(checker=False, claims={'object_00': K.INSUFFICIENT, 'object_02': K.INSUFFICIENT})
        found = flagged(review(req), check_id='CONCL-OBLIGATION-MISSING', object_id='object_01')
        self.assertEqual([(f['severity'], f['blocking']) for f in found], [('high', True)])

    def test_which_missing_obligations_matter(self):
        scope = e_scope()
        cases = {
            'about this object': (P.obligation('c', 'contact_references', scope, frames=(0, 1), object_id='object_01'),
                                  True),
            'names no object': (P.obligation('j', 'raw.robot0_joint_vel', scope, frames=(0, 1)), True),
            'timeless': (P.obligation('m', 'execution_metadata', scope), True),
            'simulator-label window': (P.obligation('t', 'recorded_time', scope, selector={
                'kind': 'simulator_labels', 'start': 0.0, 'end': 0.1}), True),
            'about another object': (P.obligation('c', 'contact_references', scope, frames=(0, 1),
                                                  object_id='object_02'), False),
            'outside the monitored interval': (P.obligation('c', 'contact_references', scope, frames=(5, 9),
                                                            object_id='object_01'), False),
            'optional': (P.obligation('c', 'contact_references', scope, mandatory=False, frames=(0, 1),
                                      object_id='object_01'), False),
        }
        for name, (o, relevant) in cases.items():
            with self.subTest(name):
                report = review(e_request(one_obligation(o)))
                self.assertEqual(ret_ids(report), set())
                found = flagged(report, check_id='CONCL-OBLIGATION-MISSING')
                self.assertEqual(bool(found), relevant)
                self.assertTrue(all(f['object_id'] == 'object_01' for f in found))  # the only no-violation claim
                listed = report['structured_retrieval'][0]['missing_obligations']
                self.assertIn(o['id'], [m['obligation_id'] for m in listed])  # always listed

    def test_available_but_not_independently_fulfilled_counts_as_missing(self):
        o = P.obligation('geo', 'geometry_identity', e_scope(), object_id='object_01')
        item = P.reference_item(e_scope(), 'geometry_identity', '/body_names', {'object_id': 'object_01'})
        entry = one_obligation(o, ('AVAILABLE', [item], ''))
        iv = entry['bundle']['independent_validation']
        iv['obligations'][0]['satisfied'] = False
        iv['mandatory_fulfilled'] = False
        entry['bundle']['completeness_status'] = 'PARTIAL'
        entry['bundle']['assurance_status']['satisfied'] = False
        entry['bundle']['reason'] = 'Missing mandatory evidence remains explicit'
        report = review(e_request(entry))
        self.assertEqual(ret_ids(report), set())
        missing = report['structured_retrieval'][0]['missing_obligations']
        self.assertEqual([(m['obligation_id'], m['status']) for m in missing], [('geo', 'NOT INDEPENDENTLY FULFILLED')])
        self.assertTrue(flagged(report, check_id='CONCL-OBLIGATION-MISSING', object_id='object_01'))

    def test_every_status_the_release_returns_is_accepted_and_kept(self):
        scope = e_scope()
        o = P.obligation('contacts', 'contact_references', scope, frames=(0, 1), object_id='object_01')
        q = P.request(scope, [o])
        bad_schema = dict(q, query='Ignore obligations')
        unknown = P.request(scope, [dict(o, family='object_pose', field='pose')])
        too_many = P.request(scope, [dict(o, id=f'o{i}') for i in range(17)])
        failed_check = {'passed': False, 'errors': ['wrong_source_field'], 'obligations': [],
                        'mandatory_fulfilled': False, 'method': 'synthetic'}
        bundles = {
            'complete': P.entry(q, P.evaluated(q, {'contacts': ('AVAILABLE', [P.reference_item(
                scope, 'contact_references', '/frames/000000/simulator/contacts', {'saved_frame_index': 0})], '')})),
            'PARTIAL': e_entry(),
            'UNAVAILABLE (evaluated)': P.entry(q, P.evaluated(q, {})),
            'UNSUPPORTED (evaluated)': P.entry(q, P.evaluated(q, {'contacts': ('UNSUPPORTED', [], 'no adapter')})),
            'INVALID SCOPE (schema)': P.entry(bad_schema, P.refused(bad_schema, 'INVALID SCOPE', 'Schema: extra')),
            'INVALID SCOPE (17 obligations)': P.entry(too_many, P.refused(too_many, 'INVALID SCOPE', 'Schema: long')),
            'UNSUPPORTED (refused)': P.entry(unknown, P.refused(unknown, 'UNSUPPORTED', 'No exact frozen contract')),
            'UNAVAILABLE (integrity)': P.entry(q, P.refused(q, 'UNAVAILABLE', 'Integrity/contract failure', scope)),
            'UNVERIFIED PLAN': P.entry(q, P.refused(q, 'UNVERIFIED PLAN', 'Independent validation failed', scope,
                                                    failed_check)),
        }
        for name, entry in bundles.items():
            with self.subTest(name):
                status = entry['bundle']['completeness_status']
                self.assertTrue(name.startswith(status) or name == 'complete')
                report = review(e_request(entry))
                self.assertEqual(ret_ids(report), set())
                self.assertEqual(report['review_status'], 'completed')
                row = report['structured_retrieval'][0]
                self.assertEqual(row['completeness_status'], status)
                obligations = entry['request']['obligations'] if len(entry['request']['obligations']) <= 16 else []
                if status != K.PHASE5_COMPLETE:
                    self.assertIn(f'is {status}:', ' '.join(report['unresolved_concerns']))
                    available = {g['obligation_id'] for g in entry['bundle']['groups'] if g['status'] == 'AVAILABLE'}
                    self.assertEqual([m['obligation_id'] for m in row['missing_obligations']],
                                     [x['id'] for x in obligations if x['id'] not in available])
                self.assertEqual(bool(flagged(report, check_id='CONCL-OBLIGATION-MISSING')),
                                 status != K.PHASE5_COMPLETE and bool(obligations))

    def test_tampering_is_caught(self):
        for name, (expected, change) in STRUCTURED_TAMPERING.items():
            with self.subTest(name):
                entry = e_entry()
                change(entry)
                report = review(e_request(entry))
                self.assertIn(expected, ret_ids(report))
                self.assertEqual(report['review_status'], 'rejected_invalid_input')
                self.assertFalse(report['structured_retrieval'][0]['accepted'])
                self.assertEqual(report['structured_retrieval'][0]['citations'], [])

    def test_every_field_of_the_citation_basis_is_checked(self):
        wrong = {'citation_version': '2', 'database_sha256': '0' * 64, 'record_id': 'channel:other',
                 'source_sha256': '1' * 64, 'execution_id': 'other', 'task_id': 'other', 'variant_id': 'other',
                 'selectors': ['/frames/000000/other'], 'component': 'elbow', 'units': 'deg',
                 'interpretation': 'conditional', 'required_properties': ['units']}
        self.assertEqual(set(wrong), set(R.expected_basis(first_item(e_entry()), {})))
        for key, value in wrong.items():
            with self.subTest(key):
                entry = e_entry()
                first_item(entry)['citation_basis'][key] = value
                recite(entry['bundle'])
                self.assertIn('RET-CITATION', ret_ids(review(e_request(entry))))

    def test_recorded_metadata_outside_the_window(self):
        scope = e_scope()
        o = P.obligation('contacts', 'contact_references', scope, frames=(0, 1), object_id='object_01')
        q = P.request(scope, [o])
        for frame, caught in ((1, False), (2, True)):
            item = P.reference_item(scope, 'contact_references', f'/frames/{frame:06d}/simulator/contacts',
                                    {'saved_frame_index': frame})
            entry = P.entry(q, P.evaluated(q, {'contacts': ('AVAILABLE', [item], '')}))
            self.assertEqual('RET-ITEM' in ret_ids(review(e_request(entry))), caught, frame)

    def test_a_bundle_that_failed_validation_returns_nothing(self):
        scope = e_scope()
        o = P.obligation('contacts', 'contact_references', scope, frames=(0, 1), object_id='object_01')
        q = P.request(scope, [o, dict(o, id='more')])

        def refused(status='INVALID SCOPE'):
            return P.entry(q, P.refused(q, status, 'Wrong task or variant', scope))

        def with_item(e):
            g = e['bundle']['groups'][0]
            g['items'] = [P.reference_item(scope, 'contact_references', '/frames/000000/simulator/contacts',
                                           {'saved_frame_index': 0})]
            P.release().cite(g, o, scope)
            e['bundle']['assurance_status']['returned_values_verified'] = True

        def mixed_groups(e):
            e['bundle']['groups'][0]['status'] = e['bundle']['missing_obligations'][0]['status'] = 'UNAVAILABLE'
        self.assertEqual(ret_ids(review(e_request(refused()))), set())
        for name, entry, change in (('evidence returned', refused(), with_item),
                                    ('evaluated status', refused('PARTIAL'), lambda e: None),
                                    ('groups with other statuses', refused(), mixed_groups)):
            with self.subTest(name):
                change(entry)
                self.assertEqual(ret_ids(review(e_request(entry))), {'RET-STATUS'})

    def test_a_request_the_release_refuses_cannot_return_evidence(self):
        scope = e_scope()
        o = P.obligation('contacts', 'contact_references', scope, frames=(0, 1), object_id='object_01')
        item = P.reference_item(scope, 'contact_references', '/frames/000000/simulator/contacts',
                                {'saved_frame_index': 0})
        refusals = {
            'duplicate obligation IDs': [o, o],
            'unregistered family': [dict(o, family='object_pose', field='pose')],
            'wrong field': [dict(o, field='simulator/time/value')],
            'missing temporal selector': [{k: v for k, v in o.items() if k != 'selector'}],
            'selector on timeless metadata': [P.obligation('m', 'execution_metadata', scope, frames=(0, 1))],
            'reversed selector': [dict(o, selector={'kind': 'frames', 'start': 2, 'end': 1})],
            'downgraded assurance': [dict(o, assurance='provenance_complete')],
            'crossing execution': [dict(o, execution_id='other')],
        }
        for name, obligations in refusals.items():
            with self.subTest(name):
                q = P.request(scope, obligations)
                self.assertIsNotNone(R.request_refusal(q))
                results = {x['id']: ('AVAILABLE', [item], '') for x in obligations}
                report = review(e_request(P.entry(q, P.evaluated(q, results))))
                self.assertIn('RET-QUERY', ret_ids(report))
        historical = P.request(scope, [o], assurance='historical_producer_attestation')
        self.assertIsNotNone(R.request_refusal(historical))
        self.assertIsNone(R.request_refusal(P.request(scope, [o])))

    def test_bundles_never_support_a_claim(self):
        """A complete bundle is not a checker result: no-violation claims without one stay unsupported."""
        scope = e_scope()
        o = P.obligation('contacts', 'contact_references', scope, frames=(0, 2), object_id='object_01')
        item = P.reference_item(scope, 'contact_references', '/frames/000000/simulator/contacts',
                                {'saved_frame_index': 0})
        q = P.request(scope, [o])
        entry = P.entry(q, P.evaluated(q, {'contacts': ('AVAILABLE', [item], '')}))
        self.assertEqual(entry['bundle']['completeness_status'], K.PHASE5_COMPLETE)
        req = e_request(entry, checker=False, claims={o: K.NO_VIOLATION for o in ('object_00', 'object_01',
                                                                                  'object_02')})
        report = review(req)
        self.assertEqual(ret_ids(report), set())
        self.assertEqual({f['object_id'] for f in flagged(report, check_id='CONCL-UNSUPPORTED', blocking=True)},
                         {'object_00', 'object_01', 'object_02'})
        self.assertEqual(report['checker_admission'], [])
        self.assertEqual(report['summary']['accepted_execution_outcome'], K.INSUFFICIENT)

    def test_retrieval_context_cannot_claim_completeness_over_a_partial_bundle(self):
        found = flagged(review(e_request(complete_claim=True)), check_id='CONCL-RETRIEVAL-COMPLETE')
        self.assertEqual([(f['severity'], f['blocking']) for f in found], [('medium', False)])
        scope = e_scope()
        o = P.obligation('geo', 'geometry_identity', scope, object_id='object_01')
        q = P.request(scope, [o])
        complete = P.entry(q, P.evaluated(q, {'geo': ('AVAILABLE', [P.reference_item(
            scope, 'geometry_identity', '/body_names', {'object_id': 'object_01'})], '')}))
        self.assertFalse(flagged(review(e_request(complete, complete_claim=True)), check_id='CONCL-RETRIEVAL-COMPLETE'))

    def test_conditional_assumptions_are_kept(self):
        scope = e_scope()
        o = P.obligation('j', 'raw.robot0_joint_pos', scope, frames=(0, 1), interpretation='conditional',
                         allow_conditional=True, required_properties=['cache_offset_seconds'])
        q = P.request(scope, [o])
        item = P.channel_item(scope, 'raw.robot0_joint_pos', (0, 1), conditional=['cache_offset_seconds'])
        entry = P.entry(q, P.evaluated(q, {'j': ('AVAILABLE', [item], 'ok', ['cache_offset_seconds'])}))
        report = review(e_request(entry))
        self.assertEqual(ret_ids(report), set())
        self.assertEqual(report['structured_retrieval'][0]['conditional_assumptions'],
                         [{'obligation_id': 'j', 'properties': ['cache_offset_seconds']}])
        self.assertIn('assumptions, not verified properties', ' '.join(report['unresolved_concerns']))

        def hidden(e):
            e['bundle']['groups'][0]['conditional_assumptions'] = e['bundle']['conditional_assumptions'] = []

        def undescribed(e):
            del first_item(e, 'j')['interpretation_properties']['cache_offset_seconds']

        def unreported(e):
            e['bundle']['conditional_assumptions'] = []
        units = P.obligation('u', 'raw.robot0_joint_pos', scope, frames=(0, 1), interpretation='verified_physical')
        q2 = P.request(scope, [units])
        si = P.channel_item(scope, 'raw.robot0_joint_pos', (0, 1))
        si['samples'][0]['selected_unit_status'] = 'CONDITIONAL'
        for name, e in (('hidden', copy.deepcopy(entry)), ('undescribed', copy.deepcopy(entry)),
                        ('unreported', copy.deepcopy(entry)),
                        ('SI units', P.entry(q2, P.evaluated(q2, {'u': ('AVAILABLE', [si], 'ok', [])})))):
            with self.subTest(name):
                {'hidden': hidden, 'undescribed': undescribed, 'unreported': unreported}.get(name, lambda e: None)(e)
                self.assertEqual(ret_ids(review(e_request(e))), {'RET-CONDITIONAL'})
        fixed = P.entry(q2, P.evaluated(q2, {'u': ('AVAILABLE', [si], 'ok', ['si_component_units'])}))
        self.assertEqual(ret_ids(review(e_request(fixed))), set())
        order = P.channel_item(scope, 'raw.robot0_joint_pos', (0, 1), conditional=['component_order'])
        physical = P.entry(q2, P.evaluated(q2, {'u': ('AVAILABLE', [order], 'ok', ['component_order'])}))
        self.assertEqual(ret_ids(review(e_request(physical))), set())  # verified_physical implies component_order

    def test_solution_links_and_phase5_ids_in_solutions(self):
        req = load(CASE_E)
        row = review(req)['structured_retrieval'][0]
        pose = req['evidence_package']['records'][3]  # object_01's pose record, the geometry item's original ID
        self.assertEqual(pose['object_id'], 'object_01')
        self.assertEqual([(x['object_id'], x['node_id'], x['evidence_id']) for x in row['linked_solutions']],
                         [('object_01', 'E1', pose['id'])])
        citation = row['citations'][0]['citation_id']
        graph = req['argument_bundle']['graphs'][1]['graph']
        next(n for n in graph['nodes'] if n['id'] == 'E1')['evidence_id'] = citation
        report = review(req)
        found = flagged(report, check_id='EV-MISSING', node_id='E1', object_id='object_01')
        self.assertIn('Phase 5 structured-retrieval ID', found[0]['explanation'])
        self.assertEqual(report['review_status'], 'rejected_invalid_input')

    def test_the_model_cannot_cite_a_retrieval_citation(self):
        citation = review(load(CASE_E))['structured_retrieval'][0]['citations'][0]['citation_id']
        reply = json.dumps({'findings': [{'object_id': 'object_01', 'node_id': 'E1', 'category': 'C05',
                                          'severity': 'medium', 'explanation': 'Overreads geometry.',
                                          'evidence_ids': [citation], 'suggested_action': 'Narrow it.'}]})
        report = review(load(CASE_E), L.ScriptedLLM(reply))
        self.assertEqual(report['llm']['accepted'], 0)
        self.assertIn('not in the package', report['rejected_llm_findings'][0]['reason'])

    def test_malformed_section_and_changed_release(self):
        req = load(CASE_E)
        req['structured_evidence'] = {'request': {}}
        report = review(req)
        self.assertIn('RET-SHAPE', ret_ids(report))
        self.assertEqual(report['review_status'], 'rejected_invalid_input')
        original = K.PHASE5_QUERY_SCHEMA_SHA256
        try:
            K.PHASE5_QUERY_SCHEMA_SHA256 = '0' * 64
            R._PINS = (('phase5_query', K.PHASE5_QUERY_SCHEMA_SHA256),) + R._PINS[1:]
            report = review(load(CASE_E))
        finally:
            K.PHASE5_QUERY_SCHEMA_SHA256 = original
            R._PINS = (('phase5_query', original),) + R._PINS[1:]
        self.assertIn('RET-RELEASE', ret_ids(report))
        self.assertEqual(review(load(CASE_E))['review_status'], 'completed')

    def test_requests_without_structured_evidence_are_unchanged(self):
        report = review(load('case_c_correct_unresolved.json'))
        self.assertEqual(report['structured_retrieval'], [])
        self.assertNotIn('Structured retrieval', ' '.join(report['unresolved_concerns']))

    def test_fixtures_come_from_the_release_code(self):
        """phase5.py runs api.py's own bundle assembly; the release's two schemas accept what it builds."""
        from critic import schema as S
        rel = P.release()
        self.assertEqual(rel.response.__code__.co_filename, str(P.API))
        bundle = load(CASE_E)['structured_evidence'][0]['bundle']
        for name in ('phase5_bundle', 'phase5_consumer'):
            self.assertEqual(S.errors(bundle, S.load(name)), [], name)


class MalformedInput(unittest.TestCase):
    """The Critic must report bad input as findings, never crash."""

    def assert_valid_report(self, report):
        self.assertTrue(report['criticisms'])
        O.validate(report, json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text()))

    def test_obviously_broken_requests(self):
        for bad in (None, [], 'text', {}, {'schema_version': K.REQUEST_SCHEMA_VERSION}):
            with self.subTest(request=bad):
                report = review(bad)
                self.assert_valid_report(report)
                self.assertEqual(report['criticisms'][0]['category'], 'C01')
                self.assertFalse(report['llm']['called'])

    def test_random_corruption_never_crashes(self):
        """Replace random values deep inside valid requests with values of the wrong type."""
        import random
        rng = random.Random(6467)
        report_schema = json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text())
        junk = [None, 7, 'x', [], {}, [1, 2], {'a': 1}, True, -1.5]
        base = [load(name) for name in EXPECTED]

        def paths(value, prefix=()):
            yield prefix
            if isinstance(value, dict):
                for k, v in value.items():
                    yield from paths(v, prefix + (k,))
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    yield from paths(v, prefix + (i,))

        with_checker, with_bundle = load(CASE_D), load(CASE_E)

        for trial in range(800):
            # trials 400-599 corrupt the checker result only, 600-799 the structured evidence only
            req = copy.deepcopy(rng.choice(base) if trial < 400 else with_checker if trial < 600 else with_bundle)
            prefix = () if trial < 400 else ('checker_assessments',) if trial < 600 else ('structured_evidence',)
            target = rng.choice([p for p in paths(req) if p and p[:len(prefix)] == prefix and p != prefix])
            parent = req
            for step in target[:-1]:
                parent = parent[step]
            if isinstance(parent, dict) and rng.random() < 0.3:
                del parent[target[-1]]
            else:
                parent[target[-1]] = rng.choice(junk)
            with self.subTest(trial=trial, path=target):
                report = review(req, L.ScriptedLLM('{"findings": []}'))
                self.assertIn('summary', report)
                O.validate(report, report_schema)


class TestOracles(unittest.TestCase):
    """How the tests reach the team's code (tests/oracles.py)."""

    def test_team_modules_do_not_read_their_annotations(self):
        """On Python 3.9 the team's modules are loaded with postponed annotations. That changes nothing as long
        as no module reads its annotations at run time (dataclasses only read ClassVar and InitVar from them, and
        neither is used). This checks every module of the R1 checker and the GSN
        and registry code (the oracles), not the separate RAG release."""
        import re
        pattern = re.compile(r'get_type_hints|__annotations__|fields\([^)]*\)[^\n]*\.type\b|ClassVar|InitVar')
        modules = sorted((ROOT / 'evaluation' / 'r1_v4').glob('*.py')) + sorted(GSN_DIR.glob('*.py'))
        self.assertIn(GSN_DIR / 'gsn.py', modules)
        self.assertIn(ROOT / 'evaluation' / 'r1_v4' / 'runtime.py', modules)
        for path in modules:
            with self.subTest(path.name):
                self.assertIsNone(pattern.search(path.read_text(encoding='utf-8')))

    def test_strict_mode_turns_a_missing_oracle_into_a_failure(self):
        probe = unittest.TestCase()

        def outcome(available):
            try:
                O.require(probe, available, 'oracle missing')
            except unittest.SkipTest:
                return 'skipped'
            except AssertionError:
                return 'failed'
            return 'ran'
        original = O.STRICT
        try:
            O.STRICT = True
            self.assertEqual((outcome(False), outcome(True)), ('failed', 'ran'))
            O.STRICT = False
            self.assertEqual((outcome(False), outcome(True)), ('skipped', 'ran'))
        finally:
            O.STRICT = original

    def test_schema_fallback_rejects(self):
        with self.assertRaises(AssertionError):
            O.validate({'a': 1}, {'required': ['b']})
        O.validate({'b': 1}, {'required': ['b']})


class VocabularyInSync(unittest.TestCase):
    def test_copies_match_existing_schemas(self):
        gs = json.loads((GSN_DIR / 'gsn_graph.schema.json').read_text())
        node_props = gs['properties']['nodes']['items']['properties']
        self.assertEqual(set(node_props['type']['enum']), K.NODE_TYPES)
        self.assertEqual(set(node_props['origin']['enum']), K.NODE_ORIGINS)
        self.assertEqual(set(node_props['validation_status']['enum']), K.NODE_STATUSES)
        self.assertEqual(set(gs['properties']['edges']['items']['properties']['type']['enum']), K.EDGE_TYPES)
        rs = json.loads((GSN_DIR / 'registry_record.schema.json').read_text())
        self.assertEqual(set(rs['required']), set(K.RECORD_REQUIRED))

    def test_optional_evidence_matches_the_r1_configuration_schema(self):
        schema = json.loads((ROOT / 'requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json').read_text())
        rules = schema['properties']['evidence_requirements']['properties']
        optional = {k for k, v in rules.items() if str(v.get('const', '')).startswith('optional')}
        self.assertEqual(optional, K.OPTIONAL_EVIDENCE)

    def test_checker_contract_copies_match_assessment_schema(self):
        schema = json.loads((ROOT / 'evaluation/r1_v4/assessment.schema.json').read_text())
        props = schema['properties']
        for key, value in A.RESULT_CONSTANTS.items():
            if key in props and 'const' in props[key]:
                self.assertEqual(props[key]['const'], value, key)
        self.assertEqual({props['checker_version']['const']}, A.KNOWN_CHECKER_VERSIONS)
        self.assertTrue(set(schema['required']) <= set(A.RESULT_REQUIRED))
        obj = props['object_assessments']['items']
        self.assertEqual(set(obj['required']), set(A.OBJECT_FIELDS))
        self.assertEqual(set(obj['properties']['applicability']['enum']), A.APPLICABILITY)
        self.assertEqual(set(obj['properties']['outcome']['enum']), K.OUTCOMES)
        self.assertEqual({obj['properties']['validation_status']['const']}, set(A.SYNTHETIC_STATUSES))
        self.assertEqual(set(obj['properties']['coverage']['required']), set(A.COVERAGE_FIELDS))

    def test_phase5_pins_match_the_release(self):
        """contract.py's copies of the Phase 5 release constants, read from its config files without importing
        them (they need the release's database paths), and the hashes of its schema files."""
        import ast

        def constants(path):
            """Literal assignments, dict(k=literal, ...) calls, and the literal set of 'set(X)|{...}'."""
            out = {}
            for node in ast.parse((ROOT / path).read_text()).body:
                if not (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)):
                    continue
                name, value = node.targets[0].id, node.value
                if isinstance(value, ast.Call) and ast.unparse(value.func) == 'dict' and not value.args:
                    out[name] = {k.arg: ast.literal_eval(k.value) for k in value.keywords}
                elif isinstance(value, ast.BinOp) and isinstance(value.right, ast.Set):
                    out[name] = ('|', ast.unparse(value.left), ast.literal_eval(value.right))
                else:
                    try:
                        out[name] = ast.literal_eval(value)
                    except ValueError:
                        pass
            return out
        release = constants('evaluation/r1_v4/rag_evidence_database/final_phase5_release/config.py')
        base = constants('evaluation/r1_v4/rag_evidence_database/retrieval_remediation/config.py')
        self.assertEqual(release['VERSION'], K.PHASE5_VERSION)
        self.assertEqual(release['QUERY_SCHEMA_SHA'], K.PHASE5_QUERY_SCHEMA_SHA256)
        self.assertEqual(base['DATABASE_SHA'], K.PHASE5_DATABASE_SHA256)
        self.assertEqual(dict(zip(base['CHANNELS'], base['FIELDS'])), K.PHASE5_CHANNELS)
        self.assertEqual({**K.PHASE5_CHANNELS, **release['GROUP_FIELDS']}, K.PHASE5_REGISTRY)
        extra = K.PHASE5_TEMPORAL - set(K.PHASE5_CHANNELS)
        self.assertEqual(release['TEMPORAL_FAMILIES'], ('|', 'set(CHANNELS)', extra))
        from critic import schema as S
        for name, pinned in (('phase5_query', K.PHASE5_QUERY_SCHEMA_SHA256),
                             ('phase5_bundle', K.PHASE5_BUNDLE_SCHEMA_SHA256)):
            self.assertEqual(hashlib.sha256(S.SCHEMAS[name].read_bytes()).hexdigest(), pinned, name)
        bundle_schema = S.load('phase5_bundle')
        self.assertEqual(tuple(bundle_schema['properties']['completeness_status']['enum']), K.PHASE5_STATUSES)
        self.assertEqual(bundle_schema['properties']['schema_version']['const'], K.PHASE5_VERSION)

    def test_digest_is_the_release_digest(self):
        """Query IDs and citations are recomputed with contract.digest; the release uses provenance.digest."""
        from evaluation.r1_v4 import provenance
        entry = load(CASE_E)['structured_evidence'][0]
        for value in (entry['request'], entry['bundle'], {'x': [1.0, -0.0, 'é', None, True]}):
            self.assertEqual(K.digest(value), provenance.digest(value))

    def test_record_ids_reproduce_registry_hashes(self):
        records = json.loads((GSN_DIR / 'demo' / 'REGISTRY_EXPORT.json').read_text())['records']
        self.assertTrue(all(K.record_content_id(r) == r['id'] for r in records))


if __name__ == '__main__':
    unittest.main()
