# Repository map

| Area | Where to start |
|---|---|
| Framework | `requirements/` and `schemas/` define requirements and data contracts. `evaluation/r1_v4/` contains the evidence readers, Checker, registry and retrieval implementations alongside versioned studies. `drafter/`, `critic/` and `drafter/revision/` implement the argument pipeline. `integration/` contains the handoff and saved Task 8A orchestrator. |
| Maintained experiment commands | The [reproduction index](../evaluation/m4_20261127/integration/EXPERIMENT_REPRODUCTION_INDEX.md) links the table replay, saved result checks, RQ3 scorer and Task 8A resumption. |
| Final results | Start with [Milestone 4 results](../evaluation/m4_20261127/MILESTONE4_RESULTS.md) and the [experiment registry](../evaluation/m4_20261127/EXPERIMENT_REGISTRY.md). Frozen result packages and provenance live under `evaluation/m4_20261127/` and the RQ1 retrieval release under `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/publication_v1/`. Manuscript sources live under `report/m4_neurips_materials/`. |
| Human evaluation | The [Task 8A reviewer packet](../evaluation/m4_20261127/integration/GSN_HUMAN_REVIEW/README.md) contains blank materials for a pending supplementary review. The completed RQ2 retrospective comparison and RQ4 consensus outcomes are documented in their result packages. `human_review_package/` retains earlier materials with their own access and handling instructions. |
| Tests | `.github/workflows/m4-cpu.yml` lists the CPU checks. Tests live under `tests/`, `integration/tests/`, and the relevant component or evaluation package. |
| Historical artifacts | Earlier dated studies in `evaluation/`, saved fixtures in `integration/fixtures/`, and records in `reports/`, `evidence/`, and `data/` preserve experiment inputs and provenance. Some records reference external sources. See the [artifact policy](ARTIFACT_POLICY.md). |

## Execution inventory

`pipeline.sh` inspects the saved inventory and source transitions. `run.sh` collects the original inventory, and `collect.sh` redirects its log to `reports/collection.log`. These commands use the active Python environment or `PYTHON`. For source-dependent commands, point `config/project.json`'s `source_results` to the local root of the original recordings, containing `summary.json`, `run_metadata.json` and the recorded run files. The checked-in value is the original Hestia location.

`audit.sh SOURCE_RESULTS OUTPUT_JSON` inventories existing annotation keys in those recordings. Choose a new output path to preserve the saved audit. Historical pilot runtime settings in `config/requirement_generation*.json` describe their original model cache and environment.
