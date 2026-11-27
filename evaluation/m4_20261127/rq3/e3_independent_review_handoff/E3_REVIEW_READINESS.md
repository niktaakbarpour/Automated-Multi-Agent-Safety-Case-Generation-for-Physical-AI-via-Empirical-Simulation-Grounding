# E3 RQ3 independent mutation-label review readiness

**Status:** review intake is prepared; no reviewer decisions have been received or created. This is not an independently validated result. Scientific-results freeze: 2026-11-24.

## Scope and source artifacts

Audited on `codex/rq3-e3-review-handoff` at the verified main base `84ca5b5f75dfe69598a6f0c794586eb38b8065b7`.

- Neutral requests and current blank form: `evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/` (`R01`–`R12` requests under `cases/` as referenced by the manifest).
- Neutral byte manifest: `evaluation/m4_20261127/rq3/RYIAD_NEUTRAL_REVIEW/NEUTRAL_CASE_MANIFEST.csv`.
- Frozen semantic/validation mutation manifest: `evaluation/m4_20261127/rq3/MUTATION_MANIFEST.csv`.
- Protocol and settings: `evaluation/m4_20261127/rq3/MUTATION_PROTOCOL.md`, `EXPERIMENT_CONFIG.md`, `GOLD_LABELS_AND_REVIEW.md`, and `RQ3_LIMITATIONS.md`.
- Full matched request schedule: `evaluation/m4_20261127/rq3/MATCHED_RUN_MANIFEST.csv`.
- Raw real Qwen run: `evaluation/m4_20261127/rq3/experiment/real_run_20261122T142300Z/RQ3_RESPONSES.jsonl` and its `.meta.jsonl` sidecar.
- Saved scorer and outputs: `evaluation/m4_20261127/rq3/experiment/score.py` and `experiment/real_run_20261122T142300Z/scored_pr34_20261123/`.
- Additive blank intake: `E3_REVIEW_INTAKE_TEMPLATE.csv` and `E3_REVIEW_INTAKE.schema.json` in this folder.

## Package checks

- The semantic audit set contains 12 cases: 8 mutation cases and 4 clean controls, drawn from 2 parent source groups. The manifest separately contains 3 validation-stratum cases; they are not part of this 12-case semantic review intake.
- The neutral manifest has 12 unique opaque blind IDs. All 12 listed request files exist and match their recorded byte counts and SHA-256 digests. The current `REVIEW_FORM.csv` has 12 blank rows and no entered decisions.
- A marker scan found no expected-label, mutation-operator, or prediction fields in the neutral requests or schema. The only hits for “Qwen” and “scored” are in the instructions, which explicitly warn against accessing those materials before freezing the review.
- Opaque row IDs are not a technical blinding boundary. The neutral package folder contains no key or model outputs, but the repository around it contains developer-authored label/mutation material and scored outputs. The package instructions correctly require a separately access-controlled review-only copy for strict blinding. A reviewer with full-repository access can defeat blinding; the reviewer’s actual access/exposure remains to be attested.
- The two-parent composition includes a development-exposed real parent and a synthetic fixture parent; source-group independence is zero. Payload content may reveal context even when the row IDs are opaque. This audit does not claim the package is anonymous to a domain-informed reviewer.
- Prior exposure is disclosed in the existing protocol/package materials. Review independence is conditional on a completed per-reviewer exposure declaration and access history; no assertion of blindness is made here.

## Intake requirements

The new blank template is additive and does not replace or edit Ryiad’s existing package. It requests, for every blind case:

- explicit `present`, `absent`, or `indeterminate` assessment;
- affected object and verification status;
- affected GSN node and verification status;
- relevant target interval and verification status;
- evidence reference IDs and an evidence-based rationale;
- confidence on a 1–5 scale;
- prior-exposure declaration and details;
- scope/source issue, uncertainty, reviewer/date, and frozen submission timestamp.

The template has 12 IDs and contains no prefilled decisions. It is an intake proposal; use it only after the review owner accepts the format. Keep the original `REVIEW_FORM.csv` unchanged.

## Blinding and handling before review

Provide only the neutral requests, review instructions, and an agreed blank intake form through an access-controlled channel. Do not provide the mutation manifest, gold-label files, scorer outputs, response JSONL, per-case result tables, or this coordinator audit to the reviewer before the submission is frozen. Do not grant access to a full repository clone if strict blindness is required. If the reviewer has already seen labels or model outputs, record the exposure and do not characterize the assessment as blinded/independent.

No answer key is reproduced in this handoff. No expected-label mapping or per-case prediction has been generated or shared by this work.

## Reviewer-only distribution staging

A separate, non-repository staging bundle was prepared at the local owner-only path `/Users/nikta/.private-review-staging/rq3-e3-20261123/reviewer_package`. Its directories are mode `0700` and files mode `0600`. The bundle contains exactly 12 neutral case JSON files plus the review instructions, current blank form/schema, additive blank intake/schema, a read-me, and a distribution manifest (18 manifest-listed files). The separate pre-distribution exposure attestation is outside the bundle. The package and attestation remain local; nothing was uploaded or sent.

All 12 distributed case copies match their original neutral-manifest SHA-256 and byte counts. The bundle manifest verifies 18/18 listed files. The case-file and filename scan found no expected-label, mutation-operator, gold-label, prediction, or scored-result fields. The request files have an empty checker-assessment list and a common fixture marker; this does not encode per-case expected labels but discloses that these are benchmark review requests. The evidence payload retains domain/source context, so a knowledgeable reviewer could infer some case provenance. The files should not be described as anonymous.

**Distribution gate not yet met:** the external reviewer has not returned a signed exposure attestation. Do not provide the case bundle until that declaration is received and checked. A local owner-only directory is secure staging, not an access-controlled reviewer delivery service. Once eligibility is established, transfer only the bundle through an organization-approved, individually restricted channel; verify recipient access and the manifest digest, and do not share repository links or grant repository access. If the reviewer previously saw labels, mutation mappings, or model outputs, record that and do not characterize the review as strictly blinded. Any full-repository access must be disclosed; repository permissions are not a blinding control.

The private distribution manifest SHA-256 at staging time is `df7351129f19572761e0b07ed2e5bc94fabd7fcf0ee19e8320359a168467fde0`. It is intentionally not committed because the bundle is nonpublic.

## Post-submission reconciliation

1. Receive and freeze the reviewer’s completed file without editing it. Record reviewer identity, declared exposure, received timestamp, and SHA-256. Validate exactly one row per blind ID, required fields, allowed assessments, and evidence/target fields. Return omissions for completion without suggesting labels.
2. Only after the submission is frozen, an authorized coordinator may access the developer-authored reference labels and the protected crosswalk. Keep the reviewer file and original developer files immutable.
3. Make an explicit disagreement ledger with one row per disagreement: blind ID, both original assessments, reviewer rationale/evidence, developer rationale/evidence, adjudicator identity, date, process, outcome, and unresolved status. Preserve original judgments even if adjudication resolves a disagreement. Do not use model predictions to decide the reference label.
4. If adjudication is not authorized or incomplete, report the disagreement as unresolved. Report any human-review result only with the actual review provenance, exposure limitations, and the 2-parent / 0-independent-source-group limitation.

Until a genuine authorized review and its exposure/provenance checks are complete, independent mutation-label findings remain **pending**. No human label, adjudication, accuracy estimate, or independent validation is created by this readiness work.
