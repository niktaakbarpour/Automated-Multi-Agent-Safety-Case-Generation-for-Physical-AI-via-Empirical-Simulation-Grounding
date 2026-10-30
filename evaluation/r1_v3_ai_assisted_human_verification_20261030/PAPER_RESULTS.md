# Paper-ready methodology and results — proposed reference, unscored

## Method and case selection

We use **AI-assisted human verification with human adjudication**. The existing
prediction-blinded sampling protocol selected one object from each of 20 distinct
recordings: all ten reserved same-task runs and ten changed-task same-scene runs
selected by a deterministic SHA256 ranking. Each stratum assigns two cases to each
of five protected objects. The assignment manifest predates this verification and
is unchanged. Prior numerical/setup/global inventory exposure prevents calling
the recordings a pristine held-out set. The 20 cases are a subset of the frozen
60-run transfer audit, not the earlier four-recording development reference.

AI Evaluator 1 and a replacement fresh-context blinded AI Evaluator 2 produced
physical observations before requirement interpretations. The replacement's
reported inputs exclude Evaluator 1 outputs and checker predictions. This is
documented access provenance, not independently proven isolation or model diversity.
Both evaluations used saved-frame sheets and computational geometry/contact data;
neither completed timed normal-speed/quarter-speed video playback. AI1 sampled
visual frames; AI2 reports inspection of all 5,347 saved indices in both cameras.

On 2026-10-30, the user reported that Human Evaluator 1 accepted all AI1 decisions,
Human Evaluator 2 accepted all replacement AI2 decisions, and a third human selected
Human 2's NV12 outcome. The source AI annotations are copied byte-for-byte and human
acceptance metadata is separate. No human identities, actual review/adjudication
dates, signed declarations, inspection intervals or new human reasoning were supplied.
Accordingly, AI-written prose and AI coverage are not attributed to human authorship
or inspection. These are user-reported acceptances, pending formal confirmation.

## Descriptive comparison and proposed adjudication

| Measure | Accepted AI1-origin record | Accepted blinded AI2-origin record |
|---|---:|---:|
| Cases | 20 | 20 |
| Non-applicable | 12 | 12 |
| Coverage-qualified no violation observed | 7 | 8 |
| Insufficient information | 1 | 0 |
| Physical-observation rows | 64 | 91 |
| Open uncertainty requests | 23 | 5 |

Initial-support and applicability labels agree for all 20 cases; outcome labels
agree for 19. This is a descriptive comparison of AI-origin proposals accepted by
humans, **not independent human inter-annotator reliability**. User-reported proposal
acceptance is 20/20 for each human; this is not an independently audited acceptance rate.

For NV12, AI1 retains insufficient information over an uncertain grasp transition;
AI2 does not infer an unsupported downward table departure from the isolated contact
gap and proposes no violation observed within reviewed coverage. The third-human
selection is reported to favor Human 2's outcome. The rationale remains explicitly
AI2-authored. Detailed phase/timing and coverage differences are not automatically
resolved by that selection. All 28 source uncertainty requests remain preserved;
the two AI2 global requests apply across cases.

| Proposed outcome | Cases |
|---|---:|
| Not applicable | 12 |
| No violation observed within reviewed coverage | 8 |
| Insufficient information at outcome-label level | 0 |
| Confirmed R1 violation | 0 |

This distribution is a **proposed, unapproved reference**, not a frozen ground truth.
Both source explanations, physical rows and uncertainties remain attached to every
case. Outcome-level certainty does not resolve evidence/force/timing uncertainty.

## Approval and V3 performance

Formal approval and reference freezing have **not** occurred. The original
independent-human collection/scoring process cannot truthfully accept these records.
The new pathway prepares separate acceptance/proposal/approval artifacts and rejects
missing declarations. Human-confirmed comparison domains and dispositions for other
physical/coverage differences are also pending.

**No V3 performance was computed in this task.** Applicability accuracy, outcome
agreement, decision coverage, abstention, confusion matrix, same-task/changed-task
and per-object performance remain pending, not zero. Historical V3 development
scores and unlabelled transfer-audit coverage are separate evidence and must not be
substituted into this table. Scoring must use the original sealed predictions only
after legitimate approval and a reviewed AI-assisted scoring protocol/adapter.

Even after approval, zero reference-positive R1 violations makes positive-class
recall/F1 non-estimable; precision is undefined if there are no positive predictions.
Non-applicability and abstentions do not count as true negatives. Localization is
unscorable for unmapped or unresolved physical phases. A qualified no-violation
observation is not proof of physical safety.

## Validity threats

- Human acceptance is reported through the user rather than authenticated individual
  declarations; actual human inspection and playback coverage remain unknown.
- Humans accepted AI-origin judgments and explanations, introducing anchoring and
  automation bias. No independent human annotation reliability is estimable.
- AI reviewers share an AI system family; fresh context is not independent-model
  reliability. The earlier exposed Evaluator 2 is excluded from this record.
- Sampling is small, same-scene, balanced by design, and not a population estimate.
  Prior exposure and development-informed requirement/checker design remain relevant.
- Saved 20-Hz samples, reduced-resolution sheets, occlusions, nominal 0.002-second
  geometry lag and unverified camera timing limit physical interpretation. Contacts
  do not measure load-bearing force. NV05/NV12 landings are terminal-censored.
- Physical-event row granularity, lift/transport boundaries and negative-coverage
  assertions differ beyond NV12. Their exact source records remain unadjudicated.

## Suggested LaTeX text and table

```latex
\paragraph{AI-assisted human verification.}
We prepared 20 object--execution cases from 20 recordings, balanced across five
protected objects and two same-scene task conditions. The coordinator reported
that two human reviewers accepted their respective AI-origin annotation proposals.
A reported third-human selection favored the second proposal for the sole
case-level outcome disagreement (NV12). AI authorship, source-specific evidence
coverage, and unresolved physical uncertainties were retained. These records are
AI-assisted human verification with human adjudication, not independent human-first
annotations; no independent inter-annotator reliability is claimed.
At this stage, formal reference approval, confirmed comparison domains, and V3
reference scoring remain pending.

\begin{table}[t]
\centering
\begin{tabular}{lrrr}
\hline
Outcome & AI1 accepted & AI2 accepted & Proposed adjudicated \\
\hline
Not applicable & 12 & 12 & 12 \\
Qualified no violation observed & 7 & 8 & 8 \\
Insufficient information & 1 & 0 & 0 \\
\hline
\end{tabular}
\caption{Descriptive AI-origin outcomes with user-reported human acceptance.
The proposed adjudicated reference is not formally approved or scored.}
\end{table}
```

Do not remove the pending-approval wording or add checker performance numbers until
the approvals, comparison domains and reproducible scoring artifacts actually exist.
