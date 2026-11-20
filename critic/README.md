# Critic Agent (midpoint prototype)

The Critic reviews a Drafter's GSN-style argument for one LIBERO execution and returns structured, machine-readable criticism. It points out unsupported claims, wrong or missing evidence, missing objects, ignored uncertainty and conclusions that break the R1 aggregation rules.

It does not decide whether the robot was safe, does not write a new argument, does not touch the evidence database and does not invent observations. A report with no findings only means this Critic found nothing wrong within the evidence it was given.

## How it works

```
review request (one execution)
  ├─ 1. validation          deterministic, always run
  │     JSON schemas, Graph.validate and Record.validate rules, evidence references,
  │     record hashes, bundle coverage, checker results, Phase 5 retrieval bundles;
  │     any failure rejects the input
  ├─ 2. rule-based review   deterministic, always run
  │     claimed outcomes vs admitted checker results, gaps and missing retrieval
  │     obligations, R1 execution aggregation
  └─ 3. LLM review          optional, only for valid input; any OpenAI-compatible server (vLLM on Hestia)
        wording-level problems the rules cannot see (e.g. "height dropped so it fell",
        "certified safe"); every finding is screened and anything citing an unknown
        node or evidence ID is rejected (details below)
  → CriticReport (JSON)
```

Every criticism records its category (C01–C13 from the handoff), severity, affected object and node, explanation, evidence IDs, suggested fix, and whether it came from a rule or the LLM. LLM findings always need human review and are never blocking on their own.

## Input: one bundle per execution

`schemas/critic_request.schema.json`, following the handoff's sections A–E:

- **evaluation_context**: requirement, execution, task, the full R1 v2 configuration (`r1_configuration`) and its hash, and the protected objects, surfaces and monitored interval copied from that configuration (never hardcoded), with `boundary_provenance` for boundaries that are resolved from recorded data.
- **argument_bundle**: one unchanged GSN 1.0.0 graph per protected object, plus the execution conclusion (claimed per-object outcomes and the execution outcome). Objects that are non-applicable or unknown are still included.
- **evidence_package**: registry records 1.0.0, exported as they are.
- **checker_assessments**: R1 checker results, each `{configuration, result, input_bundle}`: the output of `evaluation/r1_v4/runtime.py:assess` exactly as the checker wrote it, plus the R1 configuration and original inline input bundle it ran on (see below). An empty list means "not available", never "no violation".
- **structured_evidence** (optional): Phase 5 structured retrieval, each entry the exact request sent to the release and the exact bundle it returned (see below).
- **retrieval_context**: what was requested, gaps, and which records come from related executions.

The output schema is `schemas/critic_report.schema.json`.

## Validation before review

Before anything is reviewed, the Critic checks that the input is well formed, using the team's own contracts:

- the request against `schemas/critic_request.schema.json`, each graph against `gsn_graph.schema.json` and each evidence record against `registry_record.schema.json`. `schema.py` is a small standard-library JSON Schema validator that implements exactly the keywords these schemas use and raises on any other keyword, so no rule is skipped silently. A test compares it with the `jsonschema` package where that is installed;
- the whole request is standard JSON (`REQ-JSON`): the team hashes and validates with canonical JSON, which has no NaN or Infinity. Python's `json` module reads those tokens anyway, so the Critic looks for them explicitly. An integer beyond the range of a double (such as `10**1000`) is valid JSON, but the team's interval check crashes on it and past 4,300 digits Python cannot even print it, so it stops the review before anything else reads the request;
- every rule of `gsn.py:Graph.validate`, including its final canonical serialization (`GSN-CANONICAL`, so a NaN in a node's opaque provenance is refused as it is there), and of `models.py:Record.validate` (except Record.validate's symlink check, which needs the filesystem). Node and record requirement IDs and versions must match the review;
- synthetic data must be marked: a record with a `/synthetic/` source path or `provenance.synthetic` is only accepted in a request with `test_fixture: true`, and only such a request may use `/synthetic/` instead of the approved source root;
- the R1 configuration and the context's binding to it (below);
- the bundle covers the configured objects, checker results pass the admission rules below, and Phase 5 structured-retrieval bundles pass theirs (see Phase 5 structured retrieval).

### Binding to the R1 configuration

The request carries the full R1 v2 configuration. `checks.check_configuration` validates it the way `evaluation/r1_v4/configuration.py:validate_configuration` does (its schema and all 12 of its semantic rules, under the same names) and checks `r1_configuration_sha256`. Then the context must be exactly that configuration's:

- the same protected objects and support surfaces. A shorter list in the context and bundle is an unauthorized reduction (`CONFIG-OBJECTS`); a different configuration (three objects, five LIBERO objects, one object) is fine, because it is the configuration that decides;
- the same requirement, benchmark and, where the configuration sets them, execution, task and policy checkpoint. The team's configurations are templates with `execution_id: null`, so they apply to any execution of their task;
- the monitored interval on the configuration's clock (`saved_frame` is the GSN `frame` / `saved_frame_index` clock; `simulator_time` has no agreed GSN clock yet and is refused). An explicit boundary must equal the interval. A boundary resolved from recorded data (`recorded_first_policy_boundary`, `terminal_recorded_snapshot`) needs `boundary_provenance`: the frame it resolved to and the source path, hash and selector it was read from.

