# RQ3 input handoff

**Owner:** Alex (Critic). **Coordinator/evidence:** Nikta. **As of:** 2026-11-18.

Protocol M4-v1.0 and the paired RQ3 design were approved by Nikta and Alex on 2026-11-18. This approval does not approve cases, labels, Critic configuration, or results.

## Ready to inspect

- `CASE_SOURCE_INVENTORY.csv` gives IDs, pool, benchmark/task/policy, object roles, known timeline/provenance, exposure, and current eligibility state. Exact per-run hashes and remote source paths are preserved in `evaluation/r1_v3_generalization/INPUTS.json`; do not treat producer hash attestations as a local byte rehash.
- Existing human reference and checker baseline: `evaluation/r1_reference/` and `report/checker_reference_evaluation.md` (four known-exposure runs; no positive R1 violation labels; conservative adapter abstained on all 20 units).
- Existing frozen predictions and audit: `evaluation/r1_v3_generalization/execution/predictions.json`, `summary.json`, `PROTOCOL.json`, `human_label_inventory.json`, and `report/r1_v3_generalization_audit.md`. New-run predictions are not labels.
- Full evidence-only review archive is on Hestia: `/disk/1/data/niktakbr/r1-v3-generalization-20261027/blinded-review-20261027.tar.gz`, 316,311,367 bytes, SHA256 `b693f26844fa0cfbf4dd264a55cd8c1c302ea5be1af61f79eb85343b32239200`. Local `blinded_review/` is not a standalone media package. No reviewer receipt or independent submissions are present locally.

## Ready for Critic inputs

No execution group is currently approved for RQ3 outcome scoring. The 60 audited new recordings are source candidates only; all require independent human submissions/adjudication, exposure disposition, and final group-level eligibility. The four old runs are known-exposure development evidence, not pristine held-out RQ3 cases. The 432 manifest entries lack a verified canonical-group roster. Retrieval-only evidence must not be represented as physical-safety proof. R1 checker admission remains blocked pending independent validation; physical-safety claims under condition C remain blocked until admitted checked evidence exists. Actual experiments have not run.

Use the existing working Critic implementation and record its exact commit, model, prompt, decoding parameters, and output limit when verified; exact configuration remains pending. Compare paired outputs on identical eligible group IDs across (A) text-only, (B) retrieval-only, and (C) requirement-checked evidence, using the three approved mutations: unsupported absolute safety claims, incorrect evidence links, and unjustified scope narrowing. Plan three repetitions per group/condition if feasible and record actual repeats/settings. Mutations and repetitions do not increase independent N. Preserve exposure history and independent human reference labels. Do not present results until the pending eligibility, labels, and configuration are resolved.
