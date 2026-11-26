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
- Intermediate plan: `urn:trustworthy:drafter-graph-plan:0.2.2`; prompt
  `draft-argument-prompt/0.2.2`; serializer `graph-plan-to-gsn/0.2.0`.
  Historical run traces can still record prompts 0.2.0 and 0.2.1; accepted live
  arguments must declare the current prompt version. The 0.2.2 decoder minimum
  is four nodes, matching the already-required distinct root,
  strategy, context and subclaim; node order is not fixed. Complete core-shape
  guidance does not insert or repair nodes/edges in returned proposals.
- Phase 5 input: `phase5-structured-1.0.0`; retained output context:
  `drafter-phase5-context/1.0.0`.

Schemas resolve only shipped local contracts. Unknown wrapper fields, malformed
JSON, nonfinite values and duplicate JSON keys are rejected. JSON schema does not
replace shared semantic validators or the cross-field checks below.

The supported runtime also rejects cyclic Python inputs, non-string JSON keys,
nesting beyond 128 levels and numbers outside the shared interval validator's
finite double range. A larger JSON integer can be syntactically valid JSON but
is unsupported by this profile; it is rejected before model access. The supplied
configuration must contain at least one protected object. An empty R1 scope is
not invalid under the shared requirement contract, but this Drafter does not
support an empty accepted argument.

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

This route requires the repaired Critic consumer merged into main by PR #21
(`cc0c9be`). A pre-repair consumer cannot safely validate all public request
restrictions. The adapter fails closed when its frozen-public-request validator
is unavailable; it does not fall back to older copied rules. Drafter's supported
`jsonschema` range includes both the shared checker's/Critic's 4.19.1 pin and the
recorded standalone Drafter client's 4.25.1. Both endpoints were tested on Hestia;
SGLang and XGrammar versions are unchanged.

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

Standalone validation also enforces the plan's identifier, text-length and graph
size constraints (at most 24 nodes and 80 edges per graph). It rejects oversized
graphs before the shared recursive validator. Reasoning text must have 8–1600
normalized characters, no more than 1600 original characters, and at least two
distinct alphabetic words; repeated
placeholder labels are unusable text. These are usability constraints, not a
semantic proof of meaningful reasoning. Reasoning-node provenance must match the
accepted envelope's run/prompt and the exact request/serializer binding, and its
status cannot be silently promoted from proposed/unresolved.

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

