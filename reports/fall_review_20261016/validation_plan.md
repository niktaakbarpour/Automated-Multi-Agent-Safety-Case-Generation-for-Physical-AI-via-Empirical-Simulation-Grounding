# Focused validation plan for review

Status: proposed plan, not completed validation. No robot experiment reruns, checker implementation, critic or candidate approvals are authorized by this document.

## Independent recorded-example review

After agreeing the execution interval, initial-support rule and meaning of a fall, select existing recorded windows with intact provenance. Cover every protected object and distinct initial-support patterns, stationary supported objects, slides/tilts that remain supported, lift/carry/place transitions, edge departures, falls arrested on another surface or caught, ambiguous or occluded windows, and any intervals with cached/simulator pose disagreement. Use raw multi-camera images plus coherent simulator geometry/contact evidence. Do not assume any desired event class exists in these 50 runs; if a class is absent, record that validation gap instead of inventing a robot example.

Proposed independent human reviewers should first label support/applicability and event boundaries without seeing model proposals or any future checker result. They may use explicit unknown and interval-censored labels. Record exact run/frame/step/time spans, evidence, visibility and uncertainties; then adjudicate disagreements independently of checker tuning. Leave identities and decisions unentered until actual reviewers supply them. Benchmark success/failure is not a fall label.

Reserve held-out executions/windows before tuning, split by run rather than adjacent frames, and avoid counting the three proposal variants as independent evidence. Choose the validation set size after checking class availability and desired uncertainty, not a forced balanced count. Record missing classes and selection bias. Do not use synthetic examples as if they established real-event sensitivity.

## Measurement and mapping validation

Verify the per-run XML/assets and compiler version; native body/joint identity; all anonymous geometry IDs; object collision geometry ownership; actual tabletop support face; floor and other possible landing surfaces; and gravity/world units. Confirm numerical transform-consistency findings against independently examined saved frames. Cross-check initial contact locations/geometry and object shape against images before judging initial support. A declaration or absence of a contact record is not enough.

Validate raw-observation cache timing separately from simulator derived arrays, and validate the qpos versus derived-pose integration ordering. Sensors have no independent capture timestamp in the audited layout; determine defensible temporal brackets rather than assigning the frame's timestamp to every field. Verify action i/frame i+11 mapping, the last-settling prestate, final action/termination marker, and simulator-time cadence on each run. Document substep blindness; more frames or states cannot be invented retrospectively.

## Synthetic edge cases, kept in a separate evidence class

Use small constructed geometry/record arrays, not new robot executions, for: nested and anonymous geoms with duplicate None names; worldbody floor geometry; shifted/rotated/scaled table frames; quaternion xyzw/wxyz and q/−q equivalence; offset roots and centers of mass; a tilted or overhanging but supported object with root below a tabletop; side/leg contact without top support; temporary contact loss; lift/carry/place; rolling/sliding off and falling onto a non-floor surface; a fall caught before floor contact; a drop and recovery entirely between stored endpoints; moving table; unknown or verified false initial support; missing/NaN/Inf/wrong-shape positions; duplicate/reordered/gapped timestamps; cache-lagged observations; pre/post-integration pose mismatch; final-action events; events after termination; and success/failure variants with identical geometry.

First review and record expected applicability, event evidence and coverage outcome for each constructed case. Do not encode arbitrary height or duration defaults to make a case pass. Store synthetic case generators, inputs and expectations under an explicitly synthetic namespace with separate hashes. Synthetic completeness and branch coverage test logical behavior only; they do not validate detection performance on robot recordings or prove real safety.

## Evaluation and acceptance before use

Once a checker is separately authorized and built, test the measurement parser and mapping on independently audited fixtures before event classification. Evaluate event precision/recall where adjudicated event labels exist, false alarms on non-events, applicability errors, rates and causes of insufficient-information outputs, and event-time bracketing. Give run-level uncertainty and distinguish errors from genuinely unknown labels; do not count unknowns as correct negatives. Assess performance for non-floor/caught events separately to detect unintended scope narrowing.

Compare normal cadence against deliberately subsampled/gapped versions of the same reviewed windows to quantify coverage sensitivity; report that full substep ground truth is unavailable. Justify all tolerances on a development subset and freeze them before held-out evaluation. No numerical acceptance target is invented here; reviewers must set it with the intended use and observed evidence limits. Retain failed/ambiguous cases and reviewer disagreements.

The review gate is a documented decision on the draft requirement, event definition, mappings, temporal claims, validation coverage and tolerances. This plan does not supply that decision.