A configuration with no protected objects is valid: the execution is an empty scope, aggregates to `not_applicable`, is marked `empty_scope` in the summary, and a no-violation claim for it is flagged, because an empty scope is never a pass.

Every criticism has a `phase`. A `validation` criticism means the input itself is invalid: all of them are blocking, the LLM is not called, and the report's `review_status` is `rejected_invalid_input`. Its criticisms are the diagnostics, not a completed critique. A `review` criticism is a critique of a well-formed argument; these include two argument defects that `Graph.validate` accepts: a goal or strategy with no support, and support resting on an unusable record.

`review_status` is one of `completed`, `completed_llm_failed` (the rule-based review is complete but the model step failed), `rejected_invalid_input` and `internal_error` (the report failed its own schema, which is checked before it is returned, or the Critic itself raised an exception; `status_detail` says why). `review()` never raises: an exception inside the Critic is a Critic bug and comes back as an `internal_error` report, and the tests and fuzzing check that no input reaches that path. The command line exits with 0 (completed, nothing blocking), 1 (completed, blocking criticisms), 3 (input rejected), 4 (LLM step failed), 5 (internal error) or 6 (request file unreadable); 2 is the standard code for a bad command line.

One gap found in the team's code while testing: `Record.validate` alone accepts a string or an object where a list belongs (for example `"uncertainty": "frame"`), because it only iterates the value. `registry_record.schema.json` forbids this and the Critic enforces both.

## Checker results: when the Critic uses one

Checker entries must carry the original `input_bundle` with exactly `configuration`, `artifacts`, and `evidence`. The Critic verifies `provenance.input_hash`, configuration identity, and replays `evaluation.r1_v4.runtime.assess` on a deep copy. The complete result must equal the replay, including admission/rejection reasons, dependency closures, coverage, applicability, conflicts and provenance (`CHK-REPLAY`). This reuses the checker rather than duplicating its semantic rules. Inline artifacts are hash-resolved by its analytical registry; arbitrary external paths are not opened. This establishes consistency of a synthetic analytical result, not independent producer authentication or empirical validity.

**Migration:** legacy `{configuration, result}` entries can be parsed but cannot be admitted without their original input. Supply the original bundle; do not reconstruct missing observations from the result. Missing replay data or dependencies fail closed with a diagnostic before any LLM call. Existing case D/E fixtures carry the source input. The request version remains 0.3.0 (additive field), report version 0.4.0; consumers must account for the stricter admission requirement.

A label written by the caller is never enough. The Critic reads the R1 checker's own output contract (`evaluation/r1_v4/assessment.schema.json`) and `assessments.py` uses an object assessment from it only if:

- the result passes the checker's own output schema, `assessment.schema.json`, in full (`CHK-SCHEMA`; any failure refuses the whole result, since it is not what the checker writes), and it has every field `runtime.assess` writes for a valid, assessed run: R1 2.0.0, checker `r1-v4-restricted-infrastructure` 4.0.0a1, no physical safety conclusion, empirical profiles off, and the admission lists (`admitted_evidence_ids`, `rejected_evidence`, `evidence_admission`, `conflicts`); the Critic's own field and value checks stay behind the schema as a second line;
- `assessment_hash` matches the result's content and `configuration_hash` matches the supplied configuration, so neither was edited after the checker ran;
- the checker ran on the review's own R1 configuration (its content hash is `r1_configuration_sha256`), so objects, surfaces and the monitored interval match by construction; the result is for this requirement, execution and task, and a result from a template configuration (no execution) is not tied to this execution and is refused;
- the checker admitted the run itself (`provenance.admitted_purpose` is set);
- the admission ledger is one the checker writes (`CHK-LEDGER`, following `admission.py` and `runtime.py`): one admission row per evidence record; `admitted_evidence_ids` are exactly the verified rows and `rejected_evidence` exactly the others; a verified row has no reasons, comes from a record declared verified, and everything in its dependency closure is verified; a verified record lies inside the monitored interval, uses the configuration's clock and frame, is for this execution and a configured object (or `*`), and depends only on its own object's records or `*`; no listed conflict joins two verified records; `study_eligibility` follows the objects' `scope_mismatch` flags;
- the object is configured, the assessment is for this execution and the object's mapped surfaces, and it passes the consistency rules of `aggregate.py` and `applicability.py`: violation or no-violation need `applicable`, no-violation needs no missing coverage, not-applicable needs `not_applicable`; an applicable object has a violation outcome exactly when the checker admitted a violation record for it; `scope_mismatch` is set exactly when it admitted an absence record, and then only with a not-applicable or invalid-contract result and pending study eligibility;
- its evidence IDs are exactly the admitted evidence records of that object, as the checker writes them;
- every other object assessment in the same result passes too: they come from one run under one hash, so one forged object assessment makes the whole result unusable (`CHK-RESULT`);
- it is admitted for this request. The checker only produces synthetic analytical output today and empirical admission is off for the whole project, so results are used only when `test_fixture` is true, and findings call them synthetic test-fixture assessments. A result not marked synthetic is refused, because there is no empirical route yet.

