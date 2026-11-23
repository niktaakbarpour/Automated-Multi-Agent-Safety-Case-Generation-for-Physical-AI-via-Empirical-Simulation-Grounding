# Conditional RQ3 source-binding audit

## Result

The PR #39 eligibility audit remains authoritative for admission: **zero candidates are admitted**. The public R1 package build receipt and the explicitly documented R1-v3 generalization inventory identify 20 distinct canonical execution IDs and agree on all 20 expected trajectory SHA-256 values. The generalization inventory supplies exact path, task, episode, scene XML receipt, checkpoint revision, experiment ID, frame count, and object roster metadata.

A bounded existence check of the 20 exact HDF5 paths named by those receipts found **0/20 currently accessible** under the documented source root. Fresh hashing therefore verified **0** files, and HDF5 attributes could not be reopened to recheck the canonical execution identity. No other root was searched. The earlier matching hashes are historical inventory/build receipts, not current-byte verification.

The four execution IDs listed in `SOURCE_BINDING_AUDIT_SUMMARY.json` are proposed only for owner review because they span both recorded task IDs and four focal object names. The proposal is not an independent cohort or scientific approval.

## Provenance and independence

`SOURCE_BINDING_AUDIT.csv` retains the canonical IDs, exact receipt paths and expected hashes, task/episode/partition, scene XML hash, checkpoint/revision, experiment and model-configuration IDs, and current availability checks. The 20 IDs are distinct execution identifiers. They span **two task IDs**, one checkpoint revision, and a shared experiment ID in the prior inventory. Prior receipt metadata has one scene XML digest across these records; this is a source fingerprint, not proof of a separately sampled scene. No canonical source-group IDs or grouping rationale are present. Accordingly, **zero independent source groups are established**; do not treat 20 executions as 20 independent source groups.

The separate RQ1 restored 30-execution cohort is not used. No reviewer submissions, human labels, coordinator assignments, or blinding keys were inspected for this audit.

## R1 configuration and source-bound evidence

The repository's frozen `evaluation/r1_v3_generalization/blinded_review/requirement_scope.v3.json` names five protected objects and `living_room_table`, and defines frame 10 through terminal recorded snapshot as the intended interval. However, it explicitly records independent human review and event labels as pending, numerical parameters as unapproved, and all-team approval as false. It is therefore a selected scope for review, not an execution-bound approved Drafter configuration.

The prior inventory lists the protected objects in the scene and provides a scene XML hash receipt. The prior R1 package build also names a focal object per selected case. Neither supplies a currently accessible source HDF5, a freshly verified run-to-file identity, a complete execution-bound target/protected-object/support-surface role map, or a validated source-selector evidence bundle for these RQ3 requests. The 10-to-terminal interval cannot be bound to the current bytes while the source is unavailable.

## Request construction

No diagnostic Drafter request was created. Building even a non-admitted diagnostic request would require source selectors and values tied to the exact HDF5 bytes, the full execution-specific mapping and scope, and validated source/evidence records. With all exact HDF5 paths absent, those checks cannot pass. The approved `DRAFTER_GENERATION_MANIFEST.csv` remains empty.

## Outstanding approvals and data restoration

Restore the exact source bytes to an authorized, documented location (or provide a new authoritative source-location receipt) and verify their SHA-256 and embedded `global_episode_id`; do not substitute a similarly named episode. Then obtain explicit project-owner decisions on source reuse, final R1 scope/configuration and evidence policy, independent R1 reference/adjudication/freeze, case eligibility/partition/leakage review, Critic exposure clearance, and the RQ3 evidence arms/model/run/repetition/interval/cost protocol. The unsigned decision sheet is in `OWNER_REVIEW_DECISION_SHEET.md`.
