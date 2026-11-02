# Measured performance

Primary append elapsed 193.284s for 147 executions:
0.761 executions/s. Peak build RSS
1,732,092KiB. Indexing holds one execution in memory; integrity/
logical-export QA loads compact registry metadata. Profiles/maps and sources
remain outside Git; no raw frame arrays or videos are stored in SQLite.

Database: 491,192,320bytes; source restoration:
5,855,991,575bytes; semantic sidecar:17,440,768bytes.
Structured/lexical latency: `{'max': 1.06181678827852, 'median': 0.19303258135914803, 'p95': 0.2192525900900364}` seconds.
Semantic query latency and stack bindings are reported separately. Results
include source/dependency checks and depend on cache/load conditions.
Final disk1 available:1,628,873,240,576bytes, exceeding 500GB.
Disk0's pre-existing reserve deficit was not remediated or used for large new
artifacts. All computation was on Hestia; Alliance provided storage retrieval
only. No simulations, source deletion, push or merge occurred.
