# Regressions and preservation

Baseline before modifications: 578 tests passed. Final 665 tests pass (578 prior + 87 new), skipped 0, unexplained failures zero. Per-suite logs/commands are manifest-bound. New tests cover scratch tampering, verified DB identity, units, exact projection, unresolved/conditional properties, chronology/chunks and scope negatives.

Every Phase 5G table definition and row was compared exactly, including 80,786 evidence records, 2,592 raw references, FTS shadows, jobs, variants and exclusions. All 432 executions/104 variants remain. Baseline SHA `d1241f28089ff910baf8ec276fbaa3f9d2b71aa3c7b850fe494b976eb51320fb`. Phase 5E/F/G artifacts/manifests are intact.

Fresh final baseline manifests, original sources, native XML/index/model sources, primary code, frozen V3/V4 files, human reference/blinded packages, both seals and scoring guards pass. See validation/FROZEN_FINAL.json, PRESERVATION_FINAL.json and FINAL_AUDIT.json. Twelve seal members and eight scoring-protected files are unchanged. No checker/admission change.

Diagnostics retained: the velocity pilot initially used an incompatible mj_fullM signature, corrected from installed binding docs before full validation; provisional observation/inference labeling was refined using chunk metadata. Initial build candidate is preserved separately. No threshold, offset or label was tuned to conceal a failure. All subsequent applicable validation passes.

Unavailable video/resources, physical calibration, binary attestation, sensor/exposure clocks and unselected families remain explicitly untested/unsupported, never silently skipped from an admitted claim.
