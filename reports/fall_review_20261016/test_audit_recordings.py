"""Synthetic audit-helper tests only; not fall-checker validation."""
import json, tempfile, unittest
from pathlib import Path
import h5py
import mujoco
import numpy as np
from audit_recordings import array_status, descendants, rotation, value

class AuditHelpersTest(unittest.TestCase):
    def test_scalar_and_json_encodings(self):
        with tempfile.TemporaryDirectory() as d, h5py.File(Path(d)/'test.h5','w') as h:
            h.create_group('scalar').create_dataset('value',data=3)
            h.create_group('text').attrs['json']=json.dumps('time-string')
            self.assertEqual(value(h,'scalar'),3)
            self.assertEqual(value(h,'text'),'time-string')

    def test_absent_nonfinite_and_shape_are_distinct(self):
        with tempfile.TemporaryDirectory() as d, h5py.File(Path(d)/'test.h5','w') as h:
            for k,a in [('nan',[1,np.nan,3]),('shape',[1,2]),('ok',[1,2,3])]:h.create_group(k).create_dataset('value',data=a)
            self.assertEqual(array_status(h,'absent',(3,))[0],'absent')
            self.assertEqual(array_status(h,'nan',(3,))[0],'nonfinite')
            self.assertEqual(array_status(h,'shape',(3,))[0],'wrong_shape')
            self.assertEqual(array_status(h,'ok',(3,))[0],'finite')

    def test_wxyz_rotation_and_quaternion_sign(self):
        q=np.array([2**-.5,0,0,2**-.5])
        np.testing.assert_allclose(rotation(q)@np.array([1,0,0]),[0,1,0],atol=1e-14)
        np.testing.assert_array_equal(rotation(q),rotation(-q))

    def test_body_hierarchy_and_anonymous_native_geom_ids(self):
        m=mujoco.MjModel.from_xml_string('<mujoco><worldbody><geom type="plane" size="1 1 .1"/><body name="table"><geom type="box" size="1 1 .1"/><body name="child"><geom type="sphere" size=".1"/></body></body></worldbody></mujoco>')
        self.assertEqual(descendants(m,1),[1,2])
        self.assertEqual(m.ngeom,3)
        names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) for i in range(m.ngeom)]
        self.assertEqual(names,[None,None,None])
        projected=[names[i] for i in sorted({n:i for i,n in enumerate(names)}.values())]
        self.assertEqual(len(projected),1)
        self.assertEqual(m.geom_bodyid.tolist(),[0,1,2])

if __name__=='__main__': unittest.main()
