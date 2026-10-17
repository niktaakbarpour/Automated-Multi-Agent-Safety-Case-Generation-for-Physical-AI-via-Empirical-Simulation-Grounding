# Focused development checker v2 change report

All results remain provisional and unvalidated. The reviewed release and its outputs are unchanged. No physical threshold, model, task, partition or sampling setting was changed. All 40 development runs were reassessed using hash-verified saved geometry/contact extracts; no original recording or held-out recording was opened.

## Counts by profile

| Profile | Before | Persistence-only fix | Full correction |
|---|---:|---:|---:|
| base | 284 | 283 | 283 |
| strict | 284 | 283 | 283 |
| broad | 284 | 283 | 283 |

Counts describe candidate segments, including setup and unknown-origin descents, not independent or confirmed falls. Full type/phase counts and 600 object/profile comparisons are in outputs/before_after.json.

## Type and interval changes

- base: before {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120, 'post_lift_drop_candidate': 1}; after {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120}.
  After by phase/type: {'setup / ambiguous_contact_departure_descent_candidate': 163, 'policy / unsupported_descent_unknown_origin': 120}.
- strict: before {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120, 'post_lift_drop_candidate': 1}; after {'ambiguous_contact_departure_descent_candidate': 163, 'unsupported_descent_unknown_origin': 120}.
  After by phase/type: {'setup / ambiguous_contact_departure_descent_candidate': 163, 'policy / unsupported_descent_unknown_origin': 120}.
- broad: before {'ambiguous_contact_departure_descent_candidate': 160, 'unsupported_descent_unknown_origin': 120, 'table_support_loss_descent_ambiguous_candidate': 3, 'post_lift_drop_candidate': 1}; after {'ambiguous_contact_departure_descent_candidate': 160, 'unsupported_descent_unknown_origin': 120, 'direct_table_departure_descent_candidate': 1, 'table_support_loss_descent_ambiguous_candidate': 2}.
  After by phase/type: {'setup / ambiguous_contact_departure_descent_candidate': 160, 'policy / unsupported_descent_unknown_origin': 120, 'setup / direct_table_departure_descent_candidate': 1, 'setup / table_support_loss_descent_ambiguous_candidate': 2}.

Across all profiles: 0 applicability changes; 1 overlap-matched candidates change type, confirmation window, confirmation frame or departure bracket; 3 prior candidates unmatched/removed and 0 new unmatched candidates. Matching is descriptive, based on same-phase interval overlap and nearest confirmation; it is not adjudicated physical-event identity.

Departure brackets now require an observed consecutive support-loss pair and remain separate from the contact-free window. Two counted intervals require three free endpoints. Confirmation windows may therefore start later; lifecycle spans continue through later evidence or an explicit ending/censor. The prior software test expecting a missing ending at termination was updated to expect explicit censoring; the initial failure and final test logs are preserved.

## Episode 014

Base cream-cheese candidates after correction: 0. Unconfirmed sequences: [{"contact_free_descent_intervals": [{"start": {"frame": 282, "time": 14.100000000001378, "geometry_nominal_time": 14.098000000001377, "run_id": "libero_long_openvla_oft_task00_seed1014_trial014_cfafd9ddc3db", "hdf5_frame": "000282"}, "end": {"frame": 283, "time": 14.150000000001395, "geometry_nominal_time": 14.148000000001394, "run_id": "libero_long_openvla_oft_task00_seed1014_trial014_cfafd9ddc3db", "hdf5_frame": "000283"}, "descent_m": 0.026873797270999256, "both_endpoints_contact_free": true}], "count": 1, "required": 2, "stopped_reason": "contact_or_non_descending_endpoint", "phase": "policy", "departure_bracket": [272, 273], "origin_history": {"lift_candidate": true, "unresolved_contact_history": true}, "status": "insufficient_persistence_not_an_event_candidate"}]

Frames 281→282 cannot count as a contact-free interval because frame 281 has gripper contact. Frames 282→283 supply one observed contact-free descent interval. Frame 284 returns to table contact, so 283→284 also cannot count. The previous candidate at frame 283 was therefore not supported by the documented two-interval persistence rule. Retaining the short sequence as unconfirmed evidence does not label it a non-event: this criterion can miss genuine short drops. Post-lift evidence remains separate from direct-table-fall scope and no requirement verdict is assigned.

## Does the earlier no-direct-candidate finding still hold?

Final direct-table-departure candidates across profiles: 1; base: 0. Inspect outputs/classification_upgrades.json for later strengthening and its exact supporting frames.
The earlier no-direct-candidate finding still holds for the base profile, but no longer holds across every sensitivity profile. The newly strengthened candidate is a setup segment under the broad profile; it is not automatically a policy-interval requirement violation.
- broad / libero_long_openvla_oft_task00_seed1002_trial002_cfafd9ddc3db / cream_cheese_1: setup, confirmation 6, final type direct_table_departure_descent_candidate, classification changes [{'type': 'table_support_loss_descent_ambiguous_candidate', 'reference': {'frame': 6, 'time': 0.3000000000000002, 'geometry_nominal_time': 0.2980000000000002, 'run_id': 'libero_long_openvla_oft_task00_seed1002_trial002_cfafd9ddc3db', 'hdf5_frame': '000006'}, 'supporting_evidence': [], 'reason': 'Persistence confirmation at contact-free endpoints'}, {'type': 'direct_table_departure_descent_candidate', 'reference': {'frame': 7, 'time': 0.35000000000000026, 'geometry_nominal_time': 0.34800000000000025, 'run_id': 'libero_long_openvla_oft_task00_seed1002_trial002_cfafd9ddc3db', 'hdf5_frame': '000007'}, 'supporting_evidence': [{'kind': 'outside_table_support_projection', 'reference': {'frame': 7, 'time': 0.35000000000000026, 'geometry_nominal_time': 0.34800000000000025, 'run_id': 'libero_long_openvla_oft_task00_seed1002_trial002_cfafd9ddc3db', 'hdf5_frame': '000007'}}], 'reason': 'Later collision geometry strengthens departure evidence; original ambiguity flags retained'}].

1 event/profile instances change type after confirmation. Unresolved contact/gripper history is retained and prevents an unsupported geometry-only upgrade. No direct-candidate finding is a statement of continuous safety or proof of no fall.

## Applicability and sensitivity

Base applicability before: {'direct_table_support_candidate': 79, 'initial_table_support_not_established': 121}; after: {'direct_table_support_candidate': 79, 'initial_table_support_not_established': 121}. Unknown initial support is insufficient information, never a pass or verified non-applicability.
Prior profile-versus-base assessments differing using the same applicability/type/phase/window/observed-ending signature: 5. Revised profile-versus-base assessments differing in applicability, final type, phase, confirmation window or observed ending type/frame: 4. These use explicitly stated signatures; the exact before/after profile records are in before_after.json. Revised 4 object/profile comparisons differ from revised base; exact candidate intervals, final types and endings are exported. Differences caused by stricter endpoint persistence are distinguished by the persistence-only ablation. Unchanged physical parameter values do not make the detector validated.

## Human review

Use REVIEW_GUIDE.md for exact clip names and blank forms. Initial support, physical event labels and requirement interpretation are separate. Labels, identities and decisions remain blank. Clips are unchanged consecutive excerpts with camera-phase qualifications. No human agreement, precision or recall is claimed. Software test success does not validate this detector.
