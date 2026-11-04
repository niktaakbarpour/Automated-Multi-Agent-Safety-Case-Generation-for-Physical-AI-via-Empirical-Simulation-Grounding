# Automated independent replay

Frozen dataset SHA-256: `d859d142664900c0d65fdd71a964fe1d6c913642a76b3dd8a4f7e89bda5d1e37`.

Full resume (448 reused), fresh run (448 newly evaluated), partial resume (37 reused), and isolated-environment process (448 newly evaluated) yield canonical digest `52742deed7e2fbfe99bed437205e263fc32a563bd9bbbf7539852dccacfe0bd6`. Canonicalization removes only latency and random scratch-directory prefixes in error messages; identities, values, coverage, status and citations remain checked. 1792 case files were independently revalidated. An additional strict-mode 40-case subset matched status/value/citation outputs. All checks passed.

Query schema, bundle schema and capability registry were regenerated separately and matched frozen bytes. The existing database was hash-verified and preserved, not rebuilt or migrated. Retrieval replay and byte-identical interface assembly are reproducible; this does not claim historical producer-environment reconstruction, independent human replication or binary attestation.

Bounded restoration copied 122 explicit mappings/120 unique contents (148459848 bytes) for one eligible execution, retaining source hashes and canonical identities. Restored values and citations matched. Removing a required restored source failed closed despite the original source remaining available: no hidden original-path fallback. Database and catalogue remain separately pinned prerequisites. See RESTORATION_RESULTS.json and restoration.py; restoration manifests reside under the external working directory.
