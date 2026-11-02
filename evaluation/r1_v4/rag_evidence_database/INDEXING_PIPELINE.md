# Read-only reproducible population

1. Verify restored SHA-256 against the Phase 2B.2 manifest. Bind supporting requirement, native mapping, identity constraints, capability reports and producer code hashes, policy 1.0.0 and window size 32 into each execution input digest.
2. Invoke the existing reader on one execution at a time. No image pixels/videos are read by this indexer. Raw arrays are transient inputs, never SQLite payloads.
3. Construct execution documents, object/surface identities and source selectors for six measurement categories. Exact task instruction, requirement text, gate CSV and readiness text are searchable. Preserve uncertainties and provisional AI provenance.
4. Atomically insert one execution's immutable records, bounded descriptions and FTS units, then its completion/input digest. Stable IDs deduplicate reruns. Failures are logged and prevent partial insertion. Resume rehashes inputs before skipping a completed digest. Atomic execution commits are the interruption boundary.
5. After four complete jobs and passing integrity, populate the historical catalog from data/runs.json and archive identity mappings. Summaries never replace raw evidence.
6. Save a content-addressed manifest over records, searchable units, jobs and catalog. Timings are outside build identity. Reopen read-only after the builder exits.

Historical revisions remain immutable. Retrieval selects records matching the current execution input digest; prior build manifests remain available. New bindings create new IDs; identical reruns preserve IDs and build identity. Catalog source changes require a versioned rebuild. No automatic physical reinterpretation is supported.

Sources are read-only; only owned /disk/1 outputs are written. CLI address-space ceiling: 4 GiB. Units: at most 32 saved frames. One execution is read in memory; searches are capped at 10,000 candidates. The reader still validates full execution structure. No GPU job, download, simulation, hosted API or bulk restoration occurs.
