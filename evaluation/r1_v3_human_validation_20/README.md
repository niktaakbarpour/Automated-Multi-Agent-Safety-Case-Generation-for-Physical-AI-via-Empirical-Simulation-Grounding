# Ready-to-distribute, prediction-blinded R1 human validation

**The two actual archives are complete on Hestia.** This is not just a generator.
Do not distribute this coordinator directory or the private assignment map to reviewers;
distribute only the appropriate archive below. No reviewers have been contacted and no
actual human answers, approved reference or accuracy results have been created.

## Archives

| Reviewer | Absolute Hestia archive | Exact size |
|---|---|---:|
| reviewer_1 | `/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_1_R1_20.tar.gz` | 231095183 bytes |
| reviewer_2 | `/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20.tar.gz` | 231095189 bytes |

SHA256 reviewer_1:
`9baf33da88eb4cb5bc40c8d17aecaaa0bbe214fbd2356050d3d797814cfb3389`

SHA256 reviewer_2:
`830d9db04c3ed1602ec19c9c6396748130eff61916cd046fa92cfb567342b338`

Each archive contains **20 object--execution cases from 20 distinct recordings**,
**180 videos** (60 full videos: agentview, wrist and side-by-side; 120 setup previews
at normal/quarter speed), 280 boundary PNGs, neutral all-frame measurements, evidence
summaries, assignment manifest, blank four-category forms and byte-identical original
R1 instruction/definition files. Full video coverage and saved-frame rates were checked
with ffprobe. 598 files per archive were checked against checksums and the actual tar
contents. Both reviewers get equivalent content; only reviewer/return metadata differs.

`PACKAGE_VALIDATION.json` is the actual validation result; `BUILD_REPORT.json` binds
verified video hashes and source preservation. No required evidence is missing. This
is file-level readiness, not a claim that every physical question will be decidable:
occlusion, unrecorded support forces and camera/geometry timing limitations remain
explicit in the protocol and should be annotated as uncertainty when relevant.

## Sampling and blinding

`SAMPLING_PROTOCOL.json` was written before selection. `sample_cases.py` reads only
partition identities and the old neutral evidence manifest, not predictions or labels.
All ten reserved runs are included; ten of fifty changed-task runs are selected by a
fixed SHA256 ranking. One object is assigned per run, balanced at two instances per
protected object in each stratum. Mixed neutral IDs NV01--NV20 are shared across both
reviewers. The private original run/object/hash mapping is COORDINATOR_ASSIGNMENTS.json.
This is prediction blinding, not a claim of pristine recording exposure or full identity
blinding: visual task context and recorded instructions remain necessary evidence.

The original four annotation categories and original CSV headers are unchanged:
initial_support.csv, events.csv, requirement_interpretation.csv and
uncertainty_requests.csv. Every judgment/identity/date/approval/actual-review-coverage
field starts blank. The original review instructions are supplied verbatim, together
with a separate logistical note resolving historical episode/excerpt/task references.
No R1 definition, threshold, carrying criterion or label vocabulary was simplified.

## What each reviewer does

Give reviewer_1 only reviewer_1_R1_20.tar.gz and reviewer_2 only reviewer_2_R1_20.tar.gz,
privately. Each extracts their archive, opens START_HERE.md and ASSIGNMENTS.csv, and
inspects **all NV01--NV20 assigned objects** using complete videos, boundary images
and recorded measurements. They work independently and disclose prior exposure.

They complete initial support, physical events/timeline/actual windows, and uncertainty
first; save unchanged copies in annotations/physical_stage/; then complete the R1
applicability/outcome form independently. Preserve compound events and disjoint windows,
leave unknown times blank, keep every case and do not turn missing evidence into a pass.
Use UTF-8 CSV and retain the supplied columns and neutral IDs. Do not discuss answers
or view predictions/previous reference answers until both originals have been collected.

From inside the extracted reviewer-specific package:

```sh
# reviewer_1
python3 -m zipfile -c reviewer_1_R1_20_return.zip annotations
# reviewer_2, separately on their own copy
python3 -m zipfile -c reviewer_2_R1_20_return.zip annotations
```

Return only the appropriate ZIP privately to the coordinator through the agreed channel.
Do not send it to the other reviewer or publish it. Do not return the large video archive.
The ZIP must include the four completed CSV categories and the three saved physical-stage
CSVs. The uncertainty form may contain its header only if there are no requests.

## Coordinator commands: preserve returns, adjudicate, approve, freeze, score

