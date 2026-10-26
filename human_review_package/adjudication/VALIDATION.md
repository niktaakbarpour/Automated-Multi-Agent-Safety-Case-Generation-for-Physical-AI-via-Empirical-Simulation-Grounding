# Publication validation — 2026-10-26

All 90 decisions remain pending; no real reference dataset has been frozen.

## Actual checks run

- `python3 -m unittest discover -s human_review_package/adjudication/tests -v`: **44 tests passed**, including the original 32 matching/integrity/approval/export tests and 12 publication tests. Authorized local private evidence was available for evidence-dependent integration checks. Synthetic approval/export fixtures exist only in temporary test directories; they are not real adjudicator decisions.
- `R1_PUBLIC_ONLY_TESTS=1 python3 -m unittest discover -s human_review_package/adjudication/tests -v`: unittest reported **28 tests, OK (skipped=2)**. The skipped entries are the private-evidence integration class and private-proposal publication-reproduction test. Public source-comparison, publication-integrity and safety tests run without reading private excerpts.
- Original private proposal integrity verification passed before publication. Publication generation reads but does not change its artifacts; their checksums are retained in the separate public manifest.
- Public snapshot verification passed: 160 original rows represented losslessly in 90 units; run/object/event references and approval bindings valid; 38 difference units and 11 uncertainty requests preserved; 90 pending decisions, zero approved.
- All eight reviewer CSVs were compared byte-for-byte with the merged submissions on `origin/main`; all match. Original self-approvals remain original reviewer data, not third-member adjudication approval.
- The ten scientific CSV/statistics artifacts in the public snapshot are byte-identical to the private proposal. The agreement counts, denominators and kappa values were not changed.
- Publication-only redactions are documented in `publication_20261026/redaction_map.json`: private recording locations are logical references, detailed private inventory/extraction metadata is excluded, private evidence access is explicitly qualified, and separate publication checksums are generated.
- The explicit publication allowlist contains only small UTF-8 text files. Its full contents were scanned for private absolute filesystem paths and credential patterns. Raw excerpts, twelve contact sheets, media, trajectories, model files, caches and private approval ledgers are excluded/ignored.

These checks validate software behavior, source preservation, comparison reproducibility and publication boundaries. They do **not** establish continuous safety, exact subframe timing, physical causation, detector accuracy or real-world safety. Public verification cannot independently re-inspect the excluded evidence. Episode 014 cream-cheese interpretation remains conditional on Nikta’s confirmation.

## Repeat public checks

```sh
python3 human_review_package/adjudication/tools/publish_proposal.py verify --publication human_review_package/adjudication/publication_20261026
python3 -m unittest discover -s human_review_package/adjudication/tests -v
```

The public snapshot is not in the private finalizer’s format; attempting to finalize it is rejected. Restore authorized private inputs and obtain actual human decisions before using the documented private finalization workflow. No finalization of the real dataset was performed for this publication.
