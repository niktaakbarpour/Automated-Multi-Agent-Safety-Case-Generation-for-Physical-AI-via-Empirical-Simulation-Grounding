# Reproduce and resume on Hestia

All computation runs from /disk/1/data/niktakbr/trustworthy-phase16, with PYTHONDONTWRITEBYTECODE=1 and TMPDIR=/disk/1/data/niktakbr. Reuse existing packages; install nothing:

```
export PYTHONPATH=.:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages
python3 -S -m evaluation.r1_v4.rag_evidence_database.expansion /disk/1/data/niktakbr/NEW-EXPANDED.sqlite
python3 -S -m evaluation.r1_v4.rag_evidence_database.expansion /disk/1/data/niktakbr/NEW-EXPANDED.sqlite
python3 -S -m evaluation.r1_v4.rag_evidence_database integrity /disk/1/data/niktakbr/NEW-EXPANDED.sqlite
python3 -S -m evaluation.r1_v4.rag_evidence_database query /disk/1/data/niktakbr/NEW-EXPANDED.sqlite QUERY.json
```

The expansion CLI creates a new baseline copy or resumes that copy, verifying the exact immutable baseline hash first. It never writes to the original baseline. It appends only the new 36 input digests, retaining all 1,360 old IDs and job bindings. Unit schema 1.0.0, requirement 2.0.0 and database extension 1.1.0 remain compatible. The only added physical SQLite structure is a conflict-expression performance index. Window size 32 is an index choice, not a physical threshold. CLI address-space limit is 4 GiB.

Use query objects from the committed validation fixtures. Normal query and integrity commands open read-only; no graph generation or checker invocation occurs. Catalog entries remain historical Phase 5B snapshots; current raw indexing coverage is in EXPANDED_CORPUS_MANIFEST.json and rag_jobs. Do not interpret historical catalog eligibility/status fields as the current job state.

Tests: `python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/expansion/tests -v`. Expanded integration expects the documented production database, or RAG_EXPANSION_DB. For Phase 5B tests set RAG_TEST_DB to the immutable Phase 5B database. The validation driver records its exact subprocess commands/log hashes. Completed driver outputs are not overwritten; change its output directory before a new full run.

Do not rerun restoration into existing files. Receiver exclusive creation refuses overwrites. A future interrupted restoration must select only absent members and independently verify existing complete files; no cleanup/deletion is authorized. Full restoration/profile reports remain committed, raw files stay outside Git.

Production: /disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite. Full build, retrieval and validation logs are under that working directory. The independent reproduction database is validation/reproduced.sqlite. Protected originals, raw recordings, large database files and arrays are not committed. No push or merge is performed.
