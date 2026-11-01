# Observed performance and scale limits

Database size: 14,622,720 bytes (13.95 MiB), including the 2,000-entry catalog. Measured first-build time: 17.875 s; 76.08 evidence units/s including source verification and catalog population. Peak process RSS: 440,040 KiB; this includes the validation driver's inventory/protection work and is not isolated reader memory. CLI address-space cap is 4 GiB. No GPU was used.

69 first-pass queries: median 109.65 ms, p95 215.62 ms, maximum 218.11 ms. Within-request source hash deduplication is used; OS filesystem caches may be warm. These are local source/filter queries, not a cold-cache or large-corpus latency guarantee. Repeat results are byte-stable.

One execution is processed at a time; 32-frame units avoid per-frame text duplication. Search caps at 10,000 candidates, requiring metadata narrowing for scale. FTS and source-reference metadata are compact; binaries stay outside SQLite. Source rehashing is intentionally part of retrieval correctness and can dominate latency for broad multi-execution queries.

A planning extrapolation at the observed four-execution evidence density is about 340 units/execution: roughly 680,000 units for 2,000 executions, or about 5.22 million for 15,361 trajectory identities before deduplication. Evidence-only storage extrapolations are order-of-gigabytes to tens-of-gigabytes, not measured scale results; recorder/frame counts and model schemas differ. Do not extrapolate observed accuracy or latency. Broader raw payloads total 2.77 TB, exceeding current free disk1 capacity; no bulk restore is attempted. The 5.02 GB selective development plan is the next bounded data increment, subject to reader validation.
