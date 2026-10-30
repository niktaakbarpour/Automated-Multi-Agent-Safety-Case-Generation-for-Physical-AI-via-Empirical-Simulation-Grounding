# R1 V3 AI-assisted human verification — 2026-10-30

**Proposed reference only. No formal approval, reference freeze or V3 scoring.**

The user reports that Human Evaluator 1 accepted all AI Evaluator 1 proposals,
Human Evaluator 2 accepted the replacement blinded AI Evaluator 2 proposals, and
a third human selected Evaluator 2's NV12 outcome. These are reported human
acceptances of AI-authored annotations, not independent human-first annotations.
Human identities, review dates, signatures, actual inspected intervals and distinct
human reasoning were not supplied. The date in this directory is the report/intake
date, not an invented human review or adjudication date.

## Files and source preservation

- `human_evaluator_{1,2}/source_ai/`: all 66 non-media files from the two Hestia
  evaluation directories, copied byte-for-byte, including all four annotation
  categories, historical physical snapshots, reports, methods, coverage, audit data,
  original IDs/dates/AI identities, and original blank human forms.
- `human_evaluator_{1,2}/acceptance.json` and `accepted_cases.csv`: separate
  user-reported human acceptance records. Original AI CSVs are deliberately unchanged.
- `human_evaluator_{1,2}/SOURCE_MANIFEST.json`: sizes and SHA256 of all 718 source
  files, including original evidence and visual sheets retained on Hestia. This is
  a manifest, not a local copy of 355 MB of media. No source evidence was deleted.
- `human_evaluator_3_adjudication/NV12.json`: exact selected AI requirement row,
  detailed physical rows, both sources' uncertainty requests, and reported selection.
- `adjudicated_reference.csv`: 20 proposed consolidated case labels; both full source
  annotation sets embedded per case. Global requests are explicitly attached to
  every affected case. No physical-event alignment or human coverage is invented.
- `field_comparison.json`: every field across all source rows and all case coverage
  objects, with exact source values and IDs. `discrepancies.json` contains differences.
- `coverage_metadata_comparison.json` retains the distinct global coverage formats
  and method metadata. `proposed_reference_breakdown.json` gives proposed label
  counts by condition/object; these are not V3 performance metrics.
- `event_alignment_candidates.json`: analyst candidate phase groups, not approved
  event equivalences or timing labels. All original rows remain available.
- `comparison_report.md`, `comparison_summary.json`, `validation_report.md`,
  `provenance.json`, `PAPER_RESULTS.md`, `ENGINEERING_PLAN.md` and
  `APPROVAL_REQUIREMENTS.md`: interpretation, provenance, limits and handoff.

The authoritative Evaluator 1 physical correction is `annotations/physical_stage_v2/`;
the historical original snapshot remains preserved. Evaluator 2 is sourced only from
`ai_evaluator_2_blind_20261029`, never the superseded exposed assessment.

Raw relative evidence links inside copied files retain their **original source-directory
context**. Resolve them from `SOURCE_MANIFEST.json`'s `source_root` on Hestia, not from
the new local folder. Evaluator 2 also references the unchanged reviewer-2 package at
`/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20/`.
No link text inside an annotation was rewritten to disguise this distinction.

## Validate without reading predictions

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evaluation/r1_v3_ai_assisted_human_verification_20261030/verification.py validate
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s evaluation/r1_v3_ai_assisted_human_verification_20261030/tests -v
```

`verification.py prepare` creates derived records only when absent; it refuses to
overwrite an existing proposal. Tests use isolated temporary copies. No command in
this pathway reads checker predictions, approves, freezes, or scores a reference.
The original independent-human workflow and its frozen code remain unchanged.
Follow `APPROVAL_REQUIREMENTS.md` before any future freeze/scoring implementation.
