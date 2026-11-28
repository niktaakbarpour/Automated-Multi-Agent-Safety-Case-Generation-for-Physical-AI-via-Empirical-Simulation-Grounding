# M4 experiment reproduction index

All paths are repository-relative. Run the commands below from the repository root. This index was reconciled after the final RQ4 pilot and genuine Task 8A run; older feasibility reports are preserved as dated snapshots. See [`MILESTONE4_RESULTS.md`](../MILESTONE4_RESULTS.md), [`EXPERIMENT_REGISTRY.md`](../EXPERIMENT_REGISTRY.md), and [`CURRENT_INTEGRATION_STATUS.md`](CURRENT_INTEGRATION_STATUS.md) for current interpretation.

**Current state:** RQ1–RQ4 saved analyses and one genuine Task 8A Drafter request are complete at their stated experimental scope. RQ2 physical checker admission remains blocked; RQ3 is development-only with independent review pending; broader RQ4 effectiveness remains NO-GO. Task 8A supplementary reasoning review materials are published and the review is pending, its R1 v3 Drafter-to-Critic handoff is accepted and the saved draft has been resumed through the deterministic CPU Critic. Model-backed R1 v3 Critic inference, a compatible Critic-to-Revision contract, Revision and second-Critic stages remain unimplemented or unrun; end-to-end safety-case acceptance has not been demonstrated.

| Work | Saved artifacts | CPU reproduction | Scope and limitation |
|---|---|---|---|
| RQ1 historical retrieval | `evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_METRICS.md` and related frozen files | Read committed results; run available package tests | Historical exact/semantic/lexical multi-source results are 10/18, 10/18 and 8/18 for that reported subset, not all RQ1 work. Full replay needs external DB/catalogue, corpus/HDF5 and encoder. |
| RQ1 Phase 5K | `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/` and `publication_v1/` | `python evaluation/r1_v4/rag_evidence_database/retrieval_remediation/publication_v1/validate_publication.py` | Planner v2 actual replay: 216 attempts, 133 verified complete, 71 correct abstentions, 12 evaluation-unavailable in the normal run; zero confirmed false-complete retrievals. Original 49 flags are superseded evaluator interpretations. The three temporal cases passed corrected verification. Full fresh replay needs external sources and encoder. |
| RQ2 adjudicated calibration | `evaluation/m4_20261127/rq2/R1_RESULTS.csv`, `R1_METRICS.json`, `R1_EVIDENCE_NOTES.md` | `python integration/verify_saved_results.py` | Applicability 3/3; TP=1, TN=1, FP=0, FN=0 on 2 applicable cases; 1 NA excluded. One canonical source group; development-only. |
| RQ2 generalization coverage | `evaluation/m4_20261127/rq2/expanded_evaluation/` | Same saved-results verifier | 60 executions/300 object units: 120 applicable, 20 determinate, 100 abstentions; 20/120 coverage. Unlabeled coverage only, not accuracy. |
| RQ2 Task 7C retrospective | [Report and tables](../rq2/task7c_retrospective/REPORT.md) | `sha256sum -c evaluation/m4_20261127/rq2/task7c_retrospective/SHA256SUMS.txt` | 18 of 20 scored against the approved Task 8D reference. Public checksums cover derived artifacts. The source join requires restricted inputs. |
| RQ3 real Qwen run | `evaluation/m4_20261127/rq3/experiment/batch/`, `real_run_20261122T142300Z/RQ3_RESPONSES.jsonl`, metadata, `scored_pr34_20261123/` | See the saved Qwen response commands below | 108 valid Qwen3-32B responses, 36 per condition; 9 failed attempts retained, not 9 failed logical requests. Development-only, two exposed parent groups; independent label review pending. C is checker-admission-status-only. |
| Genuine R1 v3 Task 8A Drafter | `evaluation/m4_20261127/integration/task8a_r1v3/`; original request and source package in parent `integration/` directory | Request check, argument validation, `python -m integration.orchestrator resume-task8a --out-dir <new-output-dir>` | One genuine Qwen3-32B BF16 request; HTTP 200, 112.87 s, five graphs; all outcomes `insufficient_information`. Accepted handoff and saved deterministic CPU Critic resume. 135 context-only records, zero graph-eligible, no admitted checker, `safety_claim_verified:false`. Human reasoning review required; not safety-case approval. |
| One-pass integration fixture | `integration/fixtures/one_pass_20261113/`, `integration/END_TO_END_QWEN_INTEGRATION_REPORT.md` | `python integration/verify_saved_fixture.py` | Real saved Qwen calls, `test_fixture=true`; model returned zero criticisms on one controlled guarantee. Original Drafter request/run and source recordings absent. |
| Drafter/Critic/adapter | `drafter/`, `critic/`, `integration/handoff.py` | Component tests and `integration.tests.test_handoff` | Structural interfaces are tested with scripted/synthetic cases; not model effectiveness. |
| RQ4 Revision pilot | `evaluation/m4_20261127/rq4/finalized_results/` | `python3 evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py`; `sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt` | Genuine Qwen pilot: 9/9 valid responses, 9/9 correct repairs; deterministic template 2/3. Three planted defects, two source groups, zero independent cases; one coordinator-confirmed consensus form, kappa unavailable. Broader study NO-GO; not general effectiveness. |

