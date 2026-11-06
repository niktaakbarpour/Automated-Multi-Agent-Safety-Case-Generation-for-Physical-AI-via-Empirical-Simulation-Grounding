# Drafter

The Drafter proposes one GSN graph for every object in a supplied R1 configuration.
It preserves evidence scope and uncertainty; every physical outcome remains
`insufficient_information`. Structural acceptance does not establish robot safety.

Nikta ran the original code with full BF16 Qwen3-32B on Hestia. One complete
response was rejected: evidence IDs appeared as edge endpoints, Solution citations
were empty, and a decoder/schema mismatch restricted prose to single characters.
The recorded successful server was **SGLang 0.5.4.post3 / XGrammar 0.1.25**.
See [the execution report](../DRAFTER_QWEN3_32B_EXECUTION_REPORT.md).
The independent audit also exercises the frozen database, the recorded decoder
environment and actual Qwen drafting on Hestia. See
[the PR20 verification report](DRAFTER_PR20_AUDIT_AND_COMPLETION_REPORT.md) for
the exact source revisions, accepted and rejected attempts, remaining limitations
and GPU recovery evidence. Mock and scripted tests remain separate from those runs.

## Install and test

From the repository root, using Python 3.12:

```sh
python3 -m pip install -r drafter/requirements.txt
python3 -m drafter --validate-request drafter/cases/scenario_a.request.json
python3 -m unittest discover -s drafter/tests -t . -v
```

The tests use saved or constructed inputs, scripted replies and temporary local
servers. They measure software behavior, not LLM performance. XGrammar and model
weights are not required for this test suite.

The supported `jsonschema` range includes 4.19.1 (the current checker's/Critic's
pin) and 4.25.1 (the original standalone client). Both endpoints are tested on
Hestia. Structured adaptation requires the repaired Critic consumer merged by
PR21; an older consumer fails closed rather than accepting unsupported requests
as complete evidence. See the contract for supported numeric/depth and nonempty
scope limits, and for the schemas of generation/early-rejection reports.

## Input profiles

| Profile | Input and validation |
| --- | --- |
| Omitted or `archived_registry` | Original pinned Scenario A fixture, source-byte bindings and explicit configuration derivation. |
| `supplied_registry` | Another valid supported R1 configuration plus original registry records; no pinned five-object restriction. |
| `phase5_structured` | Exact Phase 5 structured query and returned bundle, with optional original registry records. |

The configurable routes support explicit inclusive saved-frame boundaries.
Unmapped clock domains or unresolved boundaries are rejected clearly.
They validate configuration, checkpoint, target scope, digests, evidence partition,
object roster and gaps before inference. Missing or malformed input returns
diagnostics rather than a traceback. Analytical fixtures must remain labelled
`test_fixture=true`; neither real nor synthetic inputs enable physical admission.

Python APIs are `request_profiles.build_supplied_request(...)` and
`phase5_adapter.adapt_phase5_request(...)`. The CLI accepts JSON objects containing
the same keyword arguments. This local example prepares both kinds of input:

```sh
mkdir -p drafter/runs
python3 - <<'PY'
import json
from copy import deepcopy
from pathlib import Path

runs = Path("drafter/runs")
legacy = json.loads(Path("drafter/cases/scenario_a.request.json").read_text())
registry = {
    "request_id": "supplied-registry-example",
    "requirement_configuration": legacy["requirement_configuration"],
    "target_execution": legacy["target_execution"],
    "monitoring_scope": legacy["monitoring_scope"],
    "registry_records": legacy["evidence_package"]["records"],
    "test_fixture": True,
}
case = json.loads(Path("critic/cases/case_e_partial_structured_retrieval.json").read_text())
ctx, entry = case["evaluation_context"], case["structured_evidence"][0]
phase_config = deepcopy(ctx["r1_configuration"])
phase_config["benchmark"]["policy_checkpoint"] = ctx["model_checkpoint"]
phase5 = {
    "request_id": "phase5-synthetic-example",
    "requirement_configuration": phase_config,
    "target_execution": {key: ctx[key] for key in (
        "execution_id", "benchmark", "task_id", "model_checkpoint", "variant_id")},
    "monitoring_scope": {
        **ctx["monitored_interval"], "bounds": "inclusive",
        "resolution_status": "provided_explicit",
        "boundary_provenance": ["Synthetic consumer fixture; not a verified execution boundary."]},
    "structured_request": entry["request"], "evidence_bundle": entry["bundle"],
    "test_fixture": True,
}
for name, value in (("registry-inputs", registry), ("phase5-inputs", phase5)):
    with (runs / (name + ".json")).open("x") as stream:
        json.dump(value, stream, indent=2)
PY
python3 -m drafter --prepare-registry drafter/runs/registry-inputs.json \
  --out drafter/runs/registry.request.json
python3 -m drafter --adapt-phase5 drafter/runs/phase5-inputs.json \
  --out drafter/runs/phase5.request.json
python3 -m drafter --validate-request drafter/runs/phase5.request.json
```

For a real retrieved response, replace the synthetic query/bundle and configuration
with the exact supplied values. The adapter performs no database call or source
replay. It preserves obligations, citations, source hashes, statuses, assumptions,
scope, values and missing evidence. It reuses the Critic's consumer consistency
checks, not a second independently maintained validator.

