import unittest

from integration.replay_m4_tables import TABLES, check_table, rq1, verify_revision_example_count


class ManuscriptMismatchTest(unittest.TestCase):
    def test_changed_retrieval_precision_fails(self):
        altered = TABLES.read_text().replace("0.958", "0.950", 1)
        with self.assertRaisesRegex(ValueError, "tab:rq1 manuscript mismatch"):
            check_table(altered, "tab:rq1", rq1())


class RevisionExampleCountTest(unittest.TestCase):
    def test_requires_expected_number_of_pass_records(self):
        output = "PASS  first\nPASS  second\nAll checks passed.\n"
        self.assertEqual(verify_revision_example_count(output, 2, "example"), 2)
        with self.assertRaisesRegex(ValueError, "expected 3 .* found 2"):
            verify_revision_example_count(output, 3, "example")

    def test_requires_success_summary(self):
        with self.assertRaises(ValueError):
            verify_revision_example_count("PASS  first\n", 1, "example")
