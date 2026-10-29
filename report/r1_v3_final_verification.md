# Final R1 v3 verification

Current branch: `feat/r1-checker-v3`.
Preserved v2 branch/commit: `feat/r1-checker-reference-evaluation` /
`9902c788156370df985ee936473a2c294e62ea26`.
Frozen inference source commit: `a357557aac457a5cecb1ee8372f70fb12d796cdd`.
The final delivery commit adds frozen manifests, outputs, evaluation and reports;
its SHA is available from `git rev-parse HEAD` and is reported in the completion message.
No main update, merge, force push or remote publication was performed.

## Verification results

| Check | Actual result |
|---|---|
| Original checker suite, Hestia | 42 passed, 0 failed |
| Preserved evaluator suite, local | 17 passed, 0 failed |
| V3 controlled suite, Hestia | 31 passed, 0 failed, 0 skipped |
| V3 full local suite | 33 passed, 0 failed, 8 dependency skips |
| Distinct v3 tests across environments | 41 passed (23 overlap) |
| Total distinct baseline plus v3 tests | 100 passed |
| Frozen inference source vs committed bytes | All six files identical |
| V2 release freeze | 144/144 file hashes identical |
| Reference/reviewer freeze | 24/24 file hashes identical |
| V2 preservation branch contents | No changes after preservation commit |
| Original recording/XML receipts | 8/8 before/after SHA256, size and mtime identical |
| V3 extraction | 4 original recordings; 1,312 snapshots; no errors |
| V3 prediction seal | All copied JSON hashes identical |
| Remote full seal, including facts | All hashes verified |
| Label-free replay, core and CLI | 20/20 core outputs identical in each |
| Scoring repeat | Byte-identical result JSON |
| Staged whitespace | Checked before final commit |

Local dependency skips are numpy/h5py geometry-integration tests; every one passed on
Hestia. They are not counted as local passes or hidden in the combined denominator.
The immutable baseline test logs and fresh v3 logs are retained. Test correctness
and empirical performance are separate claims.

The previously reported Git no-index status 1 was a difference status, not a failed
validation. The final optional compiler-discovery command also returned 1 because
neither `pdflatex` nor `tectonic` is available locally. No checker/evaluator test failed.
The LaTeX fragment was not compiled locally; no manuscript or Overleaf file was edited.

## Computed development comparison

| Measure | Frozen v2 | V3 |
|---|---:|---:|
| Applicability decisions | 0/20 | 20/20 |
| Correct applicable | 0/7 | 7/7 |
| Correct non-applicable | 0/13 | 13/13 |
| Unknown applicability | 20 | 0 |
| Compatible binary decisions | 0/7 | 6/7 |
| False R1 alarms | 0 on empty subset | 0 on 6 qualified negatives |
| Eligible abstentions | 7/7 | 1/7 |
| Positive recall / F1 | Not estimable | Not estimable |

V3 binary counts on the shared saved-frame projection: TP=0, FP=0, FN=0, TN=6.
Non-applicable units and abstentions contribute no TNs. Precision is undefined.
The one abstention is episode 014 cream cheese; its post-lift drop is preserved and
excluded from R1, while the full motion/re-placement domain remains insufficiently
qualified for a negative outcome. Physical outside-R1 matching is 37/38 phases at
strict and one-frame tolerance, with one unmatched grasp phase and no unmatched
predictions. R1-positive event performance remains unmeasurable.

## Changes and unresolved limits

Every added file across baseline preservation and v3 is enumerated in
`evaluation/r1_v3/CHANGED_FILES.md`; there are no modifications to pre-existing
protected content. `evaluation/r1_v3/verification.json` records source/prediction hashes,
coverage/results and the same full inventory. Original recordings and large evidence
files are excluded from commits. Four sealed fact gzip files remain on owned Hestia
disk1, with their location and hashes documented in the seal/README.

V3 adds a support graph grounded in recorded faces and static adjacent poses,
absence-of-support evidence, preserved departure history, deterministic sampled
fall/lift/drop interpretation, proof-based negative windows and explicit abstention.
The new evaluator retains final reference JSON, compound phases and disjoint windows,
and uses the predeclared saved-frame compatibility test. The three requested case
analyses are in `report/r1_v2_vs_v3_evaluation.md`.

Remaining limits: known development-case/reference exposure; zero empirical positive
R1 examples and no empirical indirect-support positives; no measured support-force
attribution; conservative BOX/horizontal-face/static-stencil specialization; unresolved
re-placement transitions; missing independent validation of noise/dynamics, exact camera
synchronization and intersample behavior. No held-out, continuous-safety or general
detector-accuracy claim is supported. A run/task/seed-disjoint reference with independently
reviewed in-scope positive examples remains necessary.
