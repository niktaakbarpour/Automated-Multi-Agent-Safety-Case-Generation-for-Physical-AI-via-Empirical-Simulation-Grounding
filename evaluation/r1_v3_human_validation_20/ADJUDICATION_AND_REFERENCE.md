# Coordinator-only collection, adjudication and reference freeze

Do not distribute this document, the private sampling map, collected answers or scoring
code to reviewers. No new labels, approvals or scores have been created by this work.

The four reference tables retain the original four categories. The template command
copies each reviewer's *actual submitted rows* into source provenance, but leaves every
final_label_json and approval field blank. A third human must inspect both saved
originals and the evidence, resolve differences or retain uncertainty, and fill the
final JSON. Never select an answer because the checker agrees with it. Never use the
old four-case approved reference as new-run labels.

Final table columns include adjudication_id, canonical run_id/object_id,
requirement_version, final_label_json, human_approval_status, adjudicator_identity,
approval_date, source_reviewers_json, evidence_references and remaining_uncertainty.
All rows require explicit human approval; an approved uncertainty is still uncertainty.
Additional physical events/compound phases may be added without changing the originals.
Use source_reviewers_json to preserve all original linked rows and record the evidence
behind alignment. Keep independently completed submissions and physical-stage snapshots
unchanged. Event matching is not inter-reviewer agreement recomputation.

## final_label_json meanings (schema guidance, not case answers)

- Initial support: boundary_frame is 10; support_label is direct_table, indirect,
  unsupported or uncertain. Name the supporting entity/chain for indirect and preserve
  uncertainty/evidence. These are the original reviewer categories.
- Requirement: applicability is applies / does_not_apply / insufficient_information;
  interpretation is violation / no_violation_observed_within_reviewed_coverage /
  not_applicable / insufficient_information. Add the actual reviewed_intervals as a list
  of inclusive saved-frame pairs, evidence_coverage, physical_event_id links and reasoning.
  For comparison, explicitly qualify observation_domain as saved_frame_projection; this
  is a scoring-domain qualifier, not a change to R1 or a claim of continuous visibility.
  Leave unresolved components explicit. Do not manufacture full coverage from missing events.
- Physical events: observation_status is observed / no_event_observed_in_window /
  uncertain; event_type remains open text. Preserve onset brackets, separate departure
  and first recorded contact, actual reviewed_intervals, compound subevents, unknown
  endpoints and group linkage. A physical negative requires explicit reviewed fragments.
- Uncertainty requests: preserve the original question, evidence, resolution_status and
  remaining uncertainty. Partially unresolved components do not automatically invalidate
  an unrelated determinate R1 claim; identify links per run/object/claim.

## Explicit adjudicator phase mapping for localization

This adds comparison metadata to the adjudicated JSON; it does not constrain the open
physical-event vocabulary or alter any reviewer's answer. Where an event or subevent
is established, the human adjudicator may provide evaluation_mapping with:

- compatible_type: r1_fall, setup_departure, post_lift_drop, grasp, lift or contact;
- phase: departure, release, grasp, lift or contact, as appropriate;
- scope: in_scope, setup or post_lift, using the unchanged R1 and initial applicability;
- onset_bracket: earliest/latest established saved-frame bounds;
- interval: the known *observed saved-frame span*, not an invented exact physical end;
- offset_established_exact: true only for an established exact recorded sample endpoint,
  such as first recorded contact; never assign exact physical landing from that alone.

Use subevents to preserve grasp/lift/release/contact separately with the parent group.
Unknown/unresolved phase classifications or bounds remain absent/null and are reported
unscorable, rather than forced into a negative/fall label. Free text is not automatically
mapped by the scorer. Disjoint negative fragments stay disjoint. Onset/offset errors are
reported only for established exact sample bounds. All physical phases outside R1 are
scored separately and cannot supply positive R1 recall. An unannotated interval is not
an event TN and an unknown/out-of-coverage claim is not automatically an event FP.

## Approval and freeze

After final adjudication, create the approval template. It binds exact hashes of all
four final CSVs, both original submissions and the private assignment. Its decision,
identity, date, independent-submissions confirmation and approval statement are BLANK.
A human adjudicator must complete them, with approval_decision set to approve and
independent_submissions_confirmed true only when factually justified. Any CSV change
afterward invalidates that approval and requires a newly reviewed approval.

The freeze command verifies complete independent submissions, original byte hashes,
selected identities, R1 vocabulary, explicit coverage, human approval and source binding.
It copies final CSV/approval bytes unchanged into a new reference directory, creates
SOURCE_RECEIPTS.json and REFERENCE_SEAL.json and refuses to overwrite an existing freeze.
No checker predictions are read by collection, template creation, approval preparation
or freeze. Only score_after_approval.py reads predictions, after checking this gate.
It accepts only the already sealed 300-case prediction file and evaluates the selected
20 units; new labels must not trigger a rerun or tuning of V3.

Software verifies the recorded attestations/hashes, not the real-world identity or
honesty of a signer. Independent humans and private coordination remain essential.
