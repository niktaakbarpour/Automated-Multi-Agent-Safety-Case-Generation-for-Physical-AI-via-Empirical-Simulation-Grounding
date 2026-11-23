# RQ4 feasibility: real-model Revision Agent (M4)

Written November 23, before any revision model output exists. It answers the questions in Nikta's RQ4 request: what can be run on real data, what is blocked and exactly why, and which decisions are needed before the experiment is frozen. Every statement below was checked against the code and files on main at commit `84ca5b5`.

## Short answer

- **The checked-evidence comparison (with vs. without validated R1 checker evidence) is not feasible.** No admissible empirical checker assessment exists. See section 1.
- **A small preliminary experiment of basic revision effectiveness is feasible**: Qwen-generated revisions on real Critic findings, against the existing template adapter as a baseline, with structural validation and a second Critic review. On the current contract it covers 3 cases from 2 source executions, all of one objection type (unsupported guarantee, M1). See sections 2 and 3.
- 8 to 12 cases is not reachable without extending either the revision contract (for M2) or the Critic reports (a new GPU Critic stage). Options are in section 4.

## 1. Checked-evidence comparison: blocked

- Empirical admission of R1 checker results is disabled project-wide. In `critic/assessments.py` a checker result not marked synthetic is refused with "empirical admission is disabled" (`CHK-ADMISSION`), only the status `synthetic_analytical_only` is admitted, and the only admission route the code can assign is `synthetic_test_fixture`. Both RQ3 parent requests carry `empirical_admission_enabled: false`, and neither has an admitted checker assessment (P2 has none at all).
- The Critic can admit only labelled synthetic analytical assessments (`route: synthetic_test_fixture`). Those are test fixtures and cannot stand in for checked physical evidence.
- `rq2/R1_EVIDENCE_NOTES.md` records zero independently verified controlled positives and states that the post-hoc agreement "does not admit the checker or establish independently verified physical evidence".
- RQ3 condition C carried checker-admission status only. It is not checked evidence either.

So there is no case where a revision could be given admitted, validated checker evidence. This stays blocked until R1 checker admission is enabled under an independent validation, which is outside M4.

## 2. Which real Critic findings can a Revision Agent act on?

