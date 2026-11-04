# Development and frozen assessments

Development-only results (72 new instances, plus separate original-36 diagnostics):

| Mode | N | P@1 | R@5 | R@20 | MRR | Complete multi-source |
|---|---:|---:|---:|---:|---:|---:|
| exact | 48 | 0.542 | 0.564 | 0.569 | 0.594 | 0/8 |
| lexical | 48 | 0.208 | 0.319 | 0.319 | 0.275 | 0/8 |
| semantic | 48 | 0.396 | 0.569 | 0.569 | 0.489 | 0/8 |
| field_single | 48 | 1.000 | 0.799 | 0.799 | 1.000 | 0/8 |
| hybrid_single | 48 | 0.917 | 0.715 | 0.715 | 0.917 | 0/8 |
| bundle | 48 | 1.000 | 1.000 | 1.000 | 1.000 | 8/8 |

The full planner/family fetching completed 8/8 development multi-source cases; field_single and hybrid_single completed 0/8. These share the proposal layer and isolate independent family execution. Hybrid is a bounded one-family ranking experiment, not a full hybrid baseline; it did not improve development accuracy. No learned thresholds or post-holdout vocabulary changes.

V2 on the common channel-only subset, supported by the unchanged Phase 5I primary endpoint:

| Mode | N | P@1 | R@5 | R@20 | MRR | Complete multi-source |
|---|---:|---:|---:|---:|---:|---:|
| exact | 72 | 0.958 | 0.979 | 1.000 | 0.973 | 6/6 |
| lexical | 72 | 0.458 | 0.701 | 0.708 | 0.572 | 6/6 |
| semantic | 72 | 0.819 | 0.993 | 1.000 | 0.903 | 6/6 |
| field_single | 72 | 1.000 | 0.944 | 0.944 | 1.000 | 0/6 |
| hybrid_single | 72 | 1.000 | 0.944 | 0.944 | 1.000 | 0/6 |
| bundle | 72 | 1.000 | 0.993 | 1.000 | 1.000 | 6/6 |

All eligible V2 obligations, including metadata/geometry/reference families:

| Mode | N | P@1 | R@5 | R@20 | MRR | Complete multi-source |
|---|---:|---:|---:|---:|---:|---:|
| exact | 136 | 0.544 | 0.582 | 0.610 | 0.595 | 6/24 |
| lexical | 136 | 0.316 | 0.439 | 0.445 | 0.409 | 6/24 |
| semantic | 136 | 0.544 | 0.607 | 0.610 | 0.618 | 6/24 |
| field_single | 136 | 1.000 | 0.835 | 0.835 | 1.000 | 0/24 |
| hybrid_single | 136 | 1.000 | 0.835 | 0.835 | 1.000 | 0/24 |
| bundle | 136 | 1.000 | 0.985 | 0.989 | 1.000 | 24/24 |

The broad baseline rows deliberately call the existing six-channel endpoint without adding routing/decomposition; they cannot answer every new family. They are endpoint-coverage diagnostics, not evidence that the complete historical system has these aggregate accuracies. Use common-channel rows for a fair field-retrieval comparison. Existing exact baseline receives oracle channel IDs for single-family requests and oracle frame windows; improved retrieval parses natural language. Original full legacy/physical interfaces are separately replayed in HISTORICAL_5J_COMPARISON.md.

Metrics rank distinct required families, not historical record IDs or generated answers. P@1 can be 1.0 while another requested family is omitted. C2-2 demonstrates that limitation. Every case remains in its predefined denominator.
