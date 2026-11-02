# Schema and provenance

Phase5F preserves the Phase5A evidence envelope 1.0.0 and the Phase5B/5E SQLite
extension 1.1.0. A transactional, additive migration creates its own
rag_variant_schema version 1.0.0. It does not append an incompatible version to
rag_migrations, rewrite evidence IDs, or modify the baseline database.

rag_env_variants contains a content identity, exact XML SHA-256, verified asset
content digest and canonical asset references. The stable ID is
`xmlenv:SHA256(canonical(identity_version, xml_sha256, asset_content_digest))`.
The asset digest hashes sorted canonical paths, SHA-256 values and sizes.
Different XML paths can share an identity when XML bytes and dependencies match.
Different asset contents give different IDs even with identical XML bytes.
Different XML bytes are conservatively distinct; no approximate XML equivalence
is claimed. Nested XML includes are unsupported without an explicit new contract.
Named mesh/texture aliases can share a verified file. All aliases are preserved
in external provenance; only identical file identities are deduplicated.
Conflicting hashes/sizes are rejected.

rag_execution_env binds every execution to its task, suite, exact variant,
original XML/asset manifest, mapping artifact/version and object/body/geom
identities. Geometry maps remain per execution, even when XML is shared, because
record-derived rigid transforms and validation scopes have execution provenance.
Mappings and profiles are compact external artifacts under the Phase5F work
root; EXTERNAL_PROFILE_ARTIFACTS.json pins every path, size and hash. This avoids
committing dozens of megabytes of repeated geometry metadata. Immutable SQL
triggers protect variant and execution associations. Foreign keys and explicit
integrity checks enforce their relationships. Evidence joins these normalized
relations through its stable execution ID rather than duplicating XML metadata
in each temporal window.

rag_scope_status explicitly distinguishes indexed, unindexed-profile-pending,
validated-unindexed, unsupported, unresolved and excluded states. Reserved and
preflight rows contain minimal exclusion identity metadata only. rag_variant_builds
binds the core logical build digest to all variant/scope relations. Independent
build comparison excludes physical SQLite layout and timing measurements.

The closed reader namespace `variant-v1:SUITE/task_XX` selects the exact
execution profile, never one task-wide XML. Reader version 1.4.0 retains recorder
schema4.0 semantics. New timestamp-only records use not_applicable_timestamp;
historical records remain unchanged. Source arrays, contacts, camera references,
original wording and uncertainty remain under the existing contracts. No new
numerical physical field, detector, threshold or empirical witness is introduced.

VariantQuery extends metadata filters with variant_id, field_name and explicit
comparative mode. Variant, task and execution constraints are checked before
FTS5 or optional local semantic ranking. Live XML, asset and mapping hashes are
checked. Comparative results are separate execution groups; their temporal
coverage is never composed. A shared XML is not shared observational evidence.
Unknown variants, unindexed executions, excluded scopes, unavailable timestamps,
unsupported fields/mappings, invalid scopes and valid-but-empty matches have
separate statuses. Legacy Query/search remain compatible and reject unknown
variant parameters; use the Phase5F API for variant guarantees.

All task objectives and BDDL predicates are metadata, not observations of task
completion or physical events. Native identities and saved channels are not
calibrated support/fall predicates. Empirical R1 admission remains disabled.
