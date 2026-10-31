# Reproduction and interfaces

Run on Hestia from `/disk/1/data/niktakbr/trustworthy-phase16`. No install, GPU, simulator, Alliance computation or original source write is needed. Set `PYTHONDONTWRITEBYTECODE=1`, `TMPDIR=/disk/1/data/niktakbr` and:

```
export PYTHONPATH=.:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages
python3 -S -m evaluation.r1_v4.evidence_registry_gsn demo /disk/1/data/niktakbr/NEW-UNUSED-DEMO-DIRECTORY
python3 -S -m evaluation.r1_v4.evidence_registry_gsn integrity /disk/1/data/niktakbr/NEW-UNUSED-DEMO-DIRECTORY/registry.sqlite
python3 -S -m evaluation.r1_v4.evidence_registry_gsn export /disk/1/data/niktakbr/NEW-UNUSED-DEMO-DIRECTORY/registry.sqlite
```

The demo output directory must not exist. Queries use a strict JSON object with exactly the `retrieval.Query` fields. Save `RETRIEVAL.json`'s `query` object to a fresh owned /disk/1 file, then run:

```
python3 -S -m evaluation.r1_v4.evidence_registry_gsn query DATABASE.sqlite QUERY.json
python3 -S -m unittest discover -s evaluation/r1_v4/evidence_registry_gsn/tests -v
```

`Registry(path, create=True)` creates a new database; `Registry(path)` opens read-only. `add(records)` atomically inserts an immutable batch after record, source and dependency validation, with idempotent repeated IDs. `export()` is the portable deterministic snapshot. Close connections explicitly. SQLite file bytes are not the reproducibility promise. Changing scope, source, version, capability, limitations or provenance creates a new content ID. There is no update/delete/migration API. Version incompatibility is rejected, requiring an explicit future migration design.

`Record.parse` checks the closed dataclass, supported versions, source scope, kind/status restrictions and content ID. JSON schemas validate interchange shape; Python validation enforces semantic invariants. The metadata schema wraps existing V4 `Evidence`, not a replacement physical evidence contract. Only explicit R1 2.0.0 scope is supported in this phase. Local non-symlink sources under owned /disk/1 are supported. Source files and private measurements stay on Hestia; registry records store selectors and provenance, not arrays.

`retrieve(registry, Query(...))` orders results by stable ID, matches exact identity/version/type, checks source hashes and dependency closure, and reports independent per-type availability gaps. Minimum capabilities require the exact requested status; conditional/blocked/unsupported statuses are not ranked into VERIFIED. It returns rejected counterevidence, complete dependency metadata, uncertainty, restrictions and query rationale. No interpolation, cross-clock joins, dynamic composition or physical certificate is produced. Time-gap endpoints conservatively bound missing open intervals; saved frame availability never implies substep coverage.

`Graph.validate(registry)` checks node/edge types, stable unique IDs, registry-bound solution provenance, scope and interval containment, cycles and forbidden goal promotion. `supported_by` is a GSN structural relation, not a truth evaluator. All physical goals remain unresolved; retrieval cannot promote them. Nodes retain origins for LLM proposals, observations, checker outcomes, AI and human references. Existing checker outcomes can be represented as qualified results through their own provenance; this phase does not ingest legacy V3 outcomes into R1 v2 or label synthetic outcomes empirical.

`adapter.assessment` always disables physical checking/admission even if externally supplied gate flags are changed. It does not call the V4 physical decision engine. `typed_observation` accepts only existing direct observations with unknown truth and verified measurement validity. Exact-input numeric geometry, source byte integrity, physical predicate validity and claim support remain distinct.

Trust boundary: metadata validation is not independent physical validation. Upstream producers must validate measurement structure and selectors. The production builder calls the pinned reader, checks the corrected full native map and records its version hashes. Arbitrary metadata clients cannot create a physical safety verdict through this API. Existing AI reference rows stay provisional; human forms stay blank. No calibration thresholds, source independence claims or ground truth are introduced.

The full regression driver is `python3 -S -m evaluation.r1_v4.evidence_registry_gsn.validate`; its fixed output directory must be absent. Preserve completed validation outputs; for a new run supply a new owned /disk/1 directory through `validate.main(output=...)`. Compact reports and manifests are committed; databases and full test workspaces remain outside Git.
