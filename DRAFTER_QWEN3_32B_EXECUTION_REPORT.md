# Drafter Qwen3-32B execution report

Date: 2026-11-05. This continuation report updates the prior deployment-blocker assessment, which is preserved unchanged in the earlier experiment directory.

**Actual Qwen3-32B drafting was executed on Hestia. The model returned a complete JSON graph plan, which passed the graph-plan schema but was rejected by the existing serializer. No accepted or validated GSN argument was produced.**

## 1. Environment

| Item | Observed configuration |
| --- | --- |
| Host / account | `hestia` / `niktakbr` |
| OS / Python | Rocky Linux 10.2; Python 3.12.14 |
| Hardware | Four NVIDIA L40S GPUs, each 46,068 MiB; approximately 250 GiB system RAM |
| Selected GPUs | Physical GPUs **0 and 3**, per the user's latest selection |
| Driver | NVIDIA 595.99.02; CUDA 13.2 capability reported by nvidia-smi |
| Successful serving software | SGLang 0.5.4.post3; PyTorch 2.8.0, CUDA 12.8; transformers 4.57.1; huggingface-hub 0.36.0 |
| Decoder / kernels | XGrammar 0.1.25; sgl-kernel 0.3.16.post4; flashinfer-python 0.5.0 installed; Triton attention selected |
| Client | Existing isolated Python 3.12 venv, `jsonschema==4.25.1` |
| Model | Full unquantized BF16 `Qwen/Qwen3-32B` |
| Checkpoint revision | `9216db5781bf21249d130ec9da846c4624c16137` |
| Code revision | `e7839d64f8ad902e194304e982573b05794f3471`, merged main / PR #15; main rechecked before continuation |

All requested source files were inspected before deployment in the original assessment. Their byte identities are in the prior `artifacts/source-manifest.json`. The same unmodified checkout and archived fixture were reused. Repository status remained clean.

All model work, dependency installation, schema diagnostics, fixture validation and output evaluation occurred on Hestia. Indigo was only an SSH relay through the user's authenticated control socket. The Mac only orchestrated commands and received small deliverables. No Alliance cluster was used. Weights, repositories, environments and caches are on Hestia-local disk1; short serving IPC files use Hestia-local `/tmp`. Sea NFS was not selected for computation or experiment storage. Disk1 initially had approximately 2.0 TiB free and sufficient capacity for the weights and isolated environments.

Full weights were downloaded once in the original assessment and reused: 17 safetensors shards totaling **65,524,328,560 bytes**, with all 27 checkpoint files matching expected sizes. Resolved revision and download metadata are retained in the prior `checkpoint-local-manifest.json`. No smaller model, quantization or source replay was substituted.

## 2. Deployment

The successful local endpoint was `http://127.0.0.1:8000/v1`, served by SGLang. It was not publicly bound. The server used tensor parallelism 2, BF16, context length 24,576, one running request, total-token capacity 24,576, memory fraction 0.88, chunked prefill 2,048, Triton attention, PyTorch sampling and XGrammar constraints. CUDA graphs and custom all-reduce were disabled; standard distributed/NCCL communication handled the two selected GPUs.

The original Drafter client configuration remained intact: strict JSON-schema response format, `enable_thinking=false`, temperature 0.7, top-p 0.8, max_tokens 8192, timeout 300 s, seed 42, response limit 1,048,576 bytes, no API key, and remote endpoints disabled. The revision was explicitly recorded. Checkpoint generation defaults supplied top_k 20; server preflight verified effective temperature/top-p/top-k and exact schema equality after protocol conversion. No JSON-schema keyword was removed.

The server API accepts the thinking flag, and tokenizer preflight showed the non-thinking template containing an empty closed think section. The actual completion reported zero reasoning tokens.

**Seed limitation:** SGLang 0.5.4.post3 accepts but does not propagate OpenAI per-request `seed` into its sampling parameters. The real attempt therefore used explicit server `--random-seed 42`, recorded in its command and server-info artifact; the client also requested seed 42. Warm-up and the smoke test occur before drafting and can advance server RNG state. Bitwise reproducibility was not established. Separate server processes with seeds 43/44 were prepared for the conditional additional attempts, but never executed because the first actual draft was rejected.

Preserved deployment history:

