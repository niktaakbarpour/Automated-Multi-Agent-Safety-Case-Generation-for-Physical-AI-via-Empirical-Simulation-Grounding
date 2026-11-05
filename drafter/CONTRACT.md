# Drafter foundation contract 0.1.0

This foundation defines an example input and the future output interface. It does
not call an LLM, generate an argument, run physical checking, or provide a complete
Phase 5 consumer adapter. The example is a software contract fixture containing an
unchanged archived development registry export. The exported observations retain
their original provenance; the fixture label does not turn them into synthetic
measurements or newly verified source values.

## Authoritative contracts and versions

- R1 requirement: `R1` version `2.0.0`.
- R1 configuration schema: `requirements/r1_generalized_v2/R1_V2_CONFIG_SCHEMA.json`,
  version `2.0.1`. This is distinct from the requirement version.
- Registry records: `evaluation/r1_v4/evidence_registry_gsn/registry_record.schema.json`
  and `models.Record`, version `1.0.0`.
- GSN graphs: `evaluation/r1_v4/evidence_registry_gsn/gsn_graph.schema.json` and
  `gsn.Graph`, version `1.0.0`.
- Drafter wrappers: `drafter-request/0.1.0` and `draft-argument/0.1.0`.

The JSON schemas reference the repository's existing contracts rather than copying
their definitions. Resolve external references locally relative to each schema
file. Request and output schemas live in `drafter/schemas/`. Schema validation
does not replace the upstream semantic validators or the cross-field rules below.

## Request: DraftRequest

`schemas/draft_request.schema.json` accepts only `test_fixture=true` and
`usage=contract_fixture`. It does not authorize empirical use.

| Field | Meaning |
| --- | --- |
| `request_id` | Stable identity for this input. |
| `requirement_configuration` | Complete R1 configuration, including its manifest, object/surface mapping and original validation status. |
| `requirement_configuration_sha256` | Digest of the complete derived configuration. |
| `target_execution` | Exact execution, benchmark, task and checkpoint; variant is null when unavailable, never guessed. |
| `monitoring_scope` | Explicit fixture interval, clock/domain, inclusive bounds and boundary provenance. `fixture_declared` is not verified policy/terminal boundary resolution. |
| `evidence_package` | Original registry export with all records and their unchanged content-derived IDs. |
| `evidence_package_sha256` | Digest binding that complete export. |
| `evidence_handling` | Archived-export origin, no source replay, disabled empirical admission, and the partition between graph-eligible and context-only record IDs. |
| `checker_context` | `not_available` with an empty assessment list. No caller-provided checker authority is accepted. |
| `safety_knowledge`, `related_cases` | Empty in this version; later scoped contracts can add these capabilities explicitly. |
| `retrieval_context` | Requested objects/interval, known missing coverage and limitations. `not_evaluated` is not a completeness verdict. |
| `input_provenance` | Pinned repository revision, original source-artifact identities and an explicit configuration derivation. |
| `limitations` | Standalone caveats about the fixture, archived sources and unassessed physical claims. |

Both admission and safety-verification flags are constant false. Unknown fields
are rejected throughout the new envelope. Upstream configuration and graph schemas
retain their own rules for their nested fields.

### Immutable input bindings

Use `evaluation.r1_v4.provenance.canonical` and `digest` for canonical JSON hashes.
Canonical content hashes are distinct from SHA-256 of original file bytes and from
Git's SHA-1 blob identities. `source_artifacts` records all three under explicit
names. Paths are repository-relative; the pinned revision identifies their bytes.

The fixture derives a configuration from the pinned example using a list of JSON
Pointer changes, each with exact `before` and `after` values. Keep the original
configuration and evidence export unchanged. Replay the changes and require exact
equality with the embedded configuration, then verify its digest. This is an
auditable fixture derivation, not approval or physical validation of the derived
configuration.

### Required semantic checks

These are additional to JSON-schema validation:

1. Parse finite JSON and reject duplicate keys. Resolve and validate the complete
   existing R1 configuration, preserving illustrative/unresolved manifest status.
2. Verify input artifact identities and canonical configuration/export digests.
   Validate every registry record with the original `Record.parse`, including its
   content-derived ID and permitted metadata semantics. This validates the archived
   envelope; source files on Nikta's `/disk` environment have not been replayed.
3. Bind execution, task, benchmark and checkpoint to the configuration and supplied
   records. A null variant means unknown; it grants no cross-variant equivalence.
