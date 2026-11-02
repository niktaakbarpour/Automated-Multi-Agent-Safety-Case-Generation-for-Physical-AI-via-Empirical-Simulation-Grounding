# Retrieval validation

6,468 exact source-target queries; 6,272 include literal FTS5 text. Targets are checked against original source paths, hashes and selectors before search. Aggregate Precision@1=1.0, Recall@20=1.0, MRR=1.0; correct source attribution=1.0.

| Task | Queries | P@1 | R@20 | MRR |
|---|---|---|---|---|
| object/task_01 | 1617 | 1.0 | 1.0 | 1.0 |
| object/task_03 | 1617 | 1.0 | 1.0 | 1.0 |
| object/task_05 | 1617 | 1.0 | 1.0 | 1.0 |
| object/task_09 | 1617 | 1.0 | 1.0 | 1.0 |

196 out-of-range frame queries check 1176 measurement-type gaps. 196 cases verify development/expansion isolation. Automated tests cover wrong task/object IDs, unsupported geometry and camera alignment, capability rejection and deterministic repeated queries. Query fixtures are metadata/source-target relevance judgments, never physical labels.

## Optional paraphrase comparison

| Method | Queries | P@1 | R@20 | MRR | Median seconds |
|---|---|---|---|---|---|
| fts5 | 144 | 0.083333 | 0.083333 | 0.083333 | 0.000338 |
| semantic | 144 | 0.916667 | 1.0 | 0.958333 | 0.065455 |

Source-field paraphrase probes over six valid measurement candidates, metadata constrained. Descriptions use source field semantics; hand-written templates, not independently human-labeled natural queries or physical safety understanding. Recall@20 is weak with only six candidates.

There are 12 unique hand-written query texts repeated across 12 task/execution scopes; these are controlled source lookups, not 144 independent semantic relevance cases.

| Task | Method | P@1 | R@20 | MRR |
|---|---|---|---|---|
| object/task_01 | fts5 | 0.083333 | 0.083333 | 0.083333 |
| object/task_01 | semantic | 0.916667 | 1.0 | 0.958333 |
| object/task_03 | fts5 | 0.083333 | 0.083333 | 0.083333 |
| object/task_03 | semantic | 0.916667 | 1.0 | 0.958333 |
| object/task_05 | fts5 | 0.083333 | 0.083333 | 0.083333 |
| object/task_05 | semantic | 0.916667 | 1.0 | 0.958333 |
| object/task_09 | fts5 | 0.083333 | 0.083333 | 0.083333 |
| object/task_09 | semantic | 0.916667 | 1.0 | 0.958333 |

No templates, descriptors or model weights were tuned to safety outcomes. Source retrieval metrics do not measure semantic generalization, event recognition, R1 correctness or safety. See raw result JSON for every failure and rank.

## Additional temporal-source validation

1568 additional queries cover middle frames, terminal frames and 31/32 window boundaries. Precision@1, Recall@20, MRR and source attribution are all 1.0 for every task. Each task contributes 392 additional queries, giving 2,009 per task and 8,036 source-target queries in total. Another 196 missing-normal queries and 196 wrong-task queries preserve missingness and isolation. These remain saved-frame source checks, not continuous physical coverage.
