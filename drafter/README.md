# Drafter development

The current demonstration uses the handoff's **deployment-blocked mock option**.
It runs on this Mac without a model, GPU server, API key or network connection.
The example is clearly labelled as a mock; it does not measure model performance.

Steps 1-2 provide an example input and versioned input/output contracts. Step 3
adds a local-model connection and fixed JSON probe. Step 4 adds argument generation
for the unresolved fixture profile, using the shared GSN graph schema and validator.
Only the explicit generation command sends the example evidence catalogue.

From the repository root, using Python 3.12:

```sh
python3 -m pip install -r drafter/requirements.txt
python3 -m drafter --validate-request drafter/cases/scenario_a.request.json
python3 -m unittest discover -s drafter/tests -t . -v
```

The validation command returns zero for a valid **fixture contract**, and one for
rejected input. It does not certify the evidence or robot behavior.

The example preserves Nikta's original archived registry export and all five
configured objects. Its new illustrative configuration limits the demonstration
to saved frames 10-12; it is not a full-execution assessment. The export provides
metadata and source references, not numerical observation arrays. Original
producer statuses remain unchanged; their source files were not replayed here.
Physical support/fall evidence remains blocked and missing objects/frames remain
explicit. The input supplies no checker assessment or safety conclusion.

See [CONTRACT.md](CONTRACT.md) for the exact input/output boundary, versions,
provenance rules and remaining Critic/retrieval integration.

Regenerate the example without changing source evidence:

```sh
python3 drafter/tools/build_scenario_a.py
```

This foundation uses the original registry export format. A Phase 5 bundle needs a
separate lossless adapter; grouped citations cannot be inserted as registry records.
The current fixture profile deliberately keeps empirical admission disabled.

## Run the deployment-blocked mock

From the repository root, after installing `drafter/requirements.txt`:

```sh
mkdir -p drafter/runs
python3 -m drafter --mock-demo drafter/cases/scenario_a.request.json \
  --out drafter/runs/scenario_a.mock.run.json \
  --argument-out drafter/runs/scenario_a.mock.argument.json \
  --review-out drafter/runs/scenario_a.mock.review.md
```

Open the `.review.md` file to read the argument. The `.argument.json` contains the
machine-readable graph bundle, and the `.run.json` records how it was built.
A saved example is in [examples/mock_deployment_blocked](examples/mock_deployment_blocked/).
Choose fresh output names on later runs; existing files are never overwritten.

Fixed program rules build one graph for each of the five configured objects.
They describe initial support, possible falling departures and the known evidence
gaps. Original evidence IDs and source references are retained. The example cites
the available cream-cheese metadata for frames 10 and 11 and retains its missing
frame 12, plus the other four objects' missing records. All outcomes remain unresolved.

This is a software/interface demonstration using real archived metadata, not a new
robot experiment or model result. The selected Qwen3-32B endpoint is unavailable
and no Hestia connection is configured. Mock mode never attempts a connection,
selects another model, or changes the source package. It is explicit, rather than
an automatic fallback after a failed model call.

The mock graphs pass the same shared GSN schema, `Graph.validate`, scope and
evidence-reference checks as live drafts. The enclosing
`drafter-mock-demo/0.1.0` contract keeps `model_called=false`,
`live_model_result=false` and model/prompt identities null. Fixed-rule reasoning
is labelled in graph provenance. The live `DraftArgument` validator rejects this
mock envelope; it cannot count as accepted model execution.

Exit zero means a valid mock demonstration was saved, not a successful model run.
Inspect the graphs through `argument_bundle`; a full Critic request adapter is
still separate work. Live generation can be tested later using the commands below.

## Local-model connection

The selected model is **Qwen/Qwen3-32B**, the Qwen candidate named in the Drafter
handoff. Both `config/local_model.example.json` and
`config/qwen3_32b_vllm.example.json` select that exact model ID. Model identity,
server address, sampling, output format, timeout and response-size limits remain
explicit settings.

Deployment target: a suitably sized GPU server such as Hestia. The standard model
weights exceed this Mac's 16-GB memory. Qwen3-32B has not been downloaded or run on
this Mac, and no successful live run of the selected model is claimed.

