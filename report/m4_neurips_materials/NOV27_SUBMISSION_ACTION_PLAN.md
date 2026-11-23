# M4 November 27 submission action plan

**Planning snapshot:** audit commit `1926b0b79ebf4cd1e7e1da6bcba6670977909ac3`, based on verified main `2bbfbc19dc3678b8334ef510115eaac26a0eb6a3` (PR #47). This is a coordination checklist, not manuscript prose, authorization to inspect private review material, or approval to promote pending results. Dates use the 2026 submission week.

## Submission-critical work, by blocker type

### Classification of unresolved work

“Submission-critical” means required for any claim the authors choose to include; a pending evaluation can be excluded to narrow the manuscript. It does not mean that every planned experiment must finish before submission.

| Classification | Unresolved tasks |
|---|---|
| **Submission-critical** | Author-written required sections and explicit RQs; verified citations; accurate table/caption updates for any retained result; author approval of claims, limitations, contributions and disclosures; a compiled final PDF and verified venue page limit. Any pending result that is retained requires its own reference/provenance admission gate. |
| **Important but not blocking if omitted/qualified** | E4 scientific review and any root-cause interpretation; RQ2 AI-review status/result; final independent RQ2 and RQ3 reviews if the corresponding metrics are omitted or explicitly remain pending; inclusion of RQ4 structural evidence; inclusion of RQ1/RQ3 tables that can be omitted without weakening the scoped contribution. |
| **Optional or post-submission** | The 30-execution RQ1 expansion scoring (requires Ryiad’s completed and independently verified references plus authorized freeze); RQ4 real-model revision-effectiveness experiment (currently NO-GO and would require new eligible inputs and separate authorization); any additional Qwen calls, retrieval runs, simulations or other new empirical extensions. These are not a reason to delay a submission that omits their claims. |

The empirical review tasks in A1–A3 are therefore **critical admission gates only if their results are included**. If they are not complete by the deadline, use the stated omit/pending fallback and do not imply completion.

### A. Missing empirical evidence or completed independent review

| Priority | Task and owner | Prerequisites | Required deliverable | Can complete without new experimental data? | Fallback if incomplete Nov 27 |
|---|---|---|---|---|---|
| A1 | **RQ1 expansion references — Ryiad (author); independent verifier; Nikta (authorized freeze)** | Ryiad finishes all 60 question/reference slots; verifier confirms source, task/variant, evidence IDs, facets, temporal bounds, citations and abstention rules; exposure is declared; an authorized frozen reference version is recorded. | Versioned, independently checked 60-slot question/reference dataset plus freeze record and provenance. Only after that gate may the separate RQ1 runner be used under its protocol. | **No.** The questions and references do not yet exist. Do not use the blank slots or source extracts as answers. | Omit expanded-cohort scores. State that the 30-execution expansion is pending, or omit it from results. Do not imply it verifies the historical metrics. |
| A2 | **RQ2 44-case independent event review — Nikta coordinates; designated independent reviewers submit; authorized reference owner freezes** | Reviewers finish their own records, exposure declarations and interval coverage; discrepancies are handled under the approved process; an authorized final-reference freeze is explicitly recorded. | Final reference freeze with case-level applicability/event determinations, provenance and uncertainty states; only then a reproducible scorer run and public summary. Keep N/A, exclusions, uncertain cases and checker abstentions distinct. | **No.** Missing human decisions cannot be inferred from saved predictions, calibration conditions or AI review. | Keep all 44-case performance fields PENDING. Report only existing development calibration and coverage-only results, with their limitations. Do not inspect unfinished submissions to accelerate the deadline. |
| A3 | **RQ3 independent mutation-label audit — Ryiad if exposure-qualified; Alex owns benchmark; authorized reviewer/freeze owner** | Reviewer eligibility/exposure declaration; explicit assessment of all 12 neutral cases, targets and evidence; decisions frozen before comparison to developer labels or Qwen outputs; disagreements recorded with provenance. | Independent audit record and freeze; after authorization, a comparison report separating agreements, disagreements and adjudication. | **No** for independent validation. Existing development results can be described with labels clearly identified as developer-authored and review pending. | Keep 108 responses as development-only/exploratory and state independent label review is pending. Do not call the labels human-validated. |
| A4 | **RQ2 AI-review status — Nikta / designated AI-study owner** | Confirm protocol, authorization and whether a finalized, shareable result exists. Do not inspect private outputs without separate authorization. | Either an authorized public finalized artifact with provenance and its own non-human interpretation, or an explicit “ongoing/not admitted” status. | **Yes** to document pending/excluded status; **no** to report an unverified result. | Exclude AI-review results. Never treat the AI as a third human annotator or use AI agreement as human inter-rater reliability. |

### B. Missing independent scientific verification / admission

| Priority | Task and owner | Prerequisites | Required deliverable | Can complete without new experimental data? | Fallback if incomplete Nov 27 |
|---|---|---|---|---|---|
| B1 | **E4 transfer-diagnostic scientific review — Ryiad; Nikta decides result admission** | Read the existing frozen-data diagnostic and case-linked evidence on its assigned branch; distinguish observed rejection codes from hypothesized causes. | Written scientific review and a scoped admission decision; corrections stay on the diagnostic branch and preserve frozen predictions. | **Yes.** This is review of existing data, not a new experiment. | Report only the frozen coverage fact (0/100 determinate applicable object units in the 50-execution changed-task same-scene stratum) and 38 mapping-gate exclusions separately. Omit unreviewed root-cause claims. |
| B2 | **RQ1 historical/Phase 5K table review — Ryiad (RQ1); Nikta integration; all authors approve** | Confirm each table cell against the frozen results and E5 case analysis; explicitly separate the historical 18-question C4 cohort from Phase 5K V2 and its three C2 temporal false-completes. | Author-approved table/caption changes and exact evidence references. | **Yes.** Existing frozen outputs and the saved consistency check suffice. | Keep only qualified, fully traceable frozen metrics; omit any cell whose cohort or denominator cannot be made explicit. |
| B3 | **RQ3 model-condition/table review — Alex; Nikta integrates** | Reconcile T/R/C values to the saved scorer; state 12 cases, 2 development parent groups, 0 independent groups, 3 paired repeats, exact denominators and C's admission-status-only input. | Verified table with model-only/rules+model distinction, clean-control false positives, source-group and pending-label qualifications. | **Yes.** Use the saved 108-response run and scorer only; do not make new calls or change labels/scoring. | Report as bounded development-only evidence with label audit pending, or omit the quantitative comparison if author review cannot confirm the table. |
| B4 | **RQ4 NO-GO review — Alex; Nikta integrates** | Confirm the unmerged feasibility report and main-branch structural evidence; preserve distinction between scripted tests, one-pass fixture and real-model revision. | Approved statement that real-model revision effectiveness is not evaluated; no claim of a Qwen-generated edit or second real Critic pass. | **Yes** for the NO-GO boundary. | Include software/contract evidence only if relevant; otherwise omit RQ4 effectiveness claims entirely. |

### C. Manuscript and reproducibility work

| Priority | Task and owner | Prerequisites | Required deliverable | Can complete without new experimental data? |
|---|---|---|---|---|
| C1 | **Author-owned sections and explicit RQs — each author per `M4_THREE_PERSON_WORK_SPLIT_20261120.md`; Nikta coordinates integration** | Approved scope from this plan; authors verify their own sources and claims. | Complete the existing manuscript skeleton, including abstract, RQs, method/setup, results, discussion, threats and conclusion. Author prose only; this plan does not draft it. | **Yes**, using currently admitted results and pending labels where needed. |
| C2 | **Tables, captions and evidence links — Nikta integration; Alex checks RQ3; Ryiad checks RQ1** | Registry and admission checklist; no pending result treated as final. | Update `tables.tex` and `CLAIM_EVIDENCE_CHECKLIST.md`; include denominators, group counts, uncertainty, exclusions, pending fields and limitations. | **Yes.** |
| C3 | **Citations/related work — Ryiad leads; every author verifies citations they use** | Authors consult the cited primary sources and retain precise bibliography records. | Verified references and in-text citations; no invented or unverified citations. | **Yes**, but requires literature verification. |
| C4 | **Figure and final layout — Nikta coordinates; authors review** | Final author-written manuscript and official NeurIPS 2026 style/toolchain. | Actual architecture figure, referenced caption, compiled PDF, nine-page main-content check, appendix/table/reference checks and reproducibility material. | **Yes** with a suitable toolchain; this was not available in the audit environment, so compilation/page count are currently unverified. |
| C5 | **Author forms and submission sign-off — each author; Nikta coordinates** | Final scope, author identities and institution-approved disclosure information. | Contributions, AI-use disclosure, venue checklist and all-author approval of claims/limitations. | **Yes**, but requires author input. |

## Prioritized November 23–27 checklist

### November 23 — Freeze the scope and assign work

- [ ] **Nikta:** circulate the evidence registry and this plan to Alex and Ryiad; confirm a single integration owner and author section deadlines. Do not circulate private reviewer material.
- [ ] **Alex and Ryiad:** acknowledge their table and scientific-review responsibilities; identify conflicts with active branches before editing.
- [ ] **All authors:** agree the fallback scope now: no pending metric enters the paper without its gate; no deadline-based promotion.
- [ ] **Nikta:** confirm the latest manuscript branch is based on current main and preserve the technical skeleton, separate draft worktree and collaborator branches.

### November 24 — Resolve reviewable evidence and table decisions

- [ ] **Ryiad:** review E4 existing diagnostic and record whether its observed gate analysis is scientifically usable; do not present inferred causes as observed codes.
- [ ] **Ryiad + Nikta:** check RQ1 historical 18-case C4 denominators and Phase 5K V2 numbers against the merged artifacts; preserve the three C2 false-completes as exceptions.
- [ ] **Alex:** verify RQ3 T/R/C, rule/model channels and denominators against the frozen 108-response scorer; mark independent mutation-label review pending unless a finalized freeze exists.
- [ ] **Nikta:** confirm the public status of RQ2 review without opening unfinished submissions; freeze the paper’s pending language and exclude the AI-review output absent a public authorized result.
- [ ] **All authors:** decide which RQs remain in the submission under the smallest defensible scope below.

### November 25 — Complete author-owned manuscript content

- [ ] **Nikta:** complete assigned introduction/abstract, RQ statements, RQ1/RQ2 results and integrated discussion under the work split.
- [ ] **Alex:** complete assigned Critic/RQ3 sections and the RQ4 structural-only/NO-GO qualification.
- [ ] **Ryiad:** complete assigned related work, evidence/GSN methods, RQ1 failure analysis and threats, with verified citations.
- [ ] **Nikta + Alex + Ryiad:** update quantitative tables and captions; run saved-result consistency checks only. No benchmark, inference or simulation is authorized by this plan.

### November 26 — Reproducibility, layout and scientific sign-off

- [ ] **Nikta:** obtain/use the official NeurIPS 2026 style and a compatible TeX environment; compile and inspect the PDF, main-content page count, citations, figure references, appendix links and tables.
- [ ] **All authors:** perform a claim-by-claim pass against `FINAL_EXPERIMENT_REGISTRY.md` and `RESULT_ADMISSION_CHECKLIST.md`; remove unsupported generalization or physical-safety claims.
- [ ] **Each author:** supply and approve contribution and AI-use disclosures; verify only their own citations and statements.
- [ ] **Nikta:** record unavailable checks as blockers; do not report a successful compile, page limit or reproducibility check unless actually completed.

### November 27 — Final go/no-go

- [ ] **All authors:** sign off on manuscript scope, data status, caveats, author contributions and disclosures.
- [ ] **Nikta:** verify exact final commit, compiled PDF, required files, page count and venue checklist; confirm no private reviewer material, unfinished submissions, collaborator work or frozen-output edits were included.
- [ ] **All authors:** if a scientific admission gate is still open, retain the fallback (omit/pending) and decide whether the resulting manuscript still supports its stated contribution. If not, choose NO-GO rather than overstating evidence.

## Manuscript table disposition

| Current table/content | Evidence status | Required action before submission |
|---|---|---|
| **RQ1 historical ranking** (`tables.tex`, ranking rows; `n=96`) | Supported by saved historical metrics for that eligibility denominator; execution contexts are clustered and this is not independent language sampling. | Retain only with the exact ranking cohort/eligibility and cluster limitation. Keep separate from C4 completeness. |
| **RQ1 historical C4 completeness** | Frozen case analysis supports exact 10/18, semantic 10/18 and lexical 8/18; currently not explicit in the paper table. | Add a clearly labeled 18-question C4 row or keep out of the table and cite in author-written results. Do not merge with Phase 5K. |
| **RQ1 Phase 5K V2** | Saved retrieval metrics and nominal 24/24 bundle, 84/84 obligations and 80/80 critical abstentions are traceable; the 24 C4 instances repeat eight templates over three scopes. Three C2 temporal false-completes qualify nominal completeness. | Retain only with repetition, denominator and false-complete caveat in table/caption or nearby text. Do not imply all original query obligations were met. |
| **RQ1 30-execution expansion** | No independently verified reference questions frozen; no benchmark score. | Exclude performance rows. A short “pending expansion” statement is optional and must not be framed as a result. |
| **RQ2 historical checker / N3 calibration** | Saved descriptive counts exist, but historical reference has no positive labels and N3 is 3 cases from one source group with one positive and one negative applicable case. Neither is independent test accuracy. | If retained, label as development/calibration, show applicable/determinate denominator and source group; state precision/recall limitations. Do not pool them. |
| **RQ2 60-execution coverage/transfer** | Frozen coverage counts are supported; no reference labels. Changed-task same-scene result is 0/100 determinate applicable object units across 50 executions; 38 cross-scene cases are mapping exclusions. | Retain as coverage/abstention only with object-unit and execution denominators separated. Do not label as accuracy or “100 failed runs.” |
| **RQ2 44-case independent human evaluation** | Ongoing; not admitted. | Exclude metrics. If the study is mentioned, mark all outcome fields PENDING and do not imply a completed evaluation. |
| **RQ2 independent AI review** | Ongoing; no authorized public finalized result; private outputs not inspected. | Exclude results. Do not include in human agreement or reference columns. |
| **RQ3 108-response T/R/C** | Saved scored results support descriptive development-only values: 12 cases, 2 development groups, 0 independent, three paired repeats; label review pending; C admission status only. | Retain only if the paper clearly labels these facts and condition-specific denominators; no independent accuracy or validated physical-checker interpretation. Otherwise omit the table. |
| **RQ4 structural tests** | CPU/software contracts and scripted examples only; feasibility inventory says zero eligible real revision cases with actionable authentic Critic findings. | Retain only as implementation evidence if central to the contribution. Mark real-model revision effectiveness NO-GO/not evaluated; omit any empirical efficacy row. |

## Smallest scientifically defensible submission scope

If the new human/reference reviews are unfinished by November 27, the submission can still describe **only evidence already frozen and admissible with explicit development/exposure limits**:

1. RQ1 historical ranking and Phase 5K V2 results, with the separate 18-case historical C4 completeness analysis and all three Phase 5K C2 temporal false-completes disclosed.
2. RQ2 saved historical development/N3 calibration and the 60-execution coverage/abstention analysis, each in separate cohorts; no independent checker-accuracy claim and no 44-case result.
3. RQ3 full 108-response Qwen experiment only as a development-only paired comparison, with developer-label provenance and independent label audit pending; C is admission-status-only.
4. RQ4 structural/software testing only. Do not claim real-model revision effectiveness or a second real Critic cycle. If the paper’s claimed contribution depends on RQ4 efficacy, remove or narrow that claim; if this breaks the central contribution, the correct decision is NO-GO.

The authors may narrow the RQs and claims to match this evidence boundary. Do not represent a pending evaluation as a completed result, and do not infer physical safety from retrieval completeness, checker mapping, argument validity or simulation evidence.

## Admission gates and final GO / NO-GO checklist

### Evidence admission

- [ ] Every reported result points to a frozen artifact and exact repository revision; no values come from uncommitted collaborator work unless separately reviewed, authorized and cited as such.
- [ ] Denominator, unit, eligibility/exclusion rule, source-group count and exposure are stated; repeats are not counted as independent source groups.
- [ ] N/A, excluded, uncertain, abstained and determinate outputs remain distinct; no abstention is recoded as a correct negative.
- [ ] Any claimed independent human reference has completed exposure declarations, evidence-interval checks, decision freeze and documented disagreement handling.
- [ ] No RQ1 expanded metric appears before Ryiad’s references are independently verified and authorized for freeze.
- [ ] RQ3 C is described only as admission-status-only; no independent mutation-label result appears before an authorized review freeze.
- [ ] No real-model RQ4 revision or second Critic result is claimed.

### Manuscript and reproducibility

- [ ] All required sections are author-written; each RQ is explicit and matches the results actually admitted.
- [ ] Tables, captions, figures and text agree with the registry and saved artifacts; historical C4 and Phase 5K cohorts are separate.
- [ ] Citations are real, checked by the authors, and present in the bibliography; no placeholder remains.
- [ ] Figure files exist, captions/labels are referenced, appendices resolve, and no table or citation points to a missing artifact.
- [ ] Official NeurIPS 2026 style is used; the final PDF compiles and the nine-page main-content limit is verified. If the compiler/style is unavailable, this gate is open.
- [ ] Contributions, affiliations, AI-use disclosure, venue checklist, reproducibility details and author approvals are complete.
- [ ] Final commit contains no private/incomplete reviewer records, sealed answer keys, credentials or unauthorized collaborator changes; frozen experiment outputs are unchanged.

### Decision

- [ ] **GO:** all applicable evidence and manuscript gates pass; each author approves the scoped claims and the final PDF is verified.
- [ ] **CONDITIONAL GO:** only explicitly pending evaluations are omitted/marked pending, the narrowed contribution remains supported by admitted results, and all manuscript/reproducibility gates pass.
- [ ] **NO-GO:** a central claim still requires missing independent evidence, a required review or reference is portrayed as complete when it is not, results cannot be traced, or required compilation/page/authorship checks remain unresolved.

The final decision belongs to the authors. A deadline, available prediction or successful software test does not close a scientific admission gate.
