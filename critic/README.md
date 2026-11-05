# Critic Agent (midpoint prototype)

The Critic reviews a Drafter's GSN-style argument for one LIBERO execution and returns structured, machine-readable criticism. It points out unsupported claims, wrong or missing evidence, missing objects, ignored uncertainty and conclusions that break the R1 aggregation rules.

It does not decide whether the robot was safe, does not write a new argument, does not touch the evidence database and does not invent observations. A report with no findings only means this Critic found nothing wrong within the evidence it was given.

## How it works

```
review request (one execution)
  ├─ 1. validation          deterministic, always run
  │     JSON schemas, Graph.validate and Record.validate rules, evidence references,
  │     record hashes, bundle coverage, checker results; any failure rejects the input
  ├─ 2. rule-based review   deterministic, always run
  │     claimed outcomes vs admitted checker results, gaps, R1 execution aggregation
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
- **checker_assessments**: R1 checker results, each `{configuration, result}`: the output of `evaluation/r1_v4/runtime.py:assess` exactly as the checker wrote it, plus the R1 configuration it ran on (see below). An empty list means "not available", never "no violation".
- **retrieval_context**: what was requested, gaps, and which records come from related executions.

The output schema is `schemas/critic_report.schema.json`.

## Validation before review

Before anything is reviewed, the Critic checks that the input is well formed, using the team's own contracts:

- the request against `schemas/critic_request.schema.json`, each graph against `gsn_graph.schema.json` and each evidence record against `registry_record.schema.json`. `schema.py` is a small standard-library JSON Schema validator that implements exactly the keywords these schemas use and raises on any other keyword, so no rule is skipped silently. A test compares it with the `jsonschema` package where that is installed;
- every rule of `gsn.py:Graph.validate` and of `models.py:Record.validate` (except Record.validate's symlink check, which needs the filesystem). Node and record requirement IDs and versions must match the review;
- synthetic data must be marked: a record with a `/synthetic/` source path or `provenance.synthetic` is only accepted in a request with `test_fixture: true`, and only such a request may use `/synthetic/` instead of the approved source root;
- the R1 configuration and the context's binding to it (below);
- the bundle covers the configured objects, and checker results pass the admission rules below.

### Binding to the R1 configuration

The request carries the full R1 v2 configuration. `checks.check_configuration` validates it the way `evaluation/r1_v4/configuration.py:validate_configuration` does (its schema and all 12 of its semantic rules, under the same names) and checks `r1_configuration_sha256`. Then the context must be exactly that configuration's:

- the same protected objects and support surfaces. A shorter list in the context and bundle is an unauthorized reduction (`CONFIG-OBJECTS`); a different configuration (three objects, five LIBERO objects, one object) is fine, because it is the configuration that decides;
- the same requirement, benchmark and, where the configuration sets them, execution, task and policy checkpoint. The team's configurations are templates with `execution_id: null`, so they apply to any execution of their task;
- the monitored interval on the configuration's clock (`saved_frame` is the GSN `frame` / `saved_frame_index` clock; `simulator_time` has no agreed GSN clock yet and is refused). An explicit boundary must equal the interval. A boundary resolved from recorded data (`recorded_first_policy_boundary`, `terminal_recorded_snapshot`) needs `boundary_provenance`: the frame it resolved to and the source path, hash and selector it was read from.

A configuration with no protected objects is valid: the execution is an empty scope, aggregates to `not_applicable`, is marked `empty_scope` in the summary, and a no-violation claim for it is flagged, because an empty scope is never a pass.

Every criticism has a `phase`. A `validation` criticism means the input itself is invalid: all of them are blocking, the LLM is not called, and the report's `review_status` is `rejected_invalid_input`. Its criticisms are the diagnostics, not a completed critique. A `review` criticism is a critique of a well-formed argument; these include two argument defects that `Graph.validate` accepts: a goal or strategy with no support, and support resting on an unusable record.

`review_status` is one of `completed`, `completed_llm_failed` (the rule-based review is complete but the model step failed), `rejected_invalid_input` and `internal_error` (the report failed its own schema, which is checked before it is returned; `status_detail` says why). The command line exits with 0 (completed, nothing blocking), 1 (completed, blocking criticisms), 3 (input rejected), 4 (LLM step failed), 5 (internal error) or 6 (request file unreadable); 2 is the standard code for a bad command line.

One gap found in the team's code while testing: `Record.validate` alone accepts a string or an object where a list belongs (for example `"uncertainty": "frame"`), because it only iterates the value. `registry_record.schema.json` forbids this and the Critic enforces both.

## Checker results: when the Critic uses one

A label written by the caller is never enough. The Critic reads the R1 checker's own output contract (`evaluation/r1_v4/assessment.schema.json`) and `assessments.py` uses an object assessment from it only if:

- the result has the checker's required fields and fixed values (R1 2.0.0, checker `r1-v4-restricted-infrastructure` 4.0.0a1, configuration valid and assessed, no physical safety conclusion, empirical profiles off), and the object assessment has every `ObjectAssessment` field with the right types and values;
- `assessment_hash` matches the result's content and `configuration_hash` matches the supplied configuration, so neither was edited after the checker ran;
- the checker ran on the review's own R1 configuration (its content hash is `r1_configuration_sha256`), so objects, surfaces and the monitored interval match by construction; the result is for this requirement, execution and task, and a result from a template configuration (no execution) is not tied to this execution and is refused;
- the checker admitted the run itself (`provenance.admitted_purpose` is set);
- the object is configured, the assessment is for this execution and the object's mapped surfaces, and it passes the consistency rules of `aggregate.py` (violation or no-violation need `applicable`, no-violation needs no missing coverage, not-applicable needs `not_applicable`);
- every evidence ID it cites is one of the checker's own evidence records for this execution and object, and for violation, no-violation and not-applicable it is evidence the checker admitted;
- it is admitted for this request. The checker only produces synthetic analytical output today and empirical admission is off for the whole project, so results are used only when `test_fixture` is true, and findings call them synthetic test-fixture assessments. A result not marked synthetic is refused, because there is no empirical route yet.

A result or object assessment that fails any of these gets a blocking `CHK-*` finding and is ignored: it can neither support nor contradict a claim, and the LLM is told it was not admitted and cannot cite it. Every object assessment gets a row in the report's `checker_admission` list, with the ID `ca:<assessment_hash>:<object_id>`. The hashes show that nothing changed after the checker ran; they do not show who ran it.

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

## What the Critic accepts from the model

The model step can never break or silently weaken a review (`llm.run`). Building the prompt, the call, parsing and screening all run inside one error boundary. A reply that cannot be used (no JSON, `findings` not a list, an empty or non-text reply, a timeout) gives `review_status: completed_llm_failed` with the error, and the rule-based findings stay; it is never turned into an empty critique.

Each model finding is then checked on its own, and rejected (kept under `rejected_llm_findings` with the reason) unless:

- it matches the finding format exactly (`llm.FINDING_SCHEMA`: the listed keys only, a known category and severity, non-empty explanation and suggested action, string or null IDs, a list of distinct evidence IDs);
- its category is one the model may raise. C01, C02, C03, C04 and C11 are decided by the rule-based checks only; from a model they would be unsupported;
- its object is configured, its node exists in that object's graph, and every evidence ID it cites is in the package, about the finding's object (when it names one) and about the execution under review;
- a C07 contradiction names an object and cites an admitted checker assessment for that object;
- it does not repeat a rule-based finding.

Accepted findings are still `llm_proposed`, need human review and never block on their own; the checks above make them grounded in the supplied evidence, not correct.

Every model call leaves a trace in `report.llm`: the prompt version and the sha256 of the prompt file, of the exact messages sent (after any model-card adjustment), of the review request and of the full reply; the effective settings (base URL without any user:password, model, temperature, token limit, extra parameters, prompt adjustments; never the API key); the raw reply (cut at 65,536 characters, flagged when cut); and how many findings were accepted and rejected.

## Run it

From the repository root. The Critic itself needs only the Python standard library (tested on Python 3.9, 3.10 and 3.13). Some tests use the team's own code and are skipped, with the reason shown, when it cannot run: the schema tests need `jsonschema`, the GSN validator comparison needs Python 3.10+, and re-running the R1 checker needs Python 3.10+ and `jsonschema>=4`.

```bash
# tests (no GPU, no network)
python3 -m unittest discover -s critic/tests -t . -v

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

