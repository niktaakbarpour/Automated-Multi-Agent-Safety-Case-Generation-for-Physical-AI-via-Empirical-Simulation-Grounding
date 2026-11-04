# Commands and environment

Host: Hestia. Repository: `/disk/1/data/niktakbr/trustworthy-phase16`. Working artifacts: `/disk/1/data/niktakbr/trustworthy-phase5l-working`. Python invoked with `-S`; frozen runtime package versions and imported source hashes are in FROZEN_RELEASE_CONFIGURATION.json. No global package installation or replacement occurred.

Commands (prefix `evaluation.r1_v4.rag_evidence_database.final_phase5_release.`):

- `python3 -S -m <prefix>examples`
- `python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/final_phase5_release/tests -v`
- `python3 -S -m <prefix>evaluate --run operator_fresh`
- `python3 -S -m <prefix>evaluate --run operator_partial --limit 37`, then without the limit
- `python3 -S -m <prefix>independent_audit`
- `python3 -S -m <prefix>preservation`
- `python3 -S -m <prefix>release --verify <trusted-manifest-hash>`

Replace `<prefix>` with the package prefix above. Exact inherited-suite commands, process environment and logs are preserved in FINAL_REGRESSIONS.json, reproduce.py and external baseline/post-regression artifacts. For isolated replay reproduce.py constructs a minimal environment with explicit dependency directories, thread limits and Hestia-owned caches; it imports no interactive shell initialization.

Resource preflight projected at most 1 GiB additive disk and 4 GiB memory/process with approximately 1.615 TB free. No full database/source-corpus copies or destructive cleanup were used. Bounded restored source content is 148459848 bytes. RESOURCE_PREFLIGHT.json and FINAL_RESOURCE_USAGE.json record measured disk/free-space information; no unmeasured peak RSS claim is made. Existing HDF5 arrays remain external.
