# RQ3 conditional-source eligibility audit

## Decision

**No candidate is admitted for Drafter inference.** The prior R1 validation build identifies 20 distinct LIBERO-long executions and records technical source checks for each, but the authoritative RQ3/RQ4 intake has zero cases, zero eligible cases, is not frozen, and has no labels assigned. Required cohort approvals and case-bound request inputs are absent. The approved DRAFTER_GENERATION_MANIFEST.csv remains empty and no Drafter requests were prepared.

No reviewer judgments, personal identities, or coordinator assignment mappings were opened. The source build receipt contains only generic package labels, not annotations. The ongoing RQ2 review was neither inspected nor altered.

## Sources inspected

- evaluation/r1_v3_human_validation_20/BUILD_REPORT.json: 20 selected source records, each with a canonical run ID, focal object ID, trajectory SHA-256, and prior-build source/camera checks.
- evaluation/r1_v3_human_validation_20/build_packages.py: source path selector, evidence families, and R1 review interval described by the previous package builder.
- evaluation/m4_20261127/rq3/heldout_expansion/PARENT_SOURCE_INVENTORY.csv: 432 source-catalog records. Exact canonical-ID intersection with these 20 R1 records is 0.
- Aggregate project intake snapshot SOURCE_GATE_SNAPSHOT.json, based on candidate_intake_manifest.v0.2.json, SHA-256 072f3ece5a3d9920fe12f4da6fc047e79d1d434eab6f84c8c426960809546434, repository snapshot d7571264c46fce4610d237dd2d68034e49c24b56.

The 20 source IDs and hashes are in SOURCE_ELIGIBILITY_MATRIX.csv. They comprise 10 task00 and 10 task01 execution IDs, all from LIBERO-long, OpenVLA-OFT, and the same recorded variant token. The 20 IDs and 20 recorded trajectory hashes are distinct. The source receipt contains no authoritative source-group ID or grouping rationale, so **0 independent source groups are verified**. The precise scene/environment IDs and full checkpoint/configuration revisions are also not recorded in the case receipts.

The separate 30-execution RQ1 recovered cohort was not used or counted as an RQ3 source.

## Source availability and prior technical verification

The historical package build reports:

- 1,214 files in the prior R1 evidence archive verified against its SHA256SUMS receipt; the archive hash matches the frozen provenance receipt.
- 20/20 selected trajectory hashes checked, with source file stat preserved during each package build.
- 20/20 camera-array comparisons matching the prior export.
- 180 generated video artifacts with recorded hashes/frame counts.

These are **prior build-time checks**, not a fresh source revalidation. The repository build report does not retain the resolved --recordings root or each case's resolved task-directory/episode selector. The source builder describes a relative selector under long/task_00 or long/task_01, but its per-case selector inputs are not part of the public build receipt. Consequently, this audit freshly verified **0/20 original HDF5 paths/bytes**. This means current access is unverified, not that the files are known to be absent.

The repository contains the build code and verification receipt, not the raw HDF5 recordings or the previously generated review evidence exports. Prior exports included video, frame references, contact records, object poses, native geometry, and raw image hashes. That package-level integrity does not make those exports an admitted Drafter evidence bundle.

## Scientific and contract gates

| Gate | Current count | Status and evidence |
|---|---:|---|
| Distinct source execution IDs / trajectory hashes | 20 / 20 | Verified in BUILD_REPORT.json; this does not establish source-group independence. |
| Independent source-group IDs verified | 0 / 20 | The authoritative build receipt contains no group IDs or grouping rationale. |
| Prior source-package technical checks | 20 / 20 | Prior-build receipts only; fresh original-byte access is unverified. |
| Exact source ID overlap with the 432-row RQ3 source catalog | 0 / 20 | Exact-ID comparison only; it does not prove absence from every development exposure. |
| Per-record source reuse approval | 0 verified | No per-record receipt in the authoritative intake snapshot. |
| Independent R1 reference plus adjudication/freeze | 0 verified | Intake has no cases, labels, or frozen reference. No reviewer submissions were inspected. |
| Complete execution-bound requirement configuration | 0 verified | The prior review form records r1-initial-table-support-v3-20261024; the complete approved Drafter configuration and digest are not bound to each execution. |
| Target/protected-object/surface mapping | 0 verified | A focal object ID is recorded, but the approved full roster, roles, surface identity, and execution-specific configuration are not bound. |
| Approved source-bound monitoring interval | 0 verified | The prior R1 package describes frame 10 through terminal; its source-clock boundary provenance is not bound to a Drafter request. |
| Drafter-contract evidence package | 0 verified | No case-bound Phase 5 structured request/bundle or registry export with validated execution, object, selector, and hash bindings is present. |
| Critic leakage/exposure clearance | 0 verified | Prior R1 reviewer-package exposure is known; Critic prompt/rule development exposure remains unverified. |
| Approved Drafter requests | 0 | No requests pass all gates; none were constructed. |
| Admitted new parent groups | **0** | Formal approvals and required scientific/source bindings are missing. |

