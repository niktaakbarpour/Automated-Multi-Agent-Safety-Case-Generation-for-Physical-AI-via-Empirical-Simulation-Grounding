# Measurement audit: existing LIBERO Long task 00 recordings

This is an evidence-availability and consistency audit, not a fall checker or a safety assessment. No runs are assigned fall/no-fall verdicts. Both pilots, their original responses and human-review files remain unchanged.

## Inspected executions and files

Task ID: `2448c758145ae5ad500f`; instruction: put both the alphabet soup and the tomato sauce in the basket. Scope is the 50 OpenVLA-OFT FT-All executions registered for this task, not other models or additional experiments.

Source root on Hestia:

`/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero/long/task_00/`

Directories `episode_000` through `episode_049`; seeds 1000–1049. Run IDs follow `libero_long_openvla_oft_task00_seed{seed}_trial{episode:03d}_cfafd9ddc3db`. The complete explicit list and recording paths are in `runs_inspected.csv` and `runs.json`.

For every run, inspected every stored frame's protected-object positions/orientations, simulator numerical state arrays, contact records and timeline, plus every control transition and matching policy executed action. Read metadata.json, semantic_initial_conditions.json, simulator_index.json, simulator.xml, simulator_asset_manifest.json, evaluator_version.json, completion.json and integrity_manifest.json. All 89 asset-manifest entries per run were checked for existence and content hashes, with caching for identical referenced files. One identical simulator XML hash occurs across all runs. Exact file paths and hashes are in `runs.json`; native geometry/ownership is in `compiled_geometry_mappings.json`.

The numerical audit read all 14,215 frames, not just first/middle/final samples. It did not visually adjudicate image contents, decode the MP4s, rerun policies, step physics, detect falls or assess task safety. Both raw camera datasets were checked for presence/shape/dtype throughout. The trajectory files were opened read-only; sizes match producer manifests and size/mtime stayed unchanged during scanning. Full multi-gigabyte HDF5 file hashes were not recomputed: producer hashes are explicitly marked as producer values. A new digest covers the audited numerical payload, not images or the entire HDF5 file.

## Coverage across every stored frame

| Protected object | Finite position samples | Finite quaternion samples | Missing/wrong-shape/nonfinite samples |
|---|---:|---:|---:|
| cream_cheese_1 | 14,215 / 14,215 | 14,215 / 14,215 | 0 |
| ketchup_1 | 14,215 / 14,215 | 14,215 / 14,215 | 0 |
| orange_juice_1 | 14,215 / 14,215 | 14,215 / 14,215 | 0 |
| milk_1 | 14,215 / 14,215 | 14,215 / 14,215 | 0 |
| butter_1 | 14,215 / 14,215 | 14,215 / 14,215 | 0 |

`position_coverage.csv` gives every frame/object pair, stage, control step, simulator time, raw and simulator root positions, their difference, field statuses and observed table-contact count. `timeline.csv` gives every frame's simulator and host timestamps. `runs.json` contains per-run counts and any bad-frame lists. These records audit field availability, not semantic event labels.

Every frame also has finite qpos, qvel, qacc, ctrl, flattened simulator state, body_xpos, body_xquat, geom_xpos, geom_xmat, site_xpos, site_xmat, ncon, cvel, cfrc_ext, actuator_force and sensordata. `act` is present and finite but empty in this model; its presence does not imply an actuator-activation signal. Both raw cameras are uint8 `(256,256,3)` datasets in all frames. Lossless raw images remain in HDF5; MP4s are compressed 20 FPS display views rotated 180 degrees by the recorder and add no temporal samples.

## Control actions, timestamps, beginning and termination

There are 13,665 policy control actions in total, 235–520 per run. Frame stages total 50 before_settling, 500 settling, 13,615 control and 50 terminal. Every run has contiguous frame IDs and policy control-step IDs, one transition per executed policy action, and a final terminal snapshot. No missing stored control endpoint intervals were found. Policy and transition executed actions match exactly; transition simulator times match their post-action frame times exactly.

For each run:

