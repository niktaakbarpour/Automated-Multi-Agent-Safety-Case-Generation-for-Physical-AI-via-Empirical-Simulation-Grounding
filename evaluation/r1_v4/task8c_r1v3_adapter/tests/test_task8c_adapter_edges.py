"""Additional synthetic boundaries for the recovered frozen Task 8C adapter."""
import h5py
import unittest

import test_task8c_adapter as fixture
import task8c_adapter as adapter


class AdapterBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.case = fixture.AdapterUnitTests()
        self.case.setUp()
        self.addCleanup(self.case.tearDown)

    def _remove_contact_sample(self, sample):
        with h5py.File(self.case.path, "r+") as h:
            contacts = h["contacts"]
            arrays = {name: contacts[name][()] for name in adapter.CONTACT_FIELDS}
            keep = arrays["sample_index"] != sample
            for name, data in arrays.items():
                del contacts[name]
                contacts.create_dataset(name, data=data[keep])
            ncon = h["physics/ncon"][()]
            ncon[sample] = 0
            del h["physics/ncon"]
            h["physics"].create_dataset("ncon", data=ncon)
        self.case.binding["recording_sha256"] = adapter.sha256_file(self.case.path)

    def test_missing_initial_support_stays_unresolved_in_measurement_facts(self):
        self._remove_contact_sample(10 * adapter.NATIVE_PER_FRAME)
        prepared = self.case.prepare()
        initial = prepared["frames"][10]["objects"]["cream_cheese_1"]
        self.assertEqual(initial["support_parents"], [])
        self.assertFalse(initial["table_contact"])
        self.assertNotIn("initial_support_verified", initial)

    def test_floor_contact_is_not_attributed_to_table_support(self):
        sample = 10 * adapter.NATIVE_PER_FRAME
        with h5py.File(self.case.path, "r+") as h:
            contacts = h["contacts"]
            at_sample = contacts["sample_index"][()] == sample
            for name, value in (("geom1", 8), ("body1", 1)):
                dataset = contacts[name][()]
                dataset[at_sample] = value
                del contacts[name]
                contacts.create_dataset(name, data=dataset)
            for name, value in (("geom1_name", b"floor"), ("body1_name", b"floor")):
                dataset = contacts[name][()]
                dataset[at_sample] = value
                del contacts[name]
                contacts.create_dataset(name, data=dataset)
        self.case.binding["recording_sha256"] = adapter.sha256_file(self.case.path)
        frame = self.case.prepare()["frames"][10]["objects"]["cream_cheese_1"]
        self.assertEqual(frame["contact_entities"], ["floor"])
        self.assertEqual(frame["support_parents"], [])

    def test_missing_saved_frame_is_rejected(self):
        with h5py.File(self.case.path, "r+") as h:
            h["observations/source_frame"][257] = 256
        self.case.binding["recording_sha256"] = adapter.sha256_file(self.case.path)
        with self.assertRaisesRegex(ValueError, "Missing, duplicated, or out-of-order"):
            self.case.prepare()

    def test_downward_motion_is_measurement_not_an_adapter_verdict(self):
        with h5py.File(self.case.path, "r+") as h:
            body = h["physics/body_xpos"][()]
            body[275:, 22, 2] -= 0.4
            del h["physics/body_xpos"]
            h["physics"].create_dataset("body_xpos", data=body)
        self.case.binding["recording_sha256"] = adapter.sha256_file(self.case.path)
        prepared = self.case.prepare()
        self.assertLess(
            prepared["frames"][11]["objects"]["cream_cheese_1"]["bounds"][0][2],
            prepared["frames"][10]["objects"]["cream_cheese_1"]["bounds"][0][2],
        )
        self.assertNotIn("events", prepared)
        self.assertNotIn("outcome", prepared)
        self.assertNotIn("safety_claim_verified", prepared)
