# Regression and preservation results

PASS: 521 automated tests;0 skipped; zero unexplained
failures. All 484 Phase5E tests and 37 new variant tests pass. Exact commands,
versions, return codes, counts and log SHA-256 values are in
validation/REGRESSION_RESULTS.json; full logs remain under `/disk/1/data/niktakbr/trustworthy-phase5f-working/qa`.

Fresh and independent builds have equal core exports and normalized-relation
build IDs. Resume skips 147 completed new jobs without duplicates. SQLite,
foreign keys, FTS/catalog/source dependencies and variant bindings pass. All
67,053 old evidence/index rows,2,000 catalog rows and 285 jobs remain exact.

3908 original source paths and
594 external profile/diagnostic artifacts
were freshly hash-checked. The immutable Phase5E DB remains `5d3eb7589ddbf564cf29189af3264fd9861df44780e65e3246b62bbe74bc9934`.
Baseline artifacts are unchanged; the intentionally versioned reader dispatch
is compared against its original Git commit, not falsely declared unchanged.
Frozen V3 code/predictions, both seals and their12 members, and eight protected
scoring files pass final verification. Human references/labels are untouched.

Initial pilot source-contract failures are retained in PROFILE_VALIDATION_PILOT_
ATTEMPT1/2 and external FAILURE artifacts. Consistent named asset aliases were
handled explicitly, recorded fixture roots verified, and main_table left
unresolved. No failing/skipped regression is hidden to declare success.

| Suite | Tests | Return code | Skipped |
|---|---|---|---|
| frozen_v3 | 41 | 0 | 0 |
| generalization | 13 | 0 | 0 |
| new_profile | 28 | 0 | 0 |
| partition | 8 | 0 | 0 |
| phase2a | 105 | 0 | 0 |
| phase5b | 45 | 0 | 0 |
| phase5c | 17 | 0 | 0 |
| phase5e | 32 | 0 | 0 |
| phase5e_semantic | 16 | 0 | 0 |
| profile | 30 | 0 | 0 |
| reader | 44 | 0 | 0 |
| reference | 17 | 0 | 0 |
| registry_gsn | 73 | 0 | 0 |
| review | 15 | 0 | 0 |
| variant | 37 | 0 | 0 |