The model is a setting. Sampling follows each model's card (`llm.MODEL_PRESETS`). The model comparison and the Hestia commands are in [MODEL_COMPARISON.md](MODEL_COMPARISON.md).

## The four test cases

All synthetic and marked `test_fixture: true`. Cases A to C use the three-object example configuration (`B_SYNTHETIC_THREE_OBJECTS.json`) so nothing depends on the original five LIBERO objects. Case D uses the R1 checker's own fixture (`evaluation/r1_v4/synthetic/three_object_violation.json`) and the checker's real output for it, stored in `cases/checker_outputs/`. Run `python3 -m critic.cases.build_cases` to regenerate the cases, and add `--refresh-checker-output` to re-run the checker first (it needs `jsonschema>=4`, as pinned in `evaluation/r1_v4/requirements.txt`).

| Case | What the mock Drafter did | Rule-based result |
|---|---|---|
| A: unsupported safety claim | Claims R1 satisfied for all objects from poses and contacts, with no checker assessment | 3 blocking C06 findings, one per object, each with an evidence request |
| B: missing or wrong evidence | Cites an evidence ID that was never retrieved, uses another execution's record as proof, leaves out one configured object | Input rejected (`rejected_invalid_input`), no model review; diagnostics C02 (widget_a), C03 (vial_b) and C04 (carton_c) |
| C: correct unresolved argument | Says R1 cannot be determined and keeps support and fall questions open | No findings, not blocked |
| D: claim hides a checker result | Leaves object_00 unresolved although the (synthetic) checker result reports a violation; its other two claims match the checker | Blocking C07 for object_00; the other two claims are supported |

