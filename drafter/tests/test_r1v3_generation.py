"""R1 v3 generation with scripted model replies, never a live model evaluation. CPU only.

    python3 -m unittest drafter.tests.test_r1v3_generation -v

Every model reply here is constructed test data and establishes no safety result. The admitted cases use the same
synthetic fixture as test_r1v3_profile (v3-marked record copies and a test-only admission contract).
"""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from drafter import r1v3_generation as G, r1v3_profile as P, validation as V
from drafter.argument_checks import solution_statement
from drafter.generation import generate_argument, render_review
from drafter.llm import FrozenLocalModelConfig, ModelDiscoveryResult
from evaluation.r1_v4.provenance import canonical, digest
from .test_generation import reply
from .test_llm import MODEL, configuration
from .test_r1v3_profile import TEST_CONTRACT, load_package


def model_plan(request, skip_evidence=()):
    """A constructed reply in the existing plan shape; cites every eligible record unless skipped."""
    eligible = set(request['evidence']['graph_eligible_evidence_ids'])
    records = request['source_package']['rag_source']['records']
    graphs = []
    for obj in request['requirement_configuration']['protected_objects']:
        p = obj + ':'
        nodes = [
            {'id': p + 'G1', 'type': 'goal', 'statement': f'R1 holds for {obj} across the declared saved frames.',
             'evidence_id': None, 'physical_claim': True},
            {'id': p + 'S1', 'type': 'strategy', 'statement': 'Argue over initial table support, then any fall from it.',
             'evidence_id': None, 'physical_claim': False},
            {'id': p + 'C1', 'type': 'context', 'statement': 'Saved frames 10 to 257 of the original execution, R1 v3 scope.',
             'evidence_id': None, 'physical_claim': False},
            {'id': p + 'U1', 'type': 'unresolved_claim',
             'statement': 'Initial support and any qualifying fall are not established by citable evidence here.',
             'evidence_id': None, 'physical_claim': True}]
        edges = [{'source': p + 'G1', 'target': p + 'S1', 'type': 'supported_by'},
                 {'source': p + 'G1', 'target': p + 'C1', 'type': 'in_context_of'},
                 {'source': p + 'S1', 'target': p + 'U1', 'type': 'supported_by'}]
        for index, record in enumerate(r for r in records if r['id'] in eligible and r['object_id'] == obj
                                       and obj not in skip_evidence):
            nodes.append({'id': f'{p}E{index + 1}', 'type': 'solution', 'statement': solution_statement(record),
                          'evidence_id': record['id'], 'physical_claim': False})
            edges.append({'source': p + 'U1', 'target': f'{p}E{index + 1}', 'type': 'supported_by'})
        graphs.append({'object_id': obj, 'root_id': p + 'G1', 'nodes': nodes, 'edges': edges})
    return {'graphs': graphs, 'summary': 'The argument leaves R1 open where no admitted assessment and citation exist.',
            'limitations': ['No source replay or physical checker was run by the Drafter.']}


class Base(unittest.TestCase):
    def setUp(self):
        self.config = FrozenLocalModelConfig.from_mapping(configuration(max_response_bytes=1048576))

    def run_plan(self, request, plan, calls=1):
        with patch('drafter.r1v3_generation.LocalModelClient') as constructor:
            client = constructor.return_value
            client.discover_models.return_value = ModelDiscoveryResult(
                status='ok', configured_model_available=True, model_ids=(MODEL,))
            client.complete.return_value = reply(plan)
            result = generate_argument(request, self.config)
            self.assertEqual(client.complete.call_count, calls)
            return result, client