- The prior vLLM 0.31.0 deployment loaded the full model and passed JSON probes, but the full plan schema hit unsupported `uniqueItems` or Outlines token-index compilation timeouts at both 5 and 60 seconds. Its LM Format Enforcer integration also failed an import.
- This continuation installed vLLM 0.9.2 / PyTorch 2.7.0 / llguidance 0.7.30 in a separate environment. An initial Unix-socket path exceeded the 107-character limit; using a short local TMPDIR resolved startup. Its V1 engine still rejected `uniqueItems` with HTTP 400. A CPU preflight of its official V0 processor also reported that keyword as a matcher error; no V0 server run followed.
- A separate unmodified SGLang stack compiled the unchanged full token grammar. Its first startup could not find CUDA libraries at `/usr/local/cuda`; setting CUDA_HOME to the CUDA runtime wheel already installed in its isolated environment resolved that issue. Optional DLPack allocator/tracing warnings were nonfatal.

These changes were serving configuration and dependency selection only. No Drafter generation/validation, schema, prompt, RAG adapter or Critic code was changed.

## 3. Connectivity

The existing `--check-model` and `--smoke-test-model` commands were used. In this continuation:

| Reports | Discovery | JSON probe |
| --- | --- | --- |
| `discovery.json`, `smoke.json` (isolated vLLM 0.9.2) | ready | passed |
| `discovery-sglang-seed42.json`, `smoke-sglang-seed42.json` | ready | passed |

The successful SGLang probe returned the selected model ID and the expected finite JSON object `{"probe_id":"drafter-connection-v1","status":"ok"}` with finish_reason `stop`. Attribution is supported by the local command, full checkpoint metadata, GPU worker/weight-loading logs, server-info configuration, model discovery and the actual completion response. No mock endpoint or scripted completion was used.

Across the prior assessment and continuation, five saved CLI JSON probes passed and one failed in the incompatible LM Format Enforcer deployment. Those probes are connectivity checks, not full drafting experiments. Internal serving warm-ups are not counted as Drafter attempts.

## 4. Actual Drafter execution results

The existing command generated from the unchanged `drafter/cases/scenario_a.request.json`.

| Item | Real full-draft result |
| --- | --- |
| Primary trace | `artifacts/attempt-02.run.json` in this continuation directory |
| Run UUID | `7ea617fa-5f97-4992-8588-ee4603f268d8` |
| Status | `rejected` |
| LLM actually called | `true`; completion attempted and project evidence sent |
| Model / revision | `Qwen/Qwen3-32B` / pinned revision above |
| Transport / termination | HTTP 200; completion status `ok`; finish_reason `stop` |
| Tokens | 7,155 prompt; 2,756 completion; zero reasoning; 9,911 total |
| Elapsed | 138.355870 seconds |
| Parseable finite JSON object | Yes |
| Graph-plan JSON Schema | Passed |
| Serializer | Rejected: `plan_invalid_edge_endpoint:cream_cheese_1` |
| Final accepted bundle | null |
| Actual shared `Graph.validate` | Not reached: serialization raised first |

The input schema and semantic checks passed. The report's stage flags are output_schema `passed`, graph_semantics `failed`, evidence_references `failed`, and physical_sufficiency `not_assessed`. The latter two failed flags are coarse graph-stage rejection flags; they do not imply both checks or the shared validator independently ran.

**Cumulative counts:** five existing-CLI draft invocations: four serving failures before a model plan, one actual complete model response rejected, zero accepted drafts. The four failures are three requests from the prior assessment and `attempt-01.run.json` under isolated vLLM 0.9.2 in this continuation. Additional explicit hash-matched HTTP-error diagnostic replays are saved separately and are not counted as model drafts.

Only **one actual full-draft model response** was obtained. The original instruction conditioned two additional independent generation attempts on first-draft success; because this response was rejected, seeds 43/44 were not run. No rejected graph was manually repaired or replaced.

## 5. Proposed graph contents and evaluation

The returned intermediate plan has the complete ordered five-object roster:

| Object | Proposed nodes | Proposed edges | Non-null node evidence IDs |
| --- | ---: | ---: | ---: |
| cream_cheese_1 | 6 | 9 | 0 |
| ketchup_1 | 5 | 4 | 0 |
| orange_juice_1 | 5 | 4 | 0 |
| milk_1 | 5 | 4 | 0 |
| butter_1 | 5 | 4 | 0 |
| **Total** | **26** | **25** | **0** |

