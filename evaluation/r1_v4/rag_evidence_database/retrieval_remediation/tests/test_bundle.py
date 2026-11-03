import unittest,json,tempfile,shutil,os
from pathlib import Path
from dataclasses import replace
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.config import WORK,CHANNELS,DATABASE_SHA
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import Retriever,BundleRequest
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.store import BundleStore,SourceError,VerifiedReferences
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.planner import interpret
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.compat import retrieve as strict_legacy
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.retrieval import VariantQuery
class BundleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  b=json.loads((WORK/'BUILD.json').read_text());cls.r=Retriever(WORK/'catalogue.sqlite',b['sha256']);cls.e=cls.r.catalogue.execute('select execution from catalogue order by execution limit 1').fetchone()[0];cls.c=json.loads(cls.r.catalogue.execute('select body from catalogue where execution=?',(cls.e,)).fetchone()[0]);cls.q=BundleRequest('Finger positions and arm speeds at frame 20.',cls.e,verification_mode='verified_session')
 @classmethod
 def tearDownClass(cls):cls.r.close()
 def test_mixed_intents_do_not_cross_pos_and_speed(self):
  p=interpret(self.q.query,self.c,{});self.assertEqual(p['families'],[CHANNELS[0],CHANNELS[3]])
 def test_two_families_complete(self):
  b=self.r.retrieve(self.q);self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertEqual(set(b['requested_families']),{CHANNELS[0],CHANNELS[3]})
 def test_single_document_not_complete(self):self.assertEqual(self.r.retrieve(self.q,'field_single')['completeness_status'],'PARTIAL')
 def test_no_safety_sufficiency(self):self.assertEqual(self.r.retrieve(self.q)['safety_claim_sufficiency'],'NOT_EVALUATED')
 def test_unknown_execution_denied(self):self.assertEqual(self.r.retrieve(replace(self.q,execution_id='unknown'))['completeness_status'],'INVALID SCOPE')
 def test_wrong_task_denied(self):self.assertEqual(self.r.retrieve(replace(self.q,task_id='wrong'))['completeness_status'],'INVALID SCOPE')
 def test_wrong_variant_denied(self):self.assertEqual(self.r.retrieve(replace(self.q,variant_id='wrong'))['completeness_status'],'INVALID SCOPE')
 def test_unknown_object_not_substituted(self):self.assertEqual(self.r.retrieve(replace(self.q,object_id='cup_unknown'))['completeness_status'],'AMBIGUOUS')
 def test_missing_instant_is_ambiguous(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give arm positions.'))['completeness_status'],'AMBIGUOUS')
 def test_historical_cannot_downgrade(self):
  b=self.r.retrieve(replace(self.q,assurance='historical_producer_attestation'));self.assertFalse(b['groups']);self.assertEqual(b['completeness_status'],'UNSUPPORTED')
 def test_unsupported_assurance(self):self.assertEqual(self.r.retrieve(replace(self.q,assurance='safety_guaranteed'))['completeness_status'],'UNSUPPORTED')
 def test_world_transform_cannot_complete(self):self.assertNotEqual(self.r.retrieve(replace(self.q,coordinate_frame='world'))['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_no_synchronized_instant(self):self.assertEqual(self.r.retrieve(replace(self.q,alignment='same_physical_instant'))['completeness_status'],'UNSUPPORTED')
 def test_no_interpolated_time(self):
  b=self.r.retrieve(replace(self.q,query='Give arm joint positions.',seconds_interval=(.011,.012)));self.assertEqual(b['completeness_status'],'UNAVAILABLE')
 def test_negative_interval(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give arm positions.',frame_interval=(-1,1)))['completeness_status'],'INVALID SCOPE')
 def test_conflicting_scope_cannot_be_overridden_by_plan(self):
  b=self.r.retrieve(replace(self.q,frame_interval=(21,21),plan=(CHANNELS[0],)));self.assertEqual(b['completeness_status'],'INVALID SCOPE')
 def test_action_metadata_is_original_record(self):
  b=self.r.retrieve(replace(self.q,query='Collect arm positions and action metadata before and after action 4.'));g=next(g for g in b['groups'] if g['family']=='action_metadata');self.assertEqual(g['items'][0]['value']['policy_step'],4);self.assertFalse(g['items'][0]['value']['executed_action_reference']['materialized'])
 def test_geometry_alias_only_symbolic(self):
  b=self.r.retrieve(replace(self.q,query='Identify the main_table body and geometry.'));self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertEqual(b['groups'][0]['items'][0]['origin'],'existing_derived_symbolic_identity')
 def test_strict_compat_preserves_ids(self):
  obj=sorted(self.c['objects'])[0];r=strict_legacy(self.r.store,VariantQuery(self.e,object_id=obj,interval=(20,20),evidence_types=('native_geometry',)));self.assertEqual(r['status'],'ok');self.assertTrue(r['groups'][0]['result']['results'][0]['id'].startswith('ev:'))
 def test_strict_geometry_rejects_hash_matching_symlink(self):
  b=self.r.store.binding(self.e)
  with tempfile.TemporaryDirectory(dir=WORK) as d:
   p=Path(d)/'source.xml';shutil.copyfile(b['xml_path'],p);link=Path(d)/'alias.xml';link.symlink_to(p)
   with self.assertRaises(SourceError):self.r.store.check_binding(dict(b,xml_path=str(link)),'strict')

 def test_two_distinct_single_anchors_ambiguous(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Finger positions at frame 20 and frame 30.'))['completeness_status'],'AMBIGUOUS')
 def test_two_distinct_actions_ambiguous(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Finger positions around action 2 and action 9.'))['completeness_status'],'AMBIGUOUS')

 def test_metadata_cannot_satisfy_physical_assurance(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give source hash.',assurance='verified_physical_interpretation'))['completeness_status'],'UNSUPPORTED')
 def test_metadata_cannot_ignore_unit(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give source hash.',units='kg'))['completeness_status'],'UNSUPPORTED')
 def test_metadata_cannot_ignore_coordinate(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give source hash.',coordinate_frame='world'))['completeness_status'],'UNSUPPORTED')
 def test_metadata_cannot_ignore_property(self):self.assertEqual(self.r.retrieve(replace(self.q,query='Give source hash.',required_properties=('sensor_clock_synchronized',)))['completeness_status'],'UNSUPPORTED')
