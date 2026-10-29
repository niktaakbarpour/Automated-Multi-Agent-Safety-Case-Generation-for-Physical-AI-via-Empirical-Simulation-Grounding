# Evidence-grounded R1 v3: development evaluation

## Verified baseline and branch relationship

The preserved baseline commit is `9902c788156370df985ee936473a2c294e62ea26` on
`feat/r1-checker-reference-evaluation`. It includes the original reproducible evaluation,
sealed predictions and logs. The baseline was reverified before implementation:
42/42 checker tests and 17/17 evaluator tests passed; scoring reproduced its saved
result byte-for-byte. All 144 baseline-release and 24 reference/reviewer hashes matched.
The prior exit status 1 was reproduced as Git's `diff --no-index` difference status
with no diagnostics; it was not a failed validation. No frozen predictions were rewritten.

Branch `feat/r1-checker-v3` was created directly from that preservation commit.
The v3 inference implementation, configuration, design and controlled tests were
committed as `a357557aac457a5cecb1ee8372f70fb12d796cdd` before empirical execution.
`evaluation/r1_v3/FREEZE.json` binds their exact hashes. The four original recordings
were read once for v3 inference; predictions were sealed before the new comparison
read adjudicated CSV answers. A later replay of sealed derived facts reproduced all
20 core outputs without reading labels. No threshold or inference rule was changed
after the v3 freeze or tuned to the resulting scores.

## Implementation

The frozen v2 `initial_applicability()` only produced support candidates, its
`analyze()` reset departure history at frame 10 and left R1 unassessed, and its adapter
explicitly abstained. V3 adds independent requirement reasoning in
`evaluation/r1_v3/r1_checker.py` and a read-only original-recording CLI in `execute.py`.
It reuses unchanged native-ID and transform-validation utilities, not v2 verdict logic.

Initial support requires a geometrically valid upward BOX-face contact and invariant
collision poses in frames 9, 10 and 11. Recorded signed separation and contact midpoint
must agree with the actual collision faces; side contact and proximity are insufficient.
Only the existing 512-eps coordinate-scaled arithmetic allowance is used. No physical
height band, descent distance, persistence limit or carrying-duration threshold is added.
The stencil is an adjacent observation test, not a minimum stability duration.

Indirect support follows a uniquely resolved acyclic upward chain to the table,
requiring static geometry at every link; contacts from geometrically supported children
are permitted loads. Multiple ambiguous parents, unresolved mappings and competing
contacts abstain. Absence requires complete adjacent contact bundles with no external
object contacts and separation from every table collision box. Missing a candidate
or a missing contact record cannot establish absence.

These are explicit **sampled static-equilibrium inferences**, not measured load-bearing
forces or guarantees of continuous support. All seven empirical applicable units have
direct support; this reference provides no empirical indirect-support validation.

History is retained from frame 0. Physical falls require loss of support ancestry,
consecutive completely contact-free endpoints with all corresponding collision vertices
moving downward, and separation from the table. Setup origin is retained even when
contact occurs after frame 10. Robot lift inference requires exclusive bilateral contacts,
object and both-finger upward co-motion and table separation; incidental contact is
insufficient. The lift, release/drop and first recorded contact remain separate phases.
Supported/contacted motion and isolated contact gaps retain physical uncertainty.
A later catch never erases a previously emitted fall.

A negative saved frame requires explicit consecutive invariant table-support evidence.
Full-domain negative requires every requested frame to have that evidence; missing
observations, movement and unresolved lift/re-placement transitions cause abstention.
Partial negative windows remain disjoint. Absence of detected falls does not create them.

## Actual v2 versus v3 results

Ground truth is the unchanged approved reference
`r1-reference-be76abc531f5c716efca`: 20 object/run units, 7 applicable qualified negatives,
13 non-applicable units and 0 confirmed positive R1 violations. Final JSON labels,
compound subevents, reviewed fragments and all 11 uncertainty requests were retained.
Ten requests remain partially unresolved. No continuous-time or broad population claim
is made from the four correlated, development-selected executions.

