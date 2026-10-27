# Frozen R1 V3 generalization and overfitting audit

## Finding

Frozen V3 was executed unchanged on **60 additional recordings / 300 object--run units**:
all 10 reserved same-task executions and all 50 executions of a second task in the
same scene. It processed **15,515 snapshots / 74,575 requested object-samples**, with
zero extraction errors and identical before/after recording receipts.

There is a substantial **decision-coverage failure under a task-role shift**. On the
reserved same-task set, V3 predicts 20 applicable and 30 non-applicable units, and makes
20 qualified negative decisions. On the changed-task set it predicts 100 applicable
and 150 non-applicable units, but **abstains on all 100 predicted-applicable units**.
Complete recording availability therefore does not rescue its whole-run decision
coverage when the initially supported objects become manipulation targets.

These are measured output/coverage findings, **not independent accuracy estimates**.
No independently reviewed human reference was found for any of the 60 new runs.
New applicability confusion counts, TN/FP/TP/FN, false-alarm rates, positive recall
and physical localization accuracy are pending review, not zero. No statistical
accuracy-overfitting claim can be established without those labels. The observed
coverage collapse and structural scene restrictions do establish limited operational
transfer beyond the original task. No V3 rule was repaired or tuned during this audit.

## Freeze and integrity

This audit was performed in the assistant session that implemented V3; it is not an
independent human replication. Frozen code, new execution inputs and sealed artifacts
constrain the audit, while independent human reference creation remains pending.

Audit branch: `feat/r1-v3-generalization-evaluation`, created from delivery commit
`d6657b8db2f9f91dad4931391b26ab88fee97a90`. Frozen inference source remains
`a357557aac457a5cecb1ee8372f70fb12d796cdd`.

| Frozen item | SHA256 |
|---|---|
| `r1_checker.py` | `d2914d64596f585a60021f426eb761439d604907450ebf318ca48590db0fc94f` |
| V3 evidence extractor `execute.py` | `e94ad1c34c47826a6e8a2a1b4b90543268a19d41045611c17a45287c45497cbc` |
| V3 configuration | `fd3464dc0ee0ac44ee81c325e951832896eab489517aeed0a715f8e4d0088375` |
| New sealed predictions | `0ef93ece9c3d0cb02a49a450979315a4e3be3d5f127aa48105970321f5b34984` |

The separate harness invokes original V3 `extract_frame()` and `evaluate()` functions;
it does not replace their logic, thresholds, scope or configuration. The original
four-run execution wrapper is not silently edited to accept other recordings. New
input registrations reuse the original geometry mapping only after identical XML,
complete body names, native geometry count, entity root/body IDs and every-frame
transform checks. Only the registered run ID in a derived in-memory input record is
extended; the protected mapping file remains unchanged. Different XML fails closed.

`FREEZE.json` records 221 protected file hashes, including the V2 baseline, V3 code,
tests and development predictions, approved reference, original reviewers and existing
reports. `HARNESS_FREEZE.json` binds the harness/protocol/input manifests before execution.
All 221 hashes remain identical. Original development prediction seals are unchanged.
All 102 inventoried recording/XML/metadata/native-index sets retained identical SHA256,
size and mtime receipts; all 60 inference access logs also match before/after.

## What data were selected, and what was previously seen?

The reviewed development executions are long/task_00 episodes **000, 001, 002, 014**.
The exact reserved set is **004, 009, 029, 030, 032, 034, 036, 043, 044, 048**,
seeds 1004, 1009, 1029, 1030, 1032, 1034, 1036, 1043, 1044, 1048. Their canonical run
IDs are in `evaluation/r1_v3_generalization/INPUTS.json`. They do not overlap the
original 40-run checker-development partition or the original four reviewed runs.

The secondary set is **all episodes 000--049 of long/task_01**. Task 00 instructs
putting alphabet soup and tomato sauce in the basket. Task 01 instructs putting cream
cheese and butter in the basket. It uses exactly the same XML/scene and the same five
named protected objects. Thus it is **cross-task/task-role transfer, not cross-scene**.
The unchanged R1 protects these named objects; task-target status does not silently
exempt them. Established post-lift drops remain separately outside R1.

No set here can be certified as pristine fully unseen evidence:

- `reports/fall_review_20261016/measurement_audit.md` explicitly records inspection of
  every frame's positions, orientations, contacts and transitions in **all 50 task-00
  runs** (14,215 frames). Those checks did not visually adjudicate event truth.