These are counts of a **rejected intermediate model plan**. Accepted shared-GSN graphs/nodes/edges remain **0/0/0**. The `.argument.json` is a rejected envelope with no graph bundle; it is not an accepted GSN artifact.

Four cream-cheese edges point directly to original `ev:` registry IDs, but those IDs are not declared node IDs. The solution node `cream_cheese_1:S2` has `evidence_id=null`. All 26 nodes have null evidence IDs. The four attempted registry references are eligible original IDs, so their identities were not invented; their placement as edges rather than solution citations is invalid. `REAL_PLAN_AUDIT.json` lists every dangling edge and its original record metadata.

All 26 node statements are exactly `R`. The model summary is `R`; the only model limitation is also `R`. Therefore the prose does not express meaningful R1 reasoning, the declared monitoring window, missing support/fall evidence, missing objects/frames, or explicit uncertainty. No affirmative safety statement was observed in this one-character text, but the result provides no usable safety reasoning.

Detailed requested checks:

- **Protected objects:** all five appear in correct order in the proposed plan. No accepted graph roster exists.
- **Requirement and execution scope:** input and wrapper digests remain correctly bound to R1 2.0.0 and execution `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`, over saved frames 10–12. Proposed prose `R` does not meaningfully preserve/explain that scope; final graph scope binding was not completed.
- **Evidence and provenance:** the prompt includes original eligible catalogue identities and source references. The plan has zero valid node evidence citations; no final serialized solution provenance exists. The original request/trace remain preserved.
- **Missing evidence and uncertainty:** archived limitations are retained in the input and failure envelope, but the model's own statements/limitations do not express them. Cream cheese frame 12 and all other objects' frames 10–12 remain input gaps. No numerical physical measurements or camera pixels were supplied or replayed.
- **Structured physical outcomes:** no outcome vector was generated because the accepted bundle is null. Empirical-admission and safety-verification flags remain false; no outcome was promoted to safety. `insufficient_information` remains the required contract outcome for any future accepted bundle, rather than an outcome this rejected plan successfully delivered.
- **Graph rejection:** the actual first failure is a dangling edge in the cream-cheese graph. Shared GSN validation never ran on a completed final graph.

Scientific correctness of meaningful reasoning could not be assessed from this output. It is qualitatively unusable prose, and decoder constraints materially affected it. Neither graph-plan schema success nor any future GSN validator success would establish physical safety or trustworthy argument quality.

## 6. Decoder and implementation observations

A separate offline diagnostic used the **original** text schema: type string, minLength 1, maxLength 1600, pattern `\S`. JSON Schema treats that pattern as an unanchored search; strings such as `R1` and `R1 remains unresolved for all protected objects.` are valid under the original schema.

With the installed XGrammar conversion, `R` plus EOS is accepted, while both longer schema-valid strings are rejected. The EOS-aware diagnostic is in `TEXT_GRAMMAR_DIAGNOSTIC_EOS.json`. The earlier diagnostic's text-prefix acceptance should not be confused with complete-string/EOS acceptance. XGrammar also warns that length constraints combined with pattern are ignored. This demonstrates a semantic mismatch between schema validation and the decoding language and is consistent with the single-character output. It does **not** establish that Qwen cannot produce meaningful reasoning under different serving constraints.

No schema constraint was removed, no backend code was patched and no plan statement or edge was changed. The final original Drafter schema and semantic validators remained authoritative. This experiment should be reported as a real rejected proposal under the recorded constrained-serving settings, not a clean baseline of unconstrained model reasoning quality.

An auxiliary evaluation script initially used the wrong local repository path in the new continuation directory. Its traceback is preserved. The path was corrected in a new analysis-script version and the existing reports were summarized again; no model rerun or output modification resulted.

See `DEVELOPER_HANDOFF.md` for the concise findings to share with the teammate. No external message was sent automatically.

## 7. Reproducibility and deliverables

Current Hestia artifact root:

```text
/disk/1/data/niktakbr/drafter-qwen3-32b-20261105-continuation-01/
```

Original weights, checkout, exact client environment, hardware records and prior failures remain at:

```text
/disk/1/data/niktakbr/drafter-qwen3-32b-20261105T150100Z/
```

Important current artifacts:

