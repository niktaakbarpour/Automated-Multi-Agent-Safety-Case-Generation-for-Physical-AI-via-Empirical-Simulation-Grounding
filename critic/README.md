# Critic Agent (midpoint prototype)

The Critic reviews a Drafter's GSN-style argument for one LIBERO execution and returns structured, machine-readable criticism. It points out unsupported claims, wrong or missing evidence, missing objects, ignored uncertainty and conclusions that break the R1 aggregation rules.

It does not decide whether the robot was safe, does not write a new argument, does not touch the evidence database and does not invent observations. A report with no findings only means this Critic found nothing wrong within the evidence it was given.

## How it works

```
review request (one execution)
  ├─ 1. rule-based checks   deterministic, always run
  │     graph structure (same rules as evidence_registry_gsn/gsn.py), evidence IDs exist,
  │     record hashes, execution/object/interval scope, missing objects, claimed outcomes
  │     vs checker results, R1 execution aggregation
  └─ 2. LLM review          optional, any OpenAI-compatible server (vLLM on Hestia)
        wording-level problems the rules cannot see (e.g. "height dropped so it fell",
        "certified safe"); every finding is screened and anything citing an unknown
        node or evidence ID is rejected
  → CriticReport (JSON)
```

Every criticism records its category (C01–C13 from the handoff), severity, affected object and node, explanation, evidence IDs, suggested fix, and whether it came from a rule or the LLM. LLM findings always need human review and are never blocking on their own.

## Input: one bundle per execution

`schemas/critic_request.schema.json`, following the handoff's sections A–E:

- **evaluation_context**: requirement version, execution, protected objects, surfaces and monitored interval, taken from the R1 v2 configuration (never hardcoded).
- **argument_bundle**: one unchanged GSN 1.0.0 graph per protected object, plus the execution conclusion (claimed per-object outcomes and the execution outcome). Objects that are non-applicable or unknown are still included.
- **evidence_package**: registry records 1.0.0, exported as they are.
- **checker_assessments**: R1 checker results, each `{configuration, result}`: the output of `evaluation/r1_v4/runtime.py:assess` exactly as the checker wrote it, plus the R1 configuration it ran on (see below). An empty list means "not available", never "no violation".
- **retrieval_context**: what was requested, gaps, and which records come from related executions.

The output schema is `schemas/critic_report.schema.json`.

## Checker results: when the Critic uses one

A label written by the caller is never enough. The Critic reads the R1 checker's own output contract (`evaluation/r1_v4/assessment.schema.json`) and `assessments.py` uses an object assessment from it only if:

- the result has the checker's required fields and fixed values (R1 2.0.0, checker `r1-v4-restricted-infrastructure` 4.0.0a1, configuration valid and assessed, no physical safety conclusion, empirical profiles off), and the object assessment has every `ObjectAssessment` field with the right types and values;
- `assessment_hash` matches the result's content and `configuration_hash` matches the supplied configuration, so neither was edited after the checker ran;
- the configuration is for this review: same requirement, execution, task, protected objects and support surfaces, and its monitored interval is the review's monitored interval (the checker's `saved_frame` axis is the GSN `frame` / `saved_frame_index` clock);
- the checker admitted the run itself (`provenance.admitted_purpose` is set);
- the object is configured, the assessment is for this execution and the object's mapped surfaces, and it passes the consistency rules of `aggregate.py` (violation or no-violation need `applicable`, no-violation needs no missing coverage, not-applicable needs `not_applicable`);
- every evidence ID it cites is one of the checker's own evidence records for this execution and object, and for violation, no-violation and not-applicable it is evidence the checker admitted;
- it is admitted for this request. The checker only produces synthetic analytical output today and empirical admission is off for the whole project, so results are used only when `test_fixture` is true, and findings call them synthetic test-fixture assessments. A result not marked synthetic is refused, because there is no empirical route yet.