- Frame 000000 is the pre-settling state at simulator time 0.
- Frames 000001–000010 follow ten settling commands. The last settling frame is at simulator time approximately 0.5 seconds and is the state before policy control action 0.
- Action index i (zero based) maps to post-action frame i+11. `control_step=0` also occurs on settling frames, so stage must be read; that attribute alone is not a unique action index.
- First policy-action endpoint is at approximately 0.55 seconds; the last endpoint is 12.25–26.5 seconds depending on the run. Exact run-specific termination steps, times, flags and UTC are in `runs.json` and `runs_inspected.csv`.
- A single final transition is marked terminated or truncated and its frame is terminal. The audited source takes that snapshot before breaking, with no autoreset. Termination may depend on task completion or horizon, but the proposed requirement is independent of task success.

Simulator endpoint spacing is 0.05 seconds (20 Hz); maximum numerical deviation from that period is about 2.77e−14 seconds. Model physics timestep is 0.002 seconds. Intermediate physics-step poses/contacts are not recorded. The largest host-monotonic gap between snapshots is 0.705606 seconds, including computation/recording time, while simulator endpoint cadence remains continuous. Frame UTC, monotonic_ns and wall_time_ns are host snapshot times, not independent capture times for each observation. Policy UTC is recorded before env.step, transition UTC after snapshot; exact first-action monotonic start time and per-sensor capture times are absent. The interval is bracketed by the last settling and first action endpoint, not measured continuously inside it. No frames continue after terminal state, so later motion is unobserved.

Review must resolve whether the draft's 'first control action' means policy action 0 or also the ten earlier settling commands. This audit exposes both boundaries and does not change the proposed text or silently choose an approved scope.

## Units, coordinate frames and physical reference points

The preserved recorder source hashes match the producer metadata. `run_oft.py` lines 126–155 establish settling, policy action execution, snapshot ordering and termination. `recording_base.py` lines 75–94 copies the raw observation and simulator fields; `semantic_scene.py` lines 2–9 and 56 reads native root-body poses and explicitly declares MuJoCo world positions/distances in metres and semantic quaternions wxyz.

The installed LIBERO bddl_base_domain.py matches its hash in every run's recorded evaluator provenance. Its `_setup_references` resolves each object's `root_body` to a native body ID (approximately lines 413–433), and `_create_obj_sensors` (approximately lines 501–525) returns body_xpos for `{object}_pos` and converts body_xquat to xyzw for `{object}_quat`. Therefore the field's intended frame is world and its point is the root-body frame origin, not necessarily COM, lowest point, contact point or tabletop. `initial_geometry_evidence.json` includes local body inertial offsets, which are nonzero for these objects. Simulator body_xquat and semantic quaternions use wxyz; raw object quaternions use xyzw. Gravity from the compiled model is `[0,0,-9.81]` in that world frame. These establish the simulator/producer metre convention, not an independent physical calibration.

Field semantics are stronger than in the pilot's three-frame input, but synchronization remains qualified. Same-frame raw root positions differ from simulator body_xpos by up to:

| Object | Maximum raw-vs-body position discrepancy |
|---|---:|
| cream_cheese_1 | 0.006502433 m |
| ketchup_1 | 0.006395678 m |
| orange_juice_1 | 0.006074382 m |
| milk_1 | 0.006063653 m |
| butter_1 | 0.000525302 m |

Quaternions can differ too. Free-joint qpos translations also differ from derived body poses, with maximum discrepancy about 0.006529056 m. These are measured inconsistencies between representations at a stored endpoint, not uncertainty tolerances or fall thresholds. Current robosuite environment/base.py and observables.py show sampled/cached observations and the simulation-update ordering; binding_utils.py shows name projection. Their source copies and hashes are supplied, but historical producer hashes for those robosuite dependency files were not recorded. They support an explanation, not a claim of exact historical sensor delay. Per-field sample times and exact phase offsets still need independent validation; never assign every cached field the snapshot time or silently replace recorded poses with qpos reconstruction.

## Geometry, IDs and contact records

Body names (29), joint names (17) and joint qpos addresses match compiled XML native IDs in all 50 runs. Native geometry arrays contain 161 entries, but simulator_index.geom_names has only 155. The current binding wrapper forms its name list from a name-to-ID dictionary; repeated unnamed geoms collapse to a single None entry. The saved list exactly matches that projection, not native ID order. In this model, seven unnamed table geoms become one list entry, shifting subsequent named entries by six. Direct list indexing mislabels contacts. The old task/run inventory uses that indexing; `inventory_geom_id_discrepancies.json` records 4,000 mismatching object-geometry entries over the 50 runs. Original inventories remain unchanged; the audit's separate compiled mapping is the source for further review.

