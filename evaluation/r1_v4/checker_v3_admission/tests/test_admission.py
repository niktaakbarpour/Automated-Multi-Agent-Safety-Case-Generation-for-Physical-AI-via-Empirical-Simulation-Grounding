"""CPU tests with synthetic source files and the published development seal."""

from copy import deepcopy
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
import unittest

import h5py

from evaluation.r1_v4.checker_v3_admission.admission import (
    CHECKER, NEGATIVE, PHYSICAL_GATES, assess, frozen_checker_configuration,
    require_admitted_assessment, validate_assessment,
)
from evaluation.r1_v4.evidence_registry_gsn.registry_v3 import R1_V3, RegistryV3, make_record
from evaluation.r1_v4.provenance import bytes_digest, canonical, digest, load


def binding(path):
    return {"path": str(path), "sha256": bytes_digest(path.read_bytes())}


def save(path, value):
    path.write_bytes(canonical(value) + b"\n")
    return binding(path)


class AdmissionTests(unittest.TestCase):
    frames = [9, 10, 11, 12, 13]
    object_id = "cream_cheese_1"
    execution_id = "synthetic-execution"
    task_id = "synthetic-task"

    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.trajectory = self.root / "trajectory.h5"
        self.predictions = self.root / "predictions.json"
        self.seal = self.root / "PREDICTION_SEAL.json"
        self.review = self.root / "independent_review.json"
        self.registry = RegistryV3(self.root / "registry.sqlite", source_root=self.root, create=True)
        self.addCleanup(self.registry.close)
        self.checker = frozen_checker_configuration()

    def _records(self, *, fall=False, absence=False):
        xml = self.root / "simulator.xml"
        xml.write_text(
            '<mujoco><worldbody><body name="cream_cheese_1_main"/>'
            '<body name="living_room_table"/></worldbody></mujoco>'
        )
        native = save(self.root / "native_map.json", {
            "schema_version": "native-geometry-index-v2",
            "source_xml_sha256": binding(xml)["sha256"],
            "validated_run_ids": [self.execution_id],
            "body_names": ["cream_cheese_1_main", "living_room_table"],
            "native_geom_count": 2,
            "geometries": [
                {"native_geom_id": 0, "owner_body_id": 0, "name": "object", "collision_capable": True},
                {"native_geom_id": 1, "owner_body_id": 1, "name": "table", "collision_capable": True},
            ],
        })
        supported = {"geom1": 0, "geom2": 1, "dist": 0.0, "pos": [0.0, 0.0, 0.5]}
        with h5py.File(self.trajectory, "w") as recording:
            recording.attrs["global_episode_id"] = self.execution_id
            recording.attrs["task_configuration_id"] = self.task_id
            for frame in self.frames:
                heights = [0.6 if not absence else 0.8, 0.4]
                if fall and frame >= 12:
                    heights[0] = 0.6 - (frame - 11) * 0.05
                pairs = [] if absence or (fall and frame >= 12) else [supported]
                group = recording.create_group(f"frames/{frame:06d}/simulator")
                group["body_xpos/value"] = [[0.0, 0.0, z] for z in heights]
                group["geom_xpos/value"] = [[0.0, 0.0, z] for z in heights]
                group["time/value"] = frame / 20
                group["ncon/value"] = len(pairs)
                group.create_group("contacts").attrs["json"] = canonical(pairs).decode()
        trajectory = binding(self.trajectory)
        scope = {
            "execution_id": self.execution_id, "task_id": self.task_id, "object_id": self.object_id,
            "trajectory_sha256": trajectory["sha256"], "clock": "saved_frame_index",
        }
        records = []
        for family, selector in (
            ("object_pose", "body_xpos/value"),
            ("native_geometry", "geom_xpos/value"),
            ("contact", "contacts"),
        ):
            records.append(make_record({
                "schema_version": "2.0.0", "requirement_id": "R1", "requirement_version": R1_V3,
                **scope,
                "kind": "raw_measurement", "measurement_type": family, "validation_status": "verified_source",
                "source": trajectory, "domain": "frame", "interval": [9, 13],
                "saved_frames": [
                    {
                        "frame": frame, "selectors": [f"/frames/{frame:06d}/simulator/{selector}"],
                        "simulator_time_seconds": frame / 20,
                    } for frame in self.frames
                ],
                "native_binding": {
                    "body_id": 0, "collision_geom_ids": [0],
                    "pose_phase": "native_last_forward_cache_uncalibrated_phase",
                    "simulator_xml": binding(xml), "mapping": {**native, "selector": "/geometries"},
                },
                "uncertainty": ["Synthetic saved endpoints."], "limitations": ["CPU fixture."],
            }))
        self.registry.add(records)
        citations = [
            {"record_id": row["id"], "measurement_type": row["measurement_type"], "frames": list(self.frames)}
            for row in records
        ]
        return {**scope, "frame_interval": [10, 13]}, citations

    def _prediction(self, scope, *, outcome=NEGATIVE):
        identities = {
            "run_id": scope["execution_id"], "canonical_object_id": scope["object_id"],
            "requirement_version": R1_V3,
        }
        applicability = "does_not_apply" if outcome == "not_applicable" else "applies"
        initial = {
            "applicability": applicability,
            "support_class": "direct_stable_table" if applicability == "applies" else "established_absence",
            "evidence": {"frames": [9, 10, 11], "boundary_frame": 10},
        }
        if applicability == "applies":
            initial["evidence"]["support_chain"] = [scope["object_id"], "living_room_table"]
        return {
            **identities, "requirement_id": "R1", "checker_version": self.checker["version"],
            "recording_sha256": scope["trajectory_sha256"],
            "configuration_sha256": self.checker["configuration_sha256"],
            "implementation_freeze_sha256": self.checker["implementation_freeze_sha256"],
            "source_commit": self.checker["source_commit"],
            "requested_frame_interval": scope["frame_interval"],
            "measurement_frame_intervals": [scope["frame_interval"]],
            "applicable_observation_intervals": [scope["frame_interval"]] if outcome == NEGATIVE else [],
            "applicability": applicability, "outcome": outcome, "initial_support": initial,
            "events": [{
                **identities, "event_id": "synthetic:fall", "type": "r1_fall", "phase": "departure",
                "scope": "in_scope", "status": "established", "interval": [11, 13],
                "onset_bracket": [11, 12], "onset": 12,
                "evidence": {
                    "lift_event_id": None, "support_departure_bracket": [11, 12],
                    "downward_motion_bracket": [12, 13],
                },
            }] if outcome == "violation" else [],
        }

    def _write_prediction(self, request, prediction, **seal_changes):
        artifact = save(self.predictions, [prediction])
        seal = save(self.seal, {
            "files": {"predictions.json": artifact["sha256"]},
            "reference_answers_loaded": False,
            **seal_changes,
        })
        request["prediction"] = {"artifact": artifact, "seal": seal, "row_index": 0}

    def request(self, *, outcome=NEGATIVE):
        scope, citations = self._records(fall=outcome == "violation", absence=outcome == "not_applicable")
        request = {
            "schema_version": "1.0.0", "requirement_id": "R1", "requirement_version": R1_V3,
            "purpose": "empirical_admission", "scope": scope, "citations": citations,
        }
        self._write_prediction(request, self._prediction(scope, outcome=outcome))
        return request

    def approve(self, request, **changes):
        intake = {key: value for key, value in request.items() if key != "review"}
        refs = [item["record_id"] for item in request["citations"]]
        proof = {
            "schema_version": "1.0.0", "kind": "independent_empirical_review",
            "review_id": "synthetic-review", "source_group_id": "synthetic-source-group",
            "input_sha256": digest(intake),
            "development_exposed": False, "independent_reference_validated": True,
            "gates": {
                gate: {"verification_sha256": digest({"synthetic_gate": gate}), "evidence_ids": refs}
                for gate in PHYSICAL_GATES
            },
            **changes,
        }
        request["review"] = save(self.review, proof)
        return (request["review"]["sha256"],)

    def run_assessment(self, request, trusted=()):
        return assess(request, source_root=self.root, registry=self.registry, trusted_review_hashes=trusted)

    def test_authorized_saved_frame_negative_is_reproducible(self):
        request = self.request()
        trusted = self.approve(request)
        result = self.run_assessment(request, trusted)
        self.assertEqual(result["admission_status"], "admitted")
        self.assertEqual(result["conclusion"], {"applicability": "applies", "outcome": NEGATIVE, "witness_event": None})
        self.assertIs(result["coverage"]["continuous_time_coverage"], False)
        self.assertEqual({gate["status"] for gate in result["gate_ledger"]}, {"verified"})
        self.assertEqual(require_admitted_assessment(
            result, request, source_root=self.root, registry=self.registry, trusted_review_hashes=trusted,
        ), result)

    def test_authorized_violation_binds_the_saved_in_scope_event(self):
        request = self.request(outcome="violation")
        result = self.run_assessment(request, self.approve(request))
        self.assertEqual(result["conclusion"]["witness_event"], {
            "event_id": "synthetic:fall", "selector": "/0/events/0", "interval": [11, 13],
        })

    def test_authorized_absence_is_scoped_non_applicability(self):
        request = self.request(outcome="not_applicable")
        result = self.run_assessment(request, self.approve(request))
        self.assertEqual(result["conclusion"]["applicability"], "does_not_apply")
        self.assertEqual(result["conclusion"]["outcome"], "not_applicable")

    def test_request_supplied_review_cannot_authorize_itself(self):
        request = self.request()
        self.approve(request)
        result = self.run_assessment(request)
        self.assertIn("independent_review_not_authorized", result["blockers"])
        self.assertIsNone(result["conclusion"])
        with self.assertRaisesRegex(ValueError, "not admitted"):
            require_admitted_assessment(result, request, source_root=self.root, registry=self.registry)

    def test_development_purpose_blocks_even_a_pinned_receipt(self):
        request = self.request()
        request["purpose"] = "development_diagnostic"
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("development_only_prediction", result["blockers"])
        self.assertIsNone(result["review"])
        self.assertIsNone(result["conclusion"])

    def test_source_declared_development_blocks_even_a_pinned_receipt(self):
        request = self.request()
        prediction = {**self._prediction(request["scope"]), "development_only": True}
        self._write_prediction(request, prediction)
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("development_only_prediction", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_malformed_development_marker_is_rejected(self):
        request = self.request()
        prediction = self._prediction(request["scope"])
        for row, seal in (
            ({**prediction, "development_only": "true"}, {}),
            (prediction, {"synthetic": 1}),
        ):
            self._write_prediction(request, row, **seal)
            with self.assertRaisesRegex(ValueError, "development markers must be boolean"):
                self.run_assessment(request, self.approve(request))

    def test_scope_mismatch_in_registry_citations_is_blocked(self):
        request = self.request()
        request["scope"]["task_id"] = "different-task"
        result = self.run_assessment(request, self.approve(request))
        self.assertEqual({row["status"] for row in result["evidence_ledger"]}, {"blocked"})
        self.assertIn("unverified_registry_citations", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_sparse_contact_citations_block_the_approved_negative(self):
        request = self.request()
        contact = next(item for item in request["citations"] if item["measurement_type"] == "contact")
        contact["frames"].remove(12)
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("G09_contact_based_physical_evidence", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_negative_without_qualified_coverage_is_blocked(self):
        request = self.request()
        prediction = self._prediction(request["scope"])
        prediction["applicable_observation_intervals"] = [[10, 11]]
        self._write_prediction(request, prediction)
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("G06_qualified_negative_certificate", result["blockers"])
        self.assertIn("G07_static_coverage_composition", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_fall_with_incompatible_phase_or_window_is_blocked(self):
        request = self.request(outcome="violation")
        prediction = self._prediction(request["scope"], outcome="violation")
        prediction["events"][0]["interval"] = [11, 14]
        self._write_prediction(request, prediction)
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("G05_validated_falling_witness", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_fall_descent_cannot_overlap_support_departure(self):
        request = self.request(outcome="violation")
        prediction = self._prediction(request["scope"], outcome="violation")
        prediction["events"][0]["evidence"]["downward_motion_bracket"] = [11, 12]
        self._write_prediction(request, prediction)
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("G05_validated_falling_witness", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_conflicting_in_scope_event_blocks_negative(self):
        request = self.request()
        prediction = self._prediction(request["scope"])
        prediction["events"] = self._prediction(request["scope"], outcome="violation")["events"]
        self._write_prediction(request, prediction)
        result = self.run_assessment(request, self.approve(request))
        self.assertIn("checker_outcome_conflicts_with_an_in_scope_fall", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_prediction_hash_and_seal_are_verified(self):
        request = self.request()
        original = self.predictions.read_bytes()
        self.predictions.write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
            self.run_assessment(request)
        self.predictions.write_bytes(original)
        self._write_prediction(request, self._prediction(request["scope"]), reference_answers_loaded=True)
        with self.assertRaisesRegex(ValueError, "prediction seal"):
            self.run_assessment(request)

    def test_prediction_and_configuration_scope_reject_mismatches(self):
        request = self.request()
        for key, value in (
            ("configuration_sha256", "0" * 64), ("recording_sha256", "0" * 64),
            ("canonical_object_id", "butter_1"), ("requested_frame_interval", [10, 14]),
        ):
            prediction = {**self._prediction(request["scope"]), key: value}
            self._write_prediction(request, prediction)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "prediction"):
                self.run_assessment(request)

    def test_review_cannot_be_replayed_or_omit_gates(self):
        request = self.request()
        trusted = self.approve(request, gates={})
        with self.assertRaisesRegex(ValueError, "review.*gates"):
            self.run_assessment(request, trusted)
        trusted = self.approve(request)
        request["citations"].pop()
        with self.assertRaisesRegex(ValueError, "scope or gate inventory"):
            self.run_assessment(request, trusted)

    def test_gate_proof_requires_verified_citation_ids(self):
        request = self.request()
        self.approve(request)
        proofs = load(self.review)["gates"]
        gate = "G12_independent_reference_validation"
        proofs[gate]["evidence_ids"] = ["ev:" + "0" * 64]
        result = self.run_assessment(request, self.approve(request, gates=proofs))
        self.assertIn(gate, result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_gate_proof_requires_relevant_evidence(self):
        request = self.request()
        self.approve(request)
        proofs = load(self.review)["gates"]
        gate = "G03_geometry_empirical_admission"
        proofs[gate]["evidence_ids"] = [
            item["record_id"] for item in request["citations"] if item["measurement_type"] == "object_pose"
        ]
        result = self.run_assessment(request, self.approve(request, gates=proofs))
        self.assertTrue(all(row["status"] == "verified_source" for row in result["evidence_ledger"]))
        self.assertEqual(result["blockers"], [gate])
        self.assertIsNone(result["conclusion"])

    def test_gate_proof_must_cite_the_required_frames(self):
        request = self.request()
        contact = next(row for row in self.registry.records() if row["measurement_type"] == "contact")
        payload = {key: value for key, value in contact.items() if key != "id"}
        short = make_record({**payload, "saved_frames": payload["saved_frames"][:2]})
        self.registry.add([short])
        request["citations"].append(
            {"record_id": short["id"], "measurement_type": "contact", "frames": [9, 10]}
        )
        self.approve(request)
        proofs = load(self.review)["gates"]
        gate = "G09_contact_based_physical_evidence"
        proofs[gate]["evidence_ids"] = [short["id"]]
        result = self.run_assessment(request, self.approve(request, gates=proofs))
        self.assertEqual(result["blockers"], [gate])
        self.assertIsNone(result["conclusion"])

    def test_individually_verified_citations_must_agree_on_the_simulator_model(self):
        request = self.request()
        alternate = self.root / "alternate_capture"
        alternate.mkdir()
        trajectory = alternate / "trajectory.h5"
        copyfile(self.trajectory, trajectory)
        xml = alternate / "simulator.xml"
        xml.write_bytes((self.root / "simulator.xml").read_bytes() + b"\n<!-- distinct model artifact -->\n")
        native_map = load(self.root / "native_map.json")
        native_map["source_xml_sha256"] = binding(xml)["sha256"]
        mapping = save(alternate / "native_map.json", native_map)
        old = next(row for row in self.registry.records() if row["measurement_type"] == "contact")
        payload = {key: value for key, value in old.items() if key != "id"}
        alternate_contact = make_record({
            **payload,
            "source": binding(trajectory),
            "native_binding": {
                **old["native_binding"], "simulator_xml": binding(xml),
                "mapping": {**mapping, "selector": "/geometries"},
            },
        })
        self.registry.add([alternate_contact])
        contact = next(row for row in request["citations"] if row["measurement_type"] == "contact")
        contact["record_id"] = alternate_contact["id"]
        result = self.run_assessment(request, self.approve(request))
        self.assertTrue(all(row["status"] == "verified_source" for row in result["evidence_ledger"]))
        self.assertIn("G03_geometry_empirical_admission", result["blockers"])
        self.assertIn("G09_contact_based_physical_evidence", result["blockers"])
        self.assertIsNone(result["conclusion"])

    def test_assessment_hash_alone_cannot_authorize_a_modified_result(self):
        request = self.request()
        trusted = self.approve(request)
        result = self.run_assessment(request, trusted)
        modified = deepcopy(result)
        modified["gate_ledger"][0]["reason"] = "A different review reason."
        modified["assessment_hash"] = digest({
            key: value for key, value in modified.items() if key != "assessment_hash"
        })
        for assessment, trust in ((modified, trusted), (result, ())):
            with self.assertRaisesRegex(ValueError, "verified inputs and admission policy"):
                validate_assessment(
                    assessment, request, source_root=self.root, registry=self.registry, trusted_review_hashes=trust,
                )

    def test_evaluation_only_reference_is_excluded(self):
        request = self.request()
        reference = self.root / "HUMAN_REFERENCE_EVALUATION_ONLY.json"
        request["prediction"]["seal"] = save(reference, {"synthetic_fixture": True})
        with self.assertRaisesRegex(ValueError, "evaluation-only human reference"):
            self.run_assessment(request)


class ArchivedDevelopmentTests(unittest.TestCase):
    def test_all_sealed_development_predictions_remain_unadmitted(self):
        root = CHECKER / "execution"
        predictions = binding(root / "predictions.json")
        seal = binding(root / "PREDICTION_SEAL.json")
        catalog = load(CHECKER.parent / "r1_reference" / "recordings.json")
        rows = load(root / "predictions.json")
        self.assertEqual(len(rows), 20)
        for index, row in enumerate(rows):
            request = {
                "schema_version": "1.0.0", "requirement_id": "R1", "requirement_version": R1_V3,
                "purpose": "empirical_admission",
                "scope": {
                    "execution_id": row["run_id"], "task_id": catalog["task_id"],
                    "object_id": row["canonical_object_id"], "trajectory_sha256": row["recording_sha256"],
                    "clock": "saved_frame_index", "frame_interval": row["requested_frame_interval"],
                },
                "prediction": {"artifact": predictions, "seal": seal, "row_index": index},
                "citations": [],
                "review": {"path": str(root / "unused_review.json"), "sha256": "0" * 64},
            }
            with self.subTest(index=index):
                result = assess(request, source_root=root, trusted_review_hashes=("0" * 64,))
                self.assertEqual(result["admission_status"], "not_admitted")
                self.assertIn("development_only_prediction", result["blockers"])
                self.assertIsNone(result["conclusion"])
        self.assertEqual(binding(root / "predictions.json"), predictions)
        self.assertEqual(binding(root / "PREDICTION_SEAL.json"), seal)