class RealPackage(Base):
    @classmethod
    def setUpClass(cls):
        cls.request = P.build_request(load_package(), request_id='m4-e2e-original-r1v3')

    def test_accepted_argument_leaves_every_object_unresolved(self):
        result, _ = self.run_plan(self.request, model_plan(self.request))
        self.assertEqual(result['status'], 'accepted', result['diagnostics'])
        argument = result['argument']
        self.assertEqual(V.validate_argument(argument, self.request)['contract_status'], 'valid_output_contract')
        saved = json.loads(canonical(argument))
        self.assertEqual(V.validate_argument(saved, self.request)['contract_status'], 'valid_output_contract')
        conclusion = argument['argument_bundle']['execution_conclusion']
        self.assertEqual(set(conclusion['object_outcomes'].values()), {P.INSUFFICIENT})
        self.assertEqual(conclusion['claimed_outcome'], P.INSUFFICIENT)
        self.assertEqual(conclusion['statement'], P.CONCLUSION_UNRESOLVED)
        self.assertEqual(argument['generation_provenance']['backend'], 'local_llm')
        self.assertEqual(argument['generation_provenance']['prompt_version'], G.PROMPT_VERSION)
        for item in argument['argument_bundle']['graphs']:
            self.assertFalse(any(n['type'] == 'solution' for n in item['graph']['nodes']))
        text = render_review(result)
        self.assertIn('Execution outcome (host-decided, R1 aggregation): ' + P.INSUFFICIENT, text)
        self.assertIn('no admitted checker assessment backs a definite outcome', text)

    def test_model_input_states_status_and_has_no_reference_label(self):
        sent = G.model_input(self.request)
        self.assertEqual(P._forbidden_label_paths(sent), [])
        self.assertEqual(sent['eligible_evidence_catalogue'], [])
        self.assertEqual(sum(v['records'] for v in sent['context_only_evidence'].values()), 135)
        self.assertEqual(sent['checker_context']['admission']['state'], 'not_admitted')
        self.assertEqual(set(sent['host_outcomes'].values()), {P.INSUFFICIENT})
        self.assertEqual(len(sent['evidence_gaps']), len(self.request['evidence_gaps']))
        self.assertEqual(sent['request_sha256'], digest(self.request))

    def test_citing_a_v2_record_is_rejected_by_the_plan_schema(self):
        plan = model_plan(self.request)
        record = self.request['source_package']['rag_source']['records'][0]
        graph = next(g for g in plan['graphs'] if g['object_id'] == record['object_id'])
        p = record['object_id'] + ':'
        graph['nodes'].append({'id': p + 'E1', 'type': 'solution', 'statement': solution_statement(record),
                               'evidence_id': record['id'], 'physical_claim': False})
        graph['edges'].append({'source': p + 'U1', 'target': p + 'E1', 'type': 'supported_by'})
        result, _ = self.run_plan(self.request, plan)
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['argument']['validation']['output_schema'], 'failed')
        self.assertIsNone(result['argument']['argument_bundle'])
        V.validate_argument(result['argument'], self.request)  # a valid failure envelope

    def test_invalid_request_calls_no_model(self):
        request = deepcopy(self.request)
        request['evidence']['graph_eligible_evidence_ids'] = [request['evidence']['record_ids'][0]]
        with patch('drafter.r1v3_generation.LocalModelClient') as constructor:
            result = generate_argument(request, self.config)
            constructor.assert_not_called()
        self.assertEqual((result['status'], result['failure_stage'], result['argument']), ('rejected', 'input', None))

    def test_unavailable_model_fails_without_completion(self):
        with patch('drafter.r1v3_generation.LocalModelClient') as constructor:
            constructor.return_value.discover_models.return_value = ModelDiscoveryResult(
                status='ok', configured_model_available=False, model_ids=('another-model',))
            result = generate_argument(self.request, self.config)
            constructor.return_value.complete.assert_not_called()
        self.assertEqual((result['status'], result['failure_stage']), ('failed', 'discovery'))
        V.validate_argument(result['argument'], self.request)



def without_relaxed_bounds(value):
    """The full schema with exactly the bounds the decoder schema drops removed, computed independently."""
    if isinstance(value, list):
        return [without_relaxed_bounds(v) for v in value]
    if not isinstance(value, dict):
        return value
    out = {k: without_relaxed_bounds(v) for k, v in value.items()
           if not (k == 'maxLength' and value.get('type') == 'string')
           and not (k in ('minItems', 'maxItems') and 'items' in value and 'prefixItems' not in value)}
    if isinstance(out.get('pattern'), str):
        out['pattern'] = out['pattern'].replace('[A-Za-z0-9_.:-]{1,128}$', '[A-Za-z0-9_.:-]+$')
    return out


