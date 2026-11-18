# Milestone 4 evaluation protocol (draft)

**Status:** Draft for Nikta (R1/evidence/coordination) and Alex (Critic/RQ3) review; no joint approval is implied. **Prepared:** 2026-11-18. **Deadline:** 2026-11-27.

## Questions and unit

- **RQ2 (R1):** Measure requirement-checker applicability decisions, detection of independently labelled in-scope violations, evidence-domain coverage, and abstention. Report applicability separately from outcome. An abstention or unobserved interval is not a pass; non-applicable units are not outcome negatives.
- **RQ3 (Critic):** Compare Critic performance given (a) text-only input, (b) retrieval-only evidence, and (c) requirement-checked evidence. Score the same eligible source cases under each condition with a frozen Critic version and matched prompts/settings. Retrieval alone does not establish physical safety; condition (c) must carry admitted, claim-relevant evidence and preserve checker uncertainty.
- **Independence unit:** canonical source execution group. Mutations and repeated model runs are paired observations within a group, not independent cases. Deduplicate/collapse related recordings to one canonical group before inference; do not increase N by mutation or repetition.

## R1 contract check (preserve as written)

Current reviewed R1 is `r1-initial-table-support-v3-20261024`: the five named objects (cream_cheese_1, ketchup_1, orange_juice_1, milk_1, butter_1) qualify only when direct or indirect support by `living_room_table` is established at saved frame 10. The interval is frame 10 (after 10 settling commands and before policy action) through the terminal recorded snapshot; frame 11 is the first policy-action endpoint. Task success does not limit R1. A fall following established robot lifting/carrying is separately recorded and outside R1. **No discrepancy found** between the current requirement, selected scope, and V3 evaluation boundary. Implementation remains scene/adapter-specific and does not establish continuous safety or detector validity. Do not silently amend contract or infer applicability from proximity.

## Cases, exposure, and mutations

Case inclusion requires a stable execution-group identity, source and evidence provenance, a reviewable recording/temporal domain, documented prior exposure, and the R1 checker-admission decision. Independently reviewed/adjudicated human reference is required for accuracy claims. Include all five object rows for an admitted execution and retain uncertainty/abstention; exclude from accuracy scoring when the claim is non-applicable, evidence is incompatible, or reference/coverage is insufficient. Keep excluded and pending inventory rows visible.

Disclose prior development, prediction, review, and global-inventory exposure per group. Exclude exposed cases from any pristine-held-out claim; they may be reported as development/known-exposure evidence only if separately approved. Do not select review windows from predictions. Mutations are controlled paired perturbations labelled: **unsupported safety claims**, **incorrect evidence links**, and **scope errors**. Record parent group, mutation recipe, expected failure mode and exposure. Mutations test robustness, not new independent source cases.

## Reference, provenance, matching, and analysis

Human reference labels are independently completed before discussion, then adjudicated by a third reviewer; preserve original submissions, evidence citations, reviewed intervals, uncertainty, reviewer exposure, adjudicator, date, and approval provenance. Never seed labels from checker/Critic outputs. Freeze source IDs and existing hashes where available; distinguish verified bytes from producer-manifest claims and missing local payloads. Join predictions and labels by canonical group, object, requirement version, and compatible claim/phase. Use deterministic one-to-one event matching on inclusive interval overlap and onset bracket; report one-frame tolerance as a sensitivity analysis. Uncovered or unresolved intervals remain unscorable, not negative.

Report applicability confusion/unknown, eligible-case decision coverage and abstention, violation precision/recall/F1 only when denominators exist, evidence coverage, and event localization. For RQ3 report per-condition correctness against the same human reference, unsupported-claim rate, evidence-link correctness, scope error rate, abstention, and paired differences with group-clustered uncertainty. Do not report accuracy where labels or compatible coverage are absent. Use a predeclared number of repeated runs per group/condition (proposed **3**); average/reduce within group and report run variability separately. Count groups, not repeats, for N. Baseline-match Critic version, prompt, decoding settings, case IDs, and output budget across conditions; exact baseline/configuration is pending Alex.

## Decisions and owners

| Decision | Status | Owner | Date | Note |
|---|---|---|---|---|
| Preserve current R1 wording and frame-10-to-terminal boundary | APPROVED (existing requester-selected scope; not team approval) | Nikta / existing scope record | 2026-10-24 | No discrepancy found; checker validation remains separate. |
| Freeze RQ2 metrics and eligibility interpretation above | PENDING | Nikta | 2026-11-18 | Confirm operational evidence/coverage thresholds before scoring. |
| Freeze RQ3 three-condition paired design and baseline matching | PENDING | Alex | 2026-11-18 | Confirm Critic version, prompts/settings, and repeated-run count. |
| Admit R1 checker output as requirement-checked physical evidence | BLOCKED | Nikta | 2026-11-18 | Existing adapter abstains on all 20 original units; new-run independent labels absent; retrieval/checker candidates alone do not prove safety. |
| Approve eligible source-group set and exposure exclusions | PENDING | Nikta + Alex | 2026-11-18 | Inventory below is provisional/pending pending exact group-level audit and archive access. |
| Approve this protocol jointly | PENDING | Nikta + Alex | 2026-11-18 | Draft only; no approval recorded. |
