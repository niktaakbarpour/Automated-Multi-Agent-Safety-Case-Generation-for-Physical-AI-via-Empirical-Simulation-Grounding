"""Tests for the RQ4 planted-defect repair experiment. CPU only, no model.

    PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq4/tests -p 'test_*.py' -v

The dry run feeds fixed (scripted) replies through the GPU runner, the stage 2 builder, the review packet and
the scorer. They are test inputs written to exercise each path, never model results; the scorer accepts them
only when a test passes allow_scripted=True, which the command line never does.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import csv
import json
import shutil
import sys
import tempfile
import unittest

from drafter.revision import adapters as A, engine as E

RQ4 = Path(__file__).resolve().parents[1]
EXP = RQ4 / 'experiment'
sys.path.insert(0, str(EXP))
import build_review as BR  # noqa: E402
import build_stage1 as B1  # noqa: E402
import build_stage2 as B2  # noqa: E402
import common as CM  # noqa: E402
import score as SC  # noqa: E402


def rows(path):
    with open(path, encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def write_csv(path, columns, data):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator='\n')
        w.writeheader()
        w.writerows(data)


def write_jsonl(path, lines):
    Path(path).write_text(''.join(json.dumps(l) + '\n' for l in lines), encoding='utf-8')


def edit(object_id, node_id, statement, finding_id='CRIT-001'):
    return json.dumps({'edits': [{'op': 'replace_statement', 'object_id': object_id, 'node_id': node_id,
                                  'statement': statement, 'finding_ids': [finding_id],
                                  'justification': 'The original statement claimed more than the evidence shows.'}],
                       'declined': []})


def signed(row, decision='approved'):
    return {**row, 'decision': decision, 'approver': 'Test Approver', 'approved_on': '2026-11-23',
            'attestation': CM.ATTESTATION}


class Inputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states = CM.states()
        cls.summary, cls.system, cls.requests = CM.RB.load_batch(EXP / 'batch_stage1')

    def test_stage1_files_equal_a_fresh_build(self):
        self.assertEqual(CM.stale_files({(EXP / n).resolve(): t for n, t in B1.build().items()}), [])

    def test_cases_sources_and_settings(self):
        self.assertEqual([s.case_id for s in self.states], ['P1-M1a', 'P1-M1b', 'P2-M1c'])
        self.assertEqual({s.label['mutation_operator'] for s in self.states}, {'M1'})
        self.assertEqual(len({s.label['parent_group_id'] for s in self.states}), 2)
        self.assertEqual(self.summary['settings'], CM.FROZEN)
        self.assertEqual(self.summary['system_sha256'], CM.sha256_text(CM.PROMPT_PATH.read_text(encoding='utf-8')))
        self.assertEqual(self.summary['independent_cases'], 0)
        self.assertEqual(len(self.requests), 3 * CM.REPEATS)

    def test_recorded_human_approvals(self):
        """Every approval in use comes from the hand-filled file, signed and bound to its report."""
        for s in self.states:
            approved = [d for d in s.decisions if d['decision'] == 'approved']
            self.assertEqual(len(approved), 1, s.case_id)
            d = approved[0]
            self.assertEqual(d['decided_by'], 'human_review')
            self.assertTrue(d['reviewer'])
            self.assertIn('Recorded by hand', d['note'])
            self.assertTrue(CM.matches_label(CM.approved_finding(s), s.label))
            self.assertEqual(s.request['finding_decisions'], s.decisions)

    def test_replayed_critic_report_is_the_saved_rq3_input(self):
        attempt = CM.saved_rq3_attempt('P1-M1b:R:r3')
        report = self.states[1].report
        self.assertEqual(report['llm']['input_sha256'], attempt['input_sha256'])
        self.assertEqual(report['llm']['backend'], 'replayed_saved_response')
        other = deepcopy(attempt)
        other['input_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            CM.replayed_report(self.states[1].critic_request, other)

    def test_both_methods_get_the_same_permitted_information(self):
        for s, line in zip(self.states, self.requests[::CM.REPEATS]):
            self.assertEqual(line['case_id'], s.case_id)
            template = CM.load_json(EXP / 'results' / 'template' / f'{s.case_id}.revision_result.json')
            self.assertEqual(template['permitted_information_sha256'], line['permitted_information_sha256'])
            wrapped = CM.SamePermittedInformation(A.DeterministicAdapter(), s.evidence)
            E.revise(deepcopy(s.request), wrapped)
            self.assertIn('permitted_evidence', wrapped.seen)
            self.assertEqual(CM.information_sha256(wrapped.seen), line['permitted_information_sha256'])

    def test_no_label_or_method_reaches_the_model(self):
        words = [s.case_id for s in self.states] + ['mutation', 'planted', 'gold_label', 'acceptable_model_categories',
                                                    'expected_location', 'template', 'deterministic-templates',
                                                    'DeterministicAdapter', 'FINDING_APPROVALS', 'Recorded by hand']
        for line in self.requests:
            for w in words:
                self.assertNotIn(w, line['user'], (line['run_id'], w))
        for w in words:
            self.assertNotIn(w, self.system)

    def test_other_findings_are_preserved(self):
        """A report with several findings: only the planted one is approved; the rest stay as they were."""
        source = CM.load_case('P2-CC0')[0]
        report = CM.replayed_report(source, CM.saved_rq3_attempt('P2-CC0:R:r2'))
        label = {'expected_location': {'object_id': 'carton_c', 'node_id': 'U1'},
                 'acceptable_model_categories': ['C08']}
        form = CM.approval_form_rows('P2-CC0', report, label)
        form = [signed(r) if r['on_planted_defect_node'] == 'yes' else r for r in form]
        decisions = CM.approval_decisions('P2-CC0', report, label, form)
        self.assertEqual(len(decisions), 1)
        self.assertGreater(len(report['criticisms']), 1)
        request = CM.revision_request('test', source, report, decisions)
        result = E.revise(request, A.ScriptedAdapter(json.loads(edit(
            'carton_c', 'U1', 'Initial support of carton_c is not established by the supplied evidence.',
            decisions[0]['criticism_id']))))
        self.assertEqual(result['outcome'], 'revised')
        dispositions = {d['criticism_id']: d['disposition'] for d in result['dispositions']}
        self.assertEqual(dispositions.pop(decisions[0]['criticism_id']), 'edited')
        self.assertTrue(dispositions and all(v != 'edited' for v in dispositions.values()))
        self.assertEqual({(d['object_id'], d['node_id']) for d in result['diff']}, {('carton_c', 'U1')})
        state = CM.CaseState.__new__(CM.CaseState)
        state.critic_request, state.report, state.decisions = source, report, decisions
        state.evidence = CM.permitted_evidence(source)
        text = BR.item_text(state, result)
        for c in report['criticisms']:
            if c['criticism_id'] != decisions[0]['criticism_id']:
                self.assertIn(c['explanation'], text)


class Approvals(unittest.TestCase):
    """The approval file is checked; nothing is inferred from generated fields."""

    @classmethod
    def setUpClass(cls):
        cls.rows = CM.load_approvals()
        cls.state = CM.states()[0]

    def decisions(self, rows, label=None):
        s = self.state
        return CM.approval_decisions(s.case_id, s.report, label or s.label, rows)

    def mine(self):
        return [dict(r) for r in self.rows if r['case_id'] == self.state.case_id]

    def test_recorded_rows_pass(self):
        self.assertEqual(len([d for d in self.decisions(self.rows) if d['decision'] == 'approved']), 1)

    def test_bad_rows_are_refused(self):
        row = self.mine()[0]
        cases = {
            'no row': [],
            'duplicate row': [row, row],
            'other report': [{**row, 'critic_report_sha256': '0' * 64}],
            'unknown finding': [row, {**row, 'criticism_id': 'CRIT-999'}],
            'no approver': [{**row, 'approver': ''}],
            'bad date': [{**row, 'approved_on': '23/11/2026'}],
            'wrong attestation': [{**row, 'attestation': 'ok'}],
            'bad decision': [{**row, 'decision': 'yes'}],
            'nothing approved': [{**row, **{k: '' for k in CM.HUMAN_COLUMNS}}],
            'details without decision': [{**row, 'decision': ''}],
            'finding changed': [{**row, 'category': 'C05' if row['category'] != 'C05' else 'C06'}],
        }
        for name, data in cases.items():
            with self.assertRaises(ValueError, msg=name):
                self.decisions(data)

    def test_approval_off_the_fixed_rule_is_refused(self):
        other = deepcopy(self.state.label)
        other['expected_location'] = {'object_id': 'butter_1', 'node_id': 'butter_1:G1'}
        with self.assertRaises(ValueError):
            self.decisions(self.mine(), other)

    def test_missing_or_malformed_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                CM.load_approvals(Path(tmp) / 'none.csv')
            bad = Path(tmp) / 'bad.csv'
            write_csv(bad, CM.APPROVAL_COLUMNS[:-1], [{k: v for k, v in self.rows[0].items() if k != 'attestation'}])
            with self.assertRaises(ValueError):
                CM.load_approvals(bad)


class Protection(unittest.TestCase):
    def test_write_files_never_changes_a_file_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.txt'
            CM.write_files({path: 'one'})
            CM.write_files({path: 'one'})  # the same content is fine
            with self.assertRaises(CM.ProtectedFileError):
                CM.write_files({path: 'two', Path(tmp) / 'b.txt': 'x'})
            self.assertEqual(path.read_text(), 'one')
            self.assertFalse((Path(tmp) / 'b.txt').exists())  # nothing written when anything is refused
            CM.write_files({path: 'two'}, replace=True)
            self.assertEqual(path.read_text(), 'two')

    def test_stage1_is_frozen_once_a_run_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.assertFalse(B1.run_outputs_exist(base))
            (base / 'real_run_x').mkdir()
            (base / 'real_run_x' / 'RQ4_STAGE1_RESPONSES.jsonl').write_text('')
            self.assertTrue(B1.run_outputs_exist(base))


class DryRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        T = cls.T = Path(cls.tmp.name)
        good_m1a = edit('cream_cheese_1', 'cream_cheese_1:G1',
                        'Whether cream_cheese_1 left its support during frames 10 to 257 is not established by the evidence.')
        good_m1c = edit('vial_b', 'U1', 'Whether vial_b stayed on workbench_B during frames 8 to 120 is not established.')
        replies = {
            'P1-M1a:Q:r1': good_m1a,
            'P1-M1a:Q:r2': edit('cream_cheese_1', 'cream_cheese_1:G1', 'Cream_cheese_1 was not shown to be safe.'),
            'P1-M1a:Q:r3': json.dumps({'edits': [], 'declined': [{'criticism_id': 'CRIT-001',
                                       'reason': 'insufficient_evidence', 'note': 'No evidence for this object.'}]}),
            'P1-M1b:Q:r1': 'I cannot answer in JSON.',
            'P1-M1b:Q:r2': json.dumps({'edits': [], 'declined': [], 'extra': 1}),
            'P1-M1b:Q:r3': edit('ketchup_1', 'ketchup_1:S1', 'The strategy is unchanged in meaning.'),
            'P2-M1c:Q:r1': good_m1c, 'P2-M1c:Q:r2': good_m1c, 'P2-M1c:Q:r3': good_m1c}
        (T / 'replies1.json').write_text(json.dumps(replies), encoding='utf-8')
        CM.RB.main(['--batch', str(EXP / 'batch_stage1'), '--out', str(T / 's1_all.jsonl'),
                    '--scripted', str(T / 'replies1.json')])
        cls.s1 = [l for l in CM.RB.read_jsonl(T / 's1_all.jsonl') if l['run_id'] != 'P2-M1c:Q:r3']  # a missing output
        write_jsonl(T / 's1.jsonl', cls.s1)
        cls.stage2_files = B2.build(cls.s1, allow_scripted=True)
        CM.write_files({T / n: t for n, t in cls.stage2_files.items()})
        shutil.copytree(EXP / 'results' / 'template', T / 'results' / 'template')
        replies2 = {'*': '{"findings": []}',
                    'S2:P1-M1a:template:r2': json.dumps({'findings': [{
                        'category': 'C05', 'object_id': 'cream_cheese_1', 'node_id': 'cream_cheese_1:G1',
                        'explanation': 'Still claims more than shown.', 'suggested_action': 'Narrow it.'}]}),
                    'S2:P2-M1c:Q:r1:r1': json.dumps({'findings': [{
                        'category': 'C06', 'object_id': 'carton_c', 'node_id': 'G1',
                        'explanation': 'An unsupported conclusion.', 'suggested_action': 'Mark it unresolved.'}]})}
        (T / 'replies2.json').write_text(json.dumps(replies2), encoding='utf-8')
        CM.RB.main(['--batch', str(T / 'batch_stage2'), '--out', str(T / 's2.jsonl'), '--scripted', str(T / 'replies2.json')])
        cls.s2 = CM.RB.read_jsonl(T / 's2.jsonl')
        files, cls.key = BR.build(T)
        CM.write_files({T / 'REVIEW' / n: t for n, t in files.items()})
        (T / 'KEY.json').write_text(json.dumps(cls.key), encoding='utf-8')
        cls.items = files

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def qwen(self, run_id):
        return CM.load_json(self.T / 'results' / 'qwen' / f"{run_id.replace(':', '_')}.revision_result.json")

    # ---------------------------------------------------------------- outputs and accounting
    def test_each_output_path(self):
        expected = {'P1-M1a:Q:r1': 'revised', 'P1-M1a:Q:r2': 'edit_refused', 'P1-M1a:Q:r3': 'abstained',
                    'P1-M1b:Q:r1': 'invalid_unparseable', 'P1-M1b:Q:r2': 'invalid_malformed',
                    'P1-M1b:Q:r3': 'edit_refused', 'P2-M1c:Q:r1': 'revised', 'P2-M1c:Q:r2': 'revised',
                    'P2-M1c:Q:r3': 'missing'}
        for run_id, status in expected.items():
            self.assertEqual(self.qwen(run_id)['status'], status, run_id)
        self.assertIn('statement_contains_assurance_wording',
                      self.qwen('P1-M1a:Q:r2')['result']['rejected_edits'][0]['reasons'])
        for run_id in ('P1-M1a:Q:r1', 'P2-M1c:Q:r1'):
            request = CM.load_json(EXP / 'cases' / f"{run_id.split(':')[0]}.revision_request.json")
            self.assertEqual(E.verify_result(request, self.qwen(run_id)['result']), [])

    def test_all_nine_requests_are_accounted_for(self):
        names = sorted(p.name for p in (self.T / 'results' / 'qwen').glob('*.json'))
        self.assertEqual(names, BR.expected_qwen_files())
        none = B2.build([], allow_scripted=True)
        self.assertEqual(sorted(json.loads(t)['status'] for n, t in none.items() if n.startswith('results/qwen/')),
                         ['missing'] * 9)

    def test_qwen_and_template_saw_the_same_information(self):
        for run_id in ('P1-M1a:Q:r1', 'P2-M1c:Q:r2'):
            t = CM.load_json(EXP / 'results' / 'template' / f"{run_id.split(':')[0]}.revision_result.json")
            self.assertEqual(self.qwen(run_id)['permitted_information_sha256'], t['permitted_information_sha256'])

    def test_second_critic_batch(self):
        summary = json.loads(self.stage2_files['batch_stage2/BATCH.json'])
        self.assertEqual(summary['requests'], 3 * 3 + 3 * 3 + 3)  # originals, templates, revised Qwen outputs
        self.assertEqual(summary['settings'], CM.FROZEN)

    # ---------------------------------------------------------------- response checks
    def assert_refused(self, lines, allow_scripted=True):
        with self.assertRaises(ValueError):
            B2.build(lines, allow_scripted=allow_scripted)

    def test_bad_stage1_responses_are_refused(self):
        one = self.s1[0]
        self.assert_refused(self.s1 + [{**one, 'run_id': 'P9-X:Q:r1'}])                        # unknown run ID
        self.assert_refused(self.s1 + [{**one, 'attempt': 2}])                                 # answered twice
        self.assert_refused([{**one, 'user_sha256': '0' * 64}] + self.s1[1:])                  # other input
        self.assert_refused([{**one, 'input_sha256': '0' * 64}] + self.s1[1:])                 # other messages
        self.assert_refused([{**one, 'reply_sha256': '0' * 64}] + self.s1[1:])                 # reply altered
        self.assert_refused([{**one, 'attempt': 2}] + self.s1[1:])                             # numbering
        self.assert_refused(self.s1, allow_scripted=False)                                     # scripted replies

    def model_lines(self, **settings_change):
        args = argparse.Namespace(scripted=None, base_url='http://127.0.0.1:8000/v1', model=CM.FROZEN['model'],
                                  temperature=CM.FROZEN['temperature'], max_tokens=CM.FROZEN['max_tokens'],
                                  timeout=CM.FROZEN['timeout_s'], accept_model=[])
        settings = {**CM.RB.client(args, None)('x').settings(), **settings_change}
        response = {'id': 'r', 'model': CM.FROZEN['model'], 'finish_reason': 'stop', 'usage': {}}
        return [{**l, 'backend': 'openai_compatible', 'settings': settings, 'model_revision': 'rev-1',
                 'response': response} for l in self.s1]

    def test_model_identity_and_settings_are_checked(self):
        B2.build(self.model_lines())  # a model run with the frozen settings is accepted
        self.assert_refused(self.model_lines(temperature=0.7), allow_scripted=False)
        self.assert_refused(self.model_lines(model='other/model'), allow_scripted=False)
        lines = self.model_lines()
        lines[0] = {**lines[0], 'model_revision': 'rev-2'}
        self.assert_refused(lines, allow_scripted=False)                                       # two revisions
        lines = self.model_lines()
        lines[0] = {**lines[0], 'response': {**lines[0]['response'], 'model': 'other/model'}}
        files = B2.build(lines)
        self.assertEqual(json.loads(files['results/qwen/P1-M1a_Q_r1.revision_result.json'])['status'],
                         'invalid_server_reply')

    # ---------------------------------------------------------------- blinding
    def test_review_items_are_blinded(self):
        self.assertEqual(len(self.key['items']), 6)  # 3 template + 3 revised Qwen outputs
        self.assertEqual({k['method'] for k in self.key['items']}, {'template', 'qwen'})
        form = rows(self.T / 'REVIEW' / 'REVIEW_FORM.csv')
        self.assertEqual([r['blind_item_id'] for r in form], [k['blind_item_id'] for k in self.key['items']])
        self.assertEqual(sorted(self.items), sorted(['REVIEW_FORM.csv', 'REVIEW_MANIFEST.csv', 'REVIEW_INSTRUCTIONS.md']
                                                    + [f"items/{k['blind_item_id']}.md" for k in self.key['items']]))
        for name, text in self.items.items():
            if name.startswith('items/') or name == 'REVIEW_MANIFEST.csv' or name == 'REVIEW_FORM.csv':
                for w in ('template', 'Template', 'qwen', 'Qwen', 'deterministic', 'scripted', ':Q:', 'justification',
                          'Edit: the statement', 'output_id', 'method'):
                    self.assertNotIn(w, text, (name, w))
            if name.startswith('items/'):
                for section in ('## Approved Critic finding', '## Evidence given to the revision', '- After: '):
                    self.assertIn(section, text, name)

    # ---------------------------------------------------------------- scoring and review validation
    def filled(self):
        verdicts = {'P2-M1c:Q:r1': ('partly', 'yes', 'no', 'yes'), 'P2-M1c:Q:r2': ('yes', 'yes', 'no', 'no')}
        form = []
        for k in self.key['items']:
            fixed, supported, new, scope = verdicts.get(k['output_id'], ('yes', 'yes', 'no', 'yes'))
            form.append({'blind_item_id': k['blind_item_id'], 'reviewer_id': 'test', 'review_date': '2026-11-24',
                         'prior_exposure_declaration': 'test', 'defect_fixed': fixed,
                         'revised_claim_supported_by_evidence': supported, 'new_problem_introduced': new,
                         'new_problem_description': '', 'scope_preserved': scope, 'notes': '',
                         'review_frozen_timestamp': '2026-11-24T12:00'})
        return form

    def score(self, form, name, s1=None, s2=None, key=None, extra=()):
        review = self.T / f'review_{name}'
        shutil.copytree(self.T / 'REVIEW', review)
        if form is not None:
            write_csv(review / 'REVIEW_FORM.csv', BR.FORM_COLUMNS, form)
        out = self.T / f'out_{name}'
        argv = ['--base', str(self.T), '--stage1-responses', str(s1 or self.T / 's1.jsonl'),
                '--stage2-responses', str(s2 or self.T / 's2.jsonl'), '--review-dir', str(review),
                '--key', str(key or self.T / 'KEY.json'), '--out-dir', str(out), *extra]
        return SC.main(argv, allow_scripted=True), out, review

    def assert_no_comparison(self, code, out):
        self.assertEqual(code, 1)
        self.assertFalse((out / 'RQ4_SUMMARY.csv').exists())
        self.assertFalse((out / 'RQ4_TABLES.md').exists())

    def test_invalid_review_forms_are_refused(self):
        good = self.filled()
        cases = {
            'blank': None,
            'missing_answer': [{**good[0], 'defect_fixed': ''}] + good[1:],
            'bad_value': [{**good[0], 'scope_preserved': 'maybe'}] + good[1:],
            'duplicate_id': good + [good[0]],
            'missing_row': good[1:],
            'unexpected_id': good + [{**good[0], 'blind_item_id': 'B99'}],
            'no_reviewer': [{**good[0], 'reviewer_id': ' '}] + good[1:],
            'no_exposure': [{**good[0], 'prior_exposure_declaration': ''}] + good[1:],
            'bad_date': [{**good[0], 'review_date': 'yesterday'}] + good[1:],
            'two_freezes': [{**good[0], 'review_frozen_timestamp': '2026-11-24T13:00'}] + good[1:],
            'not_frozen': [{**r, 'review_frozen_timestamp': ''} for r in good],
            'undescribed_problem': [{**good[0], 'new_problem_introduced': 'yes'}] + good[1:],
        }
        for name, form in cases.items():
            code, out, _ = self.score(form, name)
            self.assert_no_comparison(code, out)
        review = self.T / 'review_header'
        shutil.copytree(self.T / 'REVIEW', review)
        write_csv(review / 'REVIEW_FORM.csv', BR.FORM_COLUMNS[:-1], [{k: r[k] for k in BR.FORM_COLUMNS[:-1]} for r in good])
        code = SC.main(['--base', str(self.T), '--stage1-responses', str(self.T / 's1.jsonl'), '--stage2-responses',
                        str(self.T / 's2.jsonl'), '--review-dir', str(review), '--key', str(self.T / 'KEY.json'),
                        '--out-dir', str(self.T / 'out_header')], allow_scripted=True)
        self.assert_no_comparison(code, self.T / 'out_header')

    def test_changed_items_key_or_responses_are_refused(self):
        code, out, review = self.score(self.filled(), 'pre_edit')
        self.assertEqual(code, 0)
        item = review / 'items' / 'B01.md'
        item.write_text(item.read_text() + 'changed\n')
        code = SC.main(['--base', str(self.T), '--stage1-responses', str(self.T / 's1.jsonl'), '--stage2-responses',
                        str(self.T / 's2.jsonl'), '--review-dir', str(review), '--key', str(self.T / 'KEY.json'),
                        '--out-dir', str(self.T / 'out_item')], allow_scripted=True)
        self.assert_no_comparison(code, self.T / 'out_item')
        key = deepcopy(self.key)
        key['items'][0]['result_sha256'] = '0' * 64
        (self.T / 'KEY_bad.json').write_text(json.dumps(key))
        self.assert_no_comparison(*self.score(self.filled(), 'key', key=self.T / 'KEY_bad.json')[:2])
        write_jsonl(self.T / 's2_bad.jsonl', [{**self.s2[0], 'user_sha256': '0' * 64}] + self.s2[1:])
        self.assert_no_comparison(*self.score(self.filled(), 's2', s2=self.T / 's2_bad.jsonl')[:2])
        write_jsonl(self.T / 's1_bad.jsonl', self.s1[1:])  # differs from the saved results
        self.assert_no_comparison(*self.score(self.filled(), 's1', s1=self.T / 's1_bad.jsonl')[:2])

    def test_outputs_are_not_overwritten(self):
        code, out, _ = self.score(self.filled(), 'twice')
        self.assertEqual(code, 0)
        before = (out / 'RQ4_SUMMARY.csv').read_text()
        form = self.filled()
        form[0] = {**form[0], 'defect_fixed': 'no'}
        review = self.T / 'review_twice'
        write_csv(review / 'REVIEW_FORM.csv', BR.FORM_COLUMNS, form)
        argv = ['--base', str(self.T), '--stage1-responses', str(self.T / 's1.jsonl'), '--stage2-responses',
                str(self.T / 's2.jsonl'), '--review-dir', str(review), '--key', str(self.T / 'KEY.json'),
                '--out-dir', str(out)]
        self.assertEqual(SC.main(argv, allow_scripted=True), 1)
        self.assertEqual((out / 'RQ4_SUMMARY.csv').read_text(), before)
        self.assertEqual(SC.main(argv + ['--replace-outputs'], allow_scripted=True), 0)
        self.assertNotEqual((out / 'RQ4_SUMMARY.csv').read_text(), before)

    def test_pre_review_writes_facts_only(self):
        code, out, _ = self.score(None, 'pre', extra=['--pre-review'])
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['RQ4_PRE_REVIEW_FACTS.csv'])
        facts = rows(out / 'RQ4_PRE_REVIEW_FACTS.csv')
        self.assertEqual(len(facts), 12)
        self.assertTrue(all(r['defect_fixed'] == '' for r in facts))

    def test_scores_worked_out_by_hand(self):
        code, out, _ = self.score(self.filled(), 'valid')
        self.assertEqual(code, 0)
        summary = {(r['method'], r['metric']): r for r in rows(out / 'RQ4_SUMMARY.csv')}

        def frac(method, metric):
            r = summary[(method, metric)]
            return r['numerator'], r['denominator']
        self.assertEqual(frac('template', 'correct_repair'), ('3', '3'))
        self.assertEqual(frac('qwen', 'revised'), ('3', '9'))
        self.assertEqual(frac('qwen', 'invalid'), ('4', '9'))   # 2 refused edits, unparseable, malformed
        self.assertEqual(frac('qwen', 'abstained'), ('1', '9'))
        self.assertEqual(frac('qwen', 'missing_or_no_reply'), ('1', '9'))
        self.assertEqual(frac('qwen', 'correct_repair'), ('1', '9'))
        self.assertEqual(frac('qwen', 'correct_repair_of_revised'), ('1', '3'))
        q = summary[('qwen', 'correct_repair')]
        self.assertEqual((q['samples'], q['mean_over_samples'], q['sd_over_samples']), ('3', '0.1111', '0.1925'))
        self.assertEqual(frac('template', 'second_critic_target_still_flagged'), ('1', '9'))
        self.assertEqual(frac('template', 'second_critic_new_objection'), ('0', '9'))
        self.assertEqual(frac('qwen', 'second_critic_new_objection'), ('1', '3'))
        self.assertEqual(frac('qwen', 'scope_preserved=yes'), ('2', '3'))
        per = {r['output_id']: r for r in rows(out / 'RQ4_PER_OUTPUT.csv')}
        self.assertEqual(len(per), 12)
        self.assertEqual(per['P2-M1c:Q:r3']['status'], 'missing')
        self.assertEqual(per['P2-M1c:Q:r3']['correct_repair'], '0')
        self.assertEqual(per['P2-M1c:Q:r1']['new_objections'], 'carton_c G1 C06')
        self.assertEqual(per['P1-M1a:template']['second_reviews_target_flagged'], '1')
        self.assertEqual(per['P1-M1a:template']['second_reviews_missing'], '0')
        self.assertEqual(per['P1-M1a:template']['new_objections'], '')
        self.assertIn('| correct repair | 3/3 | 1/9 (mean 0.11, SD 0.19) |', (out / 'RQ4_TABLES.md').read_text())
        prov = json.loads((out / 'RQ4_PROVENANCE.json').read_text())
        self.assertEqual(prov['revision_prompt_sha256'], CM.sha256_text(CM.PROMPT_PATH.read_text(encoding='utf-8')))
        self.assertEqual(prov['model'], CM.FROZEN['model'])


if __name__ == '__main__':
    unittest.main()
