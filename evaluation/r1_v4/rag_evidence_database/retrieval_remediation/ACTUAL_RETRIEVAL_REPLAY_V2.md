# Actual retrieval replay: requested-obligations planner v2

`run_eval_v2.py` is a new, resumable actual-retrieval harness. It is separate
from frozen `run_eval.py` and does not read historical response rows as if they
were new retrieval executions. The 216-row reference corpus is exposed
development data, not an independent holdout. All results set physical
evidence eligibility to `NOT_EVALUATED`.

## What is bound and recorded

Before opening the retrieval database, the runner verifies the supplied SHA-256
for the database, catalogue, encoder artifact, and reference dataset. The
declared source root must contain all source paths referenced by the selected
reference rows. The run manifest binds those hashes, selected case IDs,
encoder revision, planner/retriever choice, source commit and component hashes.
Bundle mode uses the explicit `RequestedObligationsRetriever`; it does not load
or call the encoder, but requires the encoder artifact and revision to be
identified so the run inputs remain explicit and reproducible.

Each attempted query gets an atomic `case-<ID>.json` record. The response,
interpretation, obligations, citations, scope/value checks, latency, errors,
and separate planner/retrieval completeness statuses are retained. Aggregate
and failure-analysis files are refreshed as cases finish. A process lock
prevents simultaneous writers. Resumption skips only complete case records
whose input binding matches the current manifest; configuration or artifact
changes are rejected. Do not reuse an output directory for a different run.

## CPU tests (synthetic fixtures only)

From the repository root, with the approved Python 3.12 CPU environment:

```sh
PYTHONPATH=. python -m unittest \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_run_eval_v2 \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_requested_obligations_v2 \
  evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_bundle_v2_contract -v
```

These use synthetic inputs and fake retriever responses. They do not constitute
empirical retrieval results. The same harness test is run by the M4 CPU CI
workflow.

## Hestia replay command

First verify access to all original input files and their hashes, and choose a
new output directory on an authorized filesystem with enough available quota.
Do not copy or rebuild the database to work around access problems. The
previously pinned inputs are:

| Input | Path | SHA-256 / identity |
|---|---|---|
| SQLite evidence database | `/disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite` | `f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8` |
| Catalogue snapshot | `/disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite` | `ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e` |
| Encoder artifact | `/disk/1/data/niktakbr/trustworthy-phase5e-working/encoder/model.safetensors` | `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db` |
| Encoder revision | — | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Frozen development references | `evaluation/r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl` | `f6c6e31e12d3c0ed7e70db077494a4bed98f1d0a56d82f382c556c13b00c6caf` |
| Declared source root | `/disk/1/data/niktakbr` | Must contain all paths in the frozen references |

Run only after a separate read-only availability/hash preflight succeeds and
the quota/write destination is resolved. Use the existing Python 3.12
environment and a fresh output path:

```sh
cd /path/to/this/repository
OUT=/authorized/new/path/rq1-retrieval-v2-temporal-cases
PYTHONPATH=. python -m evaluation.r1_v4.rag_evidence_database.retrieval_remediation.run_eval_v2 \
  --database /disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite \
  --database-sha256 f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8 \
  --catalogue /disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite \
  --catalogue-sha256 ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e \
  --source-root /disk/1/data/niktakbr \
  --encoder /disk/1/data/niktakbr/trustworthy-phase5e-working/encoder/model.safetensors \
  --encoder-sha256 53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db \
  --encoder-revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 \
  --references evaluation/r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl \
  --references-sha256 f6c6e31e12d3c0ed7e70db077494a4bed98f1d0a56d82f382c556c13b00c6caf \
  --output "$OUT" \
  --case-id KH2-C2-02 --case-id KH2-C2-10 --case-id KH2-C2-18
```

After reviewing the three case-level outputs and verifying no new access or
integrity issue, the full exposed development cohort uses the same command
without the three `--case-id` arguments and with a distinct fresh output path.
The reference corpus contains 216 unique cases. A full run records every row,
including planner ambiguity/unsupported outcomes and retrieval errors.

Generated files are `case-<ID>.json`, `PER_CASE.json`, `AGGREGATE.json`,
`FAILURE_ANALYSIS.csv`, and `PROVENANCE_MANIFEST.json`. Retrieval completeness
is about evidence-family retrieval and reference checks only. It is not
physical evidence eligibility, a safety conclusion, or independent evaluation.

## Current replay status

Actual retrieval is **NO-GO** pending recovery of read access to the pinned
inputs and a verified writable output location. The read-only Hestia check
reported `/disk/1` XFS mounted with `noquota`, 2.1 TB free, and over 1.49 billion
free inodes; the `quota` utility itself returned `Disk quota exceeded` on both
queries. No files, quota settings, or processes were changed. Do not infer that
inputs are available from `df`; re-verify every required hash before replay.