The revision step (`drafter/revision`, PR #27) takes a full Critic report from `critic.review` plus an explicit decision on each model finding. It does not read raw model replies. Sources of real findings, checked one by one:

**Rule findings.** CLAIM-ABSOLUTE-SAFETY (C12) fires on P1-M1a (cream_cheese_1:G1, a goal) and P2-M1c (vial_b/U1, an unresolved claim). These are real deterministic Critic findings, and `critic.review` reproduces them on CPU. No other mutation or clean control has a rule finding.

**Model findings from the RQ3 Qwen run.** A saved reply can be turned into a production Critic report only when it was generated from exactly the prompt that production `critic.review` sends. That holds only for condition R, and only for cases with no rule finding and no admitted assessment. In production the model sees rule findings under `already_found`, while RQ3 was rule-blind. Checked by capturing the production prompt and comparing it byte for byte with the batch:

| Case | Production prompt equals the RQ3 R prompt | R replies that detect the labelled defect |
|---|---|---|
| P1-M1a | no (rule finding shown in production) | n/a |
| P2-M1c | no (rule finding shown in production) | n/a |
| P1-M1b | yes | 1 of 3 (repeat 3) |
| P2-M2b | yes | 3 of 3 |

No M3 case and no other M2 case has a detection in any condition (RQ3 tables), so there is no real finding on them to revise.

**Contract limits on what can be revised:**

- P2-M2b's labelled target is a Solution node (widget_a/E1). The revision contract never rewrites a Solution, and removes one only for rule-based citation defects with link repair switched on (`drafter/revision/edits.py`, `permitted_ops`). A model finding on a Solution has no permitted edit, so no adapter, model or template, can act on it. **M2 cannot be tested under the current contract.**
- Model findings need an explicit decision with `decided_by: human_review` and a named reviewer (revision request schema). A rule finding such as CLAIM-ABSOLUTE-SAFETY also needs one, because it is marked `human_review_required`.

Usable now, with the finding approved:

| Case | Source group | Finding | Target | Node type | Template baseline (CPU probe) |
|---|---|---|---|---|---|
| P1-M1a | P1 (real, development-exposed) | rule, C12 | cream_cheese_1:G1 | goal | revised; all validators pass; rules-only re-check clean |
| P1-M1b | P1 | model (RQ3 R repeat 3), C05 | ketchup_1:G1 | goal | revised; all validators pass; rules-only re-check clean |
| P2-M1c | P2 (synthetic) | rule, C12 | vial_b/U1 | unresolved_claim | revised; all validators pass; rules-only re-check clean |

That is 3 cases, 2 independent source executions, 1 objection type (M1), 2 rule findings and 1 model finding.

Two details checked in the probe:

- The P1-M1b report is rebuilt with `critic.review` from the saved reply of R repeat 3, the only R repeat that detected the defect. Its recorded input hash equals the hash the RQ3 runner stored for that request, so the report pairs the reply with the exact input Qwen answered. Picking the detecting repeat is a selection, and it should be reported as one.
- The template baseline writes the same goal wording for every node type. On P2-M1c it puts "This goal makes no claim ..." on an unresolved claim, and all validators still pass. Structural acceptance does not show that the new text fits, which is one reason for the independent review below.

## 3. Proposed preliminary experiment (if section 4 decisions keep the current scope)

- **Revision Agent:** a Qwen adapter implementing the existing adapter interface (`kind: model`, `propose(context)`), proposing edits in the existing edit format. The host checks every edit and every invariant exactly as for the other adapters. Nothing in the engine changes.
- **What the model receives:** the original argument bundle, the approved findings with their targets and permitted edit kinds (the engine's context), and the evidence records and retrieval context from the unchanged Critic request. The engine context has no evidence records today, so the adapter adds them read-only from the request it is built for. The engine stays untouched. No checker result is shown, since none is admitted.
- **Baseline:** the existing deterministic template adapter on the same approved findings. It needs no GPU.
- **Settings:** the RQ3 frozen Qwen3-32B settings (temperature 0.6, top_p 0.95, top_k 20, max_tokens 8192, JSON response format, thinking off), 3 samples per case. That gives 9 revision requests.
- **Validation:** the existing blocking validators (frozen inputs, diff rules, Critic input checks, no new rule findings, cited rule findings cleared, shared GSN validator, Drafter structure rules). A revision that fails any of them is counted as invalid and the original is kept.
- **Second Critic review:** the production Critic with the same settings on the original and revised arguments (a second, small GPU stage built from the stage 1 outputs). Rule findings are part of every Critic report.
- **Measures:** objections resolved, unresolved, new unsupported claims (new findings from either Critic review), evidence errors, invalid revisions and abstentions (the model declining). Reported per case, for Qwen and the template baseline, with mean ± SD over the 3 samples. Critic acceptance is never counted as success on its own.
- **Independent correctness:** each revised statement is judged by a reviewer who did not write the mutations or approve the findings, using a form with explicit criteria. Does the new text remove the unsupported claim? Does it add any claim the evidence does not support? Does it keep the object, scope and interval? Is it still a usable argument statement?

GPU work: stage 1 is 9 revision requests. Stage 2 is the second Critic on the original and revised arguments, at most 27 requests. Both are small and can run on November 24 one after the other. The agreed design is in RQ4_PROTOCOL.md, which supersedes this section where they differ.

## 4. Decisions needed before freezing

1. **Scope.** Accept the 3-case preliminary experiment above, or extend it:
   - (a) **Add M2** by extending the revision contract so an approved model finding on a Solution may lead to `remove_solution` plus an unresolved claim. This changes merged revision code whose mapping is still awaiting Ryiad's confirmation, so it needs his and Nikta's agreement.
   - (b) **More real Critic reports**: run production `critic.review` with Qwen on the 8 mutations first (a stage 0 GPU run). This gives model findings for P1-M1a and P2-M1c as well. It adds a third GPU stage, and RQ3 suggests it would not add M3 cases.
2. **Who approves findings.** Proposed rule, fixed before any revision output: approve exactly the findings that match the labelled defect, and leave every other finding undecided, so it is carried forward and never acted on. Alex would record the decisions as `human_review`, disclosed as the developer who wrote the labels, not an independent approver.
3. **Independent correctness reviewer** for the revised statements: someone other than Alex. Ryiad's label review is still open (`rq3/RYIAD_NEUTRAL_REVIEW/REVIEW_FORM.csv` is blank).
4. **Reporting.** With 3 cases from 2 source executions and one objection type, the result can only be described as preliminary and development-only. It cannot speak to checked evidence or to M2 and M3.
