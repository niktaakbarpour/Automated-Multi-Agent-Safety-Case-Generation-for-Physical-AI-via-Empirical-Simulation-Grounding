# Regressions and preservation

718 automated tests passed, with no unexplained failures/skips. Includes 521 inherited Phase 5F tests, 57 Phase 5G, 87 Phase 5H and new Phase 5I tests. Details and frozen verification: REGRESSION.json and regressions/qa.

PRESERVATION.json compares every Phase 5H table definition and ordered row, including FTS backing tables, source associations, contracts and variants. Baseline SHA-256: af8265755a8f4f1a360c6b39b99bf6ccd45a7313d9e6adf33b89acff7b67fb02. Earlier releases remain untouched. Reserved/excluded/pending rows are preserved and negative-tested.

REBUILD_RESUME.json verifies a fresh logical rebuild, full resume over 432 jobs and partial resume after deleting one execution's new scoped rows in scratch. Digests agree: 909a6d882a2a0bce364e265063d08df578e7323ca3e3a651e416153d39c50ddc. Original tables are never rewritten.

Initial SQL-placeholder, benchmark-module import and missing test-output-directory failures are preserved in initial_failed logs. Intermediate preclosure/preproducer/preassociation databases/logs preserve diagnostic history. These implementation diagnostics were corrected before final validation without source modification or contract relaxation. Git later flagged CSV CRLF line endings; explicit LF generation passed, and CSV_FORMAT_VALIDATION.json proves only line endings changed.
