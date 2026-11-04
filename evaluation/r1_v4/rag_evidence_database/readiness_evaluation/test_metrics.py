import unittest
from .metrics import mean,cluster_ci
from .run import canonical
class EvaluationChecks(unittest.TestCase):
 def test_empty_denominator_is_not_zero_accuracy(self):self.assertIsNone(mean([]))
 def test_macro_mean(self):self.assertEqual(mean([0.,1.,1.]),2/3)
 def test_bootstrap_deterministic(self):
  rows=[dict(case_id=str(i),assessment={'precision_at_1':float(i%2)}) for i in range(6)];cases={str(i):dict(suite='s',execution_id='e'+str(i//2)) for i in range(6)}
  self.assertEqual(cluster_ci(rows,cases,'precision_at_1',100),cluster_ci(rows,cases,'precision_at_1',100))
 def test_absent_ir_not_fabricated(self):self.assertIsNone(cluster_ci([],{},'MRR',100))
 def test_fault_diagnostics_only_are_excluded(self):
  a=dict(fault=dict(scratch_sha256='a',kind='corrupt'),output={'items':[{'value':1}]});b=dict(fault=dict(scratch_sha256='b',kind='corrupt'),output={'items':[{'value':1}]});self.assertEqual(canonical(a),canonical(b))
 def test_scratch_paths_not_substantive(self):
  from .config import WORK
  a=dict(fault=dict(kind='missing'),output=dict(reason=str(WORK)+'/fault-one/file'));b=dict(fault=dict(kind='missing'),output=dict(reason=str(WORK)+'/fault-two/file'));self.assertEqual(canonical(a),canonical(b))
 def test_actual_output_change_detected(self):self.assertNotEqual(canonical({'output':1}),canonical({'output':2}))
if __name__=='__main__':unittest.main()
