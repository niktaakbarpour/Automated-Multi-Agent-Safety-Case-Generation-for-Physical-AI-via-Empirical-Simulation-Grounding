# Task 7B Task 8C compatibility adapter

## Scope and boundary

`task8c_adapter.py` (`task8c-r1v3-source-adapter-1.0.0`) converts the Task 8C HDF5 source into the frozen R1 v3 saved-frame fact schema. It extracts source measurements and derives geometry-qualified support evidence. It does not import or invoke the frozen checker's decision functions. `cohort_execution_wrapper.py` is the later call boundary; it refuses execution for cases without verified runner provenance. It was not used to generate Task 8C classifications in Task 7B.

The adapter is scoped to the Task 8C protected object `cream_cheese_1`. It preserves all source cases and source groups in metadata. The checker configuration, threshold, applicability policy, event semantics and checker implementation remain unchanged.

## Source binding and fail-closed rules

- Verify the raw HDF5 SHA-256, source XML SHA-256, frozen manifest SHA-256, native geometry map hash, physical configuration hash and corrected entity inventory hash.
- Bind case ID, source execution ID and source group ID to the corresponding manifest row and source recording path.
- Verify the runner-source SHA-256 for execution-eligible cases. Refuse normal preparation if runner provenance is unverified; diagnostic extraction retains an explicit `checker_eligible: false` value.
- Validate XML, body count, geometry count, body names/owners, all entity geometry IDs, contact geometry/body IDs and names. Unknown or non-collision contact IDs fail closed.
- Reject duplicate/missing observations, invalid time values, action misalignment, incomplete contact bundles, malformed/nonfinite state or contact channels, source hash mismatch, and geometry-transform inconsistency.
- Reject protected-object contact with another object because the Task 8C cohort's target-to-object support chain is not needed and that unrelated object's XML/runtime local-transform discrepancy exceeds the frozen arithmetic allowance. The current cohort has no such target contacts. The adapter never substitutes an approximate object transform.

## Temporal projection

The Task 8C capture has 6,426 native samples at 2 ms and 258 saved observations at 50 ms. Saved frame `f` is bound to native sample `25*f`. The adapter checks all native timestamps, all `action_index` values, every contact row against `physics/ncon`, and the observation-to-native endpoint time match. It validates all intermediate 2 ms contact samples but passes only the 50 ms frame endpoints to the checker. Missing 50 ms frames are not filled from intermediate samples.

Frame 10 (sample 250, time 0.5 s) is the end of settling and is the frozen initial-support boundary. Frame 11 (sample 275) is the first monitored action endpoint. Frame 257 (sample 6425, time 12.85 s) is the terminal saved snapshot.

For sample 0 the captured action index is -1. For native sample `k >= 1`, the expected action index is `floor((k-1)/25)-10`. This preserves the ten settling actions followed by 247 stationary-hold actions and the frozen policy/action boundary.

## Geometry and coordinates

World body translation is `physics/body_xpos`; body quaternion order is MuJoCo w,x,y,z. The rotation formula matches the frozen `NativeGeometryIndex` scaled-quaternion arithmetic. For each required geom, world transform is reconstructed from its owning body's recorded pose and the frozen XML local pose: `p_geom = p_body + R_body p_local`, `R_geom = R_body R_local`. Collision-box corners are the exact frozen checker construction `product([-1,+1]^3) * half_size`, rotated and translated in world coordinates. The protected object's collision geometry is native geom 104, body 22; table collision boxes are geoms 10–14. Floor geom 8 and gripper geoms 76/77 and 79/80 are mapped from the frozen native geometry and physical configuration.

The target's all-collision-vertex pose, bounds and vertical motion are retained; no center-of-mass proxy is used. Local XML/runtime differences for relevant target/table boxes are required to be within the frozen `512 * machine_epsilon` arithmetic allowance. A separate comparison against direct historical native geometry is recorded in `SEMANTIC_EQUIVALENCE_REPORT.md`.

## Contacts and support

The capture runner copies `geom1`, `geom2`, `body1`, `body2`, `dist`, `pos`, and `frame` from MuJoCo contacts. It records `mujoco.mj_contactForce` as a six-value contact-frame force vector. The frozen v3 extractor uses geometry IDs, world contact position and signed distance; the checker does not use contact force or the contact-frame normal to infer load-bearing support. The adapter verifies and hash-binds those arrays but does not transform them or interpret them as a load measurement.

Support parents are built from the same frozen geometry-qualified rule: contact identities must resolve; only frozen table collision boxes may form the table edge; the table upper face must be horizontal; contact point, signed distance, face separation and projected overlap must agree within the checker arithmetic allowance. Contact counts alone never establish support. Table, floor, robot and all object geometry identities are validated against the XML-bound inventory. In this cohort the protected object's contact partners are table and floor geometries only; any object-to-object support contact is rejected pending an exact support-chain transform.

## Output and future execution

`prepare_case` returns 258 frame facts plus provenance and eligibility metadata. It preserves original checker outcomes by not assigning any. A future caller may pass facts to `execute_prepared_case`, which calls the unchanged R1 v3 `evaluate` function only if the adapter version, complete frame domain, monitoring interval and verified runner provenance all match. Task 7C must retain the two provenance-unverified cases as execution-ineligible records rather than treat them as physical negatives.