```sh
# On the GPU host, with a compatible vLLM environment and enough GPU memory:
vllm serve Qwen/Qwen3-32B --host 127.0.0.1 --port 8000

# List models and check that the configured ID is available; no inference.
python3 -m drafter --check-model \
  --model-config drafter/config/qwen3_32b_vllm.example.json

# Send a fixed two-field JSON probe and save a new trace file.
mkdir -p drafter/runs
python3 -m drafter --smoke-test-model \
  --model-config drafter/config/qwen3_32b_vllm.example.json \
  --out drafter/runs/connection-check.json
```

These commands assume the client is on the GPU host or has an explicitly arranged
local port forward to it. The host address/access details have not been supplied.
Use a local config copy for the actual server address and checkpoint revision.
The runtime/weights, `runs/`, `.env` and `config/*.local.json` are ignored.
Do not commit credentials or runtime files. If a server needs an API key, configure
its environment-variable name in `api_key_env`; no key value belongs in JSON.

The Qwen3-32B vLLM profile uses the documented hard switch
`chat_template_kwargs.enable_thinking=false`, through config `enable_thinking`,
with temperature 0.7 and top-p 0.8. The server/model revision remains unknown until
the intended deployment is available. Model choice stays configurable.
[Model card](https://huggingface.co/Qwen/Qwen3-32B),
[Qwen vLLM configuration](https://qwen.readthedocs.io/en/latest/deployment/vllm.html).

Connection reports retain public settings, model identity, prompt/version/hash,
raw response, request/response hashes and diagnostics. Known API secrets are
redacted. Discovery must find the configured model before a smoke request; there
is no automatic retry, redirect, model fallback or format fallback. Team-hosted
servers require explicit opt-in. Success proves this fixed connection/JSON probe
worked; it does not demonstrate argument quality or physical safety.

The existing validation command still performs no inference. Connection commands
exit zero for ready/passed and one for failure, and refuse to overwrite reports.

Existing local connection-test logs retain their original model identities; they
are not validation of Qwen3-32B. Offline tests exercise the client and explicit
request settings with temporary loopback servers. Live Qwen3-32B verification and
live argument generation with that model remain pending deployment access.

## Generate and review an argument

Once the configured model server is available:

```sh
mkdir -p drafter/runs
python3 -m drafter --generate drafter/cases/scenario_a.request.json \
  --model-config drafter/config/qwen3_32b_vllm.example.json \
  --out drafter/runs/scenario_a.run.json \
  --argument-out drafter/runs/scenario_a.argument.json \
  --review-out drafter/runs/scenario_a.review.md
```

The JSON argument is the primary GSN output. The Markdown file shows the claims,
evidence IDs, connections and limitations for review. The run report preserves the
exact prompt, compact model plan, original model response, settings and hashes.
Output files are never overwritten. Exit zero means the draft passed graph and
reference checks; exit one means rejection, transport failure or a saving error.

The model chooses nodes, reasoning, evidence references and edges in an intermediate
graph plan. The serializer binds them to the validated requirement, execution and
object scope. For solutions, it copies the exact original source references,
intervals, status and registry metadata. Solution wording must match the supplied
availability-only statement; unsupported physical assertions are rejected.
The model cannot choose authoritative status, provenance or final safety outcomes.

The resulting graphs pass the existing `Graph.validate` and the Drafter's full
output validator. Additional checks require a connected physical root, strategy,
context, subclaims, and an evidence citation wherever eligible metadata exists.
No missing structure, evidence IDs or invalid edges are silently repaired. Invalid
input is rejected before model access, and failed runs contain no accepted graph.

All five objects remain in scope. Every physical goal stays unresolved and all
outcomes are `insufficient_information`. The original input's evidence gaps and
limitations are retained. Graph checks do not establish that free-form reasoning
is scientifically correct; review the proposed statements before submission.

Offline generation tests use explicitly scripted replies, including a temporary
loopback server for the full CLI path. They verify software behavior, not model
quality. No actual Qwen3-32B argument has been generated yet. The model remains
Qwen3-32B; no smaller model is automatically selected. A complete Critic request
adapter and the production Phase 5 retrieval adapter remain separate work.
