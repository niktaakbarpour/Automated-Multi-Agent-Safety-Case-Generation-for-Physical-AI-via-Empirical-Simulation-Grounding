# Reproducing the Phase 5E database release

Run research commands only on Hestia, in
`/disk/1/data/niktakbr/trustworthy-phase16`. Generated data belongs under
`/disk/1/data/niktakbr/trustworthy-phase5e-working`; restored originals belong
under `/disk/1/data/niktakbr/r1-v4-phase5e-evidence`. Preserve all prior releases.
Use the existing Python 3.12 environment documented by the validation logs.
The h5py/torch/transformers environment is
`/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages`.
Model compilation additionally uses the existing MuJoCo environment at
`/disk/0/home/niktakbr/smolVLA_libero/.venv/lib/python3.12/site-packages`.
These paths are read-only dependencies; no new large data is written to disk0.
Set PYTHONDONTWRITEBYTECODE=1 and TMPDIR to an owned disk1 directory.

1. Verify the Phase5D baseline against build.BASE_SHA and the Phase5E artifact
   manifest. SOURCE_PLAN.json is the fixed selection and archive-member allowlist.
   The supplied receipt manifests describe actual transfers. Do not bulk restore
   other executions. Transport uses native archive retrieval on Alliance only.
   Exact member names can be passed on stdin to avoid SSH argument-length limits.
   Receivers exclusively create new files; they never overwrite existing files.
   An interrupted partial destination must be quarantined as a task-owned failed
   transfer and handled explicitly, never treated as verified evidence.
2. If restoration is needed, generate the exact pilot list with transport.py,
   transfer it through the approved SSH aliases, verify the pilot against the
   finalized profile, then restore the missing batch. pilots.py is the original
   create-only bootstrap, not a command to overwrite finalized profile files.
   For an existing profile, reader.read with the documented task_profile checks
   the restored pilot; recompile --report NEW_PATH independently reproduces its
   complete native mapping without modifying the committed profile. Existing source files must be freshly size/hash
   checked before resuming. Task profiles must pass independently. The actual
   run's TRANSFER_RESUME.json records its command-length failure and recovery.
3. Run `python3 -S -m evaluation.r1_v4.rag_evidence_database.multitask_expansion.activate`
   only after every expected source file is present. It verifies all hashes before
   final profile activation. Run the recompile module with --report NEW_PATH to independently reproduce
   all four mappings while preserving the original validation report. No physics execution occurs.
4. Use the CLI's build command with a **new** owned disk1 database path. It copies
   the immutable Phase5D baseline and appends the allowlisted executions. Repeating
   the build command resumes completed execution jobs without duplicating IDs.
   Do not change bound code or profile manifests during an index build.
5. The validate module creates a new validation directory, builds two independent
   databases, compares logical exports/build IDs, tests resume, checks all original
   source hashes, evaluates source-target queries and runs regressions. Its main
   function accepts an alternative new output directory for a fresh reproduction.
   Full-byte SQLite hashes can differ across independently built databases;
   logical content hashes are the reproducibility criterion, and each release has
   its own exact file SHA-256. Timing fields are not content identity.

The retrieval CLI accepts a JSON Query using the existing structured API:

```
python3 -S -m evaluation.r1_v4.rag_evidence_database.multitask_expansion.cli query \
  --database /disk/1/data/niktakbr/trustworthy-phase5e-working/final-validated/corpus-285.sqlite \
  --query /disk/1/data/niktakbr/query.json
```

Use QUERY_FIXTURES.json for exact tested source targets. Query fields include
execution_id, task_id (stable task configuration ID), object_id, evidence_types,
interval (inclusive saved-frame indices), stratum, capability restrictions and
optional literal FTS5 text. Missing intervals mean missing saved snapshots, not
an empirical negative or continuous coverage failure certificate.

Optional semantic commands use a separate sidecar and the locally downloaded,
pinned encoder. The core database must remain byte-identical during sidecar
construction. semantic-query takes metadata filters in --query and natural
language separately in --text. At most 100 valid metadata-filtered candidates
are allowed; broad queries fail explicitly. semantic-check verifies the sidecar's
source binding, descriptor identities, alias completeness and vector content.
The semantic index is not required for structured or FTS5 retrieval.

Do not commit database, encoder weights, recordings or videos. Do not push,
merge, run experiments, modify the R1 checker or implement downstream agents.
