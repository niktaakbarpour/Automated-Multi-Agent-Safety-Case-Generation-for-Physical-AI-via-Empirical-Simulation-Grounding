# Final frozen-V3 audit verification

Frozen delivery: d6657b8db2f9f91dad4931391b26ab88fee97a90.
Branch: feat/r1-v3-generalization-evaluation. Only new audit/evidence-mirror/report
files are added. V3, its configuration and thresholds, V2, approved human reference,
original submissions and recordings remain unchanged. No push or merge occurred.

## Executed stages

- 40-task/2,000-run catalog inventory.
- Full checksum/identity/frame/model provenance for 102 recordings: 60 selected,
  38 other-task preflights, four original reviewed records for duplicate checks.
- Unchanged V3 inference on all 60 eligible new recordings, producing 300 sealed
  outputs from 15,515 snapshots with zero extraction errors.
- Full source-receipt preservation; no duplicate complete recording, qpos/action,
  protected-geometry or initial-qpos fingerprint among the 64 compared sequences.
- Label-free replay reproduces all 300 core outputs exactly.
- Full evidence-only export: 60 videos/all-frame neutral measurements, 300 blank
  object cases per reviewer. All 1,214 package checksums and all answer blanks verified.
- All 63 inference artifact hashes (including 60 remote-only fact files) verified
  on Hestia. Copied compact JSON files match the original seal locally.
- 221/221 protected file hashes identical, including old predictions and annotations.

## Tests

- Generalization harness/summary/blinding and controlled-audit suite: 13 passed.
- Frozen V2 checker: 42 passed on Hestia.
- Frozen evaluator: 17 passed locally.
- Frozen V3 controlled tests: 31 passed on Hestia, no skips.
- Full frozen V3 local suite: 33 passed, 8 dependency skips. Those eight passed on
  Hestia; 23 tests overlap, so all 41 distinct V3 tests passed across environments.
- Total distinct cases across baseline/V3/audit: 113 passed, zero failed. Tests
  verifying a known inconsistency demonstrate its presence, not that it is fixed.

The full logs are retained in this directory. No software/control test is counted
as a new independently reviewed physical example. LaTeX text is supplied as source;
no local compiler or Overleaf manuscript change is claimed.

## Actual descriptive findings and limits

Reserved same-task: 10 runs / 50 units, 20 predicted applicable, 30 non-applicable,
0 unknown; 20/20 operational decisions and 0 applicable-case abstentions.
Changed-task same-scene: 50 runs / 250 units, 100 predicted applicable, 150 non-applicable,
0 unknown; 0/100 operational decisions and 100 applicable-case abstentions.
Raw R1 alarm outputs: zero in both partitions. These are not false-alarm rates.
Other-scene representative preflights: all 38 rejected by frozen mapping identity;
no incorrect native-ID fallback and no cross-scene accuracy claimed.

No new independent human labels were located. New truth-class counts, confusion
matrices, TN/FP/TP/FN, false-alarm rates, positive recall/F1 and event-localization
accuracy remain null/pending. Ten reserved runs had prior full numerical/setup
inspection; task-01 data had global inventory exposure. None is certified pristine
held out. The audit establishes task-dependent coverage collapse and structural
portability limitations, not a labelled accuracy/generalization estimate.

The controlled probes disclose an initial-applicability/event-tag inconsistency
and exact-rest sensitivity. No contradictory event tag was observed in the new
300 outputs. Original table collision ID 15 is omitted by configuration; no protected
contact to it occurred in these 60 recordings. Both are recorded as V4 proposals only.

## Archive and next action

Full blinded archive is on Hestia (not in Git):
/disk/1/data/niktakbr/r1-v3-generalization-20261027/blinded-review-20261027.tar.gz
Size 316311367 bytes.
SHA256 b693f26844fa0cfbf4dd264a55cd8c1c302ea5be1af61f79eb85343b32239200.
The local blinded_review directory is a compact metadata/forms mirror, not the full
review evidence. Supply the full archive privately, obtain two independent saved
human submissions and approved adjudication, then freeze a reference-capable comparison
harness under the existing handoff. Do not generate labels from checker predictions.

Generated CSV copies preserve their standard CRLF bytes and archive checksums.
A directory-local .gitattributes rule recognizes CRLF for CSV whitespace checks
while retaining the other default whitespace checks; no CSV bytes were normalized.
