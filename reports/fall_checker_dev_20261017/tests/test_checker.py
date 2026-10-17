import unittest,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from checker import analyze,load_config,validate_config
from native_geometry_v2 import NativeGeometryIndex
from run_development import allowed_run,observations
import numpy as np
C=load_config(ROOT/'config.json')
def sample(i,z=.45,support=False,contacts=None,grip=False,indirect=False,valid=True):
 return dict(frame=i,time=i*.05,valid=valid,direct_support=support,indirect_candidate=indirect,other_contacts=contacts or [],gripper_contacts=([76,79] if grip else []),bilateral_gripper=grip,bottom_z=z-.01,center_z=z,table_top_z=.43676,whole_collision_below_tabletop=z+.01<.43676,outside_table_support_projection=False)
def seq(zs,start=10,**kw):return [sample(start+i,z,**kw) for i,z in enumerate(zs)]
class CheckerTests(unittest.TestCase):
 def result(self,s):return analyze(s,C)
 def test_supported_tipping(self):self.assertFalse(self.result(seq([.48,.46,.44],support=True))['events'])
 def test_unknown_initial(self):self.assertEqual(self.result(seq([1.,.9,.8]))['initial_applicability'],'initial_table_support_not_established')
 def test_indirect_unknown(self):self.assertEqual(self.result([sample(10,indirect=True)])['initial_applicability'],'unknown_indirect_support')
 def test_direct_fall(self):self.assertEqual(self.result([sample(10,support=True)]+seq([.43,.40,.35],11))['events'][0]['type'],'direct_table_departure_descent_candidate')
 def test_lift_drop(self):
  r=self.result([sample(10,support=True),sample(11,.49,contacts=[76,79],grip=True)]+seq([.48,.46,.43],12));self.assertEqual(r['events'][0]['type'],'post_lift_drop_candidate');self.assertEqual(r['requirement_verdict'],'not_assessed_pending_approval')
 def test_setup_then_floor(self):
  r=self.result([sample(0,support=True)]+seq([.6,.5,.4],1)+[sample(10,.1),sample(11,.05,contacts=[8])]);self.assertEqual(r['events'][0]['phase'],'setup');self.assertNotEqual(r['initial_applicability'],'direct_table_support_candidate')
 def test_catch_preserved(self):
  r=self.result([sample(10,support=True)]+seq([.43,.4,.35],11)+[sample(14,.34,contacts=[76,79],grip=True)]);self.assertEqual(len(r['events']),1);self.assertIn('catch',r['events'][0]['ending']['type'])
 def test_non_floor_landing(self):
  r=self.result([sample(10,support=True)]+seq([.43,.4,.35],11)+[sample(14,.34,contacts=[156])]);self.assertEqual(r['events'][0]['ending']['contacts'],[156])
 def test_missing_breaks_chain(self):
  r=self.result([sample(10,support=True),sample(11,valid=False)]+seq([.4,.3,.2],12));self.assertTrue(r['gaps']);self.assertEqual(r['events'][0]['type'],'unsupported_descent_unknown_origin')
 def test_timing_mismatch(self):
  s=seq([.5,.4,.3]);s[1]['time']=99.;self.assertTrue(self.result(s)['gaps'])
 def test_missing_config_fails(self):
  c=dict(C);del c['descent_m']
  with self.assertRaises(ValueError):validate_config(c)
 def test_no_heldout_open(self):
  with self.assertRaises(ValueError):allowed_run('held',{'development':[],'held_out':['held']})
 def test_native_id_regression(self):
  idx=NativeGeometryIndex.load(ROOT/'corrected_native_geometry_v2.json');legacy=json.loads((ROOT/'fixtures/legacy_simulator_index.json').read_text());self.assertEqual(idx.by_id(10)['owner_body'],'living_room_table_col');self.assertEqual(idx.by_id(149)['name'],'milk_1_g1')
  with self.assertRaises(ValueError):idx.by_id(161)
  with self.assertRaises(ValueError):NativeGeometryIndex(legacy)
 def test_side_contact_not_support(self):
  idx=NativeGeometryIndex.load(ROOT/'corrected_native_geometry_v2.json');gp=np.zeros((161,3));gr=np.tile(np.eye(3),(161,1,1));gp[104]=[0,0,.6];gp[10]=[0,0,.4]
  c=dict(C,table_geom_ids=[10]);entity={'native_geom_ids':[104]}
  s=observations(idx,entity,gp,gr,[dict(geom1=10,geom2=104,pos=[0,0,.4],dist=0.)],c);self.assertFalse(s['direct_support']);self.assertEqual(s['side_or_unresolved_table_contacts'],[10])
 def test_phase_guard(self):
  idx=NativeGeometryIndex.load(ROOT/'corrected_native_geometry_v2.json')
  with self.assertRaises(ValueError):idx.validate_snapshot_transforms(np.zeros((29,3)),np.ones((29,4)),np.zeros((160,3)),np.zeros((160,9)))
if __name__=='__main__':unittest.main()

class AdditionalTests(unittest.TestCase):
 def test_ambiguous_gripper_not_direct(self):
  s=[sample(10,support=True),sample(11,.45,contacts=[76],grip=False)]+seq([.44,.42,.4],12);s[1]['gripper_contacts']=[76]
  self.assertEqual(analyze(s,C)['events'][0]['type'],'ambiguous_contact_departure_descent_candidate')
 def test_no_floor_required(self):
  r=analyze([sample(10,support=True)]+seq([.43,.4,.35],11),C);self.assertIsNone(r['events'][0]['ending'])
 def test_recovery_keeps_event(self):
  r=analyze([sample(10,support=True)]+seq([.43,.4,.35],11)+[sample(14,support=True)],C);self.assertEqual(len(r['events']),1)
 def test_table_departure_observation(self):
  r=analyze([sample(10,support=True),sample(11,.45)],C);self.assertEqual(r['support_transitions'][0]['type'],'table_support_candidate_departed');self.assertFalse(r['events'])
 def test_missing_boundary_unknown(self):self.assertEqual(analyze(seq([.4,.3,.2],11),C)['initial_applicability'],'unknown_missing_measurement')
 def test_nan_contact_rejected(self):
  idx=NativeGeometryIndex.load(ROOT/'corrected_native_geometry_v2.json');gp=np.zeros((161,3));gr=np.tile(np.eye(3),(161,1,1))
  with self.assertRaises(ValueError):observations(idx,{'native_geom_ids':[104]},gp,gr,[dict(geom1=10,geom2=104,pos=[float('nan'),0,0],dist=0)],C)