| Metric | Frozen v2 | Improved v3 |
|---|---:|---:|
| Applicability decision coverage | 0/20 | 20/20 |
| Applicable cases correctly classified | 0/7 | 7/7 |
| Non-applicable cases correctly classified | 0/13 | 13/13 |
| Incorrect determinate applicability | 0; 20 unknowns | 0; 0 unknowns |
| Unknown applicability outputs | 20 | 0 |
| R1 binary decision coverage | 0/7 | 6/7 (85.7%) |
| False R1 alarms on compatible qualified negatives | 0; empty comparison | 0/6 |
| Applicable-case abstention rate | 7/7 (100%) | 1/7 (14.3%) |
| Scope errors on non-applicable units | 0/13; all abstaining | 0/13 |
| Confirmed R1 violation recall | Not estimable | Not estimable |

Applicability matrix: reference rows, v3 prediction columns.

| Reference / prediction | Applies | Does not apply | Insufficient information |
|---|---:|---:|---:|
| Applies | 7 | 0 | 0 |
| Does not apply | 0 | 13 | 0 |
| Insufficient information | 0 | 0 | 0 |

V3 has 6 determinate applicable outcomes, 1 applicable abstention, 13 not-applicable
outcomes, no missing outputs and no R1 alarms. The compatible binary comparison contains
**TP=0, FP=0, FN=0, TN=6, denominator 6**. These are agreement counts on qualified
negatives only. The 13 non-applicable units and the abstaining unit are not TNs.
Precision is undefined (zero positive predictions). Positive-class recall and F1 are
not estimable because there are no positive R1 reference cases. No overall fall-detector
accuracy or positive-class sensitivity is established. Applicability agreement is 20/20
on these development units, not an independent generalization estimate.

## Observation-domain qualification and denominators

The pre-execution v3 design declares a **shared saved-frame projection** for comparison:
matching recording hashes, run/object/version, requested endpoints and explicit reviewed
negative fragments. A binary negative is compared only if checker support-proof windows
and reference negative windows cover the entire requested saved-frame range. This is
an explicit v3 evaluability policy under the handoff, not automatic equivalence between
video observation and geometry or a claim of synchronized camera exposure. It extends
the baseline adapter's refusal to assert compatible domains; v2 still has no determinate
outputs even under this projection. These six agreements concern this projection,
not the entirety of unobserved time between frames or every possible visual observation.

All 1,312 original snapshots were processed without extraction errors. The 1,272 requested
run-samples comprise 6,360 object-samples: 248 per object in 000, 267 in 001, 236 in 002,
and 521 in 014. Native geometry mappings were validated separately against each recording's
XML, native count and body/geometry transforms. Contacts, poses and geometry were read
from the original recordings, never from human-label tables.

V3 qualifies 2,289 negative object-samples across the seven applicable units. Six units
have full-domain proof covering 1,787 object-samples; all seven applicable units together
have 2,308 requested object-samples. Episode 014 cream
cheese has partial proof `[10,269]` and `[289,530]`; its frames 270–288 remain unqualified
for a full-domain negative. The reference retains `[10,269]` and `[286,530]` plus its
approved scope-F interpretation of the intervening lift/drop. V3 does not move its return
to rest to frame 286 merely to agree with the reference. This is the one incomplete
full-claim domain / abstention; measurement files themselves are complete.

The strict secondary sensitivity analysis excludes any unit with a linked partially
unresolved request, treating blank-object requests as run-wide. It retains only episode
014 butter: 1/20 total units, 1 eligible negative, 1 comparable v3 decision and no abstention;
v2 still abstains. Primary denominators do not discard established non-applicability merely
because a different physical-event component remains uncertain.

## Event-level results and edge cases

There are zero approved positive R1 events and zero v3 R1 event alarms. Consequently
strict and one-frame R1 matching both have no eligible pairs; recall and localization
performance for R1 violations are not estimable. No unannotated frames are event TNs.

Separately, v3 emits 37 established **outside-R1 physical phases** against 38 normalized
reference phases. Maximum-cardinality matching finds 37 matches, zero unmatched predictions
and one unmatched reference phase at both strict and ±1 saved-frame tolerance. The missing
phase is episode 014 cream-cheese grasp contact; v3 retains contacted motion but does not
promote it to an established grasp. The matching set has 17 setup departures, 18 first-recorded
contacts, one lift and one post-lift release/drop. The 18 exact recorded-contact onset/offset
sample errors are all zero. The other onset brackets are not exact physical times, and
no artificial timing errors are assigned to them. These diagnostic matches do **not**
constitute R1 TPs, R1 recall or proof that the detector recognizes positive R1 violations.
The unchanged matcher partitions type, phase and scope before assignment and retains
unknown endpoints. Tolerance changes no match in this sample; this is not general robustness.

