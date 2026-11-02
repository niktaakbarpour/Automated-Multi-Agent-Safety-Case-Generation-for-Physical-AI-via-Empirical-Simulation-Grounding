import unittest
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.audit import HERE

class PartitionAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.audit=load(HERE/'PARTITION_DETAILS.json');cls.rows=cls.audit['partitions']
 def test_forty_partitions(self):self.assertEqual(len(self.rows),40)
 def test_total_execution_count(self):self.assertEqual(sum(r['executions'] for r in self.rows),2000)
 def test_no_false_reader_eligibility(self):self.assertEqual(sum(r['candidate_database_only'] for r in self.rows if r['xml_identical_to_existing']),0)
 def test_secondary_cohort_excluded(self):
  r=next(r for r in self.rows if r['partition']=='long/task_01');self.assertEqual(r['restricted_evaluation'],50);self.assertEqual(r['candidate_database_only'],0)
 def test_all_sixty_reserved(self):self.assertEqual(len(self.audit['excluded_execution_ids']),60)
 def test_all_candidate_member_closures(self):self.assertTrue(all(r['all_required_members_mapped'] for r in self.rows));self.assertEqual(sum(r['candidate_member_count'] for r in self.rows),1900*9)
 def test_inventory_provenance(self):self.assertEqual(sha(REPO/'data/runs.json'),self.audit['source_inventory_sha256'])
 def test_baseline_hash(self):self.assertEqual(sha('/disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite'),'e5dc6aadd9444d945abe9aeb1c54461b0cd6ad5308b43c6fdc40fac65c8d07ca')
