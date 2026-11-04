# Phase 5G — Measurement-channel coverage and contracts

Database/retrieval infrastructure only. Baseline commit c24795ed9383110243288db520e5f98af484b4ad was independently verified before changes. All processing ran on Hestia. No simulations, new execution profiles, downstream safety-case agents, prediction/label edits, push or merge.

Phase 5F preserves 432 executions, 104 variants, 80,786 evidence records and 58,075 saved frames. Phase 5G adds 2,592 independently searchable direct-channel series references (six per execution), for 83,378 total records across the two evidence tables. Existing evidence bodies, units, source associations, normalized variant/scope relations and core schema remain identical.

Final database: `/disk/1/data/niktakbr/trustworthy-phase5g-working/expanded.sqlite`
SHA-256: `d1241f28089ff910baf8ec276fbaa3f9d2b71aa3c7b850fe494b976eb51320fb`
Size: 508,624,896 bytes; growth 17,432,576 bytes (3.55%).

Start with CHANNEL_SELECTION.md, EVIDENCE_CONTRACTS.md and LIMITATIONS.md. Channel inventory includes 139 HDF5 dataset patterns, 36 attribute patterns, 2630 JSON keys and nine local artifact families. These are recorded source patterns/metadata keys, not equally interpreted physical quantities.

The five newly indexed arrays remain explicitly uninterpreted raw values. Only the simulator contact-entry count has verified count units. Retrievability is not evidence that a value establishes a safety claim. Empirical R1 admission remains disabled.

CHANNEL_COVERAGE_MATRIX.csv is normalized: join channel_key to CHANNEL_INVENTORY.csv, source_key to EXECUTION_SOURCE_BINDINGS.csv and value_profile_key to VALUE_PROFILES.json. All 816,800 coverage rows are retained; the expanded matrix and per-execution inventories are external artifacts in the manifest.
