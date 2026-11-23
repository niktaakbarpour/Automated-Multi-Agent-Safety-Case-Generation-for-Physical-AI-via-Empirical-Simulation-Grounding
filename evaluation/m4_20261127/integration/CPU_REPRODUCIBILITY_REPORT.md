# CPU reproducibility record

## Environment

After commit `74578f186d6e1a3e506cf052bd2435aa19d25763`, a clean detached worktree and a new Python 3.12.14 virtual environment were created. The detached worktree shares Git objects with the main checkout but has a fresh checkout of the committed tree. The README setup command installed the declared dependencies there:

```sh
python -m pip install -r requirements.txt -r drafter/requirements.txt -r critic/requirements.txt -r evaluation/r1_v4/requirements.txt
```

The full suite and RQ3 byte comparisons below ran at commit `74578f186d6e1a3e506cf052bd2435aa19d25763`. Final commit `713b2221d340282f07e57decf42a4ee79badf968` changes only this report; at that SHA, both saved-result verifiers and `git diff --check` were rerun from the detached checkout. All checks were CPU-only. No inference, simulation, source-recovery or private RQ2 review access occurred. System Python 3.14 lacked h5py; use the documented environment rather than assuming system packages.

## Verified commands

| Command | Outcome |
|---|---|
| `python -m unittest discover -s drafter/tests -t . -v` | PASS, 209 tests |
| `python -m unittest discover -s critic/tests -t . -v` | PASS, 210 tests |
| `python -m unittest integration.tests.test_handoff -v` | PASS, 9 tests |
| `python -m unittest discover -s drafter/revision/tests -t . -q` | PASS, 102 tests; saved example checker also passed |
| `python -m drafter.revision.tools.check_examples` | PASS, all emitted checks |
| `python -m unittest evaluation.m4_20261127.rq3.tests.test_experiment evaluation.m4_20261127.rq3.tests.test_mutations -v` | PASS, 26 tests; internal simulated runner replies are explicitly scripted |
| `python -m unittest evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_bundle evaluation.r1_v4.rag_evidence_database.retrieval_remediation.tests.test_integrity -q` | PASS, 39 tests |
| `python integration/verify_saved_fixture.py` | PASS: 8 manifest file sizes and SHA-256 values; current request/report schemas and Critic checks; no model calls |
| `python integration/verify_saved_results.py` | PASS: RQ2 CSV/JSON and row-level summary counts agree |
| RQ3 scorer and table generator to a new temporary directory, then three `diff -u` checks | PASS: per-case CSV, summary CSV and table match frozen outputs |
| `git diff --check` | PASS after documentation edits |

The attempted `unittest discover -s` form for the RQ3 and RQ1 remediation directories failed because those directories lack package initializers. No tests ran under those commands. The successful module-based invocations above were used instead.

## Saved outputs and boundary

RQ3 scoring was rerun from the committed 108-request batch and saved response archive into a new temporary directory. The two CSVs matched `scored_pr34_20261123/` byte-for-byte. The table generator was missing the saved caveat about full-case citation screening, pending independent label review, development-only groups and C status-only semantics. A minimal fix in `experiment/make_tables.py` restores that caveat; the regenerated table then matched the versioned table. No frozen response or score file was edited.

The RQ2 verifier reads only the published result CSVs and metrics JSON. It does not open `R1_REVIEW_RECORDS.csv` or private review data. These verifications demonstrate internal consistency, not source reauthentication. Full RQ1 replay and source-level RQ2 replay require external data.
