# Phase 2B.2 measurement validation

All research processing ran on Hestia. Baseline ace3ef3becd0c2ce2d9cb45488707bf2101ce384; branch feat/r1-v4-libero-measurement-reader. Empirical R1 admission remains disabled.

## Restored inputs

38 exact original files were restored and freshly hash-verified, totaling 649816079 bytes. All expected digests match, including the resolved 58927-byte initial-state archive. RESTORED_SOURCES.json identifies every original/restored/archive/member path; HASH_VERIFICATION.json records fresh checksums and before/after preservation. No original recording or archive was overwritten or deleted.

| Episode | Seed | Saved frames validated | Required reader bundle |
|---|---:|---:|---|
| 000 | 1000 | 258 | Complete |
| 001 | 1001 | 277 | Complete |
| 002 | 1002 | 246 | Complete |
| 014 | 1014 | 531 | Complete |

The 1,312-frame saved projection passes identity, metadata, native mapping, array shape/type/finiteness, flattened endpoint state, initial-state, stage/control/transition, monotonic clock, static table-pose and contact-list/count checks. Transform residuals are freshly recomputed with the unchanged numerical guard. Camera references are checked without decoding pixels. Unexposed native/raw fields remain named in field_inventory.

## Tests and demonstration

| Suite | Passed | Failed | Skipped |
|---|---:|---:|---:|
| New reader | 44 | 0 | 0 |
| Phase 2A | 105 | 0 | 0 |
| Frozen V3 | 41 | 0 | 0 |
| Reference | 17 | 0 | 0 |
| Generalization | 13 | 0 | 0 |

Total 220 tests pass. New tests cover real recordings, synthetic measurements, missing/corrupt files, hashes, metadata/version/checkpoint, array shapes/types/nonfinite values, native/anonymous/object identities, coordinates, static-root changes, contact fields/counts, frame/state/initial-state/transition timing, gaps, camera limitations, unsafe HDF5 links/storage, deterministic serialization, code/source provenance, typed unknown-truth observations, and CLI source protection/exclusive output.

validation/RESULTS.json and logs preserve commands, environment, counts and log digests. CLI output /disk/1/data/niktakbr/r1-v4-phase2b2-working/cli-example-bound.json is byte-identical to the library result; validation/CLI_DEMONSTRATION.json records its digest. No physical judgment is issued. These selected regressions pass; the broader historical suite is not claimed repaired or fully rerun.

## V4 and preservation

Existing V4 measurement/frame/contact/camera/uncertainty types are reused. Bridge observations use direct_measurement, physical truth U, hashes and null uncalibrated uncertainty. No empirical adapter/profile is registered; no applicability, support, fall, handling event, positive or negative witness is produced. Native/raw phases and frames remain distinct. Per-contact normals/forces are None; unsupported camera synchronization remains explicit.

Frozen checks pass before/after: 16 audited sources, four live V3/config/execute/prediction digests, two seals with 12 members, eight human-scoring protected files and the scoring freeze. Every Phase2B.1 artifact hash matches. Git scope is limited to this new directory. Historical code, predictions, references and safeguards are unchanged. No NV/held-out execution is in the fixed scope. Synthetic fixtures remain explicit and never enter empirical evaluation.

No simulation, rendering, policy run, RAG, multi-agent implementation, Alliance compute or Sea/ISSTA access occurred. New data/artifacts are on disk1. Disk0 remains below the 500 GB reserve; no cleanup or large write occurred there. Existing packages were read with -S; none were installed and no environment was modified. Nothing was pushed or merged.

## Scientific limits

Measurement availability does not establish support or physical event validity. Geometry precision, contact interpretation, cache/exposure phase, displacement uncertainty, handling, boundary inference and qualified negative coverage need calibrated profiles and independent references. Continuous/dynamic coverage and unsupported geometry reasoning remain deferred. Weight checksum metadata is preserved; weights were not freshly verified. No accuracy, certification or human-validated reference claim is made.

CAPABILITY_MATRIX.csv classifies 20 capabilities. PHASE_2B3_READINESS.md identifies the next work. ARTIFACT_SHA256.json binds compact deliverables; Git binds that manifest. Raw payloads remain outside Git.
