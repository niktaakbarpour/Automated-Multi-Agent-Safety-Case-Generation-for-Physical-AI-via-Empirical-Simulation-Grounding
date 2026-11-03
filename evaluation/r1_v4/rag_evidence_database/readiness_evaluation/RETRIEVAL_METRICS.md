# Retrieval results

Final assessment: 162 unique questions, 18 per category, 486 case-mode instances. IR metrics apply to the 96 questions with a predefined nonempty relevance set and no required abstention; unsupported/ambiguous cases are not assigned fictitious zero relevance. Required-facet coverage and negative controls have separate denominators.

| Mode | IR n | P@1 | R@5 | R@20 | MRR |
|---|---:|---:|---:|---:|---:|
| exact | 96 | 0.958 | 0.985 | 1.000 | 0.975 |
| lexical | 96 | 0.385 | 0.592 | 0.613 | 0.473 |
| semantic | 96 | 0.792 | 0.884 | 0.896 | 0.855 |

Exact is a manually structured diagnostic, not a natural-language parser. Channel NL ranking sees six candidates within supplied execution/task/variant/temporal constraints, without positive target-channel labels. Legacy geometry/document questions use the existing variant-aware endpoint and frozen explicit family/object scopes; these are different supported interfaces. No hybrid implementation exists or was added.

| Category | Mode | IR n | P@1 | R@5 | R@20 | MRR | Complete / 18 | Correct / required abstentions |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | exact | 18 | 1.000 | 1.000 | 1.000 | 1.000 | 18 / 18 | 0 / 0 |
| C1 | lexical | 18 | 0.444 | 0.778 | 0.778 | 0.569 | 14 / 18 | 0 / 0 |
| C1 | semantic | 18 | 0.833 | 1.000 | 1.000 | 0.881 | 18 / 18 | 0 / 0 |
| C2 | exact | 15 | 1.000 | 1.000 | 1.000 | 1.000 | 15 / 18 | 3 / 3 |
| C2 | lexical | 15 | 0.400 | 0.667 | 0.667 | 0.513 | 10 / 18 | 3 / 3 |
| C2 | semantic | 15 | 0.733 | 0.933 | 0.933 | 0.811 | 14 / 18 | 3 / 3 |
| C3 | exact | 12 | 1.000 | 1.000 | 1.000 | 1.000 | 12 / 18 | 4 / 4 |
| C3 | lexical | 12 | 0.000 | 0.000 | 0.000 | 0.000 | 0 / 18 | 4 / 4 |
| C3 | semantic | 12 | 1.000 | 0.500 | 0.500 | 1.000 | 11 / 18 | 4 / 4 |
| C4 | exact | 18 | 0.778 | 0.968 | 1.000 | 0.866 | 10 / 18 | 0 / 0 |
| C4 | lexical | 18 | 0.667 | 0.833 | 0.889 | 0.741 | 8 / 18 | 0 / 0 |
| C4 | semantic | 18 | 0.889 | 0.981 | 1.000 | 0.944 | 10 / 18 | 0 / 0 |
| C5 | exact | 0 | N/A | N/A | N/A | N/A | 0 / 18 | 18 / 18 |
| C5 | lexical | 0 | N/A | N/A | N/A | N/A | 0 / 18 | 18 / 18 |
| C5 | semantic | 0 | N/A | N/A | N/A | N/A | 0 / 18 | 18 / 18 |
| C6 | exact | 8 | 1.000 | 1.000 | 1.000 | 1.000 | 6 / 18 | 10 / 10 |
| C6 | lexical | 8 | 0.375 | 0.625 | 0.625 | 0.479 | 3 / 18 | 10 / 10 |
| C6 | semantic | 8 | 0.500 | 0.750 | 0.750 | 0.604 | 4 / 18 | 10 / 10 |
| C7 | exact | 8 | 1.000 | 0.896 | 1.000 | 1.000 | 7 / 18 | 10 / 10 |
| C7 | lexical | 8 | 0.250 | 0.354 | 0.354 | 0.312 | 3 / 18 | 10 / 10 |
| C7 | semantic | 8 | 0.750 | 0.771 | 0.875 | 0.812 | 7 / 18 | 10 / 10 |
| C8 | exact | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1 / 18 | 16 / 16 |
| C8 | lexical | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1 / 18 | 16 / 16 |
| C8 | semantic | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1 / 18 | 16 / 16 |
| C9 | exact | 16 | 1.000 | 1.000 | 1.000 | 1.000 | 15 / 18 | 2 / 2 |
| C9 | lexical | 16 | 0.312 | 0.562 | 0.625 | 0.427 | 9 / 18 | 2 / 2 |
| C9 | semantic | 16 | 0.688 | 1.000 | 1.000 | 0.792 | 15 / 18 | 2 / 2 |

Completeness columns retain raw frozen-rubric output. C7-20 has an invalid superseded facet; use the separate validity overlay for C7 completeness/sufficiency (17 valid final C7 questions). IR relevance labels, all 96-question ranking denominators and factual/source audits are unaffected.

All case-level values, source bindings, ranking lists, unsupported statuses and missing facets are in RETRIEVAL_RESULTS.jsonl. Source association correctness uses the frozen registry binding map; numeric/geometry factual answers use independently inspected original artifacts. Per-category N/A means IR is not defined, not perfect or zero accuracy.

Suite-stratified execution-cluster bootstrap intervals (2,000 replicates) are in METRICS.json. They describe resampling these selected execution clusters, not population coverage, human relevance judgments or independent linguistic sampling. The final questions share 18 execution contexts. Repeated model modes are never pooled as independent observations. No universal zero-error guarantee follows from the observed zero attribution errors.

Independent audit of all returned final records/samples (separate from relevance): `{"execution_id_checks": 961, "numeric_components": 14897, "object_id_checks": 36, "raw_samples": 2972, "recorded_clock_checks": 65, "returned_records": 961, "saved_index_checks": 2907, "source_association_checks": 961, "task_id_checks": 961, "unit_checks": 2972, "variant_id_checks": 961}`. All source/execution/task/variant/object, numeric, unit and checked temporal errors were zero. This does not validate a common physical sensor instant.

| Mode | P@1 interval | R@5 interval | R@20 interval | MRR interval |
|---|---|---|---|---|
| exact | 0.924–0.989 | 0.979–0.992 | 1.000–1.000 | 0.956–0.993 |
| lexical | 0.311–0.451 | 0.521–0.661 | 0.545–0.676 | 0.425–0.524 |
| semantic | 0.716–0.862 | 0.853–0.915 | 0.863–0.926 | 0.798–0.905 |
