# Milestone 4 results and claim boundaries

This document reconciles the final M4 result artifacts with the approved protocol. Exact row-level outputs and validation procedures remain in the linked result directories. The companion [experiment registry](EXPERIMENT_REGISTRY.md) records designs, denominators, source commits and fuller reproduction details.

## RQ1 — evidence retrieval

The historical C4 multi-source subset contained 18 of 162 questions. Completeness was 10/18 exact, 10/18 semantic and 8/18 lexical. The separate planner-development comparison covered 216 exposed queries: the frozen planner omitted a requested family in three repeated temporal cases; planner v2 retained all expected families in 216/216 plans (165 complete, 9 ambiguous, 42 unsupported/incomplete). These planner results are distinct from actual retrieval.

The planner-v2 actual-retrieval replay attempted 216 queries. The original evaluator reported 96 reference-verified completions and 49 false-complete flags, among other reference-coverage flags. A separately versioned offline adjudication verified 133 complete retrievals, 71 correct abstentions, and left 12 saved rows evaluation-unavailable because the normal replay did not inject their frozen source faults. It confirmed zero false-complete retrievals, zero missing retrieved evidence, and zero incorrect numeric values; 150 numeric samples and 232 cited items were source-verified. Preserve the original 49 flags as historical evaluator outputs, superseded interpretations rather than confirmed retrieval failures. The three temporal cases (`KH2-C2-02`, `KH2-C2-10`, `KH2-C2-18`) returned both requested families and passed the corrected frame/source audit.

A separate CPU fault-injection run faithfully reproduced all 12 frozen C8 source-integrity conditions (three each: missing, corrupt, symlinked, replaced). Each was rejected as unavailable with correct abstention; no execution errors occurred and authoritative sources remained unchanged. This supplemental run does not change the 216 normal-run denominator. All RQ1 data are exposed development results, not independent evaluation; full retrieval reproduction still requires external source data, retrieval infrastructure and the pinned encoder.

Authoritative reports: [RQ1 failure analysis](rq1/RQ1_MULTI_SOURCE_FAILURE_ANALYSIS.md), historical case and missing-obligation tables in `rq1/`, and Phase 5K V2 artifacts under `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/`.

## RQ2 — R1 checker

The recovered, user-confirmed final adjudicated reference covers three controlled variants from one canonical source group. Applicability agreement was 3/3. Two applicable rows yielded TP=1, TN=1, FP=0 and FN=0, with 2/2 outcome agreement and 2/2 binary decision coverage; the third was not applicable and excluded from binary metrics. These are retrospective, post-hoc development results, not independent physical validation or a checker-accuracy claim. Preserve the earlier event-review forms as distinct records: both reviewers marked support loss, downward motion, and floor contact observed for the matched sham, although the supplied timeline records continued table contact, approximately zero vertical velocity, and no floor contact. The later final adjudication for `case_d01ff326` is “no R1 violation observed within recorded coverage”; it is retained verbatim, but frame-10 reaction forces were not independently checked and the physical discrepancy remains unresolved. The checker run itself records `human_reference_loaded=false` and `empirical_admission_enabled=false`, so no admission follows from agreement.

The separate expanded coverage audit included 60 same-scene executions / 300 object units: 120 applicable, 20 determinate, and 100 abstentions. Decision coverage was 20/120 (16.7%); abstention was 100/120 (83.3%). Cross-scene mapping gates rejected 38 executions; cross-task scored decisions were 0/100. These are coverage and abstention results, not labeled accuracy. Physical checker admission remains blocked.

Reproduce saved public counts with `python3 integration/verify_saved_results.py`. See `rq2/R1_EVIDENCE_NOTES.md` and `rq2/expanded_evaluation/METHODS_AND_LIMITATIONS.md`.

## RQ3 — Critic pilot

The paired pilot used 12 semantic cases (8 mutations and 4 controls) from 2 parent groups, with 3 repetitions per condition. All 108 responses were valid (36 each for T/R/C). For the eight mutations, detections were T 8/24, R 9/24, C 10/24; rules plus model yielded 10/24, 10/24 and 11/24. On clean controls, false positives were T 0/12, R 1/12 and C 3/12. Reference-correct model outputs were T 20/36, R 20/36 and C 19/36.

