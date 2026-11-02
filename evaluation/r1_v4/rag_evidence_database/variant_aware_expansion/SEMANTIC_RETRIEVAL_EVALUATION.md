# Optional local semantic retrieval

| Method | Query instances | P@1 | R@20 | MRR | Median seconds |
|---|---|---|---|---|---|
| fts5 | 1764 | 0.083333 | 0.08333333333333333 | 0.083333 | 0.067856 |
| semantic | 1764 | 0.935374 | 1.0 | 0.967687 | 0.107586 |

The unchanged Phase5E pinned local encoder is reused. There are
12 unique fixed linguistic probes,
7 object names, 147 execution
contexts and 98 verified new variants. Objects rotate by a
frozen episode-modulo rule; probes/descriptors/model are not tuned on results.
Query instances are not independent linguistic relevance judgments. Recall@20
has only six candidates. Metrics are not physical-event or checker accuracy.

All returned rows retain exact execution/task/object/variant provenance.
441 scope controls plus6
additional controls cover wrong variant/execution/task, absent timestamps,
unsupported spatial fields, unindexed and excluded scopes. Invalid cross-scope
returns=0. A registry document not embedded in the sidecar is explicitly
unindexed for semantic retrieval and is not returned as evidence. Phase5E's
original sidecar and 16 compatibility tests still pass against its original DB.

Full per-task/per-variant results, failures and ranks are in validation/. The
sidecar is separate from the source-of-truth SQLite database, uses metadata
filtering first and preserves all physical capability blocks. No external
embedding API, LLM drafting, RAG safety labels or agent orchestration is used.
