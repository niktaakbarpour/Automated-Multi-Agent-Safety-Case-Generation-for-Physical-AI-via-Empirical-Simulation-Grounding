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

There is no `evaluation/m4_20261127/rq4/` package or supported RQ4 reproduction command in the current repository tree. RQ4 remains unimplemented here; do not infer results from RQ1–RQ3 or report a reproduction as complete.

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
