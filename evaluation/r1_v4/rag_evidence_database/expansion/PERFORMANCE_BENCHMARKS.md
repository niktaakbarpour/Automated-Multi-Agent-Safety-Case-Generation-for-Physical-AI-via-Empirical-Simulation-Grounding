# Performance

First build: 230.398 seconds to append 10,470 new units after copying the baseline, or 45.44 new units/s. Database: 75,915,264 bytes (72.40 MiB), including 11,830 evidence records and the 2,000-entry catalog. First-process peak RSS: 307,444 KiB. CLI address-space cap: 4 GiB. One execution is processed at a time with 32-frame units. No GPU/model/simulation is used.

Independent reproduction took 230.836 seconds and matched the logical build ID and canonical export. Resume took 19.154 seconds, rechecked inputs and skipped all 36 completed jobs without duplicating baseline records. SQLite physical byte equality is not required.

Conflict dependency checks now preindex explicit relationships instead of scanning every record on recursion. Search computes conflict relationships once per request using an auxiliary expression index in the expanded database. Regressions preserve conservative rejection. No physical admission or calibration changes. Source hashes are still checked freshly per request, with only within-request deduplication.

Source I/O and immutable-record parsing remain material costs. Broad queries scale with matching sources; metadata filters and the 10,000-candidate cap remain. New model/task shapes need profiling. The remaining 359,010-unit five-object scenario is about 2.1 GB additional index storage and 2.2 hours at observed marginal throughput, excluding restoration, contention and profile validation. It was not executed.
