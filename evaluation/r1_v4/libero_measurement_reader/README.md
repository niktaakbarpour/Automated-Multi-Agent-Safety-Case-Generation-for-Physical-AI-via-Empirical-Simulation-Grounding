# Bounded LIBERO measurement reader — Phase 2B.2

Version 1.0.0 reads only the hash-bound OpenVLA-OFT LIBERO long/task00 development episodes 000,001,002,014. It issues measurement records and diagnostics. It never assesses R1 applicability, support, falling, handling exclusion, positive witnesses or negative certificates.

## Architecture

- reader.py opens HDF5 in mode r, verifies the11 required per-execution/shared input files, producer metadata/manifests, frame structure, arrays, native transforms, contact bundles, clocks and static saved table geometry. The complete 161-ID map preserves anonymous geoms.
- models.py adds typed Channel, ContactRecord, Snapshot and ReadResult interfaces, reusing existing V4 Frame, Measurement, Contact, Camera and Uncertainty types. Arrays retain source paths, shapes, dtypes, phases and hashes.
- bridge.py exposes optional V4 Evidence objects with claim=observation and truth=U. VERIFIED validity means the stated measurement-structure scope only. No empirical profile is registered. ReadResult.evidence_records, inferred_events and checker_judgments remain empty. The existing empirical admission gate is unchanged.
- __main__.py provides the read-only CLI. It creates new output files outside the evidence root, on owned disk1, or writes stdout. It never overwrites an output. Exit0 means verified stored measurements, never a safety result; exit1 reports missing/invalid/unsupported measurement input.
- restore_receive.py is the Hestia-only selective receiver; RESTORATION_PLAN.json and RESTORED_SOURCES.json retain exact archive/member/original/restored bindings. It creates files exclusively and checks known source hashes.
- SOURCE_CONTRACT.json pins retained native-map/helper/constraint sources and declares compatible requirement2.0.0/config2.0.1/manifest1.0.0/evidence1.0.0 versions. This reader does not create an empirical assessment manifest or activate compatibility by itself.

## Scope and statuses

verified_measurements means only that the requested stored measurement contract passed. missing, invalid and unsupported remain structured diagnostics. Valid snapshots are retained with explicit coverage when another local record fails; the bridge conservatively emits no observations for an overall failed result. There is no missing-to-NA or missing-to-negative conversion.

Saved native geometry/body poses use metric MuJoCo world coordinates and wxyz body quaternions. qpos/qvel contain mixed native coordinates. Raw observable frames, units and quaternion conventions remain explicitly unverified rather than relabeled as world coordinates. Endpoint qpos/qvel, last-forward geometry/contact caches and raw observation caches remain distinct. Exact phase/exposure uncertainty is null, never a zero-error assertion.

Contact.complete refers only to equality of the recorded contact-list length and recorded ncon at that snapshot. It supplies no load-bearing proof or between-snapshot completeness. Contact normals/forces remain None. Cameras expose source/index/shape references without pixel decoding or exposure synchronization. Full geometry references include unsupported shapes without solving them; the five protected-object collision unions are BOX pieces under this exact XML.

The reader reuses the unchanged NativeGeometryIndex arithmetic consistency guard. Its 512-epsilon roundoff budget is not a calibrated physical tolerance. No numeric fall/contact/persistence/alignment threshold is introduced. No simulation, physics stepping, rendering, model invocation or policy evaluation occurs.

## Data and validation

Original restored files are outside Git at /disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence/long/task_00. All38 files match expected hashes; the initial-state archive is now resolved. The four required measurement bundles are complete. MP4s, model weights and unrelated episode sidecars were not restored. Raw HDF5 includes the original stored camera images; this reader does not inspect their pixels.

See REPRODUCIBILITY.md, RESTORATION_REPORT.md, RECORDER_COMPATIBILITY.md, MEASUREMENT_VALIDATION_REPORT.md, CAPABILITY_MATRIX.csv and PHASE_2B3_READINESS.md. Exact artifact hashes are in ARTIFACT_SHA256.json; Git binds that manifest itself.