- `artifacts/attempt-02.run.json`: full real run trace, original messages/schema, public configuration, hashes, raw API response, original assistant content and validation diagnostics.
- `artifacts/attempt-02.argument.json`: rejected envelope with null bundle.
- `artifacts/attempt-02.review.md`: existing CLI's failure review.
- `artifacts/attempt-02.model-content.txt`: exact assistant content; `attempt-02.model-plan.json`: parsed copy; `attempt-02.model-plan.review.md`: readable, unchanged rejected plan.
- `REAL_PLAN_AUDIT.json`, `evaluation-verified.json`, `RESULTS_SUMMARY.json`, `TEXT_GRAMMAR_DIAGNOSTIC_EOS.json`, all under `artifacts/`.
- `environment-sglang-02.json`, `sglang-seed42-02-server-info.json`, package freezes, install logs, `server-sglang-seed42-02.log`, exit statuses and cleanup records under `artifacts/`.
- `scripts/`: exact setup, environment, serving, client, diagnostics, evaluation and reproduction commands. Seed-43/44 scripts exist but were not executed.

The exact successful serving command, run on Hestia with the saved environment, was:

```sh
CUDA_VISIBLE_DEVICES=0,3 "$BASE/sglang-venv/bin/python" -m sglang.launch_server \
 --model-path "$PREV/models/Qwen3-32B" --served-model-name Qwen/Qwen3-32B \
 --host 127.0.0.1 --port 8000 --tp-size 2 --dtype bfloat16 \
 --context-length 24576 --max-running-requests 1 --max-total-tokens 24576 \
 --mem-fraction-static 0.88 --chunked-prefill-size 2048 \
 --disable-cuda-graph --disable-custom-all-reduce --attention-backend triton \
 --sampling-backend pytorch --grammar-backend xgrammar --sampling-defaults model \
 --random-seed 42
```

`env-sglang-02.sh` explicitly sets local caches, short TMPDIR and CUDA_HOME to the installed CUDA runtime wheel. `setup-sglang.sh` records the pinned installation command; `sglang-pip-freeze.txt` records resolved transitive dependencies. The model revision and input/code hashes remain pinned separately.

The existing client invocation, from the unchanged repository, was:

```sh
"$CLIENT_PY" -m drafter --generate drafter/cases/scenario_a.request.json \
 --model-config "$BASE/artifacts/model-seed-42.local.json" \
 --out "$BASE/artifacts/attempt-02.run.json" \
 --argument-out "$BASE/artifacts/attempt-02.argument.json" \
 --review-out "$BASE/artifacts/attempt-02.review.md"
```

Do not rerun those archived output names. To reproduce into fresh outputs on Hestia after checking GPU capacity:

```sh
cd /disk/1/data/niktakbr/drafter-qwen3-32b-20261105-continuation-01
/bin/bash scripts/reproduce-sglang.sh \
 "/disk/1/data/niktakbr/drafter-qwen3-32b-repro-$(date -u +%Y%m%dT%H%M%SZ)"
```

The reproduction helper refuses an occupied port, creates fresh output files, repeats discovery/probe before drafting and cleans up its own server. It was syntax-checked; it was not itself executed as an extra model experiment. RNG/decoder behavior and software/hardware versions remain part of the reproducibility limits.

No weights, virtual environments, credentials or runtime files were committed to Git. All old run artifacts were preserved. The serving process was stopped after the rejected draft, returning GPUs 0/3 to their desktop/background usage; other users' jobs on GPUs 1/2 were left alone. Frozen RAG, checker and human-evaluation artifacts were unchanged.

Deployment references: [Qwen3-32B model card](https://huggingface.co/Qwen/Qwen3-32B), [SGLang pinned release](https://github.com/sgl-project/sglang/tree/v0.5.4.post3), [pinned OpenAI request conversion](https://github.com/sgl-project/sglang/blob/v0.5.4.post3/python/sglang/srt/entrypoints/openai/protocol.py). Captured installed behavior and exact artifacts define the reported results.

## 8. Conclusion

**Actual Qwen3-32B execution through the Drafter generation pathway is demonstrated.** The complete graph plan passed its JSON schema, but failed existing serialization checks. **Accepted, shared-validator-passing GSN generation is not demonstrated.**

The returned plan is structurally invalid and its prose is unusable under the observed decoder interpretation. No physical safety conclusion or trustworthy safety argument follows. These observed model-plan and serving compatibility issues are preserved for the Drafter teammate; no code correction or downstream integration was attempted.
