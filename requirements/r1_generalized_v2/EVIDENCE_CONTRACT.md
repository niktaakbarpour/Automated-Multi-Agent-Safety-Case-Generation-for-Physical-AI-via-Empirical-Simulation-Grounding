# Evidence contract — normative proposal

This contract specifies what an adapter must substantiate, not a promise that all
simulators record it. Interpretation follows [FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md).
Requiredness is **claim-specific**: R=required, C=conditionally required, O=optional,
X=unsupported as sole proof. The absence of a C field can require abstention or IC
when its condition holds. No optional modality is secretly mandatory for every case.

| Field/capability | Class | Admission and missing-data rule |
|---|---|---|
| Execution, object, surface identities and adapter/schema version | R | Stable IDs; complete namespace/model binding; no cross-scene native-ID assumption. Ambiguity => U; incompatible essential binding => IC. |
| Closed-scene roster/absence certificate | C | Required to report verified_absent; missing detection is X as absence proof. |
| Object collision/support geometry | R for geometry-based present-object claim | Shape, units, local frame and source/model hash. Unsupported representation => IC; transient missing sample => U. Visual mesh is not automatically collision geometry. |
| Surface geometry/support role and motion | R for present-object claim | Resolve every designated ID and its support regions/normals; include all relevant collision pieces. Moving surfaces require valid time-varying transforms and a support model. |
| World/common-frame poses and orientations | R for state-based witness | Frame IDs, metric units, quaternion convention, finite values, transformations and uncertainty. Do not silently change handedness or root/COM definitions. |
| Contact observations, normals/forces, or validated alternative support witness | C | Contact backend must certify its scope/completeness. Geometric contacts are direct simulator observations, not direct load-bearing evidence. Forces are required only if the selected support profile depends on them. Missing force cannot be fabricated or assumed present in raw HDF5. |
| Robot/gripper identity, state and pose | C | Required for applying a handling exclusion unless a different validated holding witness exists. Finger closure/visual overlap alone is X as grasp proof. |
| Velocity/acceleration | O/C | Direct or derived status must be explicit. Finite differences can be used only across valid intervals with uncertainties/correspondence; acceleration need not establish gravitational causation. |
| Camera frames and original source indices | O/C | Required if visual corroboration is part of the admitted witness or state evidence alone is inadequate. Camera identity, decoding coverage and actual inspection coverage differ. Missing frames cannot be interpolated into proof. |
| Simulator state/event timestamps | R | Clock definition, origin, uncertainty, ordering and phase. Input event labels are not accepted as physics truth without a validated producer contract. |
| Transforms to common frame and gravity direction | R for motion/geometry comparison | Source/target frames, units, validity interval and uncertainty; gravity alignment cannot be assumed for new scenes. |
| Initial/terminal observations and boundary anchors | R | Explicit policy/settling semantics and terminal/censoring status. Do not move boundaries to the first/last good frame. |
| Task instruction and target-object list | O/C | Required for interpreting experiment/task provenance or an explicitly task-conditioned requirement; not a causal or safety label. R1 protection does not silently exclude targets. |
| Artifact paths, source hashes, derived-code/config hashes | R | Hashes bind actual immutable bytes; filenames/receipts alone do not prove fresh payload identity. Preserve original/derived distinction. |
| Temporal alignment and missing intervals | R | Separate nominal index joins, state cache phase, camera exposure and true synchronization. Known/unknown bounds must be explicit per modality. |
| 2D overlap, success/failure, AI explanations | X as sole physical proof | Can navigate evidence or propose hypotheses; never substitute for measured support/motion or a reference label. |

## Layered contract and evidence validity

1. Structural configuration: required keys/types/enums/references and unique IDs.
   Failure produces `invalid_configuration`, not empirical non-applicability.
2. Foundational adapter contract: object/surface/model binding, geometry capabilities,
   clock/frame semantics and provenance. Required unsupported/incompatible capability
   produces IC for affected objects. Unaffected objects retain their own results.
3. Sample/event evidence: per-object intervals with finite admitted measurements,
   contact completeness, phase/correspondence and uncertainty. Missing/corrupt local
   segments remain U and coverage holes; they need not erase an unrelated valid event.
4. Claim witness: support/fall/handling/clear-coverage certificate referencing exact
   admitted evidence and inference-profile version. No AI text is a certificate by itself.

If a backend cannot certify all contacts, absence of entries cannot establish no
support. A validated alternative can still establish a specific positive support
witness. A single support candidate failing a strict detector is not support absence.
Multiple contacts may be loads or alternative supports; their roles require evidence.

## Direct, derived and interpreted records

Direct observations retain their producer and units: saved poses, simulator geometry,
recorded contact bundles, images and native timestamps. A contact's physical meaning
depends on simulator semantics. Derived indicators include collision bounds, support
chains, velocities, frame mappings and checker events; retain source IDs, algorithm,
version/hash, uncertainty and exact input windows. AI descriptions/recommendations
are interpretations with reviewer/model/exposure/inspection provenance, never raw facts.

## Coverage and reproducibility

Represent domain as a union of explicit intervals/cells per object, modality and
claim. Record requested, available, decoded, actually inspected, invalid and qualified
negative domains separately. Mark sequence ends and event components censored. Never
bridge a gap because a plot is smooth or a video player can interpolate frames.

Missing raw HDF5 does not automatically invalidate independently hash-bound, complete
exports for every limited claim; it prevents checks requiring raw regeneration or
unexported fields. Likewise, restoration cannot recover never-recorded forces,
camera exposure phases, higher-rate observations or post-terminal landings.

Freeze configuration, adapter/inference code, source inventory and evaluation protocol
before new empirical evaluation. Per-object outputs bind all relevant versions and
evidence. Source preservation receipts are separate from scientific validity. No
V4 reference may be generated from V4 predictions and then called independent truth.