## CPU manuscript table replay

From the root of a fresh clone, use Python 3.12. The install needs package-index access. The replay uses only repository files and temporary output.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-m4-cpu.lock
python -m pip check
python integration/replay_m4_tables.py
```

The replay checks saved manuscript table values.

### RQ3 saved Qwen responses and scores

The real response archive is at `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl`; the frozen request batch is under `evaluation/m4_20261127/rq3/experiment/batch/`. Use a new temporary output directory:

```sh
OUT="$(mktemp -d)"
env PYTHONPATH=. python evaluation/m4_20261127/rq3/experiment/score.py \
  --batch evaluation/m4_20261127/rq3/experiment/batch \
  --responses evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl \
  --out-dir "$OUT"
python evaluation/m4_20261127/rq3/experiment/make_tables.py \
  --results-dir "$OUT" --out "$OUT/RQ3_TABLES.md"
diff -u evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_PER_CASE_RESULTS.csv "$OUT/RQ3_PER_CASE_RESULTS.csv"
diff -u evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_SUMMARY.csv "$OUT/RQ3_SUMMARY.csv"
diff -u evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/scored_pr34_20261123/RQ3_TABLES.md "$OUT/RQ3_TABLES.md"
```

### Genuine Task 8A validation and saved downstream resumption

These checks use the preserved genuine output and do not run inference. Use the Python 3.12 environment installed above:

```sh
python -m evaluation.m4_20261127.integration.build_r1v3_request --check
python evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
python -m integration.orchestrator resume-task8a --out-dir "$(mktemp -d)/resume"
python -m unittest drafter.tests.test_r1v3_profile drafter.tests.test_r1v3_generation -v
```

The current R1 v3 handoff is accepted and the saved Task 8A output has been resumed through the deterministic CPU Critic. The R1 v3 Critic model route and Critic-to-Revision contract remain unimplemented; Revision and second-Critic stages have not run. This does not regenerate the draft or call a model. The historical PR #62 rejection reproduction is preserved but superseded by the PR #63 handoff contract:

```sh
set +e
python evaluation/m4_20261127/integration/task8a_r1v3/DOWNSTREAM_REPRODUCE.py
status=$?
set -e
test "$status" -eq 2 # historical pre-PR #63 diagnostic only
```

Verify the saved Task 8A artifacts with `sha256sum -c evaluation/m4_20261127/integration/task8a_r1v3/ARTIFACT_SHA256SUMS.txt`. Run the orchestration regressions with `python -m unittest integration.tests.test_orchestrator -v`.

## Interpretation rules

- Keep RQ1 historical, V1, V2 and Phase 5K cohorts separate. The historical 18-case multi-source subset is not the full RQ1 evaluation.
- RQ2's three calibration variants share one source execution; do not call them independent executions or pool other cohorts into their confusion matrix.
- RQ3 repeats and mutations do not increase independent parent groups.
- RQ4 repeats do not increase independent defect cases; its human outcome summary is based on one consensus form.
- Genuine Drafter inference, deterministic host validation, supplementary reasoning review, adapter compatibility and end-to-end acceptance are separate stages.
- Full-case citation screening does not prove evidence was in a condition-specific model input.
- Scripted tests and synthetic fixtures verify interfaces, not new physical observations.
- Missing source databases, recordings, model weights and private human materials are not bundled or substituted by aggregate results.

The recovered RQ2 retrospective records final user-confirmed labels separately from earlier event-review forms. Applicability agreed 3/3; on two applicable cases TP=1, TN=1, FP=0, FN=0; one not-applicable case was excluded. The earlier forms' sham-event observations conflict with the later adjudicated classification; this discrepancy remains unresolved physically, and the final reference did not independently check frame-10 reaction forces. The three rows share one canonical source group and do not support generalized checker accuracy or physical admission.
