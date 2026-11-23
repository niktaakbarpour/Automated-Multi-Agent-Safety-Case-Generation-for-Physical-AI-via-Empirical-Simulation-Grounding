# Remaining M4 work by owner

Internal planning aid for the 27 November submission. It follows `evaluation/m4_20261127/shared/M4_THREE_PERSON_WORK_SPLIT_20261120.md`. It does not reassign author-owned prose or infer that an ongoing review is complete.

## Ranked top ten blockers

| Rank | Blocker / next action | Owner(s) | Requires new data or finalized review? | Can be resolved without new experimental data? |
|---:|---|---|---|---|
| 1 | Finish the independent 44-case RQ2 event review, verify reviewer exposure and evidence intervals, resolve discrepancies under the approved process, and freeze only an authorized final reference. Until then all 44-case accuracy fields remain pending. | Nikta to coordinate; eligible independent reviewer(s) to complete decisions; authorized adjudication only if required | **Yes.** Completed independent decisions and explicit freeze are prerequisites. | **No.** The missing decisions cannot be inferred from predictions, conditions or AI review. |
| 2 | Complete the independent RQ3 mutation-label audit for the 12 semantic cases, including target/category/object/evidence checks and exposure declaration. Freeze reviewer decisions before comparing with developer labels. | Ryiad as independent auditor if exposure-qualified; Alex as benchmark owner; Nikta to preserve the freeze | **Yes.** Independent labels and exposure gate are pending. | **No.** Do not substitute developer labels or model outputs. |
| 3 | Complete Ryiad’s 60 RQ1 question/reference slots, independently verify their source/task/variant/facets/time/citation requirements, then record an authorized reference freeze before any expanded scoring. Current committed count is 0 authored references. | Ryiad authors; independent verifier and Nikta freeze/authorize; technical pipeline is already prepared on an unmerged branch | **Yes.** Questions and reference answers do not exist in the committed package. | **No.** The blank forms and source extracts are not scientific references. |
| 4 | Write the author-assigned manuscript sections in the existing NeurIPS skeleton: abstract, introduction/RQs, methods/setup, RQ1/RQ2 results, discussion/conclusion, Critic/RQ3, related work and threats. The current main source is placeholders only. | Nikta: abstract/introduction/R1 algorithm and RQ1/RQ2 results/integration; Alex: Critic/mutation/RQ3; Ryiad: related work, evidence/GSN methods, RQ1 failure analysis and threats | No new experiment required for accurately qualified existing results; authors’ interpretation is required. | **Yes**, through the assigned authors’ writing and review. |
| 5 | Revise the technical tables/checklist against this registry: add historical C4 exact/semantic/lexical denominators, Phase 5K false-complete qualification, RQ2 300 units and 0/100 changed-task object-unit partition, human/AI pending fields, and RQ3 repeat/channel labels. | Nikta coordinates table integration; Alex validates RQ3; Ryiad validates RQ1/E4 | No new experiment for currently verified counts; human fields stay pending. | **Yes**, from frozen artifacts, without changing them. |
| 6 | Resolve whether the separate RQ2 AI-review work has a permitted, finalized result that can be reported. Keep any AI assessment distinct from human annotations; if it remains ongoing, report only “pending” and do not access private output until authorized. | Nikta to coordinate process; designated reviewer/AI-study owner to finalize protocol and public status | **Potentially.** Any proposed result requires an authorized finalized artifact and review of provenance. | **Yes**, only to document that it is pending and exclude its results. |
| 7 | Review Ryiad’s source-linked E4 diagnosis before using root-cause explanations for the changed-task transfer result. The frozen 0/100 is a coverage result on 100 applicable object units; 38 mapping-gate rejections remain outside that denominator. | Ryiad scientific review; Nikta final admission decision | No new experiment, but independent scientific review is pending. | **Yes**, by reviewing the existing frozen diagnostic; do not invent causes. |
| 8 | Make the RQ4 admission decision explicit in the paper: include only structural CPU/software evidence and the bounded one-pass integration, state NO-GO for real-model revision effectiveness, and do not imply Qwen revision or a second real Critic pass. | Alex owns RQ4; Nikta integrates | No new data to make the accurate NO-GO statement. Real-model effectiveness would require new eligible empirical inputs and separate authorization. | **Yes** for honest limitations; **no** for an effectiveness result. |
| 9 | Verify the bibliography and related work from sources the authors actually read; add venue-required citations and repository/reproducibility information. No repository mention is itself a citation. | Ryiad leads related work; all authors verify their own citations; Nikta integrates | No new experimental data; literature research and author verification are needed. | **Yes**, but not by fabricating citations. |
| 10 | Obtain `neurips_2026.sty` and a TeX toolchain in an approved environment; compile the author-complete source, inspect the PDF, verify the nine-page main-content limit, figure/table placement and appendix references; complete three contribution statements and AI-use disclosure. | Nikta coordinates final build; each author supplies/approves their own contribution and AI-use inputs | No experimental data; an official style file/compiler and author approvals are required. | **Yes**, with environment/setup and author inputs. Current compilation was not verified. |

## Owner handoffs

### Nikta — RQ2 coordination and manuscript integration

- Preserve RQ2 private submissions and keep the 44-case event review, N3 calibration, historical development reference and 60-run coverage audit separate.
- Coordinate independent review and authorized final-reference freeze; only then consider the RQ2 final scorer. The 3-case N3 calibration remains one group and cannot stand in for the 44-case review.
- Keep AI-review results out of human agreement/accuracy claims unless an authorized, finalized study is separately admitted.
- Write and integrate the sections allocated to Nikta in the work split; verify every manuscript number against the registry and keep all pending fields visibly pending.
- Complete final repository integration, compilation/PDF inspection, page limit, checklist, author disclosures and submission coordination.

### Alex — Critic/RQ3 and RQ4 software evidence

- Personally write Critic/mutation/RQ3 methods and results from the 108 saved Qwen responses, with two development parent groups, zero independent groups, three paired repeats and C admission-status-only explicit.
- Coordinate the independent mutation-label audit; preserve developer labels and scored outputs unchanged pending the independent review.
- For RQ4, use the current NO-GO feasibility finding as the empirical boundary. Any future Qwen revision/second-Critic experiment requires eligible source-linked actionable findings, a frozen protocol and separate authorization; no such inputs are currently available.

### Ryiad — independent review, retrieval questions and supporting analysis

- Independently author the new RQ1 questions/references; do not transfer expected answers from historical 18 C4 cases or Phase 5K V2. Enable expanded scoring only after independent verification and authorized freeze.
- Complete the RQ3 mutation-label review only if reviewer exposure declarations confirm eligibility; record disagreements and provenance without seeing model results before decisions are frozen.
- Review E4 task-transfer and E5 retrieval analyses scientifically. E5 is merged in PR #47; E4 remains an uncommitted diagnostic pending review.
- Personally write the allocated Related Work, evidence/GSN methods, failure analysis and threats sections with verified citations.

### Independent reviewers / adjudication authority

- Finalize their own RQ2 event assessments and RQ3 mutation-label assessments using the approved intake paths, disclose exposure, preserve original submissions and freeze decisions before model/checker comparison.
- Do not use a third AI evaluation as a third human annotation or infer labels from perturbation names, checker outputs, or model detections.

## Freeze and sequencing

No new GPU inference, simulation, retrieval benchmark or label generation is needed to write accurate descriptive sections from currently admitted evidence. New scientific claims still require the explicit pending reviews/reference freezes above; a deadline does not change those gates. Keep any later extension separately versioned and do not alter the original November 24 frozen outputs.
