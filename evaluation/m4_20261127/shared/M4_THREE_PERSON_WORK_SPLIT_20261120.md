# Milestone 4 — three-person execution handoff (20–27 November 2026)

This is an internal task allocation, **not** manuscript text or a statement that any experiment has passed. It supersedes the temporary two-person task allocation. Milestone deadline: **27 Nov 2026, 11:59 PM EST**.

## Fixed constraints

- **Nikta alone runs all Hestia/GPU inference and simulator jobs.** Alex and Ryiad work on CPU-only local code, fixtures, review and analysis. Nobody asks either teammate to access Hestia. Nikta checks existing production GPU jobs and allocations before launching work.
- N2 is source audit, not test-case approval. The 60 source-verified candidates are **provisional/development-exposed**; zero independent RQ3 scoring cases are approved in the frozen N2 inventory. The 432 manifest entries are a source pool, not 432 independent samples.
- N3's source replay, perturbation/sham and pre-policy trial ran; the **three new calibration cases still require independent current-v3 review**. An intervention label is not an R1 gold label. The pre-policy control has no frame-10 support and is R1-non-applicable. Cases share **one canonical parent source**, not three independent cases.
- Do not admit real R1 checker outputs as authoritative until the independent empirical admission gate is met. RQ3 C cannot assert checked physical safety using unvalidated outputs. If C is unavailable, mark it unavailable (rather than synthesizing claims).
- Preserve frozen M4-v1.0 paired T/R/C design, same eligible parent groups/mutations, exact model/prompt/decoding/output-limit records and three repeats *if feasible*. Repetitions and mutations are paired observations, not new independent N.
- Instructor feedback prioritizes **verified R1 positive violations**, **GSN mutations and paired Critic evidence conditions**, and explicit accuracy/abstention metrics when estimable. Honest missing-data results take priority over ungrounded metrics. Do not expand RQ4 or rebuild infrastructure ahead of these priorities.
- The instructor forbids AI-generated final-paper prose. Each human author writes their assigned scientific text; disclose AI-assisted code/debugging/annotation reconciliation under the required AI-use disclosure.

## Owners, work and outputs

### Nikta — integration, GPU and RQ2 scientific coordination

- Own Hestia, GPU allocation checks, live Critic inference, calibration evidence provenance, and run receipts/hashes. **Only Nikta executes GPU jobs**.
- Deliver both new **blinded** N3 reviewer packages to the human reviewers without treatment labels. Keep mapping sealed until submissions are finalized; coordinate discrepancy resolution with independent evidence. Case creator is not independent gold truth.
- After review, update `rq2/R1_CASE_MANIFEST.csv`, `rq2/R1_REVIEW_RECORDS.csv`, `rq2/R1_EVIDENCE_NOTES.md` with eligibility, timings, 20 Hz limitations and results. If no verified in-scope positive by Nov 22, stop expansion and report positive-case recall **not estimable**.
- Run Alex's frozen RQ3 model-only T/R/C batch on **eligible inputs only**, using identical decoding settings and repeated trials if feasible, and return response JSON, model settings, GPU/device/seed metadata, errors, source/exposure IDs and manifests.
- Integrate results, verify no false safety claims, manage Git review/merge and final submission.

### Alex — Critic/RQ3 experiment owner (no GPU required)

- Own Critic 0.5.0 deterministic absolute-safety rule, CPU regression tests, fixed version/model/prompt configuration and **three GSN mutations**: unsupported absolute guarantees, incorrect evidence links, unjustified scope narrowing. Prepare paired clean controls and a manifest with parent IDs and exposure status.
- Implement/verify **experiment-only rule-blind model evaluation**. Model must not see `already_found` rule findings in T, R, or C, and deterministic-duplicate screening must not erase genuine model responses from the **model-only** score. Keep normal production `critic.review()` unchanged.
- Freeze **rule-only**, **model-only T/R/C**, and **deduplicated rules+model** scoring as separate reported channels. Preserve citation/grounding rejection, human-review requirements and provenance. Record all actual repeats and decoding settings; do not turn scripted/mock tests into measured LLM results.
- Hand Nikta the exact CPU-tested inference inputs, command/config and scoring scripts. After Nikta returns GPU outputs, calculate detection by mutation type/condition, false positives on clean controls, reference-supported correctness (where available), mean ± standard deviation over actual runs, and caveated denominators. No fabricated independent N.
- Personally author Critic method, mutation design, RQ3 experiment and RQ3 results text for the final submission.

### Ryiad — Drafter/integration, independent evaluation and reporting (no GPU required)

- Resume ownership of **Drafter/GSN input quality**, frozen schema and CPU integration checks. Build the minimum valid argument/evidence fixtures needed for Alex's matched mutation trials; do not change Alex's Critic rule or Nikta's R1 contract.
- Serve as an **independent blinded N3 reviewer** only if intervention assignments and candidate labels were not disclosed to him; inspect initial support, support loss, unsupported downward motion, floor contact, timing and evidence sufficiency, with references and uncertainty. If exposed, disclose and use another eligible reviewer.
- Help coordinate a **second genuinely independent reviewer** (Alex if unexposed; otherwise another eligible reviewer). Two independent observations are not automatically a verified R1 violation; check disagreements against physical logs, not intervention identity.
- Independently inspect Alex's RQ3 mutation labels, clean controls, pairing and scoring logic to avoid developer-only reference labels; keep reviewer/test-author exposure visible and report any unresolved issues.
- Analyze the **task-role transfer failure** (previously 0/100 decision coverage) using source/eligibility limitations, without claiming cross-task generalization. Contribute the R1 algorithm box, limitations/validity threats and reproducibility discussion from actual evidence.
- Personally author Drafter/GSN methodology, transfer-failure analysis and assigned reporting sections; help check required citations, references and complete AI-use disclosure.

