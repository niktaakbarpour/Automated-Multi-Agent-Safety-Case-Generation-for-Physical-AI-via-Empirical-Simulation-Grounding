# Eligibility decisions (N2)

**Audit date:** 2026-11-18. **Scope:** existing local manifests/reports only; no video decoding, source reprocessing, simulations, or inference.

**Protocol:** M4-v1.0 was approved by Nikta and Alex on 2026-11-18. This approves the evaluation design and metric definitions only; the eligibility decisions and scientific blockers below remain in force.

## Current counts

The evidence manifest has 4 original reviewed runs. The frozen V3 audit adds 10 reserved task-00 runs, 50 task-01 runs, and 38 other-task representative preflights. These represent **64 candidate source execution groups** for the two same-scene pools plus original reviewed groups, and 38 explicitly ineligible other-scene preflights. On available evidence, status is: **APPROVED 0; PROVISIONAL 0; EXCLUDED 42; PENDING 60** among the 102 enumerated source records (4 + 10 + 50 + 38). The 38 preflights and 4 reviewed development groups are excluded; the 60 audited new runs remain pending RQ3 reference admission. This is not a claim that the overall 432-manifest corpus was exhaustively grouped; the broader 432 entries remain pending and must not be added as unique execution groups.

## Decisions

- **EXCLUDED — 4 original task-00 reviewed development runs.** Prior development/review and checker exposure; useful only as known-exposure baseline. Their source recording hashes, frame counts, boundary frame 10 and first policy endpoint 11 are in `human_review_package/evidence_manifest.json` and `evaluation/r1_reference/recordings.json`.
- **PENDING — 10 reserved task-00 runs.** Audit verified 60 recordings' provenance and temporal metadata collectively and generated 300 predictions, but expressly found zero new independently reviewed cases. Reserved runs had prior full numerical/setup/mapping inspection; not pristine held out. Keep pending until new independently submitted/adjudicated labels, actual review archive access, and group-level RQ3 admission.
- **PENDING — 50 task-01 runs.** Same scene/XML, changed task and target roles; global inventory exposure. Predictions and recordings exist, but no independent labels. Cross-task is not cross-scene generalization.
- **EXCLUDED — 38 other-scene preflight representatives.** Frozen V3 mapping rejected identities. Metadata preflight does not create eligible R1 cases; no cross-scene inference/accuracy is established.
- **PENDING — 432-entry evidence-manifest corpus.** Manifest records two pools of 432 exported entries, not a verified count of canonical independent execution groups or eligible cases. Current repository `data/cases.json` has no records. Do not infer group independence or RQ3 eligibility from export counts.

Earlier evidence establishes **zero independent new-run RQ3/RQ4 labels**, not zero physical candidate recordings. Thus independent evaluation eligible now is zero. Existing reference data cover four development runs only; the conservative R1 adapter abstained on all 20 run/object units (7 reference-eligible units, 13 non-applicable), so checker admission as physical-safety evidence is **BLOCKED**. The full 60-run blinded archive (316,311,367 bytes; SHA256 `b693f26844fa0cfbf4dd264a55cd8c1c302ea5be1af61f79eb85343b32239200`) is on Hestia and the local forms directory is only a compact mirror. Blank forms are not human reference labels.

“APPROVED” means eligible for the stated confirmatory scoring scope after evidence, human reference, and exposure checks; it does not mean a prior scope selection approved detector validity. “PROVISIONAL” is metadata-only pending one or more noncritical provenance checks. “PENDING” means a required verification/reference is absent. “EXCLUDED” means the stated scope/identity/exposure rule precludes confirmatory scoring. No case is approved or provisional today.

The protocol approval does not change source status. Exact Critic configuration is **PENDING** verification. Independent labels/source eligibility remain **PENDING**. Physical R1 checker admission remains **BLOCKED** until independent validation; requirement-checked condition C cannot support physical-safety claims until that admission exists. Actual experiments have **NOT RUN** status; existing predictions are not new human reference results.
