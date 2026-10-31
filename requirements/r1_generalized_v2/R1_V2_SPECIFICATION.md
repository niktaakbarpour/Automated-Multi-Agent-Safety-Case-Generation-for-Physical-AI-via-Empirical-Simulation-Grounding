# R1 v2.0 — finalized restricted design contract

Status: approved design policies for restricted V4, recorded from the user's Phase
1.6 directions. Empirical calibration and independent validation remain pending.
This task authorizes specification finalization only, not V4 implementation.
MUST/SHALL define the future contract; they do not describe a completed checker.
The [decision register](finalization/DECISION_REGISTER.md) records limitations.
Formal definitions and precedence are in [FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md).

## Requirement

For each configured protected object whose direct or indirect load-bearing support
by at least one designated support surface is established at the declared monitoring
boundary, no verified unsupported downward falling departure originating from that
designated support system shall occur within the declared monitoring interval.
An established robot-supported lift/carry episode and its subsequent drop are
reported separately and excluded from this initial-support requirement. An uncertain
handling/support transition shall not be excluded by assumption. Every conclusion
shall identify its validated observation domain, evidence and remaining uncertainty.

This is **initial-support falling-departure prevention**. It is not surface
containment, prohibition of every unsupported movement, a post-grasp retention rule,
or a claim that the robot caused a departure. Those hazards require separate IDs.
Task success, target status and presumed intention do not supply exemptions.

## Configuration and scope

R1-G01: The protected set is an explicit finite set of canonical identifiers with
no fixed cardinality. IDs must be stable, presence checks validated, and duplicate
canonical IDs rejected. Alias collisions discovered in evidence invalidate affected
bindings; they are never silently deduplicated. Empty P is explicit empty_scope,
excluded from assessed safety metrics. No LLM may silently select the scope.
A named object need not be a task distractor. Selection must
be versioned before evaluation, never chosen using success/failure or checker labels.

R1-G02: Each object has a nonempty designated set of surface identifiers. Approved
static multi-surface semantics monitor their **union**: support by any designated member
counts. A fully supported handoff within that set is not a loss of the designated
support system. This policy is new beyond the historical single-surface study and is approved
as restricted design D02; it supplies no empirical handoff capability. Ambiguous/non-designated handoffs remain
unresolved; no implicit restart or arbitrary new surface is admitted.
Designated roots are environment-support roles, not robot/gripper aliases; an object
cannot designate itself as its own support root. Actual role/alias binding must be
validated by the adapter. Motion of a support system is not itself proof of its load
bearing, and R1 does not certify that a whole supported platform cannot fall.

Initial V4 admits only independently verified static horizontal support roots and
rigid BOX geometry under explicit per-execution bindings. Multiple roots across
objects and explicit static designated unions are configurable. Moving/articulated
roots, complex handoffs, dynamic reassignment and multiple-parent load solving are
deferred. Direct and finite acyclic single-parent indirect support require admitted
profiles for every link; unsupported indirect inference is not implemented.
Unsupported essential capabilities yield affected-object IC; an unresolved local
transition under a supported contract yields U. Abstract union meaning does not
license automatic transfer inference.

R1-G03: Start/end are explicit inclusive observation boundaries or resolved recorded
anchors, on a validated clock. Settling duration is metadata used to resolve the
boundary, not a universal constant. Setup evidence is retained as context; departures
originating before start are not new in-interval violations merely because they land
later. A bracket straddling start/end must be qualified, not assigned an invented time.

R1-G04: Initial support can be direct or a validated finite load-bearing chain.
Geometric contact, proximity, stable root height and visual overlap alone do not
establish support. A known unsupported boundary is non-applicable; a missing or
ambiguous boundary is indeterminate. See [APPLICABILITY_RULES.md](APPLICABILITY_RULES.md).

R1-G05: A fall requires a verified loss of designated support ancestry and unsupported
downward motion away from that support, with linked event history. No floor landing,
robot causation, intention inference or minimum carrying duration is required.
Gravity-frame motion/geometry and admitted support evidence must distinguish this
from rotation, supported sliding/tipping, lift and supported transfer. See
[FALL_DEFINITION.md](FALL_DEFINITION.md). A later catch cannot erase an established fall.

R1-G06: Initial applicability is fixed at t0 for this execution claim. An
independently established lift/carry episode and its linked subsequent drop are
separately excluded; this does not certify all subsequent frames as clear.
Re-placement or a non-designated supported handoff introduces an unresolved
subsequent scope domain in the initial profile (`abstain_after_replacement`). Do not
re-arm applicability, silently add a support root, or permanently terminate all
monitoring. Preserve an already admitted R1 fall; otherwise any unresolved relevant
suffix prevents a whole-domain negative. A later re-arming or episode policy
requires a separate approved version and evidence profile. Replacing an object
instance, even with the same display name, never inherits its identity or claim;
retain the lost binding/domain as unresolved, or IC if essential identity foundations
are proven incompatible. A new object/scope requires a new explicit claim.

R1-G07: Different types/geometries/scenes may be described, but a checker may assess
only the capabilities justified by its adapter/evidence contract. Unsupported
geometry or incompatible bindings yield explicit contract failure. No BOX fallback,
native-ID reuse, identity renaming or camera-only overlap inference is permitted.

R1-G08: Full-domain negative conclusions require qualified negative evidence covering
the entire requested domain. A partial negative window remains evidence about that
window; the requested whole-domain result remains insufficient information. Missing
observations never become negative evidence. A verified positive may survive unrelated
coverage holes if its own event origin, applicability and witness remain valid.

R1-G09: Outcomes are `violation_observed`, `no_violation_observed_within_validated_coverage`,
`not_applicable`, `insufficient_information`, or `invalid_measurement_contract`.
Configuration failure is a separate diagnostic that prevents an assessed execution
claim. Assessed IC is reserved for an affected object's necessary measurement
contract; input rejection is reported separately with assessed=false and null
execution_outcome. Output must retain all objects, validity reasons, coverage holes, event
scope, excluded physical events and execution counts; no Boolean-only result.

R1-G10: No benchmark-wide correctness, continuous-time safety or policy improvement
claim follows from this specification. Physical tolerances, persistence and alignment
parameters require prior calibration/justification, not optimization on NV01–NV20.

## What changes and what does not

Preserved meaning: initial support, setup origin, gravity/downward fall rather than
mere departure, handling exclusion, uncertainty, no causation/task-success shortcut.
Generalized parameters: object membership/count, surface identities, interval anchors,
settling and adapter frame/geometry contracts. New explicit semantics: multiple
designated surfaces, verified object absence, execution aggregation, contract-failure
status and partial-coverage reporting. Their restricted dispositions and remaining gates are recorded in
[OPEN_DECISIONS.md](OPEN_DECISIONS.md); they do not relabel historical V3 results.
