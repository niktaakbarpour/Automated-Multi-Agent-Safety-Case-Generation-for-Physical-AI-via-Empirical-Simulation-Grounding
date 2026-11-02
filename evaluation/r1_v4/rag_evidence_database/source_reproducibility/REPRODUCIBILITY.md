# Reproduction

All computation ran on Hestia with python3 -S and audited explicit PYTHONPATH. No Alliance computation, Sea NFS, new simulations, global installs or full-corpus copying. Resource preflight is in RESOURCE_PREFLIGHT.json. Work: /disk/1/data/niktakbr/trustworthy-phase5i-working. Diagnostic databases are retained.

From repository root run modules under evaluation.r1_v4.rag_evidence_database.source_reproducibility: inventory, dependencies (retrieval and native environment; invocation in source), clocks, build, validate, benchmarks f, benchmarks g, benchmarks h, regressions, reports. verify_baseline.py records pre-change 665-test checks. Freeze inventories before build; changed input/producer hashes reject resume.

build copies Phase 5H and adds i_ tables. validate compares baseline rows, verifies raw/clock queries, freezes restoration selection, restores bounded sources, builds independently and tests full/partial resume. Timings/bytes: BUILD.json, ASSURANCE_VALIDATION.json and RESTORATION.json. RESOURCE_OBSERVATIONS.json records retained working bytes and free disk; process RSS was sampled, not continuously measured. Arrays remain external.

Verification requires a caller-pinned manifest hash. SQLite byte layout may differ after a fresh build; logical equivalence is the reproducibility criterion. Historical reexecution and complete binary reproduction remain unsupported. Post-commit read-only preservation checks are required; no push/merge.
