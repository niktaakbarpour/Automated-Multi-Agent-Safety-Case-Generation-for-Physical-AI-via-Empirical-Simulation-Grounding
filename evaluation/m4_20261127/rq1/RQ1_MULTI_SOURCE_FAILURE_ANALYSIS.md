# RQ1 multi-source retrieval failure analysis

This technical audit covers saved Phase 5J and Phase 5K V2 artifacts for the [Milestone 4 handoff](../RYIAD_HANDOFF.md). Phase 5J shows gaps in the retrieval routes used for multi-source questions. In Phase 5K V2, the planner dropped a required family even though the source had the requested values.

## Phase 5J historical completeness

The original assessment records 10 of 18 complete cases in exact mode, 10 of 18 in semantic mode, and 8 of 18 in lexical mode. These 18 C4 multi-source questions are a subset of the 162 final questions. The audit checks all three modes for each C4 case using the frozen completeness field and missing facets. It checks the execution, task, variant and source binding for each returned record. [Frozen references](../../../evaluation/r1_v4/rag_evidence_database/readiness_evaluation/EVALUATION_DATASET.jsonl) · [Saved outputs](../../../evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_RESULTS.jsonl) · [Original metrics](../../../evaluation/r1_v4/rag_evidence_database/readiness_evaluation/RETRIEVAL_METRICS.md)

All three modes returned API status `ok` with incomplete evidence on the same eight cases. The historical raw endpoint did not record a separate obligation plan. Its status describes the response to the raw request. The saved assessment records missing facets of the original question.

The archived historical replay reused exposed Phase 5J cases. Its verified source records corroborate the availability of some missing evidence at the same scope. The historical completeness figures above use the original assessment. [Historical comparison](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/HISTORICAL_5J_COMPARISON.md) · [Archived replay](../../../evaluation/r1_v4/rag_evidence_database/working_result_archive/additional_working_summaries/trustworthy-phase5k-working/HISTORICAL_5J_COMPARISON_RESULTS.json)

| Case | Missing obligation | What the frozen evidence establishes |
| --- | --- | --- |
| C4-07 | Original action and chunk metadata | The historical raw response carries summary associations. The archived replay verifies policy and chunk metadata for steps `000119` and `000120` at frames 130–131. It supplies references to the executed action arrays. |
| C4-08 | Individual camera exposure timestamps | Joint velocity was returned. Exposure-clock alignment is unsupported, and the exact timestamps are unverified for this case. |
| C4-09 | Historical producer binary authentication | The bounded producer audit found no matching `oft_adapter.py` bytes in the audited locations. Current source verification and historical binary attestation have separate evidence requirements. |
| C4-13 | Contacting object pairs with force vectors | The response supplies the simulator contact count. Legacy contact references do not establish the requested pairs and force vectors at this frame. |
| C4-14 | Recorder host timestamp | The historical response supplies a simulator time label. The archived replay verifies the recorder's monotonic, wall-clock and UTC fields at frame 67. |
| C4-15 | Original inference metadata | The historical response carries an inference-input frame association. The archived replay verifies the recorded attributes from inference call `000007` and its input-frame association at frame 70. |
| C4-18 | Geometry identity | The same-scope C3-18 reference documents the object geometry sources. Its separate geometry alias query returned no match. The C4 raw response returned only gripper positions. |
| C4-21 | Original action metadata and sensor-clock calibration | The archived replay verifies policy and chunk metadata for steps `000035` and `000036` at frames 46–47. It lists sensor-clock calibration as unmapped. Calibration remains unverified. |

Two additional cases failed in lexical mode. C4-05 and C4-20 each asked for all six exposed raw measurement families. Their lexical requests returned `no_matching_record`. Both companion modes returned all six families at the same scope, confirming a lexical retrieval miss on these questions. C4-19 stays complete as recorded in all three modes. Its authored expected status is `INSUFFICIENT`, while the saved assessment is `SUFFICIENT` because the joint-position sample carries the requested simulator endpoint label. Both fields remain visible in the case table. The historical producer discrepancy and the test's reference rules are recorded separately. [Producer audit](../../../evaluation/r1_v4/rag_evidence_database/readiness_evaluation/PRODUCER_DISCREPANCY_AUDIT.md) · [Reference construction](../../../evaluation/r1_v4/rag_evidence_database/readiness_evaluation/REFERENCE_CONSTRUCTION.md)

## Phase 5K V2 false-complete cases

The separate V2 assessment uses 216 question instances across 24 executions and 18 variants, with 72 templates. The C4 bundle result of 24 out of 24 complete sets covers eight repeated templates. The three false-complete cases below are in **C2 temporal retrieval** and share one wording template. These development-exposed failures stay separate from both the original 18 C4 cases and the new authoring package. [V2 freeze](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/HOLDOUT_FREEZE.json) · [C4 results](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/MULTISOURCE_COMPLETENESS.md)

| Case | Requested simulator time | Joint-position source frame | Plan and saved bundle |
| --- | --- | --- | --- |
| KH2-C2-02 | 2.1 s | 42 | `RESOLVED` with only `recorded_time`. The saved bundle reports complete. |
| KH2-C2-10 | 7.0 s | 140 | `RESOLVED` with only `recorded_time`. The saved bundle reports complete. |
| KH2-C2-18 | 2.1 s | 42 | `RESOLVED` with only `recorded_time`. The saved bundle reports complete. |

The frozen references hold seven joint-position values at the indicated frame in each case. The saved exact outputs also return the joint-position family. Replaying the frozen planner on CPU reproduces the omission before evidence fetching. The bundle can satisfy the reduced plan while leaving an obligation from the original question unmet. The ablation and limitations reports document the same query-to-plan defect. [V2 reference rows](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl) · [Saved V2 results](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/HOLDOUT_RETRIEVAL_RESULTS.jsonl) · [Ablation](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/ABLATION_RESULTS.md) · [Limitations](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/REMAINING_LIMITATIONS.md) · [Issue 001](../../../evaluation/r1_v4/rag_evidence_database/retrieval_remediation/issues/001-requested-obligation-coverage.md) · [Handoff case table](heldout_expansion/RYIAD_AUTHORING_PACKAGE/PER_CASE_FAILURE_ANALYSIS.csv) · [Handoff analysis](heldout_expansion/RYIAD_AUTHORING_PACKAGE/FALSE_COMPLETE_ANALYSIS.md)

## Case tables and reproduction

- [Historical case table](RQ1_HISTORICAL_CASES.csv) joins all 18 final C4 cases to their three saved modes, including complete cases and the original assessment fields.
- [Missing-obligation table](RQ1_MISSING_OBLIGATIONS.csv) records one row per missing obligation and mode. It includes source status, the observed failure stage, the original row locators and, where available, selectors and SHA-256 receipts. Phase 5J lines refer to the historical JSONL files above. Phase 5K V2 lines refer to the separate V2 files.

Run from the repository root with ordinary Python 3.12 and CPU:

```sh
python3 evaluation/m4_20261127/rq1/build_failure_analysis.py --check
python3 evaluation/m4_20261127/rq1/heldout_expansion/RYIAD_AUTHORING_PACKAGE/verify_offline_handoff.py
```

The first command checks the frozen data, planner and planner configuration hashes. It then compares both tables with a fresh build from the saved records. For the three V2 cases it executes only the query planner. The second checks the separate source extract and its blank authoring form. Original recordings were not reopened. New source references, human labels, and held-out retrieval results remain separate.
