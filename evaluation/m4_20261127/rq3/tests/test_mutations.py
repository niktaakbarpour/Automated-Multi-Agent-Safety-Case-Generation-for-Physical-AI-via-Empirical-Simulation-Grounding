"""Tests for the RQ3 mutation benchmark (M4 task A2). CPU only, no model.

    PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq3/tests -p 'test_*.py' -v
"""
from pathlib import Path
import csv
import importlib.util
import json
import unittest

from critic import checks, contract as K, review
from critic.llm import RULE_ONLY_CATEGORIES
from drafter.argument_checks import prose_issues
from drafter.revision import invariants as V

RQ3 = Path(__file__).resolve().parents[1]
ROOT = RQ3.parents[2]
SPEC = importlib.util.spec_from_file_location('build_mutations', RQ3 / 'mutations' / 'build_mutations.py')
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def nodes(request):
    return {(g['object_id'], n['id']): n for g in request['argument_bundle']['graphs'] for n in g['graph']['nodes']}


class Benchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labels = {x['case_id']: x for x in load(RQ3 / 'mutations' / 'gold_labels.json')}
        cls.rows = {r['case_id']: r for r in csv.DictReader(open(RQ3 / 'MUTATION_MANIFEST.csv', encoding='utf-8'))}
        cls.cases = {c: load(RQ3 / 'mutations' / 'cases' / f'{c}.critic_request.json') for c in cls.labels}
        cls.parents = {k: load(ROOT / p['path']) for k, p in B.PARENTS.items()}
        cls.specs = {s['case_id']: s for s in B.SPECS}

    def test_saved_files_equal_a_fresh_build(self):
        for name, text in B.build().items():
            with self.subTest(name):
                self.assertEqual((RQ3 / 'mutations' / name).resolve().read_text(encoding='utf-8'), text)

    def test_counts_and_strata(self):
        counts = load(RQ3 / 'mutations' / 'BENCHMARK.json')['counts']
        self.assertEqual(counts, {'canonical_source_groups': 2, 'semantic_mutations': 8, 'clean_controls': 4,
                                  'validation_stratum': 3, 'by_operator': {'M1': 3, 'M2': 2, 'M3': 3}})
        self.assertEqual(len(self.cases), 15)
        self.assertEqual(load(RQ3 / 'mutations' / 'BENCHMARK.json')['independent_cases'], 0)

    def test_each_case_changes_only_what_it_says(self):
        for case_id, case in self.cases.items():
            spec, parent = self.specs[case_id], self.parents[self.specs[case_id]['parent']]
            with self.subTest(case_id):
                changed = {k for k in case if case[k] != parent[k]}
                expected = {'request_id', 'argument_bundle'} if 'node' in spec else {'request_id'}
                if spec.get('foreign'):
                    expected.add('evidence_package')
                self.assertEqual(changed, expected)
                self.assertEqual(case['request_id'], 'rq3-m4:' + case_id)
                before, after = nodes(parent), nodes(case)
                self.assertEqual(set(before), set(after))
                diff = [k for k in before if before[k] != after[k]]
                self.assertEqual(diff, [(spec['object'], spec['node'])] if 'node' in spec else [])
                if spec.get('foreign'):  # only one record is added; none is changed
                    self.assertEqual(case['evidence_package']['records'][:-1], parent['evidence_package']['records'])
                for key in ('evaluation_context', 'checker_assessments', 'retrieval_context'):
                    self.assertEqual(case[key], parent[key])

    def test_statement_changes_touch_only_the_statement(self):
        for case_id, spec in self.specs.items():
            if 'statement' not in spec:
                continue
            with self.subTest(case_id):
                before = nodes(self.parents[spec['parent']])[(spec['object'], spec['node'])]
                after = nodes(self.cases[case_id])[(spec['object'], spec['node'])]
                self.assertEqual({k for k in before if before[k] != after[k]}, {'statement'})
                self.assertEqual(prose_issues(after['statement'], 'x'), [])

    def test_the_re_pointed_citation_is_well_formed(self):
        case, parent = self.cases['P2-M2a'], self.parents['P2']
        node = nodes(case)[('vial_b', 'E2')]
        record = next(r for r in parent['evidence_package']['records'] if r['id'] == node['evidence_id'])
        self.assertEqual((record['object_id'], record['measurement_type']), ('vial_b', 'camera_reference'))
        self.assertEqual(node['statement'], nodes(parent)[('vial_b', 'E2')]['statement'])
        self.assertIn('Contact measurements', node['statement'])

    def test_m1a_is_the_saved_negative_control(self):
        control = load(ROOT / 'integration/fixtures/one_pass_20261113/artifacts/models/'
                              'critic.controlled-negative.request.json')
        self.assertEqual(self.cases['P1-M1a']['argument_bundle'], control['argument_bundle'])

    def test_semantic_cases_pass_input_validation_and_the_shared_gsn_validator(self):
        for case_id, case in self.cases.items():
            if self.labels[case_id]['stratum'] != 'semantic':
                continue
            with self.subTest(case_id):
                self.assertTrue(checks.run_all(case)[1]['input_valid'])
                self.assertEqual(V.gsn_issues(case, case['argument_bundle']), ([], []))

    def test_validation_cases_are_rejected_at_their_target(self):
        expected = {'P2-V1': 'EV-MISSING', 'P2-V2': 'EV-WRONG-OBJECT', 'P2-V3': 'EV-WRONG-EXECUTION'}
        for case_id, check_id in expected.items():
            with self.subTest(case_id):
                report = review(self.cases[case_id])
                self.assertEqual(report['review_status'], 'rejected_invalid_input')
                self.assertFalse(report['llm']['called'])
                self.assertIn((check_id, 'vial_b', 'E2'),
                              [(c['check_id'], c['object_id'], c['node_id']) for c in report['criticisms']])
                self.assertTrue(self.labels[case_id]['expected_validation_rejection'])

    def test_rule_only_channel(self):
        flagged = sorted(c for c, r in self.rows.items() if r['rule_only_flags_target'] == 'yes')
        self.assertEqual(flagged, ['P1-M1a', 'P2-M1c', 'P2-V1', 'P2-V2', 'P2-V3'])
        for case_id in ('P1-CC0', 'P1-CC1', 'P2-CC0', 'P2-CC1'):
            self.assertEqual(review(self.cases[case_id])['criticisms'], [], case_id)
        for case_id, row in self.rows.items():
            findings, _ = checks.run_all(self.cases[case_id])
            self.assertEqual(row['rule_only_findings'],
                             ';'.join(f"{f['check_id']}@{f['object_id']}:{f['node_id']}" for f in findings))

    def test_labels(self):
        for case_id, label in self.labels.items():
            with self.subTest(case_id):
                self.assertEqual(label['data_role'], 'development_only')
                self.assertIn('pending', label['review_status'])
                self.assertNotIn('independent oracle', label['review_status'])
                if label['case_type'] == 'clean_control':
                    self.assertEqual((label['expected_objection'], label['expected_location'],
                                      label['mutation_operator']), (False, None, None))
                else:
                    self.assertTrue(label['expected_objection'])
                    self.assertEqual(label['expected_location'],
                                     {'object_id': self.specs[case_id]['object'],
                                      'node_id': self.specs[case_id]['node']})
                if label['stratum'] == 'semantic' and label['case_type'] == 'mutation':
                    categories = set(label['acceptable_model_categories'])
                    self.assertTrue(categories)
                    self.assertFalse(categories & set(RULE_ONLY_CATEGORIES))

    def test_manifest_matches_cases_and_labels(self):
        self.assertEqual(list(self.rows), list(self.labels))
        for case_id, row in self.rows.items():
            with self.subTest(case_id):
                self.assertEqual(row['request_sha256'], K.digest(self.cases[case_id]))
                self.assertEqual(row['parent_request_sha256'], K.digest(self.parents[row['parent_id']]))
                self.assertEqual(row['expected_objection'], 'yes' if self.labels[case_id]['expected_objection']
                                 else 'no')
                self.assertTrue((ROOT / row['case_file']).exists())

    def test_blind_review_copies(self):
        key = load(RQ3 / 'mutations' / 'review' / 'REVIEW_KEY.json')
        semantic = sorted(c for c, l in self.labels.items() if l['stratum'] == 'semantic')
        self.assertEqual(sorted(key.values()), semantic)
        self.assertEqual(list(key), [f'R{i:02d}' for i in range(1, 13)])
        for name, case_id in key.items():
            copy = load(RQ3 / 'mutations' / 'review' / f'{name}.critic_request.json')
            self.assertEqual(copy['request_id'], 'rq3-review:' + name)
            self.assertNotIn(case_id, json.dumps(copy))
            copy['request_id'] = self.cases[case_id]['request_id']
            self.assertEqual(copy, self.cases[case_id])

    def test_parents_are_unchanged_fixtures(self):
        manifest = load(ROOT / 'integration/fixtures/one_pass_20261113/MANIFEST.json')
        fixture = ROOT / 'integration/fixtures/one_pass_20261113'
        import hashlib
        for artifact in manifest['artifacts']:
            self.assertEqual(hashlib.sha256((fixture / artifact['file']).read_bytes()).hexdigest(),
                             artifact['sha256'])
        self.assertEqual(self.parents['P2'], load(ROOT / 'critic/cases/case_c_correct_unresolved.json'))


if __name__ == '__main__':
    unittest.main()
