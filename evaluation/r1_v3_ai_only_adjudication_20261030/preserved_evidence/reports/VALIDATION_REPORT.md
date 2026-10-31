# Validation

All checks in VALIDATION.json passed on Hestia: 20 unique case identities, the AI3
and provisional-reference seals, original frozen prediction hash and configuration
bindings, 28 preserved uncertainty requests, and unchanged human-scoring freeze files.
CSV object-pose/contact times and recorded-geometry times match the nominal source
frame timestamps. This does not verify image exposure/physics synchronization.

Synthetic tests exclude non-applicable units and unknown references from binary TNs,
keep abstentions separate, reject disjoint uncovered windows and tampered seals,
and leave positive recall/F1 undefined with zero positives. No synthetic example is
counted as a research observation. Original evaluator annotation hashes were checked
before/after comparison. No original prediction was regenerated or changed.

All computation ran on Hestia. Git authoring/commit and report transfer are local
bookkeeping. Original states and full videos remain on Hestia. The assessment has
disclosed prior conversation exposure and is not a pristine independent replication.
