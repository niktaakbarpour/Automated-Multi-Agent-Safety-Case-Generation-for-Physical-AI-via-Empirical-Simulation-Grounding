# Phase5F: variant-aware RAG evidence expansion

Completed database-only milestone: 147 new executions,
98 new environment variants; 432
executions and 80,786 records in total. No empirical R1
admission, new checker, safety-case generation or multi-agent implementation.

Start with INVENTORY.md, COHORT_SELECTION.md, SCHEMA_AND_PROVENANCE.md and
COVERAGE_MATRIX.csv. Source/task/variant relations are in VARIANT_REGISTRY.csv
and EXECUTION_VARIANT_RELATIONS.csv. RETRIEVAL_EVALUATION.md and
SEMANTIC_RETRIEVAL_EVALUATION.md explain metrics and limitations.
REGRESSION_RESULTS.md, validation/ and ARTIFACT_MANIFEST.json preserve checks.
REPRODUCIBILITY.md gives exact paths/procedures; LIMITATIONS.md records gaps.

Database: `/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite`
Bytes: 491,192,320
SHA-256: `a0f9347db719902f275d0f3e89f0682f093d5ded858ab7c2823067930337baa9`

The Phase5E baseline remains `/disk/1/data/niktakbr/trustworthy-phase5e-working/final-validated/corpus-285.sqlite` at `5d3eb7589ddbf564cf29189af3264fd9861df44780e65e3246b62bbe74bc9934`.
All 67,053 old records and their original index rows remain intact. The exact
baseline reader code remains in commit114f1f6540a6ba182606a2a921af131ad6b0f7d3;
Phase5F adds its closed dispatch on a new branch without rewriting the old seal.
