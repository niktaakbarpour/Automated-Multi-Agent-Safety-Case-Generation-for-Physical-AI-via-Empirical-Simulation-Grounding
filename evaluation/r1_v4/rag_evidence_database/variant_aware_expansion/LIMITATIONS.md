# Limitations

Only the frozen cohort has fresh payload and per-execution mapping validation.
Other inventory XML hashes are metadata-backed expectations, not verified XML/
asset profiles. No filename-only identity or guessed environment assignment is
used. Nested includes, missing assets, unnamed native bodies and unsupported
geometry bindings fail closed.

The declared logical fixture main_table is not exposed in recorded fixture-root
metadata. It is left unresolved. Native XML body `table` and its geometries remain
in the complete native map, but the logical alias is not guessed or exposed as a
validated main_table pose. Other fixture roots are read from before_settling and
before_first_action metadata and checked against native bodies. Only verified
static geometry subsets are referenced; no load-bearing support or articulated
support inference follows from this bookkeeping.

Six measurement families have separate searchable units. Other saved fields,
including qacc, act, actuator_force, aggregate cfrc_ext/cvel, sensor data, raw
end-effector/object-relative observables, encoded proprioception and site poses,
remain inventoried source references without new field-specific retrieval units.
Aggregate forces do not supply absent per-contact forces/normals. Unverified raw
coordinate/quaternion conventions are not promoted to valid spatial extraction.
COVERAGE_MATRIX.csv distinguishes recorded, exposed and searchable fields.

Frame intervals refer to saved indices, not continuous physical coverage.
Endpoint state, last-forward geometry/contact caches and camera exposure need not
be simultaneous. Camera exposure timestamps/alignment remain unavailable. Time-
domain conversion, cross-execution coverage composition, support inference,
fall witnesses and negative certificates remain unsupported/blocked. Root-height
change, contact or XML declarations cannot establish these predicates.

The optional semantic index uses the existing pinned local encoder and six raw
measurement descriptors. Documents and AI interpretations are not embedded;
unembedded records are not returned as semantic matches. Metadata and variant
filters precede ranking; broad/unsupported mode scopes are rejected. Fixed
paraphrases are repeated across source contexts and rotating objects, so query
instances are not independent linguistic relevance judgments. Scores and source
retrieval correctness are not physical safety confidence or checker accuracy.

Baseline records, wording and evidence IDs are preserved exactly. This includes
legacy spatial labels on old timestamp records and legacy 'Development only'
summary text on Phase5D expansion cases. Machine-readable stratum/provenance is
authoritative; it does not authorize calibration use. Newly indexed records use
correct nonspatial timestamps and explicit database-only partition text. AI-only
interpretations remain provisional; no human references are created or changed.

Source status, measurement availability and safety sufficiency remain distinct.
The registry is not a safety certificate. No downstream safety-case agent,
argument generation, new checker or empirical R1 admission is implemented.