The reconstructed XML ordering is cross-checked across all recorded geometry positions and body transforms. Maximum position-component residual is 2.50e−16 m; rotation-component residual reaches 1.8648e−6. A saved-XML serialization/precision difference is a possible explanation for residual rotations, but has not been independently established; no acceptance tolerance is chosen. Detailed rotation residual examples are retained. Geometry correspondence is strongly supported, but fully validated shape/contact semantics and rotation error acceptance remain review work.

living_room_table body has descendant living_room_table_col, one visual mesh and six collision boxes, native collision IDs 10–15. Their recorded poses do not change over any inspected frame. For example, collision box 10 has runtime world bounds approximately x=[−0.69432,0.19432], y=[−0.61932,0.72410], z=[0.41308,0.43676]. Its geometric upper face is a candidate support face at world z=0.43676, derived from the box size and recorded transform—not from any object's root. Other box bounds are supplied per run; semantic designation of the supporting face remains pending. Floor is native geom 8, a plane at world origin with identity rotation. The visual table mesh must not substitute for collision support geometry.

All 456,612 stored contact records were read. Every contact list length matches ncon; IDs are in compiled range and distances/positions are finite. Contacts expose geom1, geom2, dist and world pos. Per-contact normal/frame, per-contact force/impulse, persistent contact identity and intermediate substep contact history are absent. Other force/sensor arrays exist but have not been validated as support-force measurements or causal evidence.

## Initial support, per run

`initial_support_inventory.csv` lists each run/object at the last settling frame; `initial_geometry_evidence.json` adds collision bounds, root and inertial offsets, mapped contact pairs and table/floor geometry. It does not adjudicate support. At that boundary:

| Object | Runs with any recorded table contact |
|---|---:|
| cream_cheese_1 | 49 / 50 (none in episode_002 / seed 1002) |
| ketchup_1 | 0 / 50 |
| orange_juice_1 | 0 / 50 |
| milk_1 | 0 / 50 |
| butter_1 | 50 / 50 |

For the reference run, cream-cheese and butter collision minima are near the candidate top face and each has four table contacts. Ketchup's initial collision z range is approximately 0.98125–1.12688; orange juice and milk approximately 0.82236–0.95356. These values come from recorded geometry transforms and compiled collision shapes, not root-height heuristics. They show why initial support cannot be assumed from BDDL On declarations or a list of protected objects. No automatic non-applicability or pass is assigned to any object or run. Whether the initial instant is pre-settling or pre-policy-action, and which geometric/contact evidence establishes support, must be reviewed; the complete timeline preserves both phases.

Native object/body and geometry mapping can be reconstructed for every run, with the residual-rotation qualification above. Evidence to investigate initial support exists for every run, but actual support and its semantic criterion are not yet independently validated. That is **available but unvalidated** evidence, not absent evidence. Absence of table contact at the stored boundary is specifically reported; it is not confused with missing contact data or proof of non-support.

## Readiness and evidence gaps

The recordings are substantially richer than the pilot input and support development of a coverage-qualified checker specification. They do not yet justify calling a continuous fall checker reliable. Required review/validation includes the fall definition; interval and initial-support instant; true support faces/bindings; mapping rotation residuals; measurement phase alignment; geometry-based treatment of tipped/lifted objects; event evidence independent of floor landing; and the limits imposed by endpoint-only storage. Numeric thresholds are intentionally unset.

Absent: substep snapshots/contact history, independent raw-sensor capture timestamps, post-termination observations and the listed per-contact quantities. Available but not fully validated: initial support, execution support-face bindings, field synchronization, contact interpretation, rotation reconstruction precision and visual corroboration. No missing numerical position samples were found in the stored frame sequences.

The four audit-helper tests passed. They check JSON/scalar decoding, missing/nonfinite/shape distinctions, quaternion conversion mathematics and nested/anonymous native geometry indexing. They are synthetic parser/mapping tests, not validation of a fall checker or evidence of safe robot execution. The first audit attempt exposed a string-encoding assumption; that parser error was fixed, its log retained, and the full 50-run scan completed afterwards. No recording was modified.
