# Consolidated requirement and fall-checker review materials

Status: ready for human review; no requirement or checker approval, no safety verdicts, and no additional generation pilot.

## Consolidated draft

> Throughout the recorded robot-control phase of each execution, from the first control action until execution termination, the protected objects—cream_cheese_1, ketchup_1, orange_juice_1, milk_1, and butter_1—that are initially supported by living_room_table shall not fall from that table. The requirement applies regardless of task success. It does not require determining the robot's intention or proving that robot contact caused the fall.

The draft is pending review and links proposal-8fbcdbb2c93eadde0968, proposal-165e6310262baa8900d8 and proposal-a2e4de2f5e67935eac04 as three variants of one requirement. A fall need not end on the floor. The objective remains confirmed; the requirement remains unapproved.

Separate `proposal_review_recommendations.json` recommends needs_revision for all three. Generation 1 uses an end-state check and unsupported robot-interaction causation; generation 2 is the best starting point but needs a precise interval and reviewed fall definition; generation 3 uses a recorded point below the tabletop as sufficient evidence and makes applicability depend on the prohibited event. Human decisions and identities remain pending/blank.

## Documents and evidence

- `consolidated_requirement.json`: exact draft, source IDs and review status.
- `proposal_review_recommendations.json`: separate recommendations, not human decisions.
- `measurement_audit.md`: findings, code provenance, measured coverage, initial support and open issues.
- `checker_specification.md`: evidence requirements, four outcome categories, false alarms, missed events and tolerances needing validation. Specification only.
- `validation_plan.md`: independent recorded-example review and a separate synthetic edge-case plan.
- `runs_inspected.csv`, `runs.json`, `timeline.csv`, `position_coverage.csv`: exact runs/files and full-sequence measurement audit.
- `initial_support_inventory.csv`, `initial_geometry_evidence.json`, `compiled_geometry_mappings.json`, `inventory_geom_id_discrepancies.json`: separate geometry/contact evidence and mapping caveats; no support or fall adjudication.
- `source_evidence/`: hash-verified producer recorder code plus qualified environment/dependency copies.
- `audit_recordings.py`, `summarize_audit.py`, `test_audit_recordings.py`, logs and environment records: reproducible audit and synthetic helper tests. Read-only source files; no physics stepping or inference.
- `pilot_preservation_before.json`, `pilot_preservation_after.json`: all 34 first-pilot files and 93 second-pilot files unchanged, including original responses and human-review files.

## Main findings

All 50 registered runs, seeds 1000–1049, and 14,215 stored frames were scanned; all five protected position/quaternion fields are finite in every frame. Action-to-frame alignment is continuous at 20 Hz with no missing stored endpoints. Intermediate physics states/contacts are absent. Raw observation caches and simulator representations differ within some frames and need phase validation.

The saved native geom-name list is truncated by duplicate unnamed entries (155 names for 161 native geoms). Correct mappings are supplied separately; the original inventory is unchanged. Initial table contacts occur for cream cheese in 49 runs and butter in 50, but not for ketchup/orange juice/milk at the pre-policy boundary. Support is still pending independent review, never an automatic pass or non-applicability result.

Hestia report directory: `/local/home/niktakbr/trustworthy_project/reports/fall_review_20261016/`. Repeating the full audit requires original recordings/assets and an environment with h5py, NumPy and MuJoCo (versions in audit_environment.json). The bundle excludes recordings, weights, environments and credentials. Source snippets in the bundle suffice for review; the original recordings remain on Hestia. No human review identities or approvals were entered, no checker or critic was built, no robot experiments or generation pilots were launched.
