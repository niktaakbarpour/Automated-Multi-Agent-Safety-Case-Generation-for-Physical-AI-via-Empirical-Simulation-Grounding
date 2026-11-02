# Reproduction and additive migration

All processing on Hestia; cwd /disk/1/data/niktakbr/trustworthy-phase16, HOME=/tmp, system PATH, PYTHONDONTWRITEBYTECODE=1. Use `/usr/bin/python3 -S`, PYTHONPATH repository + existing groot-n17-libero-gpu0-queue .venv Python3.12 site-packages + system site-packages. Compilation/velocity checks instead use smolVLA_libero .venv (MuJoCo3.8.1), OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1. No installs, GPU jobs, Sea, Alliance evaluation or source-corpus copies.

Baseline commit a6830ad25f2f3d25ad9a28322985e128e5ab1374, DB `/disk/1/data/niktakbr/trustworthy-phase5g-working/expanded.sqlite`, SHA `d1241f28089ff910baf8ec276fbaa3f9d2b71aa3c7b850fe494b976eb51320fb`. Before edits, check_release verified 585 entries and all 578 tests reran. Compilation checks all recorded indexes without stepping. Upstream 3.8.1 downloads are small pinned primary-code references, not recording restoration.

Frozen producers include config/schema/semantics/source-integrity/store/builder/contracts hashes. Frozen audits, model maps and velocity/source proofs are reused for deterministic rebuilds; changed sources/producers reject mixed resume. Version physical-semantics-1.0.0. Old schemas/rows are unchanged. Added h_meta, h_models, h_execution, h_semantics and h_jobs store interpretation/timeline metadata only; no large HDF5 arrays.

Fresh rebuild:

```python
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.build import populate
populate(Path('/disk/1/data/niktakbr/trustworthy-phase5h-working/reproduce.sqlite'))
```

Repeat for full resume: zero inserts/432 skips. Independent logical digest `3f45c16c163b6f03d314e1282ee0dac89323e8bf546c5099d0f29253065820b8` matches. Partial scratch recovery restores six annotations and skips 431 executions with the same digest. Physical SQLite hashes can differ after transaction reconstruction; manifest has current exact hashes.

Research modules: compile_models; fetch_primary; audit; velocity_validation (kinematic mass/algebra only); temporal_refinement; build; validate; binding_validation; velocity_by_channel; rebuild; semantic_benchmark; legacy_benchmarks f/g; regressions; final_audit; reports; seal_artifacts. Persistent stdout/stderr, exact suite commands and machine results are retained. Reports are create-only; repeated evaluations require fresh directories. Absolute baseline/profile paths intentionally prohibit other cohorts.

Verified query:

```
python3 -S -m evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.cli --database /disk/1/data/niktakbr/trustworthy-phase5h-working/expanded.sqlite --database-sha256 af8265755a8f4f1a360c6b39b99bf6ccd45a7313d9e6adf33b89acff7b67fb02 --query query.json
```

Require execution_id; use exact channel_id for typed filters, optional component/units/frame/property conditions and inclusive saved-frame interval such as [0,0]. Default strict mode hashes both boundaries. verified_session explicitly caches verified identities only. Conditional requests need allow_conditional=true. No unverified mode. Optional --semantic-text uses the pinned local CPU encoder; guards cannot be bypassed by ranking.

Code/reports/compact summaries are committed. DBs, detailed audits, model maps and logs remain outside Git in `/disk/1/data/niktakbr/trustworthy-phase5h-working`. Manifest excludes itself/checksum; ARTIFACT_MANIFEST.sha256 and local Git commit identify the root. Nothing pushed or merged.
