# Approved reference validation — 2026-10-26

Version: `r1-reference-be76abc531f5c716efca`, under `approved_reference/`.
Approving adjudicator: **Nikta Akbarpour**. Approval source: explicit user instruction approving the full exact current AI-assisted package, not independent reannotation/manual inspection of every event. Metadata binds the complete proposal checksums, the private finalizer bridge and the actual 90-row approval ledger.

## Actual outcomes

- Original adjudication/publication suite: **44 tests passed**.
- Complete AI proposal plus frozen-reference suite: **31 tests passed** (20 prior complete-proposal tests and 11 new freeze tests).
- Total: **75 tests passed**, no skips in these local runs with authorized evidence available.
- All 90 unique alignment units approved, none pending; table counts: 20 initial support, 39 event groups, 20 requirement interpretations, 11 uncertainty requests.
- All 160 original rows preserved losslessly. All eight source CSV hashes checked against the original proposal, and bytes compared with the merged source reviews on `origin/main`.
- Original inter-reviewer statistics copied byte-for-byte (SHA-256 `2e5d45b6b9705ad8f75d4b3d0a053c4e438f5e82d394a3a077fae604e088a046`). Historical pending-stage commentary inside that immutable statistics file is not current approval metadata.
- Existing scope F verified: recorded holding/lift before release supports episode 014 cream cheese's post-lift exclusion. No change to R1, numerical persistence threshold, or carrying-duration rule.
- Ten requests retain `partially_resolved`; one request is `resolved_existing_evidence`. Orange-juice episode-014 `fall_status=insufficient_information` remains explicit. Approval dispositions are all approved because the qualified uncertainty labels themselves were approved.
- Canonical requirement event IDs resolve to the same run/object event group. Compound phases and disjoint negative-observation fragments remain preserved in final JSON.
- Existing core finalizer emitted the four authoritative tables; the reviewed public companion contains byte-identical CSVs. A public manifest replaces private source locations/native inventory without changing labels or reviewer annotations.
- Full private-input proposal/evidence integrity checks and public companion checksums passed. Re-running core finalization and companion generation into temporary directories reproduced the same version and every companion byte; repeating into the same directory succeeded without rewriting.
- Tampered outputs, unexpected files and unsupported approval-label changes are rejected by tests.

## Commands

From repository root:

```sh
python3 -m unittest discover -s human_review_package/adjudication/tests -v
python3 -m unittest discover -s human_review_package/adjudication/ai_tests -v
python3 human_review_package/adjudication/tools/adjudicate.py verify --proposal human_review_package/adjudication/ai_private_20261026
python3 human_review_package/adjudication/ai_tools/freeze_approved.py verify --package human_review_package --publication human_review_package/adjudication/approved_reference/r1-reference-be76abc531f5c716efca
```

See the version's `REPRODUCE.md` for the exact approval-gated build. The private bridge/evidence must be restored with authorization for full evidence-gated reproduction; public verification does not establish the truth of inaccessible measurements.

The immutable approved proposal report contains two pre-existing trailing spaces. A file-specific `.gitattributes` whitespace rule preserves those hash-bound bytes; other staged whitespace checks remain enabled.

## Scientific limits

Software tests and hashes establish reproducibility and consistency, not continuous physical truth. The evidence investigation is AI-assisted and sampled; approval did not add new observations. Exact intersample timing, support forces, damage and causal responsibility remain unestablished where not recorded. Seven applicable cases have coverage-qualified no-violation observations; thirteen are non-applicable. There are no positive R1 violations in this development-selected reference. No checker accuracy, positive-class recall, or real-world safety has been measured.
