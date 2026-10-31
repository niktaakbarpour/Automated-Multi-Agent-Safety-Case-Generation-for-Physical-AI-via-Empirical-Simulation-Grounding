# Exact proposed amendments — NOT APPLIED

Targets refer to the unchanged Phase 1 documents at commit
`3d235bc69d2c23bf16803cd417f51deb7bbd2d94`. Text below has no normative force
until approved and integrated coherently. Existing schema/examples stay unchanged.
No approval signature, date or identity is invented.

## A01 — Invalid configuration is not an assessed IC outcome (D05/D09)

Finding: R1-G09 says configuration failure prevents an assessed execution claim;
the final paragraph of FORMAL_SEMANTICS.md nevertheless calls it a “diagnostic IC
outcome.” This is an output-contract ambiguity, not a V3 defect correction.

Replace the sentence beginning “Configuration-invalid executions carry” in
FORMAL_SEMANTICS.md with:

> Configuration-invalid inputs are rejected before object assessment. Emit
> configuration_status=invalid, assessed=false, object_assessments=[], and
> execution_outcome=null, with configuration diagnostics. Do not encode this input
> rejection as an assessed object or execution invalid_measurement_contract outcome;
> exclude it from assessed outcome metrics and count input rejections separately.

Append to R1-G09: “Assessed IC remains reserved for an affected object's necessary
measurement contract; input rejection is reported separately.”

## A02 — Initial capability scope versus abstract union meaning (D02/D06)

Finding: R1-G02 permits validated handoffs/dynamic support in principle, and example
C requests a time-varying tray. Neither is a validated experiment. Preferred initial
scope now excludes moving/articulated surfaces and complex handoffs. This is a
proposed release restriction, not evidence that the original abstract wording failed.

Append after R1-G02:

> Initial V4 capability scope is limited to independently bound static support roots
> and supported rigid geometry. Multiple static roots across objects and explicit
> static designated unions may be configured. Moving/articulated roots, dynamic
> handoff inference and multiple-parent load solving are not admitted in the initial
> profile. Unsupported essential capabilities yield affected-object IC; an unresolved
> transition under an otherwise supported profile yields U. These restrictions do not
> change the abstract meaning of a fully qualified supported union transfer.

Append to EXAMPLE_CONFIGS/README.md:

> Example C exercises the general schema, including deferred capabilities; it is not
> admitted by the proposed restricted initial V4 profile. Example B also requests
> non-BOX capabilities outside that initial profile. Neither is a runtime test of
> empirical support. Add a separately named static two-root BOX fixture for initial
> release conformance; do not relabel the existing examples as validated.

## A03 — Terminal/boundary-censored fall episode (D03)

Finding: InInterval requires both departure and downward phase in I, while the ideal
hazard formula is compressed. Explicitly prevent a terminal-censored transition from
being read as proof of no hazard. This clarifies admissible evidence, not an invented
post-terminal event.

Append after the InInterval definition in FORMAL_SEMANTICS.md:

> A positive requires a support-departure onset bracket wholly within I and an
> admitted unsupported downward-motion witness within I. If the available onset or
> phase evidence straddles either boundary or is terminal-censored, this candidate
> is U unless other evidence resolves it; it cannot qualify negative coverage.
> Evidence outside I may narrow an in-I fact but may not manufacture an in-I falling
> phase. Departures established before t0 remain outside this initial-support scope.
> A positive already admitted elsewhere in I retains its outcome.

Keep FALL_DEFINITION.md's no minimum fall distance/duration and no floor requirement.
No extra landing or ballistic-acceleration predicate is added.

## A04 — Handling exclusion versus unresolved suffix (D04/D08)

Finding: the fall predicate excludes established lift/carry drops, while re-placement
requires abstention. Without an explicit episode boundary, an implementer might
exclude every future frame or revoke a known earlier positive.

Replace R1-G06 with:

> R1-G06: Initial applicability is fixed at t0 for this execution claim. An
> independently established lift/carry episode and its linked subsequent drop are
> separately excluded; this does not certify all subsequent frames as clear.
> Re-placement or a non-designated supported handoff introduces an unresolved
> subsequent scope domain in the initial profile. Do not re-arm applicability,
> silently add a support root, or permanently terminate all monitoring. Preserve
> an already admitted R1 fall; otherwise any unresolved relevant suffix prevents
> a whole-domain negative. A later re-arming or episode policy requires a separate
> approved version and evidence profile.

Append the same scope condition to FORMAL_SEMANTICS.md ClearCover by reference to
R1-G06; do not create a second, competing event predicate.

## A06 — Profile separation and boundary look-ahead (D06/D07)

Append to EVIDENCE_CONTRACT.md Layered contract:

> Every inference profile declares its purpose: analytical_fixture, legacy_comparison,
> or empirical_assessment. Exact analytical inputs and legacy V3 conformance do not
> admit an empirical profile. Initial empirical scope uses the existing recorded-state
> schema with explicit model/recorder/task bindings, rigid supported geometry and
> static roots; it does not validate all LIBERO tasks or any other benchmark.
> Initial support is evaluated at t0. Declared before/after context may corroborate
> it only through an admitted boundary inference with phase uncertainty. Unchanged
> snapshots around t0 do not, by themselves, prove that no intervening policy event
> occurred. No profile may move t0 to its first usable observation or treat the
> first policy endpoint as the initial boundary.