class DecoderSchema(Base):
    """Regression: Outlines timed out (60 s) compiling the full plan schema. The server gets a schema without the
    counted-repetition bounds; the host still validates every reply against the full schema."""

    @classmethod
    def setUpClass(cls):
        cls.request = P.build_request(load_package(), request_id='m4-e2e-original-r1v3')
        cls.full = G.plan_schema(cls.request)
        cls.decoding = G.decoder_schema(cls.full)

    def test_only_the_named_bounds_are_dropped(self):
        self.assertEqual(self.decoding, without_relaxed_bounds(self.full))
        self.assertNotIn('maxLength', json.dumps(self.decoding))
        self.assertEqual(self.decoding['$defs']['text'], {'type': 'string', 'minLength': 8})
        graphs = self.decoding['properties']['graphs']
        self.assertEqual((graphs['minItems'], graphs['maxItems'], graphs['items']), (5, 5, False))
        self.assertEqual([g['properties']['object_id'] for g in graphs['prefixItems']],
                         [{'const': o} for o in self.request['requirement_configuration']['protected_objects']])
        self.assertEqual(json.dumps(self.full).count('"pattern"'), json.dumps(self.decoding).count('"pattern"'))
        self.assertNotIn('{1,128}', json.dumps(self.decoding))
        self.assertIn('maxLength', json.dumps(self.full))  # the full schema itself is unchanged
        self.assertIn('{1,128}', json.dumps(self.full))

    def test_server_gets_the_decoder_schema(self):
        result, client = self.run_plan(self.request, model_plan(self.request))
        self.assertEqual(result['status'], 'accepted', result['diagnostics'])
        self.assertEqual(client.complete.call_args.args[1], self.decoding)
        self.assertEqual(result['trace']['json_schema'], self.decoding)
        self.assertEqual(result['trace']['validation_schema_sha256'], digest(self.full))

    def test_replies_breaking_a_dropped_bound_are_rejected(self):
        def changed(edit):
            plan = model_plan(self.request)
            edit(plan)
            return plan
        long_text = 'The object stays supported. ' * 60  # over 1600 characters

        def many_nodes(plan):
            g = plan['graphs'][0]
            p = g['object_id'] + ':'
            for i in range(21):
                g['nodes'].append({'id': f'{p}C{i + 2}', 'type': 'context', 'evidence_id': None,
                                   'physical_claim': False, 'statement': f'Context note number {i + 2} for the window.'})
        cases = {
            'statement over maxLength': lambda p: p['graphs'][0]['nodes'][0].update(statement=long_text),
            'summary over maxLength': lambda p: p.update(summary=long_text),
            'more than 24 nodes': many_nodes,
            'fewer than 4 nodes': lambda p: p['graphs'][1].update(nodes=p['graphs'][1]['nodes'][:3]),
            'fewer than 2 edges': lambda p: p['graphs'][2].update(edges=p['graphs'][2]['edges'][:1]),
            'no limitations': lambda p: p.update(limitations=[]),
            'node ID over 128 characters': lambda p: p['graphs'][0]['nodes'][2].update(
                id=p['graphs'][0]['object_id'] + ':' + 'C' * 129),
        }
        for name, edit in cases.items():
            plan = changed(edit)
            self.assertTrue(Draft202012Validator(self.decoding).is_valid(plan), name)  # the server could emit it
            result, _ = self.run_plan(self.request, plan)
            self.assertEqual(result['status'], 'rejected', name)
            self.assertEqual(result['argument']['validation']['output_schema'], 'failed', name)
            self.assertIsNone(result['argument']['argument_bundle'], name)

class AdmittedFixture(Base):
    @classmethod
    def setUpClass(cls):
        package = load_package()
        records = package['rag_source']['records']
        for obj in package['execution']['protected_objects']:
            record = deepcopy(next(r for r in records if r['object_id'] == obj))
            record.update(requirement_version=P.REQUIREMENT_VERSION, id='ev:test-fixture-v3-' + obj)
            records.append(record)
        package['rag_source']['record_count_included'] = len(records)
        P.ADMISSION_VERIFIERS[TEST_CONTRACT] = lambda request: []
        cls.request = P.build_request(package, request_id='test-fixture-admitted', test_fixture=True,
                                      admission={'state': 'admitted', 'contract': TEST_CONTRACT,
                                                 'reason': 'Test-only admission inside a unit test.'})

    @classmethod
    def tearDownClass(cls):
        P.ADMISSION_VERIFIERS.pop(TEST_CONTRACT, None)

    def test_host_records_backed_outcomes(self):
        result, _ = self.run_plan(self.request, model_plan(self.request))
        self.assertEqual(result['status'], 'accepted', result['diagnostics'])
        conclusion = result['argument']['argument_bundle']['execution_conclusion']
        expected = {a['object_id']: a['classification'] for a in self.request['checker_context']['assessments']}
        self.assertEqual(conclusion['object_outcomes'], expected)
        self.assertEqual(G.model_input(self.request)['host_outcomes'], expected)
        for obj, back in conclusion['outcome_backing'].items():
            self.assertEqual(back['citations'], ['ev:test-fixture-v3-' + obj])
            self.assertEqual(back['checker_assessment']['admission_contract'], TEST_CONTRACT)
        self.assertEqual(V.validate_argument(result['argument'], self.request)['contract_status'],
                         'valid_output_contract')
        self.assertIn('from the admitted checker assessment', render_review(result))
        saved = json.loads(canonical(result['argument']))  # the CLI writes canonical JSON with sorted keys
        self.assertEqual(V.validate_argument(saved, self.request)['contract_status'], 'valid_output_contract')

    def test_plan_that_omits_available_evidence_is_rejected(self):
        result, _ = self.run_plan(self.request, model_plan(self.request, skip_evidence=('milk_1',)))
        self.assertEqual(result['status'], 'rejected')
        self.assertIsNone(result['argument']['argument_bundle'])
        self.assertTrue(any('milk_1' in d['code'] or 'plan_schema' in d['code'] for d in result['diagnostics']),
                        result['diagnostics'])


if __name__ == '__main__':
    unittest.main()
