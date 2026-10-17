# Provisional development results

Processed 40 development runs and 11409 recorded frames; 200 object/run rows. Ten held-out recordings were not processed.

Initial support categories: {'direct_table_support_candidate': 79, 'initial_table_support_not_established': 121}.

Physical candidate counts (setup and policy segments, not independent falls): {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120, 'post_lift_drop_candidate': 1}.

Measurement/sequence gaps across object reports: 0. No requirement verdicts, human labels, validated precision/recall, or continuous-safety claims are assigned.

## Sensitivity

- base: {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120, 'post_lift_drop_candidate': 1}
- strict: {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120, 'post_lift_drop_candidate': 1}
- broad: {'ambiguous_contact_departure_descent_candidate': 160, 'unsupported_descent_unknown_origin': 120, 'table_support_loss_descent_ambiguous_candidate': 3, 'post_lift_drop_candidate': 1}

5 object/profile assessments differ from base in initial category, candidate type/interval or contact ending. Full differences are in outputs/sensitivity_differences.json. Sensitivity stability is not validation.

## Supplied example agreement and unresolved interpretation

Episode 002: setup airborne/descent evidence is retained; absent initial table support and later floor contact do not create an automatic policy violation. Strict support filtering may not establish origin at deeply penetrating frame zero, so unknown-origin setup descent is deliberately reported.

Episode 014: inspect candidate output and clips for the bilateral-contact lift followed by unsupported descent and table recontact. Post-lift drop remains distinct from a direct table fall; no requirement violation is assigned.

Episodes 000/001: initial airborne objects and settling motion are reported rather than passed. Selected clips cover setup and early policy only; full development bundles were processed for detector candidates, without establishing continuous absence of falls.

No independent human labels exist in this release. Therefore there is no measured detector-versus-human agreement or disagreement rate. Unknown support, contact-force ambiguity, rotation-driven AABB motion, short events and phase uncertainty remain unresolved. Synthetic test successes are separate from recorded candidate outputs.

Candidate phase breakdown: 163 ambiguous-contact descent segments during setup; 120 policy-phase descents of objects already unsupported at the interval boundary; one policy post-lift drop candidate (episode 014). No direct table-departure fall candidate is established by this development configuration. These counts are not independent confirmed falls.
