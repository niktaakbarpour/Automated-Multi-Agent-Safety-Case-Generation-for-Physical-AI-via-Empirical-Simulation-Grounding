"""Regression boundaries from the independent PR18 audit; synthetic inputs only."""
import copy
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

from critic import review, llm as L, assessments as A, contract as K
from critic import phase5_request
from critic.cases import build_cases as B, phase5 as P
from critic.tests.test_critic import load, flagged, checker_request, CASE_D, CASE_E, e_request
from evaluation.r1_v4 import fixtures as F
from evaluation.r1_v4.runtime import assess


class Spy(L.ScriptedLLM):
    def __init__(self, reply='{"findings": []}'):
        super().__init__(reply)
        self.calls = 0

    def complete(self, *args):
        self.calls += 1
        return super().complete(*args)


def objection(req, node='G1', explanation=None):
    oid = req['evaluation_context']['protected_objects'][0]
    rid = next(r['id'] for r in req['evidence_package']['records']
               if r['object_id'] == oid and r['measurement_type'] == 'contact')
    return {'object_id': oid, 'node_id': node, 'category': 'C09', 'severity': 'high',
            'explanation': explanation or 'The wording may ignore measurement uncertainty.',
            'evidence_ids': [rid], 'suggested_action': 'Review the stated inference and retain uncertainty.'}


