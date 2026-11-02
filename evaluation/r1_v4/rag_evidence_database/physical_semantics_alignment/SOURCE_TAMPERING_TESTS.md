# Adversarial source access

All 87 new tests passed. Tests use small isolated scratch files/DBs only, never production recordings. Source-policy/end-to-end tests are in tests/test_integrity.py and tests/test_api_tampering.py; logs/commands are manifest-bound.

Covered: modified bytes; preserved mtime; replacement with wrong or identical bytes; missing sources; final/parent symlinks; redirection after cache warm-up; modification/replacement during read; missing datasets; dtype/shape changes; wrong execution header; nonfinite values; wrong expected hash; namespace separation; stale decoded-value attempts; sparse samples; altered verified DB; matching restoration after missing/mismatched source.

Strict checks hash both boundaries; session checks prove initial hashing and invalidation. Identical restored/replaced bytes require a fresh hash and exact original values. Dtype/shape is independently rejected even when a synthetic fixture supplies a new matching hash. Failures return no partial verified results. Unverified access is rejected. Conditional SI/cache properties remain distinct from verified bytes.

No actual source bytes, predictions, human packages, seals or scoring guards were modified.
