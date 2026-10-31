# V4 acceptance matrix — planned tests, not executed V4 tests

Phase 1 QA checks the documents/configuration examples only. The matrix below is
a future implementation/evaluation contract. Use analytically specified trajectories
with known support/geometry and explicit observation sampling, or separately verified
empirical examples. Do not label existing videos from imagination or LIBERO success.

| ID | Fixture / input variation | Required result or invariant |
|---|---|---|
| C00 | Zero P, empty mappings/surfaces | Empty scope; NA reason; zero eligible/TN units; no vacuous pass. |
| C01 | One rigid object, explicit static support and complete clear domain | Applies; qualified negative at declared domain only. |
| C03 | Three objects: supported negative, unsupported, unknown | Retain three rows; execution insufficient with applicable-present summary. |
| C05 | Five objects, mixed negative/NA, one verified fall | Execution violation and full vector; NA not TN. |
| C06 | Permute P/order/rename canonical IDs with equivalent bindings | Same per-identity physics; no answer logic by count/name. |
| C07 | Duplicate object/surface IDs, missing mapping, dangling/empty S(o) | Reject invalid configuration before evidence access. |
| C08 | Explicit end before start; wrong axis/kind; metadata anchor mismatch | Reject config or boundary contract; never silently repair. |
| A01 | Complete contact/geometry and true initial absence | NA; later recontact/fall does not become initial-support violation. |
| A02 | Missing contacts versus certified empty contacts | Missing => U; certified empty requires geometry/chain exclusion before absence. |
| A03 | Ambiguous identity, partial roster, verified closed-roster absence | U / U / NA with distinct reasons. |
| A04 | Direct support, certified indirect chain, cycle, multiple load paths | T / T only with admitted single-parent profile / U / deferred essential capability IC in restricted V4; graph reachability alone rejected. |
| A05 | Initially supported object moves with moving support | Deferred dynamic capability; restricted V4 reports affected-object IC. Future admitted dynamic profile requires separate version/evidence. |
| G01 | Box, sphere/convex body, mesh, deformable object | Supported geometry profile works; unsupported required representation => IC; no fabricated box substitution. |
| G02 | Same shape in transformed/rotated common frame with transformed gravity | Invariant physical classification; no hardcoded world-z answer. |
| G03 | Different XML/native IDs, anonymous pieces, omitted surface piece | Model binding catches drift; all relevant surface geometry included; no legacy ID fallback. |
| G04 | Invalid quaternion, nonfinite values, wrong units/handedness/transform | Reject affected contract/sample with reasons; not NA/pass. |
| S01 | Two objects designated to different surfaces | Per-object S enforced; contact with the other's surface does not silently redefine S. |
| S02 | One object mapped {A,B}; qualified supported handoff A→B | No unsupported departure from union; no applicability reset. |
| S03 | Departure followed by supported transfer outside S / re-placement | Default U for unresolved later claim domain; preserve events; no silent restart. |
| F01 | Analytical rigid supported→contact-free downward translation with known gravity | In-scope verified fall; no floor landing required. |
| F02 | Supported sliding/tipping/rotation near edge | Not a verified fall; negative only with complete sufficient support/motion evidence. |
| F03 | Root below table, isolated contact loss, pure rotation | No positive from these alone; U where evidence remains insufficient. |
| F04 | Established lift/carry then release outside S | Separate post-lift drop excluded under scope F; no inferred intention. |
| F05 | Incidental robot touch followed by genuine support loss/downward motion | No automatic carrying exclusion; valid fall or U by witness sufficiency. |
| F06 | Falling begins before robot catch | Existing verified fall remains; recovery cannot erase it. |
| F07 | Release initially upward, then downward | Separate release and falling phases; bracket actual origins, not a single fabricated timestamp. |
| F08 | Departure before t0, landing after t0; onset bracket crossing t0/t1 | Setup origin not new violation; boundary-straddling interval U unless narrowed. |
| F09 | Terminal-censored support transition or drop | Preserve unknown endpoints and uncertainty; no invented landing or full negative. |
| T01 | Variable settling counts 0/8/10 and recorded boundary anchors | Same semantics relative to resolved t0; no fixed frame10 assumption. |
| T02 | Irregular validated sampling; missing samples; clock rollback; phase uncertainty | Use explicit time support; gaps U; invalid clock IC; no fixed20Hz assumption. |
| T03 | Missing camera frames with sufficient independent state witness vs camera-required witness | No blanket failure in first; U/IC as appropriate in second. Decoding is not visual inspection. |
| T04 | Equal source indices with unverified camera exposure | Never assert calibrated synchronization; restrict or abstain on claims needing it. |
| N01 | Small motion within calibrated uncertainty; uncalibrated proposed tolerance | U / reject calibration claim; no arbitrary stability threshold. |
| N02 | Short true fall below proposed persistence window | Cannot silently exempt it; disclose detection limit/U rather than redefining hazard. |
| O01 | Disjoint qualified negatives with a missing transition | Whole-domain U; retain two windows; never bridge gap. |
| O02 | Valid positive window plus unrelated missing/invalid optional camera | Positive survives if its own contract/witness valid; completeness flag remains false. |
| O03 | Invalid essential identity for claimed positive | No admitted violation based on that witness; IC diagnostic retained. |
| O04 | Violation on one object and IC on another; no violation and IC on another | Violation+incomplete / IC by explicit precedence. |
| P01 | Hash/config/adapter/calibration/source drift, duplicate frames, replay | Reject tampered/inconsistent inputs; deterministic admitted outputs and seals. |
| P02 | V3 legacy-emulation facts/config and controlled regressions | Preserve old outputs under frozen V3; record intended differences under new profiles. |
| E01 | Zero empirical positives, all abstentions, all NA, unresolved references | Undefined metrics stay null; no denominator inflation; no sensitivity claim. |
| E02 | New independently verified positives/negatives, disjoint tasks/scenes/seeds | Freeze protocol; conditional and end-to-end coverage/recall; uncertainty and scope errors separate. |