A result or object assessment that fails any of these gets a blocking `CHK-*` finding and is ignored: it can neither support nor contradict a claim, and the LLM is told it was not admitted and cannot cite it. Every object assessment gets a row in the report's `checker_admission` list, with the ID `ca:<assessment_hash>:<object_id>`. Hashes alone do not authenticate the producer. The repaired consumer additionally requires the original hash-bound input and exact authoritative checker replay, so internally plausible ledger edits cannot substitute for an admitted result. That is one more reason synthetic results stay limited to test fixtures. An admitted assessment covers the review's monitored interval; its cited evidence is checked to lie inside it.

The R1 configuration has no variant field, so a checker result is tied to a variant only through its execution ID.

## How a claimed outcome is judged

Each object's claimed outcome is compared with the admitted checker assessments for that object (`checks.py:_check_object_outcome`, following `FORMAL_SEMANTICS.md`):

| Admitted assessments | Claim | Finding |
|---|---|---|
| none | anything but insufficient_information | `CONCL-UNSUPPORTED` (C06, or C08 for not_applicable) |
| one reports a violation | insufficient_information | `CONCL-HIDES-VIOLATION` (C07) |
| one reports a violation | no violation, not applicable or invalid contract | `CONCL-CONTRADICTION` (C07): an admissible violation is not overridden by other results |
| they conflict: two different definite results (violation, no violation, not applicable), or an invalid contract next to a definite result | anything, except insufficient_information when none reports a violation | `CONCL-CONFLICT` (C13), citing every assessment; both records are kept |
| the result is insufficient or invalid contract | a definite outcome | `CONCL-NOT-ESTABLISHED` (C06, or C08): a gap, not a contradiction |
| the result differs on applicability | anything but insufficient_information | `CONCL-APPLICABILITY` (C08) |
| the result is another definite outcome | anything but insufficient_information | `CONCL-CONTRADICTION` (C07) |
| the result is the same outcome | the same outcome, or insufficient_information | none |

Rows combine: when assessments conflict and one reports a violation, both the conflict row and the violation row apply. An insufficient_information assessment next to a definite one is a gap, not a conflict, so the definite one is used. An insufficient_information claim is never criticised just for being cautious. Conflicts, assessments that differ only by being insufficient, incomplete checker evidence and checker uncertainty are also listed in `unresolved_concerns`. `test_every_claim_against_every_checker_result` checks every claim against every single result and every pair of different results.

The execution outcome is aggregated over every configured object: a missing or invalid object outcome counts as `insufficient_information`, never dropped. The summary gives two aggregates. `recomputed_execution_outcome` uses the claims as stated, and the stated execution outcome must equal it. `accepted_execution_outcome` counts every object with a blocking criticism as `insufficient_information` (and is null when the input was rejected); it is the most this review accepts from the draft, not a safety verdict.

Retrieval gaps only matter for a no-violation claim, and only if they are for that object, overlap the monitored interval and are not optional evidence (`velocity` and `task_instruction` are optional in the R1 configuration schema). A gap with a malformed interval counts. If an admitted checker assessment supports the no-violation claim, a relevant gap is a medium, non-blocking finding for human review, because a gap in the Drafter's package does not by itself invalidate the checker's result. Without that support it is blocking. Every gap, relevant or not, is listed in `unresolved_concerns`.

## Unqualified safety claims (Critic 0.5.0)

R1 has no outcome that says an object or the robot is safe. The strongest negative outcome,
`no_violation_observed_within_validated_coverage`, is limited to the validated coverage of an admitted checker
assessment, and `insufficient_information` is never safety. `claims.py` (rule
`absolute-safety-claim/1.0.0`) flags any node or execution statement that claims safety outright:
an assurance word with a safety word ("guaranteed physically safe", "certified safe"), an absolute phrase
("completely safe", "zero risk") or a plain assertion ("was safe", "remained safe"). A clause with a negation before
the match ("does not establish safety", "no guarantee that it was safe") is not flagged, and a consequence after a
comma ("..., so it was safe") is checked as its own clause.

The finding is `CLAIM-ABSOLUTE-SAFETY`, category C12, review phase, blocking, with an evidence request for an
admitted checker assessment. It never declares a violation and never changes an outcome. It is a word-level rule, not
a semantic classifier, so it asks for human review. It was added because the integrated Qwen review missed the
injected "guaranteed physically safe" goal in the one-pass negative control
(`integration/END_TO_END_QWEN_INTEGRATION_REPORT.md`, section 10). Since the rule raises that objection, a model C12
on the same node is now rejected as a duplicate. Tests: `tests/test_m4_claims.py`.

Version 0.5.0 differs from 0.4.0 only by this rule: the prompt (v5), schemas and model screening are unchanged.

## Phase 5 structured retrieval

The final RAG release (`evaluation/r1_v4/rag_evidence_database/final_phase5_release`, `phase5-structured-1.0.0`) returns a bundle per structured request: groups per obligation, items with their original IDs, source hashes and selectors, `evidence-citation:` IDs, a completeness status, missing obligations, conditional assumptions, assurance and limitations. Bundle items are not registry records, and a missing obligation is not a Critic gap, so the Critic does not map one onto the other. It takes the bundle whole, in `structured_evidence`, next to the request that produced it, as the release's `DOWNSTREAM_HANDOFF.md` asks.

