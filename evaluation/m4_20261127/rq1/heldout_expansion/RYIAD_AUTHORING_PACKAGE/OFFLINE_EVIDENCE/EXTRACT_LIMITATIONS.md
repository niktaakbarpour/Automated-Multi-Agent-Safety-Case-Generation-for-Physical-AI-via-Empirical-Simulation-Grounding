# Offline evidence extract: contents and limits

## What is included

The 30 verified source trajectories were read without modification. Their current SHA-256 values were recomputed and matched the frozen source-recovery receipts before extraction. The package contains 6,870 original evidence-record envelopes and 148,225 frame/evidence samples (29,645 per family) in EVIDENCE_SAMPLES.jsonl.gz. The sampled families are timestamp, contact, object_pose, robot_state, and native_geometry. Every sample carries the canonical execution, evidence ID, object/type, frame, original selector, resolved HDF5 selector, and source trajectory SHA-256. TASK_CONTEXT.csv contains the verified task-instruction source text and metadata; task metadata hashes are matched to the task_instruction source records.

The five exported selector families are:
- timestamp: simulator/time/value;
- contact: simulator/contacts group, with simulator/ncon/value retained as a separate raw count;
- object_pose: simulator/body_xpos and body_xquat at the body_id recorded in the evidence envelope;
- robot_state: simulator/qpos, qvel, and ctrl;
- native_geometry: simulator/geom_xpos and geom_xmat at collision_geom_ids recorded in the evidence envelope.

The extract does not transform or interpret these values. An evidence ID may cover many frames and the resulting rows remain clustered within their 30 source executions. They are not independent cases.

## Explicitly not distributed

All 1,050 camera_reference evidence records are listed in UNEXTRACTED_EVIDENCE.csv. Camera pixel arrays and MP4 video are not included. Visual questions and visual event checks therefore cannot be independently verified from this GitHub package.

Raw contact groups are empty in 29,624 of the 29,645 extracted contact samples; the other 21 preserve their recorded groups. Empty serialization is not a no-contact finding. The separately reported simulator ncon field is a simulator contact count and is not object-specific physical contact proof.

The compact package omits the original multi-gigabyte HDF5 files, XML/model source archives, full image arrays, and full evidence database. The original paths and hashes remain as provenance in the source indexes, but no offline task requires those original locations. Physical fall/support labels, continuous-motion judgments, camera verification, geometry/cache-phase resolution, and any R1 human reference are not included and must not be inferred from the extracts.

## Verification scope

The source-side exporter rehashed each original trajectory and checked it against SOURCE_RECOVERY_VERIFICATION.csv. A second CPU pass compared all 148,225 published sample values with the resolved selectors in the original trajectories; all matched exactly. The published verifier recomputes checksums of every bundled file, checks every extract row's evidence ID/selector/execution/source-hash binding against the bundled verification/index records, and confirms the blank authoring fields remain empty. Because the raw trajectories are intentionally not copied, a fresh checkout cannot rehash the original HDF5 bytes; it verifies the recorded source receipt and the exact bundled extract checksums.
