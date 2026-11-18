"""The command line and the saved examples. CPU only."""
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import io
import json
import tempfile
import unittest

from critic import contract as K
from drafter.revision import contract as C, engine as G
from drafter.revision.__main__ import main
from drafter.revision.tests import support as S
from drafter.revision.tools import check_examples

ACTIONABLE = str(S.EXAMPLES / 'synthetic_actionable.revision_request.json')
ZERO = str(S.EXAMPLES / 'saved_zero_finding.revision_request.json')


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class CommandLine(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)

    def test_revise_writes_the_result_bundle_diff_and_recriticism_request(self):
        paths = {k: str(self.tmp / (k + '.json')) for k in ('result', 'bundle', 'diff', 'recriticism')}
        code, out, err = run('revise', '--request', ACTIONABLE, '--out', paths['result'], '--out-bundle',
                             paths['bundle'], '--out-diff', paths['diff'], '--out-recriticism-request',
                             paths['recriticism'])
        self.assertEqual((code, out), (0, ''))
        self.assertIn('revised', err)
        result = read(paths['result'])
        self.assertEqual(C.schema_problems(result, 'revision_result'), [])
        self.assertEqual(read(paths['bundle']), result['revised_argument_bundle'])
        self.assertEqual(read(paths['diff'])['diff'], result['diff'])
        self.assertEqual(K.digest(read(paths['recriticism'])), result['recriticism']['request_sha256'])
        self.assertEqual(run('verify', '--request', ACTIONABLE, '--result', paths['result'])[0], 0)

    def test_revise_prints_the_result_without_out(self):
        code, out, _ = run('revise', '--request', ZERO)
        self.assertEqual(code, 0)
        self.assertEqual((json.loads(out)['outcome'], json.loads(out)['stop_reason']),
                         ('no_change', 'no_actionable_findings'))

    def test_verify_rejects_a_changed_result(self):
        result = G.revise(read(ACTIONABLE))
        result['revised_argument_bundle']['graphs'][0]['graph']['nodes'][0]['statement'] = 'Changed by hand.'
        path = self.tmp / 'changed.json'
        path.write_text(json.dumps(result), encoding='utf-8')
        code, out, _ = run('verify', '--request', ACTIONABLE, '--result', str(path))
        self.assertEqual(code, 1)
        self.assertIn('does not hold', out)

    def test_exit_codes(self):
        bad = self.tmp / 'bad.json'
        bad.write_text(json.dumps({'schema_version': 'x'}), encoding='utf-8')
        self.assertEqual(run('revise', '--request', str(bad))[0], 3)
        self.assertEqual(run('revise', '--request', str(self.tmp / 'missing.json'))[0], 6)
        broken = self.tmp / 'broken.json'
        broken.write_text('{not json', encoding='utf-8')
        self.assertEqual(run('revise', '--request', str(broken))[0], 6)
        undecided = read(ACTIONABLE)
        undecided['finding_decisions'] = []
        path = self.tmp / 'undecided.json'
        path.write_text(json.dumps(undecided), encoding='utf-8')
        self.assertEqual(run('revise', '--request', str(path))[0], 1)

    def test_build_request_then_revise(self):
        fixture = S.FIXTURE
        out = str(self.tmp / 'request.json')
        code, _, _ = run('build-request', '--critic-request', str(fixture / 'critic.request.json'),
                         '--critic-report', str(fixture / 'critic.qwen.report.json'),
                         '--revision-id', 'cli:saved-zero-finding', '--out', out)
        self.assertEqual(code, 0)
        self.assertEqual(C.request_issues(read(out)), [])
        self.assertEqual(run('revise', '--request', out, '--out', str(self.tmp / 'r.json'))[0], 0)
        # a report paired with the wrong request is refused
        code, _, err = run('build-request', '--critic-request',
                           str(fixture / 'critic.controlled-negative.request.json'), '--critic-report',
                           str(fixture / 'critic.qwen.report.json'), '--revision-id', 'cli:mismatch')
        self.assertEqual(code, 3)
        self.assertIn('report_request_id_mismatch', err)

    def test_build_request_needs_the_label_for_a_scripted_report(self):
        arguments = ['build-request', '--critic-request',
                     str(S.FIXTURE / 'critic.controlled-negative.request.json'), '--critic-report',
                     str(S.EXAMPLES / 'synthetic_actionable.critic_report.json'), '--revision-id', 'cli:label']
        code, _, err = run(*arguments)
        self.assertEqual(code, 3)
        self.assertIn('scripted_report_requires_synthetic_label', err)
        code, out, _ = run(*arguments, '--synthetic-label', S.LABEL)
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)['synthetic_findings']['present'])

    def test_cycle_writes_every_piece(self):
        out = self.tmp / 'cycle'
        code, _, err = run('cycle', '--request', ACTIONABLE, '--out-dir', str(out))
        self.assertEqual(code, 0)
        self.assertIn('stop_reason=no_actionable_findings', err)
        cycle = read(out / 'cycle.json')
        self.assertEqual(C.schema_problems(cycle, 'revision_cycle'), [])
        names = sorted(p.name for p in out.iterdir())
        self.assertEqual(names, ['cycle.json', 'final_argument_bundle.json',
                                 'request_1.recriticism_report.json', 'request_1.recriticism_request.json',
                                 'request_1.revision_request.json', 'request_1.revision_result.json',
                                 'request_2.revision_request.json', 'request_2.revision_result.json'])
        self.assertEqual(K.digest(read(out / 'final_argument_bundle.json')), cycle['final_argument_bundle_sha256'])
        for index in (1, 2):
            request = read(out / f'request_{index}.revision_request.json')
            result = read(out / f'request_{index}.revision_result.json')
            self.assertEqual(G.verify_result(request, result), [])
        self.assertEqual(read(out / 'request_2.revision_request.json')['critic_report'],
                         read(out / 'request_1.recriticism_report.json'))

    def test_cycle_with_a_scripted_repeat_stops(self):
        reply = self.tmp / 'reply.json'
        reply.write_text(json.dumps({'findings': [S.guarantee_finding()]}), encoding='utf-8')
        out = self.tmp / 'repeat'
        code, _, err = run('cycle', '--request', ACTIONABLE, '--out-dir', str(out), '--scripted-reply',
                           str(reply), '--approve-as-synthetic-test')
        self.assertEqual(code, 0)
        self.assertIn('stop_reason=repeated_unchanged_findings', err)


class SavedExamples(unittest.TestCase):
    def test_every_saved_example_still_holds(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = check_examples.main()
        self.assertEqual(code, 0, [line for line in out.getvalue().splitlines() if line.startswith('FAIL')])


if __name__ == '__main__':
    unittest.main()
