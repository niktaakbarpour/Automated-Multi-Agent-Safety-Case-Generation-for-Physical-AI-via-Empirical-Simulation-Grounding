# Drafter contract

The Drafter organizes proposed reasoning and supplied observations. It does not
perform physical checking or admit a verified R1 outcome. Input/output validators
perform no inference; preparation/adaptation commands perform no database query.

## Authoritative contracts and versions

- R1 requirement: `R1` version `2.0.0`.
- Configuration schema: `requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json`,
  version `2.0.1`; distinct from the requirement version.
- Registry records: `evaluation/r1_v4/evidence_registry_gsn/registry_record.schema.json`
  and `models.Record`, version `1.0.0`.
- Shared GSN: `gsn_graph.schema.json` and `gsn.Graph`, version `1.0.0`.
- Wrapper identifiers remain `drafter-request/0.1.0` and `draft-argument/0.1.0`.
  This extension adds input profiles and mandatory review semantics to accepted
  output; older accepted envelopes without these semantics are rejected.
- Intermediate plan: `urn:trustworthy:drafter-graph-plan:0.2.0`; prompt
  `draft-argument-prompt/0.2.0`; serializer `graph-plan-to-gsn/0.2.0`.
- Phase 5 input: `phase5-structured-1.0.0`; retained output context:
  `drafter-phase5-context/1.0.0`.

Schemas resolve only shipped local contracts. Unknown wrapper fields, malformed
JSON, nonfinite values and duplicate JSON keys are rejected. JSON schema does not
replace shared semantic validators or the cross-field checks below.

## DraftRequest profiles

| Profile | Binding and permitted input |
| --- | --- |
| Omitted or `archived_registry` | The original pinned configuration derivation and unchanged archived registry export; `test_fixture=true`, `usage=contract_fixture`. |
| `supplied_registry` | Complete supported R1 configuration and original registry records; supplied-snapshot provenance; `usage=proposed_argument`. |
| `phase5_structured` | The same configurable envelope plus 1–16 exact structured query/bundle pairs and their digest; `usage=proposed_argument`. |

The original archived admission rules remain separate; choosing a new profile does
not make a changed archive pass its pinned verifier. Configurable profiles accept
different valid object rosters and surface mappings without requiring equality to
the five-object fixture. Analytical configurations require the fixture label.
`test_fixture=false` is an input classification, never empirical authority.

### Common fields and admission

- `requirement_configuration` preserves the complete configuration, assessment
  manifest, declared validation status, object/surface mapping and source bindings.
  Its digest must match `requirement_configuration_sha256`.
- `target_execution` supplies execution, benchmark, task, checkpoint and variant.
  Configuration checkpoint is required by this Drafter profile even though the
  general configuration schema permits its omission. Missing/malformed fields
  produce validation errors before any model access.
- `monitoring_scope` contains an explicit inclusive saved-frame interval, clock
  `saved_frame_index`, domain `frame`, boundary provenance and resolution status.
  Configuration boundaries must agree exactly. Other clock mappings and unresolved
  boundaries are currently unsupported; no nearest frame or inferred boundary is used.
- `evidence_package` contains original version-1 registry records, unchanged
  content-derived IDs and metadata. Its digest binds the complete export.
- `evidence_handling` partitions records into unique disjoint graph-eligible and
  context-only IDs whose union is the export. Eligibility means compatible scoped
  observation metadata, not sufficient physical evidence.
- `retrieval_context` reports the full requested roster/window, missing objects
  and gaps in eligible registry observations. It remains `not_evaluated` for
  physical completeness; actual Phase 5 statuses are retained separately.
- `checker_context` remains `not_available` with no assessments.
  `safety_knowledge` and `related_cases` remain empty pending separate contracts.
- `limitations` remain attributed input caveats. All empirical-admission and
  safety-verification flags are false.

Parse registry records using the original `Record.parse`, check dependencies,
bind requirement/execution/benchmark/task/checkpoint/object scope, and require
eligible intervals to lie inside the declared monitoring scope. Preserve excluded
records and gaps. Missing observations are not evidence of safety or a violation.

Use `provenance.canonical` and `digest` for canonical JSON identities.
These differ from hashes of original file bytes and Git blob SHA-1 identities.

### Archived binding

The archive verifier retains its pinned repository revision, known source paths,
exact Git blob/file/canonical hashes and five permitted configuration changes.
It replays each declared before/after change and requires equality with the
embedded configuration. This is reproducible fixture lineage, not approval of the
derived configuration. Source paths inside evidence never authorize file reads.

### Supplied snapshot binding

`request_profiles.build_supplied_request(...)` accepts a request ID, complete
configuration, target, monitoring scope, optional original registry records,
fixture classification and limitations. It computes the configuration/package
digests, record partition and eligible-observation gaps, then validates the result.

`input_provenance.mode=supplied_snapshot` retains these digests and explicitly
states `source_authentication=not_performed`. A matching hash is a consistency
binding, not authentication of the caller's original source. Supplied files,
producer binaries and Hestia source measurements are not opened or replayed.

## Phase 5 structured adapter

