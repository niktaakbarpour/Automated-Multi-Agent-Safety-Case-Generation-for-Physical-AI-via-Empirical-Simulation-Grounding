# Phase 5G evidence contracts — phase5g-channel-1.0.0

Frozen selection: CHANNEL_SELECTION.json. Authoritative machine contracts are
`channels.contract(channel_id)`; their canonical hashes are stored in every
series record. This additive schema keeps the 1.0/1.1 core and variant schema
unchanged. A separate `rag_channel_schema` version gates the new tables. No
in-place baseline migration is permitted. Old retrieval uses unchanged tables;
new channel retrieval uses ChannelQuery. No records are admitted to physical
checking or empirical R1 assessment.

## Identity and provenance, common to all six channels

Exactly one immutable series-reference record per selected channel per existing
execution. The execution, task and XML/environment variant come from the sealed
Phase 5F execution binding. The source is the existing trajectory.h5, bound by
path and SHA-256. Exact field below is appended to `/frames/<original_key>/`.
Each record includes the exact source frame keys, valid indices, invalid sample
reasons, dtype/shape counts, numeric sample digest, XML hash, native-map hash,
contract hash and extractor/schema/selection producer hashes. Robot observation
association `robot0` means the recorded field prefix only; it does not establish
joint order or body/geom identities. Simulator arrays/counts use `*` and have no
per-object assignment. Native maps are provenance, not a spatial admission.

| Canonical channel | Source field | Required dimensions | Units | Frame | Phase |
|---|---|---|---|---|---|
| raw.robot0_gripper_qpos | raw_observation/robot0_gripper_qpos/value | numeric (2,) | unverified/null | uninterpreted_raw_array | raw observable cache, unknown phase |
| raw.robot0_gripper_qvel | raw_observation/robot0_gripper_qvel/value | numeric (2,) | unverified/null | uninterpreted_raw_array | raw observable cache, unknown phase |
| raw.robot0_joint_pos | raw_observation/robot0_joint_pos/value | numeric (7,) | unverified/null | uninterpreted_raw_array | raw observable cache, unknown phase |
| raw.robot0_joint_vel | raw_observation/robot0_joint_vel/value | numeric (7,) | unverified/null | uninterpreted_raw_array | raw observable cache, unknown phase |
| raw.simulator_actuator_force | simulator/actuator_force/value | numeric (9,) | unverified/null | uninterpreted_raw_array | native cache, uncalibrated phase |
| simulator.ncon | simulator/ncon/value | nonnegative integer scalar | count | not_applicable_count | native cache, uncalibrated phase |

## Measurement and extraction semantics

All six channels are directly recorded. Transformation is identity; values,
component order and numeric dtype are preserved. No derived measurement is
implemented. Source hashes, dtype/shape and finite values are checked. Counts
must be nonnegative integers. Missing datasets, incompatible shapes/types,
nonfinite arrays and invalid counts abstain at the individual sample, with an
explicit reason. They are never filled or interpolated. Generic arrays receive
no automatic spatial semantics; raw records are `validated_raw_values_only`.
The count is `validated_recorded_count`: it counts saved simulator entries,
not distinct physical events, forces, supported objects or violations.

Sampling is per recorded saved snapshot. Metadata control frequency is nominal;
no uniform physical sampling interval is guaranteed. Saved-frame index is the
only query clock. Original `stage` and `control_step` attributes are returned as
recorded labels; neither is silently converted to an action index. Endpoint
simulator time, last-forward caches, raw observations and camera exposures remain
separate. Exact physical phase bounds remain unknown. Initial, settling and
terminal snapshots are included only under their original keys and labels.

No alignment, interpolation, normalization, unit conversion, joint-order decoding,
frame transform, geometry projection or object support inference occurs. A new
physical interpretation requires a new validated contract/version. Numeric sample
digests summarize raw values; they are reproducibility metadata, not measurements.

## Retrieval semantics

ChannelQuery requires an execution ID before ranking or source reads. Optional
filters are exact task, variant, channel, object association, direct-recording
origin, declared units and frame. Temporal windows are inclusive saved-frame
indices; maximum width is 4096 samples. No seconds/exposure clock queries.
A metadata-only query returns compact series references; an explicit interval
returns exact source-decoded numeric samples and selectors. Values are never
replicated as complete arrays in every search record. Unknown objects, absent
samples, excluded executions and wrong scopes cannot be substituted. Raw unit
requests such as N, meters, radians and world coordinates remain unsupported.
A derived-origin request is rejected. FTS and optional pinned local semantic
ranking operate on fixed source-field descriptions after scope filtering. Neither
ranking method interprets the values or establishes physical confidence.

Source and geometry hashes are checked before values are returned. Cached hashes
are invalidated by filesystem device/inode/size/mtime/ctime changes. Record content,
contract identity, source association, task and variant are revalidated. Provenance
and cross-scope checks have zero tolerance. Numerical validation uses exact raw
matches and independent h5py reads; it does not claim physical synchronization.
