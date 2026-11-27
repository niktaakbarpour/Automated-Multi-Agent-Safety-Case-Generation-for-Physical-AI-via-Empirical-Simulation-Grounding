import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.publication_v1.validate_publication import (
    ROOT,
    validate_case_assessments,
    validate_publication,
)


class PublicationIntegrityTests(unittest.TestCase):
    def test_committed_publication_passes_all_checks(self):
        validate_publication(ROOT)

    def test_assessment_counts_are_semantically_checked(self):
        with (ROOT / "CASE_ASSESSMENTS.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        rows[0]["final_assessment"] = "confirmed_false_complete"
        with self.assertRaisesRegex(ValueError, "unexpected assessment counts"):
            validate_case_assessments(rows)

    def test_fault_fixture_inventory_is_semantically_checked(self):
        with (ROOT / "CASE_ASSESSMENTS.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        next(row for row in rows if row["case_id"] == "KH2-C8-23")["fault_fixture_required"] = ""
        with self.assertRaisesRegex(ValueError, "frozen fault-fixture case set changed"):
            validate_case_assessments(rows)

    def test_noncanonical_line_endings_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "publication_v1"
            shutil.copytree(ROOT, copy)
            path = copy / "CASE_ASSESSMENTS.csv"
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "canonical UTF-8 with LF"):
                validate_publication(copy)

    def test_stale_hash_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "publication_v1"
            shutil.copytree(ROOT, copy)
            path = copy / "SHA256SUMS.txt"
            text = path.read_text(encoding="utf-8")
            path.write_text("0" * 64 + text[64:], encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                validate_publication(copy)


if __name__ == "__main__":
    unittest.main()