`retrieval.py` checks every entry before anything uses it, and refuses the whole input (`RET-*`, validation phase) unless:

- the bundle matches the release's `EVIDENCE_BUNDLE_SCHEMA.json` and `schemas/phase5_bundle_consumer.schema.json`, which spells out the groups, items, citation basis, validation and assurance parts the release schema leaves open, and the release's schema files still have the hashes the Critic pinned (`contract.py`, checked against the release's `config.py` by a test);
- the bundle, the request and every obligation and item are for this review's execution, task and variant. The request must state all three; a bundle for a nearby execution or variant is never a substitute;
- `query_id` is the hash of the supplied request and every group is that request's obligation, in order, with the right digest, family, mandatory flag and interpretation;
- `missing_obligations`, `conditional_assumptions`, the assurance flags and the completeness status follow from the groups and the independent validation exactly as `api.py` derives them, so a dropped missing obligation, a dropped assumption or an upgraded status is caught;
- a bundle that did not pass independent validation (INVALID SCOPE, UNSUPPORTED, UNAVAILABLE, UNVERIFIED PLAN) returns no evidence, and a request the release would refuse (bad schema, duplicate IDs, unregistered family or field, wrong selector, changed assurance, crossing scope) is not reported as evaluated;
- every item is source-verified in a validated bundle (and so is every sample), lies inside its obligation's frame window, and has the identity and origin the release gives it: a channel item is its own original channel record, a recorded-metadata item's ID is the hash of its source path, hash and selector. A channel group marked AVAILABLE covers every requested frame, and its units and frames agree with its interpretation properties;
- no item value turns an observation into a physical event (`physical_support_inferred`, `physical_contact_or_support_inferred`, `synchronized_physical_instant` and `same_physical_instant` stay false), and a channel group lists exactly the required properties its evidence marks CONDITIONAL, so a conditional interpretation cannot be passed off as verified;
- the release's four limitations are kept, and every `evidence-citation:` ID is the hash of a `citation_basis` that describes this item under its obligation and the pinned database.

An admitted bundle can only add concerns, never support a claim:

- a mandatory obligation that is missing (any status other than AVAILABLE, or AVAILABLE but not accepted by the independent validation) makes a no-violation claim `CONCL-OBLIGATION-MISSING` (C04) when it is about that object or names no object, and its window overlaps the monitored interval or cannot be placed on the frame clock (simulator labels, no window). Under an admitted no-violation checker result it is medium and needs human review; without one it is blocking;
- every status, missing obligation (mandatory or optional) and conditional assumption is kept in the report's `structured_retrieval` list and in `unresolved_concerns`; `retrieval_context` cannot claim completeness over a bundle that is not complete;
- nothing in a bundle is a checker assessment or a physical event. A COMPLETE bundle covers the request's explicit mandatory obligations only, not complete R1 observations, and leaves a no-violation claim without a checker result unsupported.

GSN 1.0.0 solution nodes keep citing registry records, as `Graph.validate` requires. The report links a solution to a citation when the solution's registry record is one of the item's `original_evidence_ids`, and only after checking that crosswalk (`RET-CROSSWALK`): an original ID that names a record in the evidence package must be one the release itself would list for that item. `retrieval_remediation/bundle.py` lists, for this execution, `object_identity` records of the obligation's object for a geometry item, `execution_metadata` records for execution metadata, and `contact` or `camera_reference` records overlapping the requested frames (of the obligation's object, when it names one) for contact and camera references; every other family lists none. A bundle that lists anything else, such as another object's pose record, is refused, because the link it would create is false. A solution that cites an `evidence-citation:`, `channel:` or `source-ref:` ID is rejected with a message saying so. If the team wants solutions to cite citations directly, that is a change to the GSN contract first. The model step does not see bundles, and a model finding that cites a citation is rejected as unknown evidence.

The Critic recomputes the hashes but cannot open the database or the sources, so a bundle is checked for consistency, not authenticated. The recorded values themselves are not covered by the citation and cannot be checked here. The crosswalk check uses only the registry records in the package: it shows that a link is one the release would make, not that the database holds that record, and an original ID that is not in the package is left unchecked and links nothing. The release's code needs its database on Hestia, so the test bundles are assembled by the release's own bundle-building code (`StructuredRetriever.response`, the citation loop and the status rule, taken from `api.py` with `ast` by `cases/phase5.py`) on synthetic groups.

## What the Critic accepts from the model

The model step can never break or silently weaken a review (`llm.run`). Building the prompt, the call, parsing and screening all run inside one error boundary. A reply that cannot be used (no JSON, `findings` not a list, an empty or non-text reply, a timeout) gives `review_status: completed_llm_failed` with the error, and the rule-based findings stay; it is never turned into an empty critique.

Each model finding is then checked on its own, and rejected (kept under `rejected_llm_findings` with the reason) unless:

