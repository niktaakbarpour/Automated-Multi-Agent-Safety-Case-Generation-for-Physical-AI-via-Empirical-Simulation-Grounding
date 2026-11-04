# Integrity negative controls

All mutations use isolated scratch files. Validated recordings, XML, predictions, annotations and seals remain unchanged.

New tests cover manifest/database mutation, incomplete restore, missing restored files with valid originals present (no fallback), wrong execution membership, traversal, symlinks, changed bytes after verification, recovery, producer/dependency/geometry/XML/contract/clock-evidence artifact corruption, invented historical attestation, retrospective-to-historical confusion, unavailable clocks and unsupported synchronization/transforms. Role mutations exercise the mandatory artifact verification path; they do not imply historical binaries exist.

Inherited tests also cover actual HDF5 shape/type/value tampering, preserved-mtime changes, replacement, parent symlinks, stale verification/decoder states, restoration and contract/source mismatches. Names/outcomes are under regressions/qa. A newly trusted manifest is a different trust root, not a bypass of the old root.
