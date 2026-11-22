"""Regression tests for the clean fixture's file and graph boundaries."""

import contextlib
import copy
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.m4_20261127.rq3.gsn_inputs import build_inputs


class CleanFixtureTests(unittest.TestCase):
    def test_changed_output_cannot_pass_reproduction_check(self):
        with TemporaryDirectory() as output, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build_inputs.main(['--out', output]), 0)
            self.assertEqual(build_inputs.main(['--check', output]), 0)
            request_path = Path(output) / 'P2.clean.critic_request.json'
            request_path.write_bytes(request_path.read_bytes() + b'\n')
            error = io.StringIO()
            with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as exit_info:
                build_inputs.main(['--check', output])
            self.assertEqual(exit_info.exception.code, 1)
            self.assertIn(request_path.name, error.getvalue())

    def test_synthetic_rows_cannot_be_reclassified_as_real(self):
        request = build_inputs.load_parents()['P2']
        request['test_fixture'] = False
        with self.assertRaisesRegex(ValueError, 'EV-(RECORD|SYNTHETIC)'):
            build_inputs.validate_shared_graphs(request)

    def test_dangling_edges_fail_shared_graph_validation(self):
        request = copy.deepcopy(build_inputs.load_parents()['P1'])
        edge = request['argument_bundle']['graphs'][0]['graph']['edges'][0]
        edge['target'] = 'nonexistent-node'
        with self.assertRaisesRegex(ValueError, 'invalid edge endpoint'):
            build_inputs.validate_shared_graphs(request)


if __name__ == '__main__':
    unittest.main()
