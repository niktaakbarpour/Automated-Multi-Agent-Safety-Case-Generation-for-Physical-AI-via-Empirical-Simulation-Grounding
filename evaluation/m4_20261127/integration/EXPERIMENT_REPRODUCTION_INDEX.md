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
- **RQ4 Revision and second Critic.** The frozen protocol uses Qwen3-32B with the RQ3 sampling settings and no per-request seed for revision. Both archived response stages record the same Qwen revision pinned above. The saved RQ4 launch script specifies XGrammar, BF16, tensor parallel size 2, context 24,576, one sequence, eager mode and GPU memory fraction 0.90. Preserve the private runtime metadata for an exact inference recreation. See the [protocol](../rq4/RQ4_PROTOCOL.md) and [public provenance](../rq4/finalized_results/RQ4_PROVENANCE_PUBLIC.json).
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

## Public CPU reproduction from a fresh clone

Activate the pinned environment above and run from the repository root. All commands in this section use tracked files and CPU only. The scripts validate or rescore saved results. The Task 8A command also executes the deterministic Critic.

```sh
export PYTHONDONTWRITEBYTECODE=1
M=evaluation/m4_20261127
R=evaluation/r1_v4/rag_evidence_database/retrieval_remediation

python integration/replay_m4_tables.py
python "$R/publication_v1/validate_publication.py"
python integration/verify_saved_results.py
sha256sum -c "$M/rq2/task7c_retrospective/SHA256SUMS.txt"
python "$M/rq4/finalized_results/validate_public_results.py"
sha256sum -c "$M/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt"
```

| Command | Tracked inputs | Expected result |
|---|---|---|
| Manuscript table replay | Historical RQ1 reports, RQ2 public tables, RQ3 frozen batch and saved replies, RQ4 CPU examples/tests and historical transcript | Four `PASS tab:…` lines. RQ3 recomputes the three scored files byte for byte from 108 replies. Model-only mutation detections are 8/24, 9/24 and 10/24. Use the dedicated RQ1 and RQ4 validators for the later result packages. |
| RQ1 publication validation | All three publication CSVs and both checksum manifests | 216 cases, 133 verified complete, 71 correct abstentions, 12 unavailable and zero confirmed false-complete. Three temporal cases verified. The separate saved fault CSV has 12 correct rejections. |
| RQ2 verifier and manifest | Calibration and task-transfer rows, transfer exclusions, and Task 7C public accounting, matrix and provenance | Calibration applicability 3/3 and TP/TN 1/1. Coverage 20/120 overall and 0/100 across tasks in the same scene, with 38 cross-scene mapping rejections. Task 7C scores 18/20, TP/FP/TN/FN 7/2/8/1, precision 77.78%, recall 87.50%, F1 82.35%, accuracy 83.33%. The public check re-joins the pseudonymized case inputs, recounts the confusion matrix and recalculates all four metrics. |
| RQ4 validator and manifest | Sanitized rows, summary and checksums | 12 validated outputs, correct repair 9/9 for Qwen and 2/3 for the template. New second-Critic objections 2/9 per method, target reflags 0/9. |

Run the RQ1 synthetic harness regressions independently with:

```sh
python -m unittest "$R/tests/test_run_eval_v2.py" "$R/tests/test_evaluate_replay_v3.py" -q
```

Expected 19 passing tests. These exercise controlled evaluator and runner behavior. The historical 12-case experiment uses the original artifacts and the targeted replay below.

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
python integration/verify_saved_fixture.py
```

The current R1 v3 handoff is accepted and the saved Task 8A output has been resumed through the deterministic CPU Critic. The R1 v3 Critic model route and Critic-to-Revision contract remain unimplemented; Revision and second-Critic stages have not run. This does not regenerate the draft or call a model. The historical PR #62 rejection check requires the pre-PR #63 source tree. Use the archived-commit command in [the CPU workflow](../../../.github/workflows/m4-cpu.yml). The supported resume leaves five conclusions unresolved and prints `safety_claim_verified: false`. Revision is skipped for lack of an actionable finding, and Checker admission stays closed. The tracked request, source context and argument are sufficient for this resume.

Verify the saved Task 8A artifacts with `sha256sum -c evaluation/m4_20261127/integration/task8a_r1v3/ARTIFACT_SHA256SUMS.txt`. Run the orchestration regressions with `python -m unittest integration.tests.test_orchestrator -v`.

## Restricted CPU rescoring and targeted fault replay

### RQ1 corrected saved responses and source-integrity faults

The verified original inputs are approximately 3.25 GB total before output and temporary copies. The evidence database is 1,411,190,784 bytes, catalogue 2,572,288 bytes, encoder 90,868,376 bytes and the 90 bound artifacts total 1,743,082,074 bytes. The saved `output/` and `three-case-output/` directories in the original replay contain 7,108,786 and 146,722 top-level file bytes. Use the input hashes above and the [publication manifest](../../r1_v4/rag_evidence_database/retrieval_remediation/publication_v1/PUBLICATION_MANIFEST.json).

With approved access, configure `RQ1_DATABASE`, `RQ1_CATALOGUE`, `RQ1_SOURCE_ROOT`, and `RQ1_RUN` (parent of the saved `output/` and `three-case-output/`). Set `RQ1_WORK` to a **new** writable work directory under an approved verifier root, outside the immutable experiment inputs. The verifier rejects symlink components. A generic system temporary directory outside the approved roots fails the verified-then-replaced fixture before retrieval.

```sh
export PYTHONPATH=.
DB_SHA=f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8
CAT_SHA=ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e
python "$R/evaluate_replay_v3.py" --references "$R/FROZEN_HOLDOUT_DATASET.jsonl" \
  --responses "$RQ1_RUN/output" --three-case-responses "$RQ1_RUN/three-case-output" \
  --catalogue "$RQ1_CATALOGUE" --source-root "$RQ1_SOURCE_ROOT" \
  --database-sha256 "$DB_SHA" --output "$RQ1_WORK/score"
