# Phase 2A validation report

Restricted analytical infrastructure: PASS. Complete repository suite: NOT GREEN;
pre-existing failures are retained and reproduced at the untouched base commit.

Base: `609ac744b1b2fb899c783de5bb3df3c39943f57e`.
Branch: `feat/r1-v4-restricted-infrastructure`. Checker `4.0.0a1`.
All execution was CPU-only on Hestia. No simulations, model calls, empirical labels,
physical fall detector, environment installation, push or merge occurred.

## Final tests

| Suite | Tests run | Result |
|---|---:|---|
| baseline_existing | 44 | Baseline failures retained: 3 problem tests, 7 skips |
| existing | 44 | Baseline failures retained: 3 problem tests, 7 skips |
| frozen_v3 | 41 | PASS |
| phase2a | 105 | PASS |
| r1_reference | 17 | PASS |
| r1_v3_ai_assisted_human_verification_20261030 | 11 | PASS |
| r1_v3_ai_only_adjudication_20261030 | 8 | PASS |
| r1_v3_generalization | 13 | PASS |
| r1_v3_human_validation_20 | 27 | One missing historical-report fixture error, reproduced at baseline |

The new suite includes all 3,906 outcome vectors of lengths 0–5, permutation checks,
0/1/3/5/17-object execution, invalid configuration/versions/hashes, static roots,
identity/absence, support-link dependencies/cycles, missing/invalid/contradictory
records, temporal gaps and uncertainty, schema serialization and CLI overwrite guards.
It tests declared analytical facts and admission, never physical detector accuracy.
The final conflict regression verifies that dependency-invalid negative candidates
cannot suppress independent valid positives. Actual admissible conflicts suspend
both dependent witnesses before aggregation.

All 55 original acceptance cases are mapped in
[ACCEPTANCE_COVERAGE.json](validation/ACCEPTANCE_COVERAGE.json): 50 have analytical
contract coverage, four retain deferred physical capabilities, and independent
empirical evaluation remains pending. A contract test for an event predicate does
not claim completion of its planned physical trajectory/measurement test.

## Existing failures and skips

The broad suite has 34 passes, two failures, one error and seven skips out of 44.
The untouched baseline reproduces the exact problem-test list and counts:

- Missing historical `data/requirement_pilots/20261016T154747Z/config.json`.
- Storage-test expectation of two filesystems; this disk1 checkout yields one.
- Existing distributed human-review template contains nonblank human fields.

The human-validation suite has 26 passes and one baseline-identical missing-file
error: `human_review_package/adjudication/test_results_final_baseline_20261026.txt`.
That missing report fixture does not indicate a changed live scoring safeguard.
No historical report, template, reference, seal or scoring policy was edited to
make tests pass. Seven old MuJoCo compiler tests skip because MuJoCo is unavailable.
Existing numpy/h5py packages were read with `-S` for frozen tests; no .pth startup
hooks, environment installation or simulator stepping were used.

## Reproducible demonstrations

| Synthetic demonstration | Full vector | Aggregate |
|---|---|---|
| Three objects | V, qualified N, NA | V with incomplete evidence |
| Five objects | qualified N, NA, U, verified-absent NA, IC | IC; study eligibility pending |
| Multiple static surfaces | qualified N, qualified N, qualified N | Qualified N at explicit saved-projection cells |

Each demonstration ran through the CLI and reproduced byte-identical library output.
Input/output hashes, exact commands and complete structured assessments are in
[demonstrations/SUMMARY.json](validation/demonstrations/SUMMARY.json). These are
synthetic declarations, not LIBERO observations, simulations or empirical effectiveness.

## Integrity and scope

All 16 audited baseline source hashes, four live V3/prediction hashes, both evaluation
seals and 12 sealed members match. The scoring freeze itself and all eight protected
scoring files match. All pre-existing tracked repository files and the finalized
specification remain unchanged. See [FROZEN_INTEGRITY.json](validation/FROZEN_INTEGRITY.json).

New artifacts are confined to `evaluation/r1_v4/` in the Hestia worktree
`/disk/1/data/niktakbr/trustworthy-phase16`. Development logs and earlier intermediate
snapshots remain under `/disk/1/data/niktakbr/r1-v4-phase2a-validation/`. No original
recordings were modified. No Sea/ISSTA access or Alliance compute was used. Disk0
already had about 360 GB free, below the 500 GB reserve; disk1 had about 1.6 TB.
No cleanup was attempted and no large artifacts were written to disk0.

## Phase 2B prerequisites

Empirical admission remains disabled, including asserted validated LIBERO profiles.
Required next work is a separately authorized recorder/model/task-scoped LIBERO
reader and evidence audit, explicit identity/frame/clock/geometry bindings, support
and phase validation, and independent calibration before any physical witness profile
can be admitted. No contact, alignment, persistence or geometry threshold was invented.

Negative measurement certificates and independent positive/negative/NA/uncertain
reference validation remain pending. Natural and controlled strata must stay separate;
AI-only historical agreement is not human-validated accuracy. Intended-study eligibility
for verified absent objects still needs a study-protocol decision. Re-arm, complex
handoffs, dynamic/multiple-parent reasoning and dynamic/handling negative composition
remain deferred. Phase 2A makes no empirical safety, accuracy or certification claim.

Analytical geometry/support/gravity/identity-transform/arithmetic references resolve
through the bound built-in profile. The clock binds to the hashed domain; roots
bind to the synthetic model/common frame. Unknown references and unsupported
boundary-context inference fail closed, with no implicit adapter defaults.
