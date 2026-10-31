# Illustrative configurations — not validated experiments

- [A_LIBERO_FIVE_OBJECTS.json](A_LIBERO_FIVE_OBJECTS.json): historical five names and
  `living_room_table`, task00 identity, expected OpenVLA OFT checkpoint, frame10 and
  ten settling commands. This **new generalized profile is not a frozen V3 config**.
  It requests all relevant support geometry rather than copying old table IDs.
- [B_SYNTHETIC_THREE_OBJECTS.json](B_SYNTHETIC_THREE_OBJECTS.json): invented scene with
  widget/vial/carton IDs on `workbench_B`, eight illustrative settling commands and
  frame8. Shape capability requests include convex/mesh support; no such adapter or
  physical validation is claimed.
- [C_SYNTHETIC_MULTIPLE_SURFACES.json](C_SYNTHETIC_MULTIPLE_SURFACES.json): three
  illustrative objects, stationary bench and time-varying tray, with one object's
  designated support set containing both. Time-axis boundaries are recorded anchors,
  not invented synchronization values. A validated dynamic-support adapter is required.

All have `validation_status=illustrative_unvalidated`, null physical calibration,
unknown phase uncertainty and null source digests/certificates. Null means **unknown**,
never zero error or permission to skip evidence. Examples describe intended contracts,
not runnable evidence files. Synthetic names/counts/indices describe hypothetical test
fixtures; they are not physical measurements or empirical outcomes.

The [schema](../R1_V2_CONFIG_SCHEMA.json) validates structure. `validate_spec.py`
also checks equal protected-object/mapping key sets, declared surface references,
unique surface IDs, axis/anchor compatibility and explicit-boundary ordering. Those
checks are Phase 1 configuration linting, not V4's evidence admission or event detection.

Before a future runtime admits a profile: resolve source hashes, actual recorded
boundaries, model/object/surface bindings, units/transforms, capability certificates,
coverage and calibration as specified in [EVIDENCE_CONTRACT.md](../EVIDENCE_CONTRACT.md).
Setting `validation_status` in JSON does not validate an adapter or establish safety.

## Phase 1.6 schema revision

All examples now use configuration schema 2.0.1 with a required manifest 1.0.0;
requirement remains R1 2.0.0. Their binding versions/hashes are unresolved and their
purpose is analytical_fixture; none is an admitted empirical configuration. Original
example versions remain in Git at the Phase 1.5 baseline.

Example C describes deferred moving-support capabilities and is outside restricted
V4. Example B requests non-BOX shapes and is also outside that profile. Neither is
evidence of implemented support. [D_STATIC_TWO_ROOT_BOX.json](D_STATIC_TWO_ROOT_BOX.json)
is a separate structural fixture: two static BOX roots, explicit singleton/union
mappings, no handoff trajectory. It tests schema design only, not physical validity.
A's BOX request is within intended capability shape but remains empirically blocked.
Legacy comparison purpose is separate; fixture purpose never authorizes empirical use.
