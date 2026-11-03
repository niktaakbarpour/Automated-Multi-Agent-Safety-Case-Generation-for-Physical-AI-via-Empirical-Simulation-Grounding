# Automated replay

All computation ran on Hestia. No Alliance compute, Sea NFS, new simulations, global dependency changes, full source copies or new database. RESOURCE_PREFLIGHT.json budgeted 2 GiB disk and 3 GiB/process; sources remain external. HF/XDG caches use the new owned working directory.

Baseline commit: c46d768263b3499e0f89d7c7b3369c17d131cc3d. Database: /disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite; SHA256 f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8. FROZEN_EVALUATION_CONFIGURATION.json pins implementation files, model, sidecar, package versions, ranking, filters, top-k and preprocessing. Phase 5I's manifest anchors selected dependency bytes; versions alone are not binary attestation. verification_mode describes the modern route; legacy retains its frozen hash-based guard, audited separately.

On Hestia, from repository root with python3 -S and the recorded explicit PYTHONPATH:

```sh
python3 -S -m evaluation.r1_v4.rag_evidence_database.readiness_evaluation.run --split final --run operator_replay
```

RUN_REPLAY.sh supplies the exact environment and validates a simple run label. A new run name starts a fresh pass; the same name validates/resumes case files. Frozen database, code, dataset, criteria, model and sidecar identities are checked before execution. No fallback, rewriting, query decomposition or hybrid ranking is inserted.

REPLAY_VALIDATION.json records two full automated final passes, full resume with 486 cached cases and partial resume with 37 seeded files / 449 new evaluations. All 486 canonical outputs agree. Only scratch diagnostic hash/path differences are excluded, never values, ranks, identities, statuses or rubric findings. This is same-host automated replication, not independent human/cross-platform replication.

METRICS.json uses fixed denominators and frozen metrics.py, including reproducible 2,000-replicate cluster intervals. Pre-final reference/harness revisions and development artifacts are retained. Final wording/criteria were not changed after final outputs. All 718 inherited regressions and seven evaluator checks passed. Baseline/frozen identities are verified again before local commit.
