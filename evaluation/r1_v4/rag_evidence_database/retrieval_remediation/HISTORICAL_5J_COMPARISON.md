# Exposed historical comparison, not generalization evidence

After both implementation freezes, the unchanged original full Phase 5J target was replayed once: 162 questions / 486 mode instances, using read-only old database/index/contracts with all outputs/scratch redirected to Phase 5K. Frozen historical artifacts/labels were not changed. Original record-ID relevance:

| Original mode | N | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| exact | 96 | 0.958 | 0.985 | 1.000 | 0.975 |
| lexical | 96 | 0.385 | 0.592 | 0.613 | 0.473 |
| semantic | 96 | 0.792 | 0.884 | 0.896 | 0.855 |

The original reported exact/semantic/lexical completeness was 10/18, 10/18, 8/18. C7-20's invalid completeness annotation remains invalid; no historical output/label was rewritten. The source-target record ranking metrics remain distinct from K family-obligation metrics.

One corrected-bundle historical comparison covers 162 questions and saves case outcomes, unmapped old obligations and the invalid annotation flag in HISTORICAL_5J_COMPARISON_RESULTS.json. Mapped-family success is not a replacement score for unmapped obligations; no apples-to-oranges claim of historical completeness improvement is made. All 486 old final diagnostics are in HISTORICAL_FAILURE_TAXONOMY.json. The exposed cases did not select retrieval rules, thresholds, prompts or rankings. New scope assessments, not this comparison, support the reported remediation results.
