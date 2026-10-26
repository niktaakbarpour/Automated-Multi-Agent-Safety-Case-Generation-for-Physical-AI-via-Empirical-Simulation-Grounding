# Reproduction

The actual approval is recorded in approval_metadata.json and approval_ledger.csv. Preserve those bytes: changing identity, date, reason, or label changes the content-addressed version. The immutable AI proposal and private bridge checksums must match the approved hashes. Authorized private evidence is required for evidence-gated freezing; public files alone cannot replace it.

From repository root (replace PUBLIC_VERSION with this directory):

```sh
python3 human_review_package/adjudication/ai_tools/freeze_approved.py build --package human_review_package --proposal human_review_package/adjudication/ai_assisted_20261026 --private-proposal human_review_package/adjudication/ai_private_20261026 --ledger PUBLIC_VERSION/approval_ledger.csv --approval-metadata PUBLIC_VERSION/approval_metadata.json --output-root human_review_package/adjudication/versioned-reference --publication-root human_review_package/adjudication/approved_reference
python3 human_review_package/adjudication/ai_tools/freeze_approved.py verify --package human_review_package --publication PUBLIC_VERSION
```

Identical inputs and script hashes reproduce identical files. The existing core finalizer verifies original sources, evidence and all approval bindings before exporting; the companion builder preserves its four finalized CSV bytes exactly. Re-execution rejects changes to an existing version. The public manifest records all workflow script hashes, recording hashes, original-review hashes, scope version/hash, private manifest hash and approved proposal checksums. Development environment: Python standard library; no model inference or simulator replay. Check repository commit containing this version for the complete implementation.
