# RQ1 final development results and fault-injection addendum

**Status:** completed exposed development experiment; not an independent evaluation. The original retrieval runs and historical evaluator output are preserved. The corrected evaluator changes adjudication only; the fault-injection suite is a separate targeted run.

## Planner development and actual retrieval

The planner-only development comparison covered 216 exposed queries. The frozen planner omitted a requested family in 3/216 cases (one repeated temporal wording pattern); planner v2 retained all expected families in 216/216 plans. V2 planner outcomes were 165 complete, 9 ambiguous, and 42 unsupported/incomplete. This is a development check, not independent natural-language validation.

The actual planner-v2 retrieval for KH2-C2-02, KH2-C2-10, and KH2-C2-18 returned both `recorded_time` and `raw.robot0_joint_pos` as available, with one numeric joint-position sample per case. The corrected source-bound evaluator verified each temporal/frame binding. See `THREE_CASE_ACTUAL_RETRIEVALS.csv`; numeric values and source paths are intentionally omitted.

The full saved-response replay attempted 216 queries and completed without execution errors. Its original evaluator reported 96 reference-verified completions, 49 false-complete flags, 28 unique cases with error strings, 5 expected-family omissions, 205/210 family coverage, and 71 abstentions. These 49 flags are retained in `CASE_ASSESSMENTS.csv` as historical evaluator outputs; they are superseded interpretations, not 49 confirmed retrieval defects.

The separately versioned offline adjudication verified 133 complete retrievals, classified 71 abstentions as correct, and left 12 saved fault rows evaluation-unavailable because the normal replay did not inject their specified source faults. It confirmed zero false-complete retrievals, zero missing retrieved evidence, and zero incorrect numeric values. Of the 49 historical flags, 37 are source-verified as complete and 12 correspond to rows requiring fault injection. Independent source checks verified 150 numeric samples and 232 cited items across 52 source files. The 90 unique source artifacts bound by the frozen references were hash-verified in preflight.

## Targeted fault-injection verification

The 12 fault rows are KH2-C8-04–07, KH2-C8-12–15, and KH2-C8-20–23: three each for `missing_source`, `corrupt_source`, `symlink_source`, and `replace_source`. Frozen expected retrieval families are empty and the frozen contract requires abstention when source integrity cannot be established. The historic fixture builder was recovered and applied to temporary copies only: absent redirect target; copied bytes with a literal suffix; symlink to a copied file; and a copied file verified before atomic replacement.

Planner v2 resolved a plan for each request, then all 12 retrievals returned `UNAVAILABLE` with an integrity/proof rejection, no complete claim, and no execution error. All authoritative sources retained their frozen hashes before and after each case. The original v1 saved bundle records also show `UNAVAILABLE` and correct abstention for all 12; individual non-bundle ablations had varying rejection/no-match status. Detailed safe results and checksums are in `FAULT_INJECTION_CASES.csv` and `PUBLICATION_MANIFEST.json`.

No implementation defect was demonstrated. No algorithmic change was made. The fault run does not alter the normal 216-case assessment: those 12 saved normal-run rows remain evaluation-unavailable in that analysis, while the separate fault suite verifies the intended rejection behavior.

## Evaluator correction and aggregate accounting

The corrected evaluator distinguishes verified completion from unverified claims, verifies alternative sources only through explicit catalogue-bound family validators, compares family-specific metadata and frame-bound timestamps, and leaves unsupported reference schemas unverifiable. The 19 unbound-source, 6 recorded-time, 4 table-identity, and 3 missing-sample legacy diagnostics overlap across 28 unique rows. The five missing-family flags include correct abstentions for unsupported/unavailable obligations. Reference coverage remains insufficient for some families; this is not interpreted as a retrieval failure.

| Corrected normal replay assessment | Cases |
|---|---:|
| Verified complete | 133 |
| Correct abstention | 71 |
| Evaluation unavailable in saved run | 12 |
| Confirmed false-complete retrieval | 0 |

The targeted 12-case fault suite is supplemental and reported separately. Do not add its cases to or subtract them from the 216 normal attempts.

## Provenance and reproduction

`PUBLICATION_MANIFEST.json` binds safe publication files to the original replay manifests and aggregates, frozen reference/database/catalogue/encoder hashes, evaluator source, and fault-runner inputs. Restricted reference contents, raw evidence, numeric outputs, exact source paths, and credentials are not included in this publication bundle.

Run the targeted fixtures only in an authorized environment where the pinned inputs already exist. Set the variables to the verified local input paths and hashes; use a new empty output directory and a dedicated writable temporary directory:

```sh
python -m unittest \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_evaluate_replay_v3 \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_run_eval_v2 \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_requested_obligations_v2 \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_bundle_v2_contract -v

PYTHONPATH="$RQ1_CHECKOUT" python \
  evaluation/r1_v4/rag_evidence_database/retrieval_remediation/run_fault_injection_v2.py \
  --database "$RQ1_DATABASE" --database-sha256 "$RQ1_DATABASE_SHA256" \
  --catalogue "$RQ1_CATALOGUE" --catalogue-sha256 "$RQ1_CATALOGUE_SHA256" \
  --source-root "$RQ1_VERIFIED_SOURCE_ROOT" \
  --output "$RQ1_NEW_FAULT_OUTPUT" --temporary-root "$RQ1_DEDICATED_TEMP_DIR"
```

The 216-case normal replay is intentionally not rerun for this addendum. Original actual-retrieval outputs are separate from the offline evaluation and the supplemental fault report.

## Limitations

The 216 queries are an exposed development cohort with repeated templates, not independent evaluation. Planner v2 is a bounded reviewed-lexicon system. Retrieval completeness does not establish physical interpretation, safety, or admission eligibility; physical evidence eligibility remains `NOT_EVALUATED`. The fault tests cover only the four frozen source-integrity conditions and do not establish behavior for every operating-system or storage failure. Frozen reference family coverage remains incomplete.
