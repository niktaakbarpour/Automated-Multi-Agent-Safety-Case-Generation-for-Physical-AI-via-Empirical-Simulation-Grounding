# M4 result-admission checklist

Use this checklist for every numeric claim, table cell and sentence in the final submission. “Present on disk” is not equivalent to verified, frozen, independent or admitted. This checklist does not authorize new experiments or inspection of private review material.

## General admission gates

- [ ] Record exact repository commit and artifact path for each number; preserve the raw frozen source artifact.
- [ ] Name the cohort, unit of analysis, eligibility filter, denominator and source-group count separately. Do not pool across phases, source groups, checker calibrations, task splits, conditions or review states.
- [ ] Identify repeated questions, objects, variants, mutations and stochastic model repeats. They are paired/repeated observations unless the protocol establishes a new independent source group.
- [ ] Distinguish exclusion/mapping failure, not-applicable (N/A), unknown/uncertain, abstention and determinate output. An abstention is never a correct negative or TN. N/A is excluded from binary violation metrics.
- [ ] Compute binary metrics only on the stated applicable, determinate, reference-labeled denominator. If positive or negative references are absent/sparse, mark precision/recall/specificity/F1 as not estimable where appropriate; never smooth or fabricate a denominator.
- [ ] Keep applicability agreement/accuracy separate from violation classification. Report decision coverage and abstention separately from conditional accuracy.
- [ ] Source/argument identity, retrieval completeness and schema validation do not establish load-bearing support, physical outcomes or physical safety.
- [ ] Label all development, exposed, synthetic, coverage-only and pending outputs. No test fixture, AI reviewer or model output may be described as a human ground truth.
- [ ] Verify pending reviewer exposure and final-reference freeze before comparison. Preserve original reviewer submissions and keep private material out of public commits.

## RQ1 — retrieval and obligation coverage

- [ ] **Historical ranking:** cite `evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_METRICS.md`; report `n=96` only for ranking-eligible IR metrics and identify 18 execution contexts/clustered source scopes. Do not count the 486 case-mode results as independent samples.
- [ ] **Historical C4 completeness:** cite `evaluation/m4_20261127/rq1/RQ1_MULTI_SOURCE_FAILURE_ANALYSIS.md`; the 18 unique C4 questions have exact 10/18, semantic 10/18 and lexical 8/18 completeness. Distinguish the eight common incomplete cases from the two additional lexical-only failures.
- [ ] **Phase 5K V2:** cite the V2 freeze/metrics and merged false-complete analysis. Report the 216-question, 24-execution, 18-variant and 72-template cohort; describe nominal C4 24/24 as eight templates repeated over three scopes; show 84/84 required-family obligations and 80/80 critical abstentions with their definitions.
- [ ] Name `KH2-C2-02`, `KH2-C2-10`, and `KH2-C2-18` as three C2 temporal query-to-plan false-completes. They omit joint-position obligations while reporting COMPLETE; do not relabel them C4 or claim the general defect is fixed.
- [ ] **30-execution expansion:** current committed authoring package has 30 selected executions and 60 blank slots, with zero independently authored query/reference pairs. Do not report retrieval performance for it. Require independent verification and authorized reference freeze first.
- [ ] Do not claim retrieval completeness equals physical safety or full evidence sufficiency.

## RQ2 — Requirement Checker

- [ ] Keep these cohorts distinct: historical development reference (20 object units/4 executions), N3 adjudicated calibration (3 cases/1 canonical group), 60-execution coverage analysis (300 object units), and the ongoing 44-case independent human evaluation.
- [ ] For the N3 three-case calibration report applicability 3/3, 2 applicable/1 N/A, TP=1/FP=0/TN=1/FN=0 over two applicable outcomes, and one source group. These sparse descriptive results are calibration, not independent accuracy or checker admission.
- [ ] For the 20-unit development reference report 7 applicable/13 N/A, six determinate outcomes (TN=6), one abstention, and zero positive references. Recall/F1 are not estimable; precision is undefined with zero positive predictions.
- [ ] For the 60-run cohort report 300 units, 120 applicable, 180 N/A, 20 determinate, 100 abstentions and 20/120 applicable decision coverage. Do not assign truth labels or accuracy metrics.
- [ ] In the changed-task same-scene stratum, report 50 executions/250 object units, 100 applicable, 150 N/A, zero determinate and 100 abstentions. The 0/100 denominator counts applicable object units, not 100 executions. Keep the 38 cross-scene mapping-gate rejections separate.
- [ ] Treat all 44-case human results as **PENDING** until both required independent review records, exposure declarations, verified intervals, discrepancy resolution and authorized final-reference freeze are complete. Do not inspect unfinished submissions for this audit.
- [ ] Treat the separate AI-review experiment as ongoing/pending. AI judgments are not a third human annotation or inter-rater score; do not use private outputs unless separately authorized and finalized.
- [ ] Preserve applicability, N/A, uncertainty, exclusions and checker abstentions as different states. Never turn abstentions into TNs.

## RQ3 — Critic mutation experiment

- [ ] Primary quantitative evidence is the saved **108-response Qwen3-32B run**, with 36 outputs per T/R/C condition; do not substitute the one-pass fixture.
- [ ] State the cohort: 12 semantic cases (8 mutations/4 clean controls), two development parent groups, zero independent source groups and three paired repeats. Repeats are not additional independent N.
- [ ] Report T/R/C denominators exactly: mutation detection out of 24 outputs (8 mutations × 3 repeats), clean-control false positives out of 12 (4 controls × 3), and reference-correct outputs out of 36 per condition. Label model-only vs rules+model; rule-only is deterministic and has one result per case.
- [ ] State that mutation labels are developer-authored and independent review is pending. Do not claim independently validated accuracy until review decisions are finalized/frozen and any disagreements are documented.
- [ ] Condition C contains checker-admission-status information only. It is not a checker verdict, independently verified physical evidence, safety oracle or basis for a checked-evidence advantage claim.
- [ ] Evidence-link correctness applies to checked citations under the scorer’s full-case scope and does not prove cited evidence was present in condition-specific model input.

## RQ4 — Revision Agent

- [ ] Report the 102 CPU tests and 149 saved-example checks as software/contract evidence, and label scripted/synthetic changes accordingly.
- [ ] State the current NO-GO: zero eligible real revision cases with authentic actionable Critic findings; zero independent source groups. The real one-pass Qwen report has no actionable finding.
- [ ] Do not claim Qwen-generated revision effectiveness, a second real Critic cycle or independent correctness. No such empirical revision run exists.
- [ ] If describing one-pass Qwen integration, state it is supplementary, development-exposed, and its controlled guarantee received zero Qwen criticisms; it is not a revision trial.

## Final author sign-off

- [ ] Every published quantity matches the cited saved artifact and its denominator.
- [ ] Every source-group and exposure statement is verified; “execution count” is not silently substituted for independent source-group count.
- [ ] The 44-case RQ2 review, AI review and RQ3 independent label audit are visibly pending unless formally finalized and admitted.
- [ ] All authors approve the limitations, table captions, citations, final submission checklist, author contributions and AI-use disclosure.
- [ ] No sentence claims that this framework certifies physical safety or that empirical simulation alone establishes real-world safety.
