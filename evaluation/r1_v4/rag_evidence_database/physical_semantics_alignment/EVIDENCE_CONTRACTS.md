# Physical semantics contracts, physical-semantics-1.0.0

This additive interpretation layer preserves all 83,378 Phase 5G evidence/channel
records, values, fields, contracts and variants. No measurement channel is added.

Each interpretation identifies execution/task/variant, original channel record,
source path/hash, exact dtype/shape and model mapping. Mappings are compiled with
MuJoCo 3.8.1 and compared to every recorded joint name and qpos/qvel address.
Recorder/run hashes match execution metadata. Installed robosuite 1.4.0 is a
version-matched reference, not recording-time binary attestation.

VERIFIED means a specific recorded/model property has primary-source support and
independent source validation. CONDITIONAL requires the stated model, unit-system
or timing assumption. UNRESOLVED lacks sufficient evidence. UNSUPPORTED is not
provided by this contract. No status certifies physical calibration or safety.

| Raw channel | Model interpretation | Units / frame | Limitation |
|---|---|---|---|
| raw.robot0_joint_pos | Seven hinge configurations in recorded/model order | rad; joint_configuration | Not Cartesian/world position |
| raw.robot0_joint_vel | Same seven joint tangent velocities | rad/s; joint_tangent_velocity | Not same-index endpoint qvel |
| raw.robot0_gripper_qpos | Two slide finger-joint configurations | m under recorded metric convention; joint_configuration | Not eef position, action or finger opening distance |
| raw.robot0_gripper_qvel | Same two slide-joint velocities | m/s under metric convention; joint_tangent_velocity | Signed joint axes, not Cartesian velocity |
| raw.simulator_actuator_force | Nine scalar actuator outputs, seven hinge and two slide transmissions | native_actuator_force; actuator_transmission | Model torque/force dimensions verified; N*m/N CONDITIONAL on MKS mass convention. Never contact force |
| simulator.ncon | Saved simulator contact-entry count | count; not_applicable_count | Not events, support or violations |

Exact joint/body/actuator IDs, addresses, local axes/anchors, gains/biases and
unit gears are variant-bound. No name-similarity identity rule. Projection y=x[j]
is an explicit original component view, not another recorded channel. No
normalization, interpolation, coordinate transform or value shift is applied.

For noninitial frames the recorded configurations satisfy q_raw=q_endpoint-h*v,
h=0.002s. Independent inverse Euler velocity validation uses
v_pre=v_endpoint-h*(M(q_pre)+hD)^(-1)*M(q_pre)*qacc. These verify model algebraic
consistency. Actual cache time endpoint-h remains CONDITIONAL without runtime
sensor timestamps or recording-time binary attestation. Initial frames have a
separate endpoint relation. No shifted values are indexed; synchronized physical
instant retrieval stays unsupported.

Snapshots have verified 0.05s simulator intervals. Action k maps to post-call
frame k+11 after ten settling frames and frame zero. Latest observation is k+10;
actual inference input follows recorded chunk ID/inference step. Queued actions
do not imply fresh inference. control_step is not a timestamp. Snapshot wall and
monotonic clocks are not exposure timestamps. Raw cache refresh rate is a
CONDITIONAL source property, separate from verified saved-frame interval.

Numeric tolerances are fixed float64 roundoff bounds in config.py and the
velocity pilot, not fitted offsets or physical thresholds. Errors and abstentions
are reported independently. No physics trajectory is replayed; velocity validation
uses only source states, kinematic mass evaluation and algebraic consistency.

Strict source access hashes an O_NOFOLLOW open descriptor before/after use.
Verified-session access first hashes bytes, then requires unchanged device, inode,
size, mtime, ctime and link count; changes rehash. Both read HDF5 through that same
descriptor, validate dtype/shape/execution ID and recheck path identity. No decoded
value cache. Missing, redirected, modified or malformed sources fail closed.
Hash-matching restored files regain verification after fresh hashing. No unverified
mode is exposed.

Retrieval enforces execution/task/variant/channel/object/component, units, frame,
transformation and requested property status before ranking. Requested conditional
properties need explicit opt-in. Scores cannot override guards. main_table remains
the separate, bounded Phase 5G derived identity; logical-table/world transforms and
safety inference remain unsupported. Empirical R1 admission remains disabled.
