# Reproduction and migration

All computation on Hestia, cwd `/disk/1/data/niktakbr/trustworthy-phase16`, HOME=/tmp, PATH=/usr/sbin:/usr/bin:/sbin:/bin, PYTHONDONTWRITEBYTECODE=1. Use `/usr/bin/python3 -S` with PYTHONPATH containing repository, existing `/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages`, `/usr/lib/python3.12/site-packages` and `/usr/lib64/python3.12/site-packages`. No installs. Local encoder uses its existing pinned model and CPU. No Alliance computation, transfers or Sea access.

Baseline is commit c24795ed9383110243288db520e5f98af484b4ad, database `/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite`, SHA-256 `a0f9347db719902f275d0f3e89f0682f093d5ded858ab7c2823067930337baa9`. All sources are existing validated bindings. Legacy `/local/home/niktakbr` assets are verified by device/inode against owned disk0 aliases. Baseline code, data and Phase 5E/5F reports remain unchanged.

Migration is additive and copy-only. `populate(new_path)` backs up Phase 5F through SQLite, creates `rag_channel_schema`, records, transactional jobs and FTS tables, and checks frozen schema/selection hashes. Core/variant migrations are unchanged. New extraction/schema version is phase5g-channel-1.0.0. VariantQuery and its semantic sidecar remain separate; ChannelQuery addresses the new series family.

Rebuild with a new owned work path:

```python
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.build import populate
result = populate(Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/reproduce-fresh.sqlite'))
```

Repeat on the same path for resume. Producers, contracts, source hashes and selection must remain unchanged; changed input/producer aborts. Expected channel logical digest: `71ce910b45a3b9e0b173eb2cec5daa1b921bdd2cabbdf46a39bad37ed4903c6e`. Independent rebuild equals it. Complete resume inserts zero/skips 432; partial scratch resume inserts six/skips 431 and restores the digest. Physical SQLite hashes can differ after scratch reconstruction; final hashes are in ARTIFACT_MANIFEST.json.

`validate.py` independently decodes every selected sample. `verification_run.py` describes fresh complete validation; `post_rebuild_validation.py` completed retained diagnostic recovery without duplicating successful rebuilds. Reports are create-only; repeat evaluations require fresh output directories. Inventory enumerates only baseline executions and freezes selection before extraction. Per-execution inventories and supplements retain all decoded key/coverage profiles.

For queries: `python3 -S -m evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.cli --database <db> --query <json>`; optional `--semantic-text` uses the pinned local encoder. Require execution_id; optional channel_id and inclusive interval such as `[0,0]`. Metadata-only queries return references without arrays. Existing Phase 5F CLI remains available.

External artifacts: `/disk/1/data/niktakbr/trustworthy-phase5g-working`. Manifest binds reports/code, current databases/sidecar, validation results, inventory/source bindings and diagnostics. ARTIFACT_MANIFEST.sha256 hashes the manifest; both are excluded from its file list to avoid recursion. Local Git commit seals tracked content. Nothing is pushed or merged.
