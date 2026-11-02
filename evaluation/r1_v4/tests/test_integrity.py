import socket
import unittest
from evaluation.r1_v4.integrity import verify
@unittest.skipUnless(socket.gethostname().lower()=='hestia','Read-only live frozen checks require Hestia')
class IntegrityTests(unittest.TestCase):
    def test_P02_frozen_v3_seals_predictions_and_scoring(self):
        result=verify()
        self.assertTrue(result['passed'])
        self.assertEqual(result['human_scoring_protected_files'],8)
        self.assertEqual(result['audited_sources'],16)
