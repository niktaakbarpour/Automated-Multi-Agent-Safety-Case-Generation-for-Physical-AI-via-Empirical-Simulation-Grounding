# Reproduction and release verification

Run on Hestia, repository `/disk/1/data/niktakbr/trustworthy-phase16`, Python `/usr/bin/python3 -S`. Dependencies are recorded in ENVIRONMENT_AND_RESOURCES.json and prior pinned manifests. Set PYTHONDONTWRITEBYTECODE=1; PYTHONPATH includes repository plus `/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages` and installed `/usr/local/lib/python3.12/site-packages`, `/usr/lib64/python3.12/site-packages`, `/usr/lib/python3.12/site-packages`. Use K-owned HF_HOME/XDG_CACHE_HOME. The existing local encoder is offline/pinned; no installation/training.

All module names below use prefix `evaluation.r1_v4.rag_evidence_database.retrieval_remediation.`:

```text
python3 -S -m <prefix>verify_release
python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/retrieval_remediation/tests
python3 -S -m <prefix>run_eval --dataset evaluation/r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl --run <new-label>
python3 -S -m <prefix>verify_outputs
python3 -S -m <prefix>final_assessment
```

`verify_outputs` checks the three documented run names; another operator can use its check_record routine and frozen binding formula with new paths. Verify ARTIFACT_MANIFEST.json against committed Git bytes before trusting results/cached progress. Each case binds request/reference, mode, database, catalogue and code. Dataset SHA `f6c6e31e12d3c0ed7e70db077494a4bed98f1d0a56d82f382c556c13b00c6caf`; implementation SHA `cecb69fd1d601a66cbeb7294099fab9cc49408f2d5235f911e28a9d65d5a3fde`; acceptance SHA `4117f21323050d4707abac453502ecb8c16fb97a6e4fa4085221591caff9a958`. Never regenerate frozen inputs during replay.

For a fresh catalogue call `build.populate(new_path)` and compare logical contents with BUILD.json. Resume validates every job input/row digest. `reproducibility.py` documents fresh/full/partial runs/catalogues; use new paths for another repetition because assertions distinguish fresh/resumed states. Automated decoding/replay is not independent human replication. Three final passes share canonical digest `cf85fddc3a0872274dd6909a1a2ef66f2221897e8fec098f54043d9ac547e8d6`. Only latency and fault-scratch path spelling are removed; IDs/values/scopes/statuses/uncertainties must match.

Restoration uses separately pinned database/catalogue plus RESTORATION_RESULTS.json's manifest. A trusted caller pins the manifest hash; canonical path/hash/execution/variant entries map to contained relative paths. No fallback/symlinks/traversal. Full-corpus or historical binary reproducibility is not claimed.

Preflight projected ≤2 GiB additive disk and ≤4 GiB/process memory with about 1.615 TB free. No corpus/database duplication or destructive cleanup. ENVIRONMENT_AND_RESOURCES.json and BENCHMARK.json capture resources/latency. Strict median 0.681s vs verified-session 0.108s on 16 calls each, shared Hestia load, descriptive only. Default strict requirements remain.

Chronology: development → V1 implementation/criteria freeze → source-grounded V1 freeze/evaluation/replay → typed diagnostic → archive V1 → narrow guard/tests → V2 implementation/criteria freeze → fresh-scope question freeze → evaluation/challenges/replay. Template overlap disclosed; no ranking/vocabulary tuning after V1. verify_release.py represents baseline checks. Original-36 selection filters development lines before parsing. Historical final cases are read only after freeze.
