# Raw-to-index validation

Six channels, 2,592 series records, 432 executions, 104 variants. Preserved core records: 80,786. Direct channels: six; derived channels: zero. Per channel: 432 records and 58,075 valid samples. Missing/unsupported samples in selected actual recordings: 0.

Independent h5py oracle redecodes every selected sample using separately declared fields/shapes, compares the complete sample digest and validates decoded contact-list length against ncon. Samples validated: 348,450. Numeric components by channel: `{"contact_length_comparisons": 58075, "raw.robot0_gripper_qpos": 116150, "raw.robot0_gripper_qvel": 116150, "raw.robot0_joint_pos": 406525, "raw.robot0_joint_vel": 406525, "raw.simulator_actuator_force": 522675, "simulator.ncon": 58075}`.

Retrieved sample vectors/scalars independently compared: 12,960. Maximum absolute value error: 0.0. Saved-index alignment errors: 0. Unit/frame inconsistencies: 0. These errors concern encoded values/indices, not physical synchronization or calibration.

First successful build: 64.568 seconds. Database growth: 17,432,576 bytes. Projected additional peak was 10 GiB with no raw-corpus duplication; disk1 free at final audit: 1,627,120,291,840 bytes. Complete runtime/producer hashes are in validation summaries and external BUILD.json.

Missing fields, incompatible shapes/types, NaN/infinity, negative/floating counts and sparse windows are tested with isolated fixtures. Sparse samples are not interpolated or shifted. Raw status protects unknown units/frames. Original stage/control_step labels are preserved without inferred action alignment. Arrays remain in HDF5 and are decoded only for requested windows.
