# Repository cleanup audit

## Active code and documentation

- The pilot queue used a personal cache fallback even though storage planning requires a configured cache before queue startup can reach runtime setup. Both now use the same project-relative path resolver. The configured absolute paths keep their existing meaning.
- Drafter and Critic have separate schema and JSON loading helpers. They serve distinct validation entry points, so sharing a loader would couple those interfaces for little benefit.
- Integration and M4 experiment scripts support direct invocation with local import paths. Their replay, scoring and fixture entry points have existing callers. Keep those interfaces and avoid a packaging refactor during M4.
- The root README, repository map and artifact policy now describe the current shell entry points and distinguish tracked review artifacts from external inputs.

## Inventory and possible archiving

The inspected branch at `6bb90f2` tracked 2,540 files totaling 648 MB of blob content. Historical experiments under `evaluation/` and `reports/` account for much of the tree. Paths and sizes below come from Git metadata.

| Path | Size | Retention reason |
|---|---:|---|
| `data/runs.json` | 81.6 MB | Execution inventory used by `src/pipeline.py` and requirement input preparation. Keep available at the existing path. |
| `evaluation/r1_v4/rag_evidence_database/source_reproducibility/PRODUCER_INVENTORY.csv` | 33.9 MB | Source provenance inventory written by the source reproducibility reporting code. |
| `evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/OFFLINE_EVIDENCE/EVIDENCE_SAMPLES.jsonl.gz` | 33.6 MB | Frozen offline evidence input read by the handoff verifier. |
| `reports/fall_review_20261016/position_coverage.csv` | 18.8 MB | Historical per-frame audit referenced by the report's measurement audit. Candidate for an access-controlled institutional archive after confirming consumers and access terms. |

An archive pilot for the historical CSV would need approval and a named institutional destination, a SHA-256 and byte-size manifest, documented access, and retrieval to the original path before running dependent reports. Missing access or changing timestamps and bytes can break reproducibility. Removing a file from the current tree leaves its history and does not reclaim historical Git storage.

## Publication review

The tracked tree includes historical reviewer, adjudication, and blinding-related paths, including archived material outside the main review package. The audit used path and Git metadata and did not inspect submissions or keys. Review access and redistribution rights with the maintainers before sharing the repository or its history more widely. Development labels and handoff records also warrant provenance and intended-audience review. Some provenance records identify infrastructure paths. Local exclusions govern future additions and do not remove tracked artifacts from older commits.
