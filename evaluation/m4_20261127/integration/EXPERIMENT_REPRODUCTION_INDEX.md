# M4 experiment reproduction index

All paths are repository-relative. Root README contains setup and exact commands.

| Work | Saved artifacts | CPU reproduction | Scope and limitation |
|---|---|---|---|
| RQ1 historical retrieval | `evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_METRICS.md` and related frozen files | Read committed results; run available package tests | Historical exact/semantic/lexical multi-source results are 10/18, 10/18 and 8/18 for that reported subset, not all RQ1 work. Full replay needs external DB/catalogue, corpus/HDF5 and encoder. |
| RQ1 Phase 5K | `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/` | Saved artifacts and its CPU tests | V2 reports 24/24 multi-source completeness, 84/84 required family obligations and 80/80 critical abstentions in its defined cohort. Temporal false-complete cases KH2-C2-02, KH2-C2-10 and KH2-C2-18 remain. Full retrieval replay needs external sources and encoder. |
| RQ2 adjudicated calibration | `evaluation/m4_20261127/rq2/R1_RESULTS.csv`, `R1_METRICS.json`, `R1_EVIDENCE_NOTES.md` | `python integration/verify_saved_results.py` | Applicability 3/3; TP=1, TN=1, FP=0, FN=0 on 2 applicable cases; 1 NA excluded. One canonical source group; development-only. |
| RQ2 generalization coverage | `evaluation/m4_20261127/rq2/expanded_evaluation/` | Same saved-results verifier | 60 executions/300 object units: 120 applicable, 20 determinate, 100 abstentions; 20/120 coverage. Unlabeled coverage only, not accuracy. |
| RQ3 real Qwen run | `evaluation/m4_20261127/rq3/experiment/batch/`, `real_run_20261122T142300Z/RQ3_RESPONSES.jsonl`, metadata, `scored_pr34_20261123/` | Rerun scorer and compare three outputs as shown in README | 108 valid Qwen3-32B responses, 36 per condition; 9 failed attempts retained, not 9 failed logical requests. Development-only, two exposed parent groups; independent label review pending. C is checker-admission-status-only. |
| One-pass integration fixture | `integration/fixtures/one_pass_20261113/`, `integration/END_TO_END_QWEN_INTEGRATION_REPORT.md` | `python integration/verify_saved_fixture.py` | Real saved Qwen calls, `test_fixture=true`; model returned zero criticisms on one controlled guarantee. Original Drafter request/run and source recordings absent. |
| Drafter/Critic/adapter | `drafter/`, `critic/`, `integration/handoff.py` | Component tests and `integration.tests.test_handoff` | Structural interfaces are tested with scripted/synthetic cases; not model effectiveness. |
| RQ4 Revision Agent | `drafter/revision/` | Revision test suite and `python -m drafter.revision.tools.check_examples` | Saved no-change and scripted changes replay; no real Qwen revision plus second Critic run. |

## Interpretation rules

- Keep RQ1 historical, V1, V2 and Phase 5K cohorts separate. The historical 18-case multi-source subset is not the full RQ1 evaluation.
- RQ2's three calibration variants share one source execution; do not call them independent executions or pool other cohorts into their confusion matrix.
- RQ3 repeats and mutations do not increase independent parent groups.
- Full-case citation screening does not prove evidence was in a condition-specific model input.
- Scripted tests and synthetic fixtures verify interfaces, not new physical observations.
- Missing source databases, recordings, model weights and private human materials are not bundled or substituted by aggregate results.