This is development-only: there are zero independent cases, the labels were developer-authored and independent review remains pending. Condition C indicates checker-admission status; it does not test admitted physical evidence. Repeats and mutations are paired, not independent samples. Reproduce scoring from archived responses using the commands in the [root README](../../README.md#rq3-saved-qwen-responses-and-scores).

## RQ4 — Revision pilot

The bounded pilot used three planted unsupported-guarantee defects across two source groups and one defect type, with zero independent evaluation cases. There were 9/9 valid genuine Qwen responses, 27/27 valid second-Critic responses and all 12 revisions were applied. Qwen had 9/9 correct repairs; the deterministic template had 2/3. Defect fixed: 9/9 vs 3/3; revised claim supported by evidence: 9/9 vs 2/3; new problem introduced: 0/9 vs 1/3; scope preserved: 9/9 vs 2/3; invalid, abstained or missing: 0/9 vs 0/3. Second-Critic reviews found new objections in 2/9 per method and reflagged the target in 0/9 per method.

Human outcomes were coordinator-confirmed from a single consensus form; independent agreement was not recalculated and Cohen’s kappa is unavailable. These results describe repeated outputs on a small fixed pilot, not general or comparative Revision Agent effectiveness. The broader RQ4 effectiveness study remains NO-GO. Public aggregate validation:

```sh
python3 evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py
sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt
```

See [finalization report](rq4/finalized_results/RQ4_FINALIZATION_REPORT.md), [manuscript tables](rq4/finalized_results/RQ4_MANUSCRIPT_TABLES.md), and [public audit](rq4/finalized_results/RQ4_PUBLICATION_AUDIT.md). Full private scorer replay requires confidential sealed review inputs and mappings, which are not included.

## Genuine R1 v3 Drafter generation

One genuine request was generated from the frozen LIBERO Long/OpenVLA-OFT execution using Qwen3-32B BF16 at revision `9216db5781bf21249d130ec9da846c4624c16137`, vLLM 0.31.0, Outlines and tensor parallel size 2. It returned HTTP 200 in 112.87 seconds, without retry. Five object graphs were generated for `cream_cheese_1`, `ketchup_1`, `orange_juice_1`, `milk_1` and `butter_1`; all five outcomes are `insufficient_information`.

The argument passed full host validation. The request had 135 context-only evidence records, zero graph-eligible records, no admitted checker assessment, no human reference labels and 15 explicit evidence gaps. `safety_claim_verified` is false. Supplementary human reasoning review is pending. The generated file is a Drafter-accepted draft, not an independently approved or physically verified safety case.

Artifact and source details: [Task 8A handoff](integration/task8a_r1v3/ALEX_HANDOFF_README.md), source generation commit `bf62fe8338d40807c6ff7e6a5b331df557aaf632`, and [current integration status](integration/CURRENT_INTEGRATION_STATUS.md).

## Verification and reproducibility levels

The RQ1/RQ2/RQ3/RQ4 public saved-result commands are CPU-only and do not repeat inference or human review. Task 8A request rebuild, argument validation, saved-run CPU resumption through the deterministic Critic, RQ4 public validation and checksum checks are also CPU-only with Python 3.12 and the documented requirements. GPU inference requires the exact model/tokenizer and serving stack, plus resource admission; raw retrieval/source-data replay requires external simulation recordings and retrieval data. Passing deterministic validators confirms checked schemas, bindings, counts or hashes only; it does not establish physical truth.

No M4 result establishes that the complete fresh-execution retrieval → checker → Drafter → Critic → Revision → second-Critic chain has been accepted. The saved Task 8A draft has been resumed through the accepted R1 v3 handoff and deterministic CPU Critic. R1 v3 Critic model inference and the R1 v3 Critic-to-Revision contract remain unimplemented; human reasoning review, downstream Revision, and second-Critic stages have not run.
