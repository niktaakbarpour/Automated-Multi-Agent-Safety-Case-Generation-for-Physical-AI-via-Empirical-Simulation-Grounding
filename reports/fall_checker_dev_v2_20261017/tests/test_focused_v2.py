import unittest,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from checker import analyze,load_config
from run_development import build_frame_observations,commit_frame_observations
from test_checker import sample,seq
C=load_config(ROOT/'config.json')
class PersistenceAndLifecycle(unittest.TestCase):
 def test_exact_supported_10_free_11_12(self):
  s=[sample(10,support=True),sample(11,.43),sample(12,.40)]
  r=analyze(s,C);self.assertEqual(r['events'],[]);self.assertEqual(r['unconfirmed_descent_sequences'][0]['count'],1)
  r=analyze(s+[sample(13,.35)],C);e=r['events'][0];self.assertEqual(e['confirmation_frame'],13);self.assertEqual(e['descent_frames'],[11,13]);self.assertEqual(e['departure_bracket'],[10,11]);self.assertTrue(all(i['both_endpoints_contact_free'] for i in e['confirmation_window']))
 def test_indirect_and_gripper_endpoint_excluded(self):
  for key,val in [('indirect_candidate',True),('gripper_contacts',[76])]:
   s=seq([.5,.49,.48]);s[0][key]=val;self.assertEqual(analyze(s,C)['events'],[])
 def test_later_geometry_upgrade(self):
  s=[sample(10,support=True)]+seq([.50,.49,.48,.40],11)
  e=analyze(s,C)['events'][0];self.assertEqual(e['initial_classification'],'table_support_loss_descent_ambiguous_candidate');self.assertEqual(e['type'],'direct_table_departure_descent_candidate');self.assertEqual([h['reference']['frame'] for h in e['classification_history']],[13,14]);self.assertEqual(e['observed_event_span']['end']['frame'],14)
 def test_later_projection_upgrade(self):
  s=[sample(10,support=True)]+seq([.50,.49,.48,.47],11);s[-1]['outside_table_support_projection']=True
  self.assertEqual(analyze(s,C)['events'][0]['type'],'direct_table_departure_descent_candidate')
 def test_contact_ambiguity_not_erased(self):
  x=sample(11,.5,contacts=[76]);x['gripper_contacts']=[76]
  s=[sample(10,support=True),x]+seq([.50,.49,.48,.40],12);e=analyze(s,C)['events'][0]
  self.assertEqual(e['type'],'ambiguous_contact_departure_descent_candidate');self.assertTrue(e['strong_departure_evidence']);self.assertTrue(e['origin_history']['unresolved_contact_history'])
 def test_postlift_never_direct(self):
  s=[sample(10,support=True),sample(11,.5,contacts=[76,79],grip=True)]+seq([.49,.48,.47,.40],12)
  e=analyze(s,C)['events'][0];self.assertEqual(e['type'],'post_lift_drop_candidate')
 def test_recovery_does_not_erase_history(self):
  s=[sample(10,support=True)]+seq([.50,.49,.48,.40],11)+[sample(15,support=True)]
  e=analyze(s,C)['events'][0];self.assertEqual(len(e['classification_history']),2);self.assertEqual(e['ending']['reason'],'table_recontact');self.assertEqual(e['observed_event_span']['end']['frame'],15)
 def test_gap_censors_then_resets_origin(self):
  s=[sample(10,support=True)]+seq([.50,.49,.48],11)+[sample(14,valid=False)]+seq([.4,.3,.2],15)
  r=analyze(s,C);self.assertEqual(r['events'][0]['ending']['reason'],'recording_gap');self.assertEqual(r['events'][0]['observed_event_span']['end']['frame'],13);self.assertEqual(r['events'][1]['type'],'unsupported_descent_unknown_origin')
 def test_termination_censors(self):
  e=analyze([sample(10,support=True)]+seq([.50,.49,.48],11),C)['events'][0];self.assertTrue(e['ending']['censored']);self.assertEqual(e['ending']['reason'],'recording_termination');self.assertEqual(e['confirmation_frame'],13)
 def test_boundary_censors_setup(self):
  r=analyze(seq([.7,.6,.5],7)+[sample(10,.4)],C);self.assertEqual(r['events'][0]['ending']['reason'],'policy_interval_boundary');self.assertEqual(r['events'][0]['phase'],'setup')
 def test_timing_gap_is_explicit(self):
  s=[sample(10,support=True)]+seq([.50,.49,.48],11)+[sample(15,.40)]
  e=analyze(s,C)['events'][0];self.assertEqual(e['ending']['reason'],'timing_or_frame_gap');self.assertEqual(e['observed_event_span']['end']['frame'],13)
class AtomicFrame(unittest.TestCase):
 def test_late_object_or_profile_failure(self):
  names=['a','b'];profiles=[('base',C),('strict',C)];ref={'frame':11,'time':.55};entities={'a':'a','b':'b'}
  for fail_at in [2,3,4]:
   calls=[]
   def produce(index,entity,gp,gr,cts,c):
    calls.append(entity)
    if len(calls)==fail_at:raise ValueError('injected late error')
    return dict(valid=True,center_z=.5,bottom_z=.4,table_top_z=.43676)
   dest={p:{n:[] for n in names} for p,_ in profiles}
   staged,err=build_frame_observations(ref,None,entities,None,None,None,profiles,names,observation_fn=produce)
   self.assertIsNotNone(err);self.assertTrue(all(not r['valid'] for os in staged.values() for r in os.values()))
   commit_frame_observations(dest,staged,11);self.assertTrue(all(len(r)==1 and not r[0]['valid'] for os in dest.values() for r in os.values()))
   with self.assertRaises(ValueError):commit_frame_observations(dest,staged,11)
   self.assertTrue(all(len(r)==1 for os in dest.values() for r in os.values()))
 def test_success_once_per_object_profile(self):
  profiles=[('base',C),('strict',C)];names=['a','b'];fn=lambda *a:dict(valid=True,center_z=.5,bottom_z=.4,table_top_z=.43676)
  staged,err=build_frame_observations({'frame':0},None,{'a':1,'b':2},None,None,None,profiles,names,fn);d={p:{n:[] for n in names} for p,_ in profiles};commit_frame_observations(d,staged,0)
  self.assertIsNone(err);self.assertTrue(all(len(s)==1 for os in d.values() for s in os.values()))
