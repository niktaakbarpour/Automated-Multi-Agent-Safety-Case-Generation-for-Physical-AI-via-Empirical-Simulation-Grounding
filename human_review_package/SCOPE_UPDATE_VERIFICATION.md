# Scope update verification — 2026-10-24

This records package-integrity checks for the selected R1 scope. It supplies no human labels, approvals, or detector validation. The earlier [export verification](VERIFICATION.md), evidence manifest and export provenance are unchanged historical records.

- Four scope/form contract tests passed: the selected package contract; rejection of completed-review/validated-detector or numerical-approval claims; rejection of false origin/missing scope decisions; rejection of prefilled human judgments.
- All six repository/package JSON Schema definitions passed Draft 2020-12 schema checks. The selected scope record passed its schema and exact decision/provenance consistency checks.
- All package JSON and CSV files parse. Both reviewer copies retain the same twenty object/run prompts for initial support, events and requirement interpretation, plus four uncertainty-request prompts. Human judgments and identities remain blank. Adjudication remains header-only.
- All 533 relative Markdown/CSV evidence links resolved both in the working package and an independently copied folder, including this report.
- All 143 pre-existing package files not intentionally edited matched their original SHA-256 checksums. This includes every video, image, supporting measurement, evidence manifest and export provenance file. Historical text/template snapshots match their original Git bytes.
- Current SHA256SUMS.txt covers the updated deliverable; the original manifest is preserved byte-for-byte in history/20261023-v1/SHA256SUMS.txt.txt and applies to the original Git revision. No historical manifest was rewritten.
- The existing neutral-package allowlist checks pass. No detector outputs, predictions or episode-specific suggested judgments were added to the neutral materials. The examples are generic hypotheticals only.
- No source recording, held-out data, checker, LLM pilot, model or robot experiment was run. Media were checked for byte identity, not decoded again. No numerical detector limits were changed or endorsed.

Commands (temporary validation environment has jsonschema; reviewers do not need Python):

```sh
python human_review_package/tools/verify_package.py human_review_package --metadata-only
python human_review_package/tools/verify_scope_update.py human_review_package
python -m unittest discover -s tests -p test_human_review_scope.py -v
```

Measurement/support-chain evidence, carrying versus incidental contact, re-placement/subsequent support transitions, sampling alignment/coverage, and checker parameter/performance validation remain open as stated in the [shared decision](REQUIREMENT_SCOPE_DECISION.md).