## Analytical and empirical ground truth

Analytical fixtures explicitly prescribe support constraints, geometry, transforms,
contact semantics, gravity, motion and sampling. They test implementation against
those assumptions, not real detector accuracy. Perturbations/noise sweeps must be
predeclared and bounded by a justified measurement model, not tuned to old labels.

Verified empirical fixtures need preserved original evidence, two independent
reviews where confirmatory human claims are intended, adjudication, uncertainty and
versioned observation domains. AI-only exploratory references remain a separate
condition. Positive R1 examples must actually meet applicability/origin/handling
semantics; post-lift drops and task failures cannot be relabeled as positives.

Success criteria: no unexpected identity/semantic changes in analytical regressions;
all mandatory negative-admission and abstention tests pass; tampering fails closed;
performance thresholds/confidence intervals and sample sizes are preregistered only
after a valid empirical protocol exists. No invented target accuracy is set here.

## Explicit analytical fixture definitions (planned, not executed)

Use symbolic positive parameters, not empirical calibration defaults. A sphere of
radius r has center c(t); gravity is (0,0,-g), g>0. Declare exact units, identity,
contact forces and continuous trajectory as fixture ground truth, then sample at
declared times. Sampled inputs alone do not license continuous negative claims.

* Stable/sliding negative: unbounded horizontal plane z=0, c(t)=(vt,0,r),
  upward normal force mg and no robot support. Changing horizontal position is not
  falling. Translate plane and object together for a validated moving-support test.
* Genuine edge fall: tabletop occupies x<=0, z<=0. Choose tau>0 and v>0 with
  v^2>gr. Set x=-v*tau/2 for t<=0; x=-v*tau/2+v*t^2/(2*tau) for
  0<t<=tau; x=v*(t-tau) thereafter. Set z=r through tau and
  z=r-g*(t-tau)^2/2 thereafter; y=0. Declare table support before tau,
  horizontal forcing during sliding, and no robot support. After tau the squared
  distance to the edge is r^2+(v^2-gr)*(t-tau)^2+g^2*(t-tau)^4/4>r^2:
  the sphere clears the edge and descends without interpenetration. This defines a
  positive origin bracket for sufficiently resolving samples; a bracket straddling
  a monitoring boundary instead tests abstention. No robot causation is asserted.
