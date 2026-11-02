# Phase 5B validation

Parent eefa9c36607ece47f0d8a57718a1d87d9969d07f; branch feat/rag-evidence-database. All research execution occurred on Hestia, outputs under owned /disk/1. No original/archived recording was modified, restored or deleted. No new experiment, embedding API, agent, GSN generator or checker was run or implemented.

| Suite | Passed | Failed / skipped |
|---|---:|---:|
| RAG database | 45 | 0 / 0 |
| Phase 5A registry/GSN preservation | 73 | 0 / 0 |
| Phase 2A infrastructure | 105 | 0 / 0 |
| Measurement reader | 44 | 0 / 0 |
| Measurement profile | 30 | 0 / 0 |
| Evidence review | 15 | 0 / 0 |
| Frozen V3 | 41 | 0 / 0 |
| Reference | 17 | 0 / 0 |
| Generalization | 13 | 0 / 0 |
| Total | 383 | 0 / 0 |

Two independent builds have identical logical build IDs and canonical evidence exports. An idempotent rerun freshly checks inputs and skips all four completed jobs. Transaction rollback, failure logging, completion markers, compatible migration, stable IDs, old Registry reopening, FTS integrity, metadata filters, gaps, invalid source rejection, uncertainty, conflicts and attribution are tested. Read-only CLI query and integrity commands succeed after the builder process exits. SQLite physical layout/timings are not the reproducibility contract.

Database integrity passes for all 1,360 evidence units and 2,000 historical catalog entries, including source hashes, dependencies, FTS correspondence and SQLite foreign keys. All 38 restored files match their prior hashes before/after. All prior audit, reader, measurement-profile, evidence-review and Phase 5A artifact manifests remain unchanged. Frozen V3 code/config/executor/predictions, both evaluation seals and 12 sealed members, human-scoring freeze and eight protected scoring files verify unchanged. Blank human forms remain untouched; no human ground truth is created. No held-out physical labels or recordings are indexed or used to tune search.

The 69 known-source development queries pass source-target checks, including 65 text queries and four terminal gap cases. Precision@1 and MRR are 1.0; Recall@1 is 0.989130; Recall@20 and precision of actually returned results up to 20 are 1.0. Relevance means source selector correctness, not physical truth. See RETRIEVAL_EVALUATION.md for protocol and limitations. No semantic generalization or checker accuracy claim is made.

Acceptance: verified development corpus indexed; every record has source provenance; references reproduce; gaps remain explicit; invalid/missing sources reject; resume and reopen work; evaluation and integrity pass; unindexed corpus is documented; no downstream safety-case functionality is added. Historical metadata expansion is explicitly separate from raw measurement coverage. All empirical V4 admission remains disabled.

Exact production path: `/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite`; size 14,622,720 bytes; SHA-256 `998827e38863e9dca7fd8fd21d8a77a50802a049ead11e2dad19081f580c7e9f`. Full logs/reproduction database reside in the same validated directory. Committed code, schema migrations, query fixtures, source/build manifests and compact reports are under `/disk/1/data/niktakbr/trustworthy-phase16/evaluation/r1_v4/rag_evidence_database/`. ARTIFACT_SHA256.json binds all package files except itself.
