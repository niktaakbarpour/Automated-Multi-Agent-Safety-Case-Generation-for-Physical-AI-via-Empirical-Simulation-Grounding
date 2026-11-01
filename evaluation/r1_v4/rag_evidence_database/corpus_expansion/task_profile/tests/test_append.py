import unittest
from dataclasses import replace
from evaluation.r1_v4.rag_evidence_database.tests import test_store as fixtures
from evaluation.r1_v4.rag_evidence_database.search import Query,search

class IndependentAppendTests(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.DatabaseTests();self.f.setUp();self.db=self.f.db;self.r=replace(self.f.r,provenance={**self.f.r.provenance,'development_only':False})
 def tearDown(self):self.f.tearDown()
 def test_closed_independent_append(self):
  self.db.put_execution('synthetic','input',[(self.r,'synthetic source','p')],stratum='corpus_expansion',independent=True);self.assertEqual(search(self.db,Query(stratum='corpus_expansion'))['matching_count'],1)
 def test_execution_identity_mismatch(self):
  with self.assertRaises(ValueError):self.db.put_execution('wrong','input',[(self.r,'source','p')],independent=True)
 def test_cross_execution_dependency_denied(self):
  with self.assertRaises(ValueError):self.db.put_execution('synthetic','input',[(replace(self.r,dependencies=('external',)),'source','p')],independent=True)
 def test_existing_execution_independent_denied(self):
  self.db.put_execution('synthetic','input',[(self.r,'source','p')],stratum='corpus_expansion',independent=True)
  with self.assertRaises(ValueError):self.db.put_execution('synthetic','input',[(self.r,'source','p')],stratum='corpus_expansion',independent=True)
 def test_corpus_not_reclassified_development(self):
  with self.assertRaises(ValueError):self.db.put_execution('synthetic','input',[(self.f.r,'source','p')],stratum='corpus_expansion',independent=True)
 def test_unknown_stratum_denied(self):
  with self.assertRaises(ValueError):self.db.put_execution('synthetic','input',[(self.r,'source','p')],stratum='unapproved')
 def test_unknown_stratum_query_denied(self):
  with self.assertRaises(ValueError):search(self.db,Query(stratum='unapproved'))
