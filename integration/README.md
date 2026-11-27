# One-pass Drafter to Critic handoff

## R1 v3

The adapter selects `critic-request/r1v3/0.1.0` for the Drafter's R1 v3 request.
It preserves the original source package and accepted generation report, including
all five GSN graphs, the outcome backing and the decoder and host validation trace.
It checks the saved completion against the full plan schema and replays its
serialization on CPU. The sidecar records canonical hashes of the exact inputs
and GSN bundle.

Use the original R1 v3 request and the accepted report from the same run.
The handoff rejects evaluation-only reference fields and file paths. The original
source package retains its note about the excluded reference.

```python
from critic import review
from evaluation.r1_v4.provenance import load
from integration.handoff import build_critic_request

request, provenance = build_critic_request(load(request_file), load(saved_generation_report))
report = review(request)
```

An exported R1 v3 Critic request also works with `python3 -m critic --request FILE`
for a deterministic review without independently admitted Checker inputs.

To supply Checker evidence, pass `checker_assessments=[{"request": checker_request,
"assessment": assessment}]` to the adapter. Call `review` with the host's
`source_root`, open `RegistryV3` instance as `registry`, `task_id` and independently
approved `trusted_review_hashes`. The Critic checks exact identity and frame
scope, then reproduces each assessment through the
[Checker admission contract](../evaluation/r1_v4/checker_v3_admission/README.md).
The report keeps the complete reproduced assessment and its gate and evidence
ledgers. Blocked assessments have no conclusion. Conflicts stay open for review.

The R1 v3 route runs deterministic checks only. A requested model backend is
reported as unavailable. The GSN's reasoning review remains required, and
`safety_claim_verified` stays false. The adapter does not run Revision.

Run the R1 v3 tests from the repository root with `requirements-m4-cpu.lock`.

```sh
python3 -m unittest integration.tests.test_r1v3_handoff critic.tests.test_r1v3_assessments
```

## R1 v2

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
