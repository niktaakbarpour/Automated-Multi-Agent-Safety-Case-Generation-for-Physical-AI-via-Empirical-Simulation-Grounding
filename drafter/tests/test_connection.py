"""Driver checks use a fake loopback server; no local model is required."""
from contextlib import redirect_stdout
from pathlib import Path
import io
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from drafter.connection import check_connection, PROBE_SCHEMA
from drafter.llm import FrozenLocalModelConfig
from drafter.validation import ROOT
from drafter.__main__ import main
from .test_llm import fake_endpoint, configuration


class ConnectionDriverTests(unittest.TestCase):
    def config(self, state):
        return FrozenLocalModelConfig.from_mapping(configuration(state['base_url']))

    def test_discovery_does_not_trigger_completion(self):
        with fake_endpoint() as state:
            result = check_connection(self.config(state))
            self.assertEqual(result['status'], 'ready')
            self.assertFalse(result['model_called'])
            self.assertEqual([r['method'] for r in state['requests']], ['GET'])

    def test_smoke_validates_fixed_json_and_preserves_trace(self):
        with fake_endpoint() as state:
            state['completion_body']['choices'][0]['message']['content'] = json.dumps(
                {'probe_id': 'drafter-connection-v1', 'status': 'ok'})
            result = check_connection(self.config(state), smoke_test=True)
            self.assertEqual(result['status'], 'passed')
            self.assertTrue(result['model_called'])
            self.assertFalse(result['argument_generated'])
            self.assertFalse(result['project_evidence_sent'])
            self.assertEqual([r['method'] for r in state['requests']], ['GET', 'POST'])
            self.assertEqual(result['probe']['json_schema'], PROBE_SCHEMA)
            self.assertRegex(result['probe']['prompt_sha256'], '^[0-9a-f]{64}$')
            self.assertIn('choices', result['completion']['raw_response'])

    def test_well_formed_wrong_json_is_not_a_successful_smoke_test(self):
        with fake_endpoint() as state:
            result = check_connection(self.config(state), smoke_test=True)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['diagnostics'][0]['code'], 'probe_schema_mismatch')

    def test_missing_model_never_falls_back(self):
        with fake_endpoint() as state:
            state['discovery_body'] = {'data': [{'id': 'some-other-model'}]}
            result = check_connection(self.config(state), smoke_test=True)
            self.assertEqual(result['status'], 'failed')
            self.assertFalse(result['model_called'])
            self.assertEqual(len(state['requests']), 1)

    def test_transport_failure_does_not_claim_a_model_reply(self):
        with fake_endpoint() as state:
            state['status'] = 500
            result = check_connection(self.config(state), smoke_test=True)
            self.assertEqual(result['status'], 'failed')
            self.assertFalse(result['model_called'])
            self.assertIsNone(result['completion'])

    def test_cli_checks_model_with_explicit_config(self):
        with fake_endpoint() as state, tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps(configuration(state['base_url'])))
            report = Path(directory) / 'report.json'
            command = [sys.executable, '-m', 'drafter', '--check-model',
                       '--model-config', str(config), '--out', str(report)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(report.read_text())['status'], 'ready')
            before = report.read_bytes()
            calls = len(state['requests'])
            repeat = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(repeat.returncode, 1)
            self.assertEqual(report.read_bytes(), before)
            self.assertEqual(len(state['requests']), calls)

    def test_output_write_failure_preserves_completed_model_execution_report(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps(configuration()))
            output = Path(directory) / 'missing-parent/report.json'
            completed = {'status': 'passed', 'model_called': True, 'run_id': 'completed-contract-probe'}
            buffer = io.StringIO()
            with patch('sys.argv', ['drafter', '--smoke-test-model', '--model-config', str(config), '--out', str(output)]), \
                    patch('drafter.connection.check_connection', return_value=completed) as check, redirect_stdout(buffer):
                code = main()
            self.assertEqual(code, 1)
            self.assertEqual(check.call_count, 1)
            result = json.loads(buffer.getvalue())
            self.assertEqual(result['status'], 'passed')
            self.assertTrue(result['model_called'])
            self.assertEqual(result['run_id'], 'completed-contract-probe')
            self.assertEqual(result['output_write_error']['code'], 'report_not_saved')


if __name__ == '__main__':
    unittest.main()
