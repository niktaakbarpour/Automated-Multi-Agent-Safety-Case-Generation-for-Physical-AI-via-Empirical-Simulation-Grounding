import csv,unittest
from pathlib import Path
D=Path(__file__).resolve().parent.parent
def rows(name):
 with open(D/name,encoding="utf-8-sig") as f:return list(csv.DictReader(f))
class HeldoutReadiness(unittest.TestCase):
 def test_no_parent_arguments_fabricated(self):
  r=rows("PARENT_SOURCE_INVENTORY.csv")
  self.assertEqual(len(r),432)
  self.assertTrue(all(x["candidate_eligibility"]=="excluded_pending_original_drafter_gsn_input" for x in r))
 def test_no_new_mutations_or_requests(self):
  self.assertEqual(rows("NEW_MUTATION_MANIFEST.csv"),[])
  self.assertEqual(rows("REQUEST_MANIFEST.csv"),[])
if __name__=="__main__":unittest.main()
