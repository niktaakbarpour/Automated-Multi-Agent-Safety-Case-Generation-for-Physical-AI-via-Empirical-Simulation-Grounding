import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from r1_checker import TABLE,UNKNOWN,initial_support,evaluate,physical_events,static_path,ranges
CONFIG=json.loads((ROOT/'config.json').read_text())


def obj(z=1., contact=TABLE):
    vertices=[[x,y,z+dz] for x in [-.1,.1] for y in [-.1,.1] for dz in [0.,.2]]
    return dict(valid=True,vertices=vertices,pose=[v for p in vertices for v in p],bounds=[[-.1,-.1,z],[.1,.1,z+.2]],
                contact_native_ids=[10] if contact==TABLE else [76,79] if contact=='robot' else [],
                contact_entities=[contact] if contact else [],support_parents=[TABLE] if contact==TABLE else [],
                support_contacts=[{'parent_entity':TABLE}] if contact==TABLE else [],
                table_contact=contact==TABLE,table_separated=contact!=TABLE,bilateral_gripper=contact=='robot',
                finger_z={'left':z,'right':z})


def frame(i,z=1.,contact=TABLE):
    return dict(frame=i,time=.05*i,valid=True,contacts_complete=True,mapping_valid=True,
                table_pose=[0.,1.],objects={'object':obj(z,contact)})


def series(n=17):
    return [frame(i) for i in range(n)]


class SupportTests(unittest.TestCase):
    def test_direct_stable_support(self):
        p=initial_support(series(),'object',CONFIG)
        self.assertEqual(p['applicability'],'applies')
        self.assertEqual(p['support_class'],'direct_stable_table')
        self.assertEqual(p['evidence']['support_chain'],['object',TABLE])
    def test_indirect_stable_support(self):
        fs=series()
        for f in fs:
            f['objects']['pedestal']=obj()
            f['objects']['pedestal']['contact_entities'].append('object')
            f['objects']['pedestal']['supported_children']=['object']
            f['objects']['object']=obj(1.2,'pedestal')
            f['objects']['object']['support_parents']=['pedestal']
        p=initial_support(fs,'object',CONFIG)
        self.assertEqual(p['support_class'],'indirect_stable_table')
        self.assertEqual(p['evidence']['support_chain'],['object','pedestal',TABLE])
    def test_indirect_incidental_contact_not_support(self):
        fs=series()
        for f in fs:
            f['objects']['pedestal']=obj()
            f['objects']['object']=obj(1.2,'pedestal')
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)
    def test_unstable_support_chain_abstains(self):
        fs=series()
        for f in fs:
            f['objects']['pedestal']=obj(1.+f['frame']*.01)
            f['objects']['object']=obj(1.2,'pedestal')
            f['objects']['object']['support_parents']=['pedestal']
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)
    def test_support_cycle_rejected(self):
        fs=series()
        for f in fs:
            f['objects']['object']['support_parents']=['object']
            f['objects']['object']['contact_entities']=['object']
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)
    def test_established_absence(self):
        fs=[frame(i,2.-i*.01,None) for i in range(17)]
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],'does_not_apply')
        self.assertEqual(evaluate(fs,'object','run',CONFIG)['outcome'],'not_applicable')
    def test_absent_contact_near_table_not_absence_proof(self):
        fs=series()
        for f in fs:
            f['objects']['object']['contact_entities']=[]
            f['objects']['object']['support_parents']=[]
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)
    def test_missing_ambiguous_or_unknown_geometry(self):
        for field in ['valid','mapping_valid','contacts_complete']:
            fs=series();fs[10][field]=False
            with self.subTest(field=field):self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)
    def test_incidental_robot_contact_does_not_make_stable_support(self):
        fs=series()
        for f in fs:f['objects']['object']['contact_entities'].append('robot')
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)
    def test_invalid_timing_abstains(self):
        for time in [float('nan'),2.]:
            fs=series();fs[10]['time']=time
            self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)

    def test_coordinate_changes_are_not_stationary(self):
        fs=series();fs[11]['objects']['object']['pose'][0]+=.001
        self.assertEqual(initial_support(fs,'object',CONFIG)['applicability'],UNKNOWN)


