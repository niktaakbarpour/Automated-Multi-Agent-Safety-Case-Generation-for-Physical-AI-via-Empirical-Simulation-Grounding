"""Tests for the RQ4 planted-defect repair experiment. CPU only, no model.

    PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq4/tests -p 'test_*.py' -v

The dry run feeds fixed (scripted) replies through the GPU runner, the stage 2 builder, the review packet and
the scorer. They are test inputs written to exercise each path, never model results.
"""
from copy import deepcopy
from pathlib import Path
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


def edit(object_id, node_id, statement):
    return json.dumps({'edits': [{'op': 'replace_statement', 'object_id': object_id, 'node_id': node_id,
                                  'statement': statement, 'finding_ids': ['CRIT-001'],
                                  'justification': 'The original statement claimed more than the evidence shows.'}],
                       'declined': []})


class Inputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states = CM.states()
        cls.summary, cls.system, cls.requests = CM.RB.load_batch(EXP / 'batch_stage1')

    def test_stage1_files_equal_a_fresh_build(self):
        for name, text in B1.build().items():
            self.assertEqual((EXP / name).read_text(encoding='utf-8'), text, name)

    def test_cases_sources_and_settings(self):
        self.assertEqual([s.case_id for s in self.states], ['P1-M1a', 'P1-M1b', 'P2-M1c'])
        self.assertEqual({s.label['mutation_operator'] for s in self.states}, {'M1'})
        self.assertEqual(len({s.label['parent_group_id'] for s in self.states}), 2)
        self.assertEqual(self.summary['settings'], CM.RQ3_SETTINGS.SETTINGS)
        self.assertEqual(self.summary['independent_cases'], 0)
        self.assertEqual(len(self.requests), 3 * CM.REPEATS)

    def test_fixed_approval_rule(self):
        for s in self.states:
            self.assertEqual(len(s.decisions), 1, s.case_id)
            d = s.decisions[0]
            finding = next(c for c in s.report['criticisms'] if c['criticism_id'] == d['criticism_id'])
            self.assertTrue(CM.matches_label(finding, s.label))
            self.assertEqual((d['decision'], d['decided_by'], d['reviewer']), ('approved', 'human_review', CM.APPROVER))

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
                                                    'DeterministicAdapter']
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
        decisions = CM.approval_decisions(report, label)
        self.assertEqual(len(decisions), 1)
        self.assertGreater(len(report['criticisms']), 1)
        request = CM.revision_request('test', source, report, decisions)
        proposal = json.loads(edit('carton_c', 'U1', 'Initial support of carton_c is not established by the supplied evidence.'))
        proposal['edits'][0]['finding_ids'] = [decisions[0]['criticism_id']]
        result = E.revise(request, A.ScriptedAdapter(proposal))
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
        CM.RB.main(['--batch', str(EXP / 'batch_stage1'), '--out', str(T / 's1.jsonl'), '--scripted', str(T / 'replies1.json')])
        lines = [l for l in CM.RB.read_jsonl(T / 's1.jsonl') if l['run_id'] != 'P2-M1c:Q:r3']  # a missing output
        cls.stage2_files = B2.build(lines)
        for name, text in cls.stage2_files.items():
            (T / name).parent.mkdir(parents=True, exist_ok=True)
            (T / name).write_text(text, encoding='utf-8')
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
        files, cls.key = BR.build(T)
        for name, text in files.items():
            (T / 'REVIEW' / name).parent.mkdir(parents=True, exist_ok=True)
            (T / 'REVIEW' / name).write_text(text, encoding='utf-8')
        (T / 'KEY.json').write_text(json.dumps(cls.key), encoding='utf-8')
        cls.items = files

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def qwen(self, run_id):
        return CM.load_json(self.T / 'results' / 'qwen' / f"{run_id.replace(':', '_')}.revision_result.json")

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

    def test_qwen_and_template_saw_the_same_information(self):
        for run_id in ('P1-M1a:Q:r1', 'P2-M1c:Q:r2'):
            t = CM.load_json(EXP / 'results' / 'template' / f"{run_id.split(':')[0]}.revision_result.json")
            self.assertEqual(self.qwen(run_id)['permitted_information_sha256'], t['permitted_information_sha256'])

    def test_second_critic_batch(self):
        summary = json.loads(self.stage2_files['batch_stage2/BATCH.json'])
        self.assertEqual(summary['requests'], 3 * 3 + 3 * 3 + 3)  # originals, templates, revised Qwen outputs
        self.assertEqual(summary['settings'], CM.RQ3_SETTINGS.SETTINGS)

    def test_review_items_are_blinded(self):
        self.assertEqual(len(self.key['items']), 6)  # 3 template + 3 revised Qwen outputs
        self.assertEqual({k['method'] for k in self.key['items']}, {'template', 'qwen'})
        form = rows(self.T / 'REVIEW' / 'REVIEW_FORM.csv')
        self.assertEqual([r['blind_item_id'] for r in form], [k['blind_item_id'] for k in self.key['items']])
        for name, text in self.items.items():
            if name.startswith('items/'):
                for w in ('template', 'Template', 'qwen', 'Qwen', 'deterministic', 'scripted', ':Q:', 'justification',
                          'Edit: the statement'):
                    self.assertNotIn(w, text, (name, w))
                for section in ('## Approved Critic finding', '## Evidence given to the revision', '- After: '):
                    self.assertIn(section, text, name)

    def score(self, form):
        path = self.T / 'form.csv'
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=BR.FORM_COLUMNS, lineterminator='\n')
            w.writeheader()
            w.writerows(form)
        out = self.T / 'out'
        code = SC.main(['--base', str(self.T), '--stage2-responses', str(self.T / 's2.jsonl'),
                        '--review-form', str(path), '--key', str(self.T / 'KEY.json'), '--out-dir', str(out)])
        return code, out

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

    def test_comparison_waits_for_a_complete_review(self):
        form = self.filled()
        form[0]['defect_fixed'] = ''
        code, out = self.score(form)
        self.assertEqual(code, 1)
        self.assertFalse((out / 'RQ4_SUMMARY.csv').exists())

    def test_scores_worked_out_by_hand(self):
        code, out = self.score(self.filled())
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
        self.assertEqual(per['P2-M1c:Q:r1']['new_objections'], 'carton_c G1 C06')
        self.assertEqual(per['P1-M1a:template']['second_reviews_target_flagged'], '1')
        self.assertEqual(per['P1-M1a:template']['new_objections'], '')
        self.assertIn('| correct repair | 3/3 | 1/9 (mean 0.11, SD 0.19) |', (out / 'RQ4_TABLES.md').read_text())


if __name__ == '__main__':
    unittest.main()
