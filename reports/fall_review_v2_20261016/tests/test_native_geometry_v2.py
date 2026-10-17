"""Actual recorded indexing regression, independent of event interpretation."""
import copy,json,unittest
from pathlib import Path
from native_geometry_v2 import NativeGeometryIndex

ROOT=Path(__file__).resolve().parents[1]

class ActualMappingRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=json.loads((ROOT/'corrected_native_geometry_v2.json').read_text())
        cls.legacy=json.loads((ROOT/'fixtures/legacy_simulator_index.json').read_text())
        cls.index=NativeGeometryIndex(cls.record)

    def test_actual_155_vs_161_failure(self):
        self.assertEqual(len(self.legacy['geom_names']),155)
        self.assertEqual(len(self.index.geometries),161)
        self.assertEqual(self.legacy['geom_names'][10],'robot0_g0_vis')
        self.assertIsNone(self.index.by_id(10)['name'])
        self.assertEqual(self.index.by_id(10)['owner_body'],'living_room_table_col')
        self.assertEqual(self.index.named_id('robot0_g0_vis'),16)
        self.assertEqual(self.index.named_id('milk_1_g1'),149)
        self.assertEqual(self.legacy['geom_names'][149],'basket_1_g0')

    def test_actual_contact_pair_and_anonymous_table_ids(self):
        a,b=self.index.contact_pair({'geom1':10,'geom2':149})
        self.assertEqual(a['owner_body'],'living_room_table_col')
        self.assertEqual(b['owner_body'],'milk_1_main')
        self.assertEqual([g['native_geom_id'] for g in self.index.geometries_for_body('living_room_table')],[9,10,11,12,13,14,15])
        self.assertEqual(self.index.named_id('floor'),8)

    def test_legacy_and_incomplete_mapping_fail_closed(self):
        with self.assertRaises(ValueError):NativeGeometryIndex(self.legacy)
        r=copy.deepcopy(self.record);r['geometries'].pop(10)
        with self.assertRaises(ValueError):NativeGeometryIndex(r)

    def test_bad_contact_ids_and_recording_identity_rejected(self):
        for n in [-1,161,True,'10']:
            with self.assertRaises(ValueError):self.index.by_id(n)
        with self.assertRaises(ValueError):self.index.named_id(None)
        with self.assertRaises(ValueError):self.index.validate_recording('unknown',self.record['source_xml_sha256'],161)
        with self.assertRaises(ValueError):self.index.validate_recording(self.record['validated_run_ids'][0],'wrong-hash',161)

    def test_corrected_inventory_uses_native_ids(self):
        inv=json.loads((ROOT/'corrected_entity_inventory_v2.json').read_text())
        self.assertEqual(len(inv['records']),50)
        for r in inv['records']:
            milk=next(e for e in r['entities'] if e['name']=='milk_1')
            self.assertEqual(milk['named_geom_ids']['milk_1_g1'],149)
            self.assertNotIn('geom_ids',milk)

    def test_actual_snapshot_and_corrupted_native_geometry_order(self):
        f=json.loads((ROOT/'fixtures/reference_snapshot_000010.json').read_text())
        arrays=[f[k] for k in ['body_xpos','body_xquat','geom_xpos','geom_xmat']]
        result=self.index.validate_snapshot_transforms(*arrays)
        self.assertFalse(result['physical_or_fall_tolerance'])
        corrupt=copy.deepcopy(arrays);corrupt[2][10],corrupt[2][149]=corrupt[2][149],corrupt[2][10]
        with self.assertRaises(ValueError):self.index.validate_snapshot_transforms(*corrupt)

if __name__=='__main__':unittest.main()
