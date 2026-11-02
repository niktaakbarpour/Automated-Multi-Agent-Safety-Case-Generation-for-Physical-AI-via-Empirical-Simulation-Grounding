# Remaining corpus expansion

The project inventory remains 2,000 executions. After this batch, 1,715 lack indexed measurements: 60 reserved evaluations, 38 historical preflight exclusions and 1,617 database-only candidates across 33 unprofiled tasks. All have catalog metadata; archive mappings are not fresh file validation.

The remaining nine-file candidate footprint is estimated at 122,776,362,497 bytes, excluding shared task/initial-state files, transient staging, databases and diagnostics. Eight remaining tasks have a single XML identity; 25 have multiple XML variants and need explicit variant-level compatibility validation. None is automatically reader-compatible.

The next reproducible single-XML candidates are `object/task_07`, `object/task_04`, `object/task_00`, `object/task_08`. A future separately authorized batch can validate these profiles, exclude their episode000 preflights, and restore up to 196 executions. Do not begin it in Phase5E. Multi-XML tasks require per-variant native mappings and array/identity checks, not reuse of one scene map.

Current database bytes per execution are 1408852; this is only a rough storage projection because objects, frame counts and task descriptions vary. Estimate future indexing time from validated-task frame counts and measured throughput, then check free space before restoration. Reserve at least 500 GB where feasible. All 2,000 executions cannot be made development data: reserved evaluations require a separate read-only partition and explicit authorization, with no retrieval tuning on safety references.
