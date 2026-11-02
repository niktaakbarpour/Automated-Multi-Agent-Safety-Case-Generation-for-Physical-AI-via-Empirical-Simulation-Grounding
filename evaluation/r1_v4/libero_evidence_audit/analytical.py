"""Declared physical interpretations test admission only; no physics is inferred."""
import copy,json,socket,unittest
from pathlib import Path
from evaluation.r1_v4.fixtures import make_bundle,seal
from evaluation.r1_v4.runtime import assess
from evaluation.r1_v4.contracts import Outcome
HERE=Path(__file__).resolve().parent
CASES=[
 ('stable_supported','N','N','Exact synthetic static support over every declared cell'),
 ('supported_sliding','U','U','Support persists during sliding; dynamic negative coverage is deferred'),
 ('intentional_lifting','V','U','Established supported lifting; intention is descriptive and unused'),
 ('fall_after_support_loss','V','V','All event premises stipulated, no holding, loss and downward phase in interval'),
 ('post_lift_release','V','U','Established prior lift excludes this drop; remaining domain lacks negative coverage'),
 ('initially_unsupported','NA','NA','Explicit synthetic exclusion of all designated support at boundary'),
 ('ambiguous_contact','V','U','Geometric contact cannot resolve initial load bearing'),
 ('missing_measurements','V','U','Necessary geometry observation missing locally'),
 ('timing_mismatch','V','IC','Incompatible necessary clock binding'),
 ('unsupported_geometry','V','IC','Non-BOX capability is unsupported'),
 ('invalid_measurement','V','U','Local malformed geometry cannot support dependent witness'),
]
def fixture(name,state):
 b=make_bundle((state,))
 rows=b['evidence']['records']
 def get(s):return next(r for r in rows if r['id']=='object_00_'+s)
 if name in ('intentional_lifting','post_lift_release'):get('fall')['payload']['handling_excluded']='T'
 if name=='ambiguous_contact':get('support')['truth']='U'
 if name=='missing_measurements':get('geometry')['validity']='missing'
 if name=='timing_mismatch':get('geometry')['frame']['clock']='unbound_clock'
 if name=='unsupported_geometry':b['configuration']['geometry_contract']['required_shape_capabilities']=['mesh']
 if name=='invalid_measurement':get('geometry')['validity']='invalid_local'
 return seal(b)
def generate():
 assert socket.gethostname().lower()=='hestia'
 results=[]
 for name,state,expected,description in CASES:
  b=fixture(name,state);result=assess(b)
  want=getattr(Outcome,expected).value
  assert result['execution_outcome']==want,(name,result['execution_outcome'],want)
  assert result['physical_safety_conclusion'] is False
  assert result['empirical_profiles_enabled'] is False
  payload=dict(synthetic=True,purpose='analytical_fixture',interpretation=description,physical_truth_is_stipulated=True,empirical_reference=False,expected_outcome=want,bundle=b)
  (HERE/'ANALYTICAL_FIXTURES'/f'{name}.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
  results.append(dict(case=name,expected=want,actual=result['execution_outcome'],passed=True,physical_safety_conclusion=False))
 (HERE/'ANALYTICAL_RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
 print('Analytical scenarios passed:',len(results))
class ContractCases(unittest.TestCase):
 def test_fixture_admission_and_empirical_guard(self):
  for name,state,expected,_ in CASES:
   with self.subTest(name=name):
    p=json.loads((HERE/'ANALYTICAL_FIXTURES'/f'{name}.json').read_text());r=assess(p['bundle'])
    self.assertEqual(r['execution_outcome'],getattr(Outcome,expected).value)
    self.assertTrue(p['synthetic']);self.assertFalse(r['physical_safety_conclusion']);self.assertFalse(r['empirical_profiles_enabled'])
 def test_no_fixture_is_empirical_reference(self):
  for p in (HERE/'ANALYTICAL_FIXTURES').glob('*.json'):
   x=json.loads(p.read_text());self.assertFalse(x['empirical_reference'])
if __name__=='__main__':generate()
