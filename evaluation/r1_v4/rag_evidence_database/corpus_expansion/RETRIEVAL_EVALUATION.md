# Final Phase 5D retrieval evaluation

1617 independently specified source-target queries cover all 49 new executions, seven objects, task instructions, metadata, poses, contacts, geometry, robot state, timestamps and camera references. 1568 include literal text. Expected relevance is a specific registered source path/hash/selector and temporal scope, not a physical event. Queries use the explicit corpus_expansion stratum.

Precision@1: 1.000000; Recall@20: 1.000000; MRR: 1.000000; source attribution correctness: 1.000000. Every positive target has one relevant window/document. Repeated responses serialize identically. Forty-nine terminal-gap cases check all six types (294 checks); top-k truncation does not truncate coverage. Forty-nine stratum-isolation queries return no new-task data under development.

Latency: median 77.68 ms, p95 85.63 ms, maximum 151.19 ms. Source hashes are freshly verified per request; OS file caches may be warm. These are local, filter-constrained lookup measurements, not cold-cache/large-corpus guarantees or a general paraphrase benchmark.

No safety outcome labels tune queries. The benchmark is source retrieval, not physical safety accuracy, empirical fall effectiveness or certification. Negative source/role/version/conflict cases are covered by regressions. Existing keyword/paraphrase limitations remain; no semantic embeddings or hosted API are introduced. Full fixtures and results are under task_profile/validation/.
