# Two-check completeness and migration

Use obligation_preservation.retrieve.Retriever with the existing BundleRequest. Historical K API remains unchanged; callers must migrate explicitly. Database/catalogue stay read-only/pinned, with source/variant/assurance constraints enforced.

COMPLETE requires (1) independent preservation of every mandatory original obligation and (2) verified fulfillment of every mandatory obligation. Missing families, changed selector attachments or unknown content cannot be excused by a reduced plan. Each source retains separate temporal coverage; no simultaneity, interpolation or shifting.

Statuses: COMPLETE WITHIN VERIFIED CONTRACT, PARTIAL, AMBIGUOUS, UNAVAILABLE, UNSUPPORTED, INVALID SCOPE, and new UNVERIFIED PLAN. Separate obligation_preservation/evidence_fulfillment results and unsatisfied IDs are exposed. No status means safety sufficiency.

UNVERIFIED PLAN may carry identified verified raw data only for residual-content uncertainty under verified_source_values. It is labelled inspection_only, assurance_satisfied_for_original_request=false and fulfillment=false. The original request is not accepted as answered. Explicit reduced plans, ambiguous selectors, unsupported physical/strict assurance requests and wrong scopes get no fallback. Consumers must not infer completeness from items. Hard typed scopes/source checks remain mandatory.

PARTIAL may carry comparison operands or explicitly requested raw values with an unsupported transform; the comparison/interpretation stays unsatisfied. No comparison answer, support/contact/safety judgment or escalation is produced. Conditional cache/native/SI distinctions remain inherited. Recorded labels associate samples, not shared physical instants.

Old fields remain; obligations/gates and UNVERIFIED PLAN require compatibility changes. Default verification stays strict; evaluation explicitly uses verified_session with identity invalidation. Empirical admission and safety_claim_verified remain false.
