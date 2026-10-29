# R1 checker against the frozen approved human reference

## Finding and paper-ready statement

The unchanged development-v2 deterministic checker was executed on the original recordings for episodes 000, 001, 002 and 014. All four recording hashes matched the human evidence manifest. The approved reference was treated as ground truth for this bounded development evaluation: 20 run/object units, 7 applicable coverage-qualified negatives, 13 non-applicable units and **0 positive R1 violations**.

The checker is a provisional physical-event candidate generator, not an implemented definitive R1 classifier. A separately versioned conservative requirement adapter retained its evidence and returned unknown applicability / insufficient information for all 20 units. Its decision coverage was **0/7** eligible reference cases, with **7/7 abstentions**. Thus this execution does not establish binary R1 accuracy. Positive-class recall and F1 are not estimable because the reference has no positive R1 violations. The 13 non-applicable cases are excluded from binary outcomes. These are four selected, correlated development runs, not a held-out generalization test or continuous-time safety guarantee.

## Frozen baseline and leakage controls

Branch: `feat/r1-checker-reference-evaluation`, created from `68acd6c6784ef2b0759f356fbdaa3a46fe75e758`.

- Checker introduction commit: `0d9802a100012413c8930c985f565147b76b7322`.
- Unchanged source: `reports/fall_checker_dev_v2_20261017/src/checker.py`, SHA256 `d365947673071431fa2a5ed6a3cbd0e6b7b96a689a6303afc872b7f94343460d`.
- Unchanged physical config SHA256: `5cb89418e08ecfa193d45315516d7d543f150dbce77d36a45f284dac4c558b30`.
- Frozen source/config/mapping/tests/runtime and protected-file hashes: `evaluation/r1_reference/baseline_freeze.json`.
- Scope: `r1-initial-table-support-v3-20261024`; adapter: `r1-requirement-adapter-v1`.
- Sealed prediction SHA256: `688d154e7d1b3dd2a0d39c08a1a5db23c3932ff7df1ecc6f46e8a35ffcb080e9`.
- Seal SHA256: `f84e46efad091242efd27be2066545ce56c41b352d761cf1660f8db05deb9288`.

The historical runtime's `source_commit=fda672f...` had untracked development-checker files. It is retained as historical provenance, not misrepresented as an exact committed checker revision. Content hashes and the later checker-introduction commit disambiguate the baseline.

The handoff, scope, prior software regressions and user-provided aggregate/special-case facts were known before execution. The protocol and adapter were written before predictions; adjudicated CSV answers and their reasoning were loaded only after predictions were saved and sealed. Opaque reference/reviewer bytes were hashed before execution without parsing labels. The scorer and reference-normalization tests were implemented after sealing. No labels or reviewer text entered the checker or adapter. This is development evaluation with known prior case exposure, not blind or held-out validation.

Only execution selection changed: the frozen development split was restricted to the four requested development runs in a temporary execution view. No physical parameters, thresholds, event rules, mapping files or original configuration were edited. Base and existing strict/broad profiles were executed by the unchanged runner; only base predictions enter the primary comparison. No profile was selected based on labels. All 20 freshly computed base object assessments equal the previously archived v2 assessments exactly.

## Implementation audit and adapter contract

The baseline requires two descending contact-free sampled intervals (three endpoints), with base contact-face band 0.0001 m, descent threshold 0.0001 m, lift clearance 0.001 m and nominal 0.05 s sampling. Its upper-face contacts are support **candidates**, bilateral contact plus clearance is a lift **candidate**, and indirect support is unresolved. It lacks contact-force evidence and a validated negative-coverage rule. Its explicit `requirement_verdict` remains unassessed. The root approved-checker registry is empty; the root inventory pipeline does not add a definitive checker.

The baseline can emit ambiguous departures, unknown-origin descents and provisional post-lift drops. A `policy` phase only describes confirmation timing: resetting at frame 10 can split an ongoing setup trajectory and create a later unknown-origin candidate. It does not establish an in-scope departure. Missing events do not establish negative evidence; missing a support candidate does not establish absence of initial support. Incidental robot contact cannot establish scope-F exclusion.

Adapter v1 therefore adds a deterministic requirement-level record while making **no new physical inference**. It records run and canonical object identity, requirement version, unknown applicability, insufficient-information outcome, specific abstention reason, frame-10 evidence, actual measurement intervals and gaps, event IDs/spans/onset brackets, support transitions, unconfirmed sequences, and checker/adapter/config hashes. It keeps claimed compatible human-reviewed intervals empty. Direct support candidates remain unknown because the frozen implementation does not establish load-bearing support; absence of a candidate also remains unknown. This is an explicit limitation of this adapter, not a conclusion that the approved human labels are uncertain.

