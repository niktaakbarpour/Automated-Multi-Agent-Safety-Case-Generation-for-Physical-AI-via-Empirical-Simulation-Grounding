# Trustworthy AI M4: empirical simulation grounding

This repository studies how evidence-grounded safety-case tools behave on recorded physical-AI simulation evidence. It does not certify a robot or policy as safe. The framework keeps measured source evidence, requirement checks, argument generation, criticism, revision and evaluation as separately validated steps.

## Research questions and architecture

- **RQ1 — Evidence retrieval:** retrieves requested evidence families and source-scoped measurements, checks obligation coverage and abstains when a request cannot be supported. Retrieval completeness is limited to the explicit request; it is not proof of R1 safety evidence sufficiency.
- **RQ2 — Requirement-aware R1 checking:** evaluates the fall-prevention requirement for specified protected non-target objects on the living-room table, under a versioned configuration and recorded monitoring interval. An unsupported decision remains an abstention. The current adjudicated sample is tiny and development-only.
- **GSN Drafter:** proposes a per-object GSN safety argument from validated configuration and supplied evidence. Its accepted structure and citations do not establish that the claims are physically true.
- **RQ3 — Critic:** checks the argument and its links, runs deterministic rules and can optionally screen model proposals. A zero-finding report is not a safety conclusion.
- **RQ4 — Revision Agent:** applies only contract-approved edits to an argument, preserving source evidence, requirement configuration and provenance. It cannot revise physical outcomes or invent evidence.

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

Raw simulation evidence, retrieval databases, model weights, private reviewer submissions and some original runtime traces are not stored in this repository.

## Level A — CPU-only setup, tests and demonstrations

