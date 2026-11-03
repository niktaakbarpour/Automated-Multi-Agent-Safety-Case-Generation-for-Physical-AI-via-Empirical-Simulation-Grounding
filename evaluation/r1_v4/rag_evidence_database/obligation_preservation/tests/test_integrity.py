import json,unittest
from dataclasses import replace
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.retrieve import Retriever,BundleRequest
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.config import CHANNELS
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.evaluate import fault
class Integrity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.r=Retriever();cls.e=cls.r.catalogue.execute('select execution from catalogue order by execution limit 1').fetchone()[0];cls.c=json.loads(cls.r.catalogue.execute('select body from catalogue where execution=?',(cls.e,)).fetchone()[0]);cls.q=BundleRequest('Joint positions at frame 20.',cls.e,verification_mode='verified_session')
 @classmethod
 def tearDownClass(cls):cls.r.close()
 def failed_source(self,kind):
  c=self.c
  with fault(self.r.store,dict(fault=kind,source_path=c['source_path'],source_sha256=c['source_sha256'])):b=self.r.retrieve(self.q)
  self.assertEqual(b['completeness_status'],'UNAVAILABLE');self.assertTrue(any(o['target']==CHANNELS[2] for o in b['query_obligations']));self.assertFalse(b['evidence_fulfillment']['passed'])
 def test_missing(self):self.failed_source('missing_source')
 def test_changed(self):self.failed_source('corrupt_source')
 def test_replaced_stale_identity(self):self.failed_source('replace_source')
 def test_symlink(self):self.failed_source('symlink_source')
 def test_instruction_bytes(self):self.failed_source('instruction_source')
 def test_recovery(self):self.assertEqual(self.r.retrieve(self.q)['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_wrong_variant(self):self.assertEqual(self.r.retrieve(replace(self.q,variant_id='wrong'))['completeness_status'],'INVALID SCOPE')
 def test_wrong_task(self):self.assertEqual(self.r.retrieve(replace(self.q,task_id='wrong'))['completeness_status'],'INVALID SCOPE')
 def test_reserved_metadata_only_no_payload(self):
  row=self.r.store.db.execute("select execution from rag_scope_status where status='excluded_reserved' limit 1").fetchone();self.assertIsNotNone(row);self.assertEqual(self.r.retrieve(replace(self.q,execution_id=row[0]))['completeness_status'],'INVALID SCOPE')
 def test_excluded_metadata_only_no_payload(self):
  row=self.r.store.db.execute("select execution from rag_scope_status where status='excluded_preflight' limit 1").fetchone();self.assertIsNotNone(row);self.assertEqual(self.r.retrieve(replace(self.q,execution_id=row[0]))['completeness_status'],'INVALID SCOPE')
 def test_incompatible_assurance(self):self.assertEqual(self.r.retrieve(replace(self.q,assurance='historical_producer_attestation'))['completeness_status'],'UNSUPPORTED')
 def test_metadata_cannot_satisfy_typed_physical_assurance(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give source hash.',assurance='verified_physical_interpretation'))['completeness_status'],'UNSUPPORTED')
 def test_parenthetical_conjunction(self):
  b=self.r.retrieve(replace(self.q,query='Joint positions (raw) and velocities at frame 20.'));self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertEqual(set(b['requested_families']),set(CHANNELS[2:4]))
