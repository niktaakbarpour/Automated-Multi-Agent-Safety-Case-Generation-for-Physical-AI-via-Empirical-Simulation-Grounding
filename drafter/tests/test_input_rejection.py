"""Regression checks for safe rejection before inference or output acceptance."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from drafter.__main__ import main
from drafter.generation import generate_argument
from drafter.mock_demo import run_mock_demo
from drafter.validation import ContractError, ROOT, read_json, validate_request
from evaluation.r1_v4.provenance import digest


class InputRejectionTests(unittest.TestCase):
    def request(self):
        return read_json(ROOT / 'drafter/cases/scenario_a.request.json')

    def test_missing_checkpoint_rejected_in_both_modes_before_client(self):
        request = self.request()
        del request['requirement_configuration']['benchmark']['policy_checkpoint']
        request['requirement_configuration_sha256'] = digest(request['requirement_configuration'])
        with self.assertRaises(ContractError):
            validate_request(request)
        with patch('drafter.generation.LocalModelClient') as client:
            for result in (run_mock_demo(request), generate_argument(request, None)):
                self.assertEqual(result['status'], 'rejected')
                self.assertFalse(result['model_called'])
                self.assertIsNone(result['argument'])
                self.assertTrue(result['diagnostics'])
            client.assert_not_called()

    def test_malformed_nested_fields_rejected_without_uncaught_errors(self):
        for path, value in ((('requirement_configuration', 'benchmark'), None),
                            (('requirement_configuration', 'benchmark', 'policy_checkpoint'), None),
                            (('target_execution',), []), (('evidence_package', 'records'), {}),
                            (('monitoring_scope', 'interval'), [False, 12])):
            with self.subTest(path=path):
                request = self.request()
                parent = request
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                with patch('drafter.generation.LocalModelClient') as client:
                    for result in (run_mock_demo(request), generate_argument(request, None)):
                        self.assertEqual(result['status'], 'rejected', result)
                        self.assertFalse(result['model_called'])
                    client.assert_not_called()

    def test_cli_rejects_and_saves_missing_checkpoint_for_both_modes(self):
        request = self.request()
        del request['requirement_configuration']['benchmark']['policy_checkpoint']
        request['requirement_configuration_sha256'] = digest(request['requirement_configuration'])
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / 'request.json'
            source.write_text(json.dumps(request))
            for mode in ('--mock-demo', '--generate'):
                destination = folder / (mode[2:] + '.json')
                arguments = ['drafter', mode, str(source), '--out', str(destination)]
                if mode == '--generate':
                    arguments += ['--model-config', str(ROOT / 'drafter/config/qwen3_32b_vllm.example.json')]
                with patch('sys.argv', arguments), redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 1)
                result = read_json(destination)
                self.assertEqual(result['status'], 'rejected')
                self.assertFalse(result['model_called'])

    def test_cli_deep_or_invalid_json_saves_rejection_without_traceback(self):
        for index, content in enumerate(('[' * 2000 + '0' + ']' * 2000, '{broken', '{"a":1,"a":2}')):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                source, destination, review = folder / 'input.json', folder / 'report.json', folder / 'review.md'
                source.write_text(content)
                args = ['drafter', '--mock-demo', str(source), '--out', str(destination), '--review-out', str(review)]
                with patch('sys.argv', args), redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(main(), 1)
                report = read_json(destination)
                self.assertEqual(report['contract_status'], 'rejected')
                self.assertFalse(report['model_called'])
                self.assertNotIn('Traceback', output.getvalue())
                self.assertIn('No argument was accepted', review.read_text())
