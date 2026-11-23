import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ShellEntrypointTest(unittest.TestCase):
    def test_shell_scripts_parse(self):
        for name in ("pipeline.sh", "run.sh", "collect.sh", "audit.sh"):
            subprocess.run(["bash", "-n", str(ROOT / name)], check=True)

    def test_pipeline_reports_missing_python(self):
        env = dict(os.environ, PYTHON="m4-python-command-that-does-not-exist")
        result = subprocess.run(
            ["bash", str(ROOT / "pipeline.sh"), "inventory"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 127)
        self.assertIn("was not found", result.stderr)
