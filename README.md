# OpenVLA–LIBERO execution inventory

Current stage: execution inventory only. No LLM is implemented or called. Requirements (including proposals), cases, claims, checked safety events and objections are empty. Benchmark failures remain benchmark outcomes, with safety status `not_assessed` and no violation verdict.

## Sources and coverage

Source recordings: `/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero`.
Model: `moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10`, revision `638918f3d1c2e43a39a8a20772bdb8b91835e4b7`.
40 tasks, 50 runs each, 2,000 runs total. Recorded success: Goal 96.4%, Spatial 91.4%, Object 98.8%, Long 95.2%. These numbers describe task completion only.

`data/tasks.json` contains environment facts and the separate environment success definition. `data/runs.json` contains each execution's identity, outcome, native objects, conditions, measurement inventory and file references. `reports/existing_annotations_audit.json` inventories source JSON files and records the search for existing structured safety annotations. `reports/source_manifest.json` contains small-file hashes. Each run's `execution_files` lists its existing artifacts, byte sizes and producer integrity entries where available.

Large trajectories and videos remain in their original locations and formats. Small task BDDL definitions and the verified checkpoint tokenizer are retained under `evidence/`. Token decoding checks logged prompts; it does not invoke a model.

## Identifier contract

| Field | Meaning and convention |
|---|---|
| task_id | Existing unique `task_configuration_id`, preserved verbatim |
| run_id | Existing unique `global_episode_id`, preserved verbatim |
| step_id | Original zero-based integer control index within a run; `(run_id, step_id)` identifies a transition |
| requirement_id | Future reviewed requirement; no instances allocated |
| case_id | Future safety case; no instances allocated |
| claim_id | Future claim within a case; no instances allocated |
| event_id | Future selected event from approved rules; no instances allocated |
| objection_id | Future criticism; no instances allocated |

The suite-local numeric task ID is retained separately as `benchmark_task_id`; it repeats across suites. Native body, geometry and joint IDs are valid only within the run's simulator index. Do not match them across runs without their run ID.

## Instructions and environment facts

The exact recorded policy instruction is primary. BDDL language is retained separately, and exact text differences are reported in `reports/instruction_mismatches.json` (30 tasks). All recorded inference token sequences are decoded using the hash-verified source tokenizer and checked against the logged instruction. A missing recorded instruction would use an explicitly marked BDDL fallback; none were needed in this collection.

Objects and fixtures come from semantic initial conditions, BDDL and simulator XML/index. Region declarations are marked when their target is absent from the declared scene. Native table/floor geometry is recorded separately from BDDL fixture names; an unverified name alias is not imposed. Intended interaction records the instruction, objects of interest and goal predicates; no contact permissions are inferred.

## Measurements and limitations

Recorded evidence includes actions, policy chunks and inference linkage; control transitions and timestamps; robot joint, gripper and end-effector observations; object poses; simulator positions, velocities and body/geometry/site transforms; contact geometry IDs, distance and position; RGB camera observations and two camera videos; initial conditions, simulator XML/index, evaluator code/version and resource logs.

XML declares end-effector force and torque sensors and six sensor values are recorded. Channel mapping, units and calibration are not tabulated in the recording index, so physical thresholds or calibrated interpretations are not inferred. Contact records do not contain per-contact forces. Continuous physics-substep contacts, material damage, fragility, human presence, prohibited regions and a safety contact policy are not supplied. Task failure alone cannot establish a safety violation.

Measurement-key inventory samples first/middle/final frames of every run. All recorded control transitions remain accessible. The raw accessor verifies the original step and frame control-step alignment. Its `frame_id`/`video_frame_id` use recorded frame indices, including initial/settling frames; videos have not been independently decoded to verify every frame. Full HDF5 checksums are referenced from producer manifests, with current byte sizes checked; large arrays were not independently rehashed.

## Commands

Run on Hestia:

```bash
cd /local/home/niktakbr/trustworthy_project
bash pipeline.sh inventory
bash pipeline.sh validate
bash pipeline.sh transition --run-id '<existing global_episode_id>' --step-id 0
bash pipeline.sh collect
```

`collect` regenerates task/run inventory without executing a policy or simulator. `validate` checks every task/run link, suite outcome, native body binding and trajectory byte size, plus first/last transitions in each suite and invalid-step rejection. Python uses the existing Hestia virtual environment identified in `pipeline.sh`.

Future requirement proposal, initial safety-case generation, event checking and criticism are outside this implementation. Any later event must reference its run, start/end steps, reviewed requirement, checker version and supporting measurements. Ordinary transitions do not receive event IDs. The future study concerns whether an argument reflects recorded executions; revising an argument does not certify that a policy is safer.