Reports are in `examples/`. `case_a…scripted_llm_demo.json` shows the LLM step with a **hand-written** reply (not a real model). It contains two valid findings plus one with an invented evidence ID and one with a made-up node, and the Critic rejects those two. Real model outputs will be added after the Hestia run.

## Tests (110)

- the four cases produce exactly the expected findings, and Case C gets none
- requests, graphs, records and reports validate against their JSON schemas
- validation before review (audit I3, I4, I9): the audit's probes (required request fields removed; node and record requirement IDs changed to R999 with recomputed record IDs; a dangling edge) are all rejected with `rejected_invalid_input` and the model is not called; synthetic records need `test_fixture`; every validation criticism is blocking; duplicate edges are blocking; an unsupported goal is a blocking review criticism; a model failure gives `completed_llm_failed`; a report that fails its own schema gives `internal_error`; every command-line exit code
- **agreement with the original GSN validator:** 12 kinds of broken graph that `gsn.py:Graph.validate` rejects are all flagged by the Critic as validation criticisms and reject the whole review, and the real `demo/GRAPH.json` passes both
- **agreement with the original record validator:** the team's real demo records pass both; 23 single-rule breaks and 400 random corruptions (with recomputed IDs, so the hash cannot give them away) are rejected by the Critic exactly when `Record.parse` or the registry schema rejects them
- the built-in schema validator uses only supported keywords in all six schemas, follows JSON rules (true is not 1, 1.0 is an integer), and gives the same verdict as `jsonschema` on the cases and 1,800 corrupted documents
- evidence IDs reproduce the registry's content hashes; a tampered record is caught
- configurable R1: an extra configured object is reported missing; fewer objects are not demanded
- checker admission (audit I1): real checker output is admitted in a fixture; a self-asserted `validated_checker` label, a re-hashed result for the wrong requirement, task or interval, synthetic output in a non-fixture request, output not marked synthetic, an edited result or configuration, a run the checker refused, a configuration with other objects, surfaces, execution or interval boundaries, a wrong clock or checker version, object assessments with unknown, wrong-object or unadmitted evidence, broken consistency rules, wrong object, execution, requirement, surface or status, and duplicates are all refused and never produce a C07. Each of these checks was switched off in turn to confirm a test fails without it
- the stored checker output is exactly what `runtime.assess` produces for its fixture (needs Python 3.10+ and `jsonschema>=4`, like the checker itself)
- the copied checker constants (required fields, fixed values, enums, checker version) match `evaluation/r1_v4/assessment.schema.json`
- conflicts and applicability (audit I2): the audit's probe (no-violation claims while one assessment reports a violation and another does not) is caught twice, as a contradiction and as a conflict; every row of the table above has a test, including insufficient and invalid-contract results giving C06/C08 rather than C07
- gaps (audit I11): gaps for other objects, outside the monitored interval or for optional evidence give no finding but stay listed; a relevant gap is non-blocking under an admitted no-violation result and blocking without one
- every conclusion finding and gap rule was switched off in turn to confirm a test fails without it
- R1 configuration (audit I6): all 12 semantic rules agree with `validate_configuration` by name on every example configuration and the checker fixture; an oracle against the real function (Python 3.10+ with `jsonschema>=4`) compares verdicts and rule names on 300 random corruptions too; the audit's probe (context and bundle reduced to one object) is rejected; configuration hash, scope, templates, surfaces, interval clock, explicit boundaries and boundary provenance are each checked; the real five-object LIBERO profile (names read from `A_LIBERO_FIVE_OBJECTS.json`) is reviewed with no findings and a dropped LIBERO object is caught; empty scope; full-vector aggregation; the accepted outcome
- R1 aggregation precedence, checker contradiction (C07), an "insufficient information" claim that hides a checker violation (C07), unsupported non-applicability (C08), related-case misuse (C11), no-violation claims over retrieval gaps (C04)
- model output (audit I5, I8, I10): the audit's probes (a list as the category; a C07 with no evidence) are handled; every field of a finding is type-checked (19 kinds of broken finding); unusable replies and failures inside prompt building, parsing or screening give `completed_llm_failed` with the rule findings kept; rule-only categories are refused; a C07 must cite an admitted assessment for its object; citations must match the finding's object and execution; the trace hashes match what was sent and received (checked against a local fake vLLM server), the API key never appears in the report, and a long reply is cut but hashed in full; every rejection rule and trace field was switched off in turn to confirm a test fails without it
- LLM screening: invented IDs/nodes, malformed findings and duplicates rejected; a broken or empty model reply does not break the review; the HTTP client works against a local fake vLLM server; credentials in the server URL are not recorded
- the model comparison runner (`compare_models.py`) works end to end against a fake vLLM server, skips Case B (rejected before the model step, so no model is asked) and keeps each call's trace
- **never crashes on bad input:** broken requests and 600 randomly corrupted ones (200 of them inside the checker result) all come back as valid reports