- it matches the finding format exactly (`llm.FINDING_SCHEMA`: the listed keys only, a known category and severity, non-empty explanation and suggested action, string or null IDs, a list of distinct evidence IDs);
- its category is one the model may raise. C01, C02, C03, C04 and C11 are decided by the rule-based checks only; from a model they would be unsupported;
- its object is configured and its node exists in that object's graph. A finding with a node but no object must name a node that exists in exactly one graph, and is then about that graph's object (node IDs such as `G1` repeat across the object graphs, so `object_id: null` with `G1` has no unique target);
- every evidence ID it cites is in the package, about the finding's object (named, or fixed by its node) and about the execution under review; a cited registry record must also be on the review's clock and overlap the monitored interval, and, when the finding names a node with a temporal scope, be on that node's clock and overlap its interval;
- a C07 contradiction names an object and cites an admitted checker assessment for that object;
- a cautious structured outcome never exempts contradictory prose from C09. Against an unresolved conclusion, a complete statement quotation anchors an objection; explicit assertive wording also keeps it for review. Unanchored, ambiguous objections are retained with `C09_UNRESOLVED` in `rejected_llm_findings` **and** `unresolved_concerns`, rather than being declared false or promoted to established criticisms. Consumers must surface these unresolved concerns for human review. The positive wording cues only retain proposals; they do not establish semantic correctness. Accepted findings remain nonblocking, human-review-required proposals;
- it does not repeat a rule-based finding.

Accepted findings are still `llm_proposed`, need human review and never block on their own; the checks above make them grounded in the supplied evidence, not correct.

Every model call leaves a trace in `report.llm`: the prompt version and the sha256 of the prompt file, of the exact messages sent (after any model-card adjustment), of the review request and of the full reply; the effective settings (base URL without any user:password, model, temperature, token limit, extra parameters, prompt adjustments, accepted model names; never the API key); the raw reply (cut at 65,536 characters, flagged when cut); the server's own account of the reply (`response`: id, the model it answered as, finish reason, token usage); and how many findings were accepted and rejected. A parseable reply is not proof of a complete one, so a reply that did not finish (`finish_reason` other than `stop`, for example `length` at the token limit) or came from another model is not used, and the review is `completed_llm_failed`.

## Run it

From the repository root. Full runtime validation now requires Python 3.10+ and `pip install -r critic/requirements.txt` (jsonschema 4.19.1). Repair verification uses Python 3.12 on Hestia. The older annotation-loading test helpers are not a production Python 3.9 compatibility guarantee.

The tests use the team's own `Graph.validate`, `Record.parse`, `validate_configuration`, and R1 checker as references. Install `critic/requirements-test.txt`, which includes the runtime jsonschema pin. The repair was actually verified on Hestia Python 3.12; other Python versions are not claimed verified by this run. Historical annotation-loading helpers remain for older oracle tests. Strict mode turns a skipped oracle into a failure. Authoritative replay dependencies are required at runtime; missing dependencies never authorize admission.

```bash
# tests (no GPU, no network); CRITIC_STRICT_TESTS=1 fails instead of skipping
pip install -r critic/requirements-test.txt
CRITIC_STRICT_TESTS=1 python3 -m unittest discover -s critic/tests -t . -v

# rule-based review of one case
python3 -m critic --request critic/cases/case_a_unsupported_claim.json

# full review with a model served by vLLM
vllm serve openai/gpt-oss-20b --port 8000
python3 -m critic --request critic/cases/case_a_unsupported_claim.json \
  --backend openai --base-url http://localhost:8000/v1 --model openai/gpt-oss-20b \
  --out critic/examples/case_a.report.gpt-oss-20b.json
```

From Python:

```python
from critic import review
from critic.llm import OpenAICompatibleLLM
report = review(request_dict, OpenAICompatibleLLM(base_url='http://localhost:8000/v1', model='openai/gpt-oss-20b'))
```

The model is a setting. Sampling follows each model's card (`llm.MODEL_PRESETS`). The server's reply must say it finished (`finish_reason: stop`) and name the requested model; if the server answers under another name (a `--served-model-name`, a checkpoint path), pass that name with `--accept-model NAME` (`accepted_models=[...]` in Python). Anything else gives `completed_llm_failed`, with the server's response id, model, finish reason and token usage kept in `report.llm.response`. The model comparison and the Hestia commands are in [MODEL_COMPARISON.md](MODEL_COMPARISON.md).

## The five test cases

All synthetic and marked `test_fixture: true`. Cases A to C use the three-object example configuration (`B_SYNTHETIC_THREE_OBJECTS.json`) so nothing depends on the original five LIBERO objects. Cases D and E use the R1 checker's own fixture (`evaluation/r1_v4/synthetic/three_object_violation.json`) and the checker's real output for it, stored in `cases/checker_outputs/`. Run `python3 -m critic.cases.build_cases` to regenerate the cases, and add `--refresh-checker-output` to re-run the checker first (it needs Python 3.10+ and `jsonschema`, as pinned in `evaluation/r1_v4/requirements.txt`).

