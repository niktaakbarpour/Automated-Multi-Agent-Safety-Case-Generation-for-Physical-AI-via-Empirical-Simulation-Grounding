# RQ2 Task 7C retrospective Checker evaluation

**Status:** completed retrospective development evaluation. This is a publication of recovered Task 7C/7D results; no Checker execution, simulation, GPU job, rescoring run, or reference-label change was performed for this publication.

## Cohort and method

The cohort contains 20 human-reviewed Task 8C evaluation units from 10 matched source groups for the frozen R1 v3 Checker and its versioned Task 8C source adapter. The separately finalized Task 8D reference was approved on 2026-11-24. The Checker implementation was frozen and its outputs were recorded later, on 2026-11-25. Although predictions were sealed before the evaluation join/scoring step and were not provided to the reference process, the reference predates the Checker workflow; this is retrospective compatibility evaluation, not a prospective blinded holdout.

For verification, the sealed Task 7C outputs were reconciled against the approved reference, Task 8D source bindings, Checker/reference join, per-case result ledger, and recorded outputs. Case IDs, evaluation-unit/object identity, source group, execution identity, recording hash, outcome category, and binding flags were checked. All 20 case joins and source bindings matched; no mismatch was found. The Task 7C manifest covered 30 artifacts, all of whose hashes matched. The approved-reference integrity manifest covered 12 files, all of whose hashes and sizes matched. The Task 7D verifier independently recomputed the joins and metrics, and its numerical summary matched the recovered summary byte-for-byte.

Runner provenance was verified for 18/20 cases. The frozen Checker ran on those 18 cases; two cases were not executed because source-runner provenance was unavailable. They are not negative predictions, abstentions, or execution failures. The determinately scored subset had no abstentions, invalid outcomes, or execution failures.

## Results

The confusion matrix for the 18 executed, eligible cases is:

| Approved human reference | Checker: violation | Checker: no violation | Total |
|---|---:|---:|---:|
| Violation observed | 7 (TP) | 1 (FN) | 8 |
| No violation within validated coverage | 2 (FP) | 8 (TN) | 10 |
| **Total** | **9** | **9** | **18** |

The full-cohort accounting, including the two non-executed cases, is in [COHORT_ACCOUNTING.csv](COHORT_ACCOUNTING.csv). The cases not executed for missing runner provenance are listed in [NOT_EXECUTED_CASES.csv](NOT_EXECUTED_CASES.csv): `case_d438b297` (approved-reference negative) and `case_d71df8f3` (approved-reference positive). Their missing predictions were excluded from the 18-case confusion matrix.

| Metric | Value | Calculation |
|---|---:|---:|
| Precision | 77.78% | 7 / (7 + 2) |
| Recall / sensitivity | 87.50% | 7 / (7 + 1) |
| F1 | 82.35% | 2 × 7 / (2 × 7 + 2 + 1) |
| Accuracy | 83.33% | (7 + 8) / 18 |
| Specificity | 80.00% | 8 / (8 + 2) |
| Full-cohort execution coverage | 90.00% | 18 / 20 |

Machine-readable values and source digests are in [PROVENANCE.json](PROVENANCE.json). The [checksum manifest](SHA256SUMS.txt) covers the published tables, report, and provenance.

## Interpretation and limitations

- This 20-case evaluation is retrospective and development-only. It is not an independent holdout or prospective blinded evaluation. The 20 cases comprise 10 matched source groups, not 20 independent source groups; one group had no eligible execution. No confidence interval or generalization claim is made.
- The approved reference records 20/20 agreement and classification Cohen’s κ=1.000. The approval record attests that the submissions were independent, but the two archived submission files are byte-identical and reviewer eligibility, prior exposure, and completion times are unrecorded. Those files therefore cannot independently establish separate review activity.
- The simplified categorical reference contains no event timestamps or evidence citations. In `case_bb7f216a`, the approved positive reference conflicts with all 258 saved simulation states showing table support. The discrepancy is unresolved; the reference and false-negative result are preserved unchanged.
- The two false positives show recorded table departure and downward motion after upward motion, without qualified robot-contact evidence. The Checker/reference disagreements remain unresolved; the Checker, rules, and labels were not changed.
- The scope is one controlled task, one designated object, one requirement version, one Checker/configuration, and one source-adapter version. The result does not establish natural policy-failure detection, cross-task or cross-scene generalization, physical truth, evidence admission, or safety-case validity. Checker performance does not itself admit an assessment to the evidence registry.

## Provenance and reproducibility boundary

The published provenance records bind these results to the approved reference, Task 7C prediction seal and ledger, source-manifest digest, frozen Checker version/configuration, and Task 8C adapter freeze. Raw reference submissions, raw evidence traces, remote payloads, and private source-binding files are not included. Consequently, a fresh clone can verify the published derived artifacts but cannot reproduce the private source join or checker execution from raw inputs. No experiment is to be rerun to use these results.
