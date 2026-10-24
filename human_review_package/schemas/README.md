# CSV schema and legacy compatibility
CSV headers are the primary schema. Empty human fields mean pending/unknown, not a negative label or approval. Initial support labels: direct_table, indirect, unsupported, uncertain. observation_status: observed, no_event_observed_in_window, uncertain. Event types are open text. Frame fields are integer original recording indices when known; no required default. Dates and reviewer identities are human-entered text. Approval fields stay blank until explicitly completed by a human.

record_id is stable across reviewer copies. Distinguish copies using reviewer_copy. Added physical events must receive unique event_id values and retain run_id/object_id. The legacy mapping CSV preserves original run/object/frame keys without modifying legacy records. Legacy initial support records used run_id, object and frame=10. Map object_id→object, support_label→initial_support_label, evidence references→evidence_frame_refs; preserve reasons/uncertainty and identity. Event records map run_id/object_id and onset/departure/landing fields by meaning, never by row position. Requirement interpretation records retain requirement draft ID and link to physical event IDs. Do not coerce uncertainty into pass/fail or manufacture approvals.

The conversion utility exports CSV rows to a JSON envelope with source filename and complete fields; legacy record updates still require explicit human mapping review. Existing releases and human-review JSON records remain untouched.

See legacy_field_mapping.csv for explicit event/requirement field correspondences. These are import guidance, not a claim that new event rows correspond one-to-one to older event prompts. Resolve references by run/object plus reviewed interval and event ID. Preserve all originals.

## Selected R1 and additive schema change — 2026-10-24

[Scope decision](../REQUIREMENT_SCOPE_DECISION.md) and [machine-readable record](../requirement_scope.v3.json) are current. The standalone [scope schema v1](requirement_scope.v1.schema.json) follows the repository's explicit schema_version and Draft 2020-12 conventions. It does not alter the candidate-requirement schemas, original draft JSON, legacy human-review JSON, or historical approved fields. It separates requirement_scope_status from independent_human_review_status, event_label_status and detector_validation_status. Future scope/status updates require a new version/schema where necessary; this record is an immutable selection snapshot, not a live approval tracker.

### requirement_interpretation.csv

- requirement_version: the selected version provided by the template; version metadata is not a judgment.
- applicability: applies / does_not_apply / insufficient_information. does_not_apply requires evidence establishing absence of initial table support, not just missing evidence.
- interpretation: violation / no_violation_observed_within_reviewed_coverage / insufficient_information / not_applicable. The first requires sufficient evidence of an R1 event. The second is coverage-qualified, not a continuous safety claim. not_applicable accompanies verified non-applicability. Do not force binary pass/fail.
- physical_event_id: link to the independently saved physical record(s), including a clearly identified no-event record if relevant. Physical events outside R1 remain in events.csv.
- evidence_links and supporting_frame_references: evidence locations and original frame intervals; semicolons may separate references.
- review_start_frame / review_end_frame: actual reviewed interval (inclusive original saved indices), not an assumed full requirement interval.
- evidence_coverage: short_window / full_execution / partial_execution / insufficient_information. Full execution means the saved frame-10-to-terminal interval was reviewed, with gaps, visibility and sample limitations explained; it does not assert unobserved continuous behavior.
- reasoning, confidence_uncertainty, unresolved_scope_questions: explain conclusions and any remaining event, measurement, definition or coverage uncertainty.
- scope_agreement_reference: legacy field name; cite the shared decision ID/version, not invented team agreement.
- approval_decision: retained legacy human-only field; leave blank unless a human explicitly supplies a decision and explains its meaning. It is not scope selection, collective approval or detector validation.

All added review fields start blank. The two blank reviewer copies remain equivalent. The CSV-to-JSON envelope preserves all columns without deciding labels; no envelope version change is needed.

### Adjudication and migration

final_labels.csv adds immutable source-file hashes and verbatim original answer columns, plus reviewed coverage/frame references. Existing label, applicability, interpretation and reasoning fields remain separate. Keep both dated originals alongside adjudication; source references identify filenames and stable record/event IDs. Copy answers verbatim (a complete source row encoded as JSON is acceptable); do not replace originals with the final answer.

The pre-update blank templates are preserved byte-for-byte in [history](../history/20261023-v1/README.md). Do not overwrite any completed form held elsewhere. Archive its original bytes/version first; start a fresh current template for a new R1 judgment, retain old labels and evidence links, and explicitly cross-reference old record IDs. Never automatically relabel historical answers or copy an old approval into the new scope.
