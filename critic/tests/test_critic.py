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


class GeneralizedConfiguration(unittest.TestCase):
    """R1 is configurable: no fixed object list, no fixed surface."""

    def test_extra_configured_object_is_reported_missing(self):
        req = load('case_c_correct_unresolved.json')
        req['evaluation_context']['protected_objects'].append('flask_d')
        req['argument_bundle']['protected_objects'].append('flask_d')
        report = review(req)
        self.assertTrue(flagged(report, check_id='BUNDLE-MISSING', object_id='flask_d'))
        self.assertEqual(report['summary']['objects_missing'], ['flask_d'])

    def test_fewer_configured_objects_are_not_demanded(self):
        req = load('case_c_correct_unresolved.json')
        req['evaluation_context']['protected_objects'] = ['widget_a']
        req['argument_bundle']['protected_objects'] = ['widget_a']
        req['argument_bundle']['graphs'] = req['argument_bundle']['graphs'][:1]
        req['argument_bundle']['execution_conclusion']['object_outcomes'] = {'widget_a': K.INSUFFICIENT}
        report = review(req)
        self.assertFalse(report['summary']['blocking_defects'], report['criticisms'])

    def test_graph_for_unconfigured_object(self):
        req = load('case_c_correct_unresolved.json')
        req['evaluation_context']['protected_objects'].remove('carton_c')
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
        self.assertTrue(flagged(review(req), check_id='CONCL-AGGREGATION'))

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
        self.assertTrue({'CHK-REQUIREMENT', 'CHK-TASK', 'CHK-TIME'} <= check_ids(report))
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
        cases = {
            'CHK-EXECUTION': lambda i: i['configuration'].update(execution_id='other-execution'),
            'CHK-OBJECTS': lambda i: i['configuration']['protected_objects'].pop(),
            'CHK-SURFACES': lambda i: i['configuration']['support_surfaces'].pop(),
            'CHK-TIME': lambda i: i['configuration']['monitoring_interval'].update(
                end={'kind': 'terminal_recorded_snapshot', 'value': None}),
            'CHK-PRODUCER': lambda i: i['result'].update(checker_version='9.9.9'),
        }
        for check_id, change in cases.items():
            with self.subTest(check_id):
                report = review(checker_request(forged(change)))
                self.assertIn(check_id, check_ids(report))
                self.assertEqual(admitted_objects(report), set())
                self.assertFalse(flagged(report, category='C07'))

    def test_clock_must_match(self):
        req = checker_request()
        req['evaluation_context']['monitored_interval']['clock'] = 'simulation_time_s'
        report = review(req)
        self.assertIn('CHK-CLOCK', check_ids(report))
        self.assertEqual(admitted_objects(report), set())

    def test_missing_surface_list_fails_closed(self):
        req = checker_request()
        del req['evaluation_context']['support_surfaces']
        report = review(req)
        self.assertIn('CHK-SURFACES', check_ids(report))
        self.assertEqual(admitted_objects(report), set())

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
        self.assertIn('not in the package', report['rejected_llm_findings'][0]['reason'])
        view = json.loads(L.build_messages(checker_request(item), [], {}, report['checker_admission'])[1]
                          .split('\n', 1)[1])
        self.assertEqual({a['admitted'] for a in view['checker_assessments']}, {False})

    def test_request_and_report_match_schema(self):
        if jsonschema is None:
            self.skipTest('jsonschema not installed')
        req = load(CASE_D)
        jsonschema.validate(req, json.loads((ROOT / 'critic/schemas/critic_request.schema.json').read_text()))
        jsonschema.validate(review(req), json.loads((ROOT / 'critic/schemas/critic_report.schema.json').read_text()))


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
        req = {'evaluation_context': {'execution_id': n0['execution_id'], 'requirement_version': '2.0.0',
                                      'protected_objects': [n0['object_id']]},
               'evidence_package': {'records': records}, 'retrieval_context': {}}
        self.assertIsNone(self._original_rejects(graph, records))
        self.assertEqual(self._ours(req, {'object_id': n0['object_id'], 'graph': graph}), [])

    def test_mutations(self):
        req = load('case_c_correct_unresolved.json')
        records = req['evidence_package']['records']
        base = req['argument_bundle']['graphs'][0]['graph']

        def nodes(g):
            return {n['id']: n for n in g['nodes']}

        def m_fake_evidence(g): nodes(g)['E1']['evidence_id'] = 'ev:' + '0' * 64
        def m_goal_promoted(g): nodes(g)['G1']['validation_status'] = 'verified_measurement'
        def m_physical_strategy(g): nodes(g)['S1']['physical_claim'] = True
        def m_bad_edge_type(g): g['edges'].append({'source': 'E1', 'target': 'G1', 'type': 'supported_by'})
        def m_dangling_edge(g): g['edges'].append({'source': 'G1', 'target': 'NOPE', 'type': 'supported_by'})
        def m_cycle(g): g['edges'].append({'source': 'S1', 'target': 'G1', 'type': 'supported_by'})
        def m_interval_stretch(g): nodes(g)['E1']['scope']['interval'] = [8, 200]
        def m_source_mismatch(g): nodes(g)['E2']['provenance']['selector'] = '/elsewhere'
        def m_evidence_on_goal(g): nodes(g)['G1']['evidence_id'] = nodes(g)['E1']['evidence_id']
        def m_status_mismatch(g): nodes(g)['E1']['validation_status'] = 'verified_source'
        def m_duplicate_node(g): g['nodes'].append(copy.deepcopy(nodes(g)['A1']))

        mutations = [m_fake_evidence, m_goal_promoted, m_physical_strategy, m_bad_edge_type, m_dangling_edge,
                     m_cycle, m_interval_stretch, m_source_mismatch, m_evidence_on_goal, m_status_mismatch,
                     m_duplicate_node]
        self.assertIsNone(self._original_rejects(base, records))
        self.assertEqual(self._ours(req, {'object_id': 'widget_a', 'graph': base}), [])
        for mutate in mutations:
            with self.subTest(mutation=mutate.__name__):
                g = copy.deepcopy(base)
                mutate(g)
                original = self._original_rejects(g, records)
                ours = self._ours(req, {'object_id': 'widget_a', 'graph': g})
                self.assertIsNotNone(original, 'mutation should be invalid for the original validator')
                self.assertTrue(ours, f'original rejected ({original}) but the Critic found nothing')


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
