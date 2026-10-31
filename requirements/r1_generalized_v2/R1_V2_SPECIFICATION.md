# R1 v2.0 — normative proposal

**Proposed specification, not yet approved for V4 implementation.** MUST/SHALL
describe the proposed contract, not a claim that the frozen checker implements it.
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
no fixed cardinality. A named object need not be a task distractor. Selection must
be versioned before evaluation, never chosen using success/failure or checker labels.

R1-G02: Each object has a nonempty designated set of surface identifiers. Proposed
multi-surface semantics monitor their **union**: support by any designated member
counts. A fully supported handoff within that set is not a loss of the designated
support system. This policy is new beyond the historical single-surface study and
requires approval [D02](OPEN_DECISIONS.md). Ambiguous/non-designated handoffs remain
unresolved; no implicit restart or arbitrary new surface is admitted.
Designated roots are environment-support roles, not robot/gripper aliases; an object
cannot designate itself as its own support root. Actual role/alias binding must be
validated by the adapter. Motion of a support system is not itself proof of its load
bearing, and R1 does not certify that a whole supported platform cannot fall.

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

R1-G06: Re-placement after handling and departure after non-designated supported
handoff remain unresolved in this proposal's default executable policy:
`abstain_after_replacement`. Do not silently restart R1 or declare all later frames
negative. A separately approved rule/version is necessary to resolve them [D04].

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
claim. Output must retain all objects, validity reasons, coverage holes, event
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
status and partial-coverage reporting. These require the approvals listed in
[OPEN_DECISIONS.md](OPEN_DECISIONS.md); they do not relabel historical V3 results.
