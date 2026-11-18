# RQ3 input handoff (draft)

**Owner:** Alex (Critic). **Coordinator/evidence:** Nikta. **As of:** 2026-11-18.

## Ready to inspect

- `CASE_SOURCE_INVENTORY.csv` gives IDs, pool, benchmark/task/policy, object roles, known timeline/provenance, exposure, and current eligibility state. Exact per-run hashes and remote source paths are preserved in `evaluation/r1_v3_generalization/INPUTS.json`; do not treat producer hash attestations as a local byte rehash.
- Existing human reference and checker baseline: `evaluation/r1_reference/` and `report/checker_reference_evaluation.md` (four known-exposure runs; no positive R1 violation labels; conservative adapter abstained on all 20 units).
- Existing frozen predictions and audit: `evaluation/r1_v3_generalization/execution/predictions.json`, `summary.json`, `PROTOCOL.json`, `human_label_inventory.json`, and `report/r1_v3_generalization_audit.md`. New-run predictions are not labels.
- Full evidence-only review archive is on Hestia: `/disk/1/data/niktakbr/r1-v3-generalization-20261027/blinded-review-20261027.tar.gz`, 316,311,367 bytes, SHA256 `b693f26844fa0cfbf4dd264a55cd8c1c302ea5be1af61f79eb85343b32239200`. Local `blinded_review/` is not a standalone media package. No reviewer receipt or independent submissions are present locally.

## Ready for Critic inputs

No execution group is currently approved for RQ3 outcome scoring. The 60 audited new recordings are source candidates only; all require independent human submissions/adjudication, exposure disposition, and final group-level eligibility. The four old runs are known-exposure baselines, not independent RQ3 cases. The 432 manifest entries lack a verified canonical-group roster. Retrieval-only evidence must not be represented as physical-safety proof. R1 checker admission remains blocked pending a validated requirement-compatible evidence/coverage path and independent references.

Alex should freeze the Critic build, prompt, decoding parameters, output budget and matching across text-only, retrieval-only and requirement-checked conditions. Use identical case IDs and paired outputs; disclose the above exposure. Do not multiply N by mutations or repeated runs. Proposed repeats: 3 per group/condition, pending Alex approval. Do not generate any output until eligible groups and the protocol are approved.
