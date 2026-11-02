# Recorder and identity contract

Exact source hashes are in SOURCE_BINDINGS.json. Fresh bytes match Phase 2A baseline. Historical producer identity is separately checked for run_oft.py, recording_base.py and semantic_scene.py against reports/fall_review_v2_20261016/source_provenance.json.

## Model and task

Sample: LIBERO canonical suite libero_10 (directory label long), task00, task configuration 2448c758145ae5ad500f; LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket. Instruction: put both the alphabet soup and the tomato sauce in the basket. BDDL evidence/task_definitions/2448c758145ae5ad500f.bddl has expected SHA256 2e661058917f683a25bce480015197f0a2c1911bcbc2b9dd9d947199069c9618.

Historical checkpoint metadata: moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10, revision 638918f3d1c2e43a39a8a20772bdb8b91835e4b7; experiment openvla-oft-6e4ac614cfafd9ddc3db; model configuration 85620572476d4a08fc0d. Sources: data/requirement_inputs/v2-confirmed/provenance.json scope and data/runs.json. Weight bytes were not reloaded or freshly verified. Original metadata must be restored before re-attesting raw execution identity.

Producer run_oft.py schema 4.0 wraps base Recorder. It saves global_episode_id, model/task/experiment IDs and recorder/dataset versions; seed=1000+episode, initial state index=episode modulo archive length. Horizon 520, 256x256 observations, 20 Hz control, ten settling commands, native eight-action open-loop chunks, no added domain randomization. These are cohort settings.

## Format

HDF5 roots include frames, transitions, policy_steps, inference_calls, preprocessing, language_inputs, benchmark_initial_state, settling_actions and upstream_rollout. write_tree stores leaf arrays beneath value datasets. Frame keys are six-digit indices. Snapshot attributes include stage, control_step, UTC, wall and monotonic host clocks. Simulator fields include time, flattened state, qpos/qvel/ctrl, body_xpos/body_xquat, site_xpos and ncon; optional native arrays include qacc, cvel, cfrc_ext, actuator_force, geom_xpos/geom_xmat and sensor data. Check each record's availability.

Contacts store geom1, geom2, dist and pos only. Per-contact forces, normals/frame and impulse history are omitted. Body external forces and sensor channels cannot be relabeled as per-contact forces. MP4 images are rotated 180 degrees for viewing; raw uint8 camera arrays were stored in HDF5. No original cameras were decoded in this audit.

Freshly hashed gzip exports contain run/frame IDs, world geom poses, contacts, nominal phase and previously computed identity_guard residuals. They omit qpos, body poses, raw ncon, cameras and inference inputs. Residual bounds are checked internally, not regenerated from missing raw arrays. Hashes establish content identity, not physical truth.

Preserved evidence/geometry_v2/simulator.xml SHA256 a6177b7383b3b273ed1f41ad1ca342c921aea86584348a6d05a4bdff703e4542 matches the native map. All 161 native IDs, including anonymous geometry, are retained. Never resolve contacts through the lossy legacy geom_names list. XML equality alone does not validate another recorder/task/profile.