* Lift/carry exclusion: c(t)=(x0,0,r+h(t)), with h increasing after lift,
  declared load-bearing robot constraint and absent table contact. A later release
  has ballistic z from its actual release state; it tests the proposed post-lift
  exclusion, not an R1 positive. Removing the support declaration tests uncertainty.
* Pure rotation: fixed center with analytically prescribed rotation and maintained
  valid support. Descending vertices alone must not establish a translational fall.
* Missing/invalid evidence: mask a known interval, change a frame transform without
  a binding, or corrupt a source hash in a copy. Expect U or IC/rejection by the
  contract; never derive a replacement negative from hidden fixture ground truth.

Sphere capability must be explicitly supported/validated before these event
fixtures can be admitted; a BOX-only adapter must report unsupported geometry.
These definitions specify future tests, not new simulator runs or verified labels
for NV01–NV20. Noise, timing offsets and finite precision require separate bounded
measurement fixtures and justified calibration.

## Phase 1.6 restricted profile and amendment acceptance cases

The original matrix contains future/general cases: A05, dynamic S02 and moving-plane
fixtures are deferred and must yield affected-object IC in restricted V4, never
claimed supported. Non-BOX G01/sphere fixtures likewise require a later capability
release; structural descriptions remain illustrative. A04 supports only admitted
direct/single-parent chains; cycles cannot prove support and multiple-parent solving
is deferred. E02 is pending empirical validation, not an executed acceptance test.

| ID | Fixture / input variation | Required result or invariant |
|---|---|---|
| R16C01 | Invalid schema/mapping/config manifest mismatch | configuration_status=invalid, assessed=false, object_assessments=[], execution_outcome=null; separate rejection denominator. |
| R16C02 | Required version/hash unresolved, changed bytes, unsupported evidence/checker contract | Structure alone admits nothing; necessary runtime contract IC, no asserted positive or negative. |
| R16C03 | Manifest requirement/adapter/schema/source/domain drift versus top-level config | Reject internally inconsistent config; actual source/provenance tampering IC for dependent claims. |
| R16S01 | Static two-root BOX mapping / moving or articulated root | Static structural fixture accepted; physical admission still gated / essential unsupported capability IC. |
| R16S02 | Object re-placement, instance replacement or non-designated handoff | No re-arm/reassignment/name inheritance; relevant unresolved suffix U; prior independently admitted positive retained. |
| R16F01 | Onset or downward phase censored at t0/t1 | Candidate U unless resolved; cannot qualify negative; separate admitted positive survives. |
| R16E01 | Admissible same-event contradiction to positive | Suspend dependent witness; U, or IC if essential foundation proven incompatible; retain records and investigation status. |
| R16E02 | Invalid optional source unrelated to admitted positive / shared foundation invalid | Positive+incomplete / dependent positive not admitted; assess invalidity before aggregation. |
| R16N01 | Two qualified windows missing join transition; overlapping dependent copies | Gap remains U; no double counting/independence; no changed projection. |
| R16N02 | Carry/post-lift exclusions offered as full negative coverage | Reject unsupported dynamic composition; episode retained, whole-domain U without another admitted positive. |
| R16A01 | All combinations of admitted V, IC, U, N, NA including empty vector and permutations | V > IC > U > N > NA; N only with applicable admitted negative; complete vector/counts; empty excluded. |
| R16P01 | Analytical/legacy purpose offered as empirical validation; hash or flag alone | Refuse empirical admission; independent scoped capability/calibration records required. |
| R16P02 | Duplicate resolved aliases / incomplete presence roster | Binding IC / U; never deduplicate silently or infer verified absence. |

These are planned V4 tests. Phase 1.6 executes only schema/document checks; no
event checker, physical fixture execution, empirical evaluation or V4 aggregation
implementation has been run. Coverage completeness is separate from primary outcome:
V with unrelated U/IC remains incomplete; full negative requires all relevant cells.
