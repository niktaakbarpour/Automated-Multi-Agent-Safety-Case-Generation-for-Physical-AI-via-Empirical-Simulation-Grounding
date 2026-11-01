# Retrieval evaluation

825 source-target queries (785 with text): 681 queries over all 40 executions plus 144 geometry/robot/timestamp/camera queries on the new 36. Expected relevance is source path/hash/selector correctness, not physical truth. Exact execution/task/object/interval scopes, pose-versus-contact and repeated serialization are tested.

Precision@1 1.000000; Recall@1 0.998818; Recall@20 0.999394; MRR 1.000000. All returned results are source-relevant. The shared instruction query has 40 relevant documents; top-20 recall for that query is necessarily 0.5, explaining macro recall below one. No threshold is tuned to safety labels.

All source attribution triples match expected targets. Forty terminal-frame gap cases pass for pose and contact even at output limit 1; coverage uses all valid matching windows. Synthetic negative tests cover corrupt/missing sources, invalidity, dependencies, conflicts and identity/version mismatch. These are not safety accuracy metrics.

Main query latency: median 110.53 ms, p95 132.02 ms. Additional queries: median 116.31 ms, p95 131.49 ms. Filesystem caches may be warm; these are local measurements, not scale guarantees.

Five paraphrase probes miss under literal FTS while keyword/metadata forms find the targets. General natural-language discovery is not established. SEMANTIC_RETRIEVAL_ASSESSMENT.md designs an optional versioned local index; no embedding implementation/comparison is claimed. Held-out safety outcomes are not retrieval relevance labels.
