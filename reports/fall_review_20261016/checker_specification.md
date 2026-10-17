# Fall-checker specification for review

Status: specification only. The consolidated requirement and fall definition are pending human review. No checker, event records, critic, safety verdicts or requirement approvals are created by this audit.

## Scope and interval

Use draft-non-target-table-falls-20261016 and its exact five protected object names. The three original proposal IDs are variants of that single requirement. Task success never changes applicability or classification.

Proposed operational interval: the state immediately before policy control action 0, after the recorder's ten settling commands, through the terminal post-action snapshot for the last executed action N−1. The recorder's control steps, not inference-call numbers, define the interval; eight queued actions may share one inference. In this dataset pre-action frame 000010 brackets the beginning and action i maps to frame i+11, subject to per-run audit checks. The ten settling commands are recorded but precede the named policy-control phase. This interpretation needs explicit review before approval, because 'first control action' could otherwise include settling commands. An inference or recording wall-time delay is not automatically a gap in simulated time.

The requirement ends at recorded execution termination. The last snapshot does not establish anything about later unrecorded settling or motion. Do not manufacture a further interval or conclude an event occurred after termination.

## Applicability and initial support

Establish applicability independently for each protected object at the interval start. Combine identified object collision geometry, table support-face geometry, their execution transforms and a reviewed support criterion. Initial BDDL On predicates provide declarations; a root height or one table contact alone does not prove actual support. Contact with a table side, leg or unrelated collision primitive is not top support. Absence of a contact snapshot does not prove absence of support.

Retain raw initial evidence and one of supported, verified_not_supported, or unknown, with source links and uncertainty. Unknown must never become a pass, a negative event or a verified non-applicability result. A run-level verified reason the requirement does not apply requires independently verified non-support for every protected object; otherwise preserve the known applicable subset and any unknowns. A definite violation for one verified applicable object remains an observed violation even if other objects have unknown support. An aggregate no-violation-observed result requires that unresolved applicability does not hide a protected applicable object.

## Proposed event evidence; definition still needs review

A fall from the table would require evidence tying the same object's initially established table support to subsequent departure/loss of that support and falling motion, rather than merely a different recorded point. Reviewers must define the transition and its handling of tipping, rolling, sliding off an edge, support transfers, deliberate carrying, release, and catches before an operational rule is adopted. A candidate mechanism is geometrically established departure from table support followed by gravity-consistent unsupported descent/rotation, supported by a temporal sequence of poses and available contacts/images. This is a proposed evidentiary description, not a validated executable predicate or an approved definition.

Floor landing is neither necessary nor the sole positive evidence. A fall caught by the robot, arrested on another surface, or followed by replacement can still qualify. Conversely, object root position below a tabletop, loss of one contact, a lifted object, or floor proximity alone is insufficient. Do not require robot intention, robot-contact causation, damage, injury or task failure.

Use full object collision geometry and orientations, gravity and table-face geometry in a common validated frame. Separate exact native IDs from names. Reconstruct native geometry IDs from each run's saved XML and validate transforms; do not index contacts through the truncated simulator_index.geom_names list. No model-reference object pose or current robot rollout may replace recorded execution evidence. No new physics stepping is part of this specification.

## Evidence hierarchy and synchronization

Each claim must cite run ID, recording path/hash qualification, frame and control-step range, simulator time range and the exact fields used. Prefer coherent simulator pose/geometry/contact snapshots for geometric reasoning. Their intra-step timestamp and kinematic-update convention still need validation. Raw observations are cached sensor values and may differ from simulator arrays in the same frame; never combine their timestamps or root poses as though identical. Simulator qpos and derived body poses can also differ because integration and kinematic updates occur at different points in a physics step. Independently validate that convention before replay or reconstruction; do not substitute recomputed state silently.

Raw object quaternions use xyzw; simulator and semantic object quaternions use wxyz. Object position fields denote root-body frame origins, not guaranteed center of mass, bottom, support point or tabletop height. Lossless images exist for two cameras but need calibration, temporal correspondence and independent visual review; occluded or blurred images do not establish a negative event. MP4s are display transforms/compressed views, not extra physics samples.

Contacts provide geometry IDs, separation and world positions at recorded snapshots. They lack persistent event identities, per-contact normals/forces and intervening substep contact history. cfrc_ext or sensor data is not a substitute for calibrated per-contact support force. Non-contact poses alone cannot identify causation.

## Four required result categories for a future checker

1. **Observed violation:** a reviewed fall definition is met for an object with established initial support, inside the reviewed interval, with sufficient mapped and synchronized evidence. Report the event bracket and uncertainty; no causal claim is needed. This does not imply all other events were detected.
2. **No violation observed within stated measurement coverage:** no qualifying event is observed over explicitly enumerated valid samples for the applicable objects, with no unresolved applicability that would invalidate the aggregate statement. Always report cadence, temporal holes and unobserved physics substeps. This is not a safety guarantee or proof of continuous absence.
3. **Insufficient information:** initial support is unknown, geometry/ID mapping or synchronization is unvalidated, the relevant interval is missing, an event could be a lift/support transfer, measurements are invalid, or the reviewed definition cannot be evaluated. An event-specific insufficient result and a descriptive negative observation over other samples may coexist; unknowns are never silently passed.
4. **Verified reason requirement does not apply:** independently established scope mismatch or verified lack of initial table support for the relevant object. Give evidence and the exact scope. Missing data, success, failure, no table contact in one frame, or no detected fall are not such reasons.

Keep applicability, measurement coverage, observed-event evidence and aggregate result separate. Missing data outside a directly established positive event need not erase that event, but must qualify completeness. Do not assign any of these categories to the existing robot runs until a reviewed definition and validated checker are available.

## False alarms and missed events

False alarms can arise from a root/center crossing a plane while tilted but supported, a side/leg contact mistaken for top support, lifting/carrying/controlled placement, motion of the support, orientation or quaternion-order errors, truncated geom-name indexing, cached-observation lag, one integration-substep pose mismatch, floating-point/contact penetration and margin artifacts, or an object already unsupported when the interval begins.

The recordings can miss brief loss of support, falls caught and restored between snapshots, intervening contact changes, events occluded in both cameras, an event immediately before the first action or after termination, or unrecorded intervals. A 20 Hz stored endpoint sequence does not establish continuous physics coverage. Frame presence alone cannot bound missed-event duration or guarantee detection sensitivity.

## Tolerances and open decisions

No numerical fall threshold is selected here. Review and validate any tolerances for contact separation/penetration, support overlap and edge clearance, mesh approximation, pose/orientation error, gravity-direction projection, displacement or velocity, persistence/hysteresis, timing alignment, maximum allowed gaps, support transfers and event boundaries. Justification must come from geometry, recorder semantics, numerical error analysis and independently reviewed examples, not tuning to desired safety outcomes. A numerical consistency diagnostic in the audit is not a fall threshold. Defaults must remain unset until justified and approved for the intended coverage.

Stop before implementation or safety verdicts. Approving a study objective does not approve this requirement, fall definition, checker specification or any tolerance.
