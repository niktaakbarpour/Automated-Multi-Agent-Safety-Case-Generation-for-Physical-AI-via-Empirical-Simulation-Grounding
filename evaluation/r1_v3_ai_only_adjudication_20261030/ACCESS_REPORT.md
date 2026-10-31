# Exact Trustworthy source evidence located on Fir

Authenticated Fir control socket successfully reused. Controller reports complete transfer at 2026-10-28 01:31:17 UTC: 158/158 archives and 2,797,334,422,626 logical bytes. No controller changes made.

All 20 NV cases are present in completed archive receipts. Every original trajectory SHA256 matches its Trustworthy assignment. Each has 24 member entries including both original MP4 cameras, trajectory.h5, metadata, simulator XML/index, semantic initial conditions and completion-related records. Exact members, sizes and hashes are in fir_receipt_matches.json; case-level paths are in evidence_availability.csv.

This is receipt-level verification, not fresh decoding or rehashing of archive payloads. Expected frame counts are from assignments and have not been verified by decoding in this session. Checkpoint expected by the Trustworthy manifest is moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10; fresh original metadata inspection remains pending.

All five source dataset archives report HSM exists+archived (0x9), without a released flag. No restore/recall was requested. Fir associations include authorized def-hvpham_cpu and def-hvpham_gpu. Other listed accounts are outside scope and were not used. No compute job was submitted.

## Assessment status

Evaluator 3 has not assessed source frames or measurements and has not produced labels. No three-evaluator comparison, provisional AI reference or exploratory score is claimed. Earlier evaluator judgments were not opened during this evidence-location work. No approved reference, predictions or original evidence was changed.

## Next evidence processing step

Selectively stage only the exact members in the receipt matches into a new private remote scratch directory. Verify each staged member hash against the receipt, then inspect original run metadata, HDF5 layout, frame counts, camera completeness and object/geometry identity. Use def-hvpham_cpu for measurement/video processing rather than login-node computation. Preserve staging manifests and all commands. An evidence-first Evaluator 3 assessment and sealed draft must precede opening previous judgments. Evidence access is now located; assessment and scoring remain unfinished.