| Case | What the mock Drafter did | Rule-based result |
|---|---|---|
| A: unsupported safety claim | Claims R1 satisfied for all objects from poses and contacts, with no checker assessment | 3 blocking C06 findings, one per object, each with an evidence request |
| B: missing or wrong evidence | Cites an evidence ID that was never retrieved, uses another execution's record as proof, leaves out one configured object | Input rejected (`rejected_invalid_input`), no model review; diagnostics C02 (widget_a), C03 (vial_b) and C04 (carton_c) |
| C: correct unresolved argument | Says R1 cannot be determined and keeps support and fall questions open | No findings, not blocked |
| D: claim hides a checker result | Leaves object_00 unresolved although the (synthetic) checker result reports a violation; its other two claims match the checker | Blocking C07 for object_00; the other two claims are supported |
| E: claim over a partial structured retrieval | Claims match the checker; its Phase 5 bundle (PARTIAL) left a mandatory contact obligation for object_01 unavailable | One medium C04 for object_01 that needs human review, not blocking; the bundle's statuses and missing obligations are listed, and its object_00 contact citations are linked to object_00's solution E2 through the contact record the release lists for them |

Reports are in `examples/`. `case_a…scripted_llm_demo.json` shows the LLM step with a **hand-written** reply (not a real model). It contains two valid findings plus one with an invented evidence ID and one with a made-up node, and the Critic rejects those two. Real model outputs will be added after the Hestia run.

## Tests

206 tests in strict mode as of Critic 0.5.0 (189 in 0.4.0, plus 17 in `tests/test_m4_claims.py`). The
heading of this section said 160 before Nov 18; that number was out of date.

