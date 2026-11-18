# Milestone 4 evaluation protocol

**Version:** M4-v1.0 | **Status:** APPROVED by Nikta and Alex, 2026-11-18 | **Deadline:** 2026-11-27

Protocol approval freezes the study design and metric definitions. It does not approve source cases, human labels, checker validity, or experimental results.

## Research questions and frozen design

- **RQ2 — R1 checker:** Evaluate applicability, evidence coverage, decision coverage, abstention, and violation detection where independent reference labels and suitable positive and negative cases exist. Prioritize controlled R1 positive violations and matched controls. Report applicability separately from outcome; non-applicable and unknown cases are not negatives, and abstention is not a pass. Do not report detection accuracy without independent reference labels and a suitable case set.
- **RQ3 — Critic:** Run paired comparisons on the same eligible canonical source execution groups under **(A) text-only**, **(B) retrieval-only**, and **(C) requirement-checked evidence**. Use the existing working Critic implementation. Freeze model, prompt, decoding settings, and output limit when verified; unknown exact configuration remains pending. Compare unsupported-claim rate, evidence-link correctness, unjustified scope narrowing, abstention, and reference-based correctness where labels support it. Retrieval alone does not establish physical safety.
- **RQ3 mutations:** (1) unsupported absolute safety claims; (2) incorrect evidence links; and (3) unjustified scope narrowing. Record mutation recipe, parent group, intended failure mode, and exposure. Keep mutations paired within their parent group.

## Independent unit and repetition

The independent unit is the **canonical source execution group**. Related recordings must be grouped before scoring. Mutations and repeated inference runs are paired observations and never add independent cases. Plan three inference repetitions per group and condition if feasible; record actual repetitions and model settings. Do not invent sample sizes or treat repeats as independent observations.

## R1 contract (verified; wording and boundary preserved)

Current reviewed R1 is `r1-initial-table-support-v3-20261024`: the five named objects (cream_cheese_1, ketchup_1, orange_juice_1, milk_1, butter_1) qualify only when direct or indirect support by `living_room_table` is established at saved frame 10. The interval is frame 10 (after 10 settling commands and before policy action) through the terminal recorded snapshot; frame 11 is the first policy-action endpoint. Task success does not limit R1. A fall following established robot lifting/carrying is separately recorded and outside R1. No discrepancy was found between the current requirement, selected scope, and implemented evaluation boundary. This contract check does not establish detector validity or continuous safety.

## Eligibility, exposure, references, and analysis

Require stable group identity, source/evidence provenance, reviewable temporal domain, documented prior exposure, and a recorded checker-admission decision. Preserve all object rows, uncertainty, and abstentions. Existing development-exposed cases are development evidence, not pristine held-out evaluation. Disclose development, prediction, review, and global-inventory exposure; do not select review windows from predictions.

Physical-safety accuracy claims require independent human reference labels. Preserve original reviewer submissions, provenance, evidence citations, reviewed intervals, uncertainty, exposure, adjudicator identity and date. Where feasible, use two reviewers working independently before discussion, followed by adjudication only if a third adjudicator actually participates. Do not imply third-party adjudication if it did not occur. Never seed labels from checker or Critic output.

Freeze source IDs and existing hashes where available; distinguish verified bytes from producer-manifest claims and unavailable payloads. Join outputs and references by canonical group, object, requirement version, and compatible claim/phase. Uncovered or unresolved intervals remain unscorable, not negative. Report counts and denominators; omit accuracy metrics when labels or compatible coverage are absent. Event-localization sensitivity studies are deferred.

## Scope for the deadline

Prioritize controlled R1 positive violations with matched controls for RQ2 and a small paired RQ3 study covering the three mutation types. Defer large-scale annotation, additional benchmarks or requirements, complex temporal-localization sensitivity studies, and full Revision-Agent evaluation unless core work is complete. Do not run or claim experiments as part of this protocol approval.

## Decision register

| Decision | Status | Owner | Date | Boundary |
|---|---|---|---|---|
| Preserve current R1 contract and exact frame-10-to-terminal boundary | APPROVED | Nikta + Alex | 2026-11-18 | Contract approval does not validate the checker. |
| Freeze RQ2 metric definitions and priority | APPROVED | Nikta + Alex | 2026-11-18 | Applicability, evidence/decision coverage, abstention, violation detection when reference and cases permit. |
| Freeze paired RQ3 A/B/C design and three mutation types | APPROVED | Nikta + Alex | 2026-11-18 | Same eligible groups; paired observations. |
| Exact Critic commit/model/prompt/decoding/output-limit configuration | PENDING | Alex | 2026-11-18 | Record exact values when verified; use existing working Critic. |
| Source eligibility and independent human reference labels | PENDING | Nikta + Alex | 2026-11-18 | Existing development cases are not pristine held-out data. |
| Physical R1 checker admission | BLOCKED | Nikta | 2026-11-18 | Requires independent validation against suitable human reference evidence. |
| Condition C for physical-safety claims | BLOCKED | Nikta + Alex | 2026-11-18 | Requires admitted requirement-checked evidence; retrieval alone is insufficient. |
| Actual experimental results | NOT RUN | Nikta + Alex | 2026-11-18 | No result is implied by approval of this protocol. |
