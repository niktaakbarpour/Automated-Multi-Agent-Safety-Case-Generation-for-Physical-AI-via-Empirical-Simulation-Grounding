# Reproducing Phase5F on Hestia

All research commands run on Hestia in
`/disk/1/data/niktakbr/trustworthy-phase16`. Baseline commit:
114f1f6540a6ba182606a2a921af131ad6b0f7d3. Never alter Phase5E data or reports.
Set PYTHONDONTWRITEBYTECODE=1, TMPDIR to an owned disk1 directory, and PYTHONPATH
to the repository plus the existing h5py environment
`/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages`
and system Python3.12 site packages. Native compilation additionally uses the
existing MuJoCo3.8.1 environment
`/disk/0/home/niktakbr/smolVLA_libero/.venv/lib/python3.12/site-packages`.
The local encoder/model/version hashes remain in the Phase5E encoder manifest;
no hosted embedding API or new package installation is required.

1. Verify ARTIFACT_MANIFEST.json, the baseline DB SHA, COHORT.json and the external
   profile manifest. The cohort is frozen: three cheapest eligible multi-XML
   partitions, episodes1..49. The inventory is source identity metadata, not
   physical labels. Excluded IDs must remain excluded.
2. Source payloads are under
   `/disk/1/data/niktakbr/r1-v4-phase5f-evidence/`. If absent, use the exact
   COHORT archive/member list and transport.py/receive.py through approved storage
   SSH aliases. Pilot files precede batch restoration. Alliance executes native
   archive retrieval only; processing and hashing are on Hestia. Receivers create
   files exclusively and reject mismatches. Never overwrite originals or restore
   other executions. Existing complete files are verified and reused.
3. `validate_profiles pilot` and `validate_profiles batch` reproduce every exact
   source profile without stepping physics. Existing matching artifacts are
   compared, never overwritten; mismatches require diagnosis/new version.
   Profiles live under the Phase5F work directory, outside Git. Initial failure
   diagnostics are retained. Nested includes/unverified mappings remain blocked.
4. Frozen external maps and BASELINE_ENVIRONMENTS.json are reused for indexing.
   For a bootstrap on empty working storage, baseline.discover verifies the old
   native maps against actual XML/assets without rerunning old experiments;
   finalize_profiles freezes admitted IDs and external artifact hashes. Creation
   manifests are exclusive to avoid overwriting a previous release.
5. Build a new working database, never the baseline, using the public function:

```
python3 -S -c 'from pathlib import Path; from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.build import populate; print(populate(Path("/disk/1/data/niktakbr/trustworthy-phase5f-working/reproduce-fresh.sqlite"))["build_id"])'
```

Repeat the same command for resumed ingestion. All 147 completed new jobs must
skip without duplication and preserve the logical build ID. A second fresh path
must have the same core record/unit digests and variant-relation digest. Physical
SQLite hashes can differ without logical differences. Code/profile/source
bindings are frozen during each build. Do not change bound producers mid-build.

6. The saved rebuild, evaluate, negative_evaluate, semantic_evaluate and
   regressions modules provide exact validation procedures. Their default report
   paths are create-only; preserve existing reports and use a fresh test-output
   version when repeating a complete validation run. Per-source tests use original
   file hashes and selectors; source relevance is not physical ground truth.
7. Query the new interface with a JSON VariantQuery:

```
python3 -S -m evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.cli query --database /disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite --query /disk/1/data/niktakbr/query.json
```

Use execution_id plus optional task_id, variant_id, object_id, evidence_types,
field_name and inclusive saved-frame interval. Explicit comparative=true is
required to request multiple execution groups. Unsupported seconds/exposure
conversion is rejected. `variants` lists normalized associations; `check` checks
core sources and variant integrity.

8. Optional `semantic-query` additionally takes --sidecar and --text. It uses the
   same scope guard before the unchanged Phase5E local encoder/ranker. A sidecar
   is bound to the exact source DB bytes and must be regenerated for a different
   release. Descriptors are source-field metadata only; no physical judgments.

Keep recordings, model weights, generated databases and large geometry maps
outside Git. Commit only code and compact manifests/reports. Do not push, merge,
run simulations or begin downstream safety-case generation.