Python **3.12** is the verified environment for the commands below. From a fresh clone, at the repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r drafter/requirements.txt -r critic/requirements.txt -r evaluation/r1_v4/requirements.txt
```

The install is CPU-capable and does not install model weights or call a model. The package manifests pin or bound NumPy, h5py, tokenizers and jsonschema dependencies. Python 3.12.14 with these manifests was tested for this guide; other Python versions are not claimed as verified here.

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

### Saved integration and revision examples

- `python integration/verify_saved_fixture.py` checks the saved one-pass Qwen Drafter/Critic fixture and its manifests. Both historical Qwen reports have zero findings, including the controlled guarantee; current deterministic Critic rules flag that controlled guarantee. The original Drafter request/run envelope and source recordings are not present in the fixture, so this is not a complete regeneration of the original Drafter call.
- `python -m drafter.revision.tools.check_examples` checks saved revision requests/results. The saved real zero-finding report produces a no-change outcome. The separate scripted two-round revision cycle is an integration demonstration, not a real model revision.
- `python -m unittest integration.tests.test_handoff -v` tests the Drafter-to-Critic adapter on scripted inputs.

See the [reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md) for result paths, commands and boundaries.

## Level C — New inference and external evidence

New model inference requires a compatible OpenAI-style serving endpoint or local server, the specified checkpoint and tokenizer, hardware admission, environment/runtime versions, frozen input manifests and output destinations. Model weights are not included. New RQ3 inference used Qwen/Qwen3-32B revision `9216db5781bf21249d130ec9da846c4624c16137`, two L40S GPUs, BF16 and vLLM's native sampling fallback (`VLLM_USE_FLASHINFER_SAMPLER=0`); the precise recorded run notes and server launch command are in the real-run directory. Do not copy the old launch command without checking current resource admission and approvals.

A full RQ1 replay additionally requires the external retrieval database/catalogue, source recordings and pinned encoder described in its reproducibility documentation. RQ2 source-level replay requires the source HDF5 and associated recordings; external paths in result provenance are not available from GitHub. Any new human-reviewed RQ2 evaluation requires genuine independent human submissions and an authorized adjudication workflow. No model or scripted output may stand in for those labels.

The isolated RQ3 unseen-parent expansion remains blocked: PR #39 and stacked PR #41 document the unavailable HDF5 sources and zero admitted independent parent executions. These changes do not merge or replace those PRs.

## Scientific boundaries

- RQ1 completeness is scoped to the requested obligations. The known temporal false-complete failures remain.
- RQ2's finalized binary comparison has one positive, one negative, one not-applicable case and one canonical source group. Expanded outputs are coverage/abstention counts, not accuracy.
- RQ3's 108 responses are development-only; 12 semantic cases come from two exposed parent groups. The independent mutation-label audit is pending. C is admission-status-only.
- The saved one-pass Qwen interaction shows real model calls on a development fixture and one controlled semantic miss; it does not establish physical safety or general Critic effectiveness.
- RQ4 revision safeguards are exercised by saved and scripted CPU examples. No genuine real-model changed-argument / second-Critic end-to-end cycle is demonstrated.
- A passing schema, CPU test, source hash or component handoff proves only its checked contract, not the truth of physical claims or complete system-level performance.

## Reports

- [End-to-end feasibility](evaluation/m4_20261127/integration/END_TO_END_FEASIBILITY_REPORT.md)
- [CPU reproducibility record](evaluation/m4_20261127/integration/CPU_REPRODUCIBILITY_REPORT.md)
- [RQ1-RQ4 reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md)
# Trustworthy AI safety-case framework

This repository contains a prototype framework for grounding safety-case arguments in recorded Physical AI executions. It includes execution-inventory code, requirement and evidence schemas, Drafter and Critic components, integration fixtures, tests, and research evaluation packages.

The repository does **not** establish that a policy is safe. Recorded task success is not a safety label, geometric contact is not proof of physical support, and an unresolved checker result is not a pass. Read each study's limitations before interpreting its saved outputs.

## Project map

- `src/`: execution inventory, source-backed measurements, identifiers, geometry, and collection commands.
- `schemas/`, `config/`, `requirements/`: data contracts, approved checker configuration, and R1 definitions.
- `drafter/`: argument planning, generation, validation, and revision components.
- `critic/`: structural and evidence-link checks, review logic, and model-assisted criticism.
- `integration/`: orchestration and end-to-end fixtures.
- `tests/`: CPU tests for the core framework.
- `evaluation/`: versioned research protocols, frozen inputs, saved outputs, and evaluation-specific tools.
- `data/`, `evidence/`, `reports/`: compact execution metadata and provenance. Large trajectories and videos are not required for the CPU checks below.

## Environment setup

Use Python 3.12 for the current M4 offline packages. A basic local environment is:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The checked-in root requirements file is not a full lockfile for every optional model server, simulator, or Hestia workflow. The root `pipeline.sh` currently points at a site-specific Hestia virtual environment; it is not a portable clean-clone launcher. The commands below use explicit repository-relative paths and do not call a model or simulator.

## CPU validation

From the repository root, run the core tests and the evaluation integrity checks:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest discover -s evaluation/m4_20261127/rq3/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python evaluation/m4_20261127/rq3/mutations/build_mutations.py --check
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python evaluation/m4_20261127/rq3/experiment/build_batch.py --check
python evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/verify_offline_handoff.py
```

The RQ1 verifier uses only the Python standard library. The RQ3 mutation and batch checks are CPU-only and do not perform inference. A successful check verifies the saved artifacts against the checked-in builders; it does not independently validate scientific labels or claims.

## Research-question status and reproduction

### RQ1 — evidence retrieval and references

The offline authoring package contains 30 canonical source executions and 60 blank query/reference slots. Its evidence extracts support offline source inspection, but they are not a completed gold reference set and do not contain image pixels or all source measurements. Read the [package guide](evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/README.md) and [extract limitations](evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/OFFLINE_EVIDENCE/EXTRACT_LIMITATIONS.md), then run the verifier above.

**Supported now:** verify the package and author/query against the bundled evidence. **Not supported now:** reproduce a held-out retrieval score; the reference slots remain blank and no frozen independent scoring set is provided.

### RQ2 — R1 checker coverage

The committed [expanded-evaluation summary](evaluation/m4_20261127/rq2/expanded_evaluation/SUMMARY_METRICS.json), [methods and limitations](evaluation/m4_20261127/rq2/expanded_evaluation/METHODS_AND_LIMITATIONS.md), case results, eligibility inventory, and exclusions preserve the current coverage analysis. The 60-execution generalization cohort has no independent human labels; the saved findings are coverage and abstention measures, not accuracy. Cross-scene mapping-gate exclusions are not checker abstentions. The historical 432-execution count is not an identified per-execution sample.

