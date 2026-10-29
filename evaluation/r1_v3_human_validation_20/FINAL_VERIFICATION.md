# Final readiness and integrity verification

The immediate deliverables are two physically created, ready-to-distribute archives
on Hestia, not only build scripts. They were built from the verified 60-run evidence
archive and original recordings. No required evidence file is missing.

## Archive 1

Path: /disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_1_R1_20.tar.gz
Size: 231095183 bytes.
SHA256: 9baf33da88eb4cb5bc40c8d17aecaaa0bbe214fbd2356050d3d797814cfb3389

## Archive 2

Path: /disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20.tar.gz
Size: 231095189 bytes.
SHA256: 830d9db04c3ed1602ec19c9c6396748130eff61916cd046fa92cfb567342b338

Each has 20 object--execution cases from 20 distinct runs, 180 videos (60 full individual/
side-by-side, 120 normal/quarter-speed setup previews), 280 boundary PNGs, all-frame
neutral measurements, four original CSV categories, case summaries and exact original
R1 instruction/definition files. Each archive's 598 files were verified against the
package checksums and by reading the actual tar contents. The two archives contain
byte-equivalent evidence/protocol/assignments and equivalent blank forms; differences
are limited to reviewer/return metadata. No canonical run IDs, predictions, previous
reference answers or private coordinator map appear in either reviewer archive.

The deterministic sample has one unit per run: all ten reserved runs, plus ten changed-
task runs selected by fixed SHA256 ranking. Object assignments are balanced at two per
object per stratum. The selector never reads predictions or reference answers. The
private source mapping and hashes are retained for later canonical joins.

## Validation performed

- Original 316311367-byte source archive SHA256 verified, and extracted source manifest
  bound back to that actual archive.
- All 1214 source-review checksum entries verified before package creation.
- All selected source recording hashes and before/after size/mtime preserved.
- Every selected raw camera array matched the prior neutral export's array hash.
- All 180 unique generated video streams checked by ffprobe for frame count/rate;
  both reviewer copies and tar members match those verified stream hashes.
- Complete target-object poses, recorded geometry, frame references, both-camera image
  hashes, boundary images and all nine video files checked for each case.
- Four original CSV header sets preserved; human answer, identity/date/approval and
  actual reviewed-coverage fields verified blank in both packages.
- Original R1 instructions, scope decision and scope JSON verified byte-identical.
- 27 local tests passed, including deterministic/balanced sampling, actual readiness
  records, old protected hashes, immutable collection, human-approval gating, positive-
  capable scoring, unknowns/abstentions, disjoint windows and zero-positive metrics.
  Software metric fixtures are synthetic TEST_* examples in temporary directories,
  not new human labels or empirical detector-validation results.
- Coordinator workflow/scoring tests additionally ran on Hestia. Logs are retained.
- All 397 recorded pre-existing protected file hashes remain identical. No V3 code,
  configuration, predictions, original recording, prior human submission or approved
  development reference was modified. No push or merge occurred.

## What remains pending

No actual reviewer returns, human adjudication, approval or new reference freeze exists
yet. No new accuracy has been calculated. Collection preserves original bytes; final
labels and explicit approval can only be supplied by humans. The scoring CLI checks the
approved frozen reference and both source receipts before reading the already sealed
predictions, and rejects a changed sample/code/config/source file. Source code cannot
prove the real-world honesty/independence of a signer; private human coordination and
prior-exposure disclosure are still necessary.

These recordings are not certified pristine held-out evidence, as the prior audit
explains. File completeness does not guarantee a determinate physical answer: occlusion,
uncertain force support and camera/contact timing limitations must remain uncertainty.
No support-force measurements or interpolated observations were invented.

Use README.md for exact distribution/return/collection/adjudication/approval/freeze/
scoring commands. Only distribute the reviewer-specific archives, not this coordinator
folder or the parent audit results. Actual archives remain on Hestia; Git contains
software, private coordinator metadata and validation reports only.
