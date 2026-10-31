# Phase 1 validation record

Status: passed specification/document checks; proposed requirement, not approved.
Baseline: 30b4ac9cc8e2a1d0e83f72ee74d31f77829e62c1.

Research QA ran on Hestia, using system Python and jsonschema, in:
`/disk/1/data/niktakbr/trustworthy-r1-generalized-spec-v2-20261031/repo/`.
No Alliance compute, simulator runs, decoding, new scoring or V4 implementation
was performed in Phase 1. Nothing was written to `/disk/0` by this task.

Command (from that repository snapshot):

```sh
/usr/bin/python3 requirements/r1_generalized_v2/validate_spec.py /disk/1/data/niktakbr/trustworthy-r1-generalized-spec-v2-20261031/QA_RESULTS_03.json
```

The machine-readable result is `QA_RESULTS.json`, copied as derived QA metadata.
Its source-package hashes bind the audited specification files and validation
script; this summary and the copied result are delivery records added afterward.

Passed: Draft 2020-12 schema meta-validation; three illustrative configurations;
23 configuration acceptance/rejection fixtures (including cardinalities 0/1/3/5);
68 relative references and source-line bounds; 16 source snapshots matching the
authoritative baseline; outcome vocabulary and all D01–D11 approval gates.

Live Hestia checks matched the frozen V3 checker, execution adapter, configuration
and predictions. Both historical evaluation seals and their 7/5 member hashes
verified, along with all eight human-scoring-protected files. Exact source hashes
and paths are recorded in the JSON result. Existing result artifacts were read,
not changed; the proposed specification does not relabel historical outcomes.

Manual consistency review covered applicability versus invalid contracts,
initial-support and handling scope, missing observations, gravity-relative falling,
partial negative coverage, aggregation precedence and schema/example limitations.
The analytical event definitions and V4 acceptance matrix are **planned tests**;
they were not executed. JSON conformance is not physical validation, adapter
certification, calibration or scientific approval. All D01–D11 remain pending.

Local preservation check: no tracked changes outside the new Phase 1 directory
relative to the exact baseline. Only new specification and QA files are committed.
No V2/V3 implementation, references, predictions, recordings or safeguards changed.
