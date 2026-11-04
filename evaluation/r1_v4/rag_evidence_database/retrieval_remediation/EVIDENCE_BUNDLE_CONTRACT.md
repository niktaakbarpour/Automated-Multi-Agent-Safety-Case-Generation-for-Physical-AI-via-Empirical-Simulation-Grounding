# Evidence bundle contract

Machine schema: EVIDENCE_BUNDLE.schema.json. Entry point: `Retriever(index_path, expected_index_sha256).retrieve(BundleRequest(...))`. Database and catalogue are separately pinned. Strict is default; verified_session explicitly reuses cryptographically verified identity only while descriptor/file signatures remain stable.

Output preserves original query, resolved execution/task/variant, interpretation, requested families, per-family items/coverage, original evidence IDs or explicitly derived source-reference IDs, artifact paths/hashes/selectors, units/semantic properties, integrity/assurance, assumptions, missing evidence and uncertainties. Source references are not new measurement records. Direct values remain direct; symbolic identity/physical annotations remain derived/conditional as inherited.

Global states: COMPLETE WITHIN VERIFIED CONTRACT, PARTIAL, UNAVAILABLE, UNSUPPORTED, AMBIGUOUS, INVALID SCOPE. Completeness concerns requested retrieval obligations, never a safety claim. Every required family must be AVAILABLE and every requested saved sample present. Action/inference metadata have separate action coverage. Camera/contact records remain references; no calibrated images, physical event or support inference. Known issue 001 can omit an obligation before this check: unreviewed natural-language COMPLETE is not yet a dependable query-completeness guarantee.

Typed frame/clock intervals cannot conflict; unknown/contradictory object or scope context abstains. Channels retain inherited raw/source semantics, revolute/prismatic units under the recorded metric convention, conditional actuator SI interpretation and conditional cache offset. World transforms, sensor synchronization, historical binary attestation and new action values are not enabled. Metadata-only typed measurement requests fail closed in guard-1.

Source text/BDDL/instruction-like bytes are data. safety_claim_sufficiency=NOT_EVALUATED, safety_claim_verified=false and empirical_admission_enabled=false. There is no production factual/safety judge. Values permit checking narrow facts under contracts; no R1 judgment is produced.
