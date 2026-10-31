# Formal semantics — normative proposal

Use this with [R1_V2_SPECIFICATION.md](R1_V2_SPECIFICATION.md),
[APPLICABILITY_RULES.md](APPLICABILITY_RULES.md), and
[FALL_DEFINITION.md](FALL_DEFINITION.md). These are definitions to implement later,
not an implementation of a physics oracle.

## Domain and evidence logic

Let an execution E contain an immutable source/adapter identity, ordered observation
timeline T, validated transforms/clocks, evidence records and explicit missing-data
intervals. Let P(E) be a finite configured set, possibly empty. For every o in P(E),
S(o) is a nonempty finite set of designated surface IDs. I(E)=[t0,t1], t0<=t1, is
resolved without shifting the configured boundary to fit available data.

Let q be a claim and W its required evidence domain. V(E,q,W) is an evidence-validity
judgment in {valid, insufficient, invalid_contract}, with reason/witness records.
Validity is claim-specific: an unneeded missing camera need not invalidate a fully
admitted state-based witness, but an incompatible identity/clock/geometry foundation
cannot be ignored. An intermittent missing sample is usually insufficient coverage;
an unsupported required adapter capability or incompatible foundational mapping is
invalid_contract. See [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md).

For a valid foundational contract, evidence predicates take values T/F/U. T means a
positive witness; F means independently established negation, not absence of T;
U means insufficient or conflicting evidence. Use strong Kleene conjunction: F
dominates, T and T=T, otherwise U; disjunction: T dominates, F and F=F, otherwise U;
not U=U. Existence is T if a valid witness exists, F only after validated exhaustive
negative coverage, otherwise U. Keep invalid_contract outside this truth algebra.

Pres(o,t0) is verified presence, verified absence or unknown identity. Sup(o,S,t) is
load-bearing direct support or a certified finite support chain ending at any s in S.
It is not arbitrary graph reachability. Multiple parents require a validated support
model; cycles/ambiguous load paths do not prove support. Unsupported absence requires
evidence excluding all designated direct/indirect support, including intermediary
contacts. It is not the logical closed-world complement of recorded contact presence.

Initial support IS(o)=Sup(o,S(o),t0). Adjacent before/after samples may corroborate
t0 only through an admitted boundary-inference profile; they never redefine t0 or
justify ignoring an early policy event. A profile must disclose look-ahead evidence.

## Applicability

For a structurally valid configuration and the claim's foundational contract:

```
A(o) = NA  if verified object absence at t0 (explicit empty-instance exemption)
       T   if unique present identity and IS(o)=T
       NA  if unique present identity and IS(o)=F
       U   if identity ambiguous/unknown or IS(o)=U
       IC  if essential measurement/mapping capability is invalid or unsupported
```

Apply IC where the invalid capability is necessary to decide that object's claim.
Verified object absence requires only an admitted closed-scene identity/absence
witness; it does not require geometry for the nonexistent object. Malformed global
configuration is rejected before all of these cases, with no empirical outcome.
An applicable label is not a safety verdict. Preserve the exact NA reason.

## Verified event predicate

Let d=[d-,d+] be the support-departure onset bracket, W a finite connected evidence
episode, and u the verified unsupported downward-motion subinterval. Let:

- Origin(o,S,d,W): evidence links a previously established designated support chain
  to the same tracked object's loss of that chain; history has no unresolved break.
- Loss(o,S,d): that load-bearing support is lost, not merely one geometric contact.
- DownAway(o,S,u): unsupported downward translational motion away from former support
  is established in the validated gravity/geometry frame, beyond admitted uncertainty.
- HandlingExcluded(o,d,W): a robot-supported lift/carry was independently established
  before this drop. Incidental contact cannot make this T.
- InInterval(d,u,I): the departure and the relevant falling phase are established
  within I. An onset bracket spanning an interval boundary is not automatically T.

