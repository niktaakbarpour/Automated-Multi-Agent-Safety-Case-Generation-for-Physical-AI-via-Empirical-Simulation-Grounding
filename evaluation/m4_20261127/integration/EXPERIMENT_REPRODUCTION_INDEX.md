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

## CPU installation

Use CPython **3.12.16** (verified on macOS arm64). The Linux CPU workflow selects the Python 3.12 series. From a fresh Git clone, use a POSIX shell, Python with `venv` and pip, and access to PyPI or a mirror containing the same wheels. Checksum commands use GNU `sha256sum`; on macOS use `shasum -a 256 -c` in its place. The saved-result and regression paths use CPU only and need no model server, CUDA, simulator installation or external recordings.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -VV
python -m pip --isolated install --index-url https://pypi.org/simple \
  -r requirements-m4-cpu.lock -r requirements.txt \
  -r drafter/requirements.txt -r critic/requirements.txt \
  -r evaluation/r1_v4/requirements.txt
python -m pip check
python -c 'import h5py, jsonschema, numpy'
```

Source-level retrieval also needs SQLite with FTS5 support through Python’s `sqlite3` module. The lock pins the shared CPU environment, including `jsonschema==4.19.1`, `h5py==3.12.1`, `numpy==1.26.4`, and `tokenizers==0.22.2`. The component files declare their own constraints and are installed together as in CI. Geometry, pilot and historical prompt requirements are separate workloads. If a restricted index cannot supply a pin such as `anyio==4.16.0`, obtain the pinned wheels through an approved index or wheelhouse. Preserve the lock.

## Model setup for fresh inference

These experiments use pretrained checkpoints without training or fine-tuning. Download snapshots only when preparing a fresh inference environment. Set `MODEL_ROOT` to a writable local directory with room for the weights (Qwen BF16 weights alone require roughly 64 GB). The `hf` CLI is supplied by the locked Hugging Face Hub package.

```sh
export MODEL_ROOT=/path/to/model-storage
hf download Qwen/Qwen3-32B --revision 9216db5781bf21249d130ec9da846c4624c16137 --local-dir "$MODEL_ROOT/Qwen3-32B"
hf download sentence-transformers/all-MiniLM-L6-v2 --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 --local-dir "$MODEL_ROOT/encoder"
hf download moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10 --revision 638918f3d1c2e43a39a8a20772bdb8b91835e4b7 --local-dir "$MODEL_ROOT/OpenVLA-OFT"
```

- **Qwen model server.** Use a separate Linux GPU environment with a compatible NVIDIA driver, CUDA and vLLM. Task 8A records vLLM 0.31.0, BF16 without quantization, tensor parallel size 2, context 24,576, one sequence, GPU memory fraction 0.90, eager mode and thinking disabled. It used Outlines with JSON schema, temperature 0.7, top-p 0.8, seed 42 and 8,192 maximum output tokens. See [Task 8A run metadata](task8a_r1v3/RUN_METADATA_PUBLIC.json).
- **RQ3 Critic inference.** The saved run used two NVIDIA L40S GPUs (48 GB each), BF16, tensor parallel size 2, context 24,576, one sequence and GPU memory fraction 0.90. Serve the local Qwen snapshot under `Qwen/Qwen3-32B` at a configurable OpenAI-compatible endpoint. Use XGrammar with `json_object`, thinking disabled, temperature 0.6, top-p 0.95, top-k 20, 8,192 output tokens and `VLLM_USE_FLASHINFER_SAMPLER=0`. See the [recorded runtime and compatibility notes](../rq3/experiment/real_run_20261122T142300Z/RUN_NOTES.md).
- **RQ4 Revision and second Critic.** The frozen protocol uses Qwen3-32B with the RQ3 sampling settings and no per-request seed for revision. The public final provenance omits the actual stage checkpoint revisions and server hardware. The Qwen download above pins the verified RQ3/Task 8A checkpoint. Exact RQ4 inference requires the original stage metadata. See the [protocol](../rq4/RQ4_PROTOCOL.md) and [public provenance](../rq4/finalized_results/RQ4_PROVENANCE_PUBLIC.json).
- **Encoder and recorded policy.** MiniLM can run locally on CPU for semantic retrieval. The recorded RQ1 bundle replay checks its weights and revision without executing the encoder. OpenVLA-OFT identifies the Task 8A recording producer. The evaluations consume existing LIBERO recordings. Producing new rollouts would require the matching LIBERO simulator, task assets and policy runtime and would yield new data.

## Prepare inputs

**Simulation recordings.** Obtain the original collection from the project maintainers where access is authorized. There is no public download for the original recording tree. Preserve the run identities and layout below. For inventory tooling, set `source_results` in a local `config/project.json` to the collection root. Check small-file bindings against [the source manifest](../../../reports/source_manifest.json) and trajectory bindings against `data/runs.json` and each episode's `integrity_manifest.json`.

```text
RECORDINGS/{summary.json,run_metadata.json}
RECORDINGS/<suite>/task_*/{task.bddl,run_metadata.json}
RECORDINGS/<suite>/task_*/episode_*/{trajectory.h5,metadata.json,evaluation.json,completion.json,integrity_manifest.json,semantic_initial_conditions.json,simulator_index.json,simulator.xml,evaluator_version.json,success_condition_source.py.txt}
```

### RQ1 retrieval

For the public path, use the committed publication tables and manifests in the index above. For a source-level replay, provision these exact artifacts in a local staging area. The database and catalogue require authorized access to the original snapshots. Generic LIBERO data or newly built SQLite files cannot replace them.

| Required filename | SHA-256 |
|---|---|
| `expanded.sqlite` | `f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8` |
| `catalogue.sqlite` | `ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e` |
| `encoder/model.safetensors` | `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db` |
| `FROZEN_HOLDOUT_DATASET.jsonl` | `f6c6e31e12d3c0ed7e70db077494a4bed98f1d0a56d82f382c556c13b00c6caf` |

Use the tracked [frozen dataset](../../r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl) as the exact inventory for the 216 queries. Its `source_artifacts` entries give source filenames, layout and digests for the 90 unique original HDF5, XML and JSON artifacts. Request the exact bound corpus and profiles from the maintainers. Verify the inputs before invoking `run_eval_v2` with configurable `--database`, `--catalogue`, `--encoder`, `--references`, `--source-root` and a new `--output` directory. The frozen harness expects the original absolute artifact bindings under the declared root, so copying the tree under a new prefix alone is insufficient. A compatible source mount or a separately validated relocation mechanism is required for fresh replay on another host. Keep the original reference and digests intact. See the [runner contract and historical invocation](../../r1_v4/rag_evidence_database/retrieval_remediation/ACTUAL_RETRIEVAL_REPLAY_V2.md).

### RQ2 Checker

Use the committed calibration tables, expanded coverage outputs and Task 7C publication for CPU checks. The raw retrospective audit requires the original HDF5 recordings and related manifests, the approved Task 8D reference and source bindings, and the sealed Task 7C prediction ledger and outputs. Obtain them from the project maintainers with permission to access the original human records. Match case ID, execution, recording digest and run provenance before joining predictions to references. The [Task 7C provenance](../rq2/task7c_retrospective/PROVENANCE.json) supplies the reference, ledger and audit digests. The restricted source join and two unavailable source-runner bindings cannot be reconstructed from the public tables.

### RQ3 Critic

Use the tracked frozen batch in `rq3/experiment/batch/`, archived `RQ3_RESPONSES.jsonl` and development labels in `rq3/mutations/gold_labels.json`. The CPU scorer consumes these directly. Preserve the paired parent and mutation IDs and check regenerated files against the committed scored outputs using the commands below. The separate unseen-parent expansion lacks admitted independent source recordings and completed labels.

### RQ4 Revision

Use the committed cases, finding approvals, and `rq4/finalized_results/` checksums for public verification. Full private scoring needs the original `RQ4_STAGE1_RESPONSES.jsonl`, `RQ4_STAGE2_RESPONSES.jsonl`, sealed review form and blind mapping from the coordinator, plus the matching stage batches. Validate the response digests in the public provenance before applying the [protocol's preparation and scoring steps](../rq4/RQ4_PROTOCOL.md). The public release omits the sealed review inputs and raw stage responses. The published Task 8A supplementary review packet is a separate pending review.

## CPU manuscript table replay

```sh
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
