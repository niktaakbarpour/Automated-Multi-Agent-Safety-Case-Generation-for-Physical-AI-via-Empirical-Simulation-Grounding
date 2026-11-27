# E3 distribution readiness and release gate

**Package status: staged, not distributed.** No reviewer submission or exposure declaration has been received. No labels, predictions, or judgments were created or changed.

## Private staging and contents

The nonpublic bundle is staged outside the repository at `/Users/nikta/.private-review-staging/rq3-e3-20261123/reviewer_package` with owner-only filesystem permissions (directories `0700`, files `0600`). Its manifest lists 18 files:

- exactly 12 neutral request JSONs under `cases/` (R01–R12);
- neutral review instructions and a package read-me;
- the existing blank review form and schema;
- the additive blank intake form and schema;
- `DISTRIBUTION_MANIFEST.csv`, listing each other reviewer-visible file’s relative path, size, digest, and role.

The 12 cases are exact byte copies of their neutral-manifest sources: all 12 byte counts and SHA-256 hashes match. All 18 manifest-listed files passed package hash/size verification. The manifest SHA-256 at preparation was `df7351129f19572761e0b07ed2e5bc94fabd7fcf0ee19e8320359a168467fde0`.

## Content and leakage checks

Checked filenames and structured request fields for developer case identifiers, expected-label/mutation-operator/gold-label/prediction/scored-result keys. No such keys or filenames were found. `checker_assessments` is empty in each request. The generic fixture marker is the same in all 12 cases, so it does not distinguish the target classification, but it discloses benchmark-fixture status. Evidence text itself necessarily contains task/source context; an expert may infer provenance. The IDs are opaque, not a guarantee of anonymity. No answer key, mutation manifest, scorer output, model response, or prediction is packaged.

The package instructions warn that the repository contains answer-key and result material. The reviewer must not receive a repository clone/link. This local staging directory is restricted to the current account and is not a substitute for an approved reviewer delivery system with named-recipient access controls.

## Required pre-distribution exposure gate

The blank `PRE_DISTRIBUTION_EXPOSURE_ATTESTATION.csv` is staged outside the package at `/Users/nikta/.private-review-staging/rq3-e3-20261123/PRE_DISTRIBUTION_EXPOSURE_ATTESTATION.csv`. It asks the reviewer to declare prior access to developer labels, model outputs/predictions, mutation mapping, full repository, and other exposures. It must be completed and signed before the reviewer receives any case files.

If the reviewer reports seeing labels, predictions, or the mutation mapping, do not describe the resulting assessment as strictly blinded. Record the exposure scope and date, consult the study owner on whether review remains useful, and preserve that limitation. If the reviewer has full-repository access, remove that access or obtain a clear no-access/no-consultation attestation before delivery; do not assume repository controls provide blinding. No cases have been transferred while this declaration is blank.

After eligibility is confirmed, release only the manifest-listed bundle through an individually restricted, approved channel. Verify recipient access and the manifest digest after transfer. Do not post the bundle in the repository, a public link, or a broadly accessible drive.

## Submission freeze

The reviewer completes the agreed form independently and returns it with a dated/frozen timestamp. The coordinator must preserve the received bytes, record receipt and reviewer exposure metadata, calculate a SHA-256 digest, and validate one complete row for each of the 12 blind IDs before accessing or comparing developer labels or any model results. Keep the review submission confidential and outside Git. Only after this freeze may an authorized coordinator make a separate disagreement/adjudication ledger; retain both original judgments and provenance, and do not use model predictions as ground truth.

The actual review remains pending. This package alone cannot support a claim of independent validation; source evidence comes from two parent groups and zero independent groups.
