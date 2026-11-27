# RQ4 finalized scoring results

## Status and provenance

These results reproduce the completed frozen RQ4 pilot from run `real_run_20261124T215049Z`. The protocol/run source commit was `c524765604f61fbb15a5c9c7bd46d2b76516a5c3`; the final scorer correction is PR #57 commit `dd0c4f8815cd3c230b301280f543d333a756985e` (source SHA-256 `0c2c7146a227c0238dc14493856fcc6cf5322861873dd6cb208ee3101109c866`; its recorded CPU suite passed 29/29). The source result files were verified against the preserved final integrity record. This publication derivative does not rerun inference, human review, or scoring.

There were 9/9 valid genuine Qwen responses, 27/27 valid second-Critic responses, and all 12 revision outputs were applied. There were 3 planted unsupported-guarantee defects, 2 source groups, zero independent evaluation cases, and one defect type. Qwen has three repeated outputs per defect; template has one output per defect. Repeated outputs are not independent cases.

## Frozen outcomes

| Measure | Qwen | Deterministic template |
|---|---:|---:|
| Correct repair (four prespecified criteria) | 9/9 (100.0%) | 2/3 (66.7%) |
| Defect fixed | 9/9 (100.0%) | 3/3 (100.0%) |
| Revised claim supported by evidence | 9/9 (100.0%) | 2/3 (66.7%) |
| New problem introduced | 0/9 (0.0%) | 1/3 (33.3%) |
| Scope preserved | 9/9 (100.0%) | 2/3 (66.7%) |
| Invalid, abstained, or missing | 0/9 (0.0%) | 0/3 (0.0%) |
| Second-Critic target reflagged | 0/9 reviews | 0/9 reviews |
| Second-Critic reviews with new objection | 2/9 reviews | 2/9 reviews |

Human outcomes are coordinator-confirmed from a single consensus form. Agreement is not independently recalculated; Cohen's kappa is unavailable. The public result CSV is an explicitly sanitized derivative of the frozen per-output table: reviewer/blind identifiers, raw revised prose, and objection text have been omitted; the recorded judgments and counts are unchanged. See `RQ4_PUBLICATION_AUDIT.md`.

## Interpretation and claim limits

In this bounded development-stage pilot of three planted defects, all nine Qwen outputs met the prespecified four-part human criterion for correct repair (9/9), compared with two of three deterministic template outputs (2/3). All 12 revisions fixed the planted defect. One template revision introduced a semantic role mismatch and failed the evidence-support and scope criteria. These observations are descriptive for the repeated outputs on this small fixed set.

Do not claim general or comparative Revision Agent effectiveness, generalization to arbitrary requirements or naturally occurring Critic findings, physical safety correctness, correctness from Critic acceptance, or fully validated end-to-end safety-case generation. The broader RQ4 effectiveness study remains **NO-GO**. No effect of admitted physical checker evidence was tested.

## Reproducibility

From the repository root:

```sh
python3 evaluation/m4_20261127/rq4/finalized_results/validate_public_results.py
sha256sum -c evaluation/m4_20261127/rq4/finalized_results/ARTIFACT_SHA256SUMS.txt
```

The validator recomputes primary numerators and denominators from the sanitized case-level rows and checks them against the published aggregate CSV. It does not rerun RQ4 scoring or reconstruct any confidential reviewer mapping. The frozen scoring implementation is `evaluation/m4_20261127/rq4/experiment/score.py`; full scorer reruns require the confidential sealed review inputs and are intentionally not published.

The raw stage response hashes were preserved in the private finalization record: Stage 1 SHA-256 `388eef7dfbdb346e5ee9e907266e6744e65d66c7d022270b53711729cdf570ae`; Stage 2 SHA-256 `5888078ed549427db7264fc6e11b1306e1fd3661570d0c9129d4b65e7bb1afe8`. Reviewer forms, blind key, and coordinator mappings are confidential and excluded.