python "$R/run_fault_injection_v2.py" --database "$RQ1_DATABASE" --database-sha256 "$DB_SHA" \
  --catalogue "$RQ1_CATALOGUE" --catalogue-sha256 "$CAT_SHA" \
  --source-root "$RQ1_SOURCE_ROOT" --output "$RQ1_WORK/fault" --temporary-root "$RQ1_WORK"
```

The first command independently checks saved response provenance and values against original sources and writes case classifications, aggregate and provenance. The second executes only the 12 targeted CPU faults on temporary fixtures, expecting 12 rejections. The rescored aggregate matched the final saved aggregate byte for byte. Compare fault CSV rows by case ID and exclude `latency_seconds` from equality checks because it records the new execution time. All other fields matched. Use the runner contract linked above for the separate source-level 216-query experiment.

For an authorized download, package the exact bound files in a manifest-backed archive with the database and catalogue and provide the encoder download separately. An isolated Linux container or mount namespace can expose a read-only dataset mount at the original absolute prefix and a separate writable fixture directory under the approved root. This preserves literal path bindings, bytes and descriptor checks. A portable code change would need an explicit allowlisted path mapping shared by catalogue, verifier and evaluator, preservation of the original logical path/hash in provenance, and tests for traversal and symlink rejection. A generic symlink or rewriting the frozen JSONL would break the current binding contract. Release rights for the original recordings and simulator artifacts have yet to be confirmed. Use controlled storage and a license/privacy review before releasing bytes.

### RQ2 Task 7C and RQ4 private scoring

- **Task 7C.** The restricted Task 8D finalized-reference package supplies `APPROVED_REFERENCE.csv` (12,448 bytes), `SOURCE_BINDINGS.csv` (5,513 bytes), and approval, seal and integrity metadata. Task 7C supplies `COHORT_PREDICTIONS.csv` (39,581 bytes), `remote_execution_payload.json` (415,623 bytes), sealed prediction records and bound run logs. Task 7D's archived `verify_task7c_consistency.py` joins these with the saved score rows. To run the archived verifier in an authorized copy, set its `BASE` and `REF` constants to the extracted Task 7C and finalized-reference directories and redirect `OUT` to a new directory. Run `python "$TASK7D_WORK/verify_task7c_consistency.py"` and compare `TASK7D_CORRECTED_NUMERICAL_SUMMARY.json` against the SHA-256 in [public provenance](../rq2/task7c_retrospective/PROVENANCE.json). For saved scoring, release a separately sealed, pseudonymized case-to-reference/prediction join with execution status, object identity and recording hashes. Raw audit or Checker execution additionally needs the original 20-case manifest, bound recordings (1,083,589,774 bytes across 20 trajectories), runner provenance and simulator identity artifacts. Preserve the two unavailable runner bindings as exclusions.
- **RQ4.** Provision the saved experiment tree containing `batch_stage2/`, `results/` and `sealed/REVIEW_KEY.json` (3,505 bytes). Supply the two archived stage response files (25,931 and 52,137 bytes), and the finalized review directory containing the bound `items/B*.md`, `REVIEW_MANIFEST.csv` (1,015 bytes) and `REVIEW_FORM.csv` (5,552 bytes). Keep the response and review digests, model revisions and request identities. See [public provenance](../rq4/finalized_results/RQ4_PROVENANCE_PUBLIC.json) for response hashes. The CPU scorer recomputes the published summary byte for byte from the two saved response stages and the recorded judgments. A releaseable scoring package would require approved pseudonyms and a separately sealed derivative if redactions change any bound bytes. The original reviewer form and confidential blind mapping require coordinator access.

```sh
PYTHONPATH=. python "$M/rq4/experiment/score.py" --base "$RQ4_PRIVATE_EXPERIMENT" \
  --stage1-responses "$RQ4_RUN/RQ4_STAGE1_RESPONSES.jsonl" \
  --stage2-responses "$RQ4_RUN/RQ4_STAGE2_RESPONSES.jsonl" \
  --review-dir "$RQ4_REVIEW" --key "$RQ4_PRIVATE_EXPERIMENT/sealed/REVIEW_KEY.json" \
  --out-dir "$RQ4_NEW_OUTPUT"
