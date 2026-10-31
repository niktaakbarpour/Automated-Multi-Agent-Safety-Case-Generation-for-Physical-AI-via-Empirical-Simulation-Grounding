# Restricted R1 V4 infrastructure — Phase 2A

Checker `4.0.0a1`; requirement `2.0.0`; configuration schema `2.0.1`; manifest
`1.0.0`; evidence/assessment schema `1.0.0`. This executable infrastructure accepts
explicit synthetic analytical assumptions. It contains no physical fall detector,
LIBERO reader, simulator, model call or empirically admitted measurement profile.
Synthetic outputs never establish empirical safety or effectiveness.

The finalized Phase 1.6 specification remains unchanged and authoritative. The
Phase 2A user instruction authorizes infrastructure implementation; the older
phase-specific statements saying no implementation describe Phase 1.6's boundary.
No scientific rule or numerical calibration was added to resolve a conflict.

## Architecture

| Module | Responsibility |
|---|---|
| `configuration.py` | Reuses the authoritative schema; checks mappings, identities, boundaries and manifest consistency before evidence assessment. |
| `manifest.py` | Closed version/hash registry; exact normative-package, schema, adapter, profile, capability and checker bindings; hash-resolved inline artifacts. |
| `contracts.py` | Frozen dataclasses/enums for measurements, geometry, contacts, cameras, frames, uncertainty, evidence, dependencies, coverage and object assessments. |
| `admission.py` | Source-ledger admission, claim/kind checks, boundary/clock/scope checks, explicit single-parent constraints, conflicts and transitive dependency propagation. |
| `applicability.py` | Pure per-object bookkeeping with initial applicability fixed at t0; no automatic re-arm or object-name replacement. |
| `temporal.py` | Explicit snapshots and transition cells, negative coverage, joins, gaps, overlaps, invalid and unobserved cells; no interpolation. |
| `aggregate.py` | Pure deterministic V > IC > U > qualified N > NA aggregation, counts and empty-scope accounting. |
| `runtime.py`, `__main__.py` | Structured assessment and CLI; stable serialization/hashing, diagnostics and provenance. |
| `fixtures.py`, `demonstrate.py` | Synthetic declarations and reproducible CLI/library demonstrations. |
| `integrity.py`, `validate.py` | Hestia tests, baseline comparison, frozen checks and 55-case acceptance mapping. |

## Runtime input and trust boundary

Run from the repository root on Hestia:

```sh
export HOME=/tmp PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONDONTWRITEBYTECODE=1 TMPDIR=/disk/1/data/niktakbr
python3 -m evaluation.r1_v4 --input evaluation/r1_v4/synthetic/three_object_violation.json --output /disk/1/data/niktakbr/NEW-assessment.json
```

Input contains `configuration` (including the manifest), `evidence` and inline
`artifacts`. The CLI refuses existing output files. Exit 0 means assessment without
missing requirements; exit 1 means configuration rejection or reported missing/
unsupported requirements; exit 2 means transport/JSON/input-output failure. Read
outcomes and physical validity from the structured result, not the exit code.
Duplicate JSON keys and nonfinite numbers, including exponent overflow, are rejected.

Artifact references are keys, never filenames or network locations. Runtime reads
no caller-selected files beyond explicit input/output paths. Built-in records cannot
be overridden. Runtime pins the entire 13-file normative package, schemas, analytical
adapter/profile/capability records and checker source/contract inventory. Unresolved
required bindings produce IC; internally inconsistent configuration is rejected
before assessment.

Embedded artifacts are hashed over UTF-8 JSON with sorted keys, compact separators,
unescaped Unicode and finite numbers (`provenance.canonical`). Built-in file bindings
use exact bytes; virtual normative/checker inventories use canonical filename/hash
maps. Input/configuration/assessment hashes use canonical JSON. This explicitly
defined Python JSON contract does not claim RFC 8785 conformance.

A source ledger binds each full record to exact synthetic assumptions. Model/roster,
domain and validity scope are separately hash-bound. A hash proves content identity,
never physical truth. Supplied validation flags/certificates cannot enable empirical
admission. `physical_safety_conclusion=false` and `empirical_profiles_enabled=false`
are unconditional output restrictions.

## Evidence and uncertainty semantics

