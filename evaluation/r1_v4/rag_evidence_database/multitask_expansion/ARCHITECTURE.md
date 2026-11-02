# Database-only extension architecture

Phase5E extends the existing Phase5A registry and Phase5B hierarchical RAG index.
The evidence envelope remains 1.0.0; registry/store migrations and stable-ID rules
are reused. The validated 89-execution SQLite release is copied read-only, then
new execution jobs are atomically appended. Original record IDs and historical
catalog entries remain unchanged. Index builds bind source files, task profile,
reader, record factory, store and retrieval code. A completed job with the same
binding is a no-op. Failures are logged separately and cannot create a completed
partial execution. One execution is validated/indexed at a time, in 32-frame
windows; raw arrays and media stay outside SQLite.

The new profile namespace multitask-v1:object/task_XX dispatches to a closed
source registry, with reader version 1.3.0. Each task has separately compiled
native mapping, object ownership, static fixture IDs, shape declarations,
metadata expectations and an exact recording allowlist. Source-plan and profile
hash mismatches, unknown tasks, wrong roots, unsupported episodes and reserved
execution identities fail closed. Existing reader profiles remain unchanged.

The generic record factory has two presentation corrections for newly built
records: execution text states the actual study partition rather than assuming
all data is development; timestamp-only records use a nonspatial coordinate-frame
declaration. Previously indexed records are preserved byte-for-byte. These
changes do not implement new measurement channels or physical semantics.

Structured and FTS5 retrieval are the existing API and database schema. New
source-target queries validate independent original-source selectors, task and
execution isolation, all six measurement types and frame-domain gaps. The
optional CPU encoder index is a separate SQLite sidecar. It neither mutates the
core database nor changes any validity/admission decision. Core measurements,
AI interpretations, unresolved physical capability and human annotations remain
distinct. No GSN generation, LLM drafting, agents, empirical checker or R1 outcome
admission is implemented in this phase.

Modules: plan (selection), transport/receive/resume_transport (storage retrieval),
pilots/profile/activate/recompile (independent measurement profiles), build
(existing factory/store integration), evaluate (source targets), semantic and
semantic_evaluate (optional retrieval comparison), cli, validate and automated
tests. Generated source manifests and validation reports accompany the code;
recordings, databases and encoder weights remain outside Git on Hestia disk1.