This adapter is separately versioned from the faithful raw baseline. It does not implement a new validated support/fall classifier. The scorer rejects determinate claims from adapter v1 instead of silently promoting candidates. A future substantive adapter needs a new version, justification, frozen predictions and evaluation; thresholds must not be tuned here and called held-out accuracy.

Native IDs are resolved with each run's inventory and validated against its own XML hash, full native geometry count and per-frame body/geometry transforms. All four XML hashes agree; shared mapping reuse is allowed only after these checks. Anonymous native geometries are retained. The legacy shortened named-geometry list is never indexed as native simulator IDs. All 1,312 original snapshots were processed without frame errors.

## Computed applicability and outcome results

Rows are approved reference applicability; columns are adapter applicability. All 20 initial-support labels are determinate in the reference.

| Reference / checker | Applies | Does not apply | Unknown |
|---|---:|---:|---:|
| Applies | 0 | 0 | 7 |
| Does not apply | 0 | 0 | 13 |
| Unknown | 0 | 0 | 0 |

The seven applicable units are butter in all four episodes and cream cheese in 000, 001 and 014. The other thirteen are non-applicable. Every unit is retained individually in `evaluation/r1_reference/results.json`, including reference support, final interpretation, evidence windows, candidate IDs, uncertainty links and abstention reason.

| Quantity | Computed result |
|---|---:|
| Reference eligibility coverage | 7/20 (35%) |
| Determinate applicability decisions | 0/20 |
| Determinate compatible binary decisions | 0/7 (0%) |
| Applicable-case abstention rate | 7/7 (100%) |
| Units with complete requested sampled measurement frames | 20/20 |
| Units with established compatible claim domains | 0/20 |
| R1 alarms on non-applicable units (scope errors) | 0/13, with all 13 abstaining |
| Determinate applicability mismatches | 0, with 20 unknowns |

The binary comparison subset is empty: **denominator 0**, with computed TP=0, FP=0, FN=0, TN=0 **on that empty subset only**. These zeros are bookkeeping, not measured success rates or evidence of absence of errors. There are no TNs among the thirteen non-applicable units and no TNs credited for abstentions. Precision is undefined; positive-class recall and F1 are not estimable, including end-to-end recall. Accuracy is undefined on this empty subset. Neither passing software tests nor human agreement establishes checker accuracy.

## Coverage and uncertainty

| Episode | Original frames | Requested R1 saved frames | Valid samples per object | Object-samples (five objects) |
|---|---:|---|---:|---:|
| 000 | 258 | 10–257 | 248 | 1,240 |
| 001 | 277 | 10–276 | 267 | 1,335 |
| 002 | 246 | 10–245 | 236 | 1,180 |
| 014 | 531 | 10–530 | 521 | 2,605 |
| Total | 1,312 | per-run endpoints | 1,272 run-samples | 6,360 |

These counts describe saved endpoint geometry/contact measurements, not independent trials or continuous coverage. Geometry has a nominal 0.002 s phase lag; camera exposure synchronization is unverified. The adapter does not equate complete geometry endpoint availability with reference-qualified multimodal observation coverage. All seven eligible units therefore remain abstentions despite complete requested measurement frames. No recording, identity or frame-domain mismatch was found; the missing component is established requirement-level evidence and claim-domain compatibility, not absent HDF5 files.

The reference's explicit applicable negative fragments cover 2,292 object-samples. Episode 014 cream cheese retains **[10,269] and [286,530]**, not one negative interval across the lift/drop. Its approved full-execution R1 interpretation also uses the scope-F exclusion; it is not a physical no-event label for frames 270–285. All 19 reference negative-window records remain disjoint as supplied. Physical events and the overall requirement interpretation are preserved separately.

Ten partially unresolved requests are retained. Primary eligibility is per claim: the later uncertain orange-juice fall does not invalidate its known initial non-applicability. A stricter secondary analysis removes any unit with a linked unresolved request; blank-object requests apply run-wide. It leaves **1/20 unit**, episode 014 butter: 1 eligible case, 0 compatible determinate decisions, 1 abstention. This restriction is a conservative uncertainty sensitivity analysis, not a revised primary denominator.

## Events and required case audits

