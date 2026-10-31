# Complete comparison of accepted AI-origin evaluations

Method: AI-assisted human verification with human adjudication, as reported by the
user on 2026-10-30. Acceptance and adjudication dates themselves were not supplied.

| Comparison | Result |
|---|---:|
| Assigned object identity | 20/20 matching |
| Initial support labels | 20/20 matching |
| Requirement applicability | 20/20 matching |
| R1 outcome labels before adjudication | 19/20 matching |
| AI Evaluator 1 physical rows | 64 |
| Blinded AI Evaluator 2 physical rows | 91 |
| Uncertainty requests, Evaluator 1 / 2 | 23 / 5 |
| Proposed labels after reported NV12 selection | 12 non-applicable; 8 qualified no-violation |

These are descriptive agreements between accepted **AI-origin** records. They are
not independent human inter-annotator reliability, a model-diversity experiment,
or checker accuracy. Human acceptance of source proposals is user-reported 20/20
for each human; actual inspected evidence/coverage remains unconfirmed.

## Field-level audit

`field_comparison.json` contains 1,700 comparisons: 447 exact agreements and 1,253
differences. This includes 20 complete nested COVERAGE objects; each CSV field is
compared over its complete ordered values/IDs for a case. Global uncertainty rows
are attached to every affected case, so counts of differing fields are not counts
of independent scientific disagreements. Split/merged rows cause structural
differences even where some phase descriptions may be compatible.

There are 338 identifier/provenance differences retained separately, 280 descriptive
detail/uncertainty differences retained without claiming semantic equivalence,
212 coverage/evidence differences requiring confirmation, 422 potential substantive
or structural field differences left unresolved, and one outcome disagreement
resolved at the reported-selection level. Exact values, including every temporal
bound, object ID, evidence reference and additional annotation field, remain in JSON.
No event IDs are paired by ordinal position or assumed equal across evaluators.

## NV12: outcome resolved by reported third-human selection

Human 1 accepted AI1's `applies / insufficient_information`. Human 2 accepted blinded
AI2's `applies / no_violation_observed_within_reviewed_coverage`. The user reports
that the third human selected Human 2's outcome. That outcome is selected in the
proposed consolidated reference. The exact AI2 requirement row, rationale and all
physical rows are in `human_evaluator_3_adjudication/NV12.json`.

AI1's corrected no-event window ends at 199; its uncertain support transition spans
199–203. AI2 explicitly describes grasp adjustment at 198–202, retains uncertainty
about instantaneous support at 200, and does not infer downward fall from isolated
contact absence. Both identify later lift/carry and post-lift release, with unknown
terminal landing. Outcome selection does not erase those limitations or certify
continuous support. The rationale is AI2-authored; no distinct human rationale,
identity, signature, review date or inspection coverage was supplied.

## Other differences that remain unadjudicated

| Cases | Difference | Disposition |
|---|---|---|
| All 20 | AI1 sampled sheets and `partial_execution`; AI2 all saved indices and `full_execution` for saved-index sheets. Neither performed timed playback. Evidence paths, prose and confidence qualifications differ. | Coverage confirmation required; preserve both. |
| NV01/02/04/07/08/09/10/14/15/18/19/20 | AI2 adds explicit post-setup negative windows; AI1 records setup phases without the same extra negative rows. | Additional coverage assertions are not automatically common accepted physical truth. |
| NV03/05/12/13 | AI1 combines setup separation/return; AI2 splits upward separation, descent and landing. | Candidate descriptive granularity difference; retain components and request phase mapping confirmation. |
| NV05/06/12/16 | Lift interval ends differ: AI1 191/81/211/78; AI2 193/83/213/80. AI2 starts transport at 183/73/203/70; AI1 at 191/81/211/78. Lift onset brackets also differ. | Unresolved boundary/phase convention or substantive timing difference; no automatic adjudication. |
| NV05/06/12/16 | AI1 combines release/descent; AI2 separates gripper release and unsupported drop, with narrower/different onset brackets. | Unresolved mapping/timing; retain both, no event-localization score. |
| NV06/16 | AI1 combines basket contact/settling; AI2 splits basket landing and later no-departure window. First recorded contacts agree at 148/146. | Contact agreement does not settle all phase bounds or coverage. |
| NV20 | AI1 supported displacement window 180–205, onset 180–184; AI2 180–204, onset 179–185, with flanking negatives. | Unresolved temporal/coverage difference. |
| All cases; especially NV05/NV12 | 23 case-specific AI1 requests versus 5 AI2 requests including two global requests; terminal-censored landing and force/timing limits persist. | Retain all requests open; acceptance alone is not evidence of resolution. |

`event_alignment_candidates.json` retains full grouped source rows to assist a human
reviewer. Grouping is an analyst navigation aid, never an approved semantic alignment.
No further substantive disagreement has been automatically resolved. Matching
outcome labels do not imply matching event annotations or comparison domains.
