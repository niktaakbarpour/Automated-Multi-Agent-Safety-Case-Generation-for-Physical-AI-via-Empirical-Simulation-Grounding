# RQ2 Requirement Checker scoring protocol v1

**Status:** specification fixed in this branch before this evaluator is run on any independent human-reference file. **Scope:** the saved RQ2 checker predictions and a separately finalized, adjudicated reference table. This document does not change the checker, its output, or the M4 study protocol.

## Cohort and split

The authorized calibration manifest in the source evaluation worktree was `../calibration_checker_v1/input_manifest.json`: three calibration cases (`case_e930c71c`, `case_d01ff326`, `case_58e84070`), one canonical source execution group (`libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`), five object predictions per case (15 assessment units). The manifest and non-synthetic reference inputs are not bundled with this technical evaluator. The saved human comparison/reference is for `cream_cheese_1` only; the other four objects have no reference labels. This is development calibration, not independent evaluation.

The two `trace_A`/`trace_B` entries in `R1_CASE_MANIFEST.csv` are controlled event-review traces and explicitly are not R1 reference labels; they are not substituted for the frozen calibration cohort. The 60 execution candidates in `CASE_SOURCE_INVENTORY.csv` are provisional metadata candidates with no independent reference labels and are not the human-review cohort. The independent confirmatory RQ2 cohort currently identifiable from these authorized records is zero. The three calibration references are coordinator-adjudicated and marked not independently verified; they remain descriptive development evidence.

Prediction rows must carry one of two explicit split labels: `development_calibration` or `independent_evaluation`. Each canonical source group must belong to exactly one split across the entire input. Calibration and independent evaluation are summarized separately; there is no threshold selection or calibration on independent evaluation. The unit for independence is the canonical source execution group, not an object row, case, intervention, or repeated run.

## Keys, eligibility, and join contract

Each prediction and reference row is keyed by `(case_id, object, source_group_id, requirement_version)`. The evaluator accepts normalized prediction CSV or the frozen checker JSON prediction array. For JSON that omits the source group, use the authorized case manifest and label its split explicitly. The evaluator rejects duplicate keys, conflicting group identity for a case/object/requirement, missing prediction/reference joins, split disagreement, unknown split values, and any non-finalized reference row. The reference table is an explicit CLI argument; the script performs no search, glob, or discovery of human-review files. The prediction file is checked against the SHA-256 recorded in the frozen output seal before scoring. A caller must provide a separate finalized adjudicated-reference CSV; reviewer submissions and incomplete forms are not accepted as references.

Rows marked `excluded` are retained in per-case output and exclusion counts/reasons, but excluded from performance denominators. `not_applicable` reference units contribute to applicability scoring only and are excluded from violation TP/FP/TN/FN. `unknown` applicability or `unscorable` violation references are retained but excluded from relevant accuracy denominators. For an applicable reference, a checker `not_applicable` result is an applicability disagreement and a non-binary violation result; it is never a true negative.

## Metrics

* **Applicability agreement/accuracy:** among included units with a determinate reference applicability (`applicable` or `not_applicable`) and a decided checker applicability prediction (the same two values), report exact agreement divided by the decided denominator. Also report applicability decision coverage as decided checker applicability predictions divided by determinate included applicability references. Abstentions and invalid contracts lower coverage and are not counted as correct or incorrect applicability decisions.
* **Violation confusion matrix:** among included, applicable references with a binary human violation label and a binary checker violation decision, `violation` is positive and `no_violation` is negative. Report TP, FP, TN, FN and their decided-pair denominator.
* **Precision:** `TP / (TP + FP)`. **Recall:** `TP / (TP + FN)`. **Specificity:** `TN / (TN + FP)`. Binary accuracy, when shown, is `(TP + TN) / (TP + FP + TN + FN)`. A zero denominator yields `null`/not estimable, never zero.
* **Violation decision coverage:** binary-scored applicable reference units divided by all included applicable references with a binary violation label. Abstentions, invalid contracts, and checker-not-applicable mismatches are separately counted and excluded from TP/FP/TN/FN; they are never recoded as negatives. Report abstentions by reference class so the missing decisions remain visible.
* **Exclusion and not-applicability:** report excluded units and reasons; determinate not-applicable references; unknown/unscorable references; and checker not-applicable decisions. Not-applicable units are not negatives for violation detection.

## Dependence and interpretation

Report object/case counts and distinct canonical source-group counts separately, plus per-source-group summaries. Do not treat object rows, interventions, repeated runs, or multiple cases from one execution as independent samples. With one or very few source groups, all estimates are descriptive; do not compute case-level confidence intervals, significance tests, or population claims. Group bootstrap or other uncertainty estimates require enough independent source groups and a separately approved analysis plan. State sparse numerators and denominators; suppress or mark metrics `not estimable` when a denominator is zero. No held-out accuracy is produced until finalized independent references exist and keys join exactly.

## Reproducible invocation

```sh
python3 evaluation/m4_20261127/rq2/final_evaluation_v1/score_rq2.py \
  --predictions /path/to/sealed_predictions.json \
  --prediction-sha256 EXPECTED_SHA256_FROM_OUTPUT_SEAL \
  --prediction-split development_calibration \
  --case-manifest /path/to/authorized_case_manifest.json \
  --finalized-references /path/to/finalized_adjudicated_references.csv \
  --output-dir /path/to/new_versioned_output
```

The command emits `per_case.csv` and `summary.json`. It never writes into the frozen prediction or reference paths.
