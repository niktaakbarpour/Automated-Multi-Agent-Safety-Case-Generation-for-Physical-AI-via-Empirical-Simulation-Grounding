# Outstanding approval and evaluation requirements

## Why the original workflow cannot be used

`../r1_v3_human_validation_20/workflow.py` requires two complete independent submissions,
nonoverlapping human identities, pre-interpretation physical-stage snapshots, a
third adjudicator's final labels and explicit `independent_submissions_confirmed=true`.
`score_after_approval.py` verifies that approved independent reference and its seals
before reading predictions. Its freeze also binds the old code/protocol hashes.

These records contain AI-origin snapshots and user-reported acceptance. Relabelling
AI identities or asserting independent submissions would be false. Neither old
source code nor frozen protocols have been changed. A separate **AI-assisted human
verification** preparation/validation pathway is supplied here. It stops at missing
human declarations and does not reuse the independent-reference seal type.

## What actual humans/coordinator must supply

1. Confirmed identities and actual review dates for the two accepting humans, their
   confirmations of the user's report, and an honest description of evidence each
   inspected. Unknown coverage must remain unknown; do not copy AI coverage as human
   coverage. AI prose remains attributed to AI. Confirm the third human's identity,
   actual adjudication date, and the NV12 outcome selection.
2. Dispositions for physical phase/boundary, coverage and uncertainty/detail differences
   listed in `discrepancies.json`. Source identifiers alone need no adjudication.
   NV12's reported outcome selection does not approve every underlying boundary.
   Differences may be retained explicitly as unscorable; no forced resolution is needed.
3. For each case, explicitly approve an evidence-qualified saved-frame comparison
   domain or mark it unscorable with a reason. AI frame-sheet coverage and computational
   measurement coverage are distinct from actual human inspection. Broad outcome
   acceptance does not establish synchronized exposure, force support or continuous
   observation, and does not resolve the open playback requests.
4. An authorized approver's identity, date, explicit approval statement, acceptance
   of the nonindependent AI-assisted method and remaining limitations, bound to the
   exact proposal, source acceptances and discrepancy hashes. Software can check
   complete declarations, not authenticate the signer or prove their inspection.

The user's current task supplies acceptance/selection reports. It does **not** provide
the missing identities, dates, inspection details or formal reference approval. No
signature, approval decision, reference seal or scoring result has been manufactured.

## Commands after the missing information is available

From the repository root, preserve the blank template and make a separate declaration:

```sh
cp -n evaluation/r1_v3_ai_assisted_human_verification_20261030/APPROVAL_TEMPLATE.json /private/tmp/trustworthy-ai-assisted-approval.json
```

Actual reviewers/coordinator complete that JSON. Each pending discrepancy ID is
`case_id:table:field`; permitted dispositions are `retain_both_unscorable`,
`descriptive_only_confirmed`, `selected_source_1`, or `selected_source_2`, with a human
reason. These dispositions do not erase original rows. `comparison_domain_by_case`
must contain all 20 IDs, with either `{status: unscorable, reason: ...}` or
`{status: approved_saved_frame_projection, intervals: [[start,end],...], reason: ...}`.
Use valid JSON quoting, as illustrated by the actual template's other fields.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_v3_ai_assisted_human_verification_20261030/verification.py validate
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_v3_ai_assisted_human_verification_20261030/verification.py check-approval --approval /private/tmp/trustworthy-ai-assisted-approval.json
```

The second command currently rejects the blank template, as intended. Successful
declaration checking would still require coordinator authentication and review of a
**separate AI-assisted freeze/scoring adapter**. No command to falsely invoke the old
independent-reference scorer is provided. Implementing that adapter is deferred until
legitimate approval/domain decisions exist; otherwise its reference semantics would
be invented. Reuse the old immutable matching/coverage logic only under a new named
protocol, seal and tests, retaining explicit abstention and non-applicability handling.

Then score only the unchanged predictions on Hestia:

`/disk/1/data/niktakbr/r1-v3-generalization-20261027/execution/predictions.json`

Expected SHA256: `0ef93ece9c3d0cb02a49a450979315a4e3be3d5f127aa48105970321f5b34984`.
Reference verification must precede prediction reads. Report applicability/outcome
agreement, abstention, compatible-domain coverage and binary confusion separately;
stratify by assignment condition and object. Non-applicable units never add TNs.
Unmapped physical phases remain unscorable. With no approved positive R1 violations,
positive recall/F1 are undefined. Do not substitute historical development metrics.
