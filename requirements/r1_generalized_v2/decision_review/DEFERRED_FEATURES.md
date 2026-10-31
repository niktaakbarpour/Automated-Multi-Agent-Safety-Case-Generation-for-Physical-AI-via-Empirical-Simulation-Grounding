# Recommended exclusions from initial V4

These are DEFER recommendations, not silently approved scope changes. See the
[matrix](D01_D11_DECISION_MATRIX.md) and [amendments](PROPOSED_AMENDMENTS.md).

| Decisions | Feature excluded initially | Required behavior | Re-entry evidence/gate |
|---|---|---|---|
| D02.c/D06.d | Moving/articulated support roots; active/deformable bodies | Essential unsupported capability => IC, not NA or safe. Local uncertain motion within an admitted profile => U. | Time-varying geometry, load/dynamics model, calibrated transforms and independent capability tests. |
| D02.c/D04.c | Dynamic handoffs, multiple-parent load inference, re-arming after placement | Preserve physical records; unresolved suffix U, no implicit support root or new applicability epoch. | New episode/scope semantics, witness profiles and analytical plus empirical tests. |
| D03.a | Containment, unsafe release, post-grasp drop, collision or causal blame as R1 extensions | Keep separately named candidate requirements; no implementation here. Established handling drops remain excluded from narrow R1. | Separate hazards, evidence contracts, positive references and denominators. |
| D06.d/D11.d | Vision-only inference and additional benchmarks | Reject unsupported essential contracts; no overlap-based support/grasp/fall inference. | Camera calibration, occlusion/identity/geometry/clock contract and independent benchmark evaluation. |
| D06.d/D11.d | General meshes/convex/spheres as initial empirical adapter scope | IC for unsupported essential representation; no BOX substitution. | Shape-specific predicates/tests. Existing sphere analytical fixture remains future scope, not an executable BOX adapter test. |
| D07.c | Empirical hysteresis/persistence and automatic threshold tuning | No numerical default; no short-fall exemption. | Independent calibration and sensitivity/detection-limit analysis, not NV-label fitting. |
| D08.c | Dynamic/handling/post-lift negative-domain composition | Record qualified individual phases; unresolved uncovered cells prevent a full negative. | Approved bridge rules and support/scope witnesses over every requested cell. |
| D10.d | New simulations, controlled perturbations, dataset expansion | Plan only; no runs in this task. | Separate authorized protocol with locked partitions and evidence/reference procedure. |
| D11.d | Empirical certification/generalization claims | Capability declaration and structural conformance are not certification. | Scoped empirical evaluation and independent references, with limitations. |

Multiple static surfaces across objects and arbitrary object counts are **not**
deferred structurally. Static designated unions may be represented per object;
unvalidated handoff inference is deferred. All empirical support predicates still
require admission. No claim of validating all LIBERO Long tasks follows.