Raw Phase 5 channels remain attributed context; they are never fabricated into
`ev:` registry records. Only original compatible registry records with exact
source links can become GSN Solutions. The accepted argument's `evidence_context`
must equal the context recomputed from its input. Complete retrieval concerns
explicit requested observations, not sufficient evidence that R1 holds.
Hashes and local consistency checks do not independently authenticate source bytes.

## Explicit mock

```sh
python3 -m drafter --mock-demo drafter/cases/scenario_a.request.json \
  --out drafter/runs/scenario_a.mock.run.json \
  --argument-out drafter/runs/scenario_a.mock.argument.json \
  --review-out drafter/runs/scenario_a.mock.review.md
```

A prepared configurable request can replace Scenario A. Fixed rules build graphs
for its actual object roster. Mock mode never calls a model or automatically
replaces a failed live run. Its distinct envelope records `model_called=false`
and `live_model_result=false`; it cannot count as accepted LLM output.
Saved mock examples are in [examples/mock_deployment_blocked](examples/mock_deployment_blocked/).

## Qwen rerun on the GPU host

Reuse Nikta's recorded SGLang environment and local checkpoint revision
`9216db5781bf21249d130ec9da846c4624c16137`. Set the client/server Python paths and
checkpoint path for that host. The observed run used two L40S GPUs numbered 0/3;
use only the GPU assignment allocated for the new run.

First, in the serving environment, run the CPU grammar diagnostic:

```sh
"$SERVING_PY" drafter/tools/check_xgrammar_compatibility.py \
  --expected-xgrammar-version 0.1.25 --out drafter/runs/xgrammar-check.json
```

This checks complete strings through EOS and compiles the full new plan schema.
It uses a tiny ASCII vocabulary, not Qwen's tokenizer, and performs no inference.
It must pass before the full server test; it does not replace that test.
The Mac test run did not execute this optional compiler diagnostic.

Start the recorded server configuration in a separate terminal, with its saved
CUDA_HOME/local-cache environment and available GPU allocation:

```sh
CUDA_VISIBLE_DEVICES=0,3 "$SERVING_PY" -m sglang.launch_server \
  --model-path "$QWEN_CHECKPOINT" --served-model-name Qwen/Qwen3-32B \
  --host 127.0.0.1 --port 8000 --tp-size 2 --dtype bfloat16 \
  --context-length 24576 --max-running-requests 1 --max-total-tokens 24576 \
  --mem-fraction-static 0.88 --chunked-prefill-size 2048 \
  --disable-cuda-graph --disable-custom-all-reduce --attention-backend triton \
  --sampling-backend pytorch --grammar-backend xgrammar --sampling-defaults model \
  --random-seed 42
```

From the repository root on that host, using the client environment:

```sh
"$DRAFTER_PY" -m drafter --check-model \
  --model-config drafter/config/qwen3_32b_sglang.example.json
"$DRAFTER_PY" -m drafter --smoke-test-model \
  --model-config drafter/config/qwen3_32b_sglang.example.json \
  --out drafter/runs/qwen.smoke.json
"$DRAFTER_PY" -m drafter --generate drafter/cases/scenario_a.request.json \
  --model-config drafter/config/qwen3_32b_sglang.example.json \
  --out drafter/runs/qwen.run.json \
  --argument-out drafter/runs/qwen.argument.json \
  --review-out drafter/runs/qwen.review.md
```

Use a prepared request to test Phase 5 integration. Discovery/probe success is
only a connection check. Keep all failed runs and choose new output names;
existing files are never overwritten. SGLang 0.5.4.post3 ignores the per-request
seed; the server seed is recorded, but bitwise reproducibility is not established.
Earlier vLLM profiles remain configurable alternatives, not demonstrated working
full-schema deployments. No model, backend or output-format fallback is automatic.

## Output and review

The run report retains exact input/prompt/schema hashes, model settings, response,
plan and diagnostics. Accepted output uses the original shared GSN validator and
the same complete Drafter graph checks as standalone validation. Nodes, edges,
citations or missing evidence are never silently repaired.

The decoder schema now permits full sentences, distinguishes graph-node IDs from
evidence IDs, and requires non-null Solution citations. Host checks still enforce
declared endpoints, scope, evidence eligibility, usable prose and uniqueness.
Plan/prompt version 0.2.2 uses a minimum of four nodes for the four already-required
core roles and gives a complete, typed core-structure example. It does not fix
node ordering, insert missing structure, repair model responses or establish
scientific correctness. Unresolved claims must be connected through their strategy;
they are not defeaters. Invalid proposals remain saved rejections.

The displayed summary and execution conclusion are host-controlled and unresolved.
Model summary/limitations are retained separately in `reasoning_review`, explicitly
marked for review; LLM node prose has corresponding review markers. This flags
possible contradictory text without pretending that a keyword filter can prove
arbitrary reasoning correct. Read the Markdown review before using a draft.

Runtime files, local configuration and credentials stay outside committed examples.
Use `api_key_env` for an environment-variable name if authentication is needed;
never place a key value in JSON. See [CONTRACT.md](CONTRACT.md) for exact boundaries.

### Ordered object generation

The request-specialized decoder binds each graph array position to the exact
`protected_objects` configuration order using Draft2020-12 `prefixItems`. It also
restricts node and edge namespaces and eligible Solution IDs to that position's
object. An empty eligible catalogue permits no Solution node. This applies to
archived, supplied-registry and Phase 5 profiles. It does not sort returned graphs
or change evidence identity, scope or provenance. Host validation still rejects
any roster, order, endpoint or evidence violation independently of the decoder.
