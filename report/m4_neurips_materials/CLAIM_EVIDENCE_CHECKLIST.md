# M4 manuscript claim-to-evidence checklist

Technical verification aid only. Every item requires author review before submission. No incomplete reviewer submissions were opened for this checklist.

## RQ1 — Retrieval and obligation coverage

- [ ] Historical retrieval metrics attributed only to the 96 eligible queries; identify the 18 execution contexts and avoid treating 486 case-mode instances as independent.
  - `evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_METRICS.md`
- [ ] Phase 5K V2 counts (24/24, 84/84, 80/80) remain separate from historical retrieval ranking metrics.
  - `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/RETRIEVAL_METRICS.md`
- [ ] Discuss false-complete cases KH2-C2-02, KH2-C2-10, KH2-C2-18 and missing `raw.robot0_joint_pos`; do not imply the development guard is a validated fix.
  - `evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/FALSE_COMPLETE_ANALYSIS.md`
- [ ] State retrieval/argument completeness does not demonstrate physical safety.

## RQ2 — Requirement Checker

- [ ] Current adjudicated calibration is 3 cases, 1 source group, applicability agreement 3/3; binary confusion matrix is based on 2 applicable cases (TP=1, FP=0, TN=1, FN=0), with one NA excluded.
  - `evaluation/m4_20261127/rq2/R1_METRICS.json`
  - `evaluation/m4_20261127/rq2/R1_RESULTS.csv`
- [ ] Sparse positive/negative denominators are explicit; metrics are descriptive; no human-review findings are claimed as independent until authorized evaluation is complete.
  - `evaluation/m4_20261127/rq2/R1_EVIDENCE_NOTES.md`
- [ ] Historical development reference remains distinct: 20 units, 7 applicable, 13 NA, 1 abstention, 6 determinate negatives, no positive labels; recall not estimable.
  - `evaluation/r1_v3/results.json`
  - `evaluation/m4_20261127/rq2/expanded_evaluation/SUMMARY_METRICS.json`
- [ ] 60-execution analysis is coverage-only: 300 units, 120 applicable, 180 NA, 20 decisions, 100 abstentions; it is not the human-review cohort and is not accuracy evidence.
  - `evaluation/m4_20261127/rq2/expanded_evaluation/SUMMARY_METRICS.json`
- [ ] Trace_A/trace_B event reviews are not treated as R1 reference labels.
  - `evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/FALSE_COMPLETE_ANALYSIS.md`

## RQ3 — Critic mutation experiment

- [ ] Primary quantitative evidence is the full 108-response Qwen3-32B run, not the one-pass report.
  - `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl`
  - `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_SUMMARY.csv`
  - `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_PER_CASE_RESULTS.csv`
  - `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_TABLES.md`
- [ ] State 12 semantic cases, 8 mutations, 4 clean controls, 3 conditions × 3 repeats, 2 development parent groups, and zero independent groups.
  - `evaluation/m4_20261127/rq3/MUTATION_PROTOCOL.md`
  - `evaluation/m4_20261127/rq3/EXPERIMENT_CONFIG.md`
- [ ] Report T/R/C detections, false positives, and correctness with the exact denominators in `tables.tex`; do not make inferential claims from repeated paired observations.
- [ ] C is admission-status-only; it does not contain independently verified physical checker judgments.
  - `evaluation/m4_20261127/rq3/EXPERIMENT_CONFIG.md`
- [ ] Mark independent mutation-label review **PENDING**.
  - `evaluation/m4_20261127/rq3/GOLD_LABELS_AND_REVIEW.md`
- [ ] One-pass fixture is supplementary integration evidence; identify the controlled guarantee miss and do not represent this as RQ3 primary quantitative evidence.
  - `integration/END_TO_END_QWEN_INTEGRATION_REPORT.md`

## RQ4 — Revision and integration

- [ ] Separate scripted software demonstrations from real-model behavior; no real-model revision followed by a second real Critic cycle has been demonstrated.
  - `drafter/revision/README.md`
  - `drafter/revision/examples/two_round_cycle/cycle.json`
  - `evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md`
- [ ] One-pass integration claims are limited to the saved real Qwen calls and their observed outputs.
  - `integration/END_TO_END_QWEN_INTEGRATION_REPORT.md`

## Cross-cutting checks

- [ ] Source-group dependence, sparse denominators, applicability, not-applicable units, and abstention handling are explicit.
- [ ] Structural/schema/argument validity is not equated with truth or demonstrated physical safety.
- [ ] Human-review fields are marked pending where applicable; incomplete reviewer submissions are not consulted.
- [ ] No new citations are added without author verification; no references are inferred from repository mentions alone.
- [ ] All three author contribution statements and the full AI-use disclosure are supplied and approved by the authors.
- [ ] The official NeurIPS 2026 style file is present and the compiled main content is within the nine-page handoff limit.