## Integration note: Phase 5 RAG release

The final RAG release (`evaluation/r1_v4/rag_evidence_database/final_phase5_release`, schema `phase5-structured-1.0.0`) returns evidence as bundles with `evidence-citation:` IDs, a `completeness_status` and `missing_obligations`. The Critic currently reads registry 1.0.0 records (`ev:` IDs), because that is what GSN 1.0.0 solution nodes cite. Connecting the two needs a small adapter, not a Critic change:

- `completeness_status` → `retrieval_context.complete_within_requested_scope` (true only for `COMPLETE WITHIN VERIFIED CONTRACT`)
- `missing_obligations` → `retrieval_context.gaps`
- bundle evidence groups → `evidence_package.records`

Open question for the team: should GSN solution nodes cite registry `ev:` IDs or the new `evidence-citation:` IDs? The Critic's evidence-ID checks follow whichever the graph schema uses.

## Limits (honest)

- The LLM part has only been exercised with scripted replies and a fake server so far. Real model behaviour still has to be measured on Hestia.
- Three synthetic cases cannot show research-level Critic quality.
- Temporal coverage is checked at the level of declared intervals and retrieval gaps, not per measurement cell.
- Boundary provenance is checked for consistency, but the Critic cannot open the recorded source it names. `simulator_time` configurations are refused until the GSN graphs agree on a clock for them.
- `Record.validate`'s symlink check needs the filesystem and is not repeated.
- Rule-based checks cover C01–C04, C06–C08 and C11 (plus part of C05/C12). C09, C10 and C13 rely on the LLM for now.
- Not implemented on purpose: Drafter, Revision Agent, RAG changes.

## Files

```
critic/
  critic.py          review(): runs checks, then the LLM, builds and checks the report
  checks.py          validation and rule-based review checks
  schema.py          built-in JSON Schema validator for the schemas above
  llm.py             prompt, backends (none / scripted / OpenAI-compatible), output screening
  contract.py        shared vocabulary copied from the GSN, registry and R1 contracts
  assessments.py     when a checker result is admitted
  __main__.py        command line
  compare_models.py  exploratory model comparison for Hestia
  prompts/critic_system_v3.md
  schemas/           request and report JSON schemas
  cases/             four synthetic requests, expected results, scripted replies, stored checker output, generator
  examples/          example reports
  tests/             unit tests
```
