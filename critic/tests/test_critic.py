"""Critic tests. Run from the repository root:

    python3 -m unittest discover -s critic/tests -t . -v

No network, no GPU and no LLM service are needed.
"""
import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from critic import assessments as A, checks, contract as K, llm as L, review
from critic.cases import build_cases as B

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / 'critic' / 'cases'
EXPECTED = json.loads((CASES / 'expected.json').read_text())
GSN_DIR = ROOT / 'evaluation' / 'r1_v4' / 'evidence_registry_gsn'

try:
    import jsonschema
except ImportError:  # optional
    jsonschema = None

try:  # teammate's original validator, used as an oracle
    from evaluation.r1_v4.evidence_registry_gsn.gsn import Graph, Node, Edge
except Exception:  # pragma: no cover - module missing or incompatible
    Graph = None


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
        if jsonschema is None:
            self.skipTest('jsonschema not installed')
        report_schema = json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text())
        request_schema = json.loads((ROOT / 'critic/schemas/critic_request.schema.json').read_text())
        graph_schema = json.loads((GSN_DIR / 'gsn_graph.schema.json').read_text())
        record_schema = json.loads((GSN_DIR / 'registry_record.schema.json').read_text())
        for name in EXPECTED:
            req = load(name)
            jsonschema.validate(req, request_schema)
            for item in req['argument_bundle']['graphs']:
                jsonschema.validate(item['graph'], graph_schema)
            for rec in req['evidence_package']['records']:
                jsonschema.validate(rec, record_schema)
            for backend in (L.NullLLM(), L.ScriptedLLM((CASES / 'scripted_replies' / f'{name[:6]}.txt').read_text())):
                jsonschema.validate(review(req, backend), report_schema)

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
        if jsonschema is not None:
            jsonschema.validate(report, json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text()))

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
        # The checker itself needs Python 3.10+ and jsonschema>=4 (evaluation/r1_v4/requirements.txt).
        if sys.version_info < (3, 10):
            self.skipTest('the R1 checker needs Python 3.10+')
        if jsonschema is None or not hasattr(jsonschema, 'Draft202012Validator'):
            self.skipTest('the R1 checker needs jsonschema>=4')
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
        if jsonschema is None:
            self.skipTest('jsonschema not installed')
        req = load(CASE_D)
        jsonschema.validate(req, json.loads((ROOT / 'critic/schemas/critic_request.schema.json').read_text()))
        jsonschema.validate(review(req), json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text()))


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
        with self.assertRaises(S.UnsupportedKeyword):  # also refused while validating, not only up front
            S.errors(1, {'format': 'email'})

    def test_agrees_with_jsonschema(self):
        if jsonschema is None or not hasattr(jsonschema, 'Draft202012Validator'):
            self.skipTest('jsonschema>=4 not installed')
        import random
        from critic import schema as S
        rng = random.Random(6467)
        junk = [None, 7, -1, 'x', '', [], {}, [1, 1], {'a': 1}, True, 1.5, 0, 'R1', '2.0.0', 'frame']
        docs = {'request': [load(n) for n in EXPECTED], 'checker_assessment': [B.checker_item()['result']],
                'r1_configuration': [B.checker_item()['configuration']]}
        docs['gsn_graph'] = [g['graph'] for d in docs['request'] for g in d['argument_bundle']['graphs']]
        docs['registry_record'] = [r for d in docs['request'] for r in d['evidence_package']['records']]
        docs['report'] = [review(d) for d in docs['request']]

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
        if sys.version_info < (3, 10) or jsonschema is None or not hasattr(jsonschema, 'Draft202012Validator'):
            self.skipTest('the R1 checker needs Python 3.10+ and jsonschema>=4')
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
        seen = {}
        reply = (CASES / 'scripted_replies' / 'case_a.txt').read_text()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                seen.update(path=self.path, model=body['model'], roles=[m['role'] for m in body['messages']])
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
            client = L.OpenAICompatibleLLM(base_url=f'http://127.0.0.1:{server.server_port}/v1', model='fake-model')
            report = review(load('case_a_unsupported_claim.json'), client)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(seen, {'path': '/v1/chat/completions', 'model': 'fake-model', 'roles': ['system', 'user']})
        self.assertTrue(report['llm']['ok'])
        self.assertEqual(report['llm']['model'], 'fake-model')
        self.assertEqual(len([c for c in report['criticisms'] if c['finding_source'] == 'llm_proposed']), 2)

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


@unittest.skipIf(Graph is None, "teammate's evidence_registry_gsn module not importable")
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


class MalformedInput(unittest.TestCase):
    """The Critic must report bad input as findings, never crash."""

    def assert_valid_report(self, report):
        self.assertTrue(report['criticisms'])
        if jsonschema is not None:
            schema = json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text())
            jsonschema.validate(report, schema)

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

        with_checker = load(CASE_D)

        for trial in range(600):
            # the last 200 trials corrupt the checker result only
            req = copy.deepcopy(rng.choice(base) if trial < 400 else with_checker)
            prefix = () if trial < 400 else ('checker_assessments',)
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
                if jsonschema is not None:
                    schema = json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text())
                    jsonschema.validate(report, schema)


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

    def test_record_ids_reproduce_registry_hashes(self):
        records = json.loads((GSN_DIR / 'demo' / 'REGISTRY_EXPORT.json').read_text())['records']
        self.assertTrue(all(K.record_content_id(r) == r['id'] for r in records))


if __name__ == '__main__':
    unittest.main()