- the five cases produce exactly the expected findings, and Case C gets none
- requests, graphs, records and reports validate against their JSON schemas
- validation before review (audit I3, I4, I9): the audit's probes (required request fields removed; node and record requirement IDs changed to R999 with recomputed record IDs; a dangling edge) are all rejected with `rejected_invalid_input` and the model is not called; synthetic records need `test_fixture`; every validation criticism is blocking; duplicate edges are blocking; an unsupported goal is a blocking review criticism; a model failure gives `completed_llm_failed`; a report that fails its own schema gives `internal_error`; every command-line exit code
- **agreement with the original GSN validator:** 14 kinds of broken graph that `gsn.py:Graph.validate` rejects are all flagged by the Critic as validation criticisms and reject the whole review, and the real `demo/GRAPH.json` passes both
- **agreement with the original record validator:** the team's real demo records pass both; 23 single-rule breaks and 400 random corruptions (with recomputed IDs, so the hash cannot give them away) are rejected by the Critic exactly when `Record.parse` or the registry schema rejects them
- the built-in schema validator uses only supported keywords in all nine schemas, follows JSON rules (true is not 1, 1.0 is an integer), and gives the same verdict as `jsonschema` on the cases and 2,700 corrupted documents
- evidence IDs reproduce the registry's content hashes; a tampered record is caught
- configurable R1: an extra configured object is reported missing; fewer objects are not demanded
- checker admission (audit I1): real checker output is admitted in a fixture; a self-asserted `validated_checker` label, a re-hashed result for the wrong requirement, task or interval, synthetic output in a non-fixture request, output not marked synthetic, an edited result or configuration, a run the checker refused, a configuration with other objects, surfaces, execution or interval boundaries, a wrong clock or checker version, object assessments with unknown, wrong-object or unadmitted evidence, broken consistency rules, wrong object, execution, requirement, surface or status, and duplicates are all refused and never produce a C07. Each of these checks was switched off in turn to confirm a test fails without it
- the stored checker output is exactly what `runtime.assess` produces for its fixture (needs `jsonschema`, like the checker itself)
- the copied checker constants (required fields, fixed values, enums, checker version) match `evaluation/r1_v4/assessment.schema.json`
- conflicts and applicability (audit I2): the audit's probe (no-violation claims while one assessment reports a violation and another does not) is caught twice, as a contradiction and as a conflict; every row of the table above has a test, including insufficient and invalid-contract results giving C06/C08 rather than C07
- gaps (audit I11): gaps for other objects, outside the monitored interval or for optional evidence give no finding but stay listed; a relevant gap is non-blocking under an admitted no-violation result and blocking without one
- every conclusion finding and gap rule was switched off in turn to confirm a test fails without it
- R1 configuration (audit I6): all 12 semantic rules agree with `validate_configuration` by name on every example configuration and the checker fixture; an oracle against the real function (needs `jsonschema`) compares verdicts and rule names on 300 random corruptions too; the audit's probe (context and bundle reduced to one object) is rejected; configuration hash, scope, templates, surfaces, interval clock, explicit boundaries and boundary provenance are each checked; the real five-object LIBERO profile (names read from `A_LIBERO_FIVE_OBJECTS.json`) is reviewed with no findings and a dropped LIBERO object is caught; empty scope; full-vector aggregation; the accepted outcome
- R1 aggregation precedence, checker contradiction (C07), an "insufficient information" claim that hides a checker violation (C07), unsupported non-applicability (C08), related-case misuse (C11), no-violation claims over retrieval gaps (C04)
- model output (audit I5, I8, I10): the audit's probes (a list as the category; a C07 with no evidence) are handled; every field of a finding is type-checked (19 kinds of broken finding); unusable replies and failures inside prompt building, parsing or screening give `completed_llm_failed` with the rule findings kept; rule-only categories are refused; a C07 must cite an admitted assessment for its object; citations must match the finding's object and execution; the trace hashes match what was sent and received (checked against a local fake vLLM server), the API key never appears in the report, and a long reply is cut but hashed in full; every rejection rule and trace field was switched off in turn to confirm a test fails without it
- LLM screening: invented IDs/nodes, malformed findings and duplicates rejected; a broken or empty model reply does not break the review; the HTTP client works against a local fake vLLM server; credentials in the server URL are not recorded
- the model comparison runner (`compare_models.py`) works end to end against a fake vLLM server, skips Case B (rejected before the model step, so no model is asked) and keeps each call's trace
- Phase 5 structured retrieval (audit I7): Case E's bundle is admitted and kept whole; every status the release returns (complete, PARTIAL, UNAVAILABLE, UNSUPPORTED, INVALID SCOPE, including a request with 17 obligations, UNVERIFIED PLAN) is accepted and kept distinct; 53 kinds of tampering (edited or re-hashed citations, edited request, groups, missing obligations, assumptions, limitations, statuses, validation and assurance flags, another execution, task or variant, items outside their window, not source-verified, with another origin or identity, or promoted to a physical event, channel samples missing or with other units, experimental route, safety or empirical flags) and every field of the citation basis are caught; hidden conditional properties are caught; a bundle that failed validation returns nothing; a request the release refuses cannot return evidence; which missing obligations matter for a no-violation claim (object, window, simulator labels, timeless, optional); an AVAILABLE group the independent validation did not accept counts as missing; a complete bundle never supports a claim; solution links; a citation in a solution or a model finding is refused; a changed release is refused; the pinned constants match the release's `config.py` and schema hashes, and the Critic's hash function gives the same hashes as the release's (`provenance.digest`). Every RET check, refusal rule and review rule was switched off in turn to confirm a test fails without it
- test setup (audit I10): the team's modules load on Python 3.9 and do not read their annotations; `CRITIC_STRICT_TESTS=1` turns a missing oracle into a failure; the schema fallback rejects invalid documents
- **regressions for the second audit** (`AuditR2`, from `AUDIT_REPORT_2026-11-05_R2.md`):
  - R2-01: the auditor's five re-hashed forgeries (no `rejected_evidence`, a list as `assessment_manifest`, outcome `"safe"`, evidence or manifest version `999`) are refused with `CHK-SCHEMA`, the model is not called and the CLI exits 3; `jsonschema` with the original schema rejects the same five; and in 250 random re-hashed edits of the real result, nothing the original schema rejects is admitted
  - R2-02: the auditor's ledger forgeries (`evidence_admission` cleared, a cited dependency rejected but still listed as admitted or with its dependants still verified, cited evidence moved to `[10000, 10001]`, `scope_mismatch` set) and three more (another clock, a conflict between verified records, a violation outcome with no violation record) are refused before the model with CLI exit 3; 21 single-rule forgeries each trip their own rule, and each ledger and consistency rule was switched off in turn to confirm a test fails (27 mutations, none survive); in the other direction, the team's checker run on 300 generated bundles (random objects and states, random edits of validity, intervals, dependencies, conflicts, clocks and truth values; rejected rows, conflicts and absent objects all covered) is never refused
  - R2-03: the auditor's graph (NaN inside a node's opaque provenance, which `Graph.validate` refuses through its final canonical serialization) is refused with `GSN-CANONICAL` and `REQ-JSON`, before the model, both as a Python object and when read from JSON text; the same graph and one with `-Infinity` are part of the shared-validator agreement test; NaN or Infinity placed at 300 random places in the five cases is always refused before the model, and the report stays standard JSON
  - R2-04: the auditor's monitored-interval endpoint `10**1000` is refused with `REQ-JSON` before the model, through the API and the CLI (exit 3, report written); integers beyond a double (including one past Python's 4,300-digit limit) at 300 random places are always refused, never a crash; the schema validator still agrees with `jsonschema` that such integers are JSON integers; an exception inside the Critic gives an `internal_error` report and CLI exit 5; the random-corruption test now also uses `10**1000` and NaN and fails on any `internal_error`
  - R2-05: the auditor's scripted findings are rejected: a C05 citing a properly hashed record of the same object at `[10000, 10001]` (the control, a record inside the interval, is accepted), and `object_id: null` with the shared node `G1` citing another object's record; so is the real GPT-OSS-20B finding from the audit (node `D1`, in every graph, citing several objects' assessments); a node that exists in only one graph binds the finding to that object; a citation outside the cited node's interval, or on another clock, is rejected; each rule was switched off in turn to confirm a test fails
  - R2-06: the auditor's crosswalk forgery (the object_01 geometry item listing object_02's E1 record, citation unchanged) is refused with `RET-CROSSWALK` before the model, links nothing and exits 3; another object's record, the wrong measurement type, a record outside the frames, another execution, and a family the release gives no original IDs are each refused; Case E's own links follow the release's rule; the crosswalk table matches `bundle.py` (read with `ast`); each rule was switched off in turn to confirm a test fails
  - R2-07: against a local fake vLLM server, the auditor's two probes (a valid `{"findings": []}` with `finish_reason: length`, and a reply from `ANOTHER-MODEL`) give `completed_llm_failed` with the server metadata kept; so do `content_filter`, a missing finish reason or model, no choices, two choices and non-text content; an alias is accepted only when named (`--accept-model` on the CLI too); a normal reply keeps id, model, finish reason and usage; each check was switched off in turn to confirm a test fails
  - Case C's original unanchored C09 objections are not promoted; they remain explicit unresolved concerns. Contradictory prose at G1, U1, D1 or the execution conclusion is no longer exempted by an insufficient_information vector. Anchored or assertive-wording objections remain nonblocking proposals for human review.
