# One-pass Drafter to Critic handoff

`build_critic_request(original_drafter_request, accepted_generation_report)` returns
an independently copied Critic request and provenance sidecar. It validates the
Drafter request/report/argument, binds the original request hash and runs existing
Critic input checks. It performs no inference, retrieval, checker assessment or
argument revision. Agent implementations and frozen contracts are unchanged.

The argument bundle, full R1 configuration, execution identities, original registry
records, checker entries and exact Phase5 request/bundle pairs are copied intact.
Both monitoring boundaries must currently be explicit indices. Non-explicit source
boundary certificates require a separately validated adapter; no certificate is
inferred from free-form prose.

The Critic envelope cannot represent the full Drafter retrieval/review envelopes.
The sidecar retains both verbatim. The exact original retrieval context is also
encoded as attributed canonical JSON in Critic retrieval limitations, visible in
its model prompt. Original gaps without measurement_type are not assigned an
invented type: they remain in that lossless context, while only already-typed gaps
are copied into the Critic's typed gap list. Structured request/bundle pairs remain
in the native Critic structured_evidence field; its existing compact model view
need not include all source values. This distinction must remain visible when
interpreting evidence-aware semantic criticism.

Unknown registry-export completeness is represented conservatively as false,
never promoted from narrower Phase5 mandatory-obligation completeness. Requested
families are copied from explicit structured obligations if no original requested
measurement list exists. Analytical test_fixture classification is retained; it
does not change genuine retrieved source values into fabricated observations.
Model review text and warnings remain in the sidecar; the original warning is
also carried to Critic limitations. A valid handoff says nothing about physical
safety, calibration, empirical checker admissibility or model reasoning quality.

Run tests on Hestia with:

```bash
python -m unittest integration.tests.test_handoff -v
```

Tests use explicitly scripted/synthetic fixtures, not real model responses. Actual
one-pass experiment commands and raw traces are stored separately from Git.
