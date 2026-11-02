# Calibration feasibility

Every physical calibration gate remains open. No threshold is proposed or fitted. Observed residuals and nominal simulator settings are not physical uncertainty bounds. Frozen NV cases/held-out labels are excluded.

| Quantity | Available measurements | Candidate method | Required references / current sufficiency | Status |
|---|---|---|---|---|
| Geometry transforms | BOX half-sizes, world geom poses, inherited recomposition residuals | Reproduce body/local/world transforms from restored arrays; propagate serialization and arithmetic separately | Original XML/body/geom arrays and independent orientation checks; originals absent | CONDITIONALLY_SUPPORTED investigation |
| Physical geometry tolerance | Collision bounds, signed separation | Compare independent clearance/contact references; sensitivity analysis | Verified separated/touching/penetrating/edge cases; no independent labels here | BLOCKED_ON_EVIDENCE |
| Support/contact interpretation | IDs/dist/pos, saved static poses, historical constraints | Validate force-free equilibrium alternative or contact-force profile, including competing support | Independent direct/indirect/side-contact/held/sliding cases; contact normals/forces not recorded | BLOCKED_ON_EVIDENCE |
| Downward translation | Corresponding collision shapes; historical native velocities | Bound gravity-frame rigid-body translation and rule out rotation/reference changes | Independent fall/rotation/sliding/lifting/post-lift examples including brief events | Algebra feasible; physical inference BLOCKED_ON_EVIDENCE |
| Persistence/hysteresis | Saved endpoints | Estimate sensitivity and missed-event limits using independent multi-rate/event references | Credible onset bounds and short events; none independent here | BLOCKED_ON_EVIDENCE; no minimum-duration exemption |
| Recording interval | Saved indices/times and nominal control rate | Inspect intervals/discontinuities and phase bounds on originals | Full restored sequence and event order | Structural checks feasible; physical coverage BLOCKED_ON_EVIDENCE |
| State/frame alignment | Prior endpoint/cache studies and nominal physics step | Reproduce source-specific residuals; keep bundles distinct and propagate phase bounds | Native arrays and matching producer dependency/binary provenance | CONDITIONALLY_SUPPORTED investigation; no calibrated profile |
| Camera alignment | Snapshot host times; historically stored images | Verify observable/exposure timing independently or keep camera qualitative | Producer camera/observable implementations and exposure reference | BLOCKED_ON_EVIDENCE; restoration may not resolve |
| Measurement precision | Binary64 fields and prior roundoff study | Separate representation, serialization, arithmetic and physical uncertainty | Original arrays plus independent geometry reference | Arithmetic study feasible; physical precision BLOCKED_ON_EVIDENCE |
| Negative coverage | Full exports and explicit cell infrastructure | Validate support per cell/transition and all joins | Independent eligible negatives, uncertainty and boundary cases | BLOCKED_ON_EVIDENCE; continuous/dynamic composition unsupported |

The four examples are development diagnostics, not a calibration reference dataset. Natural executions must stay separate from future controlled perturbations. No independently verified in-scope fall is established here. Setup flight and post-lift drops cannot be repurposed as R1 positives. Historical AI-only agreement remains exploratory.

Reference acquisition needs a frozen protocol, disjoint validation, verified positives/eligible negatives/NA/U, independent reviews, exposure disclosure and adjudication. Intended-study eligibility of absent objects remains a user protocol decision. Missing evidence and NA never become true negatives. Restoration cannot recover never-recorded contact forces/normals, exposure timestamps, substeps or post-terminal observations.
