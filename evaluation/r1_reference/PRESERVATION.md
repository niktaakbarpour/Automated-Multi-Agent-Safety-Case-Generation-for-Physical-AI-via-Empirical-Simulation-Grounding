# Baseline preservation verification

Verified before checker-v3 implementation, 2026-10-27, on branch
`feat/r1-checker-reference-evaluation`, parent `68acd6c6784ef2b0759f356fbdaa3a46fe75e758`.

The archived scoring result reproduced byte-for-byte using the CLI scoring implementation;
all 17 evaluation tests passed locally and all 42 original checker tests passed again
in the existing Hestia runtime. All 144 baseline-release hashes and 24 protected
reference/reviewer hashes matched the pre-execution freeze. Frozen predictions were
not regenerated or rewritten. Eight large gzip evidence artifacts remain on Hestia;
only compact results, software, manifests and logs are committed here.

The previous command with exit status 1 was `git diff --no-index --check /dev/null FILE`.
Rechecking each of its four targets reproduced status 1 with empty stdout/stderr:
Git's no-index difference status, not a failed test or whitespace diagnostic.
The normal staged `git diff --cached --check` passes with status 0.

Implementation inventory:

- `reports/fall_checker_dev_v2_20261017/src/checker.py`: frozen provisional candidate
  detector. `initial_applicability()` does not establish stable support or absence;
  `analyze()` leaves requirement verdicts unassessed and resets history at frame 10.
- `src/run_development.py` in that release: read-only HDF5 observations, native-ID,
  transform and timing guards. Contact geometry is not measured support force.
- `native_geometry_v2.py` and corrected inventories: full native IDs, including
  anonymous geometry; per-recording XML identity required before mapping reuse.
- `evaluation/r1_reference/run_frozen.py`: preserves raw checker outputs; adapter
  v1 intentionally emits unknown/insufficient information without requirement evidence.
- `score.py`, `matching.py`, `protocol.json`: immutable baseline scoring protocol,
  approved final-label parsing, explicit abstentions, exact event matching and
  zero/one-saved-frame sensitivity. V1 scorer cannot accept v3 determinate decisions.
- Approved reference: 20 support labels, 20 R1 interpretations, 39 event groups,
  11 uncertainty requests (10 partially unresolved), plus approval/hash metadata.
- Scope/schema: frame-10 initial direct or indirect table support; setup and
  established post-lift departures excluded; no new physical limits or carrying duration.

Verified outcome: 20 unknown applicability outputs, 7/7 applicable-case abstentions,
0/7 binary decision coverage, no positive R1 reference examples. This is a preserved
development baseline, not a detector-accuracy estimate. V3 will branch from this commit;
no baseline evaluator, prediction, approved label or original recording will be changed.
