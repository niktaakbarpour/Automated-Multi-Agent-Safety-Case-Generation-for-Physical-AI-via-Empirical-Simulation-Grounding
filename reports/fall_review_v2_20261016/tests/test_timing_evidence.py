"""Recorded measurement algebra, not synthetic robot evidence or a fall test."""
import json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RecordedTimingEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.samples=json.loads((ROOT/'fixtures/actual_recorded_timing_samples.json').read_text())['samples']

    def test_Euler_translation_identity_in_actual_excerpts(self):
        for s in self.samples:
            for q,b,v in zip(s['qpos_xyz'],s['recorded_body_xyz'],s['qvel_xyz']):
                # Arithmetic allowance for subtraction/multiplication of binary64 coordinates;
                # not a physical support or fall threshold.
                tol=512*sys.float_info.epsilon*max(1,abs(q),abs(b))
                self.assertLessEqual(abs(q-b-s['dt']*v),tol)

    def test_raw_and_derived_are_not_assumed_synchronous(self):
        samples=[s for s in self.samples if s['object']=='milk_1' and s['frame']=='000011']
        self.assertTrue(samples)
        self.assertTrue(any(s['recorded_body_xyz']!=s['recorded_raw_xyz'] for s in samples))
        self.assertTrue(any(s['qpos_xyz']!=s['recorded_body_xyz'] for s in samples))

    def test_boundary_geometry_is_separate_static_evidence(self):
        r=json.loads((ROOT/'prepolicy_static_endpoint_geometry.json').read_text())
        self.assertTrue(r['no_physics_steps']);self.assertEqual(len(r['records']),50)
        self.assertTrue(all(x['contact_records_at_this_reconstructed_pose']=='not_computed' for x in r['records']))

if __name__=='__main__':unittest.main()
