"""Guard against accidental approval, scope narrowing or synthetic/recorded conflation."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ReviewBoundaries(unittest.TestCase):
    def test_pending_requirement_and_unchanged_five_object_scope(self):
        r=json.loads((ROOT/'requirement_v2.json').read_text())
        self.assertFalse(r['approved']);self.assertIsNone(r['human_review']['decision'])
        self.assertEqual(r['human_review']['reviewer'],'')
        self.assertEqual(r['interval'],'From the saved state immediately before the first policy-issued action, after the ten settling commands, through the terminal post-action snapshot.')
        self.assertEqual(set(r['protected_objects']),{'cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1'})
        self.assertTrue(r['falls_need_not_land_on_floor'])

    def test_human_forms_have_no_preentered_labels_or_decisions(self):
        for name in ['initial_support_forms.json','event_forms.json','uncertainty_forms.json']:
            r=json.loads((ROOT/'human_review'/name).read_text());self.assertFalse(r['human_labels_entered'])
            for f in r['forms']:
                self.assertEqual(f['reviewer'],'');self.assertIsNone(f['decision'])
                if 'support_label' in f:self.assertIsNone(f['support_label'])
                if 'event_interpretation' in f:self.assertIsNone(f['event_interpretation'])

    def test_actual_box_quaternions_match_six_digit_XML_rounding(self):
        rows=json.loads((ROOT/'rotation_serialization_evidence.json').read_text());self.assertEqual(len(rows),80)
        for r in rows:
            q=r['runtime_relative_quaternion'];saved=list(map(float,r['xml_quaternion_tokens'].split()))
            # The result also holds with the tighter recomposition arithmetic budget,
            # rather than the initial diagnostic's conservative 1e-12 zero-noise cutoff.
            rounded=[float(format(v,'.6g')) if abs(v)>512*sys.float_info.epsilon else 0. for v in q]
            self.assertEqual(rounded,saved)

if __name__=='__main__':unittest.main()
