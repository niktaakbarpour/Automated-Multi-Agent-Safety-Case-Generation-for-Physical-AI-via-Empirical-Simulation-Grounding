"""Recorded software regressions, NOT adjudicated event labels or validation."""
import json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from checker import analyze,load_config
class RecordedRegressions(unittest.TestCase):
 def test_014_previous_candidate_now_short_unconfirmed_sequence(self):
  data=json.loads((R/'fixtures/recorded_episode_014_base.json').read_text());c=load_config(R/'config.json');ns={};exec(compile((R/'fixtures/previous_checker.py').read_text(),'previous_checker','exec'),ns)
  self.assertTrue(any(e['confirmation_frame']==283 and e['type']=='post_lift_drop_candidate' for e in ns['analyze'](data['samples'],c)['events']))
  result=analyze(data['samples'],c);self.assertFalse(result['events']);seq=next(s for s in result['unconfirmed_descent_sequences'] if s['contact_free_descent_intervals'][0]['start']['frame']==282);self.assertEqual(seq['count'],1);self.assertTrue(seq['origin_history']['lift_candidate'])
 def test_002_broad_later_geometry_changes_type(self):
  data=json.loads((R/'fixtures/recorded_episode_002_broad.json').read_text());c=load_config(R/'config.json');c.update({k:v for p in c['sensitivity_profiles'] if p['name']=='broad' for k,v in p.items() if k!='name'})
  e=analyze(data['samples'],c)['events'][0];self.assertEqual(e['initial_classification'],'table_support_loss_descent_ambiguous_candidate');self.assertEqual(e['type'],'direct_table_departure_descent_candidate');self.assertEqual(e['classification_history'][1]['reference']['frame'],7);self.assertEqual(e['phase'],'setup')
