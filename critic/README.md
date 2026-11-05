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
- **checker_assessments**: validated checker outputs. An empty list means "not available", never "no violation".
- **retrieval_context**: what was requested, gaps, and which records come from related executions.

The output schema is `schemas/critic_report.schema.json`.

## Run it

From the repository root, Python 3.10+, standard library only (`jsonschema` is optional, for one test):

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

## The three test cases

All synthetic and marked `test_fixture: true`. They use the three-object example configuration (`B_SYNTHETIC_THREE_OBJECTS.json`) so nothing depends on the original five LIBERO objects. Run `python3 -m critic.cases.build_cases` to regenerate them.

| Case | What the mock Drafter did | Rule-based result |
|---|---|---|
| A: unsupported safety claim | Claims R1 satisfied for all objects from poses and contacts, with no checker assessment | 3 blocking C06 findings, one per object, each with an evidence request |
| B: missing or wrong evidence | Cites an evidence ID that was never retrieved, uses another execution's record as proof, leaves out one configured object | Blocking C02 (widget_a), C03 (vial_b) and C04 (carton_c) |
| C: correct unresolved argument | Says R1 cannot be determined and keeps support and fall questions open | No findings, not blocked |

Reports are in `examples/`. `case_a…scripted_llm_demo.json` shows the LLM step with a **hand-written** reply (not a real model). It contains two valid findings plus one with an invented evidence ID and one with a made-up node, and the Critic rejects those two. Real model outputs will be added after the Hestia run.

## Tests (32)

- the three cases produce exactly the expected findings, and Case C gets none
- requests, graphs, records and reports validate against their JSON schemas
- **agreement with the original GSN validator:** 11 kinds of broken graph that `gsn.py:Graph.validate` rejects are all flagged by the Critic, and the real `demo/GRAPH.json` passes both
- evidence IDs reproduce the registry's content hashes; a tampered record is caught
- configurable R1: an extra configured object is reported missing; fewer objects are not demanded
- R1 aggregation precedence, checker contradiction (C07), an "insufficient information" claim that hides a verified violation (C07), unsupported non-applicability (C08), related-case misuse (C11), no-violation claims over retrieval gaps (C04)
- LLM screening: invented IDs/nodes, malformed findings and duplicates rejected; a broken or empty model reply does not break the review; the HTTP client works against a local fake vLLM server
- **never crashes on bad input:** broken requests and 400 randomly corrupted ones all come back as valid reports with C01 findings

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
  __main__.py        command line
  compare_models.py  exploratory model comparison for Hestia
  prompts/critic_system_v1.md
  schemas/           request and report JSON schemas
  cases/             three synthetic requests, expected results, scripted replies, generator
  examples/          example reports
  tests/             unit tests
```
