# Restricted V4 readiness assessment

Current status: **not authorized to begin implementation**. No decision is approved
by this review; no V4 code exists in the package. Scientifically blocked profiles
remain blocked even if structural design is accepted.

| Gate | Recommendation / readiness | Required next evidence or approval |
|---|---|---|
| R0 Design dispositions | All actual D01–D11 reviewed with subdecisions. | User accepts/changes each recommendation, explicit exclusions and bounded first scope. |
| R1 Normative consistency | Exact proposed amendments supplied, not applied. | Approve amendments; integrate and revalidate specification/schema/test expectations in a subsequent authorized change. |
| R2 Pure software contracts | Ready for restricted work after R0/R1 and implementation authorization. | Configuration, IDs, typed object outcomes, scoped diagnostics, aggregation and coverage algebra; no physical claims. |
| R3 Analytical fixture profile | Design ready, physical implementation/tests not run. | Known-truth fixtures for supported BOX geometry and contract failures; separate synthetic fixture producer from empirical adapter. Sphere fixtures remain unsupported until capability exists. |
| R4 LIBERO evidence reader | Schema knowledge exists; not empirically certified. | Exact recorder/model/XML/schema binding, source hashes and temporal/geometry validation; source processing on Hestia only. |
| R5 Empirical witness profiles | BLOCKED_ON_EVIDENCE where required support, geometry or phase validity is absent. | Resolve G01–G07/G09 in the evidence ledger. Admission is claim-specific, not all-or-nothing by benchmark name. |
| R6 New empirical evaluation | BLOCKED_ON_EVIDENCE and separate authorization. | Natural/controlled protocol, independent applicable positive/negative references, locked splits/metrics (G08). |

Recommended first implementation milestone, **after** approval and specification
amendment: configuration and output contracts, explicit profile capability admission,
applicability/aggregation/coverage bookkeeping against analytical inputs, tamper/replay
tests and frozen-history preservation. It may produce deliberately unknown/IC
empirical outcomes; inability to classify is not a reason to relax the contract.
No threshold-enabled detector or generalization claim is part of this milestone.

Use the existing [V4 plan](../V4_IMPLEMENTATION_PLAN.md) modules, without creating
them now: configuration/contracts, adapters and identity/geometry/time admission,
support/events/scope, coverage/assessment/aggregation, provenance/CLI. Physical
profiles enter only through independent admission records. No model/LLM makes
protected-set selection or supplies substitute measurements.

Required planned test additions to [V4_TEST_MATRIX.md](../V4_TEST_MATRIX.md):

- DR01: two distinct aliases resolving to one body rejected; verified absence
  preserves object NA but can invalidate intended study eligibility.
- DR02: static designated union versus moving-root IC; local handoff ambiguity U;
  another object's supported static root remains evaluable.
- DR03: terminal-censored departure and falling phase straddling t1 cannot produce
  a negative; a prior valid positive survives later re-placement ambiguity.
- DR04: malformed config returns assessed=false and null assessed outcomes, distinct
  from an assessed object's IC.
- DR05: overlapping same-source exports do not double coverage or independent
  evidence counts; incompatible clocks or uncovered transition cells block merging.
- DR06: shared-foundation contradiction suspends positive admission; unrelated optional
  missing camera does not. Majority vote never resolves the conflict.
- DR07: profile/version/calibration scope mismatch refuses admission, despite valid
  JSON and certificate hashes; synthetic conformance cannot self-certify empirical use.

These are planned tests only. No new recording, simulator run, V4 test execution,
RAG database, multi-agent code or dataset expansion is performed in Phase 1.5.