There were **29 provisional candidates**: 17 marked setup, 12 marked policy; 17 ambiguous-contact departures and 12 unknown-origin descents. All remain unscorable as definitive R1 events. There are 0 definitive R1 event predictions and 0 approved positive R1 reference events. Strict localization and the prespecified ±1 saved-frame tolerance both have **0 eligible R1 pairs**; neither supports a localization-performance estimate or a robustness claim. No unannotated frames are event TNs.

The matcher partitions run/object/version, compatible event type, phase and scope; uses inclusive overlap plus onset-bracket compatibility; and finds deterministic maximum-cardinality one-to-one assignments, then total IoU, minimum onset distance and stable IDs. It retains unknown endpoints. Matching tests exercise non-greedy assignments, duplicates, phase/scope rejection, disjoint windows and one-frame sensitivity. The reference normalization retains all 39 final event records, their original compound fields and group linkage, and separately represents 38 established outside-R1 physical phases (including recorded-contact observations). These are not positive R1 examples or R1 detector FNs. The remaining physical records retain the distinction between an observed motion and an established fall.

- **Episode 002 cream cheese:** reference setup departure bracket [0,1], downward-motion onset [4,5], first recorded floor contact 12. Landing after frame 10 does not move departure into R1. Initial support at frame 10 is absent, hence non-applicable. The base checker retained an ambiguous setup descent over [4,9], then censored it at the frame-10 boundary. That is not a matched definitive departure/landing event, nor an R1 violation. The broad-profile historical software regression is not substituted for base. The unresolved causal-overlap question remains unresolved.
- **Episode 014 cream cheese:** reference grasp [269,270], held lift onset [272,273], last sampled holding 281, release/drop onset [281,282], first recorded table contact 284. Existing scope F excludes this established held-lift/drop; no carrying-duration threshold is introduced. The frozen checker emitted no event candidate, but retained one contact-free descent interval 282→283, versus its unchanged two-interval requirement, with lift/contact-history flags. Failure to produce a candidate is not a correct negative R1 prediction. All compound phases and the two reviewed negative fragments remain present.
- **Episode 014 orange juice:** reference tip-and-slide onset [57,58], table-contact gap [246,246], visually qualified tipping range [245,248], review through 265; fall status remains `insufficient_information`. Negative fragments [15,57] and [265,530] do not cover the intervening motion. The checker has only early setup/unknown-origin descent candidates and no established later fall classification. This cannot be converted to a physical fall negative. Reference R1 non-applicability remains determinate because initial table support was absent.

No definitive mismatched R1 claims are measurable: every prediction abstains. The explicit disagreement is decision availability—unknown versus seven established applicable and thirteen established non-applicable reference cases. Event candidate timing/semantics do not support claiming successful localization.

## Reproduction, tests and preservation

See `evaluation/r1_reference/README.md` for exact CLI commands. The original Hestia execution used Python 3.12.14, numpy 2.5.3 and h5py 3.16.0 in the existing runtime; it used no simulator stepping, model inference or GPU job. `execution/runtime.json` records argv and hashes. Recording/XML SHA256, size and mtime match before and after execution in the two receipt files.

The repository includes sealed predictions, raw result JSON, sensitivity JSON, manifests, computed comparisons, code, tests and test logs. The eight larger geometry/contact and observation gzip files remain under `/disk/1/data/niktakbr/r1-reference-evaluation-20261027/predictions/raw/` on Hestia; their exact hashes are in the seal. They are not silently treated as locally available. The scorer requires all sealed JSON artifacts and verifies any locally present large artifacts; it lists uncopied large files explicitly. Fresh execution regenerates them from the original recordings.

Validation: **42/42 inherited checker tests passed on Hestia; 17/17 adapter/scoring/matching tests passed locally.** The original four per-object base assessments reproduce the historical v2 outputs exactly. Reference internal checksums and the pre-execution protected-file hashes were verified. No approved reference, reviewer submission, original recording, baseline checker file or main-branch content was edited. Added files are confined to `evaluation/r1_reference/` and this report.

The blocker to an accuracy claim is substantive: the frozen implementation supplies provisional physical evidence but no validated requirement decision or compatible negative-observation policy. Adapter v1 exposes that gap without weakening R1. Separately, zero positive R1 examples prevents positive recall/F1 estimation even if a future adapter yields determinate predictions. A confirmatory study needs independently reviewed in-scope positive examples and run/task/seed separation, while preserving this frozen reference and baseline.