- `reports/fall_review_v2_20261016/measurement_findings_v2.md` records setup/mapping
  inspection of all 50 beginnings, including the support pattern. The original split
  itself warns that availability/setup diagnostics saw all runs.
- The global 2,000-run inventory inspected first/middle/final measurement availability,
  instructions and metadata for all tasks. No prior event-specific V3 outputs or
  independent labels for task 01 were found in the inspected repository artifacts.

The ten reserved runs were reserved from future checker-event evaluation, not unseen
geometry/support evidence. Their current outputs are new frozen-checker executions,
but their support conditions were known during earlier development. New task-01
full-sequence inference is new to this audit; prior global inventory exposure remains.
Human reviewers must disclose any prior exposure separately. Absence of a recorded
prior inspection is not proof that a person never saw the data.

## Inventory and provenance

The catalog covers **40 tasks / 2,000 recordings**. All ten reserved task-00 and all
50 task-01 recordings passed full input hashing, run/task identity, checkpoint metadata,
frame coverage and native mapping validation. Four original reviewed recordings were
also rehashed/fingerprinted for duplicate comparisons. One episode-000 preflight was
performed for each of the other 38 tasks: **102 recordings inventoried in total**.

All 102 metadata records attest the same checkpoint,
`moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10`, revision
`638918f3d1c2e43a39a8a20772bdb8b91835e4b7`, with the same recorded weight digests.
Selected-run model-configuration IDs match the catalog and HDF5 metadata. Weight
binaries were not rehashed and no model was run; checkpoint verification here means
rehashed metadata/recording provenance, not a new weight audit.

All selected recordings have ten settling commands, saved frame 10 tagged settling,
frame 11 as the first policy endpoint, consecutive frame keys, matching transitions
and per-recording terminal frames. The harness checks time continuity/action endpoints
and full native transforms before admitting evidence. Missing data would produce
insufficient-information outputs, never negatives; no such extraction gaps occurred.

Among the **64 full-sequence fingerprints** (60 new plus four original), there were:

- 64 distinct whole-HDF5 hashes;
- 64 distinct complete qpos-plus-executed-action stream hashes;
- 64 distinct complete protected-geometry stream hashes;
- 64 distinct frame-0--10 qpos fingerprints.

No exact duplicate whole recording or shared complete trajectory was detected by
these definitions. This does not make the runs statistically independent: they share
a checkpoint, scene, benchmark and related initial-state/goal structure. Near-duplicates,
shared subsequences and population independence are not established by cryptographic
inequality. Frames are not counted as independent executions or confidence samples.

## Cross-scene eligibility and failure of portability

Only long tasks 00 and 01 in the catalog contain all five protected objects and the
named support table under the unchanged scope. Other tasks have absent protected
identities, a different named table, different scene XML, or combinations of these.
All **38 representative preflights** outside those two tasks were rejected by the
frozen mapping identity check. They were **not** passed through incorrect native IDs,
renamed as the original table, or counted as classifier negatives/300 scored units.
No cross-scene inference accuracy or decision-coverage rate is measured here.

Concrete example: long/task_07 episode 000 contains `living_room_table`, cream cheese
and ketchup, but lacks butter, milk and orange juice and has **149 native geometries**
instead of 161. Its XML differs. The frozen mapper refuses it. A subset of its objects
could motivate a future scope-preserving per-recording mapping study, but that is not
an execution of this frozen implementation's supported five-object scene interface.

The support core is name-independent once qualified facts are supplied, but extraction
and configuration are explicitly scene-bound: original table/floor/gripper IDs,
`living_room_table`, `robot0_`/`gripper0_` naming and BOX horizontal-face reasoning.
The configuration also lists table collision IDs 10--14 while the unchanged native
mapping includes an additional owned collision BOX, ID 15. The full neutral contact
export found **no protected-object contact to ID 15 in these 60 runs**; this is a
structural completeness concern, not an observed new-run misclassification.
See `TABLE_GEOMETRY_AUDIT.json`; V3 was not modified to include it.

## Development versus new-data output behavior

**All new-data applicability/outcome numbers below are predictions, not human truth.**
Operational coverage is conditioned on the checker's predicted-applicable units.
The development predicted and approved applicable sets happen to agree (seven units).

