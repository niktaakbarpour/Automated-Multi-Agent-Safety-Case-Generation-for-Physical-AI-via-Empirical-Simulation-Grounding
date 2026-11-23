import csv
import subprocess
import sys
import unittest
from pathlib import Path

D = Path(__file__).resolve().parent


class SourceEligibilityTests(unittest.TestCase):
    def test_generated_matrix_and_blocker_counts(self):
        subprocess.run([sys.executable, str(D.parent / "build_source_eligibility_matrix.py"), "--check"], check=True)
        with (D.parent / "SOURCE_ELIGIBILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 20)
        self.assertEqual(len({r["canonical_execution_id"] for r in rows}), 20)
        self.assertEqual(len({r["source_trajectory_sha256"] for r in rows}), 20)
        self.assertTrue(all(r["admission_decision"] == "not_admitted" for r in rows))
        self.assertTrue(all(r["request_sha256"] == "" for r in rows))


if __name__ == "__main__":
    unittest.main()
