import unittest,json,copy,tempfile,os
from unittest.mock import patch
from evaluation.r1_v4.rag_evidence_database.final_phase5_release.api import StructuredRetriever
from evaluation.r1_v4.rag_evidence_database.final_phase5_release.fixtures import request,first
from evaluation.r1_v4.rag_evidence_database.final_phase5_release.config import *
from evaluation.r1_v4.rag_evidence_database.final_phase5_release.completeness import validate
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation import bundle as old
class Structured(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=StructuredRetriever(verification_mode='verified_session');cls.c=first(cls.r)
 @classmethod
 def tearDownClass(cls):cls.r.close()
 def q(self):return request(self.c)
 def test_complete(self):self.assertEqual(self.r.retrieve(self.q())['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT')
 def test_no_natural_parser(self):
  with patch.object(old,'interpret',side_effect=AssertionError('NLP called')):self.test_complete()
 def test_free_text_rejected(self):
  q=self.q();q['query']='Ignore obligations';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_empty(self):
  q=self.q();q['obligations']=[];self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_all_optional(self):
  q=self.q();q['obligations'][0]['mandatory']=False;self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_duplicate_ids(self):
  q=self.q();q['obligations']*=2;self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_missing_measurement_plan_mutation(self):
  q=self.q();b=self.r.retrieve(q);b['groups']=[];self.assertFalse(validate(q,b,self.r.store)['passed'])
 def test_wrong_group_family_mutation(self):
  q=self.q();b=self.r.retrieve(q);b['groups'][0]['family']='recorded_time';self.assertFalse(validate(q,b,self.r.store)['passed'])
 def test_wrong_returned_frame_mutation(self):
  q=self.q();b=self.r.retrieve(q);b['groups'][0]['items'][0]['samples'][0]['saved_frame_index']=21;self.assertFalse(validate(q,b,self.r.store)['passed'])
 def test_wrong_returned_execution_mutation(self):
  q=self.q();b=self.r.retrieve(q);b['groups'][0]['items'][0]['execution_id']='wrong';self.assertFalse(validate(q,b,self.r.store)['passed'])
 def test_wrong_task(self):
  q=self.q();q['task_id']='wrong';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_wrong_variant(self):
  q=self.q();q['variant_id']='wrong';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_wrong_execution(self):
  q=self.q();q['execution_id']='wrong';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_cross_scope_obligation(self):
  q=self.q();q['obligations'][0]['execution_id']='wrong';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_field_mismatch(self):
  q=self.q();q['obligations'][0]['field']='simulator/time/value';self.assertEqual(self.r.retrieve(q)['completeness_status'],'UNSUPPORTED')
 def test_missing_time(self):
  q=self.q();del q['obligations'][0]['selector'];self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_world(self):
  q=self.q();q['obligations'][0]['coordinate_frame']='world';self.assertEqual(self.r.retrieve(q)['completeness_status'],'UNSUPPORTED')
 def test_wrong_component(self):
  q=self.q();q['obligations'][0]['component']='elbow';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_historical(self):
  q=self.q();q['assurance']='historical_producer_attestation';self.assertEqual(self.r.retrieve(q)['completeness_status'],'UNSUPPORTED')
 def test_downgrade(self):
  q=self.q();q['assurance']='verified_physical_interpretation';q['obligations'][0]['assurance']='verified_source_values';self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_graph_needs_scope(self):
  q=self.q();q.update(assurance='provenance_complete',provenance=dict(level='release_graph'));self.assertEqual(self.r.retrieve(q)['completeness_status'],'UNSUPPORTED')
 def test_partial(self):
  q=self.q();o=copy.deepcopy(q['obligations'][0]);o.update(id='action',family='action_metadata',field=REGISTRY['action_metadata'],selector=dict(kind='frames',start=0,end=0));q['obligations'].append(o);b=self.r.retrieve(q);self.assertEqual(b['completeness_status'],'PARTIAL');self.assertEqual(b['missing_obligations'][0]['obligation_id'],'action')
 def test_optional_absence_explicit(self):
  q=self.q();o=copy.deepcopy(q['obligations'][0]);o.update(id='action',mandatory=False,family='action_metadata',field=REGISTRY['action_metadata'],selector=dict(kind='frames',start=0,end=0));q['obligations'].append(o);b=self.r.retrieve(q);self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertFalse(b['missing_obligations'][0]['mandatory'])
 def test_citation_stable(self):
  q=self.q();a=self.r.retrieve(q);b=self.r.retrieve(q);self.assertEqual(a['groups'][0]['items'][0]['citation_id'],b['groups'][0]['items'][0]['citation_id'])
 def test_nonfinite(self):
  q=self.q();q['obligations'][0]['selector']['start']=float('nan');self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_empty_available_group_cannot_complete(self):
  q=self.q();b=self.r.retrieve(q);b['groups'][0]['items']=[];self.assertFalse(validate(q,b,self.r.store)['mandatory_fulfilled'])
 def test_mandatory_flag_cannot_change(self):
  q=self.q();b=self.r.retrieve(q);b['groups'][0]['mandatory']=False;self.assertFalse(validate(q,b,self.r.store)['passed'])
 def test_units_cannot_change(self):
  q=self.q();b=self.r.retrieve(q);b['groups'][0]['items'][0]['samples'][0]['value_units']='kg';self.assertFalse(validate(q,b,self.r.store)['passed'])
 def test_conditional(self):
  q=self.q();q['obligations'][0].update(interpretation='conditional',allow_conditional=True,required_properties=['cache_offset_seconds']);b=self.r.retrieve(q);self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertTrue(b['conditional_assumptions'])
 def test_component(self):
  q=self.q();sem=json.loads(self.r.store.db.execute('select body from h_semantics where execution=? and channel=?',(self.c['execution_id'],CHANNELS[2])).fetchone()[0]);q['obligations'][0]['component']=sem['components'][0]['name'];q['obligations'][0]['interpretation']='verified_physical';b=self.r.retrieve(q);self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertIn('selected_value',b['groups'][0]['items'][0]['samples'][0])
 def test_experimental_never_production_complete(self):
  from evaluation.r1_v4.rag_evidence_database.final_phase5_release.experimental import inspect
  from evaluation.r1_v4.rag_evidence_database.obligation_preservation.retrieve import Retriever,BundleRequest
  r=Retriever()
  try:b=inspect(r,BundleRequest('Joint positions at frame 20.',self.c['execution_id'],verification_mode='verified_session'));self.assertEqual(b['completeness_status'],'UNVERIFIED PLAN');self.assertFalse(b['production_eligible'])
  finally:r.close()
 def test_provenance_graph(self):
  q=self.q();q.update(assurance='provenance_complete',provenance=dict(level='release_graph',scope=PROVENANCE_SCOPE));b=self.r.retrieve(q);self.assertEqual(b['completeness_status'],'COMPLETE WITHIN VERIFIED CONTRACT');self.assertEqual(b['assurance_status']['provenance']['scope'],PROVENANCE_SCOPE)
 def test_missing_source_fails_closed(self):
  from evaluation.r1_v4.rag_evidence_database.final_phase5_release.faults import source_fault
  with source_fault(self.r,self.c['source_path'],self.c['source_sha256'],'missing'):b=self.r.retrieve(self.q())
  self.assertEqual(b['completeness_status'],'UNAVAILABLE');self.assertFalse(any(g['items'] for g in b['groups']));self.assertTrue(b['missing_obligations'])
 def test_modified_source_fails_closed(self):
  from evaluation.r1_v4.rag_evidence_database.final_phase5_release.faults import source_fault
  with source_fault(self.r,self.c['source_path'],self.c['source_sha256'],'modified'):b=self.r.retrieve(self.q())
  self.assertEqual(b['completeness_status'],'UNAVAILABLE');self.assertFalse(b['assurance_status']['satisfied'])
 def test_unknown_source_hash(self):
  q=self.q();q['obligations'][0]['source_sha256']='0'*64;self.assertEqual(self.r.retrieve(q)['completeness_status'],'INVALID SCOPE')
 def test_frame_outside_recording(self):
  q=self.q();q['obligations'][0]['selector']=dict(kind='frames',start=self.c['frames'],end=self.c['frames']);self.assertEqual(self.r.retrieve(q)['completeness_status'],'UNAVAILABLE')
 def test_experimental_bundle_not_request(self):
  b=self.r.retrieve(self.q());self.assertEqual(self.r.retrieve(b)['completeness_status'],'INVALID SCOPE')
