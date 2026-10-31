# Phase 2B.1 evidence audit

Baseline: c98a2b81e125bc60b6062b21eebdb75c426e30db. All computation and evidence inspection execute on Hestia under /disk/1/data/niktakbr/trustworthy-phase16. Empirical V4 admission stays disabled.

## Sampling and exposure

Use exactly episodes 000, 001, 002 and 014 of OpenVLA-OFT long/task_00. These are the four pre-existing development diagnostic examples in reports/fall_review_v2_20261016/example_manifest.json: setup/support context, ordinary configuration/occlusion, setup departure, and handling/release. Selection reuses measurement questions and prior development exposure; it does not rank predictions. This purposive sample cannot establish accuracy. The historical split is proposed, locked before tuning, and explicitly not human-approved; calling it development does not upgrade its approval status.

`audit_sources.py` verifies membership in proposed_split.json development and excludes its held_out set plus COORDINATOR_ASSIGNMENTS.json run identities for NV01–NV20. Entire frozen executions are excluded. Only identity/split metadata is read for exclusion. No held-out measurement or label is used for calibration. These examples overlap earlier development studies and references and cannot become independent validation cases.

## Missing originals

All four original trajectory paths are absent on Hestia. Original recordings actually inspected: **0**. Preserved full-sequence geometry/contact exports inspected: **4**, **1,312 saved frames**. These are derived, baseline-identical artifacts. DEVELOPMENT_SAMPLE_MANIFEST.csv distinguishes requested original paths/expected hashes from actual export paths/fresh hashes. No execution substitution occurred. Original expected hashes from data/runs.json are historical receipts, not fresh payload verification.

The authorized fallback determines minimum restoration evidence and feasibility without claiming raw regeneration. SELECTIVE_RESTORATION.json records exact paths, sizes, available historical hashes and purpose. Deduplicate repeated task/manifest/completion entries by path for transfer. Retrieve into a new owned disk1 directory, retain the identity map, then verify all hashes. Alliance archive locations and bytes must first be checked against the transfer journal; this phase does not assert archive availability or run a transfer. No simulations or deletion occurred.

## Checks and limits

All inspected repository sources are hashed and compared with the baseline blob. Native IDs must be contiguous, model-bound and ownership-resolved. Check saved-frame order/stage/control offsets, finite geometry/contact values and recorded transform identity residuals. Compute BOX bounds from world geom_xpos/geom_xmat and native half-sizes. Include all table collision pieces 10–15. Saved pose invariance is not continuous support proof.

No load-bearing, falling, lifting, absence, negative coverage or camera synchronization conclusion is empirically admitted. Missing raw ncon prevents fresh contact-completeness certification. Prior timing reconstructions remain qualified historical findings. Unknown physical tolerances remain unset. Analytical fixtures test explicit assumptions and conservative admission only.

## Reproduction on Hestia

Set PYTHONDONTWRITEBYTECODE=1 and TMPDIR to owned disk1, then run from repository root:

```sh
python3 evaluation/r1_v4/libero_evidence_audit/audit_sources.py
python3 -m evaluation.r1_v4.libero_evidence_audit.analytical
python3 -m unittest evaluation.r1_v4.libero_evidence_audit.analytical -v
```

Generation updates only this package. It fails if an original trajectory appears, requiring a reviewed raw-inspection protocol rather than silently changing input kind. SOURCE_BINDINGS.json records exact inspected source hashes. ARTIFACT_SHA256.json binds deliverables; Git binds that manifest itself. Numbers reported as observations or inherited findings are not decision thresholds.

The restoration list also names the task's benchmark_initial_states.init archive, whose expected digest/size must be resolved from restored metadata before any transfer. That unresolved item is explicit null, not a guessed hash. Per-run HDF5 benchmark_initial_state remains the primary saved state. The duplicate metadata.json copy is omitted because run_metadata.json carries the same historical bytes. Reattesting model weights is outside this geometry audit; checkpoint metadata identity is qualified accordingly.

Reproduce the contact/geometry diagnostic windows with `python3 -m evaluation.r1_v4.libero_evidence_audit.diagnostics` and capability dispositions with `python3 -m evaluation.r1_v4.libero_evidence_audit.build_capabilities`. Run the selected regression and frozen-integrity pipeline with `python3 -m evaluation.r1_v4.libero_evidence_audit.validate_audit`. Exact test commands and environment are persisted in validation/RESULTS.json. No raw data or videos belong in the audit commit.
