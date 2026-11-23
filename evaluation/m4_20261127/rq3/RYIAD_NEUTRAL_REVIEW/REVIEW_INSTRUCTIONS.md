# Neutral RQ3 case review instructions

Review the 12 cases R01-R12 independently using the Critic request JSONs in cases/. These files omit expected mutation labels and evaluation results. The case IDs are opaque. Do not infer the intended label from a filename, order, or prior Qwen response.

For each case, review the argument, requirement context, evidence actually included in the request, source references, and scope. Record your own observations in REVIEW_FORM.csv:
- whether a defect is present, absent, or indeterminate;
- affected object and GSN node;
- defect description in your own words;
- whether cited/source evidence supports the proposed safety statement or objection;
- any evidence-link, scope, or unsupported-guarantee issue;
- uncertainty, alternatives, and reviewer exposure declaration.

Do not access, search for, or run the mutation manifest, gold labels, scorer outputs, or the saved real-response/results directories before your form is completed, dated, and frozen. Do not change a judgment to match a later key. If you have previously seen any expected-label or result artifact, mark prior exposure and do not represent the review as blinded or independent.

## Repository-level exposure limitation

The main repository already contains answer-key-bearing benchmark and scored-result files outside this neutral folder. This folder has no access-control boundary against the rest of the repository. A reviewer who clones the full repository can technically open those files. Independence therefore depends on a documented non-exposure attestation; if strict technical blinding is required, the coordinator must provide a separately access-controlled review-only copy before review.

The neutral folder contains no answer key, mutation-type labels, human judgments, or model results. It is a development benchmark and includes only two parent groups (one real development-exposed group and one synthetic fixture); it cannot support claims about independent physical-parent generalization.
