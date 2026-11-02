# Retrieval and assurance

Phase 5I: 7776 positive assurance/recorded-clock queries; 22304 negatives; 5184 independent raw comparisons; maximum/mean numeric error 0; recorded-label alignment errors 0; leakage 0. These are source checks, not safety accuracy.

Phase 5H rerun: 12960 exact queries, 35264 negatives, P@1/R@20/MRR all 1.0. Wrong execution/task/variant/source/field/object/unit/frame/alignment/status and excluded/reserved/pending IDs fail before results.

Optional semantic benchmark: 12 unique formulations repeated across 432 scopes. Metrics: `{"fts5": {"MRR": 0.7526041666666666, "instances": 5184, "precision_at_1": 0.6238425925925926, "recall_at_20": 0.9166666666666666}, "semantic": {"MRR": 1.0, "instances": 5184, "precision_at_1": 1.0, "recall_at_20": 1.0}}`. Negatives: 5456, leakage 0. Repeated contexts are not independent linguistic cases. Phase 5F/G reruns are under legacy_f/legacy_g.

ASSURANCE_VALIDATION.json contains strict/session, physical and provenance timings under concurrent validation load, not stable throughput estimates. Stronger provenance pays hashing costs without relaxing checks. Semantic similarity cannot override scope or assurance gates.
