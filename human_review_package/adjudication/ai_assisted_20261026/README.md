# Complete AI-assisted R1 proposal — pending human approval

Read adjudication_evidence_report.md and adjudication_summary.json. All four adjudicated_*.csv filenames denote **provisional AI-generated recommendations**, never approved human ground truth. Their dataset_status and human_approval_status columns make this explicit. All 90 alignment units are represented, with complete original reviewer rows retained in complete_adjudication_decisions.csv.

The unchanged original independent-review statistics are in original_agreement_statistics.json. The new evidence-qualified coverage issue does not rewrite those statistics. Disjoint negative-observation fragments stay disjoint; the compound lift/drop retains explicit subevents. Blank exact physical timings remain unknown.

The adjacent ignored local HTML review interface groups A agreements, B mechanical reconciliations, C substantive cases and D unresolved requests; its E section exports a signed decision ledger only after an actual human enters decisions, identity, date and reasons. It does not approve anything by opening the file. A/B can be reviewed as batches; C/D are shown individually. Contact sheets are loaded from local evidence directories and must not be pushed.

After actual review, validate the downloaded ledger against the new private proposal. Do not apply new decision bindings to the old proposed_20261026 package. The private bridge is a new proposal compatible with the existing approval-gated finalizer; no real finalization is performed during preparation.

```sh
python3 human_review_package/adjudication/ai_tools/complete_adjudication.py verify --package human_review_package --out human_review_package/adjudication/ai_assisted_20261026
python3 human_review_package/adjudication/ai_tools/complete_adjudication.py check-approvals --package human_review_package --out human_review_package/adjudication/ai_assisted_20261026 --private-proposal human_review_package/adjudication/ai_private_20261026 --ledger nikta_reviewed_approvals.csv
```

Only after explicit approval, the unchanged existing finalizer can consume that verified new private proposal and signed ledger, preserving unresolved decisions. It emits group-level canonical events with subevents/intervals preserved in final_label_json. This AI-assisted preparation does not execute finalization, amend reviewers, approve labels, commit or push anything.
