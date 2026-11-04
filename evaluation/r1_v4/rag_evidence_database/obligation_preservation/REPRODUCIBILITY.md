# Reproduction

Hestia, repository `/disk/1/data/niktakbr/trustworthy-phase16`, work `/disk/1/data/niktakbr/trustworthy-phase5k1-working`. Use /usr/bin/python3 -S, PYTHONDONTWRITEBYTECODE=1, repository plus recorded Python 3.12 site-packages in PYTHONPATH. HF_HOME/XDG_CACHE_HOME use phase5k1-owned caches. No installs/training/model changes. Existing semantic model is pinned by the K manifest. No Alliance computation or Sea NFS.

RESOURCE_PREFLIGHT.json budgeted ≤1 GiB added disk/4 GiB per process before work. FINAL_PRESERVATION.json records used/free space. No destructive cleanup/full-corpus copying. Faults use isolated bounded scratch copies.

Module prefix: evaluation.r1_v4.rag_evidence_database.obligation_preservation.

```text
python3 -S -m <prefix>.validate_references
python3 -S -m <prefix>.evaluate --dataset evaluation/r1_v4/rag_evidence_database/obligation_preservation/FROZEN_EVALUATION_DATASET.jsonl --run <new-label>
python3 -S -c "from evaluation.r1_v4.rag_evidence_database.obligation_preservation.metrics import run; run('final_v2')"
python3 -S -m <prefix>.preservation
python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/obligation_preservation/tests
```

Do not regenerate inputs. Dataset `1332e509a5384293e8334e680193242f31482279121443231cd28bc0c80cc14f`; implementation `656f9b3fd576f0a7448cef45e32137000293710ac1663be9f257cde7c6c6a6d5`; references `d5b7ba042d737e56f4f776d1daa836da507008cbbab76544e3b0d0ff31108843`; criteria `d66a607687081053b10a8f7d38d549a63c5f82e655ef346515f80d3826c63771`. Git-bound ARTIFACT_MANIFEST.json is the trust root. Cases bind request/reference, mode, database, catalogue and code. Resume validates canonical bytes.

All three passes share `5bc4b7b58190f1395d5e925f46d5491abcd79245761e38e524ebb9089006d99e`. Full resume 288/288; partial 37 reused/251 completed. All 864 files match after removing only latency/scratch spelling; all values/IDs/obligations/status/uncertainty remain. Modified-output control fails. Automated replay/source decoding is not human replication.

Checkout parent `dda1353dc590613dc5f09682616f8e5e13fef570` and verify K manifest `e0006613de605ad14025c91ae23fd16ab373fb5f7acd1bf1449fdf0c626122ee`. This branch adds an opt-in wrapper; unchanged database/catalogue remain hash-pinned prerequisites. V1 is archived, not replaced. Each assessment was frozen first; V2 uses fresh scopes and 72 new formulations repeated twice. No corrected-final tuning/exclusions.