V3 also retains 48 unscorable fall-classification observations: 29 contacted-motion groups
and 19 uncertain support transitions. They are not counted as falls, false positives or
negatives. All 39 final reference event groups, including compound subevents and disjoint
negative windows, remain in the computed comparison JSON.

1. **Episode 002 cream cheese:** v3 preserves departure `[0,1]`, downward motion `[4,5]`,
   first recorded floor contact 12 and setup scope. Boundary contact-free separated
   observations establish non-applicability. The landing after frame 10 does not create
   a policy-origin R1 violation. Causation from initial overlap remains unestablished.
2. **Episode 014 cream cheese:** v3 infers the held lift from exclusive bilateral
   contact and upward co-motion over 273→274; departure bracket `[272,273]` and last held
   sample 281 are retained. Release `[281,282]`, unsupported downward pair 282→283 and
   first recorded table contact 284 form a retained post-lift drop outside R1. It introduces
   no carrying-duration threshold. The whole-unit outcome still abstains because the
   motion/re-placement interval lacks the required full-domain negative proof.
3. **Episode 014 orange juice:** initial non-applicability is established independently
   of its later physical classification. Contacted motion and isolated transition
   `[245,246]` remain uncertain; there is no consecutive unsupported descending pair
   establishing a fall there. The checker does not turn the absence of a fall claim
   into a physical negative, and the approved `fall_status=insufficient_information`
   remains in the comparison. Negative fragments `[15,57]` and `[265,530]` are unchanged.

## Reproducibility, tests and preservation

Prediction SHA256: `f4f99d4e1f08eb3a82c4062d2725a42d3c510442a927c7e9badfd1a4846e8ee1`.
`FREEZE.json`, `execution/PREDICTION_SEAL.json`, runtime and eight before/after receipts
record code/config and recording provenance. All receipts have identical content hashes,
sizes and mtimes before and after reading. The four larger derived-fact gzip files remain
on owned Hestia disk1; their hashes are in the seal. All their hashes and a 20-unit
core-output replay were verified there. Compact predictions, results and logs are committed;
original recordings and large raw evidence are not.

Tests cover direct/indirect support, absence, ambiguity, contacts, native mapping, support
cycles, supported tipping, setup departures, an in-scope synthetic fall, bilateral versus
incidental contact, post-lift drop, catch/recovery, missing intervals and disjoint coverage.
After sealing, recorded regressions cover the three required cases; scorer tests reject
tampering, uncovered-domain TNs and non-applicable alarms being counted as binary FPs.

**41 distinct v3 tests passed across the available environments:** 33 passed locally
(with 8 numpy/h5py tests skipped there), and all 31 controlled tests passed on Hestia
(including those 8, with no skips; 23 overlap). The 42 frozen checker and 17 baseline
evaluator tests also passed. This is 100 distinct passing tests across baseline and v3,
not 100 independent detector validation examples. Test logs and the final protected-file
verification are under `evaluation/r1_v3/`.

See `evaluation/r1_v3/README.md` for exact execution/scoring commands and
`report/r1_midpoint_results.tex` for manuscript-ready text. No original recording,
reviewer annotation, approved reference, frozen v2 artifact or existing source was modified.
No main-branch update, force push, merge or manuscript edit was performed.

## Remaining limitations

The reference and requested case scenarios informed development, and were already known
in the conversation. Sealing after implementation prevents runtime label leakage and
post-score tuning; it cannot make these cases held out. There are no empirical positive
R1 examples or indirect-support examples here. Static-adjacent evidence can abstain on
supported moving objects or a departure at the first policy endpoint. The face reasoning
is specialized to the recorded BOX geometry and horizontal support faces; unresolved
multiple support parents abstain. Robot support remains a sampled multimodal geometric
inference, not measured gripping force or a causal attribution. Noise or dynamics not
represented by these runs need separate validation. Re-placement transitions remain
conservative and the cream-cheese case abstains at whole-unit level.

Obtain independently reviewed in-scope positive violations and run/task/seed-disjoint
cases for confirmatory evaluation. Do not change R1, tune thresholds repeatedly on this
reference, or use the 37 outside-scope phase matches to manufacture positive R1 recall.
