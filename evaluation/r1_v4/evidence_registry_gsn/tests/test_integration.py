"""Real development-only integration; no labels, media or physical judgments."""
import unittest,tempfile
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.demo import demonstrate
from evaluation.r1_v4.evidence_registry_gsn.registry import Registry
from evaluation.r1_v4.provenance import load,canonical

class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(dir='/disk/1/data/niktakbr');cls.out=Path(cls.tmp.name)/'demo';demonstrate(cls.out)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_real_development_records(self):
  r=Registry(self.out/'registry.sqlite')
  try:
   self.assertEqual(len(r.records()),18);self.assertTrue(all(x.execution_id=='libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db' for x in r.records()))
   self.assertTrue(all(x.provenance.get('development_only') for x in r.records()))
  finally:r.close()
 def test_four_distinctions(self):
  a=load(self.out/'ASSESSMENT.json');self.assertTrue(a['evidence_retrieved']);self.assertEqual(len(a['measurement_records_valid']),15);self.assertFalse(a['sufficient_for_physical_checking']);self.assertFalse(a['safety_claim_supported'])
 def test_known_gap(self):
  r=load(self.out/'RETRIEVAL.json');self.assertTrue(all(x['missing_intervals']==[[12,12]] for x in r['coverage'].values()))
 def test_no_ai_measurement_promotion(self):
  r=load(self.out/'REGISTRY_EXPORT.json');a=[x for x in r['records'] if x['kind']=='ai_reference_judgment'];self.assertEqual(len(a),1);self.assertEqual(a[0]['validation_status'],'provisional')
 def test_all_source_integrity(self):
  r=load(self.out/'REGISTRY_INTEGRITY.json');self.assertTrue(all(x['source']=='verified_source' and not x['dependencies'] for x in r['records'].values()))
 def test_graph_roundtrip(self):
  from evaluation.r1_v4.evidence_registry_gsn.gsn import Graph,Node,Edge
  x=load(self.out/'GRAPH.json');g=Graph(tuple(Node(**n) for n in x['nodes']),tuple(Edge(**e) for e in x['edges']),x['schema_version']);r=Registry(self.out/'registry.sqlite')
  try:g.validate(r);self.assertEqual(canonical(g.export()),canonical(x))
  finally:r.close()
 def test_json_schemas(self):
  import jsonschema
  from evaluation.r1_v4.evidence_registry_gsn.builder import HERE
  for name in ('registry_record.schema.json','gsn_graph.schema.json'):jsonschema.Draft202012Validator.check_schema(load(HERE/name))
  for record in load(self.out/'REGISTRY_EXPORT.json')['records']:jsonschema.validate(record,load(HERE/'registry_record.schema.json'))
  jsonschema.validate(load(self.out/'GRAPH.json'),load(HERE/'gsn_graph.schema.json'))
