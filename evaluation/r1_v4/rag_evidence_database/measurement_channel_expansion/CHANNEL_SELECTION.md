# Frozen bounded selection

CHANNEL_SELECTION.json was created after the complete 432-execution HDF5 census
and before installing or running the extractor. Its inventory-summary hash and
baseline identity are frozen. Later JSON and geometry inventory supplements do
not change the selection. All six channels have 58,075 recorded source samples
across all 432 executions and 104 variants. No additional profiles are admitted.

| Channel | Scientific inspection value | Status | Cost and independent check |
|---|---|---|---|
| raw.robot0_gripper_qpos | Inspect changes in the recorded gripper configuration vector | Direct raw values; units, component order and physical frame unverified | One series reference per execution; exact h5py sample comparisons |
| raw.robot0_gripper_qvel | Inspect recorded gripper velocity-vector changes | Direct raw values; physical units/order unverified | Same; finite/type/shape checks and exact samples |
| raw.robot0_joint_pos | Inspect recorded robot joint configuration history | Direct raw values; joint order/units unverified | Same; compare each saved vector independently |
| raw.robot0_joint_vel | Inspect recorded robot joint velocity history | Direct raw values; joint order/units unverified | Same; no differentiation or normalization |
| raw.simulator_actuator_force | Inspect saved actuator-output-array changes | Direct raw values; actuator order and units unverified | Same; no joint-torque/contact-force interpretation |
| simulator.ncon | Find the saved simulator contact-entry count | Direct recorded nonnegative integer; count units | Same; independent comparison to decoded saved contact-list length |

The recorder source has the metadata-bound SHA-256
7ce898669c01fd3a6b7a7c3217a6326464ff9343aab32c25fe4a16b08b1f5268
in all 432 executions. It copies raw observations and simulator arrays; `ncon`
is copied from `sim.data.ncon`. This verifies the recording pathway, not the
physical semantics of raw observation components or dynamics-cache timing.

Each source is decoded once per build and independently decoded once for full
validation. Numeric arrays remain in HDF5; the database stores series references,
valid/missing indices, hashes and bounded descriptions. The six channels add
2,592 records without increasing execution count or duplicating raw time series.
Retrieval decodes only explicit saved-frame windows. Build measurements and
storage growth are reported in EXTRACTION_VALIDATION.md.

Additional body/geom poses, contacts, qpos/qvel/ctrl and timestamps already have
Phase 5F family references. Raw eef/object observables, cvel, qacc, cfrc_ext,
sensordata, sites, policy inputs/actions and resource/clock metadata remain
inventoried but are not automatically promoted to validated physical channels.
Their units, reference points, object associations and temporal alignment need
individual contracts. No derived channels are implemented in this release.
