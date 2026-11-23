# RQ3 conditional-source CPU validation report

All commands were rerun from the repository root on feature branch research/m4-rq3-source-eligibility-20261123 after fast-forwarding to origin/main commit efece5dd8bc409d201f585e0da377dcb37ebcf5f. Environment: Python 3.14.2. No GPU inference, model call, simulation, reviewer-submission access, or data modification was performed.

## Checks and results

The staged-file whitespace check passed with Git treating CRLF as a line ending: git -c core.whitespace=cr-at-eol diff --cached --check. Existing CSV bytes were preserved. The staged-file secret/private-data and oversized-file scans found no matches; no raw recordings or weights are staged.

| CPU command | Result |
|---|---|
| python3 evaluation/m4_20261127/rq3/heldout_expansion/build_source_eligibility_matrix.py | PASS: generated 20 source rows; 0 admitted; blocker counts are overlapping. |
| python3 evaluation/m4_20261127/rq3/heldout_expansion/build_source_eligibility_matrix.py --check | PASS: 20 distinct execution IDs/hashes; source-group independence not verified; 20 prior-build receipts; 1,214-file prior evidence-archive receipt and 180 video receipts structurally checked; 0 admitted; blocker totals match case rows. Task count is 10 task00 + 10 task01; exact-ID intersection with the 432-row source catalogue is 0. |
| python3 evaluation/m4_20261127/rq3/heldout_expansion/validate_drafter_generation_manifest.py --check-template | PASS: required columns present, 0 approved generation rows, inference not run. |
| python3 -m unittest drafter.tests.test_decoder_regressions drafter.tests.test_validation_regressions drafter.tests.test_ordered_plan | PASS: 42 tests in 21.534 seconds. Covers invalid graph endpoints, evidence citation constraints, statement/prose validity, and ordered-plan invariants. |
| python3 -m unittest evaluation.m4_20261127.rq3.heldout_expansion.tests.test_heldout_readiness | PASS: 2 tests; no fabricated parent arguments, mutations, or requests. |
| python3 -m unittest evaluation.m4_20261127.rq3.heldout_expansion.tests.test_source_eligibility | PASS: new matrix and admission invariants. |

## Checks not claimed as passing

- No Drafter request-schema or Phase 5 adapter validation was run for these candidates: no request exists, and required source/configuration/approval bindings are missing.
- Original HDF5 bytes were not freshly re-opened or rehashed: the prior package build verified hashes but did not retain the resolved source root/per-case selector in the repository receipt.
- No model generation or accepted GSN parent was produced.
- Source-metadata checks do not establish physical safety, R1 applicability, or an R1 violation.
- No current serializer implementation changes were made. The prior saved invalid model output remains unmodified.
