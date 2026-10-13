import tempfile,unittest
from pathlib import Path
from facts import instruction
from identifiers import Registry,step_id
class Contract(unittest.TestCase):
 def test_instruction(self):
  x=instruction('Open drawer.','open drawer');self.assertEqual(x['text'],'Open drawer.');self.assertTrue(x['exact_mismatch']);self.assertFalse(x['fallback_used']);self.assertEqual(x['environment_bddl_language'],'open drawer')
  x=instruction(None,'exact BDDL');self.assertTrue(x['fallback_used']);self.assertIsNone(x['exact_mismatch']);self.assertEqual(x['text'],'exact BDDL')
 def test_identity(self):
  with tempfile.TemporaryDirectory() as d:
   r=Registry(Path(d));r.register_many([('task','source-1',{'a':1})]);r.register_many([('task','source-1',{'a':1})]);self.assertEqual(r.require('task','source-1'),{'a':1})
   with self.assertRaises(ValueError):r.register_many([('run','source-1',{'a':1})])
   with self.assertRaises(ValueError):r.register_many([('requirement','req1',{})])
 def test_steps(self):
  self.assertEqual(step_id(0),0)
  for v in [-1,True,1.2,'1']:
   with self.assertRaises(ValueError):step_id(v)
if __name__=='__main__':unittest.main()
