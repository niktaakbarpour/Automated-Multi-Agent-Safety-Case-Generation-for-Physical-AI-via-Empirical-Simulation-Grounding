# Reproduce on Hestia

Worktree: `/disk/1/data/niktakbr/trustworthy-phase16`. Use existing approved packages; install nothing. Set PYTHONDONTWRITEBYTECODE=1 and TMPDIR=/disk/1/data/niktakbr, then:

```
export PYTHONPATH=.:/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages:/usr/lib/python3.12/site-packages:/usr/lib64/python3.12/site-packages
python3 -S -m evaluation.r1_v4.rag_evidence_database build /disk/1/data/niktakbr/NEW-DATABASE.sqlite
python3 -S -m evaluation.r1_v4.rag_evidence_database build /disk/1/data/niktakbr/NEW-DATABASE.sqlite
python3 -S -m evaluation.r1_v4.rag_evidence_database integrity /disk/1/data/niktakbr/NEW-DATABASE.sqlite
python3 -S -m evaluation.r1_v4.rag_evidence_database query /disk/1/data/niktakbr/NEW-DATABASE.sqlite QUERY.json
python3 -S -m evaluation.r1_v4.rag_evidence_database catalog /disk/1/data/niktakbr/NEW-DATABASE.sqlite --text 'alphabet soup'
```

Use the `query` object of any committed QUERY_FIXTURES entry as QUERY.json. Database sources and outputs remain on Hestia. Query prints compact references, not raw arrays or images. The builder creates a new database or idempotently resumes it; it never deletes or overwrites a source. CLI supports `export` (canonical evidence metadata) and explicit additive `migrate`. Do not migrate the preserved Phase 5A production database; use a new copy to exercise migration.

All four approved development episodes must be available at the restored source root. No substitution is allowed. Source errors fail the current job with failure logging. One committed transaction is the resume unit. Different source/policy bindings create new evidence revisions; queries select current jobs. Logical build IDs and canonical exports must reproduce; physical SQLite bytes and elapsed timings need not.

```
RAG_TEST_DB=/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/tests -v
```

Without RAG_TEST_DB, real integration tests create and clean an isolated temporary database under owned /disk/1. All such fixtures are synthetic except the explicitly named four production development executions. Full validation driver: `validate.main('/disk/1/data/niktakbr/NEW-VALIDATION-DIRECTORY')`; output directory must not exist. It builds two databases, rechecks resume, executes known-target queries and regressions, and verifies source/frozen integrity.

Production database: `/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite`. Reproduction database: sibling `reproduced.sqlite`. Test logs and full build reports: the same validated directory. Compact reports, code, inventories and hashes: this package. No database or raw evidence is committed.