## Immediate deadlines and handoffs

| Due | Nikta | Alex | Ryiad |
| --- | --- | --- | --- |
| **Nov 20–22** | Distribute N3 blinded packages; supervise independent intake; R1-v3 classification/hard stop | Freeze mutations, clean controls, T/R/C input schema and rule-blind CPU tests | Complete eligible independent N3 review; check mutation and citation oracle design |
| **Nov 22–24** | Approve inputs and run authorized GPU RQ3 batches; return artifacts | Deliver scripts/config; accept and score real model outputs | Independently verify paired-case scoring and analyze task-role failure |
| **Nov 24–25** | Audit denominator/validity and integrate tables | Finish RQ3 quantitative tables and limitations | Finish RQ2/transfer/GSN analysis and visualizations |
| **Nov 26–27** | Final fact audit, Git integration and submission | Write/edit own Critic/RQ3 sections | Write/edit own related methods, threats and required disclosures |

## Instructor M3 feedback to verify in final manuscript

1. Narrow title and research questions to measured contributions (primarily RQ2/RQ3); do not claim safety-case generation novelty beyond demonstrated components.
2. R1 algorithm box, exact perturbation scope/validity, independent gold-label status, checker precision/recall/abstention **only with qualified denominators**.
3. Three GSN mutation operators; explicit T text-only, R retrieval-only, C checked-evidence baseline definitions; same cases/parameters; repeated model trials and **mean ± std** where available.
4. One experimental-settings table (policy, task, scene, model, temperature/decoding, hardware). Explain RQ2/RQ3 validity threats: one source group/scene/policy, simulated perturbation, 20 Hz sampling and limits to independence.
5. Explain task-role transfer failure; move engineering regression-test counts to appendix; no universal safety claim from qualified negatives.
6. NeurIPS 2026 `\\usepackage[preprint]{neurips_2026}`, ≤9 main content pages, 150–200 word abstract with an **actual** quantitative result, 10–15 central related papers, natbib, full checklist, contribution statements for **all three** teammates, repository URL, complete AI-use disclosure. Order: paper, references, appendices, checklist, contributions, AI-use disclosure.

No live RQ3 model findings or independent N3 reviewer judgments are implied by this plan.

## Additional work balance and direct-paper ownership (Nov 20 revision)

The individually issued handoffs supersede the brief owners table above for detailed workload allocation. All three teammates must **personally write and edit their own sections directly in the same shared manuscript**, not merely send bullets to Nikta or rely on AI-generated report prose.

**Nikta:** all GPU/Hestia execution, R1-v3 calibration review coordination and RQ2 scientific decisions, RQ2 evaluation, frozen run provenance, main-paper abstract/introduction/R1 algorithm and results, full manuscript integration and submission.

**Alex:** merged Critic 0.5.0/rule owner, independent model-only T/R/C evaluation adapter (PR #30 must first pass CPU tests), benchmark authoring, full scoring/repeated-trial evaluation, Critic/mutation/results sections written by Alex.

**Ryiad (expanded, substantive ownership):**
1. Own the **Drafter/GSN and source-to-evidence fixture interface**: build and CPU-validate clean inputs and reproducible contract tests for Alex's three mutation operators; do not require Hestia.
2. Perform an **independent R1-v3 blinded physical-event review**, only if not exposed to condition mapping; otherwise coordinate an unexposed reviewer and work on audit instead.
3. Independently audit **mutation labels and T/R/C scoring**, including control false positives, model/rule double counting, source grouping and invalid-input-vs-semantic-error strata.
4. Lead a **source-indexed 0/100 task-role transfer-failure root-cause investigation**, with a bounded CPU diagnostic when a valid source permits it.
5. Lead a **bounded 10/18 multi-source retrieval incompleteness study**, analyzing the eight incomplete cases and distinguishing source gaps from query/contract bugs; keep RQ1 as supporting work.
6. Run CPU-only Drafter -> Critic -> scripted Revision integration/regression checks without claiming independently validated RQ4 revision effectiveness.
7. Personally write the GSN/evidence pipeline methodology, related work synthesis, transfer/retrieval results, validity/reproducibility discussion and supporting appendix material.

**Deadlines:** Nov 22 labels/input freeze; Nov 24 scientific result freeze and Ryiad's transfer/retrieval/scorer QA; Nov 25 each author inserts own sections; Nov 26 full-PDF cross-review; Nov 27 submit.

**If time remains AFTER P0:** broaden independently reviewed R1 positives, larger independent RQ3 source groups, one more task/requirement with valid reference, genuine model-based Revision/Critic-2 experiments, second-model ablations and Milestone 6 code packaging. None may jeopardize the nine-page paper, checklist, full AI-use disclosure or deadline.
