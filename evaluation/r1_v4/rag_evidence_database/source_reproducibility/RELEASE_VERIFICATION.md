# Independent release verification

A caller must supply an independently trusted SHA-256 for ARTIFACT_MANIFEST.json. The manifest verifies database, contracts/code, preservation results and external artifacts. A hash generated today anchors current bytes, not recording-time identity.

Run on Hestia:

```sh
python3 -S -m evaluation.r1_v4.rag_evidence_database.source_reproducibility.check_release --sha256 TRUSTED_MANIFEST_SHA256 --scope metadata
```

Use `--scope sources` for original recordings/XML/assets/proofs and `--scope provenance` for selected dependency/binary artifacts. Approved paths, descriptor-bound access, no symlinks and hashes remain mandatory. Metadata-only operation cannot return source values when external data are absent.

`ProvenanceStore(database, expected_sha256=trusted_database_sha)` and `retrieve(store, ProvenanceQuery(...))` retain Phase 5H guards. verified_source_values verifies original bytes, bindings, contract, dtype/shape and scope. verified_physical_interpretation also requires verified order, units and coordinate type; conditional properties cannot satisfy it. provenance_complete requires explicit scope `release-evidence-graph-v1` and verifies its artifact closure. historical_producer_attestation fails explicitly throughout this release. Missing historical evidence does not invalidate otherwise verified raw retrieval.

Restoration uses restore.create(database, executions, fresh_root) and a caller-pinned RESTORE.json hash. Paths map explicitly to content-addressed scratch objects with execution membership and canonical hash enforced. RestoredRelease verifies the copied database and execution graph artifacts before descriptor-bound raw reads. It never falls back to originals. The runtime is the separately inventoried current Hestia environment, not an archived hermetic runtime. Historical producer reexecution is unsupported.

Metadata-only needs pinned database/schema/code. Verified values additionally need HDF5 and referenced geometry/proofs. Annotations need model/primary-source validation artifacts. Bounded provenance also needs selected current dependency artifacts and producer matches. The 60 reserved, 38 excluded and 1,470 pending executions are never restored or read.
