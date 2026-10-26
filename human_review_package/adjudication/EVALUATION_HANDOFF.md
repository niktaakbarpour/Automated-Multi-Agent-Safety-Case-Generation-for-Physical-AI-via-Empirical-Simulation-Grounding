# Evaluate the automated R1 checker against the approved reference

Reference: `approved_reference/r1-reference-be76abc531f5c716efca/`. This is a four-run development reference, independently annotated by two humans and finalized through AI-assisted adjudication approved by a third researcher. No automated-checker accuracy has been measured here. Freeze the checker implementation/model/prompt/configuration and the evaluation protocol before generating predictions.

## Inputs and identity

Use `adjudicated_initial_support.csv` for frame-10 support, `adjudicated_requirement_interpretation.csv` for R1 applicability and interpretation, and `adjudicated_events.csv` for physical-event phases and reviewed windows. Use `final_label_json`, not a historical proposal status or an empty flat CSV cell. Preserve all 20 run/object requirement records. Resolve native simulator integers within each recording's own object mapping; join by run ID, canonical object ID and requirement version. Check recording hashes against the manifest. The four runs have different terminal frames.

Require each checker result to include run ID, canonical object ID, R1 version, applicability, outcome (`violation`, `no_violation_observed_within_reviewed_coverage`, `insufficient_information`), reviewed frame intervals, event IDs/types/onset-end bounds, abstention reason, and checker commit/configuration hash. Reject mismatched runs, unknown identities or incompatible requirement versions rather than silently aligning them.

## Label mapping and eligible comparisons

| Reference | Checker comparison |
|---|---|
| `applies` + `violation` | Positive R1 label within the established event interval and evaluated coverage |
| `applies` + `no_violation_observed_within_reviewed_coverage` | Coverage-qualified negative for the same reviewed observation domain, never proof of continuous safety |
| `does_not_apply` + `not_applicable` | Evaluate applicability separately; exclude from binary R1 outcome counts |
| `insufficient_information` or unresolved event classification | Exclude from determinate binary outcome counts; retain an explicit uncertainty/abstention record |

Ten uncertainty requests retain unresolved components; this does not automatically invalidate every linked R1 label. Determine eligibility per claim: for example, an uncertain later orange-juice fall does not make known absence of initial support an applicable R1 case. Do not turn that physical uncertainty into a negative fall label. Report sensitivity restricted to records without unresolved components as a separate, smaller analysis.

Use frame 10 through each terminal snapshot. A setup departure before frame 10 stays outside R1 even if landing occurs later. Retain physical setup/post-lift events without treating them as R1 violations. Episode 014 cream cheese has an approved existing-scope-F exclusion for the established held lift followed by release; a checker must not infer that any incidental robot contact warrants exclusion. No carrying-duration threshold was approved. Initial indirect support requires a stable support chain, not proximity.

For this exact reference, inspect `adjudication_summary.json` before computing denominators: there are no adjudicated positive R1 violations. It cannot estimate sensitivity to R1 violations. Positive physical events outside R1 do not supply positive R1 examples. Obtain new independently reviewed in-scope positive examples without changing R1 to manufacture them.

## Outcome confusion counts and abstention

Primary outcome unit: one eligible run/object R1 interpretation with compatible observation coverage. Predeclare an observation-domain compatibility check; different sampled/video coverage must not be called equivalent continuous coverage. A checker with insufficient coverage or an explicit unknown result is an abstention, not a true negative.

- TP: reference positive and checker positive on a compatible evaluated domain. Event localization is scored separately below.
- FP: reference coverage-qualified negative and checker claims an R1 violation on that same evaluable domain.
- FN: reference positive and checker returns a determinate negative on the compatible domain.
- TN: reference coverage-qualified negative and checker returns the corresponding determinate negative. This is agreement on recorded coverage only.

Primary precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 = 2TP/(2TP+FP+FN), conditional on determinate checker outputs and eligible reference labels. Any zero denominator is `undefined`, with the relevant counts reported. When no reference positives exist, report recall and positive-class F1 as not estimable, even if a formula with false positives alone yields zero. Do not report undefined recall as 100% or infer detector accuracy from adjudicated consensus.

Report total 20 units, reference eligibility coverage (determinate applicable/20), checker decision coverage (determinate compatible predictions/eligible units), abstention rate (abstentions/eligible units), uncovered/mismatched domains, and reasons. Report positive-class recall counting abstentions as missed positives as a separate end-to-end operational measure when positives exist; do not hide abstention by reporting only conditional metrics. Report applicability confusion counts across all determinate support cases separately. Inapplicable cases do not inflate TN counts; R1 alarms on them are scope errors tracked in applicability/scope-error statistics. Report event-level scoring separately from run/object outcomes. Four correlated, selected runs do not support broad population claims; do not treat their frames as independent samples for confidence intervals.

## Event matching

For reviewer reliability, retain the original immutable statistics and their existing matching rules. Checker localization is a separate analysis, not a recomputation of inter-reviewer agreement. Its protocol must be fixed before reading checker outputs:

1. Partition by run ID, canonical object ID, requirement version, event type/compatible phase, and in-scope versus setup/post-lift status. Do not match a generic drop to an R1 fall without checking applicability and exclusion.
2. Read uncertainty brackets, explicit reviewed fragments and compound `subevents` from `final_label_json`. Distinguish first recorded contact from exact landing; do not collapse the cream-cheese negative fragments `[10,269]` and `[286,530]` across the lift/drop.
3. Primary localization match: inclusive saved-frame intervals overlap, with onset compatible with the annotated onset bracket. Exact boundaries are not asserted where unknown. Use a prespecified one-saved-frame tolerance sensitivity analysis (nominal 0.05 s), not a new physical persistence or carrying threshold; report both strict and tolerance results. Do not convert video time to exact simulator subframe time without validated synchronization.
4. Use deterministic one-to-one maximum-cardinality matching; among equal-cardinality assignments prefer total interval IoU, then minimum onset distance, then stable event IDs. Score phases separately where a compound group contains distinct grasp/lift/release/contact observations; retain the group linkage. Specify the compatible event-type vocabulary in the evaluation configuration before scoring.
5. Matched positive R1 events are event TP; unmatched established reference R1 events are event FN; unmatched predicted R1 events are event FP only where the claim is adjudicable within reviewed coverage. Unknown/out-of-coverage event claims are unscorable and reported separately, not negatives. Duplicate predictions left after matching count as duplicate FP where otherwise adjudicable. Report onset/offset error only against established sample bounds; censored or unknown endpoints do not become exact times. Never count all unannotated frames as event TN.

## Leakage controls and next execution

These four executions were selected for development and inspected during construction of the reference. They cannot serve as a pristine held-out generalization test. Keep reference labels, reviewer text, adjudication reasoning and contact sheets out of checker inputs and agent context until predictions are saved. If the checker or its prompts/thresholds were informed by these cases, label results as development evaluation. Freeze and hash predictions before scoring; archive their configuration, failures and abstentions. Do not tune thresholds on this reference and then call the same result held-out accuracy.

Next: implement an adapter producing the schema above; validate identities and coverage against the reference; run the frozen checker on the original recordings without supplying labels; save prediction hashes; score outcomes, applicability and localized events separately. Build an independent run/task/seed-disjoint evaluation set with positive R1 cases and human labels for confirmatory evaluation. Preserve train/development/test separation at run and related-task level, and document any prior model exposure. No checker execution or accuracy claim is part of this dataset-freezing change.