cmp "$RQ4_NEW_OUTPUT/RQ4_SUMMARY.csv" "$M/rq4/finalized_results/RQ4_SUMMARY.csv"
```

## Scoring input release boundary

### RQ2 public case inputs

`rq2/task7c_retrospective/SCORING_INPUTS_PUBLIC.csv` is a release derivative with one row per case. It was projected from the approved Task 8D reference and sealed Task 7C predictions after checking case-set equality, execution and group identity, recording digest and agreement with the historical scored join. Randomly ordered opaque case and group labels retain the paired structure without publishing the original identifiers or a crosswalk. The projection includes only reference classification, Checker applicability and outcome, and execution status. It omits raw recordings and hashes, reviewer fields, free text, source paths, and private case bindings. Group and outcome patterns can still be recognizable to someone with the original records. The original seal and manifests cover the original package only.

```sh
python integration/verify_saved_results.py
```

Expected `task7c_retrospective.scoring_input_rows_verified: 20`, 18 scored and two provenance exclusions. The public verifier recomputes the metrics from the released case rows. The archived Task 7D verifier still requires the original sealed inputs for a source audit. The derivative SHA-256 is `a60648d0273b05b58bc8eb0fa8a523dc794e8e2ea707c073ae8b8adf04940412`.

### RQ1 minimum controlled-access archive

The release already includes sanitized case assessments, temporal outcomes and fault outcomes under `publication_v1/`. Run its validator in the public command block above. The offline evaluator needs the full response and citation content to verify source selectors and numeric values. The saved records include raw values and original source bindings omitted from the public release. Removing them would invalidate the per-record digest and prevent the source checks. No redacted response is presented as an original input.

For an approved transfer, use the following layout. Retain the original bytes of both sets of replay inputs. The evaluator checks every sealed case digest, each aggregate digest, and the full frozen reference digest. Bind the archive to the publication manifest and verify the separate source file digests before use.

```text
RQ1_RUN/
  output/{PROVENANCE_MANIFEST.json,AGGREGATE.json,case-*.json}           # 216 records
  three-case-output/{PROVENANCE_MANIFEST.json,AGGREGATE.json,case-*.json} # 3 records
RQ1_DATA/
  expanded.sqlite
  catalogue.sqlite
  encoder/model.safetensors
  sources/<original root-relative paths from FROZEN_HOLDOUT_DATASET.jsonl>
```

Supply the archive through controlled institutional storage after reviewing redistribution rights for the raw recordings, simulator artifacts and material incorporated into the databases. Restore the bound source prefix as described above. Point the restricted CPU scoring command at this layout. The database is required for actual retrieval and fault replay. For offline scoring the evaluator uses its recorded digest, the catalogue and original sources.

### RQ2 trajectory archive

A source audit needs the coordinator-only `EXECUTION_MANIFEST.csv`, the 20 HDF5 files at its recorded bindings, and bound runner/configuration, XML, BDDL and asset records. Keep the sealed prediction package and approved reference package at separate paths for the Task 7D verifier. Do not package the original human submissions for public distribution. Arrange controlled access through the coordinator and confirm redistribution rights before distributing recordings. The public scoring command above requires none of these files.

### RQ4 public and controlled-access scoring

The approved public `finalized_results/RQ4_PER_OUTPUT.csv` already binds the twelve outputs to cases and retains the score-bearing judgments and second-Critic objection counts. Run the existing `validate_public_results.py` command above to recompute the published primary and second-Critic counts. Expected 9/9 correct Qwen repairs, 2/3 template repairs, and 2/9 new objections per method. This uses the sanitized judgments after scoring the model outputs.

The public audit explicitly withheld raw model responses, blind mappings and confidential review forms. The existing full scorer verifies original response, revision and review-item bindings. Its controlled-access layout and exact invocation are given above. The public judgments must not be substituted into that original sealed input contract. An additional raw-response release would need clearance for model content, inputs and blind mapping, plus a newly sealed derivative with approved pseudonyms and checked response-to-output bindings. Preserve the public audit and original hashes.

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
