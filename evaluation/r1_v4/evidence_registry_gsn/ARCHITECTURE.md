# Phase 5A architecture (recorded before implementation)

Parent: 6c41960c9658fc0ef67406b3d27330169eba8335. All execution is on Hestia /disk/1.

Existing `src/evidence.py` resolves raw run/step observations; it does not provide persistent claim retrieval. `data/claims.json` and `data/objections.json` are empty, governed by an explicitly empty collection schema. Requirement proposal tools produce review-only candidates with source pointers and hashes. They will remain unchanged: this scaffold does not promote their proposals into requirements. `src/pilot_storage.py` budgets runtime files; it is not an evidence store.

The new nested package uses SQLite with an immutable canonical JSON record table and indexed scope columns. Schema 1.0.0 records reference sources, never copy arrays or media. Content IDs bind the full record, including versions, selectors, scope, dependencies, uncertainty and validation status. New revisions receive new IDs. Database schema version mismatches fail closed. Portable canonical JSON export, rather than SQLite byte identity, is the reproducibility contract.

Reuse `evaluation.r1_v4.provenance` for canonical JSON, hashing and strict loading, and `contracts.Evidence` through the existing measurement-reader bridge. Registry metadata wraps those contracts rather than inventing physical predicate payloads. The original reader remains responsible for HDF5 structure, native identity and phase validity. Registry source verification only establishes byte identity. Observations retain unknown physical truth.

Deterministic retrieval filters exact requirement version, execution, object, requested type and clock/domain. It reports overlap and gaps, dependency integrity/conflicts, capabilities, source integrity and uncertainty. Reported coverage is metadata availability, never a continuous physical certificate. No ranking model, embedding, confidence cutoff, evidence independence assumption or physical inference is used.

Typed GSN nodes distinguish provenance origins and unresolved physical goals from measurement solutions. Typed edges enforce source/target categories, acyclic argument structure and registry bindings. A solution may document a measurement, AI judgment or checker result without supporting physical truth. All physical goal statuses are restricted to unresolved in this phase; unsupported promotion is rejected even if evidence validates.

The capability adapter consumes existing Phase 2B.4 gates, exposes read-only observations and always disables empirical admission. The demonstration uses episode 000 only, explicit cream_cheese_1 bindings and selected recorded endpoint samples; source metadata are taken from the verified reader and previous audit, not reconstructed from names. SQLite and generated work outputs live outside Git. Compact export, graph, reports and tests are committed.

Deferred: LLM retrieval, agents, drafting/criticism/revision execution, calibration, empirical support/fall/negative admission, cross-clock coverage joins and automatic claim support. No original or held-out data change.
