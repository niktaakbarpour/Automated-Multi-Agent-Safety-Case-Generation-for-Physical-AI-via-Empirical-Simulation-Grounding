import unittest

from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.requested_obligations_v2 import (
    VERSION,
    interpret_v2,
)


CATALOGUE = {"frames": 300, "objects": {"cream_cheese_1": {"category": "cream_cheese"}, "ketchup_1": {"category": "ketchup"}}}
CONTEXT = {"object_id": None}


def interpret(query):
    return interpret_v2(query, CATALOGUE, CONTEXT)


class RequestedObligationPlannerV2Tests(unittest.TestCase):
    def test_three_exposed_temporal_label_cases_retain_joint_position(self):
        expected = {
            "KH2-C2-02": "2.1",
            "KH2-C2-10": "7.0",
            "KH2-C2-18": "2.1",
        }
        for case_id, label in expected.items():
            with self.subTest(case=case_id):
                plan = interpret(f"Show joint configuration at simulator label {label} seconds.")
                self.assertEqual(plan["status"], "RESOLVED")
                self.assertEqual(plan["families"], ["recorded_time", "raw.robot0_joint_pos"])
                self.assertEqual(plan["seconds_interval"], [float(label), float(label)])
                self.assertEqual(plan["planner_version"], VERSION)

    def test_joint_position_with_frame_qualifier(self):
        plan = interpret("Report arm joint configuration at saved frame 42.")
        self.assertEqual(plan["status"], "RESOLVED")
        self.assertIn("raw.robot0_joint_pos", plan["families"])
        self.assertNotIn("recorded_time", plan["families"])
        self.assertEqual(plan["frame_interval"], [42, 42])

    def test_existing_supported_gripper_and_arm_pattern(self):
        plan = interpret("Finger positions and arm speeds at frame 20.")
        self.assertEqual(set(plan["families"]), {"raw.robot0_gripper_qpos", "raw.robot0_joint_vel"})
        self.assertEqual(plan["status"], "RESOLVED")

    def test_shared_subject_without_explicit_mapping_is_ambiguous(self):
        plan = interpret("Show gripper and joint positions at frame 20.")
        self.assertEqual(plan["status"], "AMBIGUOUS")
        self.assertTrue(plan["unresolved_obligations"])

    def test_multiple_measurement_families_and_scope(self):
        plan = interpret("Show gripper positions and joint velocities at frame 20.")
        self.assertEqual(
            set(plan["families"]),
            {"raw.robot0_gripper_qpos", "raw.robot0_joint_vel"},
        )
        self.assertEqual(plan["frame_interval"], [20, 20])

    def test_ambiguous_joint_state_is_not_resolved(self):
        plan = interpret("Show joint state at frame 20.")
        self.assertEqual(plan["status"], "AMBIGUOUS")
        self.assertEqual(plan["obligation_plan_status"], "INCOMPLETE")
        self.assertTrue(plan["unresolved_obligations"])

    def test_unsupported_physical_request_is_not_complete(self):
        plan = interpret("Show contact force at frame 20.")
        self.assertNotEqual(plan["status"], "RESOLVED")
        self.assertTrue(plan["unsupported"])

    def test_unknown_measurement_request_is_explicit(self):
        plan = interpret("Report wrist orientation at frame 20.")
        self.assertNotEqual(plan["status"], "RESOLVED")
        self.assertEqual(plan["obligation_plan_status"], "INCOMPLETE")
        self.assertTrue(plan["unresolved_obligations"])

    def test_mixed_supported_and_unsupported_span_stays_incomplete(self):
        plan = interpret("Report joint positions and wrist orientation at frame 20.")
        self.assertIn("raw.robot0_joint_pos", plan["families"])
        self.assertTrue(plan["unresolved_obligations"])
        self.assertNotEqual(plan["status"], "RESOLVED")

    def test_paraphrase_development_cases(self):
        variants = [
            "Return the robot's joint configuration at simulator time 2.1 seconds.",
            "At simulator label 2.1 seconds, provide arm joint positions.",
            "Fetch joint angles for saved frame 42.",
        ]
        for query in variants:
            with self.subTest(query=query):
                plan = interpret(query)
                self.assertIn("raw.robot0_joint_pos", plan["families"])
                self.assertEqual(plan["status"], "RESOLVED")

    def test_temporal_qualifier_without_requested_measurement_is_not_invented(self):
        plan = interpret("What is recorded at simulator label 2.1 seconds?")
        self.assertNotEqual(plan["status"], "RESOLVED")

    def test_missing_temporal_scope_remains_ambiguous(self):
        plan = interpret("Report joint positions.")
        self.assertEqual(plan["status"], "AMBIGUOUS")

    def test_all_supported_measurement_families_are_retained(self):
        plan = interpret("Collect finger positions and speeds and arm joint positions and rates at frame 8.")
        self.assertEqual(
            set(plan["families"]),
            {"raw.robot0_gripper_qpos", "raw.robot0_gripper_qvel", "raw.robot0_joint_pos", "raw.robot0_joint_vel"},
        )

    def test_all_channels_legacy_pattern_remains_resolved(self):
        plan = interpret("Collect all six recorded measurement channels at frame 45.")
        self.assertEqual(plan["status"], "RESOLVED")
        self.assertEqual(len(set(plan["families"]) & {"raw.robot0_gripper_qpos", "raw.robot0_gripper_qvel", "raw.robot0_joint_pos", "raw.robot0_joint_vel", "raw.simulator_actuator_force", "simulator.ncon"}), 6)
        self.assertEqual(len(plan["families"]), len(set(plan["families"])))

    def test_object_scope_contradiction_is_preserved(self):
        plan = interpret_v2(
            "Report joint positions for ketchup_1 at frame 10.",
            CATALOGUE,
            {"object_id": "cream_cheese_1"},
        )
        self.assertEqual(plan["status"], "INVALID SCOPE")

    def test_frame_scope_conflict_is_preserved(self):
        plan = interpret_v2(
            "Report joint positions at frame 20.",
            CATALOGUE,
            {"object_id": None, "frame_interval": (21, 21)},
        )
        self.assertEqual(plan["status"], "INVALID SCOPE")


if __name__ == "__main__":
    unittest.main()
