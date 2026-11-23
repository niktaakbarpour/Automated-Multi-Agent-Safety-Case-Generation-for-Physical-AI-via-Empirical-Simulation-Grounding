# Sharing and privacy boundary

This handoff contains only compact M4 source metadata, evidence-record envelopes, selected recorded values, blank authoring forms, and verification tools. It does not contain raw HDF5 recordings, images, XML source archives, model weights, credentials, private keys, reviewer identities, private RQ2 review submissions, or coordinator mappings.

The package is published in the project's private repository and includes internal execution IDs, source hashes, and original source-location strings as provenance. Keep the repository restricted to project collaborators. Do not mirror these files to a public repository or unrestricted issue tracker.

The bundled extracts make the listed numeric evidence available offline. Do not use provenance-only source-location fields as instructions for accessing another machine. The workflow is: clone the repository, read the package guide, run its Python 3 standard-library verifier, and author using the bundled CSV/JSONL files.
