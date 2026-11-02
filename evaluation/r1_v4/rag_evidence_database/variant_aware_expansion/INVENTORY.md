# Remaining inventory and variant discovery

The initial remaining pool has 1,617 candidates in 33 task partitions: eight
single-XML partitions and 25 multi-XML partitions. All candidate episode payloads
were absent from their original Hestia paths. All had expected XML hashes and
producer/archive mappings; this was metadata evidence, not fresh payload
validation. INVENTORY.json preserves the initial machine-readable expectations;
INVENTORY_VERIFIED.json adds actual admitted identities. Reserved/preflight
records are not inspected beyond exclusion identity metadata.

After restoration, 147 candidates each have exactly one
verified XML/assets variant and native mapping. Their 98
unique variants cover three task profiles.49 variants are shared across the two
goal tasks. XML filename and task identity are never treated as variant identity.
Content, verified external dependencies and per-execution geometry are checked.

Multiple possible variants:0 among validated executions. Missing expected XML
metadata:0 in the initial candidate pool. Unresolved/unrestored payload profiles:
1470. Unresolved native XML/body mappings:
0 in the admitted cohort; not assessed for unrestored candidates. The logical
main_table alias remains unresolved for all 147 and is not separately extracted.
No unknown body/geometry assignment is fabricated to increase coverage.

Single-XML assumptions were isolated in the Phase5E task profile registry,
pilot compilation, task-wide mapping selection and source-scope record factory
call sites. Phase5F supplies per-execution profiles and normalized relations,
reuses the factory and core schema, and guards scope before both retrieval modes.
