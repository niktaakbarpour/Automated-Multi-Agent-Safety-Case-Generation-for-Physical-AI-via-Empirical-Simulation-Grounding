import tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from facts import xml_info
try:import mujoco
except ImportError:mujoco=None

@unittest.skipUnless(mujoco,'MuJoCo required for compiler-based geometry verification')
class GeometryTest(unittest.TestCase):
    def parse(self,content):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'model.xml';p.write_text(content);r=xml_info(p)
            self.assertEqual(r['geometry_resolution']['status'],'compiler_resolved',r['geometry_resolution'])
            return r
    def test_nested_geometry_and_hierarchy(self):
        r=self.parse('<mujoco><worldbody><body name="living_room_table"><body name="child"><geom type="box" size="1 2 3"/></body></body></worldbody></mujoco>')
        t=r['native_surface_geometry'][0];self.assertEqual(len(t['geometries']),1)
        self.assertEqual(t['geometries'][0]['owner_body'],'child');self.assertEqual(r['body_hierarchy'][1]['parent'],'living_room_table')
    def test_worldbody_geometry(self):
        r=self.parse('<mujoco><worldbody><geom name="floor" type="plane" size="1 1 .1"/></worldbody></mujoco>')
        self.assertEqual(r['worldbody_geometry'][0]['name'],'floor');self.assertEqual(r['native_surface_geometry'][0]['owner_body'],'world')
    def test_nested_coordinate_transforms_and_rotated_box_bounds(self):
        r=self.parse('<mujoco><compiler angle="degree"/><worldbody><body name="table" pos="10 0 0" euler="0 0 90"><body name="child" pos="1 0 0"><geom name="top" type="box" pos="1 0 0" size="1 2 3"/></body></body></worldbody></mujoco>')
        g=r['all_geometry'][0]
        for a,b in zip(g['position_world_reference'],[10,2,0]):self.assertAlmostEqual(a,b)
        for a,b in zip(g['world_aabb_reference']['min'],[8,1,-3]):self.assertAlmostEqual(a,b)
        self.assertEqual(g['horizontal_upper_face_z_candidate'],3)
    def test_effective_defaults_and_collision_role_not_render_group(self):
        r=self.parse('<mujoco><default><default class="visual"><geom contype="0" conaffinity="0"/></default></default><worldbody><body name="table" childclass="visual"><geom name="vis" type="box" size="1 1 1" group="0"/><geom name="col" type="box" size="1 1 1" contype="1" conaffinity="1" group="1"/></body></worldbody></mujoco>')
        self.assertEqual([g['geometry_role'] for g in r['all_geometry']],['visual_only','collision_enabled'])
    def test_explicit_contact_pair_overrides_zero_mask_role(self):
        r=self.parse('<mujoco><worldbody><geom name="a" type="sphere" size="1" contype="0" conaffinity="0"/><geom name="b" type="sphere" size="1" contype="0" conaffinity="0"/></worldbody><contact><pair geom1="a" geom2="b"/></contact></mujoco>')
        self.assertTrue(all(g['geometry_role']=='collision_enabled' for g in r['all_geometry']))
    def test_unsupported_xml_is_reported_without_invented_transforms(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'model.xml';p.write_text('<mujoco><worldbody><body name="table"><body name="nested"><geom mesh="missing" type="mesh"/></body></body></worldbody></mujoco>')
            r=xml_info(p);self.assertEqual(r['geometry_resolution']['status'],'unresolved')
            self.assertEqual(len(r['native_surface_geometry'][0]['geometries']),1)
            self.assertNotIn('position_world_reference',r['native_surface_geometry'][0]['geometries'][0])
    def test_mesh_scaling_and_compiler_mesh_alignment(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'tetra.obj').write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n')
            (p/'model.xml').write_text('<mujoco><asset><mesh name="m" file="tetra.obj" scale="2 3 4"/></asset><worldbody><body name="table" pos="10 20 30"><geom type="mesh" mesh="m"/></body></worldbody></mujoco>')
            r=xml_info(p/'model.xml');self.assertEqual(r['geometry_resolution']['status'],'compiler_resolved')
            box=r['all_geometry'][0]['world_aabb_reference']
            for a,b in zip(box['min'],[10,20,30]):self.assertAlmostEqual(a,b,places=5)
            for a,b in zip(box['max'],[12,23,34]):self.assertAlmostEqual(a,b,places=5)

class InventoryCoverageTest(unittest.TestCase):
    def test_three_frame_field_inventory_does_not_claim_full_run_or_units(self):
        import h5py
        from facts import inventory
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with h5py.File(p/'trajectory.h5','w') as h:
                h.attrs['global_episode_id']='reference-run-123'
                for i in range(5):
                    g=h.create_group(f'frames/{i:06d}');g.attrs['stage']='control'
                    g.create_dataset('raw_observation/milk_1_pos/value',data=[0.,0.,0.])
                    c=g.create_group('simulator/contacts');c.attrs['json']='[]'
                result=inventory(h,p,{'sensor_declarations':[]})
                self.assertEqual(result['reference_run_id'],'reference-run-123')
                self.assertEqual([f['frame_id'] for f in result['sampled_frames']],[0,2,4])
                c=result['coverage_qualification'];self.assertEqual(c['sample_count'],3)
                for name in ['full_run_availability_verified','units_verified','coordinate_frames_verified','object_reference_points_verified']:self.assertFalse(c[name])
