# Retrieval evaluation

69 deterministic development queries, 65 using text. Relevance targets are source-document or measurement selectors, not physical safety annotations. Targets cover all four executions, task instructions, all five objects, known pose/contact windows and the shared task instruction. QUERY_FIXTURES.json records exact expected stable IDs. Native reader regressions independently validate source structure.

Precision@1: 1.000000; Recall@1: 0.989130; Recall@20: 1.000000; MRR: 1.000000. Precision of actually returned results up to 20: 1.000000 (denominator is actual returned count, not fixed 20). One instruction query has four relevant documents, explaining Recall@1 below one. All returned source path/hash/selector triples match the expected registered target metadata. Repeated queries serialize identically.

Four directly specified terminal-frame gap cases pass, for both pose and contact, even with output limit 1. Gap reporting uses all valid matching windows, not top-k output only. Synthetic negative tests additionally cover missing/changed sources, wrong identities, validity/capability restrictions, dependencies, conflicts, migration, rollback and resume markers. No synthetic-only success is called empirical retrieval effectiveness.

These are purposive, largely exact/filter-constrained source lookups on one development task. They do not establish unseen paraphrase, semantic reasoning, broad-corpus retrieval quality, physical-event correctness, safety accuracy or certification. No frozen outcomes are used as relevance labels. Metrics and complete per-query results appear in validation/RETRIEVAL_METRICS.json.
