"""Synthetic pre-sampling roster constraints; no empirical/model results."""
from copy import deepcopy
import unittest
from jsonschema import Draft202012Validator
from drafter.generation import _serialize_plan
from drafter.mock_demo import _mock_provenance
from drafter.plan_schema import build_plan_schema
from drafter.validation import ContractError, validate_argument
from .test_generation import model_plan
from .test_input_profiles import registry_input


class OrderedPlanTests(unittest.TestCase):
    def test_arbitrary_configuration_order_and_rosters(self):
        for roster in (['zeta', 'alpha'], ['d', 'c', 'b', 'a'],
                       ['orange_juice_1', 'butter_1', 'milk_1', 'ketchup_1', 'cream_cheese_1']):
            with self.subTest(roster=roster):
                request = registry_input(objects=roster, records=False)
                before = deepcopy(request)
                plan = model_plan(request)
                Draft202012Validator(build_plan_schema(request)).validate(plan)
                bundle = _serialize_plan(plan, request, _mock_provenance(plan), mock=True)
                self.assertEqual(bundle['protected_objects'], roster)
                self.assertEqual([g['object_id'] for g in bundle['graphs']], roster)
                self.assertEqual(request, before)
                for g in bundle['graphs']:
                    for n in g['graph']['nodes']:
                        self.assertEqual(n['scope']['object_id'], g['object_id'])
                        self.assertEqual(n['scope']['interval'], request['monitoring_scope']['interval'])
                        self.assertIn('request_sha256', n['provenance'])

    def test_reordered_plan_rejected_without_mutation_by_schema_and_host(self):
        request = registry_input(objects=['zeta', 'alpha'], records=False)
        plan = model_plan(request)
        plan['graphs'].reverse()
        before = deepcopy(plan)
        self.assertFalse(Draft202012Validator(build_plan_schema(request)).is_valid(plan))
        with self.assertRaisesRegex(ContractError, 'plan_object_roster_or_order'):
            _serialize_plan(plan, request, _mock_provenance(plan), mock=True)
        self.assertEqual(plan, before)

    def test_missing_duplicate_extra_or_unknown_objects_rejected(self):
        request = registry_input(objects=['zeta', 'alpha'], records=False)
        schema = Draft202012Validator(build_plan_schema(request))
        base = model_plan(request)
        for kind in ['missing', 'duplicate', 'extra', 'unknown']:
            p = deepcopy(base)
            if kind == 'missing': p['graphs'].pop()
            elif kind == 'extra': p['graphs'].append(deepcopy(p['graphs'][0]))
            elif kind == 'duplicate': p['graphs'][1] = deepcopy(p['graphs'][0])
            else: p['graphs'][0]['object_id'] = 'unknown'
            with self.subTest(kind=kind): self.assertFalse(schema.is_valid(p))

    def test_position_binds_node_root_and_edge_namespaces(self):
        request = registry_input(objects=['zeta', 'alpha'], records=False)
        schema = Draft202012Validator(build_plan_schema(request))
        for field in ['root', 'node', 'source', 'target']:
            p = model_plan(request); g = p['graphs'][0]
            if field == 'root': g['root_id'] = 'alpha:G1'
            elif field == 'node': g['nodes'][0]['id'] = 'alpha:G1'
            else: g['edges'][0][field] = 'alpha:G1'
            with self.subTest(field=field): self.assertFalse(schema.is_valid(p))

    def test_exact_object_prefix_with_regex_metacharacter(self):
        request = registry_input(objects=['object.a', 'objectXa'], records=False)
        p = model_plan(request); v = Draft202012Validator(build_plan_schema(request))
        v.validate(p)
        p['graphs'][0]['nodes'][0]['id'] = 'objectXa:G1'
        self.assertFalse(v.is_valid(p))

    def test_object_specific_evidence_and_no_solution_for_empty_object(self):
        request = registry_input()
        p = model_plan(request); v = Draft202012Validator(build_plan_schema(request)); v.validate(p)
        solution = next(n for n in p['graphs'][0]['nodes'] if n['type'] == 'solution')
        leaked = deepcopy(solution); leaked['id'] = p['graphs'][1]['object_id'] + ':E9'
        p['graphs'][1]['nodes'].append(leaked)
        self.assertFalse(v.is_valid(p))
        with self.assertRaises(ContractError):
            _serialize_plan(p, request, _mock_provenance(p), mock=True)

    def test_reordered_configuration_keeps_original_evidence_owner(self):
        roster = ['butter_1', 'milk_1', 'orange_juice_1', 'ketchup_1', 'cream_cheese_1']
        request = registry_input(objects=roster)
        p = model_plan(request); v = Draft202012Validator(build_plan_schema(request));v.validate(p)
        solutions = [(g['object_id'], n['evidence_id']) for g in p['graphs'] for n in g['nodes'] if n['type']=='solution']
        self.assertTrue(solutions)
        records = {r['id']:r for r in request['evidence_package']['records']}
        for obj, key in solutions:self.assertEqual(records[key]['object_id'],obj)
        before=deepcopy(request)
        bundle=_serialize_plan(p,request,_mock_provenance(p),mock=True)
        for g in bundle['graphs']:
            for n in g['graph']['nodes']:
                if n['type']=='solution':self.assertEqual(n['provenance']['registry_record'],records[n['evidence_id']])
        self.assertEqual(request,before)

    def test_schema_creation_is_independent_and_does_not_change_configuration(self):
        request = registry_input();before=deepcopy(request)
        first=build_plan_schema(request);first['properties']['graphs']['prefixItems'][0]['properties']['object_id']['const']='tampered'
        second=build_plan_schema(request)
        self.assertEqual(request,before)
        Draft202012Validator(second).validate(model_plan(request))