`schemas/generation_run.schema.json` describes complete generation-run reports,
including invalid-input and failed-model attempts. Early CLI parsing or setup
rejections use `schemas/operation_rejection.schema.json` and
`drafter-operation-rejection/0.1.0`. The CLI continues to return 1 on rejection
or failure (0 on success, argparse's 2 on invalid command syntax).

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

The request-specialized decoder uses Draft2020-12 `prefixItems` and `items:false`
to bind graph positions to the exact configuration roster. Each position also
binds node/edge namespaces and object-specific eligible registry citations.
The host independently rejects roster/order/identity/evidence violations. No
post-generation reordering, ID rewriting or evidence reassignment is performed.

## R1 v3 source-package profile (versioned)

`drafter-request/0.2.0` with `input_profile=r1v3_source_package`, and `draft-argument/0.2.0`, implemented in
`drafter/r1v3_profile.py`. They sit next to the profiles above, which are unchanged. `validate_request` and
`validate_argument` dispatch on `schema_version`; a 0.2.0 request must be paired with a 0.2.0 argument.

**Configuration.** `requirements/r1_initial_table_support_v3/R1_V3_DRAFTER_CONFIG_SCHEMA.json`
(`r1-v3-drafter-config/1.0.0`). It is derived from the frozen v3 files and bound to each by SHA-256: the checker
configuration `evaluation/r1_v3/config.json`, the selected requirement scope
`evaluation/r1_v3_generalization/blinded_review/requirement_scope.v3.json` and its scope decision
`REQUIREMENT_SCOPE_DECISION.md`. Those files are read, never changed or reinterpreted. A configuration that differs
from the one derived from them is refused. It fixes requirement `R1` version `r1-initial-table-support-v3-20261024`,
the five protected objects, the inclusive saved-frame window starting at frame 10 and ending at the terminal recorded
snapshot, the checker version and configuration hash, the outcome vocabulary of the v3 checker and the R1
aggregation precedence.

**Request.** `drafter.r1v3_profile.build_request(package, request_id=...)` takes a source evidence package
(`source-evidence-package/original-r1-v3-pre-integration-1`, such as
`evaluation/m4_20261127/integration/ORIGINAL_EXECUTION_EVIDENCE_PACKAGE.json`) and keeps it unchanged in the request,
bound by digest. Every other field is derived from the package, the configuration and the admission state, and the
validator recomputes each one, so none can drift from its source:

- target execution: execution ID, trajectory SHA-256 and path, source-identity status;
- monitoring scope: inclusive saved frames (10 to 257 for the original execution), terminal-snapshot end basis;
- evidence: all record IDs, the digest of each record and of the whole list, the retrieval selectors (database
  path and SHA-256, source commit, retrieval API, queried window, indexed requirement version, record types and
  count), the records' requirement versions, the graph-eligible and context-only partition and its rule, and the
  package's citation status. A record is graph-eligible only as an original
  record of this execution and a protected object under R1 v3, inside the window. Records of another requirement
  version stay context and are never cited, re-versioned or mapped;
- coverage and uncertainty per object and measurement type, as retrieved;
- checker context: status, checker version, configuration, prediction and seal hashes, assessments, and an
  admission record (`state`, `contract`, `reason`);
- explicit evidence gaps per object (no v3-citable evidence, no or non-admitted checker assessment, physical
  coverage not qualified, missing saved frames) and the package's limitations.

The package must name this requirement, object roster, window start and checker configuration, its record count and
queried window must match its records and the monitoring window, every assessment and
record must belong to the execution and roster, the checker must not have loaded reference answers, and no human
reference label may appear anywhere (the package's own note that the human reference is excluded is allowed).

**Admission.** An assessment is admitted only through a contract registered in
`r1v3_profile.ADMISSION_VERIFIERS` whose verifier accepts the request. None is registered: admission belongs to the
evidence-registry contract, which does not exist yet. Until then every request is `not_admitted`, and a request that
claims admission is refused.

**Outcomes.** An object outcome other than `insufficient_information` is accepted only with an `outcome_backing` that
names an admitted checker assessment of the same object, classification, checker version and configuration hash under
the request's admission contract, and at least one graph-eligible citation for that object. Otherwise the outcome is
`insufficient_information`. The execution outcome is the R1 aggregation (violation > insufficient_information >
no_violation_observed_within_reviewed_coverage > not_applicable). Summary and conclusion are host texts derived from
the outcomes. GSN physical-claim nodes stay unresolved and model prose still requires review.

**Status of the original execution.** Its package gives 135 retrieved records, all R1 2.0.0, so 0 are graph-eligible
under v3, and a frozen development-only checker assessment that is not admitted. Every object outcome is therefore
`insufficient_information`, as the rules require, with 15 explicit evidence gaps. A definite outcome becomes possible
when an admission contract and v3-citable records exist, without a change to this profile.

**Generation.** `generation.generate_argument` sends a `drafter-request/0.2.0` to `r1v3_generation.py`, so
`python -m drafter --generate` is unchanged. The model gets the v3 requirement, target, window, the graph-eligible
catalogue, counts of context-only records, coverage, the checker context with its admission state, the evidence
gaps and `host_outcomes`, and returns a plan in the existing plan schema (prompt
`prompts/draft_argument_r1v3_v1.md`). The host decides every outcome: an object gets its checker classification
only when the assessment is admitted and the plan cites graph-eligible evidence for that object; otherwise it stays
`insufficient_information`. The model never sets an outcome. The outcome backing lists exactly the Solution nodes of
that object's graph, and every reasoning node is bound to the request, the run, the prompt and the serializer
version. An accepted argument needs a real generation run (`backend` other than `not_run`).

**Decoder schema.** The server gets `r1v3_generation.decoder_schema(plan_schema)`, not the full plan schema. The
first GPU run failed with HTTP 500 because Outlines did not compile the full schema within its 60-second limit: it
turns counted repetitions (text `maxLength` 1600, node ID length `{1,128}`, and `minItems`/`maxItems` on the node,
edge and limitation arrays) into a regex automaton that grows too large. The decoder schema drops exactly those
bounds and keeps everything else (identifier patterns, roster and order, node types, physical-claim and evidence
constraints, required keys, no extra properties, text `minLength`). Every reply is still validated against the full
schema, so a reply that breaks a dropped bound is rejected, never repaired. CPU measurements with a 48,781-token BPE
vocabulary (not Qwen's): Outlines did not finish the full schema in 200 s and built the decoder schema in 2.4 s;
XGrammar 0.1.25 compiles both and accepts a valid scripted plan through EOS. Before a GPU run,
`drafter/tools/check_outlines_compatibility.py` repeats the Outlines check with the serving tokenizer, and
`drafter/tools/check_xgrammar_compatibility.py` now accepts an R1 v3 request.

The request for the original execution is `evaluation/m4_20261127/integration/DRAFTER_R1V3_REQUEST.json`, rebuilt
and checked by `python -m evaluation.m4_20261127.integration.build_r1v3_request --check`. With the current package
no record is v3-citable and no assessment is admitted, so a run on it leaves every object `insufficient_information`.

**Not yet covered.** The mock driver still produces the v2 envelope only, and the hand-off to the Critic and
Revision Agent depends on their R1 v3 support.

Tests: `drafter/tests/test_r1v3_generation.py` (scripted model replies: the real package leaves every object
unresolved, a cited v2 record fails the plan schema, an invalid request calls no model, the admitted fixture gets
host-backed outcomes, a plan that drops available evidence is rejected) and `drafter/tests/test_r1v3_profile.py`
(the real package, the frozen-file binding, and rejection of a wrong
source hash, a requirement or roster mismatch, a changed window, a wrong checker hash, loaded reference answers,
human labels, a claimed admission without a contract, a missing or ineligible citation, a non-admitted assessment,
an unbacked or mismatched outcome, citations that are not the graph's Solution nodes, a Solution that does not
carry its record, reasoning not bound to its run, and a non-aggregated execution outcome). A synthetic fixture with a test-only
admission contract exercises the accepted definite path; it is not evidence or an admission.
