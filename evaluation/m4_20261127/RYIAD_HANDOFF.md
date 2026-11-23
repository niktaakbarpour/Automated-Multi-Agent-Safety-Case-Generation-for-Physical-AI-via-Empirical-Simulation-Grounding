# Ryiad's Milestone 4 offline handoff

This handoff is designed to work from a fresh clone with Python 3.12 and ordinary CPU access. It does not require GPU inference, simulation, external data mounts, or access to another machine. Start in the repository root and follow the sections below.

## 1. RQ1 query/reference authoring

Package:
- evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/README.md
- evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/AUTHORING_GUIDE.md
- evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/BLANK_QUERY_REFERENCE_FORM.csv
- evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/AUTHORING_FORM_SCHEMA.json

The package contains 30 verified canonical source executions, four task IDs, four variants, 6,870 evidence-record envelopes, 148,225 source-value samples, and 60 blank question/reference slots. It contains actual timestamps, object-pose, robot-state, contact-group and native-geometry values for the selectors in the index. Image pixels are excluded. Do not infer physical events or generate missing values.

Run the offline integrity check:

    python3 evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/verify_offline_handoff.py

This verifier uses only the Python standard library. The one-time extractor is included for provenance but is not needed for the local authoring workflow.

Deliverable: complete the assigned slots in BLANK_QUERY_REFERENCE_FORM.csv with original questions, atomic obligations, exact object/source/family/field/time scope, evidence IDs and selectors, coverage/missingness, expected-abstention rationale, and independent source-check status. Preserve blank or pending values whenever the bundled records do not support verification. Do not run a retrieval score before the reference set is independently checked and frozen.

Known limits: the extract is raw recorded data, not physical truth. Empty serialized contact groups are not no-contact judgments; simulator contact count is not object-specific contact proof. Sparse frames are not continuous coverage. No images or video are included, so visual checks are unavailable. Physical fall/support and safety labels are not provided.

## 2. RQ1 historical completeness and false-complete analysis

Read the historical and Phase 5K sources:

- evaluation/r1_v4/rag_evidence_database/retrieval_remediation/HISTORICAL_5J_COMPARISON.md
- evaluation/r1_v4/rag_evidence_database/retrieval_remediation/MULTISOURCE_COMPLETENESS.md
- evaluation/r1_v4/rag_evidence_database/retrieval_remediation/ABLATION_RESULTS.md
- evaluation/r1_v4/rag_evidence_database/retrieval_remediation/REMAINING_LIMITATIONS.md
- evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/PER_CASE_FAILURE_ANALYSIS.csv
- evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/FALSE_COMPLETE_ANALYSIS.md

Keep the historical 18-case multi-source results distinct from Phase 5K's 24-execution/18-variant assessment. The three temporal-plan false-complete examples are development failures, not new held-out cases. Analyze source gaps versus query/contract obligation loss from the records; do not claim the old 18 cases were the complete RQ1 evaluation.

Deliverable: a source-linked failure analysis that explains each missing obligation, its retrieval-plan status, and whether the evidence source existed. Do not create new labels or metrics.

## 3. RQ2 task/role transfer investigation

Start with:

- evaluation/m4_20261127/rq2/RYIAD_TASK_ROLE_TRANSFER_HANDOFF.md
- evaluation/m4_20261127/rq2/expanded_evaluation/CHECKER_CASE_RESULTS.csv
- evaluation/m4_20261127/rq2/expanded_evaluation/SOURCE_ELIGIBILITY_INVENTORY.csv
- evaluation/m4_20261127/rq2/expanded_evaluation/EXCLUSIONS.csv
- evaluation/m4_20261127/rq2/expanded_evaluation/SUMMARY_METRICS.json
- evaluation/m4_20261127/rq2/expanded_evaluation/METHODS_AND_LIMITATIONS.md
- evaluation/m4_20261127/rq2/R1_CASE_MANIFEST.csv
- evaluation/m4_20261127/rq2/R1_EVIDENCE_NOTES.md

The frozen changed-task same-scene partition has 0/100 decision coverage and 100/100 abstentions among applicable object units; the 10-execution same-task reserved partition has 20/20 coverage. These are coverage results, not accuracy. Use exact frozen partition names. Do not relabel mapping-gate exclusions as abstentions, infer violations from task outcome, or treat object rows from one execution as independent executions.

Deliverable: a bounded analysis of the changed-task coverage failure using per-case provenance, eligibility, and abstention reasons, with exclusions separate. The 38 cross-scene mapping-gate exclusions were not evaluated. A separate task-role-specific dataset was not found; state that limitation rather than inventing cases.

## 4. RQ3 independent mutation-label audit

Neutral materials:

- evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/REVIEW_INSTRUCTIONS.md
- evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/NEUTRAL_CASE_MANIFEST.csv
- evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/REVIEW_FORM.csv
- evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/cases/

CPU implementation and benchmark:

- evaluation/m4_20261127/rq3/mutations/build_mutations.py
- evaluation/m4_20261127/rq3/mutations/cases/
- evaluation/m4_20261127/rq3/experiment/score.py
- evaluation/m4_20261127/rq3/MUTATION_PROTOCOL.md
- evaluation/m4_20261127/rq3/tests/test_mutations.py

Run the CPU mutation validation test:

    python3 -m unittest discover -s evaluation/m4_20261127/rq3/tests -p test_mutations.py

Inspect the scorer interface without scoring: PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/score.py --help. The implementation accepts the frozen batch, response JSONL, and a separate output directory. Only after the independent form is frozen and unblinding is authorized, run it with PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/score.py --batch evaluation/m4_20261127/rq3/experiment/batch --responses evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl --out-dir evaluation/m4_20261127/rq3/experiment/ryiad_review_scoring. Keep these local outputs uncommitted unless specifically approved.\n\nComplete and freeze the neutral review form before accessing answer-key or saved-score files. Record prior exposure in the form. Do not use model responses to decide whether a mutation label is correct, and do not alter a judgment to match a key. The neutral folder contains no expected labels, mutation-type labels, human judgments, or Qwen results.

Blinding limitation: the main repository already contains answer-key-bearing benchmark files and scored results outside the neutral folder, and the repository does not provide folder-level access control. If you have opened or previously seen any such material, declare exposure; do not claim this audit was blinded or independent. For strict technical blinding, a coordinator must provide a separately access-controlled review-only copy before review. Do not run the scorer until the independent review is frozen.

RQ3 context: the existing real-model run is development-only, contains two parent groups, and condition C represents checker-admission status only. The audit does not create an unseen-parent claim or independent mutation labels.

## Prerequisites and expected deliverables

Prerequisites: a fresh clone of this repository, Python 3.12, and CPU. The RQ1 verifier uses only the standard library. The RQ3 mutation tests use the checked-in project test setup; no inference is required.

Return:
1. the completed RQ1 CSV, with unsupported slots left pending and source/evidence references preserved;
2. a source-linked RQ1 historical/Phase 5K failure analysis;
3. a bounded RQ2 transfer analysis with exact per-case records and limitations;
4. a completed, signed RQ3 neutral review form with exposure declaration, frozen before unblinding.

Do not add AI-generated questions, gold labels, reviewer decisions, or paper prose. Keep scientific decisions and human judgments authored by their designated people.
