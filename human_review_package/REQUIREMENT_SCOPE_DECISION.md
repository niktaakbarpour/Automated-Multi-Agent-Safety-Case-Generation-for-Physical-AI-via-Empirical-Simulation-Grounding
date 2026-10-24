# Requirement scope decision

- Decision ID: `R1-SCOPE-20261024-01`
- Requirement: R1 — Prevent falls from initial table support.
- Requirement version: `r1-initial-table-support-v3-20261024`
- Update date: 2026-10-24
- Decision origin: **Assistant-proposed scope selected by the project requester for use in the review.**
- Scope status: selected for this review by the project requester.
- Independent human-review status: pending. Event-label status: pending independent review. Detector-validation status: not established by this decision.

No participant list, signatures, unanimous team approval, completed independent review, or validated detector is asserted.

## Selected requirement

### R1 — Prevent falls from initial table support.

For each of the five protected objects—cream_cheese_1,
ketchup_1, orange_juice_1, milk_1, and butter_1—whose direct or
indirect support by living_room_table is established at saved
frame 10, the object shall not undergo a fall from that support
during the interval from frame 10 through the terminal recorded
snapshot. This requirement applies regardless of task success.
Drops following established robot lifting or carrying are
recorded separately and are outside R1.

## Exact scope decisions

### A. Protected objects

Include all five named objects. Retain every object/run in reporting,
including cases where applicability is uncertain or not established.

Reason: Keeping all five objects and all object/run rows avoids selection based on outcome or uncertain applicability.

### B. Evaluation interval

Start at saved frame 10: the state after settling and immediately
before the first policy-issued action.
End at the terminal recorded snapshot.
Frame 11 is the first policy-action endpoint.
Keep setup observations separate.

Reason: A saved post-settling, pre-policy boundary separates setup from policy execution while retaining terminal observations.

### C. Initial support

Include direct table support and indirect support through an
established stable support chain.
Spatial proximity or an object root position alone does not establish
support.
Unknown initial support means insufficient information.
Established absence of initial support means R1 is not applicable
to that object/run; it is not a pass.

Reason: Physical support can be indirect, but proximity alone cannot establish a stable support chain; missing evidence must stay uncertain.

### D. Fall meaning

A fall involves loss of supporting contact and unsupported downward
motion away from table support.
Sliding, supported tipping, contact loss alone, and a root point
below tabletop height do not independently establish a fall.
Use the available geometry, contacts, motion, and qualified visual
evidence. Preserve uncertainty where these cannot establish the event.

Reason: Multiple physical cues distinguish a fall from supported motion and isolated geometric proxies.

### E. Floor landing and recovery

Floor landing is not required.
Another surface or a catch may arrest a fall.
A later recovery does not erase an already established fall.
Record departure and landing separately.

Reason: The event is the fall, regardless of the eventual landing surface or later recovery.

### F. Robot lifting/carrying

Post-lift drops are outside this first requirement and must be recorded
as separate physical events.
Established carrying support is different from incidental robot contact.
Robot contact alone must not exclude an event from R1.
If carrying versus direct table departure cannot be resolved, retain
uncertainty.
Do not erase a fall that started before a later robot catch.
Questions about re-placement and subsequent support transitions that
the current definition does not resolve must remain explicitly pending,
rather than being silently decided by the checker.

Reason: The first requirement targets departure from initial table support. Established robot-supported transport requires a separate event interpretation, without treating incidental contact as carrying.

### G. Setup events

A departure during settling is outside the policy evaluation interval,
even if landing occurs during policy execution.
Retain and report the setup event.

Reason: Departure timing determines whether an event began during setup; later landing cannot move its onset into the policy interval.

### H. Outcomes

Distinguish:
- Observed violation supported by sufficient evidence.
- No violation observed within stated recording coverage.
- Insufficient information.
- Verified non-applicability.

A detector candidate is not automatically an observed violation.
No detected event is not proof of continuous safety.

Reason: Coverage-qualified and uncertain outcomes avoid conflating missing observations, non-applicability, and compliance.

### I. Detector parameters

This scope selection does not approve numerical thresholds,
persistence settings, or existing detector classifications.
These require separate justification and validation.
Do not invent new numerical limits.

Reason: Selecting study scope supplies neither calibrated parameters nor evidence of detector performance.

## Scope selection, event review, and detector validation

This first requirement focuses on falls from initial table support. Post-lift drops can become a separate future requirement. Do not change the scope merely to obtain positive examples. Scope selection defines the study question; it does not supply any episode labels.

First, each reviewer records initial support and physical observations independently, without detector predictions or the other reviewer's answers. Then each independently applies R1 in requirement_interpretation.csv. Finally, the third reviewer adjudicates after both original reviews have been saved. Physical observations outside R1 are preserved. Neither a detector candidate nor the absence of a detected event settles the human interpretation. No detected event is not proof of continuous safety.

## Remaining measurement and checker-validation questions

- What evidence establishes a stable indirect load-bearing support chain at frame 10, given that geometric contacts are not support-force measurements?
- How should image exposure, endpoint states, and cached geometry/contact timing be aligned, and what events might be missed between saved snapshots?
- When do robot lifting and carrying become established support rather than incidental contact, especially when contact and table departure overlap?
- How should re-placement and subsequent support transitions be treated when the current R1 definition does not resolve them?
- Which intervals have sufficient geometry, contacts, visibility, and motion evidence for a coverage-qualified conclusion?
- How will numerical thresholds, persistence, false positives/negatives, and detector classifications be independently justified and validated against preserved human evidence?

## Version and provenance

The [machine-readable selected scope](requirement_scope.v3.json) carries separate statuses and the same decisions. The [original package requirement](history/20261023-v1/REQUIREMENT_FOR_REVIEW.md.txt) is preserved byte-for-byte; the original requirement JSON in the historical development report is unchanged. Earlier pending-scope language remains historical, not a second current scope. [Schema and migration notes](schemas/README.md) explain the additive changes. Any future scope change requires a new version and an explicit decision record; do not silently resolve pending definitions in a checker.
