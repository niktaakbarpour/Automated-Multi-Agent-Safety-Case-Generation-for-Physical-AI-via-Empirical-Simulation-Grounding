# Repository map

## Active components

- `src/`, `config/`, `schemas/`, and `requirements/` hold the execution inventory, configuration, data contracts, and requirement definitions.
- `drafter/` and `critic/` implement argument drafting, criticism, and revision.
- `integration/` contains component handoffs and saved-fixture validators.
- `tests/` and component-local test directories cover the inventory and research tools.
- `evaluation/m4_20261127/` contains the current M4 protocols, frozen cohorts, saved scores, and reproduction utilities. The CPU replay is documented in the root README.
- `report/m4_neurips_materials/` contains manuscript source and table material.

## Historical and supporting material

- `evaluation/` also retains earlier RQ1/RQ2 studies and development iterations used to explain provenance and limitations.
- `reports/` and `evidence/` retain source manifests, run records, and validation outputs.
- `data/` contains versioned inventory records. Large records and traces can reference external source data.
- `human_review_package/` contains review workflow artifacts. Consult its access and handling instructions before use.
- `pipeline.sh` is a repository-relative inventory CLI. `run.sh` and `collect.sh` perform the historical collection operation and require the configured external recordings and collection dependencies. `audit.sh` preserves a Hestia-specific annotation audit invocation.

See [artifact policy](ARTIFACT_POLICY.md) for retention and access boundaries.