- **never crashes on bad input:** broken requests and 800 randomly corrupted ones (200 of them inside the checker result, 200 inside the structured evidence) all come back as valid reports, never `internal_error`

## Limits (honest)

- Historical runs used prompt v3 (R2 audit) and v4 (PR18 audit). Prompt v5 repair verification, repeated model tests and the four genuine C09 counterexamples are documented separately in CRITIC_PR18_FIXES_AND_VERIFICATION_REPORT.md. Neither structural acceptance nor a small exploratory comparison establishes model reliability.
- The screening rules check that a model finding is grounded (its IDs, object, execution and time fit the package), not that its criticism is right; accepted findings stay non-blocking and need human review.
- Five synthetic cases cannot show research-level Critic quality.
- Phase 5 bundles are checked for consistency and their hashes recomputed, but not authenticated against the database. The test bundles are synthetic; the R2 audit ran real frozen bundles for one LIBERO execution through the Critic on Hestia (all five statuses, wrong variant refused), which is not universal compatibility. Links to GSN solutions are checked against the release's crosswalk rules using the package's records, not the database.
- Temporal coverage is checked at the level of declared intervals and retrieval gaps, not per measurement cell.
- Boundary provenance is checked for consistency, but the Critic cannot open the recorded source it names. `simulator_time` configurations are refused until the GSN graphs agree on a clock for them.
- `Record.validate`'s symlink check needs the filesystem and is not repeated.
- Rule-based checks cover C01–C04, C06–C08 and C11 (plus part of C05/C12). C09, C10 and C13 rely on the LLM for now.
- The unqualified-safety rule is lexical. It misses a safety claim worded without its trigger words (for example
  "it never fell"), and it can flag an unusual sentence that uses them harmlessly. Each finding asks for human review.
- Checker results: the ledger rules catch results that contradict themselves, not a forgery that is consistent everywhere; empirical admission stays disabled and synthetic results are used only in test fixtures.
- Not implemented on purpose: Drafter, Revision Agent, RAG changes.

## Files

```
critic/
  critic.py          review(): runs checks, then the LLM, builds and checks the report
  checks.py          validation and rule-based review checks
  claims.py          the unqualified safety claim rule (0.5.0)
  schema.py          built-in JSON Schema validator for the schemas above
  llm.py             prompt, backends (none / scripted / OpenAI-compatible), output screening
  contract.py        shared vocabulary copied from the GSN, registry and R1 contracts
  assessments.py     when a checker result is admitted
  retrieval.py       when a Phase 5 structured-retrieval bundle is admitted, and what it may be used for
  __main__.py        command line
  compare_models.py  exploratory model comparison for Hestia
  prompts/critic_system_v5.md   the current model prompt (v3 is kept: the R2 audit's real runs used it)
  schemas/           request and report JSON schemas, and the Phase 5 bundle as the Critic reads it
  cases/             five synthetic requests, expected results, scripted replies, stored checker output, generator,
                     and phase5.py (test bundles built by the release's own code)
  examples/          example reports
  tests/             unit tests, and oracles.py (loads the team's code on 3.9; strict mode)
  requirements-test.txt  jsonschema for the test oracles (the Critic itself needs nothing)
```

## PR18 independent audit corrections

Prompt v5 removes the blanket unresolved-node C09 exemption and asks for the complete offending statement. Non-finite JSON constants and overflowing float literals in model replies fail the model step with the original text/hash retained as diagnostics, never as parsed findings. CLI reports use strict finite-JSON serialization. Empty/whitespace/malformed model aliases fail configuration; configured aliases match exactly. Inference settings are deep snapshots, including nested sampling options and accepted-model lists. Authentication fields cannot be supplied through extra_body; URL credentials/authentication query fields are omitted from traces.

`phase5_request.py` executes database-independent predicates extracted from the frozen public `StructuredRetriever.prepare`, using its schema and constants. It removes catalogue/channel lookups and guards that require those rows, without substituting invented database values. Scope binding and returned-source/citation/crosswalk consistency are additionally checked by `retrieval.py`. This preflight does not authenticate external database contents, channel component identities or a producer's claimed values; the frozen retriever retains those responsibilities. Real integration verification exercises the complete frozen API on Hestia. Case E has supported global contact references and a missing settling-action obligation, not unsupported object-filtered contacts. Tests also execute the **entire** original public prepare method against explicitly synthetic metadata, including its rejection of the old filter.

See `CRITIC_PR18_FIXES_AND_VERIFICATION_REPORT.md` for before/after counterexamples, real retrieval and model execution results, compatibility decisions and remaining scientific limitations. No successful retrieval or model criticism establishes physical safety.

The public retrieve() aggregate sample-budget guard is also reused for the lower bound established by returned nonempty frame windows. Unknown or out-of-range windows are not invented, and legitimate unavailable bundles are preserved.