| Quantity | Original development | Reserved same task | Changed task, same scene |
|---|---:|---:|---:|
| Executions / object units | 4 / 20 | 10 / 50 | 50 / 250 |
| Predicted applies / does not apply / unknown | 7 / 13 / 0 | 20 / 30 / 0 | 100 / 150 / 0 |
| Qualified negative outputs | 6 | 20 | 0 |
| Abstentions among predicted applicable | 1/7 | 0/20 | 100/100 |
| Declared-domain operational decision coverage | 6/7 | 20/20 | 0/100 |
| Raw R1 alarm outputs | 0 | 0 | 0 |
| Independently reviewed object units | 20 | 0 | 0 |
| Applicability agreement/confusion | 20/20 on development | Pending | Pending |
| Compatible TN / FP / TP / FN | 6 / 0 / 0 / 0 | Not measurable | Not measurable |
| False-alarm rate / R1 recall / event localization | Development limits apply | Pending | Pending |

Zero raw alarms on unlabeled data does not establish zero false alarms, no missed
violations, or zero actual positives. The 30+150 non-applicable predictions do not
supply TNs. New ground-truth applicability counts are unknown. New positive-reference
counts are unknown; the original reference still has zero positive R1 violations.
Positive recall cannot be calculated, and frames/synthetic fixtures do not supply it.

The source of the changed-task abstentions is explicit: the negative rule requires
invariant table support over the whole requested domain, while motion/lift/release
and re-placement are not composed into a full-domain negative proof. V3 infers 100
lifts (50 cream-cheese and 50 butter) and 87 post-lift drops (50 and 37 respectively),
yet every predicted-applicable whole-unit outcome abstains. These phase counts are
unreviewed classifications, not independently verified exclusions or event accuracy.
There are 2 uncertain descents; they are not promoted to R1 violations. Raw setup and
post-lift phase misclassification rates and strict/one-frame localization cannot be
scored without reviewed events. All such metrics are `null` in `summary.json`.

## Concrete case studies

1. **Reserved task-00 episode 004, cream cheese:** requested frames `[10,279]`, explicit
   invariant-table proof `[10,279]`, predicted applies and qualified negative. This is
   a new execution result but not an independent human-verified negative. It shows
   the original same-task stationary evidence pattern still admits decisions.
2. **Task-01 episode 000, cream cheese:** requested `[10,247]`, negative proof only
   `[10,68]`, inferred lift onset `[68,69]`, release/drop onset `[140,141]`, drop span
   `[140,145]`. The whole-unit outcome abstains, despite complete measurement coverage.
   No human event match or approved exclusion is inferred from those predicted tags.
3. **Task-01 episode 000, butter:** requested `[10,247]`, negative proof `[10,193]`,
   inferred lift onset `[193,194]`, holding phase through 244. Outcome abstains. Both
   target identities are affected, so this is not only the original cream-cheese case.
4. **Cross-scene task-07 episode 000:** the 149-geometry/different-XML/missing-object
   preflight is rejected. Failure is interface/scope portability, not a measured
   incorrect support decision. No fabricated unknown object poses are used.

## Controlled overfitting and logic probes (synthetic, not empirical accuracy)

The audit uses three explicitly controlled probes without modifying V3:

- A consistent represented lateral pose change of **1e-10 m** at the adjacent snapshot
  makes the exact-rest support policy abstain. This is a sensitivity demonstration,
  not a proposed new threshold or evidence of a real recorded misclassification.
- For an initially unsupported object later placed on the table and then departing,
  V3 correctly keeps run-level `does_not_apply/not_applicable`, but emits a physical
  event tagged **`r1_fall/in_scope`**. This is a concrete event-tag consistency defect:
  consumers must apply the initial-applicability gate before using event tags. No
  such contradictory tag appeared in the 300 new empirical outputs. It is a V4
  proposal, not repaired here and not counted as an independently reviewed error.
- Renaming the object in the controlled held-lift/drop scenario preserves the post-lift
  classification. The core has no cream-cheese/episode-specific answer branch. This
  rules out that particular name-hardcoding explanation, not all forms of overfitting.

No hidden episode label lookup was found in the inference core. Original support
patterns were already known, and exact-stationarity/full-domain negative logic is
closely aligned with static distractors in the development task. The measured 100%
changed-task abstention is evidence of narrow operational generalization, while the
lack of new labels prevents establishing statistical accuracy degradation or selecting
which new predictions are correct. Do not fix the failures and re-score this cohort
as independent performance.

