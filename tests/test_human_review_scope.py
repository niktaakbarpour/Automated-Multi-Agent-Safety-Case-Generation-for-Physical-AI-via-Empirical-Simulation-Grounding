"""Scope/form contract tests; no detector, model, experiment or held-out data execution."""
import copy,csv,importlib.util,json,tempfile,unittest
from pathlib import Path
from jsonschema import ValidationError
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scope_verify',ROOT/'human_review_package/tools/verify_scope_update.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class ReviewScopeTest(unittest.TestCase):
    def setUp(self):
        p=ROOT/'human_review_package'
        self.value=json.loads((p/'requirement_scope.v3.json').read_text())
        self.schema=json.loads((p/'schemas/requirement_scope.v1.schema.json').read_text())
    def test_selected_package_contract(self):
        mod.verify(ROOT/'human_review_package')
    def test_selection_cannot_imply_review_or_validation(self):
        for field,value in [('independent_human_review_status','complete'),('event_label_status','approved'),('detector_validation_status','validated'),('all_team_members_approved',True),('numerical_parameters_approved',True)]:
            with self.subTest(field=field):
                doc=copy.deepcopy(self.value);doc[field]=value
                with self.assertRaises(ValidationError):mod.validate_scope(doc,self.schema)
    def test_wrong_origin_and_missing_scope_rejected(self):
        doc=copy.deepcopy(self.value);doc['decision_origin']='Team unanimously approved'
        with self.assertRaises(ValidationError):mod.validate_scope(doc,self.schema)
        doc=copy.deepcopy(self.value);del doc['scope_decisions']['F']
        with self.assertRaises(ValidationError):mod.validate_scope(doc,self.schema)
    def test_prefilled_human_judgment_rejected(self):
        src=ROOT/'human_review_package/reviewer_1/requirement_interpretation.csv'
        with src.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        rows[0]['interpretation']='violation'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'requirement_interpretation.csv'
            with p.open('w',encoding='utf-8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
            with self.assertRaises(AssertionError):mod.read_template(p)

if __name__=='__main__':unittest.main()
