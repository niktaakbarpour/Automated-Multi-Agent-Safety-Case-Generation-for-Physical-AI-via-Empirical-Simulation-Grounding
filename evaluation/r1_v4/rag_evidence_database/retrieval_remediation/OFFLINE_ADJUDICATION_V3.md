# Offline saved-response adjudication v3

 evaluate_replay_v3.py is a separately versioned, offline evaluator for saved
planner-v2 actual-retrieval records. It never invokes the planner or retriever,
and refuses to overwrite a nonempty output directory. Its result is distinct
from the original v2 evaluator report and from any new retrieval execution.

## Corrections

- A claimed-complete response is not called false merely because a frozen
  reference does not cover every requested family. It is claimed_complete_unverifiable
  unless source-backed family checks establish it.
- Exact frozen-reference path/hash matches are accepted. A source outside that
  list is accepted only through an explicit family validator, such as a
  catalogue-bound execution metadata path/hash or the catalogue main-table
  audit and mapping chain. No generic alternative-source fallback exists.
- Metadata uses typed validators for raw channels, recorded time, action
  metadata, inference metadata, geometry identity, main-table identity,
  execution metadata, source provenance, camera references, and contact
  references. Unknown reference schemas remain unverifiable.
- A scalar recorded-time reference is matched to its corresponding frame. Other
  returned frames are checked against their own HDF5 selectors and clock fields,
  not compared to that one scalar.
- A request with an unsupported component that was deliberately not executed
  is evaluated as an abstention; absent samples are not counted as retrieved
  evidence missing from a response that was never run.
- Rows requiring source-fault injection are marked evaluation_unavailable
  when the saved replay manifest shows the planner-v2 harness ran without those
  fixtures. The original actual-retrieval result is retained.

## Assessments

Each row receives one assessment plus overlapping diagnostics:

- correct_and_verified_complete
- confirmed_false_complete
- claimed_complete_unverifiable
- verified_incomplete
- correct_abstention
- incorrect_abstention
- evaluation_unavailable
- unresolved_discrepancy

The output includes CASE_CLASSIFICATIONS.jsonl, AGGREGATE.json, and a
PROVENANCE_MANIFEST.json. The manifest binds the evaluator source, correction
checkout, preserved replay manifests and aggregate hashes, frozen references,
catalogue, and pinned database SHA-256. Before evaluation it verifies each
saved record canonical hash and each run aggregate hash.

## Reproduce the offline evaluation

From the repository root, in Python 3.12 with the CPU dependencies installed:

    python evaluation/r1_v4/rag_evidence_database/retrieval_remediation/evaluate_replay_v3.py \
      --references evaluation/r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl \
      --responses /path/to/preserved-216-case-output \
      --three-case-responses /path/to/preserved-three-case-output \
      --catalogue /disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite \
      --source-root /disk/1/data/niktakbr \
      --database-sha256 f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8 \
      --output /path/to/new-offline-evaluation-directory

This command only reads source files and saved retrieval outputs. The exposed
216-row cohort remains development data, not independent evaluation.