The exact blocker codes are in SOURCE_ELIGIBILITY_MATRIX.csv; overlapping blocker counts are in BLOCKER_COUNTS.csv. Every listed blocker affects all 20 candidate rows, so these counts overlap and must not be summed as though they were disjoint cases.

The aggregate intake records these six approvals as outstanding:

1. Operational RQ3/RQ4 wording, strata, gold-label rubric, and scoring.
2. R1 owner approval of empirical scope, source reuse, and admissible-evidence policy.
3. Independent R1 review, adjudication, explicit approval, and reference freeze.
4. Critic owner closure or explicit acceptance of adversarial/contract audit blockers.
5. Case eligibility, partition, leakage review, reviewer effort, and blinding-key custody.
6. Evidence arms, model/run settings, repetitions, interval method, and cost accounting.

No approval is inferred from a recording, prior successful package build, or prior model execution.

## Drafter request readiness

The current Drafter contract requires a complete R1 configuration, exact target execution metadata, explicit source-bound monitoring scope, and evidence records/context validated against the same execution and selectors. The Phase 5 adapter preserves evidence as retrieved context and does not authenticate the original source or establish physical sufficiency.

For these 20 candidates, no execution-bound configuration, complete object/surface mapping, resolved current source path, or Drafter-contract evidence bundle is available in the inspected repository records. Therefore, a request could not be responsibly assembled, even as a useful CPU diagnostic. The candidate source records are not entered into the approved generation manifest.

The existing 432-source catalog records no original Drafter argument for its rows. It is not evidence that these 20 R1 records already have valid GSN parents. The 20-case R1 cohort also has known prior R1-review exposure; Critic-specific leakage must be reviewed before calling any future parent unseen.

## Serializer diagnosis

The previous saved Qwen plan was schema-valid under its historical graph-plan schema but semantically invalid. Four supported_by edge targets were evidence-registry IDs rather than declared graph-node IDs; the saved structured diagnostic was plan_invalid_edge_endpoint:cream_cheese_1. The graph used one-character R statements/summary and [R] limitations, and its proposed nodes had no usable evidence citations. The serializer correctly rejected it before shared GSN and Critic validation. Its stderr file was empty; no Python traceback was saved.

The current contract separates JSON shape validation from graph-semantic checks. Current bounded CPU regression tests pass endpoint, evidence-citation, prose-validity, and ordering checks. No implementation defect is demonstrated and validation was not weakened. The saved response cannot be mechanically converted into a valid argument: doing so would require substantive claim, graph, and evidence decisions. It remains rejected and unchanged; a later approved source must receive a newly generated argument.

See SERIALIZER_FAILURE_RECEIPT.md for the artifact-level diagnosis and CPU_VALIDATION_REPORT.md for commands and results.

## Readiness

- Prior source integrity receipts: **20/20**.
- Independent source-group identities verified: **0/20**.
- Freshly reverified original source paths/bytes in this audit: **0/20**.
- Complete, technically validated Drafter inputs: **0/20**.
- Required scientific/project approvals complete: **0/20**.
- New eligible parent arguments: **0**.
- Valid generation requests prepared: **0**.
- GPU inference ready: **No**.

The next required work is an owner-approved, per-source binding packet for a small chosen subset: exact source path and fresh hash; requirement configuration/version/digest; target and protected-object/surface mappings; approved interval and temporal provenance; and the exact validated evidence bundle. The independent R1 reference/adjudication and Critic exposure/contract approvals must also be recorded before any request is admitted.
