"""Controlled face/ID/contact integration; requires the existing Hestia runtime."""
import copy
import json
import os
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
try:
    import numpy as np
    import h5py
    AVAILABLE=True
except ImportError:
    AVAILABLE=False
from r1_checker import initial_support
CONFIG=json.loads((ROOT/'config.json').read_text())


@unittest.skipUnless(AVAILABLE,'numpy/h5py integration runs on Hestia')
class FaceEvidenceTests(unittest.TestCase):
    def setUp(self):
        baseline=Path(os.environ.get('R1_BASELINE_RELEASE',str(ROOT.parents[1]/'reports/fall_checker_dev_v2_20261017')))
        sys.path.insert(0,str(baseline/'src'))
        from execute import extract_frame
        self.extract=extract_frame
        class Index:
            def by_id(self,i):
                if isinstance(i,bool) or not isinstance(i,int) or i not in range(6):raise ValueError('Unknown native ID')
                owner=['living_room_table','object','robot0_left','robot0_right','floor','pedestal'][i]
                return dict(native_geom_id=i,type='mjGEOM_BOX',size=[.1,.1,.1],collision_capable=True,owner_body=owner,body_ancestry=[owner,'world'])
            @property
            def geometries(self):return [self.by_id(i) for i in range(6)]
            def contact_pair(self,c):return self.by_id(c['geom1']),self.by_id(c['geom2'])
            def validate_snapshot_transforms(self,*args):pass
        self.index=Index()
        self.gp=np.array([[0,0,.9],[0,0,1.1],[4,0,3],[5,0,3],[0,0,0],[0,0,1.1]],dtype=float)
        self.rot=np.array([np.eye(3)]*6)
        self.entities={'object':{'native_geom_ids':[1]}}
        self.physical=dict(table_geom_ids=[0],floor_geom_ids=[4],gripper_left_ids=[2],gripper_right_ids=[3])
        self.contacts=[dict(geom1=0,geom2=1,pos=[0,0,1.],dist=0.)]
    def make(self,contacts=None,ncon=None):
        contacts=self.contacts if contacts is None else contacts
        with h5py.File('controlled','w',driver='core',backing_store=False) as h:
            s=h.create_group('simulator')
            for name,data in [('geom_xpos',self.gp),('geom_xmat',self.rot),('body_xpos',[[0,0,0]]),('body_xquat',[[1,0,0,0]]),('time',.5),('ncon',len(contacts) if ncon is None else ncon)]:s.create_dataset(name,data=data)
            s.create_group('contacts').attrs['json']=json.dumps(contacts)
            return self.extract(h,10,self.index,self.entities,self.physical,CONFIG)
    def test_true_upper_face(self):
        f=self.make();self.assertEqual(f['objects']['object']['support_parents'],['living_room_table'])
    def test_signed_penetration_consistent_face(self):
        self.gp[1,2]-=1e-7
        c=copy.deepcopy(self.contacts);c[0].update(dist=-1e-7,pos=[0,0,1.-.5e-7])
        self.assertEqual(self.make(c)['objects']['object']['support_parents'],['living_room_table'])
    def test_side_contact_not_upward_support(self):
        c=copy.deepcopy(self.contacts);c[0]['pos'][2]=.9
        self.assertEqual(self.make(c)['objects']['object']['support_parents'],[])
    def test_inconsistent_contact_distance_not_support(self):
        c=copy.deepcopy(self.contacts);c[0]['dist']=-.001
        self.assertEqual(self.make(c)['objects']['object']['support_parents'],[])
    def test_unknown_native_geometry_rejected(self):
        c=copy.deepcopy(self.contacts);c[0]['geom2']=100
        with self.assertRaises(ValueError):self.make(c)
    def test_incomplete_contacts_rejected(self):
        with self.assertRaises(ValueError):self.make(ncon=2)
    def test_nonfinite_contact_rejected(self):
        c=copy.deepcopy(self.contacts);c[0]['pos'][0]=float('nan')
        with self.assertRaises(ValueError):self.make(c)
    def test_indirect_upper_face_chain(self):
        self.gp[1,2]=1.3;self.entities['pedestal']={'native_geom_ids':[5]}
        self.contacts=[dict(geom1=0,geom2=5,pos=[0,0,1.],dist=0.),dict(geom1=5,geom2=1,pos=[0,0,1.2],dist=0.)]
        f=self.make();fs=[dict(copy.deepcopy(f),frame=i,time=.05*i) for i in [9,10,11]]
        result=initial_support(fs,'object',CONFIG)
        self.assertEqual(result['support_class'],'indirect_stable_table')

if __name__=='__main__':unittest.main()
