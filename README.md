# Trustworthy AI for Physical AI

This project evaluates tools that build evidence-grounded safety arguments from recorded robot simulation data. It separates source measurements, requirement checks, argument generation, criticism, revision, and evaluation. A completed software check or generated argument does not certify physical safety.

## Framework

The workflow is `recorded execution → evidence retrieval → optional requirement check → GSN Drafter → Critic → reviewed Revision → second Critic`.

- **RQ1 retrieval** finds requested evidence families, checks source bindings and obligation coverage, and abstains when evidence is unavailable.
- **RQ2 Checker** evaluates the R1 fall-prevention requirement for protected objects over recorded frames. It reports unresolved results when evidence does not support a decision.
- **Drafter** produces a per-object Goal Structuring Notation (GSN) argument from a validated request and supplied evidence.
- **Critic** checks argument structure, links and evidence, using deterministic rules and an optional model route.
- **Revision** applies only approved, contract-permitted edits and preserves evidence and provenance.

The saved genuine Task 8A argument has five `insufficient_information` conclusions. The deterministic CPU Critic handoff is supported. Human review materials are prepared and human judgments are pending. The model-backed R1 v3 Critic route and compatible downstream Revision path are incomplete, so end-to-end safety-case acceptance has not been demonstrated.

## Repository guide

| Path | Contents |
|---|---|
| `src/`, `config/`, `schemas/`, `requirements/` | Recorded execution inventory, configuration, schemas and requirement definitions |
| `evaluation/r1_v4/` | Versioned evidence registry, Checker, measurement readers and retrieval implementations |
| `drafter/`, `critic/`, `drafter/revision/` | Argument generation, criticism and constrained revision |
| `integration/` | Component handoffs, saved fixtures and Task 8A CPU orchestration |
| `evaluation/m4_20261127/` | M4 protocols, frozen inputs, results and validators |
| `reports/`, `evidence/`, `data/` | Inventory records, manifests and historical evidence |
| `human_review_package/` | Review materials with package-specific handling instructions |
| `report/m4_neurips_materials/` | Manuscript source and supporting material |

See [the repository map](docs/REPOSITORY_MAP.md) for maintained scripts and historical artifacts, and [the artifact policy](docs/ARTIFACT_POLICY.md) for access and preservation guidance.

## Install

Use CPython 3.12. The pinned CPU environment was verified with Python 3.12.16 on macOS arm64. From the repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip --isolated install --index-url https://pypi.org/simple \
  -r requirements-m4-cpu.lock -r requirements.txt \
  -r drafter/requirements.txt -r critic/requirements.txt \
  -r evaluation/r1_v4/requirements.txt
python -m pip check
```

The lock includes `jsonschema==4.19.1`, `h5py==3.12.1`, `numpy==1.26.4`, and `tokenizers==0.22.2`. Existing experiments use pretrained models. Model training is not required. Checkpoint downloads, recorded inference settings, and environment details are in the [reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md#model-setup-for-fresh-inference).

## Quick start

These checks use tracked data, run on CPU, and do not call a model:

```sh
python integration/replay_m4_tables.py
python integration/verify_saved_fixture.py
python integration/verify_saved_results.py
```

The first summarizes archived experimental outcomes. The fixture verifier checks saved component inputs and outputs. The result verifier recomputes public RQ2 counts, including Task 7C. These commands verify saved work. They do not rerun the experiments.

To resume the saved genuine Task 8A request through the currently supported deterministic CPU Critic:

```sh
python -m evaluation.m4_20261127.integration.build_r1v3_request --check
python evaluation/m4_20261127/integration/task8a_r1v3/validate_generated_argument.py
python -m integration.orchestrator resume-task8a --out-dir "$(mktemp -d)/resume"
```

This validates and resumes the saved argument. It does not perform fresh Drafter inference or Checker admission.

## Result reproduction

The [RQ1–RQ4 reproduction index](evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md) is the authoritative command guide. It separates saved-result verification, numerical recomputation, model-response rescoring, source-level replay, and fresh inference. The principal result sets are:

| Experiment | Result package | Reproduction available from a fresh clone |
|---|---|---|
| **RQ1 Phase 5K retrieval** | `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/publication_v1/` | Publication integrity and result validation. Corrected saved-response rescoring and fault replay require restricted replay outputs and source inputs. |
| **RQ2 calibration and transfer** | `evaluation/m4_20261127/rq2/` | Public calibration, coverage and pseudonymized Task 7C counts are recomputed from tracked rows. Source audit requires original recordings and restricted provenance. |
| **RQ3 Critic mutation experiment** | `evaluation/m4_20261127/rq3/` | Saved model responses can be rescored from the tracked batch and labels. Fresh inference requires the pinned Qwen model and GPU serving stack. |
| **RQ4 Revision experiment** | `evaluation/m4_20261127/rq4/finalized_results/` | Public result validation recomputes sanitized counts. Full rescoring requires the original response, review and blind-key package. |

RQ1 source files and databases, RQ2 trajectories and private source bindings, and RQ4 confidential review bindings are not distributed in the public repository. The index documents their required filenames, sizes where measured, hashes, access boundaries and preparation instructions. Redistribution rights for the large source datasets require confirmation.

## Tests and hardware

Run maintained CPU tests with:

```sh
python -m unittest integration.tests.test_handoff integration.tests.test_r1v3_handoff \
  integration.tests.test_replay_m4_tables integration.tests.test_orchestrator -v
python -m unittest discover -s evaluation/m4_20261127/rq4/tests -p 'test_*.py' -v
python -m unittest drafter.tests.test_r1v3_profile drafter.tests.test_r1v3_generation -v
```

RQ1 synthetic regressions and other component checks are listed in the reproduction index and CI workflow. Fresh Qwen inference uses a compatible Linux GPU server and the pinned checkpoint. The recorded Qwen3-32B runs used two NVIDIA L40S GPUs in BF16 with tensor parallelism of two. CPU result checks and the saved Task 8A deterministic resume require no GPU.

## Contributors

The project was developed collaboratively by Nikta Akbarpour, Alex Hashemi, and Ryiad Elewi. Their implementation and evaluation contributions are represented in the repository history. The experimental registry identifies the ownership and provenance of individual work.

## Interpretation

RQ1–RQ4 results are bounded development results with experiment-specific limitations. RQ2 retrospective scoring is not an independent holdout. RQ3 uses exposed development groups and awaits independent label review. RQ4 is a small planted-defect pilot. The supplementary Task 8A reasoning review has materials prepared, with judgments pending. No result establishes physical safety or general system effectiveness. Read [Milestone 4 results](evaluation/m4_20261127/MILESTONE4_RESULTS.md), the [current integration status](evaluation/m4_20261127/integration/CURRENT_INTEGRATION_STATUS.md), and the [experiment registry](evaluation/m4_20261127/EXPERIMENT_REGISTRY.md) before interpreting metrics.