R1-G04 retains direct/qualified indirect support. Single-parent chain conformance
does not waive empirical inference validation. No mandatory force field is invented;
a force-free alternative must substantiate its own support assumptions.

## A08 — Cross-source coverage admission (D08)

Append after ClearCover in FORMAL_SEMANTICS.md:

> Composition operates on claim-qualified domain cells, not raw file availability.
> Certificates may be joined only when execution/object/surface identity, requirement,
> profile scope, clock transforms and uncertainty are compatible, and all requested
> transition cells at joins are independently qualified. Overlap does not double
> coverage or create independent evidence. Derived copies sharing a producer are
> recorded as dependent. Unresolved contradictory evidence blocks negative admission
> on affected cells. No interval union closes a missing cell or changes the requested
> observation projection. Independence is not required to cover two different cells,
> but is never inferred from different filenames or camera labels.

Initial release retains only admitted static-negative profiles. Dynamic/carry/excluded
phase composition is deferred; an excluded episode may still be reported as an event.

## A09 — Conflict admission before precedence (D09/D05)

Finding: the formal text calls for a conflict investigation but does not fully specify
how pending conflicts affect an otherwise positive candidate. This is consequential
for positive-first aggregation.

Append before the object outcome rule in FORMAL_SEMANTICS.md:

> Classify validity before outcome precedence. A missing observation under a supported
> contract yields U on the affected domain. Unresolved contradictory admissible
> observations yield U for affected predicates and suspend any witness relying on
> them. Proven incompatible essential identity/clock/geometry/provenance foundations
> yield IC for all dependent claims. A positive is admitted only after its full
> dependency set, applicability, scope and event evidence remain valid. A credible
> same-event contradiction cannot be declared unrelated without investigation.
> An admitted positive survives only genuinely unrelated gaps/invalid optional
> sources. Retain both conflicting records, dependency scope and resolution status;
> evaluator majority or weak visual signals cannot resolve the conflict.

This refines V(E,q,W), Ev and witness admission; it does not alter strong Kleene
logic or turn local invalid observations into evidence of a negative event.

## A11 — Schema/capability certification boundary (D11)

Finding: the schema includes adapter_version and external artifact references but
does not explicitly bind evidence-schema, inference-profile and intended-checker
versions. Capability names are free identifiers; validated_contract with a hash can
be structurally accepted without any physical validation. Existing documentation
warns against that interpretation; runtime requirements need an explicit binding.

Proposed text to append to EVIDENCE_CONTRACT.md:

> A resolved runtime assessment manifest MUST bind requirement version, configuration
> schema ID/hash, evidence schema ID/version, adapter ID/version/hash, inference profile
> ID/version/hash, checker ID/version/hash, purpose and capability record, calibration
> records/validity scope, source/model hashes and requested observation domain.
> Structural JSON validation is not empirical validation. The runtime must resolve
> referenced records and check compatible scope, hashes and capabilities; a
> validated_contract flag, certificate string or hash alone cannot admit a profile.

Proposed schema change, not applied: add a required versioned assessment-manifest
binding (or equivalent explicit fields) in the next reviewed configuration schema;
validate its structure and cross-contract compatibility separately. Keep status
proposed_pending_approval until actual approval, and distinguish capability-tested
from empirically validated scope in the referenced record. Decide exact field names
and schema revision at integration review; do not pretend the current schema already
expresses every binding. This is a remaining engineering contract review, not a
scientific numeric calibration decision.

## Consistency map after approval

| Requirement/formal concern | Applicability/fall/evidence consequence | Plan/test consequence |
|---|---|---|
| A01 input rejection | NA/U/IC remain assessed distinctions only. | Configuration/contracts plus DR04; no empirical denominator for rejected input. |
| A02 static first profile | Same abstract union/IS predicate, explicit capability gate. | Adapter/support capability matrix; A05/S02 deferred empirical cases; DR02. |
| A03 interval witness | Censored transition U; no moved boundary or invented falling phase. | Temporal/events/scope F08/F09 plus DR03. |
| A04 initial epoch/handling | Fixed initial applicability, excluded episode and unknown suffix separate. | Scope/coverage S03/F04/F06 and DR03. |
| A06 purpose/boundary | No contact-only force inference or post-action boundary substitution. | Adapter/temporal A02/A04/T01/T04; exact analytical inputs distinct from empirical data. |
| A08 negative certificates | Compatible cells and joins, gaps/conflicts explicit. | Coverage O01/T03/T04 plus DR05. |
| A09 admission precedence | Positive-first only after dependency/conflict admission. | Assessment/aggregate O02/O03/O04 plus DR06. |
| A11 independent contracts | Capability-supported object claims only; unsupported essential capability IC. | Configuration/provenance P01/P02 plus DR07. |

No amendment is needed to reinterpret historical V3; it must remain unchanged.
The matrix's D01 absence/study distinction is implemented as protocol eligibility
metadata, preserving the existing object NA proposal rather than changing it silently.
