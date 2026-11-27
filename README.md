# Trustworthy AI M4: empirical simulation grounding

This repository studies how evidence-grounded safety-case tools behave on recorded physical-AI simulation evidence. It does not certify a robot or policy as safe. The framework keeps measured source evidence, requirement checks, argument generation, criticism, revision and evaluation as separately validated steps.

## Current Milestone 4 status

The genuine R1 v3 Drafter run and bounded RQ4 Revision pilot are complete. The Drafter produced five graphs with `insufficient_information` for every protected object; the frozen request had zero graph-eligible evidence and no admitted checker assessment. Its output passed Drafter and host-side validation, but it is still a draft: supplementary human reasoning review is pending, the R1 v3 Drafter-to-Critic adapter contract is not yet integrated, and end-to-end safety-case acceptance has not been demonstrated.

RQ2 and RQ3 results remain development evidence with their documented admission and independent-review limitations. RQ4 is a small planted-defect pilot, not evidence of general Revision Agent effectiveness. No result establishes physical safety. See the [current M4 results](evaluation/m4_20261127/MILESTONE4_RESULTS.md), [integration status](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md), and [experiment registry](evaluation/m4_20261127/EXPERIMENT_REGISTRY.md).

## Reproduce the four M4 manuscript tables on CPU

From the root of a fresh clone, use Python 3.12. The install needs package-index access. The replay uses only repository files and temporary output.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-m4-cpu.lock
python -m pip check
python integration/replay_m4_tables.py
```

Success prints four `PASS tab:…` lines with the checked rows and exits zero. The replay compares them with [the manuscript tables](report/m4_neurips_materials/tables.tex). A missing input, failed validator or table mismatch exits nonzero.

| Manuscript label | Replay implementation (functions in [the CPU command](integration/replay_m4_tables.py)) | Evidence and interpretation |
|---|---|---|
| `tab:rq1` | `rq1()` | Extracts historical ranking metrics and Phase 5K V2 coverage, abstention and failure IDs from the four reports cited in the LaTeX table. |
| `tab:rq2` | `rq2()`, [verify_saved_results.py](integration/verify_saved_results.py) | Recounts public calibration and expanded coverage rows and reads historical aggregates from [results.json](evaluation/r1_v3/results.json). Independent evaluation remains pending. |
| `tab:rq3-conditions` | `rq3()`, [score.py](evaluation/m4_20261127/rq3/experiment/score.py), [make_tables.py](evaluation/m4_20261127/rq3/experiment/make_tables.py) | Rescores archived Qwen replies, compares all three generated files byte-for-byte, and checks the T/R/C paper columns. |
| `tab:rq4` | `rq4()`, [verify_saved_fixture.py](integration/verify_saved_fixture.py), [check_examples.py](drafter/revision/tools/check_examples.py), revision unit tests | Verifies the one-pass fixture and runs current checks. Runs 102 revision tests and requires 145 passing checks from the current checker. The manuscript’s historical 149 is verified separately by counting passing checks in the [A0 transcript](drafter/revision/handoff/TEST_TRANSCRIPT.txt). |

This command replays saved results. Level C below describes the external requirements for fresh model inference and raw-data reproduction.

## Repository and contributor guides

- [Repository map](docs/REPOSITORY_MAP.md) describes active components and historical result areas.
- [Cleanup audit](docs/REPOSITORY_CLEANUP_AUDIT.md) records code findings, archive candidates, and publication risks.
- [Artifact policy](docs/ARTIFACT_POLICY.md) explains frozen evidence, generated outputs, external dependencies, and restricted records.

## Research questions and architecture

- **RQ1 — Evidence retrieval:** retrieves requested evidence families and source-scoped measurements, checks obligation coverage and abstains when a request cannot be supported. Retrieval completeness is limited to the explicit request; it is not proof of R1 safety evidence sufficiency.
- **RQ2 — Requirement-aware R1 checking:** evaluates the fall-prevention requirement for specified protected non-target objects on the living-room table, under a versioned configuration and recorded monitoring interval. An unsupported decision remains an abstention. The current adjudicated sample is tiny and development-only.
- **GSN Drafter:** proposes a per-object GSN safety argument from validated configuration and supplied evidence. Its accepted structure and citations do not establish that the claims are physically true.
- **RQ3 — Critic:** checks the argument and its links, runs deterministic rules and can optionally screen model proposals. A zero-finding report is not a safety conclusion.
- **RQ4 — Revision Agent:** applies only contract-approved edits to an argument, preserving source evidence, requirement configuration and provenance. It cannot revise physical outcomes or invent evidence. The completed genuine Qwen run is a bounded pilot on three planted defects; repeated outputs are not independent cases, and the broader effectiveness study remains NO-GO.

The intended flow is:

`recorded evidence -> retrieval -> optional R1 assessment -> Drafter -> Critic -> reviewed revision -> second Critic -> scoring`

Each arrow has its own contract. The complete chain has not been demonstrated on a new, independently eligible physical execution. See [the feasibility report](evaluation/m4_20261127/integration/END_TO_END_FEASIBILITY_REPORT.md).

## Repository map

| Path | Contents |
|---|---|
| `requirements/` | Versioned R1 definitions and configuration contracts |
| `evaluation/r1_v4/` | Evidence registry, checker infrastructure, measurement readers and RAG releases |
| `drafter/` | Drafter request, graph-plan, serialization and validation code |
| `critic/` | Critic schemas, input checks, deterministic rules and optional model screening |
| `drafter/revision/` | Contract-bound, auditable argument revision |
| `integration/` | Drafter-to-Critic adapter and saved one-pass fixture |
| `evaluation/m4_20261127/rq1/` | RQ1 frozen retrieval evaluations and remediation analyses |
| `evaluation/m4_20261127/rq2/` | Final calibration and expanded coverage-only analysis |
| `evaluation/m4_20261127/rq3/` | Mutation protocol, frozen benchmark, raw model responses and scores |
| `evaluation/m4_20261127/integration/` | Feasibility and reproduction reports |

Full raw simulation recordings, retrieval databases, model weights and some original runtime traces are external. The repository tracks historical review and adjudication artifacts alongside the public replay inputs. See the [artifact policy](docs/ARTIFACT_POLICY.md) before redistribution.

## Level A — CPU tests and demonstrations

Run the main CPU regression suites:

```sh
python -m unittest discover -s drafter/tests -t . -v
python -m unittest discover -s critic/tests -t . -v
python -m unittest integration.tests.test_handoff -v
python -m unittest discover -s drafter/revision/tests -t . -v
python -m drafter.revision.tools.check_examples
python -m unittest evaluation.m4_20261127.rq3.tests.test_experiment evaluation.m4_20261127.rq3.tests.test_mutations -v
python -m unittest evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_bundle evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_integrity -v
```

The RQ3 and RQ1 remediation tests are invoked by module because those test directories are not Python packages for `unittest discover -s`. These commands use scripted, synthetic or saved test inputs. The RQ3 unit tests print scripted request activity; those replies are test inputs, not new model results.

Verify the committed one-pass fixture and public RQ2 tables:

```sh
python integration/verify_saved_fixture.py
python integration/verify_saved_results.py
```

These validators make no model calls and do not read private RQ2 reviewer files. The first checks eight fixture hashes and current Critic contracts. The second recalculates the public RQ2 confusion and coverage counts from committed case rows and metrics.

Other useful CPU commands:

```sh
python -m drafter --validate-request drafter/cases/scenario_a.request.json
python -m critic --help
python -m drafter.revision --help
```

A synthetic integration or revision example demonstrates interface behavior only. It is not a physical execution or an effectiveness result.

## Level B — Reproduce saved analyses without inference

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

The scorer and table generator are CPU-only. This re-analysis does not rerun Qwen. The expected archive has 108 valid replies (36 each for T/R/C) and nine retained failed attempts; these are attempts, not nine failed logical requests. The score files are development-only, use two exposed parent groups, and await Ryiad's independent mutation-label review. Condition C contains checker-admission status only, not independently verified physical checker evidence. Citation screening against a full case does not show that the condition-specific model input contained the cited evidence.

### RQ2 saved results

Run `python integration/verify_saved_results.py`. The current adjudicated calibration reports applicability agreement 3/3 and TP=1, TN=1, FP=0, FN=0 on two applicable cases; one not-applicable case is excluded from binary metrics. These three variants share one canonical source group. The expanded 60-execution analysis is unlabeled coverage evidence: 300 object units, 120 applicable, 20 determinate decisions and 100 abstentions. Its overall coverage is 20/120. The verifier checks those counts against committed row-level artifacts; it does not authenticate external Hestia source recordings or create new labels.

### RQ1 saved results

Committed RQ1 metric and assessment files can be read directly under `evaluation/m4_20261127/rq1/` and `evaluation/r1_v4/rag_evidence_database/`. Historical, V1, V2 and Phase 5K findings are separate populations. Phase 5K V2 reported 24/24 multi-source completeness and 84/84 required-family obligations, while three temporal-plan cases remain false-complete: `KH2-C2-02`, `KH2-C2-10` and `KH2-C2-18`. These results do not mean that full retrieval can be rerun from a fresh clone: the retrieval database, source corpus/HDF5 recordings and pinned local encoder are external. Do not run the Hestia-only replay instructions as if their dependencies were bundled.

### Genuine Task 8A artifact validation and known adapter result

These checks use the preserved genuine output and do not run inference. Use the Python 3.12 environment installed above:

```sh
python -m evaluation.m4_20261127.integration.build_r1v3_request --check
python evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
python -m unittest drafter.tests.test_r1v3_profile drafter.tests.test_r1v3_generation -v
```

The current adapter rejection is expected and independently reproducible without a model call. Exit status 2 with the expected `ContractError` markers indicates the known interface mismatch; any other exit status is an error:

```sh
set +e
python evaluation/m4_20261127/integration/task8a_r1v3/DOWNSTREAM_REPRODUCE.py
status=$?
set -e
test "$status" -eq 2
```

The generated argument passed full host validation and has five `insufficient_information` object outcomes. Evidence admission remains disabled; the draft still requires supplementary human reasoning review and downstream adapter integration. See [current integration status](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md).

### Finalized RQ4 public results

The bounded pilot’s public case-level and aggregate files can be checked on CPU without inference, human review or sealed mappings:

```sh
python evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py
sha256sum -c evaluation/m4_20261127/integration/task8a_r1v3/ARTIFACT_SHA256SUMS.txt
sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt
```

See [Milestone 4 final results](evaluation/m4_20261127/MILESTONE4_RESULTS.md) for results and claim limits.

### Saved integration and revision examples

- `python integration/verify_saved_fixture.py` checks the saved one-pass Qwen Drafter/Critic fixture and its manifests. Both historical Qwen reports have zero findings, including the controlled guarantee; current deterministic Critic rules flag that controlled guarantee. The original Drafter request/run envelope and source recordings are not present in the fixture, so this is not a complete regeneration of the original Drafter call.
- `python -m drafter.revision.tools.check_examples` checks saved revision requests/results. The saved real zero-finding report produces a no-change outcome. The separate scripted two-round revision cycle is an integration demonstration, not a real model revision.
- `python -m unittest integration.tests.test_handoff -v` tests the Drafter-to-Critic adapter on scripted inputs.

See the [current reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md) and [experiment registry](evaluation/m4_20261127/EXPERIMENT_REGISTRY.md) for result paths, commands and boundaries. The historical feasibility report is retained as a dated snapshot; current Task 8A status is in [the integration status report](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md).

## Level C — New inference and external evidence

New model inference requires a compatible OpenAI-style serving endpoint or local server, the specified checkpoint and tokenizer, hardware admission, environment/runtime versions, frozen input manifests and output destinations. Model weights are not included. New RQ3 inference used Qwen/Qwen3-32B revision `9216db5781bf21249d130ec9da846c4624c16137`, two L40S GPUs, BF16 and vLLM's native sampling fallback (`VLLM_USE_FLASHINFER_SAMPLER=0`); the precise recorded run notes and server launch command are in the real-run directory. Do not copy the old launch command without checking current resource admission and approvals.

A full RQ1 replay additionally requires the external retrieval database/catalogue, source recordings and pinned encoder described in its reproducibility documentation. RQ2 source-level replay requires the source HDF5 and associated recordings; external paths in result provenance are not available from GitHub. Any new human-reviewed RQ2 evaluation requires genuine independent human submissions and an authorized adjudication workflow. No model or scripted output may stand in for those labels.

The isolated RQ3 unseen-parent expansion remains blocked: PR #39 and stacked PR #41 document the unavailable HDF5 sources and zero admitted independent parent executions. These changes do not merge or replace those PRs.

## Scientific boundaries

- RQ1 completeness is scoped to the requested obligations. The known temporal false-complete failures remain.
- RQ2's finalized binary comparison has one positive, one negative, one not-applicable case and one canonical source group. Expanded outputs are coverage/abstention counts, not accuracy.
- RQ3's 108 responses are development-only; 12 semantic cases come from two exposed parent groups. The independent mutation-label audit is pending. C is admission-status-only.
- The saved one-pass Qwen interaction shows real model calls on a development fixture and one controlled semantic miss; it does not establish physical safety or general Critic effectiveness.
- RQ4 includes a genuine Qwen Revision pilot and second-Critic outputs on three planted defects (9 Qwen outputs, 3 template outputs). Its human judgments came from one coordinator-confirmed consensus form; independent agreement metrics are unavailable. This does not demonstrate the complete Task 8A Drafter-to-Critic-to-Revision-to-second-Critic chain or general effectiveness.
- A passing schema, CPU test, source hash or component handoff proves only its checked contract, not the truth of physical claims or complete system-level performance.

## Reports

- [Milestone 4 final results](evaluation/m4_20261127/MILESTONE4_RESULTS.md)
- [Experiment registry](evaluation/m4_20261127/EXPERIMENT_REGISTRY.md)
- [Current integration status](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md)
- [End-to-end feasibility historical snapshot](evaluation/m4_20261127/integration/END_TO_END_FEASIBILITY_REPORT.md)
- [CPU reproducibility record](evaluation/m4_20261127/integration/CPU_REPRODUCIBILITY_REPORT.md)
- [RQ1-RQ4 reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md)

## Existing execution-inventory workflow

The root `pipeline.sh` provides task/run inventory and transition-inspection commands. It uses the active Python environment or the interpreter selected by `PYTHON`. Commands that read recordings require the external source location in `config/project.json`. `collect` inventories existing recordings and does not run a policy. `validate` checks the saved inventory and selected trajectory bindings. These commands are separate from RQ1–RQ3 evaluation reproduction.
