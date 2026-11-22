"""Tests for the RQ3 T/R/C experiment tooling (M4 task A3). CPU only, no model.

    PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq3/tests -p 'test_*.py' -v

The dry run at the end feeds fixed (scripted) replies through run_batch.py and score.py. Those replies are test
inputs written to exercise each scoring path; they are not model results.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import csv
import json
import sys
import tempfile
import unittest

from critic import checks, llm as L

RQ3 = Path(__file__).resolve().parents[1]
ROOT = RQ3.parents[2]
EXP = RQ3 / 'experiment'
sys.path.insert(0, str(EXP))
import build_batch as BB  # noqa: E402
import conditions as CND  # noqa: E402
import run_batch as RB  # noqa: E402
import score as SC  # noqa: E402
import settings as S  # noqa: E402

SAVED_REPORT = ROOT / 'integration/fixtures/one_pass_20261113/artifacts/models/critic.qwen.report.json'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def csv_rows(path):
    with open(path, encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def view(user):
    assert user.startswith(CND.USER_PREFIX)
    return json.loads(user[len(CND.USER_PREFIX):])


class Capture(L.ScriptedLLM):
    """Records what critic.llm.run would send to a model."""
    def complete(self, system, user):
        self.sent = (system, user)
        return '{"findings": []}'


class Batch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary, cls.system, cls.requests = RB.load_batch(EXP / 'batch')
        cls.labels = {x['case_id']: x for x in load(RQ3 / 'mutations' / 'gold_labels.json')}
        cls.manifest = {r['case_id']: r for r in csv_rows(RQ3 / 'MUTATION_MANIFEST.csv')}
        cls.cases = {c: load(ROOT / cls.manifest[c]['case_file']) for c in {r['case_id'] for r in cls.requests}}

    def test_saved_batch_equals_a_fresh_build(self):
        for name, text in BB.build().items():
            self.assertEqual((EXP / name).read_text(encoding='utf-8'), text, name)

    def test_every_semantic_case_in_every_condition_and_repeat(self):
        semantic = [c for c, r in self.manifest.items() if r['stratum'] == 'semantic']
        expected = {f'{c}:{k}:r{n}' for c in semantic for k in CND.CONDITIONS for n in range(1, S.REPEATS + 1)}
        self.assertEqual({r['run_id'] for r in self.requests}, expected)
        self.assertEqual(len(self.requests), len(expected))
        self.assertFalse({r['case_id'] for r in self.requests} & {c for c, r in self.manifest.items()
                                                                  if r['stratum'] != 'semantic'})
        self.assertEqual(self.summary['independent_cases'], 0)
        self.assertFalse(self.summary['model_sees_rule_findings'])

    def test_manifest_rows_match_the_requests(self):
        rows = csv_rows(RQ3 / 'MATCHED_RUN_MANIFEST.csv')
        self.assertEqual([r['run_id'] for r in rows], [r['run_id'] for r in self.requests])
        for row, request in zip(rows, self.requests):
            self.assertEqual(row['user_sha256'], request['user_sha256'])
            self.assertEqual(row['parent_group_id'], self.labels[request['case_id']]['parent_group_id'])

    def test_repeats_send_identical_inputs(self):
        users = {}
        for r in self.requests:
            users.setdefault((r['case_id'], r['condition']), set()).add(r['user_sha256'])
        self.assertTrue(all(len(v) == 1 for v in users.values()))

    def test_no_label_case_id_or_rule_finding_reaches_the_model(self):
        case_ids = set(self.manifest)
        for r in self.requests:
            v = view(r['user'])
            self.assertEqual(v['already_found'], [], r['run_id'])
            for word in case_ids | {'gold', 'mutation', 'clean_control', 'acceptable_model_categories',
                                    'expected_objection', 'expected_location'}:
                self.assertNotIn(word, r['user'], r['run_id'])
            for f in checks.run_all(deepcopy(self.cases[r['case_id']]))[0]:
                self.assertNotIn(f['explanation'], r['user'], r['run_id'])

    def test_condition_views(self):
        by = {(r['case_id'], r['condition']): view(r['user']) for r in self.requests if r['repeat'] == 1}
        shared = ('evaluation_context', 'graphs', 'execution_conclusion', 'already_found')
        for case_id in self.cases:
            t, r, c = (by[(case_id, k)] for k in CND.CONDITIONS)
            self.assertEqual(set(t), set(r))
            self.assertEqual(set(c), set(r) | {'checker_status'})
            for key in shared:
                self.assertEqual(t[key], r[key], (case_id, key))
                self.assertEqual(r[key], c[key], (case_id, key))
            self.assertEqual((t['evidence'], t['checker_assessments'], t['retrieval_context']), ([], [], None))
            self.assertEqual(r['checker_assessments'], [])
            self.assertEqual((r['evidence'], r['retrieval_context']), (c['evidence'], c['retrieval_context']))
            self.assertEqual(c['checker_status'], CND.STATUS_NONE_ADMITTED)  # no checker is admitted in R1

    def test_c_and_r_equal_what_the_production_rule_blind_path_sends(self):
        """C without its status line is exactly the critic.llm.run(rq3_rule_blind=True) input; so is R while
        the admission log is empty, which holds for both parents."""
        by = {(r['case_id'], r['condition']): r['user'] for r in self.requests if r['repeat'] == 1}
        for case_id, case in self.cases.items():
            findings, info = checks.run_all(deepcopy(case))
            llm = Capture('')
            L.run(llm, case, findings, info['records'], info['checker_admission'], rq3_rule_blind=True)
            system, user = llm.sent
            self.assertEqual(system, self.system)
            c = view(by[(case_id, 'C')])
            del c['checker_status']
            self.assertEqual(c, view(user), case_id)
            self.assertEqual(info['checker_admission'], [], case_id)
            self.assertEqual(by[(case_id, 'R')], user, case_id)

    def test_settings_are_the_saved_one_pass_settings(self):
        saved = load(SAVED_REPORT)['llm']['settings']
        args = argparse.Namespace(scripted=None, base_url=saved['base_url'], model=S.SETTINGS['model'],
                                  temperature=S.SETTINGS['temperature'], max_tokens=S.SETTINGS['max_tokens'],
                                  timeout=S.SETTINGS['timeout_s'], accept_model=[])
        self.assertEqual(RB.client(args, None)('x').settings(), saved)
        self.assertEqual(self.summary['settings'], S.SETTINGS)


def reply(*findings):
    return json.dumps({'findings': list(findings)})


def finding(category, location, evidence_ids=()):
    return {'category': category, 'object_id': location['object_id'], 'node_id': location['node_id'],
            'explanation': 'test explanation', 'suggested_action': 'test action', 'evidence_ids': list(evidence_ids)}


class DryRun(unittest.TestCase):
    """Scripted replies through the runner and the scorer, one per scoring path."""

    @classmethod
    def setUpClass(cls):
        labels = {x['case_id']: x for x in load(RQ3 / 'mutations' / 'gold_labels.json')}
        m1a = labels['P1-M1a']['expected_location']
        other = {'object_id': 'butter_1', 'node_id': 'butter_1:G1'}
        cls.replies = {
            'P1-M1a:T:r1': reply(finding('C12', m1a)),                       # detection
            'P1-M1a:T:r2': reply(finding('C08', m1a)),                       # right place, wrong category
            'P1-M1a:T:r3': reply(finding('C12', other)),                     # right category, wrong place
            'P1-M1a:R:r1': reply(finding('C12', m1a, ['EV-NOT-IN-PACKAGE'])),  # invented evidence ID
            'P1-M1a:R:r2': reply(),                                          # abstention
            'P1-M1a:R:r3': 'not JSON at all',                                # invalid output
            'P1-M1a:C:r1': reply(finding('C11', m1a)),                       # rule-only category
            'P1-CC0:T:r1': reply(finding('C05', m1a)),                       # clean-control false positive
            '*': reply(),
        }
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        (tmp / 'replies.json').write_text(json.dumps(cls.replies), encoding='utf-8')
        cls.out = tmp / 'responses.jsonl'
        argv = ['--batch', str(EXP / 'batch'), '--out', str(cls.out), '--scripted', str(tmp / 'replies.json')]
        RB.main(argv)
        cls.second_pass = len(RB.read_jsonl(cls.out))
        RB.main(argv)  # a rerun sends nothing new
        lines = RB.read_jsonl(cls.out)
        cls.rerun_lines = len(lines)
        lines = [x for x in lines if x['run_id'] != 'P1-M1a:C:r2']  # a missing output
        for x in lines:
            if x['run_id'] == 'P1-M1a:C:r3':  # an attempt with no server reply
                x.update(reply=None, reply_sha256=None, error='URLError: test')
        cls.out.write_text(''.join(json.dumps(x) + '\n' for x in lines), encoding='utf-8')
        SC.main(['--responses', str(cls.out), '--out-dir', str(tmp)])
        cls.rows = {r['run_id']: r for r in csv_rows(tmp / 'RQ3_PER_CASE_RESULTS.csv')}
        cls.summary = csv_rows(tmp / 'RQ3_SUMMARY.csv')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_runner_records_every_request_once(self):
        self.assertEqual(self.second_pass, len(RB.load_batch(EXP / 'batch')[2]))
        self.assertEqual(self.rerun_lines, self.second_pass)
        self.assertEqual(len(self.rows), self.second_pass)

    def test_each_scoring_path(self):
        r = self.rows
        self.assertEqual((r['P1-M1a:T:r1']['status'], r['P1-M1a:T:r1']['detected']), ('valid', '1'))
        self.assertEqual((r['P1-M1a:T:r2']['target_hit'], r['P1-M1a:T:r2']['detected']), ('1', '0'))
        self.assertEqual(r['P1-M1a:T:r2']['target_categories'], 'C08')
        self.assertEqual((r['P1-M1a:T:r3']['target_hit'], r['P1-M1a:T:r3']['off_target_accepted'],
                          r['P1-M1a:T:r3']['detected']), ('0', '1', '0'))
        self.assertEqual((r['P1-M1a:R:r1']['hallucinated_citations'], r['P1-M1a:R:r1']['raw_target_hit'],
                          r['P1-M1a:R:r1']['detected']), ('1', '1', '0'))
        self.assertEqual((r['P1-M1a:R:r2']['abstained'], r['P1-M1a:R:r2']['detected']), ('1', '0'))
        self.assertEqual(r['P1-M1a:R:r3']['status'], 'invalid_output')
        self.assertEqual(r['P1-M1a:R:r3']['detected'], '')
        self.assertEqual((r['P1-M1a:C:r1']['rule_only_category_at_target'], r['P1-M1a:C:r1']['detected']),
                         ('1', '0'))
        self.assertEqual(r['P1-M1a:C:r2']['status'], 'missing')
        self.assertEqual(r['P1-M1a:C:r3']['status'], 'no_reply')
        self.assertEqual(r['P1-CC0:T:r1']['clean_control_false_positive'], '1')
        self.assertEqual(r['P1-CC0:T:r2']['clean_control_false_positive'], '0')
        self.assertTrue(all(x['backend'] == 'scripted' for x in r.values() if x['status'] != 'missing'))

    def test_rule_only_channel_and_union(self):
        r = self.rows
        self.assertEqual(r['P1-M1a:T:r2']['rule_only_detected'], '1')  # CLAIM-ABSOLUTE-SAFETY, C12
        self.assertEqual(r['P1-M1a:T:r2']['rules_plus_model_detected'], '1')
        self.assertEqual(r['P1-M3a:T:r1']['rule_only_detected'], '0')
        self.assertEqual(r['P1-M3a:T:r1']['rules_plus_model_detected'], '0')
        flagged = {x['case_id'] for x in r.values() if x['rule_only_detected'] == '1'}
        self.assertEqual(flagged, {'P1-M1a', 'P2-M1c'})
        self.assertTrue(all(x['rule_only_findings'] == '0' for x in r.values() if x['case_type'] == 'clean_control'))

    def test_summary_rates_use_valid_outputs_and_repeats(self):
        def get(channel, condition, subset, metric):
            hits = [x for x in self.summary if (x['channel'], x['condition'], x['subset'], x['metric'])
                    == (channel, condition, subset, metric)]
            self.assertEqual(len(hits), 1, (channel, condition, subset, metric))
            return hits[0]
        t = get('model_only', 'T', 'all_mutations', 'detection')
        self.assertEqual((t['numerator'], t['denominator'], t['repeats']), ('1', '24', '3'))
        self.assertNotEqual(t['sd_over_repeats'], '')
        c_valid = get('model_only', 'C', 'all_requests', 'valid_output')
        self.assertEqual((c_valid['numerator'], c_valid['denominator']), ('34', '36'))
        r_valid = get('model_only', 'R', 'all_requests', 'valid_output')
        self.assertEqual((r_valid['numerator'], r_valid['denominator']), ('35', '36'))
        rule = get('rule_only', '', 'all_mutations', 'detection')
        self.assertEqual((rule['numerator'], rule['denominator']), ('2', '8'))
        fp = get('model_only', 'T', 'clean_controls', 'false_positive')
        self.assertEqual((fp['numerator'], fp['denominator']), ('1', '12'))


if __name__ == '__main__':
    unittest.main()
