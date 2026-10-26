# Public R1 proposed adjudication

All **90 decisions are pending**; no human-reference dataset is frozen. Original reviewer CSVs remain unchanged. Statistics and scientific decision ledgers are byte-identical to the private proposal. See adjudication_report.md, agreement_statistics.json, evidence_review.csv and adjudication_decisions.csv.

Private raw JSON/CSV excerpts and twelve contact sheets are excluded. The manifest lists their hashes and logical references, clearly marked unavailable in the public snapshot. It contains no private absolute recording locations or raw native-object inventory. redaction_map.json documents the transformation; original private proposal hashes are retained without its private paths. Existing authorized reviewer submissions and previously published evidence references are not re-added or modified by this change.

From the repository root:

```sh
python3 human_review_package/adjudication/tools/publish_proposal.py verify --publication human_review_package/adjudication/publication_20261026
python3 -m unittest discover -s human_review_package/adjudication/tests -v
```

The public verifier checks source-file hashes, lossless annotation representation, approval bindings, run/object/event references, unchanged statistics, pending status, checksum inventory and publication safety. It does **not** independently validate excluded scientific evidence. Private-evidence integration tests run when authorized excerpts are present; otherwise they explicitly skip. Portable source-comparison/publication tests remain available.

Approval_template.csv is still pending. Proposed labels and references are prefilled for review, not signed off. Nikta must explicitly approve, correct or preserve uncertainty, with attributable identity/date/rationale. The episode-014 cream-cheese interpretation remains conditional on her support/carrying confirmation. All eleven uncertainty requests and sampling/visibility/causation limitations remain.

Do not finalize from this redacted snapshot. It deliberately lacks the private finalizer’s proposal format and approval context. With authorized evidence restored, a coordinator first verifies the original private proposal and applies actual human decisions to a copied approval ledger. Only after approval, run from the repository root:

```sh
python3 human_review_package/adjudication/tools/adjudicate.py finalize --proposal human_review_package/adjudication/proposed_20261026 --approvals nikta_reviewed_approvals.csv --output-root versioned-reference
```

That command has **not** been executed on the real dataset. Synthetic approval/export tests use temporary directories only. Original source annotations are never overwritten; unresolved cases stay explicit. Adjudicated consensus is not independent inter-rater reliability, and neither these selected executions nor the reference labels establish detector accuracy or real-world safety.

To reproduce this publication transformation, use the unchanged authorized private proposal and a NEW output directory:

```sh
python3 human_review_package/adjudication/tools/publish_proposal.py build --proposal human_review_package/adjudication/proposed_20261026 --out publication-reproduction
```