4. Require finite ordered intervals, correct domain/clock, explicit fixture bounds,
   the complete configured protected-object list and valid surface mappings.
   Do not change the monitoring interval to fit available observations.
5. Require graph-eligible and context-only ID lists to be disjoint, duplicate-free
   and together equal the original export's record IDs. A graph-eligible record must
   have compatible requirement/execution/object scope, matching clock/domain and an
   interval contained in the declared monitoring scope. This label means eligible
   as a scoped observation reference, not sufficient to establish a physical claim.
6. Keep excluded observations and attributed interpretations as context-only.
   Context-only records cannot be cited as solution nodes. Preserve gaps for every
   configured object and uncovered interval without interpreting absence as safety.
7. Keep checker assessments empty, all empirical-admission flags false and all
   physical outcomes unresolved. Unsupported or unavailable evidence remains
   explicit; it is not a negative result.

The foundation input validator may report schema/semantic success for this fixture.
That result never upgrades `illustrative_unvalidated`, establishes load-bearing
support, calibrates falls, authenticates unavailable producer binaries, or certifies
the execution.

## Future output: DraftArgument

`schemas/draft_argument.schema.json` defines a future output only. No generated
DraftArgument is delivered by this foundation.

The interface validator `validate_argument(argument, request)` checks a supplied
result against its validated input and the original graph/record contracts. These
are contract checks, not generation or scientific validation. Tests may construct
small graphs in memory to exercise these rules without delivering a generated
argument. This archived fixture profile has a nonempty protected-object set;
accepted results require nonempty graphs and an explicit complete object vector.
Handling generalized empty scope needs an explicit later contract rather than an
accepted empty draft.

- `request_id` and the request/configuration/export digests bind a result to its
  exact input; they must match the validated request.
- `generation_status` is `accepted`, `rejected` or `failed`. Accepted means a draft
  passed input, graph and reference checks, not that a safety claim was accepted.
- `argument_bundle` is null on rejection/failure. On acceptance it contains
  `execution_id`, the complete `protected_objects`, one `{object_id, graph}` entry
  per configured object, and `execution_conclusion` with a full object-outcome map.
- Each graph uses the existing GSN schema and must pass actual
  `Graph.validate(registry)`. Every solution cites an original graph-eligible `ev:`
  ID and retains exactly matching source path/hash/selector, object, requirement,
  interval, clock, domain, origin and status. Existing GSN rules prohibit
  cross-object edges; aggregate across graphs in the wrapper.
- In this profile every physical goal remains unresolved and every object/execution
  outcome is `insufficient_information`. Configured objects without evidence still
  receive graph entries. More capable checker-backed output needs a later contract
  and an enforced admission boundary, not a new caller flag.
- `summary`, `limitations`, and structured `diagnostics` make uncertainty and failures
  inspectable. `validation` separately reports input schema/semantics, output schema,
  graph semantics and evidence-reference checks. Physical sufficiency is always
  `not_assessed`.
- Accepted output requires actual local-LLM run identity, model ID, prompt version
  and digest, and raw-output digest. A missing model revision remains null instead
  of being invented. Rejected/failed results may identify a backend as `not_run`.
  No such generation trace is fabricated in this foundation.

The execution wrapper follows the current Critic's graph/object structure. A future
adapter must supply its surrounding request fields from the same original package.
Passing this shape does not establish that the audited Critic has enforced its own
input contracts or evidence authority. Do not rely on its present acceptance as a
validation oracle.

## Phase 5 integration boundary

The production `phase5-structured-1.0.0` route has grouped obligations and items,
original IDs, `evidence-citation:` IDs, exact source references, assurance,
interpretation conditions and distinct noncomplete statuses. Those groups are not
registry records. This request profile accepts a registry export only; passing a
Phase 5 bundle in its place must fail validation.

A future lossless adapter must retain the original structured request/response,
release binding, obligation identities, fulfilled/missing statuses, source selectors
and hashes, scope, original IDs, canonical citations and interpretation limitations.
It must define a verified mapping into graph-ready registry records without
renaming citations to `ev:` or inventing object/time attribution. The present
fixture does not claim production Phase 5 integration.

Retrieval completeness is relative to mandatory explicit obligations. It does not
establish R1 satisfaction. Current source integrity is distinct from historical
producer attestation, and available measurements are distinct from admitted
physical events. All these boundaries remain unchanged.