## Independent ground truth and blinded handoff

The existing human-label inventory examined **33 CSV sources under the existing human
review package**, including original submissions and approved/adjudicated copies.
They cover only the four original run IDs. No independently approved new-run reference
was found. This is an inventory of the inspected repository sources, not a claim about
unknown annotations in external accounts or unprovided private folders.

An evidence-only package was generated independently from original recordings for
all **60 runs / 300 object units per reviewer**. It contains full 20-fps side-by-side
videos with exact saved-frame captions, boundary PNGs at 0 and 8--13, neutral all-frame
poses, contacts, geometry, raw image hashes, original R1 scope, instructions and two
sets of blank initial-support, physical-event, interpretation and uncertainty forms.
No checker predictions, proposed answers or prediction-selected windows are included.
Each video's frame count and rate were verified with ffprobe. All **1,214 package
file hashes** were verified; all human answer fields are blank. Reviewers must watch
complete runs, annotate physical evidence before interpreting R1, disclose exposure,
preserve disjoint windows/compound events, freeze original submissions and obtain
third-researcher adjudication before a reference comparison. No reviewer was contacted
or sent this package automatically.

Full package on Hestia:

```
/disk/1/data/niktakbr/r1-v3-generalization-20261027/blinded-review-20261027.tar.gz
```

Size **316,311,367 bytes**; SHA256
`b693f26844fa0cfbf4dd264a55cd8c1c302ea5be1af61f79eb85343b32239200`.
The repository's `blinded_review/` is a **compact mirror of forms/manifests only**;
media/neutral measurements remain in the full archive and must accompany review.
It is not a standalone local evidence package. All 60 larger checker fact gzip files
also remain on Hestia; their hashes are in the prediction seal. `REMOTE_VERIFICATION.json`
records verification of all 63 inference artifacts and the full review package.

## Tests, reproduction and remaining blocker

See `evaluation/r1_v3_generalization/README.md` for the inventory, unchanged-checker,
summary and neutral-export commands. Source/model/recording metadata, exposure
provenance, deduplication definitions, errors, abstentions, events and partial windows
are retained. No original recording, V2/V3 artifact, approved label, reviewer submission
or main-branch content was edited. No branch was pushed or merged.

The original V3 controlled suite passed 31/31 on Hestia; local full V3 tests passed
33 with eight numpy/h5py cases skipped locally (those eight passed remotely), covering
41 distinct V3 tests. The frozen V2 checker suite passed 42/42 and its evaluator suite
17/17. Separate harness/summary/blinding tests and a final protected-file report are
under this audit directory. Software/control tests are not independent physical truth.

**Accuracy evaluation is blocked by missing independent new-run labels, not missing
recordings or failed inference.** Actual human review/adjudication is the next step;
no empty or generated label table is substituted. Reference-compatible confusion and
localization metrics must be frozen/scored separately after that reference exists.
V4 proposals are isolated in `evaluation/r1_v3_generalization/V4_PROPOSALS.md`.

## Answers to the audit questions

1. Tested: unchanged V3 on ten reserved task-00 and fifty task-01 recordings; structural
   preflight on 38 other task representatives; full duplicate/provenance comparisons
   with the original four; three separately identified synthetic logic probes.
2. Truly unseen: none can be certified fully unseen from available exposure history.
   Reserved event outputs and task-01 full-sequence V3 outputs are new, but prior
   numerical/setup/global inventory inspection prevents a pristine holdout claim.
3. Independently verifiable numbers: hashes, identities, deduplication, output counts,
   zero extraction errors, complete export coverage and blank forms; original approved
   development agreement remains a separate result. New correctness counts are absent.
4. Unmeasurable: new support accuracy, actual applicable/positive counts, false alarms,
   TN/FP/TP/FN, recall/F1, localization and scope-phase accuracy without human labels;
   empirical cross-scene inference was not eligible under frozen bindings.
5. Overfitting evidence: strong task-dependent abstention/coverage collapse and structural
   scene dependence; no demonstrated statistical accuracy overfit or episode-answer
   hardcoding. Controlled event-tag inconsistency and exact-rest sensitivity warrant review.
6. V4: consider coherent event applicability gating, compositional observation-domain
   proofs, validated per-recording mappings/table coverage and independent positive
   references. Preserve this frozen evaluation; do not claim V4 changes as its results.
