# Performance and resources

Primary build elapsed 402.218 seconds for 196 additional executions; 0.487 executions/s, 67.933 saved frames/s and 112.531 new records/s. This includes baseline copying, source validation, reader work and final snapshot; cache conditions affect repetition.

Validation-process peak RSS: 2,017,952 KiB; address-space cap 8,589,934,592 bytes. Indexing holds one execution at a time; export/integrity QA reads the compact registry in memory. Source binaries remain outside SQLite.

Structured/FTS latency seconds: `{'max': 0.21388596948236227, 'median': 0.13595928438007832, 'p95': 0.15488468576222658}`. These include fresh source/dependency validation, not just SQL. Database: 401,522,688 bytes. Optional sidecar: 14,614,528 bytes, 66 unique descriptor vectors and 61,788 evidence aliases.

Restored source footprint: 15,487,193,491 bytes across 1,772 files. Initial disk1 available space was 1,653,112,385,536 bytes; RESOURCE_CHECK.json records a fresh subsequent check. Disk0 had a pre-existing reserve shortfall; no cleanup or large disk0 writes were performed. Alliance performed archive storage retrieval only. No GPU inference, physics execution or new simulations were used.
