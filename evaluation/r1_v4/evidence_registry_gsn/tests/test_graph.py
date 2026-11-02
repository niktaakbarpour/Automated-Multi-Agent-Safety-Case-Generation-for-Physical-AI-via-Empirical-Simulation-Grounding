from dataclasses import replace
import unittest
import test_registry as fixtures
from evaluation.r1_v4.evidence_registry_gsn.gsn import Node,Edge,Graph
from evaluation.r1_v4.evidence_registry_gsn.retrieval import subtract
from evaluation.r1_v4.provenance import canonical

class GraphTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.RegistryTests();self.fixture.setUp();self.registry=self.fixture.registry;self.r=self.fixture.record;self.fixture.add()
  self.scope=dict(requirement_id='R1',requirement_version='2.0.0',execution_id='synthetic-execution',object_id='obj',interval=(1,3),domain='frame',clock='saved_frame')
  self.goal=Node('G','goal','Unresolved R1',self.scope,{'synthetic':True},'unresolved','unresolved_conclusion',physical_claim=True)
  self.solution=Node('E','solution','Measurement available',self.scope,{k:getattr(self.r,k) for k in ('source_path','source_sha256','selector')},'verified_measurement','retrieved_observation',self.r.id)
  self.graph=Graph((self.goal,self.solution),(Edge('G','E','supported_by'),))
 def tearDown(self):self.fixture.tearDown()
 def test_valid_trace(self):self.graph.validate(self.registry)
 def test_stable_export(self):self.assertEqual(canonical(self.graph.export()),canonical(replace(self.graph,nodes=tuple(reversed(self.graph.nodes))).export()))
 def bad(self,g):
  with self.assertRaises(ValueError):g.validate(self.registry)
 def test_invalid_evidence_id(self):self.bad(replace(self.graph,nodes=(self.goal,replace(self.solution,evidence_id='missing'))))
 def test_incorrect_source(self):self.bad(replace(self.graph,nodes=(self.goal,replace(self.solution,provenance={'source_path':'wrong'}))))
 def test_invalid_edge(self):self.bad(replace(self.graph,edges=(Edge('E','G','supported_by'),)))
 def test_missing_endpoint(self):self.bad(replace(self.graph,edges=(Edge('G','missing','supported_by'),)))
 def test_promotion(self):self.bad(replace(self.graph,nodes=(replace(self.goal,validation_status='verified_measurement'),self.solution)))
 def test_promotion_bypass_flag(self):self.bad(replace(self.graph,nodes=(replace(self.goal,physical_claim=False,validation_status='verified_measurement'),self.solution)))
 def test_duplicate_node(self):self.bad(replace(self.graph,nodes=(self.goal,self.goal)))
 def test_scope_mismatch(self):self.bad(replace(self.graph,nodes=(self.goal,replace(self.solution,scope={**self.scope,'object_id':'other'}))))
 def test_judgment_origin(self):self.bad(replace(self.graph,nodes=(self.goal,replace(self.solution,origin='human_reference_judgment'))))
 def test_cycle(self):
  child=replace(self.goal,id='G2');self.bad(Graph((self.goal,child),(Edge('G','G2','supported_by'),Edge('G2','G','supported_by'))))
 def test_version(self):self.bad(replace(self.graph,schema_version='2'))
 def test_time_gap(self):self.assertEqual(subtract((0.,2.),[(0.,.5),(1.,2.)]),[[.5,1.]])
 def test_missing_time_point(self):self.assertEqual(subtract((1.,1.),[]),[[1.,1.]])
 def test_solution_interval_overclaim(self):
  goal=replace(self.goal,scope={**self.scope,'interval':(1,4),'clock':'saved_frame','domain':'frame'})
  solution=replace(self.solution,scope=goal.scope)
  self.bad(Graph((goal,solution),(Edge('G','E','supported_by'),)))
 def test_nested_solution_scope(self):
  goal=replace(self.goal,scope={**self.scope,'interval':(0,4),'clock':'saved_frame','domain':'frame'})
  solution=replace(self.solution,scope={**goal.scope,'interval':(1,3)})
  Graph((goal,solution),(Edge('G','E','supported_by'),)).validate(self.registry)
