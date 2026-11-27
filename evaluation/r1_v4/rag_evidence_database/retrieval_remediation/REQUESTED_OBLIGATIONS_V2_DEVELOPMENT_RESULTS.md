# Requested-obligation v2 development comparison

This is a planner-only regression comparison on the exposed, frozen 216-row
RQ1 corpus (72 repeated wording templates across the corpus). It is not a new
independent evaluation and does not modify the frozen dataset, saved results,
or historical reports. Reproduce it with:

```sh
python -m evaluation.r1_v4.rag_evidence_database.retrieval_remediation.evaluate_obligations_v2
```

| Planner | Expected-family omissions | False-complete plans | Plan outcome |
|---|---:|---:|---|
| Frozen planner v1 | 3/216 | 3/216 | Omitted joint position for the same temporal-label wording template |
| Requested-obligations v2 | 0/216 | 0/216 | 165/216 complete plans; 9/216 ambiguous; 42/216 unsupported/incomplete |

V2 recovered the missing expected family on 3/216 rows and introduced zero
expected-family regressions on this exposed corpus. 51/216 plans remain
incomplete (9 ambiguous and 42 unsupported). These three rows are
repeated scope instances of one formulation and are not three independent
linguistic failures. V2's unsupported and ambiguous counts are conservative
plan abstentions, not retrieval failures.

The authoritative historical retrieval output contains 216 bundle-mode rows.
It records 3/216 false-complete responses, exactly KH2-C2-02, KH2-C2-10, and
KH2-C2-18. Actual retrieval was not replayed under v2: that requires the
authorized private retrieval database and source artifacts. The v2 wrapper is
covered in CI with synthetic fixtures. No retrieval-level improvement number
is claimed.

No independent evaluation is available. The held-out authoring package has 60
blank query/reference slots for 30 canonical executions and no completed
independently authored query/reference pairs. A new evaluation must freeze the
corrected build first and have an independent author produce new query
formulations and evidence-derived obligation references without copying the
exposed regression cases.
