# Narrow-fact evidence sufficiency

The production APIs do not classify sufficiency. All categories below come from the external predeclared rubric, not retriever assertions or an LLM judge. There is no physical-safety sufficiency result.

| Mode | Sufficient | Conditional | Insufficient | Unavailable | Ambiguous | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| exact | 81 | 3 | 12 | 41 | 1 | 24 |
| lexical | 48 | 0 | 18 | 71 | 1 | 24 |
| semantic | 80 | 0 | 12 | 45 | 1 | 24 |

Each case records separate relevance, completeness, credibility, attribution, numerical matching and uncertainty requirements. Required facets must all be present for a sufficient result. Conditional sufficiency is explicitly limited to a documented cache assumption or verified metadata document requiring field inspection. An answerable false candidate number may be contradicted by sufficient source evidence; sufficient does not mean the candidate assertion is true.

Missing-facet counts across final modes: `{"action_chunk_metadata": 3, "action_metadata": 6, "actuator_temperature": 3, "applied_control_series": 3, "calibrated_depth": 3, "camera_exposure_time": 3, "camera_exposure_timestamp": 6, "checkpoint_declaration": 2, "collision_impulse": 3, "contact_force_world": 3, "contact_pairs_and_force": 3, "continuous_physical_coverage": 3, "encoder_calibration": 3, "exact_temporal_scope": 3, "external_load_cell": 3, "finger_taxels": 3, "geometry_identity": 24, "hardware_accelerometer": 3, "historical_binary": 3, "identity_document": 2, "inference_metadata": 3, "main_table_alias": 12, "measured_friction": 3, "microphone_audio": 3, "physical_metrology_certificate": 3, "physical_support": 6, "physical_support_event": 3, "provenance_report": 1, "raw.robot0_gripper_qpos": 62, "raw.robot0_gripper_qvel": 8, "raw.robot0_joint_pos": 51, "raw.robot0_joint_vel": 19, "raw.simulator_actuator_force": 11, "recorder_host_timestamp": 3, "sensor_clock_calibration": 3, "sensor_clock_sync": 3, "simulator.ncon": 2, "source_hash": 4, "support_sensor": 3, "wrist_force_torque": 3}`. Counts include repeated modes and deliberately unsupported requests; they are not prevalence estimates.

The six exposed measurement families do not form an automatic cross-interface evidence assembler. Frame/action/chunk association summaries are available, but do not substitute for original action vectors, original policy/inference entries and their source fields in the stricter completeness checklist. Camera exposure clocks, calibration and physical event claims remain unsupported. Contact-pair references exist in the legacy corpus; missing pair-force/physical-time interpretation must not be described as absence of all contact data.

A verified main_table symbolic mapping exists in bounded tabletop source audits, but direct logical alias retrieval remains a gap in the evaluated interfaces. Geometry identity references can support native identity without establishing pose, support, contact or safety. No geometric identity has been promoted to a physical-event conclusion.

A zero-hit lexical/semantic result is classified unavailable at that interface/query, not evidence that the source artifact never existed. Source absence claims rely on the independent source/contract audit, not search failure.

Reference-validity qualification: the table above preserves raw frozen-scorer output. C7-20 (final) retained an unrelated arm-position requirement after its metadata-only reference revision; its sufficiency judgment is invalid. C7-06 is the analogous development annotation. Do not interpret either as a demonstrated production failure. The dataset, criteria and raw results are unchanged. The following post-hoc validity overlay excludes only these completeness judgments, not relevance/source/assurance measurements, and does not change recommendation B.

| Mode | Valid final sufficiency n | Counts after validity exclusion |
|---|---:|---|
| exact | 161 | {"AMBIGUOUS": 1, "CONDITIONALLY_SUFFICIENT": 3, "INSUFFICIENT": 11, "INVALID": 24, "SUFFICIENT": 81, "UNAVAILABLE": 41} |
| lexical | 161 | {"AMBIGUOUS": 1, "INSUFFICIENT": 18, "INVALID": 24, "SUFFICIENT": 48, "UNAVAILABLE": 70} |
| semantic | 161 | {"AMBIGUOUS": 1, "INSUFFICIENT": 12, "INVALID": 24, "SUFFICIENT": 80, "UNAVAILABLE": 44} |
