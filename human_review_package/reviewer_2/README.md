# reviewer_2
Work in your own local copy. Read [instructions](../REVIEW_INSTRUCTIONS.md) and the [object guide](../OBJECT_GUIDE.md). Both reviewer folders refer to the same shared evidence. Read the [shared R1 scope decision](../REQUIREMENT_SCOPE_DECISION.md); it records requester-selected scope, not team approval or checker validation.

Open the CSVs in Excel, Numbers, or LibreOffice; preserve the UTF-8 CSV format when saving. Text IDs must remain text. Semicolons separate multiple evidence references. Leave unknown timing blank and explain uncertainty. Dates may use YYYY-MM-DD.

- [Initial support](initial_support.csv): twenty factual rows; enter direct_table, indirect, unsupported, or uncertain.
- [Physical events](events.csv): twenty object/run prompts, with no expected event. Enter observed, no_event_observed_in_window, or uncertain in observation_status. Add a row for each separate event; use a unique event_id such as RUN:OBJECT:E01. Add unanticipated event types freely. If you narrow the review interval, edit its bounds and state why.
- [Uncertainty requests](uncertainty_requests.csv): add rows as needed; resolution fields begin blank.
- [Requirement interpretation](requirement_interpretation.csv): complete independently after saving initial-support and physical-event records, applying the selected R1 without seeing detector predictions or the other reviewer’s answers. Record the actual reviewed interval and coverage, evidence, explanation and remaining uncertainty. Reference the actual event_id or a clearly identified no-event record.

Fill identity, date, reasons, uncertainty and prior-exposure disclosure yourself (including 'none' if appropriate). There are no human approvals in this template. Save a dated immutable independent copy before discussion. Return completed forms privately to the coordinator; do not commit or share answers where the other reviewer can see them before both reviews are complete.

Review order: first initial support and physical events independently; then R1 interpretation independently; finally the third reviewer adjudicates after both original reviews have been saved. Keep every object/run and all physical events, including events outside R1. No binary pass/fail answer is required. See the [form vocabulary and migration notes](../schemas/README.md).
