# Third-member adjudication

Current completed-review comparison: [start here](START_HERE.md), then read the
[proposed report](publication_20261026/adjudication_report.md) and
[publication review](PUBLICATION_REVIEW.md). The root `disagreements.csv` and
`final_labels.csv` remain the original blank templates; the dated proposal lives
under `publication_20261026/`. The unchanged private proposal remains local under
`proposed_20261026/`. Neither is approved human ground truth. No final dataset
has been frozen; raw excerpts and contact sheets are excluded from publication.

Wait until both independent reviews have been returned privately and saved unchanged. Keep dated original CSVs in separate coordinator storage; do not overwrite them or publish either set early. Compare matching run/object/record IDs and any added event IDs. Align multiple events by physical description and interval; do not assume row order pairs events.

Record disagreements in disagreements.csv: label differences, no-event versus uncertain, differing event inventories, onset intervals (including overlapping but nonidentical ranges), departure/landing timing, visibility and reasons. Re-watch the referenced shared evidence and consult measurements. Ask for existing evidence where necessary. Enter an adjudicated label and reasoning in final_labels.csv only after human review. Preserve uncertainty when evidence cannot settle a question. Keep source record IDs for both original reviews. No human decision is prefilled and no automated rule settles disagreements.

Use the [shared selected-scope decision](../REQUIREMENT_SCOPE_DECISION.md); it records requester selection, not all-member approval. Independent physical observations come first, each reviewer's R1 interpretation second, and adjudication last. A disagreement with scope is an unresolved question for a future explicit version, not permission to overwrite the selected scope or an original answer.

In final_labels.csv, retain immutable source filenames/record IDs in original_review_1_reference and original_review_2_reference, their file SHA-256 values, and each original answer verbatim in the corresponding columns. Include the complete relevant CSV row as JSON text if needed to preserve evidence, explanation, interval and uncertainty. Keep those original files unchanged alongside the final decision and reasoning. Do not replace physical-event descriptions with requirement judgments. Distinguish applicability and interpretation using the [documented vocabulary](../schemas/README.md); record reviewed frames and coverage. Unresolved cases may remain uncertain. Identity, date and human_approval remain blank until the actual adjudicator fills them. Scope selection is not human_approval of labels or detector validation.