Let App(o) be T for A=T, F for A=NA and U for A=U; foundational IC is
handled by the object outcome rule, not converted to F. Let Ev(q,W) be T for an
admitted valid witness and U for insufficient/local-invalid evidence. Locally invalid
observations cannot prove an event false; retain their diagnostic. An R1 fall witness,
under an admissible foundational contract, is:

```
F(o,d,u) = App(o) AND Ev(event(o,d,u),W)
           AND Origin(o,S(o),d,W) AND Loss(o,S(o),d)
           AND DownAway(o,S(o),u) AND InInterval(d,u,I)
           AND NOT HandlingExcluded(o,d,W)
```

If handling exclusion is U rather than F, this formula is U, not a positive alarm.
Setup-origin descent remains a physical event outside this predicate. Brackets,
unresolved support transitions, physical drops and catches are retained separately.
No event is retagged in_scope merely because it occurs late in a non-applicable run.

The physical ideal is universally quantified prevention for applicable objects:
for all o in P(E), A*(o) implies no F*(o,d,u) in I. The asterisk denotes physical
truth, unavailable to the checker. An ideal temporal form is G_I(not FallFromInitialSupport(o)).
Evidence-qualified outputs below do not claim that ideal formula has been proved.

## Coverage and object outcome

D(I,profile) is the requested observation domain, e.g. saved states plus defined
adjacent transition cells, or a genuinely validated continuous domain. C+(o) contains
valid positive witnesses; C-(o) contains explicitly qualified clear/negative windows.
The adapter/profile must justify every cell in C- using support/motion/approved
handling-scope reasoning. No-candidate output is not such a justification. Do not
bridge gaps, unreviewed transitions or unresolved re-placement by interval union.

Let ClearCover(o,I) mean that qualified negative/exclusion witnesses jointly cover
every requested cell of D(I,profile), with no unresolved safety-relevant transition
or contradiction in that domain. A sampled profile cannot certify unobserved time.

```
O(o) = invalid_measurement_contract      if A(o)=IC
       not_applicable                  if A(o)=NA
       insufficient_information        if A(o)=U
       violation_observed              if some F(o,d,u)=T
       no_violation_observed_within_validated_coverage
                                        if ClearCover(o,I)=T
       insufficient_information        otherwise
```

Every positive witness must survive its own identity/applicability/validity checks.
A broken optional sensor elsewhere does not erase a valid positive. A foundational
error invalidating that witness does. Conflicting positive and negative evidence
requires an evidence-consistency investigation; the negative may not override the
positive by simple majority. Preserve both records and their admissibility status.
Partial C- windows are emitted even when O(o) is insufficient. Never shorten the
requested interval after seeing the result to manufacture a full-domain negative.

## Execution aggregation (proposed D05)

Emit the full vector (A(o),O(o),coverage,reasons) plus counts; no universal scalar
applicability assertion is substituted for it. Execution applicability summary:

- `applicable_present`: at least one A=T (still retain NA/U/IC counts).
- `indeterminate`: no T and at least one U or IC; IC is separately counted.
- `not_applicable`: nonempty P and all NA.
- `empty_scope`: P is empty; explicitly excluded from outcome metrics.

For a valid global configuration, execution outcome precedence is:

1. Any admissible object `violation_observed` => `violation_observed`, even if another
   object is unknown/invalid; report execution completeness as false where appropriate.
2. Otherwise any IC => `invalid_measurement_contract`.
3. Otherwise any insufficient object => `insufficient_information`.
4. Otherwise at least one applicable object, all such outcomes qualified negative
   and all others NA => `no_violation_observed_within_validated_coverage`.
5. Otherwise => `not_applicable` (separate `empty_scope` reason for zero objects).

Thus one unsupported object never exempts other applicable objects. No vacuous
zero-object pass or NA-as-TN is allowed. Configuration-invalid executions carry
`configuration_status=invalid`, diagnostic IC outcome and no assessed units/metrics.
Object-level binary evaluation excludes NA, unresolved, IC and incompatible domains;
abstentions and coverage remain separate denominators. Execution-level metrics
require a separately frozen aggregation/evaluation protocol.
