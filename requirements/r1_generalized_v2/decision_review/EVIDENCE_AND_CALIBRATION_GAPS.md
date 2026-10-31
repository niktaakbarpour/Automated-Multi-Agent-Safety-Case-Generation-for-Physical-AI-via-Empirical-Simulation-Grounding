# Evidence gates and calibration gaps

No new measurements or calibration have been obtained in Phase 1.5. This ledger
distinguishes known provenance from missing scientific support. Restoration is not
authorized by a design recommendation; it also cannot recover fields never recorded.

| Gate | Decisions | Existing evidence / limitation | Needed to unblock | Effect until resolved |
|---|---|---|---|---|
| G01 Identity/complete geometry | D01.b/c D02.d D06.c D11.c | Source-bound inventories and native geometry binding exist for historical scene; omitted table ID15 documented in old mapping. | Fresh model-bound complete collision roster, role and alias checks, absent-instance certificate if used. | Incompatible essential binding IC; transient ambiguous identity U; no absence exemption without certificate. |
| G02 Support interpretation | D02.b/d D06.c D08.d | V3 uses static sampled upward BOX geometry and invariant paths; contact alone is not force. | Recorder contact scope/order/completeness audit, geometry/support inference assumptions with independent analytical checks and empirical counterexamples; forces/normals only if profile needs them. | No admission of load-bearing support from bare contact; profile unsupported IC or local insufficient witness U. |
| G03 Spatial uncertainty | D03.c D07.b | Arithmetic roundoff is known code policy, not calibrated physical error. | Units/transforms/COM-or-justified-rigid-reference, gravity direction, collision geometry/pose uncertainty, signed separation semantics and validated uncertainty propagation. | Boundary-overlap U; incompatible model IC. No fabricated distance threshold. |
| G04 State/contact phase and t0 | D03.c D06.c D07.b | Frame10 and transition schema checked historically; nominal cadence/lag do not establish phase bounds. | Producer call order, state-cache/contact timestamps and boundary inference uncertainty, with read-only code/data evidence where available. | Cannot admit a claim needing unresolved phase; state-only claims require their own contract. No shifting t0. |
| G05 Camera exposure | D06.c D07.b D08.d | Decoding and matching frame labels do not establish exposure timing. | Per-camera producer/exposure convention and bounds relative to state/action clocks if used temporally. | Images may navigate/corroborate at qualified scope; no synchronized physical witness from indices alone. Optional camera unknown does not invalidate independent admitted state evidence. |
| G06 Raw-source completeness | D06.c D11.c | Phase 1 audit reports raw HDF5 absent on Hestia, preserved hash-bound exports available. No fresh payload inventory undertaken here. | Determine claim-specific needed fields; restore exact source only if required and authorized. Verify fresh hashes and export correspondence if regeneration needed. | Missing raw not blanket IC; missing required exported measurements U/unsupported profile IC as appropriate. |
| G07 Negative-domain certification | D08.d | V3 qualified static windows, abstains on unresolved motion. | Same-claim source/clock/dependency consistency, transition cell ownership and negative certificate justification; no automatic intersample interpolation. | Partial windows retained, requested-domain U on gaps/conflicts. |
| G08 Reference positives and splits | D10.c | Old cohort has no confirmed positive violations; references AI-origin/provisional, with prior reviewer exposure. | Independent applicable positive/negative verification, adjudication, provenance and disjoint natural/controlled partitions. | No human-validation claim, positive recall or population accuracy from old agreement. |
| G09 Profile conformance | D11.c | Schema/examples validated structurally only. | Version compatibility matrix; analytical capabilities, unsupported cases, tamper/replay checks; empirical scope record distinct from conformance. | No self-certified empirical validity from validated_contract or an artifact hash. |

Calibration protocol proposal: define measurands and intended predicates first;
identify producer/reference and timestamp phase; derive uncertainty sources and
propagation; predeclare acceptance limits from required discriminability and evidence,
not desired checker scores; assess boundary/short-event sensitivity on independent
fixtures; freeze calibration identity and validity scope before held-out evaluation.
No numerical values, sample sizes or precision targets are invented here.

All operations remain on Hestia under `/disk/1`; no research writes to `/disk/0`,
Alliance compute, Sea access, new experiments or evidence restoration occurred.
Hash preservation demonstrates byte identity, not empirical truth.
