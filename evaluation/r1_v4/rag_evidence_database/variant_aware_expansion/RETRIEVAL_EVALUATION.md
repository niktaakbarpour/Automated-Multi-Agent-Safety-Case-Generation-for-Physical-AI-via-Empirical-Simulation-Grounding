# Variant-aware source retrieval evaluation

3985 prospectively fixed source-target queries passed, with
Precision@1=1.0, Recall@20=1.0 and
MRR=1.0. Source, task, execution, variant and temporal attribution
are all 1.0; invalid cross-scope returns=0. Per-task and per-variant counts/metrics
are saved in validation/RETRIEVAL_METRICS.json, with exact query samples and full
fixtures retained under the work directory. Relevance means exact original
file/hash/selector/frame-window identity, not physical safety understanding.

Initial, middle and terminal snapshots,31/32 boundaries, instructions, metadata,
object identities and all six families are tested. Old task profiles contribute
baseline metadata/raw queries; old record/index rows are preserved exactly.

1768 adversarial controls passed: wrong task, execution,
known-incompatible variant, unresolved variant, unsupported field/spatial field,
missing exposure timestamp, unresolved logical fixture, unsupported clock,
uncalibrated geometry admission and out-of-range frames. One reserved and one
preflight identifier enforce exclusions without payload/outcome inspection.
Unindexed cases and implicit comparisons are distinct statuses. Explicit shared-
variant comparison returns two separately identified executions without merging
coverage. No failed match becomes a physical negative or safety verdict.

Observed latency seconds: `{'max': 1.06181678827852, 'median': 0.19303258135914803, 'p95': 0.2192525900900364}`. These include live source,
asset and mapping validation, not SQL alone. Saved-frame availability is not
continuous physical coverage or camera alignment. There is no empirical R1
assessment, threshold optimization or safety-label tuning in this evaluation.

| Task configuration | Queries | P@1 | R@20 | MRR |
|---|---|---|---|---|
| 18573886c3dbce39b02e | 19 | 1.0 | 1.0 | 1.0 |
| 1b921c8dfd61bb78bb84 | 1274 | 1.0 | 1.0 | 1.0 |
| 2448c758145ae5ad500f | 19 | 1.0 | 1.0 | 1.0 |
| 2a5acddf5a0e33b0d470 | 1323 | 1.0 | 1.0 | 1.0 |
| 30c0f61d2d5786fae8b6 | 19 | 1.0 | 1.0 | 1.0 |
| 4013b7c5a98750b7e80d | 19 | 1.0 | 1.0 | 1.0 |
| 6da51604f02b12a90682 | 1274 | 1.0 | 1.0 | 1.0 |
| 7894e3922dc1e048d44c | 19 | 1.0 | 1.0 | 1.0 |
| b12b2d70fe80d3547b1e | 19 | 1.0 | 1.0 | 1.0 |
