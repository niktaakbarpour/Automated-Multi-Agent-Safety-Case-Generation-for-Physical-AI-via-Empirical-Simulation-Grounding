# Artifact policy

- **Frozen evidence and results** include versioned experiment inputs, protocols, checksums, labels, saved outputs, and manuscript tables. Preserve their bytes and provenance. Reproduce saved analyses through the documented validators rather than editing frozen files.
- **Historical records** under `evaluation/`, `reports/`, and `evidence/` explain prior experiments and development decisions. Their age or size alone is not grounds for removal.
- **Generated outputs** are include logs and reports under `reports/` and inventory records under `data/`. Some generated files are tracked scientific provenance. Review changes before committing them. Do not treat generated output as a new scientific result without the relevant protocol and review.
- **External dependencies** include raw simulation recordings, retrieval databases, model weights, and selected runtime traces. Their availability and redistribution rights vary. A saved-result replay does not provide fresh inference or raw-data reproduction.
- **Restricted material** includes human-review and adjudication records. Git readers can retrieve tracked review artifacts. Follow the package-specific access instructions and do not copy submissions or judgments into public summaries.

Removing a tracked artifact from the current tree does not erase its Git history. Any proposed archive or access change needs a verified destination, integrity manifest, retrieval procedure, and review of access requirements.