class CheckerReplay(unittest.TestCase):
    def assert_refused(self, req):
        spy = Spy()
        r = review(req, spy)
        self.assertEqual((r['review_status'], spy.calls), ('rejected_invalid_input', 0))
        self.assertFalse(any(x['admitted'] for x in r['checker_admission']))
        return r

    def test_missing_source_input_is_not_a_verified_result(self):
        q = load(CASE_D)
        del q['checker_assessments'][0]['input_bundle']
        r = self.assert_refused(q)
        self.assertTrue(flagged(r, check_id='CHK-REPLAY'))

    def test_original_rehashed_semantic_counterexamples(self):
        def rec(r, name='object_00_fall'):
            return next(x for x in r['evidence_records'] if x['id'] == name)
        def row(r):
            return next(x for x in r['evidence_admission'] if x['evidence_id'] == 'object_00_fall')
        mutations = {
            'self cycle': lambda r: rec(r)['dependencies'].append('object_00_fall'),
            'missing foundations': lambda r: (rec(r).update(dependencies=[]),
                                                row(r).update(dependencies=['object_00_fall'])),
            'length unit': lambda r: rec(r)['frame'].update(length_unit='km'),
            'time unit': lambda r: rec(r)['frame'].update(time_unit='ms'),
            'handedness': lambda r: rec(r)['frame'].update(handedness='left_handed'),
            'missing source hash': lambda r: row(r).update(source_hash=None),
            'fall predicate': lambda r: rec(r)['payload'].update(origin='F'),
            'temporal uncertainty': lambda r: rec(r)['uncertainty'].update(temporal=5),
            'negative uncertainty': lambda r: rec(r)['uncertainty'].update(temporal=-1),
            'coverage': lambda r: r['object_assessments'][1]['coverage'].update(
                requested=[], available=[], admitted=[], negative=[], dependencies=[]),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                q = load(CASE_D)
                mutate(q['checker_assessments'][0]['result'])
                q['checker_assessments'][0] = A.rehash(q['checker_assessments'][0])
                self.assertTrue(flagged(self.assert_refused(q), check_id='CHK-REPLAY'))

    def test_resealed_invalid_sources_cannot_be_promoted(self):
        mutations = {
            'cycle': lambda r: r['dependencies'].append(r['id']),
            'foundations': lambda r: r.update(dependencies=[]),
            'frame': lambda r: r['frame'].update(length_unit='km'),
            'predicate': lambda r: r['payload'].update(origin='F'),
            'uncertainty': lambda r: r['uncertainty'].update(temporal=2),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                source = F.make_bundle(('V', 'N', 'NA'))
                mutate(next(r for r in source['evidence']['records'] if r['id'] == 'object_00_fall'))
                F.seal(source)
                expected = assess(source)
                fall = next(x for x in expected['evidence_admission'] if x['evidence_id'] == 'object_00_fall')
                self.assertNotEqual(fall['status'], 'verified')  # authoritative independent reference
                forged = copy.deepcopy(expected)
                for x in forged['evidence_admission']:
                    x.update(status='verified', reasons=[])
                forged['admitted_evidence_ids'] = sorted(x['id'] for x in forged['evidence_records'])
                forged['rejected_evidence'] = []
                forged['object_assessments'] = copy.deepcopy(B.checker_item()['result']['object_assessments'])
                item = {'configuration': source['configuration'], 'input_bundle': source, 'result': forged}
                item = A.rehash(item)
                q = checker_request(item)
                q['evaluation_context']['r1_configuration'] = source['configuration']
                q['evaluation_context']['r1_configuration_sha256'] = K.digest(source['configuration'])
                r = self.assert_refused(q)
                text = ' '.join(x['explanation'] for x in r['criticisms'])
                self.assertIn('CHK-REPLAY', {x['check_id'] for x in r['criticisms']})
                self.assertTrue(any(reason in text for reason in fall['reasons']))

    def test_genuine_checker_results_in_both_directions(self):
        for states in [('V', 'N', 'NA'), ('N', 'ABSENT', 'IC'), ('U', 'V', 'N')]:
            with self.subTest(states=states):
                source = F.make_bundle(states)
                item = {'configuration': source['configuration'], 'input_bundle': source, 'result': assess(source)}
                from critic.checker_replay import problems
                self.assertEqual(problems(item), [])

    def test_genuine_conflicting_results_do_not_erase_a_violation(self):
        # Both results really run the checker, with the same source-bound config.
        # Different explicit source selections yield contradictory analytical
        # assessments. No checker result or admission row is hand-edited.
        source = F.make_bundle(('V', 'N', 'NA'))
        cfg = source['configuration']
        cells = [x['id'] for x in source['artifacts']['synthetic:domain']['cells']]
        source['evidence']['records'].append(F.record(
            cfg, 'object_00_alternative_negative', 'object_00', 'static_negative',
            dependencies=['object_00_support'], interval=[0, 2], cells=cells,
            payload={'method': 'exact_static_constraint'}))
        F.seal(source)
        items = []
        for excluded in ['object_00_alternative_negative', 'object_00_fall']:
            selected = copy.deepcopy(source)
            selected['evidence']['records'] = [x for x in selected['evidence']['records'] if x['id'] != excluded]
            items.append({'configuration': cfg, 'input_bundle': selected, 'result': assess(selected)})
        q = checker_request(*items, claims={'object_00': K.NO_VIOLATION})
        q['evaluation_context'].update(r1_configuration=cfg, r1_configuration_sha256=K.digest(cfg))
        q['argument_bundle']['execution_conclusion']['claimed_outcome'] = K.NO_VIOLATION
        r = review(q)
        self.assertEqual(r['review_status'], 'completed')
        self.assertEqual(sum(a['admitted'] for a in r['checker_admission']), 6)
        self.assertTrue(flagged(r, check_id='CONCL-CONFLICT'))
        self.assertTrue(any(A.assessment_id(items[0]['result'], 'object_00') in f['evidence_ids']
                            for f in flagged(r, check_id='CONCL-CONTRADICTION')))
        self.assertNotEqual(r['summary']['accepted_execution_outcome'], K.NO_VIOLATION)

    def test_invalid_result_cannot_support_c07(self):
        q = load(CASE_D)
        q['checker_assessments'][0]['result']['evidence_records'][0]['producer'] = 'forged'
        q['checker_assessments'][0] = A.rehash(q['checker_assessments'][0])
        self.assert_refused(q)

    def test_source_hash_mismatch_is_diagnostic(self):
        q = load(CASE_D)
        q['checker_assessments'][0]['input_bundle']['artifacts']['synthetic:model']['complete_roster'] = False
        self.assertTrue(flagged(self.assert_refused(q), check_id='CHK-REPLAY'))


class C09Grounding(unittest.TestCase):
    def run_finding(self, q, f):
        return review(q, Spy(json.dumps({'findings': [f]})))

    def test_four_original_false_negatives_and_proposed_variation(self):
        statement = ('These uncertain contact measurements establish initial load-bearing support with exact '
                     'timing; uncertainty can be ignored.')
        for node in ['G1', 'U1', 'D1', None]:
            for status in ['unresolved', 'proposed']:
                with self.subTest(node=node, status=status):
                    q = load('case_c_correct_unresolved.json')
                    if node:
                        target = next(n for n in q['argument_bundle']['graphs'][0]['graph']['nodes'] if n['id'] == node)
                        target.update(statement=statement, validation_status=status, physical_claim=status == 'unresolved' and target['physical_claim'])
                    else:
                        q['argument_bundle']['execution_conclusion']['statement'] = statement
                    f = objection(q, node, f'The statement "{statement}" treats uncertain contact as exact support.')
                    r = self.run_finding(q, f)
                    self.assertEqual(r['llm']['accepted'], 1)
                    self.assertTrue(flagged(r, category='C09')[0]['human_review_required'])

    def test_original_case_c_objection_is_not_promoted(self):
        for oid in ['widget_a', 'vial_b', 'carton_c']:
            q = load('case_c_correct_unresolved.json')
            f = objection(q, 'U1', "The statement 'contact is geometric' fails to propagate uncertainty to the final conclusion.")
            f['object_id'] = oid
            f['evidence_ids'] = [next(x['id'] for x in q['evidence_package']['records']
                                      if x['object_id'] == oid and x['measurement_type'] == 'contact')]
            r = self.run_finding(q, f)
            self.assertEqual((r['llm']['accepted'], r['llm']['rejected']), (0, 1))
            self.assertTrue(any('C09_UNRESOLVED' in x for x in r['unresolved_concerns']))

    def test_safe_prose_and_other_unsupported_inferences(self):
        for text in ['The object is safe despite uncertain measurements.',
                     'Geometric contact establishes verified load-bearing support.',
                     'No violations were recorded, which proves the object was safe.']:
            q = load('case_c_correct_unresolved.json')
            next(n for n in q['argument_bundle']['graphs'][0]['graph']['nodes'] if n['id'] == 'U1')['statement'] = text
            self.assertEqual(self.run_finding(q, objection(q, 'U1', f'"{text}" overstates the evidence.'))['llm']['accepted'], 1)

    def test_strategy_and_solution_are_not_exempted_by_cautious_conclusion(self):
        for node in ['S1', 'E2']:
            q = load('case_c_correct_unresolved.json')
            self.assertEqual(self.run_finding(q, objection(q, node))['llm']['accepted'], 1)

    def test_ambiguous_unanchored_objection_is_retained_for_review(self):
        q = load('case_c_correct_unresolved.json')
        r = self.run_finding(q, objection(q))
        self.assertEqual(r['llm']['accepted'], 0)
        self.assertTrue(any('human review' in x for x in r['unresolved_concerns']))
        self.assertNotIn('has nothing to object to', r['rejected_llm_findings'][0]['reason'])

    def test_original_unquoted_execution_counterexample_is_not_suppressed(self):
        q = load('case_c_correct_unresolved.json')
        q['argument_bundle']['execution_conclusion']['statement'] = (
            'The contact timings are exact and support is established with certainty, '
            'irrespective of the recorded uncertainty.')
        r = self.run_finding(q, objection(q, None, 'Synthetic citation-based objection.'))
        self.assertEqual(r['llm']['accepted'], 1)
        q['argument_bundle']['execution_conclusion']['statement'] = (
            'Initial support is unresolved, but the object is safe.')
        self.assertEqual(self.run_finding(q, objection(q, None))['llm']['accepted'], 1)


class Phase5PublicGuards(unittest.TestCase):
    def test_aggregate_budget_cannot_be_claimed_as_complete(self):
        scope = P.scope_of('synthetic-execution', 'synthetic-task', B.VARIANT)
        obligations = [P.obligation(f'c{i}', 'camera_references', scope, frames=(0, 4095)) for i in range(5)]
        q = P.request(scope, obligations)
        results = {o['id']: ('AVAILABLE', [P.reference_item(scope, 'camera_references',
                   '/frames/000000/camera', {'saved_frame_index': 0})], 'synthetic') for o in obligations}
        bundle = P.evaluated(q, results)
        r = review(e_request(P.entry(q, bundle)))
        self.assertEqual(r['review_status'], 'rejected_invalid_input')
        self.assertTrue(flagged(r, check_id='RET-QUERY'))
        # No returned window implies no proof that frames() selected that range.
        unavailable = P.evaluated(q, {})
        self.assertIsNone(phase5_request.returned_window_refusal(q, unavailable))

    def test_explicit_record_source_and_object_bindings(self):
        from critic.tests.test_critic import one_obligation, e_scope
        scope = e_scope()
        for field, wrong in [('record_id', 'channel:forged'), ('source_sha256', '0' * 64)]:
            with self.subTest(field=field):
                o = P.obligation('j', 'raw.robot0_joint_pos', scope, frames=(0, 1), **{field: wrong})
                item = P.channel_item(scope, 'raw.robot0_joint_pos', (0, 1))
                r = review(e_request(one_obligation(o, ('AVAILABLE', [item], 'ok'))))
                self.assertEqual(r['review_status'], 'rejected_invalid_input')
                self.assertTrue(flagged(r, check_id='RET-ITEM'))
        o = P.obligation('g', 'geometry_identity', scope, object_id='object_00')
        item = P.reference_item(scope, 'geometry_identity', '/body_names', {'object_id': 'object_01'})
        r = review(e_request(one_obligation(o, ('AVAILABLE', [item], 'ok'))))
        self.assertEqual(r['review_status'], 'rejected_invalid_input')

    def test_case_e_runs_the_entire_public_prepare_on_synthetic_metadata(self):
        # The original public method, unmodified; only its catalogue/channel I/O
        # is an explicitly synthetic fixture. No frozen data/source is invented.
        import math
        from jsonschema import Draft202012Validator
        from critic import schema as S
        from evaluation.r1_v4.rag_evidence_database.final_phase5_release.config import (
            REGISTRY, TEMPORAL_FAMILIES, CHANNELS, PROVENANCE_SCOPE)
        tree = ast.parse((S.PHASE5 / 'api.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'StructuredRetriever')
        fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'prepare')
        error = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'QueryError')
        namespace = dict(math=math, json=json, REGISTRY=REGISTRY, TEMPORAL_FAMILIES=TEMPORAL_FAMILIES,
                         CHANNELS=CHANNELS, PROVENANCE_SCOPE=PROVENANCE_SCOPE)
        exec(compile(ast.Module(body=[error, fn], type_ignores=[]), 'frozen-public-prepare', 'exec'), namespace)
        q = B.case_e()['structured_evidence'][0]['request']
        scope = {k: q[k] for k in ['execution_id', 'task_id', 'variant_id']}
        catalogue = dict(scope, objects={o: {} for o in ['object_00', 'object_01', 'object_02']})
        def execute(sql, params):
            if 'catalogue' in sql:
                row = (json.dumps(catalogue),)
            else:
                row = (json.dumps({'id': 'channel:synthetic', 'source_sha256': '0' * 64,
                                   'object_id': 'synthetic-robot'}), json.dumps({'components': []}))
            return SimpleNamespace(fetchone=lambda: row)
        db = SimpleNamespace(execute=execute)
        adapter = SimpleNamespace(validator=Draft202012Validator(S.load('phase5_query')),
                                  backend=SimpleNamespace(catalogue=db), store=SimpleNamespace(db=db))
        self.assertEqual(namespace['prepare'](adapter, q)[1], scope)
        forged = copy.deepcopy(q)
        next(o for o in forged['obligations'] if o['family'] == 'contact_references')['object_id'] = 'object_00'
        with self.assertRaises(namespace['QueryError']) as failure:
            namespace['prepare'](adapter, forged)
        self.assertEqual(failure.exception.status, 'UNSUPPORTED')

    def test_corrected_case_e_has_no_unsupported_filters(self):
        q = B.case_e()['structured_evidence'][0]['request']
        self.assertIsNone(phase5_request.refusal(q))
        for o in q['obligations']:
            if o['family'] != 'geometry_identity':
                self.assertNotIn('object_id', o)

    def test_all_nonchannel_metadata_filters_use_public_rules(self):
        q = copy.deepcopy(B.case_e()['structured_evidence'][0]['request'])
        for family in ['contact_references', 'camera_references', 'execution_metadata', 'source_provenance',
                       'recorded_time', 'action_metadata', 'inference_metadata']:
            o = P.obligation('bad', family, P.scope_of(q['execution_id'], q['task_id'], q['variant_id']),
                             object_id='object_00')
            if family in K.PHASE5_TEMPORAL:
                o['selector'] = {'kind': 'frames', 'start': 0, 'end': 1}
            q['obligations'] = [o]
            with self.subTest(family=family):
                self.assertEqual(phase5_request.refusal(q)[0], 'UNSUPPORTED')

    def test_unsupported_request_cannot_claim_complete(self):
        q = load(CASE_E)
        entry = q['structured_evidence'][0]
        o = next(x for x in entry['request']['obligations'] if x['family'] == 'contact_references')
        o['object_id'] = 'object_00'
        entry['bundle']['query_id'] = 'query:' + K.digest(entry['request'])
        entry['bundle']['requested_obligations'] = copy.deepcopy(entry['request']['obligations'])
        next(g for g in entry['bundle']['groups'] if g['obligation_id'] == o['id'])['request_digest'] = K.digest(o)
        spy = Spy()
        r = review(q, spy)
        self.assertEqual((r['review_status'], spy.calls), ('rejected_invalid_input', 0))
        self.assertTrue(flagged(r, check_id='RET-QUERY'))

    def test_public_assurance_and_selector_boundaries(self):
        q = B.case_e()['structured_evidence'][0]['request']
        for mutate in [lambda x: x['provenance'].update(scope='invented'),
                       lambda x: x['provenance'].update(level='release_graph'),
                       lambda x: [o.update(mandatory=False) for o in x['obligations']],
                       lambda x: x['obligations'][1]['selector'].update(end=4096),
                       lambda x: x['obligations'][1].update(interpretation='verified_physical')]:
            v = copy.deepcopy(q)
            mutate(v)
            self.assertIsNotNone(phase5_request.refusal(v))


class ModelBoundary(unittest.TestCase):
    def test_cyclic_python_input_rejects_but_shared_json_values_do_not(self):
        from critic import checks
        shared = {'metadata': [1, 2]}
        self.assertEqual(checks.nonstandard_json([shared, shared]), [])
        q = load('case_c_correct_unresolved.json')
        provenance = q['argument_bundle']['graphs'][0]['graph']['nodes'][0]['provenance']
        provenance['cycle'] = provenance
        spy = Spy()
        r = review(q, spy)
        self.assertEqual((r['review_status'], spy.calls), ('rejected_invalid_input', 0))
        json.dumps(r, allow_nan=False)

    def test_cli_nonfinite_reply_is_a_failed_model_step_with_strict_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'reply.txt'
            p.write_text('{"findings":[{"category":"C09","explanation":NaN}]}')
            c = subprocess.run([sys.executable, '-m', 'critic', '--request',
                                str(B.HERE / 'case_c_correct_unresolved.json'), '--backend', 'scripted',
                                '--scripted-reply', str(p)], capture_output=True, text=True)
            self.assertEqual(c.returncode, 4)
            result = json.loads(c.stdout, parse_constant=lambda x: self.fail(x))
            self.assertEqual(result['review_status'], 'completed_llm_failed')
            self.assertNotIn('Traceback', c.stderr)

    def test_nonfinite_and_overflowing_json_never_enter_reports(self):
        for token in ['NaN', 'Infinity', '-Infinity', '1e9999', '-1e9999']:
            for location in ['explanation', 'unknown']:
                with self.subTest(token=token, location=location):
                    reply = '{"findings":[{"category":"C09","' + location + '":' + token + '}]}'
                    r = review(load('case_c_correct_unresolved.json'), Spy(reply))
                    self.assertEqual(r['review_status'], 'completed_llm_failed')
                    self.assertIn('numeric value', r['llm']['error'])
                    self.assertEqual(r['rejected_llm_findings'], [])
                    json.dumps(r, allow_nan=False)
                    self.assertIn(token, r['llm']['raw_response'])

    def test_alias_validation_and_exact_matching(self):
        for aliases in [[''], ['  '], ['\t\n'], [' valid'], [None], [{}], 'alias']:
            with self.subTest(aliases=aliases):
                with self.assertRaises(ValueError):
                    L.OpenAICompatibleLLM(model='selected', accepted_models=aliases)
        client = L.OpenAICompatibleLLM(model='selected', accepted_models=['alias', 'alias'])
        self.assertEqual(client.accepted_models, ['alias', 'selected'])
        for name, valid in [('selected', True), ('alias', True), ('other', False), ('', False), (' ', False), (None, False)]:
            self.assertEqual(client.response_problem({'model': name, 'finish_reason': 'stop'}) is None, valid)

    def test_cli_empty_alias_is_an_argument_error(self):
        p = subprocess.run([sys.executable, '-m', 'critic', '--request', str(B.HERE / CASE_D),
                            '--backend', 'openai', '--model', 'selected', '--accept-model', ' '],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn('Traceback', p.stderr)

    def test_trace_is_a_deep_snapshot(self):
        extra = {'seed': 9, 'options': {'nested': [1, 2]}}
        client = L.OpenAICompatibleLLM(model='selected', api_key='DO_NOT_RECORD', extra_body=extra,
                                      accepted_models=['alias'])
        q = load('case_c_correct_unresolved.json')
        text = '{"findings": []}'
        metadata = {'id': 'test', 'model': 'selected', 'finish_reason': 'stop', 'usage': {}}
        with mock.patch.object(client, 'call', return_value=(text, metadata)):
            r = review(q, client)
        saved = json.dumps(r, sort_keys=True, allow_nan=False)
        extra['options']['nested'].append(3)
        client.extra_body['options']['nested'].append(4)
        client.extra_body['seed'] = 99
        client.accepted_models.append('later')
        metadata['model'] = 'later'
        metadata['usage']['later'] = 1
        self.assertEqual(json.dumps(r, sort_keys=True, allow_nan=False), saved)
        self.assertEqual(r['llm']['settings']['extra_body']['seed'], 9)
        self.assertEqual(r['llm']['response_sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(r['llm']['request_sha256'], K.digest(q))
        self.assertNotIn('DO_NOT_RECORD', saved)

    def test_returned_report_does_not_alias_request_provenance(self):
        q = load(CASE_E)
        r = review(q)
        original = json.dumps(r, sort_keys=True)
        q['structured_evidence'][0]['bundle']['limitations'].append('later mutation')
        q['structured_evidence'][0]['bundle']['assurance_status']['requested'] = 'later mutation'
        self.assertEqual(json.dumps(r, sort_keys=True), original)

    def test_core_wire_fields_cannot_hide_in_extra_body(self):
        for key in ['model', 'messages', 'max_tokens', 'temperature', 'api_key', 'authorization', 'headers']:
            with self.assertRaises(ValueError):
                L.OpenAICompatibleLLM(model='selected', extra_body={key: 'override'})
        client = L.OpenAICompatibleLLM(model='selected')
        client.extra_body['model'] = 'later-override'
        with self.assertRaises(ValueError):
            client.settings()
        with self.assertRaises(ValueError):
            client.call('system', 'user')

    def test_url_authentication_is_not_in_settings(self):
        client = L.OpenAICompatibleLLM(model='selected',
                                      base_url='http://user:PASS@localhost/v1?api_key=SECRET#PRIVATE')
        self.assertEqual(client.settings()['base_url'], 'http://localhost/v1')
