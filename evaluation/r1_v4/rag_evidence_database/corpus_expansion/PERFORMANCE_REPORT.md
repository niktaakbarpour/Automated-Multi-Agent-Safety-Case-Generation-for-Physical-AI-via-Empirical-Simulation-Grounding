# Final Phase 5D performance

The primary validated build copies the Phase 5C release then appends 49 executions / 9,961 units in 97.212 seconds (102.47 new units/s). Final database: 134,828,032 bytes (128.58 MiB), containing 89 executions, 21,791 evidence records and 2,000 historical catalog entries. First-process peak RSS: 699,836 KiB; the command uses a 4 GiB address-space limit. One execution is processed at a time, with 32-frame index windows rather than per-frame text copies.

An independent build from the immutable baseline has the same logical build ID and canonical evidence export. Resume rehashes sources and skips all 49 completed jobs. SQLite physical layout need not match. Closed independent append avoids repeatedly loading unrelated old execution graphs; its source, scope and incoming-conflict guards are tested, followed by complete database integrity validation. It does not weaken physical or measurement gates.

The new task has smaller source/state footprints than task 00, so timings are not a controlled cross-profile speed comparison. HDF5 I/O, shape checks, source hashing and parsing still dominate at scale. The 10,000-candidate query cap requires metadata narrowing; optional stratum filtering preserves old query IDs when absent.

Actual staging is 443 source files / 3,656,363,457 bytes. Working data and all databases stay on /disk/1; no original is overwritten/deleted and no large file goes to /disk/0. No GPU, new simulation or Alliance computation occurs. No additional batch is launched.