**Supported now:** inspect the frozen results and their provenance. There is no checked-in command that reruns the checker and regenerates the M4 summary from raw source data. A new checker run requires the source dataset and approved environment; it must not be presented as a replay of the saved results.

### RQ3 — Critic mutation and model comparison

The [frozen mutation protocol](evaluation/m4_20261127/rq3/MUTATION_PROTOCOL.md), [experiment configuration](evaluation/m4_20261127/rq3/EXPERIMENT_CONFIG.md), manifests, batch, raw responses, and scored outputs describe the current development experiment. Rebuild/check the mutation set and batch with the CPU commands above. Replay the saved response scoring into a new directory with:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python evaluation/m4_20261127/rq3/experiment/score.py \
  --batch evaluation/m4_20261127/rq3/experiment/batch \
  --responses evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl \
  --out-dir /tmp/trustworthy-rq3-replay
```

This recreates scored tables from the saved replies; it does not rerun inference. The existing run used `Qwen/Qwen3-32B` revision `9216db5781bf21249d130ec9da846c4624c16137`. New inference requires that model (or an explicitly recorded replacement), a compatible OpenAI-style model server, and suitable GPU memory. The frozen request batch, prompts, decoding settings, response log, and run notes must be retained together. For a new run, use `experiment/run_batch.py` with an explicit `--batch`, `--out`, `--base-url`, and `--model-revision`, then score that new response file separately.

**Scientific limit:** the current mutation benchmark has two parent groups, zero independent groups, and developer-authored labels pending independent review. Condition C represents checker-admission status; it does not test a verified physical checker verdict. Results are development diagnostics, not general performance estimates.

### RQ4

The RQ4 Revision Agent is implemented and CPU-tested under `drafter/revision/`, including scripted revision and saved no-change examples. However, no frozen M4 RQ4 empirical evaluation package or real Qwen-generated revision followed by a second Critic evaluation is currently available for reproduction. The existing tests establish contract and integration behavior, not empirical revision effectiveness.

## Data, access, and expected outputs

Compact schemas, manifests, metadata, and explicitly packaged evidence extracts are versioned with their study documentation. Raw HDF5 trajectories, videos, model weights, and source datasets may require separate Hestia access and are not necessary for the CPU checks. Source paths in manifests are provenance records; they are not portable download links. Do not commit credentials, model weights, raw recordings, private human-review submissions, coordinator-only material, or new unapproved labels. Preserve any human judgments only in their approved access-controlled location. The current private GitHub `main` already contains `human_review_package/` (including reviewer and adjudication subdirectories) and `evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/`; this guide does not add or change them. Audit their approved access scope before creating any public copy.

CPU checks produce test output and compare generated artifacts in place; they should not change tracked files. The RQ3 scoring command writes `RQ3_PER_CASE_RESULTS.csv` and `RQ3_SUMMARY.csv` only under the requested output directory. New inference produces JSONL response and metadata files and requires an explicit model-server run.

## Existing execution-inventory workflow

The root `pipeline.sh` provides task/run inventory and transition-inspection commands. It currently embeds a site-specific Python path and source-data location; verify both against the target Hestia checkout before use. `collect` inventories existing recordings and does not run a policy. `validate` checks the saved inventory and selected trajectory bindings. These commands are separate from RQ1–RQ3 evaluation reproduction.

## Reproducibility gaps to close

1. Add a portable, fully pinned test/runtime dependency set and remove the site-specific interpreter/data paths from any future general-purpose launcher.
2. Add a deterministic RQ2 result-replay script that regenerates the saved coverage summary from the frozen prediction, eligibility, and exclusion inputs.
3. Complete and independently freeze RQ1 references before publishing retrieval scores.
4. Implement and document an RQ4 package before claiming RQ4 reproduction support.
5. Resolve the independent-label, source-integrity, and reviewer-access limitations recorded by each evaluation before making accuracy or safety claims.
