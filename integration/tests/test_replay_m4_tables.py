import unittest

from integration.replay_m4_tables import TABLES, check_table, rq1


class ManuscriptMismatchTest(unittest.TestCase):
    def test_changed_retrieval_precision_fails(self):
        altered = TABLES.read_text().replace("0.958", "0.950", 1)
        with self.assertRaisesRegex(ValueError, "tab:rq1 manuscript mismatch"):
            check_table(altered, "tab:rq1", rq1())
