import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

import task8c_adapter as adapter
from cohort_execution_wrapper import execute_prepared_case


def fixture_geometry():
    bodies = ["world"] * 29
    bodies[1] = "floor"
    bodies[3] = "living_room_table"
    bodies[22] = "cream_cheese_1_main"
    bodies[25] = "robot0_left"
    bodies[26] = "robot0_right"
    geometries = []
    for i in range(adapter.EXPECTED_GEOM_COUNT):
        body = 0
        collision = False
        name = None
        geom_type = "mjGEOM_MESH"
        size = [0.0, 0.0, 0.0]
        if i == 1:
            body, collision, name, geom_type, size = 22, True, "target", "mjGEOM_BOX", [.1,.1,.1]
        elif i == 8:
            body, collision, name, geom_type = 1, True, "floor", "mjGEOM_PLANE"
        elif i == 10:
            body, collision, name, geom_type, size = 3, True, "table", "mjGEOM_BOX", [.1,.1,.1]
        elif i == 76:
            body, collision, name, geom_type, size = 25, True, "left_finger", "mjGEOM_BOX", [.01,.01,.01]
        elif i == 79:
            body, collision, name, geom_type, size = 26, True, "right_finger", "mjGEOM_BOX", [.01,.01,.01]
        geometries.append(dict(native_geom_id=i, name=name, owner_body_id=body,
            owner_body=bodies[body], body_ancestry=[bodies[body]], type=geom_type,
            size=size, collision_capable=collision, local_position_xml=[0.,0.,0.],
            local_rotation_xml=np.eye(3).tolist(),
            box_corner_displacement_bound_due_to_rotation_serialization_m=0.0))
    return dict(source_xml_sha256="", native_geom_count=adapter.EXPECTED_GEOM_COUNT,
        body_names=bodies, geometries=geometries)


def write_h5(path, *, duplicate_frame=False, timestamp_shift=0.0, drop_contact=False,
              identity="cream_cheese_1_main", wrong_geometry_owner=False):
    count = adapter.EXPECTED_NATIVE_SAMPLES
    action = np.asarray([adapter._sample_action_index(i) for i in range(count)], dtype=np.int32)
    times_after = np.arange(count, dtype=np.float64) * .002
    times_before = times_after.copy()
    times_before[1:] -= .002
    ncon = np.ones(count, dtype=np.int32)
    samples = np.arange(count, dtype=np.int32)
    if drop_contact:
        samples = samples[1:]
    with h5py.File(path, "w") as h:
        h.attrs["execution_kind"] = "fresh_deterministic_reset"
        h.attrs["target_object"] = "cream_cheese_1"
        h.attrs["target_body_id"] = 22
        h.attrs["target_body_name"] = identity
        h.attrs["r1_boundary_frame"] = 10
        h.attrs["terminal_frame"] = 257
        h.attrs["native_timestep_s"] = .002
        h.attrs["control_timestep_s"] = .05
        actions = h.create_group("actions")
        actions.create_dataset("settling_actions", data=np.zeros((10,7)))
        actions.create_dataset("stationary_hold_actions", data=np.zeros((247,7)))
        obs = h.create_group("observations")
        frames = np.arange(adapter.EXPECTED_FRAMES, dtype=np.int32)
        if duplicate_frame:
            frames[100] = frames[99]
        obs.create_dataset("source_frame", data=frames)
        obs.create_dataset("time", data=np.arange(adapter.EXPECTED_FRAMES)*.05 + timestamp_shift)
        physics = h.create_group("physics")
        physics.create_dataset("time_before", data=times_before)
        physics.create_dataset("time_after", data=times_after)
        physics.create_dataset("action_index", data=action)
        physics.create_dataset("ncon", data=ncon)
        body_pos = np.zeros((count, adapter.EXPECTED_BODY_COUNT, 3))
        body_pos[:,22,2] = .2
        physics.create_dataset("body_xpos", data=body_pos)
        body_quat = np.zeros((count, adapter.EXPECTED_BODY_COUNT, 4))
        body_quat[:,:,0] = 1.
        physics.create_dataset("body_xquat", data=body_quat)
        contacts = h.create_group("contacts")
        rows = len(samples)
        g1 = np.full(rows, 10, dtype=np.int32)
        g2 = np.full(rows, 1, dtype=np.int32)
        b1 = np.full(rows, 3, dtype=np.int32)
        if wrong_geometry_owner:
            b1[:] = 4
        b2 = np.full(rows, 22, dtype=np.int32)
        for name, data in {
            "sample_index": samples, "geom1":g1, "geom2":g2, "body1":b1, "body2":b2,
            "dist":np.zeros(rows), "pos":np.tile([0.,0.,.1],(rows,1)),
            "frame":np.tile([0.,0.,1.,1.,0.,0.,0.,1.,0.],(rows,1)),
            "force_contact_frame":np.zeros((rows,6)),
            "geom1_name":np.asarray([b"table"]*rows), "geom2_name":np.asarray([b"target"]*rows),
            "body1_name":np.asarray([b"living_room_table"]*rows),
            "body2_name":np.asarray([b"cream_cheese_1_main"]*rows),
        }.items():
            contacts.create_dataset(name, data=data)


class AdapterUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / "recording.h5"
        self.xml = self.root / "simulator.xml"
        self.runner = self.root / "runner.py"
        self.xml.write_text("fixture XML bytes")
        self.runner.write_text("frozen fixture capture source")
        self.old_expected = adapter.EXPECTED_XML_SHA256
        adapter.EXPECTED_XML_SHA256 = adapter.sha256_file(self.xml)
        self.index = fixture_geometry()
        self.index["source_xml_sha256"] = adapter.EXPECTED_XML_SHA256
        self.entities = {"schema_version":"corrected-entity-inventory-v2","records":[
            {"source_xml_sha256":adapter.EXPECTED_XML_SHA256,"entities":[
                {"name":"cream_cheese_1","root_body_name":"cream_cheese_1_main","body_id":22,"native_geom_ids":[1]}]}]}
        self.physical = dict(table_geom_ids=[10], floor_geom_ids=[8],
            gripper_left_ids=[76], gripper_right_ids=[79])
        self.checker = dict(objects=["cream_cheese_1"], arithmetic_eps_multiplier=512,
            start_frame=10, sample_period_s=.05, time_arithmetic_allowance_s=1e-8)
        self.binding = dict(case_id="case_fixture", source_execution_id="exec_fixture",
            source_group_id="group_fixture", recording_sha256="",
            runner_sha256=adapter.sha256_file(self.runner), runner_source_path=str(self.runner),
            source_provenance_status="VERIFIED", xml_sha256=adapter.EXPECTED_XML_SHA256)
        write_h5(self.path)
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)

    def tearDown(self):
        adapter.EXPECTED_XML_SHA256 = self.old_expected
        self.tmp.cleanup()

    def prepare(self):
        return adapter.prepare_case(self.path, self.xml, self.binding, self.index,
            self.physical, self.checker, self.entities)

    def test_exact_frame_projection_and_boundaries(self):
        result = self.prepare()
        self.assertEqual(result["frame_count"], 258)
        self.assertEqual(result["frames"][10]["sample_index"], 250)
        self.assertEqual(result["frames"][11]["sample_index"], 275)
        self.assertEqual(result["frames"][257]["sample_index"], 6425)
        self.assertFalse(result["intermediate_native_samples_used_as_checker_frames"])
        self.assertEqual(result["frames"][10]["objects"]["cream_cheese_1"]["support_parents"], ["living_room_table"])

    def test_recording_hash_mismatch_rejected(self):
        self.binding["recording_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "Recording SHA"):
            self.prepare()

    def test_runner_provenance_mismatch_is_fail_closed(self):
        self.binding["source_provenance_status"] = "UNVERIFIED"
        with self.assertRaisesRegex(ValueError, "Runner provenance"):
            self.prepare()

    def test_runner_source_hash_mismatch_rejected(self):
        self.runner.write_text("different runner bytes")
        with self.assertRaisesRegex(ValueError, "Runner source SHA"):
            self.prepare()

    def test_unverified_diagnostic_facts_never_eligible(self):
        self.binding["source_provenance_status"] = "UNVERIFIED"
        result = adapter.prepare_case(self.path, self.xml, self.binding, self.index,
            self.physical, self.checker, self.entities, diagnostic_unverified=True)
        self.assertFalse(result["checker_eligible"])

    def test_protected_body_identity_rejected(self):
        write_h5(self.path, identity="wrong_body")
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "Protected object"):
            self.prepare()

    def test_contact_owner_identity_rejected(self):
        write_h5(self.path, wrong_geometry_owner=True)
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "body IDs disagree"):
            self.prepare()

    def test_missing_contact_rows_rejected(self):
        write_h5(self.path, drop_contact=True)
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "Incomplete contact rows"):
            self.prepare()

    def test_duplicate_frame_rejected(self):
        write_h5(self.path, duplicate_frame=True)
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.prepare()

    def test_invalid_timestamp_rejected(self):
        write_h5(self.path, timestamp_shift=.001)
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "timestamps do not align"):
            self.prepare()

    def test_geometry_local_world_and_vertex_transform(self):
        idx = fixture_geometry()
        q = [math_sqrt_half(), 0., 0., math_sqrt_half()]
        body_pos = np.zeros((29,3)); body_pos[22] = [1.,2.,3.]
        body_quat = np.zeros((29,4)); body_quat[:,0] = 1.; body_quat[22] = q
        idx["geometries"][1]["local_position_xml"] = [1.,0.,0.]
        gp, gr = adapter._geometry_world(idx, body_pos, body_quat)
        np.testing.assert_allclose(gp[1], [1.,3.,3.], atol=1e-14)
        np.testing.assert_allclose(gr[1], [[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]], atol=1e-14)
        corners = adapter._corners(idx, 1, gp, gr)
        self.assertEqual(corners.shape, (8,3))
        self.assertAlmostEqual(float(corners[:,0].min()), .9)
        self.assertAlmostEqual(float(corners[:,0].max()), 1.1)

    def test_nonfinite_contact_force_rejected(self):
        with h5py.File(self.path, "r+") as h:
            h["contacts/force_contact_frame"][0,0] = np.nan
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "Nonfinite contact"):
            self.prepare()

    def test_native_sample_alignment_rejected(self):
        with h5py.File(self.path, "r+") as h:
            h["physics/action_index"][275] = 1
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "Action-to-native-sample"):
            self.prepare()

    def test_xml_hash_mismatch_rejected(self):
        self.index["source_xml_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Geometry index XML"):
            self.prepare()

    def test_native_geometry_identity_mismatch_rejected(self):
        self.index["geometries"][1]["owner_body_id"] = 21
        with self.assertRaisesRegex(ValueError, "Geometry owner identity"):
            self.prepare()

    def test_contact_geometry_name_mismatch_rejected(self):
        with h5py.File(self.path, "r+") as h:
            h["contacts/geom2_name"][:] = np.asarray([b"wrong"] * adapter.EXPECTED_NATIVE_SAMPLES)
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "geometry names disagree"):
            self.prepare()

    def test_unknown_contact_geometry_rejected(self):
        with h5py.File(self.path, "r+") as h:
            h["contacts/geom1"][0] = 50
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "non-collision geometry"):
            self.prepare()

    def test_missing_measurement_channel_rejected(self):
        with h5py.File(self.path, "r+") as h:
            del h["physics/body_xquat"]
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(KeyError, "body_xquat"):
            self.prepare()

    def test_invalid_quaternion_rejected(self):
        with h5py.File(self.path, "r+") as h:
            h["physics/body_xquat"][0,22] = [0.,0.,0.,0.]
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "Invalid wxyz"):
            self.prepare()

    def test_collision_vertices_and_bounds_match_box_rule(self):
        result = self.prepare()
        obj = result["frames"][10]["objects"]["cream_cheese_1"]
        self.assertEqual(len(obj["vertices"]), 8)
        np.testing.assert_allclose(obj["bounds"], [[-.1,-.1,.1],[.1,.1,.3]], atol=1e-15)
        self.assertEqual(len(obj["pose"]), 12)

    def test_robot_contact_is_mapped_but_not_load_bearing_support(self):
        with h5py.File(self.path, "r+") as h:
            h["contacts/geom1"][:] = 76
            h["contacts/body1"][:] = 25
            del h["contacts/geom1_name"]
            h["contacts"].create_dataset("geom1_name", data=np.asarray(
                [b"left_finger"] * adapter.EXPECTED_NATIVE_SAMPLES))
            del h["contacts/body1_name"]
            h["contacts"].create_dataset("body1_name", data=np.asarray(
                [b"robot0_left"] * adapter.EXPECTED_NATIVE_SAMPLES))
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        fact = self.prepare()["frames"][10]["objects"]["cream_cheese_1"]
        self.assertEqual(fact["contact_entities"], ["robot"])
        self.assertEqual(fact["support_parents"], [])
        self.assertFalse(fact["bilateral_gripper"])

    def test_object_to_object_alternative_support_fails_closed(self):
        self.index["body_names"][21] = "alphabet_soup_1_main"
        g = self.index["geometries"][82]
        g.update(owner_body_id=21, owner_body="alphabet_soup_1_main",
                 body_ancestry=["alphabet_soup_1_main"], type="mjGEOM_BOX",
                 collision_capable=True, size=[.01,.01,.01], name="soup")
        self.entities["records"][0]["entities"].append({"name":"alphabet_soup_1",
            "root_body_name":"alphabet_soup_1_main","body_id":21,"native_geom_ids":[82]})
        with h5py.File(self.path, "r+") as h:
            h["contacts/geom1"][:] = 82
            h["contacts/body1"][:] = 21
            h["contacts/geom1_name"][:] = np.asarray([b"soup"] * adapter.EXPECTED_NATIVE_SAMPLES)
            del h["contacts/body1_name"]
            h["contacts"].create_dataset("body1_name", data=np.asarray(
                [b"alphabet_soup_1_main"] * adapter.EXPECTED_NATIVE_SAMPLES))
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        with self.assertRaisesRegex(ValueError, "object-to-object contact"):
            self.prepare()

    def test_raw_force_normal_channels_do_not_become_checker_inputs(self):
        baseline = self.prepare()["frames"][10]
        with h5py.File(self.path, "r+") as h:
            h["contacts/frame"][:] = np.tile([0.,1.,0.,1.,0.,0.,0.,0.,1.],
                                             (adapter.EXPECTED_NATIVE_SAMPLES,1))
            h["contacts/force_contact_frame"][:] = np.tile([999.,-999.,3.,4.,5.,6.],
                                             (adapter.EXPECTED_NATIVE_SAMPLES,1))
        self.binding["recording_sha256"] = adapter.sha256_file(self.path)
        changed = self.prepare()["frames"][10]
        self.assertEqual(baseline, changed)

    def test_contact_force_or_normal_tampering_without_new_hash_rejected(self):
        with h5py.File(self.path, "r+") as h:
            h["contacts/force_contact_frame"][0,0] = 123.
        with self.assertRaisesRegex(ValueError, "Recording SHA"):
            self.prepare()

    def test_authoritative_case_and_group_binding(self):
        source = {"blinded_case_id":"case_fixture", "new_execution_id":"exec_fixture",
            "coordinator_group_id":"group_fixture", "raw_hdf5_sha256":self.binding["recording_sha256"],
            "xml_sha256":self.binding["xml_sha256"], "raw_hdf5_path":str(self.path)}
        binding = dict(self.binding, recording_path=str(self.path))
        adapter.validate_manifest_case(source, binding,
            "f30f4b9e907fa0cdda75c3ca31de08e50de9a916f2f27bf69ece776c37966617")
        source["coordinator_group_id"] = "other_group"
        with self.assertRaisesRegex(ValueError, "coordinator_group_id"):
            adapter.validate_manifest_case(source, binding,
                "f30f4b9e907fa0cdda75c3ca31de08e50de9a916f2f27bf69ece776c37966617")

    def test_wrong_manifest_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            adapter.validate_manifest_case({}, {}, "0"*64)

    def test_execution_wrapper_never_calls_checker_for_unverified_case(self):
        called = []
        def evaluator(*args):
            called.append(True)
            raise AssertionError("checker must not be invoked")
        prepared = {"adapter_version":adapter.ADAPTER_VERSION,"checker_eligible":False,
            "source_provenance_status":"UNVERIFIED","frame_count":258,"frames":[{}]*258,
            "monitoring_start_frame":10,"terminal_frame":257,"case_id":"case_fixture"}
        with self.assertRaisesRegex(ValueError, "provenance"):
            execute_prepared_case(prepared,evaluator,{})
        self.assertEqual(called,[])


def math_sqrt_half():
    return 2 ** -0.5


if __name__ == "__main__":
    unittest.main()