Direct/derived measurements, contacts and cameras are representable but do not infer
support, carrying, falling or negative coverage. Contact alone and isolated heights
cannot become witnesses. Typed geometry validates declared BOX dimensions and
provenance; this is not empirical geometry validation. Protected bodies may move;
static horizontal support roots are a separate model role.

Only source-bound synthetic declarations with admitted prerequisite chains establish
analytical presence, identity, initial support, event predicates or static negative
certificates. Every support link must be an explicit exact fixture constraint.
Cycles remain unresolved; multiple-parent solving is unsupported. Graph connectivity
is not physical support.

Missing observations under a supported profile yield U; missing version/hash
contracts, source corruption or incompatible essential bindings yield IC. Unscopable
header/envelope errors invalidate the evidence contract. Malformed payloads retain
local invalidity; dependent witnesses become U, while unrelated valid witnesses
survive. Conflicts/dependency reasons remain in output. Admissible same-predicate
or positive/negative event conflicts suspend dependent witnesses before aggregation;
there is no majority/confidence shortcut.

The analytical profile assumes exact temporal coordinates. Synthetic zero uncertainty
means exact mathematical input, never empirical calibration. Unknown/nonzero phase
bounds or unresolved descriptions cause abstention for affected records. Onset and
downward intervals must lie within fixed boundaries, have established ordering and
a nonzero downward phase. No minimum physical distance/duration, contact threshold
or alignment window is set.

Verified absence is NA with `scope_mismatch=true` and
`study_eligibility=pending_protocol_decision`. Missing detection is not absence;
incomplete rosters cannot establish it. Unsupported body geometry is irrelevant to
an admitted absence proof. Incompatible identity/presence foundations still block
that proof. No intended-study eligibility policy is chosen.

## Coverage and aggregation

Snapshot/transition cells are explicit, unique and boundary-bound; every requested
join is in the domain. Negative certificates qualify only listed static cells.
Unlisted joins/gaps are never filled by interval union. Overlaps are deduplicated;
producers, source hashes and dependencies remain visible and do not establish
independence. Dynamic/handling negative composition is disabled. Uncertain replacement,
re-placement or handoff boundaries block subsequent whole-domain negatives; prior
independent positives are retained.

`coverage.missing` means cells lacking admitted negative certificates;
`coverage.unobserved` means cells without explicitly listed record coverage. A
positive cell can be observed while lacking negative coverage. `invalid` reports
invalid cell bindings separately. An event never becomes complete negative coverage.

Results retain all configured objects, applicability/outcomes, counts, evidence IDs,
conflicts, unknowns, invalidity and completeness. A sound admitted violation dominates
unrelated NA/U/IC. Empty scope/NA never contributes a TN or safety pass; no empirical
metrics are produced. Completeness is conservative and independent of the primary
outcome. Source ordering preserves per-object semantics; changed ordered provenance
can change the input hash.

## Implemented and analytically tested

Configuration/manifest versions/hashes; arbitrary explicit counts; static unions;
identity/presence; typed records; dependency admission/conflicts; uncertainty; static
coverage cells; aggregation; CLI; reproducible synthetic demonstrations. See
[validation/ACCEPTANCE_COVERAGE.json](validation/ACCEPTANCE_COVERAGE.json) for all
55 planned cases and limits. Declaration tests do not complete physical trajectory
or empirical acceptance tests.

## Deferred, blocked or unsupported

All empirical admission is disabled, including LIBERO. The first future empirical
adapter remains restricted by the finalized LIBERO scope; none is implemented or
certified here. Calibration, load-bearing/handling inference, recorder/state/contact
phase, geometry/gravity/pose uncertainty, negative certificates and independent
reference validation remain evidence gates. No empirical fall, continuous-time
safety or accuracy claim is supported.

Moving/articulated roots, multiple-parent solving, complex handoffs, automatic re-arm,
dynamic reassignment, dynamic/handling coverage, non-BOX empirical shapes, vision-only
profiles and other benchmarks remain deferred/unsupported. Natural and controlled
empirical data must remain separate. Historical AI-only agreement remains exploratory.

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

Analytical inference references must resolve to the built-in profile; the clock
binds to the hashed domain and roots to the synthetic model/common frame. Unknown
geometry, gravity, transform or clock references cannot be ignored. Boundary-context
inference beyond the exact declared t0 is not implemented in this profile.
