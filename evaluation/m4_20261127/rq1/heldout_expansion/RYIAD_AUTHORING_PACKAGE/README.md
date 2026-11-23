# RQ1 offline authoring package

This package is designed for a local repository checkout. It contains 30 source-execution capability rows, four task IDs, four variants, 60 empty query/reference slots, the source/evidence index, source-recovery receipts, complete compact evidence-record envelopes, and actual recorded values for the indexed measurement selectors that can be exported safely and usefully.

No raw trajectories, model weights, credentials, private keys, reviewer identities, or private RQ2 materials are included. The source paths in provenance CSVs document origin only; the workflow uses the bundled extracts.

## Start here

1. Read AUTHORING_GUIDE.md and OFFLINE_EVIDENCE/EXTRACT_LIMITATIONS.md.
2. Run from the repository root:
   python3 evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/verify_offline_handoff.py
3. Review SOURCE_CAPABILITIES.csv, SOURCE_EVIDENCE_INDEX.csv, OFFLINE_EVIDENCE/TASK_CONTEXT.csv, and the compressed JSONL evidence extracts.
4. Fill only BLANK_QUERY_REFERENCE_FORM.csv. Keep all other human fields blank until you have authored and checked each reference. Do not run retrieval or write predictions into this template.

## Package contents

- SOURCE_CAPABILITIES.csv: one row per selected canonical execution.
- BLANK_QUERY_REFERENCE_FORM.csv: two blank slots per execution; no questions or gold references are supplied.
- SOURCE_EVIDENCE_INDEX.csv: exact evidence IDs, requirement/version metadata, object, type, saved-frame interval, original selector, source hash, validation, and limitations.
- SOURCE_RECOVERY_VERIFICATION.csv and SOURCE_REFERENCE_HASH_VERIFICATION.csv: frozen source recovery and hash checks.
- SOURCE_RECOVERY_SUMMARY.json: aggregate verified counts.
- OFFLINE_EVIDENCE/EVIDENCE_RECORDS.jsonl.gz: original indexed evidence-record envelopes for the selected executions (metadata/provenance; these envelopes do not themselves contain raw numeric samples).
- OFFLINE_EVIDENCE/EVIDENCE_SAMPLES.jsonl.gz: source values read from exact HDF5 selectors and linked to evidence IDs.
- OFFLINE_EVIDENCE/TASK_CONTEXT.csv: recorded task text and metadata with source-record hashes.
- OFFLINE_EVIDENCE/UNEXTRACTED_EVIDENCE.csv and EXTRACT_LIMITATIONS.md: explicit data not distributed and what cannot be checked offline.
- OFFLINE_EVIDENCE/EXTRACT_MANIFEST.json: source hashes, file sizes/checksums, counts, and extractor version.
- AUTHORING_FORM_SCHEMA.json and OFFLINE_EVIDENCE/EVIDENCE_SAMPLES.schema.json: record schemas.
- build_offline_evidence_extract.py: reproducible source-side export tool; not needed for offline use.
- verify_offline_handoff.py: standard-library-only local integrity and blank-form check.

The historical 18-case analysis and three Phase 5K false-complete cases are separate development evidence. They are linked in evaluation/m4_20261127/RYIAD_HANDOFF.md and are not reused as new cases.
