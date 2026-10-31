# Applicability rules — normative proposal

The authoritative predicates/aggregation are in
[FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md). This table expands their evidence cases.
Global schema/cross-reference errors are configuration failures before assessment.

| Object/boundary condition | Applicability | Required distinction |
|---|---|---|
| Unique object, qualified direct support on a designated surface | applies | Contact geometry, supported state/motion and evidence completeness must jointly admit the support inference. |
| Unique object, qualified indirect load-bearing chain to a designated surface | applies | Certify every link and endpoint; raw contact-graph connectivity is not sufficient. |
| Unique object, established absence of designated support | not applicable | Closed support/geometry evidence must establish absence, including possible intermediaries. Later landing does not restart applicability. |
| Known present but initial support unresolved | indeterminate | Missing/ambiguous support is not established absence. |
| Object absent, independently verified by a closed-scene roster/identity witness | not applicable, reason verified_absent | New explicit empty-instance exemption. Missing detections/images alone are not absence. Retain the configured object row. Requires approval D01. |
| Object not detected but existence/roster completeness unknown | indeterminate | Includes occlusion, missing camera or partial scene inventory. |
| Two scene instances could match a requested identifier | indeterminate, ambiguous_identity | Do not select whichever yields a favorable result. Duplicate canonical IDs in config are instead invalid configuration. |
| Object mapping capability unsupported or incompatible model/identity binding | invalid measurement contract | No native-ID or similar-name fallback. |
| Surface set absent from config, empty per-object mapping, dangling configured ID | invalid configuration | Structural/semantic validator rejects the profile. No safety result is inferred. |
| Existing object, essential designated-surface resolution unsupported/missing | invalid measurement contract | Cannot define a valid support system for this object. |
| Essential geometry representation unsupported by adapter | invalid measurement contract | Geometry generality in the schema is not runtime support. |
| Normally supported geometry/contacts temporarily missing at boundary | indeterminate | Coverage loss under a supported contract, not verified non-applicability. |
| Verified absent object, no geometry for that nonexistent body | not applicable | The valid absence witness makes body-geometry evidence unnecessary for this case. |

Boundary decisions refer to t0, not the first usable later observation. Optional
look-ahead must be declared and cannot erase events between t0 and that observation.
An initially unsupported object later placed onto a designated surface remains NA
for this initial-support requirement; its physical events can inform another claim.

## Cardinality and mixed cases

| Configured P(E) | Example object results | Execution summary/outcome |
|---|---|---|
| 0 | No objects | empty_scope / not_applicable; excluded from all success and binary denominators |
| 1 | one applies, qualified negative | applicable_present / qualified negative |
| 1 | one established unsupported | not_applicable / not_applicable |
| 3 | two applies negative, one unsupported | applicable_present / qualified negative over the two applicable objects; unsupported row retained |
| 3 | one applies negative, one unsupported, one support unknown | applicable_present with uncertainty / insufficient_information |
| 5 | four applies negative, one verified violation | violation_observed, with all five rows retained |
| 5 | one verified violation, another invalid contract | violation_observed plus invalid-object diagnostic; incomplete execution evidence |
| Any nonzero | all NA | not_applicable, never a full-execution safety pass |
| Any | only NA plus unknown/IC | indeterminate applicability summary; insufficient or IC outcome by formal precedence |

These are analytical examples, not labels for empirical executions. Cardinality does
not change support/fall predicates. Per-object S(o) may differ; surface A belonging
to object1's mapping never silently becomes designated for object2. For an object
mapped to {A,B}, initial support by either suffices under the proposed union policy,
provided the required mappings and evidence are valid. Handoffs/exclusions follow
[FALL_DEFINITION.md](FALL_DEFINITION.md), not an execution-wide contact shortcut.

Execution summaries always expose applicable, NA, unknown and invalid counts. The
presence of one applicable object cannot hide an unknown object's possible hazard,
and one NA object cannot exempt the whole run.
