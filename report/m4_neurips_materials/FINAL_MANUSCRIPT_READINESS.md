# Final manuscript readiness audit

**Audit base:** `main` at `2bbfbc19dc3678b8334ef510115eaac26a0eb6a3` (merged PR #47). This is a technical audit only. No author-owned final-paper prose was drafted, and no incomplete or private reviewer output was opened.

## Manuscript source and scope

The current committed source is `report/m4_neurips_materials/main.tex`, with tables in `report/m4_neurips_materials/tables.tex` and a technical claim checklist in `report/m4_neurips_materials/CLAIM_EVIDENCE_CHECKLIST.md`. It is a placeholder skeleton rather than a complete manuscript. The separate `report/M4_RESULTS_DISCUSSION_DRAFT.md` in the local paper-draft worktree is untracked, was not inspected, and is not part of main; it must not be mistaken for an author-approved final section.

Required top-level headings are present: Abstract, Introduction, Related Work, Methodology, Experimental Setup, Results, Discussion, Threats to Validity and Conclusion. There are no finalized RQ1–RQ4 question statements; the Introduction placeholder tells the assigned author to add them. The Experimental Setup placeholder requests distinct cohorts and scoring rules.

## Specific issues to resolve

| Priority | Source location | Audit finding and action for authors |
|---|---|---|
| P0 | `main.tex:21-23` | Abstract is entirely a placeholder. The required 150–200 words, a verified quantitative result and the authors’ final qualification are missing. |
| P0 | `main.tex:25-32` | Introduction, explicit RQ statements, contribution scope and Related Work are placeholders. Related Work has no verified citations. Authors must write their assigned sections and verify cited works. |
| P0 | `main.tex:31-32`, `41-49`, `53-60` | Methodology, Experimental Setup, Results, Discussion, Threats and Conclusion have no author-written content. RQ4 author assignment is still “assignment to confirm.” |
| P0 | `main.tex:62-73` | No bibliography/citations, author identities/affiliations, contributions or approved AI-use disclosure. `main.tex` has no `\cite*`, `\bibliography` or `\addbibresource`; no `.bib` file is tracked in the manuscript directory. |
| P1 | `tables.tex:13-21` | Historical ranking values use `n=96`, while the distinct historical C4 completeness result uses 18 questions: exact 10/18, semantic 10/18, lexical 8/18. The current table says “Execution contexts 18” but omits the C4 mode-specific denominator and could conflate ranking and completeness cohorts. Add an explicit row or label the distinction in author prose. |
| P1 | `tables.tex:17-20` | Phase 5K V2 has nominal C4 bundle completeness 24/24 and 84/84 obligations, but the 24 C4 instances are eight repeated templates across three scopes. The three `KH2-C2-*` false-completes are separate C2 temporal cases, not C4 cases; state that the planner dropped joint-position requirements while returning COMPLETE. Do not imply unqualified original-request completeness. |
| P1 | `tables.tex:39-42` | RQ2 needs the 3-case/1-source-group calibration clearly named as calibration, the historical 20-object/4-execution development reference kept separate, and the 60-execution cohort identified as 300 object units. Add the 50-execution changed-task same-scene partition: 0/100 determinate applicable object units and 100/100 abstentions; 38 cross-scene mapping-gate exclusions are separate. The 44-case human evaluation and AI-review experiment remain pending; no results are admitted. |
| P1 | `tables.tex:60-70` | RQ3 condition rows agree with the saved table, and correctly say two development parent groups / zero independent groups and C status-only. State explicitly that each condition has three paired repeats (36 outputs; mutation denominator 24; control denominator 12), so repeats are not independent source groups. Clarify clean-control false positives are equal for model-only and rules+model here; consider including the separate deterministic rule-only row. Independent label audit stays pending. |
| P1 | `tables.tex:87-89` | The RQ4 table correctly distinguishes CPU/saved-example checks from real-model behavior but should say NO-GO for a real-model effectiveness study: zero eligible real cases with an authentic actionable Critic finding, zero independent groups, no Qwen-generated revision and no second real Critic pass. The feasibility inventory is on an unmerged branch. |
| P1 | `main.tex:34-39` | Figure is a boxed placeholder, not an architecture diagram. No author-reviewed image/diagram or final caption exists. The label `fig:workflow` is not referenced in the current source. |
| P1 | `CLAIM_EVIDENCE_CHECKLIST.md` and `tables.tex` | The checklist is useful but not yet complete author approval. It should add the explicit historical 18-case C4 figures, the changed-task 0/100 partition, the 44-case and AI-review pending states, and current source-group denominators. |
| P1 | `main.tex:12-14` | The source documents a nine-page main-content limit from the M4 handoff. The draft has not been typeset, so compliance cannot be assessed. |
| P1 | `main.tex:4` | No `neurips_2026.sty`, `.bib`, `latexmk`, `pdflatex` or `tectonic` was found in the checked environment. Compilation and PDF/page-count verification are blocked; do not claim a successful compile. |
| P2 | `main.tex:65-73` | Appendix checklist, contributions and AI-use sections are placeholders. The required supplemental materials are not complete. |

## Quantitative consistency notes

- The currently committed numbers in the RQ2 and RQ3 tables are traceable to saved aggregates. `python3 integration/verify_saved_results.py` passed at the audit base and reported `private_review_records_opened: 0`.
- RQ1 historical counts were checked against `readiness_evaluation/RETRIEVAL_METRICS.md` and merged PR #47’s case-level analysis. `python3 evaluation/m4_20261127/rq1/build_failure_analysis.py --check` passed; it verifies the frozen historical and Phase 5K artifacts and replays only the saved planner on the three known cases. It does not run a retrieval benchmark.
- The RQ2 0/100 transfer figure is 100 applicable **object units** from 50 changed-task executions, not 100 independent task executions. The 60-execution cohort has 300 object units and is coverage-only.
- RQ3 percentages are paired condition/repeat outputs from two development parent groups, not independent evaluations. The scorer’s developer labels remain pending independent audit; no external reference-label claim is admitted.
- Neither retrieval completeness nor GSN/schema validity means demonstrated physical safety. This qualification must appear in author-written interpretation and conclusion.

## Compilation and page status

No LaTeX compiler or official NeurIPS 2026 style file was available, so compilation was not attempted and the current page count is **unknown**. Since almost all body text is still placeholder text, a page count on the skeleton would not establish final nine-page compliance in any case. Use the official venue style and final author-written content before checking layout.

## Submission readiness

**Not submission-ready.** The section scaffold and technical tables exist, but every narrative section, citations, actual figure/caption, author-approved claims, disclosure material, final human-reference decisions, and compiled-PDF/page verification remain unfinished. The authors—not this audit—must write the manuscript sections under the M4 authorship allocation.
