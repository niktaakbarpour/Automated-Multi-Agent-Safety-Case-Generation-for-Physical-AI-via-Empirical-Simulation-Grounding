# Phase 5A validation

Parent: `6c41960c9658fc0ef67406b3d27330169eba8335`; implementation branch: `feat/versioned-evidence-registry-gsn`. Architecture was documented before implementation. All research execution and source inspection ran on Hestia with owned /disk/1 outputs. No installations, simulations, Alliance jobs, Sea NFS access, ISSTA access or additional image transfers were performed.

## Results

| Suite | Passed | Failed / skipped |
|---|---:|---:|
| Registry, retrieval, GSN, real-source integration | 73 | 0 / 0 |
| Phase 2A infrastructure | 105 | 0 / 0 |
| Measurement reader | 44 | 0 / 0 |
| Measurement profile | 30 | 0 / 0 |
| Phase 2B.4 review | 15 | 0 / 0 |
| Frozen V3 | 41 | 0 / 0 |
| Reference regressions | 17 | 0 / 0 |
| Generalization regressions | 13 | 0 / 0 |
| Total | 338 | 0 / 0 |

Tests cover stable IDs, changed identities and versions, immutable persistence, readonly access, hash mismatch/missing sources, unapproved/symlink sources, exact and reproducible queries, wrong execution/object/version, per-type temporal gaps, overlapping availability, unsupported geometry/alignment, capability restrictions, dependency scope/clock/conflicts/transitive source failure, uncertainty, schema validation, graph provenance/edge/cycle/interval constraints and forbidden claim promotion. Synthetic fixtures are explicitly labeled and separate from development integration. No frozen outcomes are used as development labels. The relevant suites pass; this report does not claim every unrelated historical repository test has been repaired or executed.

Two independently built SQLite indexes yielded byte-identical portable JSON exports, manifests, retrieval outputs, assessments, graph exports, integrity results and readable reports. SQLite binary identity is not required. The read-only CLI query also matched the structured API result in the completed smoke check. Final production exports bind implementation source hashes and the requirement and gate snapshot hashes.

## Demonstration

18 immutable records: 15 raw measurement references (three each of object pose, native BOX geometry, contact, timestamp and camera references), two documents and one provisional AI reference judgment. One approved development execution, episode 000, cream_cheese_1, frames 9/10/11. The full native map retains all 161 native geometry identities; selected geometry references name object ID 104 and static table IDs 10–15. This is a restricted source sample, not benchmark validation.

Retrieval returns 15 measurement records, exact source selectors/hashes and complete dependency metadata. It requests frame 12 as well and reports its absence from this index for every requested type. The source recording has further frames; index scope is not silently expanded. The 22-node/21-edge graph contains all eight supported node categories. Solution intervals bind to their individual source intervals inside the claim scope. R1 remains unresolved; no safety outcome, empirical witness, physical support judgment or negative certificate is admitted.

## Preservation

Fresh hashes of all 38 original restored files match Phase 2B.4 source bindings before and after validation. Previous audit, reader, measurement-profile and evidence-review artifact manifests verify unchanged. The blank human review form remains unchanged. Frozen V3 checker/configuration/executor and predictions match their preserved hashes. Both evaluation seals and 12 sealed members verify; the human-scoring freeze and eight protected scoring files verify. All pre-existing tracked files, including V4 decision and admission logic, remain unchanged. See validation/FROZEN_BEFORE.json and FROZEN_AFTER.json for exact hashes. Final staged scope and whitespace checks are restricted to this new directory.

## Limits and readiness

Measurement byte identity and structural validity do not establish physical predicate validity. Initial load-bearing support, empirical fall witnesses, negative certificates, uncertainty/phase calibration and independent physical references remain blocked. Geometry and contact physical admission remain conditional; dynamic coverage composition is unsupported; camera exposure alignment is unresolved. AI interpretations remain provisional and are not human ground truth. No verified in-scope R1 positive has been established. Even all-VERIFIED external gate flags cannot enable physical checking through this adapter.

Ready for a bounded provenance-aware drafting/criticism/revision prototype with explicit unresolved claims. Not ready for empirical R1 admission or safety certification. No agents or new retrieval models were executed here.

## Exact locations

Committed package: `/disk/1/data/niktakbr/trustworthy-phase16/evaluation/r1_v4/evidence_registry_gsn/`.

Production database: `/disk/1/data/niktakbr/trustworthy-phase5a-working/release-validation/demo-a/registry.sqlite`.

Reproduction database: sibling `demo-b/registry.sqlite`. Full test logs and validation results: `/disk/1/data/niktakbr/trustworthy-phase5a-working/release-validation/`. Compact exports, graph and readable report: package `demo/`. Compact machine results and frozen checks: package `validation/`. Source evidence remains under `/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence/long/task_00/` unchanged. No database, recording, video or large numerical array is committed. ARTIFACT_SHA256.json binds all compact deliverables except itself.