class EventTests(unittest.TestCase):
    def test_positive_negative_evidence_not_missing_candidates(self):
        p=evaluate(series(),'object','r',CONFIG)
        self.assertEqual(p['outcome'],'no_violation_observed_within_reviewed_coverage')
        self.assertEqual(p['applicable_observation_intervals'],[[10,16]])
    def test_true_in_scope_fall_no_floor_required(self):
        fs=series()
        for i,z in [(12,1.5),(13,1.4),(14,1.3),(15,1.2),(16,1.1)]:fs[i]=frame(i,z,None)
        p=evaluate(fs,'object','r',CONFIG)
        self.assertEqual(p['outcome'],'violation')
        self.assertTrue(any(e['type']=='r1_fall' and e['evidence']['support_departure_bracket']==[11,12] for e in p['events']))
    def test_setup_departure_landing_after_boundary(self):
        fs=[frame(0)]+[frame(i,2.-i*.03,None) for i in range(1,13)]+[frame(i,.1,'floor') for i in range(13,17)]
        p=evaluate(fs,'object','r',CONFIG)
        self.assertEqual(p['outcome'],'not_applicable')
        e=next(e for e in p['events'] if e['type']=='setup_departure')
        self.assertEqual(e['onset_bracket'],[0,1])
        self.assertEqual(e['evidence']['first_recorded_contact_frame'],13)
    def test_post_lift_drop_and_recovery_retained(self):
        fs=series();fs[12]=frame(12,1.1,'robot');fs[13]=frame(13,1.2,'robot')
        fs[14]=frame(14,1.25,None);fs[15]=frame(15,1.15,None)
        p=evaluate(fs,'object','r',CONFIG)
        self.assertTrue(any(e['type']=='post_lift_drop' and e['scope']=='post_lift' for e in p['events']))
        self.assertFalse(any(e['type']=='r1_fall' for e in p['events']))
        self.assertEqual(p['outcome'],UNKNOWN) # Re-placement domain unresolved.
        drop=next(e for e in p['events'] if e['type']=='post_lift_drop')
        self.assertEqual(drop['evidence']['first_recorded_contact_frame'],16)
    def test_robot_incidental_contact_not_carrying(self):
        fs=series();fs[12]=frame(12,1.1,'robot');fs[12]['objects']['object']['bilateral_gripper']=False
        fs[13]=frame(13,1.2,None);fs[14]=frame(14,1.1,None)
        events=physical_events(fs,'object',CONFIG)
        self.assertFalse(any(e['type']=='post_lift_drop' for e in events))
        self.assertFalse(any(e['type']=='lift' for e in events))
    def test_supported_tipping_not_fall(self):
        fs=series();fs[12]['objects']['object']['pose'][0]+=.1
        p=evaluate(fs,'object','r',CONFIG)
        self.assertFalse(any(e['type']=='r1_fall' for e in p['events']))
        self.assertTrue(any(e['type']=='contacted_motion' for e in p['events']))
        self.assertEqual(p['outcome'],UNKNOWN)
    def test_one_contact_gap_preserves_physical_uncertainty(self):
        fs=series();fs[12]=frame(12,1.1,None)
        p=evaluate(fs,'object','r',CONFIG)
        self.assertEqual(p['outcome'],UNKNOWN)
        self.assertTrue(any(e['type']=='support_transition_uncertain' for e in p['events']))
        self.assertFalse(any(e['type']=='r1_fall' for e in p['events']))
    def test_fall_not_erased_by_later_robot_catch(self):
        fs=series();fs[12]=frame(12,1.5,None);fs[13]=frame(13,1.4,None);fs[14]=frame(14,1.3,'robot')
        self.assertEqual(evaluate(fs,'object','r',CONFIG)['outcome'],'violation')
    def test_incomplete_intervals_do_not_become_negative(self):
        fs=series();fs[13]['valid']=False
        p=evaluate(fs,'object','r',CONFIG)
        self.assertEqual(p['outcome'],UNKNOWN)
        self.assertEqual(p['applicable_observation_intervals'],[[10,12],[15,16]])
    def test_disjoint_coverage_not_bridged(self):
        fs=series();fs.pop(13)
        p=evaluate(fs,'object','r',CONFIG)
        self.assertEqual(p['outcome'],UNKNOWN)
        self.assertEqual(p['applicable_observation_intervals'],[[10,12],[15,16]])
    def test_rotation_alone_not_unsupported_fall(self):
        fs=series();fs[12]=frame(12,1.2,None);fs[13]=frame(13,1.1,None)
        fs[13]['objects']['object']['vertices'][0][2]=1.3
        self.assertFalse(any(e['type']=='r1_fall' for e in physical_events(fs,'object',CONFIG)))
    def test_duplicate_frames_rejected(self):
        fs=series();fs.append(copy.deepcopy(fs[-1]))
        with self.assertRaises(ValueError):evaluate(fs,'object','r',CONFIG)

if __name__=='__main__':unittest.main()