`phase5_adapter.adapt_phase5_request(...)` additionally accepts the exact
`structured_request` and returned `evidence_bundle`, with optional original
registry records. It creates `structured_evidence=[{request,bundle}]`, records its
digest and validates the complete supplied request. The builder also accepts a
list of structured pairs for multiple queries.

The adapter composes the existing `critic.retrieval` consumer checks rather than
copying their logic. It checks query/obligation identity, source/citation basis,
release/assurance, scope, missing obligations, conditional interpretations and
status relationships. It adds R1 object and monitoring-window checks. These are
local consistency checks; trusted live source verification remains the retriever's
separate responsibility.

Keep `COMPLETE WITHIN VERIFIED CONTRACT`, `PARTIAL`, `UNAVAILABLE`,
`UNSUPPORTED`, `INVALID SCOPE` and `UNVERIFIED PLAN` distinct. Valid rejection
or partial snapshots may remain explicit unresolved context; evidence cannot be
silently promoted to a more complete status. Completeness covers the explicit
mandatory obligations, not all facts needed to prove R1.

The context retains exact entries, retrieval rows, source artifacts, original item
IDs, citation IDs/bases, obligations, missing evidence, values and assumptions.
An existing `ev:` record is eligible only through an identical compatible
`original_evidence_ids` source link. Raw `channel:`, `source-ref:` and
`evidence-citation:` items remain context. They are never renamed into registry
records, graph nodes, object-specific physical claims or checker outcomes.

The model receives this attributed context. Accepted `evidence_context` must
equal the ledger independently recomputed from the validated request. A caller
cannot supply a different ledger or omit it from an accepted structured draft.

CLI `--prepare-registry INPUTS.json` and `--adapt-phase5 INPUTS.json` accept JSON
keyword arguments matching these APIs and save a prepared request with `--out`.
They perform no inference, retrieval or source authentication. The standard
validation, mock and generation commands accept the resulting request.

## DraftArgument and validation

`generation_status` is `accepted`, `rejected` or `failed`. Rejection/failure
has a null `argument_bundle` and explicit diagnostics. Acceptance requires the
exact request/configuration/evidence digests and fixture classification, complete
ordered object roster, one graph per object and full outcome vector. Every object
and execution outcome is `insufficient_information`.

Generation and standalone output validation enforce the same Drafter rules:
one physical root goal, strategy and context, a strategy subclaim, globally unique
object-prefixed IDs, connected reachable nodes, declared edge endpoints, and an
eligible original Solution citation when such records exist. The actual shared
`Graph.validate` still enforces edge typing, cycles, evidence provenance and scope.
Every Solution preserves its exact record source path/hash/selector, interval,
clock/domain, status and complete registry metadata. Cross-object links and
context-only citations are rejected.

The decoder uses full-sentence string constraints without the incompatible
substring regex. Node variants require correct physical flags, non-null eligible
Solution evidence and null evidence elsewhere. `uniqueItems` is omitted only
from the decoder limitations array for backend compatibility; host validation
still checks duplicate limitations. Namespace constraints do not replace declared
node membership, object scope or reference checks. Unusable single-character or
repeated-placeholder prose is rejected. Invalid output is not repaired.

### Host conclusions and model prose

Displayed `summary`, execution conclusion and required limitations come from
trusted host templates and the validated input. The validator checks exact values;
they cannot silently assert safety while structured outcomes remain unresolved.
Input limitations are explicitly attributed as unverified text.

Original model summary/limitations remain in mandatory `reasoning_review` with
`status=required` and a fixed review warning. LLM reasoning-node provenance also
requires the review marker; physical goals stay unresolved. This explicitly flags
arbitrary model prose, including possible contradictions, for human/Critic review.
It does not claim that a keyword filter proves all free-form statements consistent
or true. Graph acceptance and scientific argument quality are separate.

### Trace and actual execution

Accepted live output requires run identity, configured/effective model identity,
prompt version/hash and original output digest. Unknown model revisions remain
null; the pinned SGLang example records the revision used in Nikta's actual run.
The report preserves exact messages/schema, raw response, plan and stage diagnostics.
It distinguishes schema/serialization rejection from shared graph validation;
a validator not reached is reported as not run.

Nikta's original Qwen response passed intermediate JSON schema, then failed
serialization before shared graph validation. Its five graph plans, 26 nodes and
25 edges are rejected-plan counts, not accepted GSN artifacts. The EOS-aware
XGrammar diagnostic explains the observed single-character constraint. That run
does not establish Qwen reasoning performance. Updated-code GPU generation and
real-database adapter execution remain pending. Preserve original failed artifacts.

## Explicit mock boundary

`--mock-demo` assembles a fixed-rule plan for the supplied supported object roster
without model configuration, inference or network access. It uses the same shared
graph/reference checks and preserves unresolved outcomes. Its distinct
`drafter-mock-demo/0.1.0` and `drafter-mock-run/0.1.0` envelopes keep
`model_called=false`, `live_model_result=false`, null model/prompt identities
and deterministic generator/source/plan bindings.

Mock reasoning is labelled `deterministic_mock`; original Solution metadata
retains its observation origin/status. The live validator rejects mock envelopes.
A successful mock is an interface demonstration, not model performance, completed
Critic integration or robot-safety validation. There is no automatic mock fallback.
