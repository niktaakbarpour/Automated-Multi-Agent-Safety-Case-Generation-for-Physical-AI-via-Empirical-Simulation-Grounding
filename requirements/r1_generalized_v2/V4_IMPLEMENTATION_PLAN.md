# V4 engineering plan — no implementation in Phase 1

Phase 1.6 design dispositions are in [OPEN_DECISIONS.md](OPEN_DECISIONS.md).
Implementation requires a subsequent user task; empirical use additionally requires
[EMPIRICAL_GATES.md](finalization/EMPIRICAL_GATES.md). Proposed
paths/interfaces below do not exist as checker modules in this task. V3 remains frozen.
The target semantics are [FORMAL_SEMANTICS.md](FORMAL_SEMANTICS.md), not copied
V3 event tags or an LLM's free-text judgment.

## Proposed boundaries and interfaces

| Proposed module | Interface / responsibility |
|---|---|
| `r1_v4/configuration.py` | `load_config(path) -> ValidatedConfig or ConfigDiagnostics`; JSON Schema plus semantic references/boundaries; never assert empirical validity from JSON. |
| `r1_v4/contracts.py` | Immutable typed `ExecutionIdentity`, `ObjectBinding`, `SurfaceBinding`, `EvidenceValidity`, `ClockDomain`, `CoverageSet`, `Witness`, `ObjectAssessment`, `ExecutionAssessment`. |
| `r1_v4/adapters/base.py` | `describe_capabilities()`, `resolve_identity(config, source)`, `read_window(request)`, `verify_source(binding)`; normalized observations retain original units/frames/producer hashes and converted common-frame values. |
| `r1_v4/adapters/libero.py` | Recorded metadata/timeline, native geometry IDs/anonymous pieces, HDF5 or admitted preserved-export reader, object/surface/robot roles. No name prefixes or table IDs in the reasoning core. |
| `r1_v4/geometry.py` | `validate_geometry(binding, window)` and capability-dispatched support/contact/motion witnesses. Initial release is restricted to admitted rigid BOX profiles, returning IC for unsupported required representations. |
| `r1_v4/temporal.py` | Resolve t0/t1 and context, monotonic clocks, source/event/exposure phase intervals, missing cells and censoring. Never infer exposure synchronization from equal frame labels. |
| `r1_v4/support.py` | `assess_support(object, surface_set, boundary, evidence) -> T/F/U + witness`; direct and validated indirect chains, complete absence proof, cycles rejected; multiple-parent inference deferred. |
| `r1_v4/events.py` | `track_physical_episodes(...) -> evidence-qualified phases`; support loss, downward motion, carrying/release, recontacts and censoring kept separate. Preserve setup/history and prior established events. |
| `r1_v4/scope.py` | `classify_requirement_scope(event, applicability, interval, handling_policy)`; non-applicable objects never receive in-scope R1 violation tags. Unknown origin/handling never silently excluded. |
| `r1_v4/coverage.py` | `qualify_clear_windows(...)` and validated union/containment operations; do not fill gaps or treat absent candidates as negatives. |
| `r1_v4/assessment.py` | Apply object outcome precedence, preserve NA/unknown/IC distinctions, reasons and claim-specific coverage. |
| `r1_v4/aggregate.py` | Execution vector/counts and approved restricted precedence/empty scope; no implicit all-objects-NA shortcut. |
| `r1_v4/provenance.py` | Source/config/checker/adapter/calibration hashes, model bindings, exact input windows, output seals and replay manifests. No credentials or raw media in Git. |
| `r1_v4/cli.py` | Read-only evaluation into a new output directory; explicit validation failures, deterministic replay and refusal to overwrite sealed results. No simulation stepping or model calls. |

`ObjectAssessment` must include requirement/checker/adapter/profile versions;
execution/object/S identities; applicability and reason; contract status;
requested/available/admitted/negative/unknown domains; physical and requirement events;
excluded phases; scoped outcome and rationale; evidence IDs/hashes; calibration and
alignment uncertainty; and reproducible diagnostics. Never collapse this to `pass`.

`ExecutionAssessment` must include every configured object, applicability/outcome
counts, empty-scope status, primary outcome, completeness flags and invalidity reasons.
Any benchmark adapter must negotiate capabilities. An unsupported shape/clock/force
assumption is an explicit result; it is not permission to synthesize observations.

## Implementation sequence and acceptance gates

1. Approve semantics and evidence/aggregation decisions. Freeze the specification
   version and an analytical fixture protocol. No NV cohort tuning.
2. Implement configuration/typed output contracts and semantic validation. Complete
   zero/one/three/five-object tests before reading empirical sources.
3. Implement deterministic identity/geometry/time admission with a limited declared
   capability profile. Reject mismatched model/native IDs and incomplete contact
   absence proofs. Validate transforms/units independently of event logic.
4. Implement applicability; then physical-phase tracking; then scope gating. Require
   an explicit initial-applicability gate for every R1 event and preserve setup origin.
5. Implement qualified negative windows and aggregation. Dynamic/handling negative composition remains deferred; no implementation in the
   initial profile. Static joins require qualified transition cells.
6. Implement immutable provenance, source-preservation receipts and replay. Freeze
   inference source/config before reading new reference labels or executing evaluation.
7. Run analytical tests, metamorphic identity/frame/unit transformations and frozen
   V3-emulation comparisons. Document differences rather than editing old outputs.
8. Plan a separately authorized, disjoint empirical evaluation with verified positive
   and negative reference cases. Do not launch new recordings/simulations in this phase.

## Research operation and repository boundaries

Compute on Hestia, all new staging/results under `/disk/1`; `/disk/0` is already
below the requested 500-GB reserve and must receive no new research payloads. No
deletion or simulator rerun is authorized. Alliance is storage/archive/restoration,
not a compute fallback. Do not use Sea or the ISSTA repository. Preserve a source
inventory and exact commands for every later run; choose persistent scheduling/session
mechanisms for long work without interfering with other jobs.

## Completion criteria for a later V4 phase

All [test matrix](V4_TEST_MATRIX.md) required cases pass on the declared capability
profile; unsupported profiles fail explicitly; frozen-artifact hashes remain unchanged;
new inference and evidence protocol are sealed; performance claims respect unknowns,
coverage and zero-positive denominators. Additional adapters are separately validated
deliverables, not evidence supplied by the configuration schema. No RAG, safety-case
drafting, critic or argument-revision implementation belongs in Phase 1 or this plan's
first checker milestone.

## Restricted entry order after Phase 1.6

First implement configuration 2.0.1/manifest contracts, semantic consistency checks,
dependency-scoped validity records and pure aggregation over admitted synthetic
outcome records. Keep all empirical capabilities disabled. Then add analytical
fixture conformance only. Runtime evidence schema/profile/checker artifacts must
be explicitly versioned and hashed when created; unresolved examples fail admission.
No new numeric defaults, simulator jobs, RAG or multi-agent implementation follows
from this plan. See [V4_ENTRY_CHECKLIST.md](finalization/V4_ENTRY_CHECKLIST.md).
