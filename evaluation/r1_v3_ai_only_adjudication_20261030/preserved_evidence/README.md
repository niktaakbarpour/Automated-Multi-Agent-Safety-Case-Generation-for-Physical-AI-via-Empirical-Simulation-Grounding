# Current preserved-evidence evaluation

These derived artifacts were generated and validated on Hestia under
`/disk/1/data/niktakbr/trustworthy-ai3-preserved-20261030/`, then transferred to this
repository with the user's explicit authorization. No videos, image sheets, raw
trajectories or per-frame simulator-state files are included in this import.

This directory contains the current completed, scope-limited assessment. Earlier
access/staging reports in the parent directory remain historical records of the
infrastructure work and its blockers, not the current assessment status.

- `assessment/`: AI3 decisions, evidence-sufficiency matrix, source/coverage ledger,
  contact-regime summaries, optional restoration requirements, report and seal.
- `comparison/`: three-evaluator comparison, all-field source comparison, all 28
  original uncertainty requests, conservative provisional AI reference, its seal,
  unresolved cases and exploratory V3 agreement scores.
- `reports/`: paper-ready results, discrepancy analysis, validation, and exact
  optional raw restoration source mappings for NV06/NV12/NV16.
- `TRANSFER_SHA256.json`: the Hestia export hash and all 23 imported file hashes.
- `LIVE_SOURCE_VERIFICATION.json`: subsequent live Hestia verification of all export
  members, both seals, original annotation preservation, frozen predictions and the
  eight original human-scoring-protected files.

The assessment and provisional reference contain 12 non-applicable, five qualified
no-violation and three unresolved outcomes. NV06 and NV16 lack sufficient visual
transition review in this assessment; NV12 retains unresolved support during grasp
adjustment. No majority-vote substitution was made for the unresolved cases.

Exploratory agreement: applicability 20/20; outcomes 16/17 on determinate references;
four comparable decisions among five eligible applicable references (80% coverage,
20% eligible-reference abstention). Binary counts are TN=4 and TP=FP=FN=0. Three
unresolved reference outcomes and twelve non-applicable units do not become TNs.
There are no confirmed positive R1 reference cases; positive recall/F1 and precision
are undefined. Raw exact-label matches including unknown as a label are not physical
correctness on those unknown cases.

All results are provisional AI-only reference agreements. They are not independently
human-validated accuracy. AI3 disclosed prior conversation exposure, sampled visual
coverage and lack of timed full-video playback. Nominal source timestamps agree;
camera exposure/physics phase, support forces and between-snapshot behavior remain
unverified. Raw HDF5 files remain absent. No restoration was needed for the current
limited recommendations; preserved-video review should precede optional raw audits.

## Verify imported artifacts

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s evaluation/r1_v3_ai_only_adjudication_20261030/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s evaluation/r1_v3_ai_assisted_human_verification_20261030/tests -v
```

Local tests verify delivery integrity, schema/identity/denominator consistency and
preservation of earlier records. Research processing, scoring and its synthetic
logic tests ran on Hestia; see `reports/VALIDATION.json`. Original sealed files are
kept byte-identical; this README and import records are outside those seals.
