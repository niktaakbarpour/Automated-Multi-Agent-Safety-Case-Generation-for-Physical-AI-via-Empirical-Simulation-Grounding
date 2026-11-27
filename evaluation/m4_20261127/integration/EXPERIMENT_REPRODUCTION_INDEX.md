# M4 experiment reproduction index

All paths are repository-relative. Root README contains the Python 3.12 CPU setup. This index was reconciled after the final RQ4 pilot and genuine Task 8A run; older feasibility reports are preserved as dated snapshots. See [`MILESTONE4_RESULTS.md`](../MILESTONE4_RESULTS.md), [`EXPERIMENT_REGISTRY.md`](../EXPERIMENT_REGISTRY.md), and [`CURRENT_INTEGRATION_STATUS.md`](CURRENT_INTEGRATION_STATUS.md) for current interpretation.

**Current state:** RQ1–RQ4 saved analyses and one genuine Task 8A Drafter request are complete at their stated experimental scope. RQ2 physical checker admission remains blocked; RQ3 is development-only with independent review pending; broader RQ4 effectiveness remains NO-GO. Task 8A reasoning review is pending, its Drafter-to-Critic adapter is rejected by the current contract, and end-to-end safety-case acceptance has not been demonstrated.

| Work | Saved artifacts | CPU reproduction | Scope and limitation |
|---|---|---|---|
| RQ1 historical retrieval | `evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_METRICS.md` and related frozen files | Read committed results; run available package tests | Historical exact/semantic/lexical multi-source results are 10/18, 10/18 and 8/18 for that reported subset, not all RQ1 work. Full replay needs external DB/catalogue, corpus/HDF5 and encoder. |
| RQ1 Phase 5K | `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/` | Saved artifacts and its CPU tests | V2 reports 24/24 multi-source completeness, 84/84 required family obligations and 80/80 critical abstentions in its defined cohort. Temporal false-complete cases KH2-C2-02, KH2-C2-10 and KH2-C2-18 remain. Full retrieval replay needs external sources and encoder. |
| RQ2 adjudicated calibration | `evaluation/m4_20261127/rq2/R1_RESULTS.csv`, `R1_METRICS.json`, `R1_EVIDENCE_NOTES.md` | `python integration/verify_saved_results.py` | Applicability 3/3; TP=1, TN=1, FP=0, FN=0 on 2 applicable cases; 1 NA excluded. One canonical source group; development-only. |
| RQ2 generalization coverage | `evaluation/m4_20261127/rq2/expanded_evaluation/` | Same saved-results verifier | 60 executions/300 object units: 120 applicable, 20 determinate, 100 abstentions; 20/120 coverage. Unlabeled coverage only, not accuracy. |
| RQ3 real Qwen run | `evaluation/m4_20261127/rq3/experiment/batch/`, `real_run_20261122T142300Z/RQ3_RESPONSES.jsonl`, metadata, `scored_pr34_20261123/` | Rerun scorer and compare three outputs as shown in README | 108 valid Qwen3-32B responses, 36 per condition; 9 failed attempts retained, not 9 failed logical requests. Development-only, two exposed parent groups; independent label review pending. C is checker-admission-status-only. |
| Genuine R1 v3 Task 8A Drafter | `evaluation/m4_20261127/integration/task8a_r1v3/`; original request and source package in parent `integration/` directory | `python3 -m evaluation.m4_20261127.integration.build_r1v3_request --check`; `python3 evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py`; adapter reproduction instructions in `task8a_r1v3/ALEX_HANDOFF_README.md` | One genuine Qwen3-32B BF16 request; HTTP 200, 112.87 s, five graphs; all outcomes `insufficient_information`. Full host validation passed. 135 context-only records, zero graph-eligible, no admitted checker, `safety_claim_verified:false`. Human reasoning review required. Adapter rejection remains for Alex; not safety-case approval. |
| One-pass integration fixture | `integration/fixtures/one_pass_20261113/`, `integration/END_TO_END_QWEN_INTEGRATION_REPORT.md` | `python integration/verify_saved_fixture.py` | Real saved Qwen calls, `test_fixture=true`; model returned zero criticisms on one controlled guarantee. Original Drafter request/run and source recordings absent. |
| Drafter/Critic/adapter | `drafter/`, `critic/`, `integration/handoff.py` | Component tests and `integration.tests.test_handoff` | Structural interfaces are tested with scripted/synthetic cases; not model effectiveness. |
| RQ4 Revision pilot | `evaluation/m4_20261127/rq4/finalized_results/` | `python3 evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py`; `sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt` | Genuine Qwen pilot: 9/9 valid responses, 9/9 correct repairs; deterministic template 2/3. Three planted defects, two source groups, zero independent cases; one coordinator-confirmed consensus form, kappa unavailable. Broader study NO-GO; not general effectiveness. |

## Interpretation rules

- Keep RQ1 historical, V1, V2 and Phase 5K cohorts separate. The historical 18-case multi-source subset is not the full RQ1 evaluation.
- RQ2's three calibration variants share one source execution; do not call them independent executions or pool other cohorts into their confusion matrix.
- RQ3 repeats and mutations do not increase independent parent groups.
- RQ4 repeats do not increase independent defect cases; its human outcome summary is based on one consensus form.
- Genuine Drafter inference, deterministic host validation, supplementary reasoning review, adapter compatibility and end-to-end acceptance are separate stages.
- Full-case citation screening does not prove evidence was in a condition-specific model input.
- Scripted tests and synthetic fixtures verify interfaces, not new physical observations.
- Missing source databases, recordings, model weights and private human materials are not bundled or substituted by aggregate results.