A result or object assessment that fails any of these gets a blocking `CHK-*` finding and is ignored: it can neither support nor contradict a claim, and the LLM is told it was not admitted and cannot cite it. Every object assessment gets a row in the report's `checker_admission` list, with the ID `ca:<assessment_hash>:<object_id>`. The hashes show that nothing changed after the checker ran; they do not show who ran it.

Two limits for now. The R1 configuration has no variant field, so a checker result is tied to a variant only through its execution ID. Interval boundaries other than explicit frame indices (for example `terminal_recorded_snapshot`) are refused until boundary provenance is part of the request.

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
| B: missing or wrong evidence | Cites an evidence ID that was never retrieved, uses another execution's record as proof, leaves out one configured object | Blocking C02 (widget_a), C03 (vial_b) and C04 (carton_c) |
| C: correct unresolved argument | Says R1 cannot be determined and keeps support and fall questions open | No findings, not blocked |
| D: claim hides a checker result | Leaves object_00 unresolved although the (synthetic) checker result reports a violation; its other two claims match the checker | Blocking C07 for object_00; the other two claims are supported |

Reports are in `examples/`. `case_a…scripted_llm_demo.json` shows the LLM step with a **hand-written** reply (not a real model). It contains two valid findings plus one with an invented evidence ID and one with a made-up node, and the Critic rejects those two. Real model outputs will be added after the Hestia run.

## Tests (50)

- the four cases produce exactly the expected findings, and Case C gets none
- requests, graphs, records and reports validate against their JSON schemas
- **agreement with the original GSN validator:** 11 kinds of broken graph that `gsn.py:Graph.validate` rejects are all flagged by the Critic, and the real `demo/GRAPH.json` passes both
- evidence IDs reproduce the registry's content hashes; a tampered record is caught
- configurable R1: an extra configured object is reported missing; fewer objects are not demanded
- checker admission (audit I1): real checker output is admitted in a fixture; a self-asserted `validated_checker` label, a re-hashed result for the wrong requirement, task or interval, synthetic output in a non-fixture request, output not marked synthetic, an edited result or configuration, a run the checker refused, a configuration with other objects, surfaces, execution or interval boundaries, a wrong clock or checker version, object assessments with unknown, wrong-object or unadmitted evidence, broken consistency rules, wrong object, execution, requirement, surface or status, and duplicates are all refused and never produce a C07. Each of these checks was switched off in turn to confirm a test fails without it
- the stored checker output is exactly what `runtime.assess` produces for its fixture (needs Python 3.10+ and `jsonschema>=4`, like the checker itself)
- the copied checker constants (required fields, fixed values, enums, checker version) match `evaluation/r1_v4/assessment.schema.json`
- R1 aggregation precedence, checker contradiction (C07), an "insufficient information" claim that hides a checker violation (C07), unsupported non-applicability (C08), related-case misuse (C11), no-violation claims over retrieval gaps (C04)
- LLM screening: invented IDs/nodes, malformed findings and duplicates rejected; a broken or empty model reply does not break the review; the HTTP client works against a local fake vLLM server
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
- Rule-based checks cover C01–C04, C06–C08 and C11 (plus part of C05/C12). C09, C10 and C13 rely on the LLM for now.
- Not implemented on purpose: Drafter, Revision Agent, RAG changes.

## Files

```
critic/
  critic.py          review(): runs checks, then the LLM, builds the report
  checks.py          rule-based checks
  llm.py             prompt, backends (none / scripted / OpenAI-compatible), output screening
  contract.py        shared vocabulary copied from the GSN, registry and R1 contracts
  assessments.py     when a checker result is admitted
  __main__.py        command line
  compare_models.py  exploratory model comparison for Hestia
  prompts/critic_system_v2.md
  schemas/           request and report JSON schemas
  cases/             four synthetic requests, expected results, scripted replies, stored checker output, generator
  examples/          example reports
  tests/             unit tests
```
