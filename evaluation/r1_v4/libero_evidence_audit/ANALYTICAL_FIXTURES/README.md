# Exact analytical declarations

These eleven JSON fixtures stipulate physical interpretations; they are not simulated trajectories, original LIBERO records or independent empirical references. Coordinates/times in their bundles are exact analytical inputs. No estimator or physical threshold is tested. The Phase 2A runtime tests admission, applicability, missing evidence, uncertainty and outcome logic on those declarations.

| Case | Expected analytical outcome |
|---|---|
| stable_supported | Qualified N on all explicit static cells |
| supported_sliding | U: no admitted dynamic negative coverage |
| intentional_lifting | U: stipulated handling excludes candidate; no whole-domain negative |
| fall_after_support_loss | V: all linked event premises stipulated |
| post_lift_release | U: excluded drop does not clear remaining domain |
| initially_unsupported | NA: explicitly established boundary support absence |
| ambiguous_contact | U: boundary support unresolved |
| missing_measurements | U: necessary local geometry missing |
| timing_mismatch | IC: necessary clock incompatible |
| unsupported_geometry | IC: required shape capability unsupported |
| invalid_measurement | U: local geometry record explicitly invalid |

Intention is only the lifting case's descriptive name. Runtime exclusion uses stipulated established handling, never inferred intention. Initial non-applicability is a declared support exclusion, not missing contact treated as absence. Local invalidity differs from an incompatible measurement foundation. Every result has physical_safety_conclusion=false and empirical_profiles_enabled=false.

Rebuild with `python3 -m evaluation.r1_v4.libero_evidence_audit.analytical`. Test checked-in bundles with `python3 -m unittest evaluation.r1_v4.libero_evidence_audit.analytical -v`. Interpretation and expected result are outside the runtime bundle and are never empirical labels.

These bundles contain logical event/support premises rather than numerical sliding or free-flight trajectories. A future calibrated measurement producer still needs independent trajectory/reference tests. The present fixtures only verify that the infrastructure preserves those distinctions when explicitly supplied and abstains when necessary premises are absent.