The tools and immutable matching helper are staged at the same Hestia root as the
packages. They also run from this repository directory with standard-library Python.
Use private storage and new output directories; no command overwrites an existing
submission/reference/score. A corrected submission goes into a new collection root,
retaining the earlier original. These commands are for **after human returns arrive**;
there are no completed submissions to collect or score now. Place the two private
return ZIPs in private_validation/incoming/ before running collection. That private
intake directory is already created on Hestia.

```sh
R1_REVIEW_ROOT=/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027
R1_REVIEW_PRIVATE="$R1_REVIEW_ROOT/private_validation"
umask 077

python3 "$R1_REVIEW_ROOT/workflow.py" collect \
  --reviewer reviewer_1 \
  --submission "$R1_REVIEW_PRIVATE/incoming/reviewer_1_R1_20_return.zip" \
  --out "$R1_REVIEW_PRIVATE/collected"

python3 "$R1_REVIEW_ROOT/workflow.py" collect \
  --reviewer reviewer_2 \
  --submission "$R1_REVIEW_PRIVATE/incoming/reviewer_2_R1_20_return.zip" \
  --out "$R1_REVIEW_PRIVATE/collected"

python3 "$R1_REVIEW_ROOT/workflow.py" adjudication-template \
  --collected "$R1_REVIEW_PRIVATE/collected" \
  --out "$R1_REVIEW_PRIVATE/adjudication"
```

The third human now reviews both saved original submissions and source evidence and
fills every final_label_json/approval field in the four adjudicated CSVs. The template
never chooses an answer, even when reviewers agree, and never reads predictions.
See ADJUDICATION_AND_REFERENCE.md for final JSON/coverage/phase mapping guidance.
Unresolved components may stay uncertain; the software must not decide them for humans.

```sh
# Run only after the human's final adjudication CSVs are complete:
python3 "$R1_REVIEW_ROOT/workflow.py" approval-template \
  --collected "$R1_REVIEW_PRIVATE/collected" \
  --adjudication "$R1_REVIEW_PRIVATE/adjudication" \
  --out "$R1_REVIEW_PRIVATE/APPROVAL.json"
```

The adjudicator manually completes APPROVAL.json with their identity/date, explicit
approve decision, factual confirmation of independent submissions and approval statement.
The source/CSV hashes are already populated, not the decision. No approval is manufactured.
Any CSV edit afterward requires a newly reviewed approval template and human approval.

```sh
python3 "$R1_REVIEW_ROOT/workflow.py" freeze \
  --collected "$R1_REVIEW_PRIVATE/collected" \
  --adjudication "$R1_REVIEW_PRIVATE/adjudication" \
  --approval "$R1_REVIEW_PRIVATE/APPROVAL.json" \
  --out "$R1_REVIEW_PRIVATE/approved_reference"

python3 "$R1_REVIEW_ROOT/score_after_approval.py" \
  --reference "$R1_REVIEW_PRIVATE/approved_reference" \
  --predictions /disk/1/data/niktakbr/r1-v3-generalization-20261027/execution/predictions.json \
  --out "$R1_REVIEW_PRIVATE/evaluation.json"
```

Scoring verifies the approved reference seal and source-submission/recording bindings
**before reading predictions**, then checks the already sealed V3 prediction SHA256,
checker/configuration identity and selected cases. No V3 rerun or tuning is allowed.
Positive cases are supported if independently established. Unknowns, incomplete domains,
non-applicability and outside-R1 phases stay explicit; non-applicable cases never add TNs.
Positive recall/F1 are not estimable if the new approved reference has zero positives.
Both conditional and end-to-end recall are reported when applicable. Event localization
is separate, strict and one-saved-frame tolerant, with explicit approved phase mapping;
unmapped/uncertain bounds are unscorable rather than invented times.

## Reproduce selection and validation

Selection is preserved; to verify it, run the test suite rather than overwrite it:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s evaluation/r1_v3_human_validation_20/tests -v
```

For an independent on-Hestia recheck of the existing physical archives, choose a new
validation output path:

```sh
python3 /disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/validate_packages.py \
  --packages /disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages \
  --out /disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/PACKAGE_VALIDATION_recheck.json
```

The archived materials, original recordings, frozen predictions and prior reference
were not changed by the submission/scoring tooling. Complete package creation and
archive inspection ran on Hestia; local source includes only code/manifests/reports,
not the large distribution archives. Do not distribute private coordinator metadata.
