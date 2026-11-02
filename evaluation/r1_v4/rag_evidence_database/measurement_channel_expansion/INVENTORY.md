# Recorded-versus-indexed inventory

The complete HDF5 dataset/group-attribute tree and available JSON fields were inspected for exactly 432 indexed executions. No reserved/preflight payloads or 1,470 pending profiles were inspected. Total: 58,075 saved frames; 139 dataset patterns, 36 attribute patterns, 2630 metadata keys. Availability is per execution and variant, not assumed uniform. Numeric event indices are normalized in inventory identifiers only; source selectors preserve original keys.

Phase 5F exposes body position/quaternion, native geom pose, robot qpos/qvel/ctrl, endpoint time, contact-list and camera references under established family records. A family reference does not necessarily provide independently typed numeric retrieval for each underlying array. Remaining fields distinguish saved-but-not-independently-searchable data, unextracted raw observations, data requiring decoding and fields with unverified units/frame/phase.

Phase 5G adds the six frozen channels. Each is present at all 58,075 saved samples. The inventory retains dtype/shape distributions, source keys/hashes, task/variant coverage, missing execution counts, extraction feasibility, validation requirements and uncertainty. Native geometry fields and logical bindings have GEOMETRY_CHANNEL_INVENTORY.csv and SPATIAL_BINDINGS.csv audits.

No video or resources.csv payload is locally available in the restored subset. Their absence here is not a claim that original archives lack them. Camera arrays and available HDF5 inference/rollout timing fields were inventoried. Recorder code documents videos and resource sampling, but those payloads were not restored or evaluated. Additional restoration is outside this bounded expansion.

No dedicated camera-exposure timestamp or direct per-contact-force dataset exists in the inspected HDF5 trees. Snapshot wall/monotonic attributes are not exposure times; actuator_force is not per-contact force. Object motion, eef arrays, cvel, cfrc_ext, qacc, sites, sensordata, actions and policy inputs remain inventoried with unverified semantics where applicable. Raw retrieval does not establish a validated world-frame trajectory.
