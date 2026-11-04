# Critic LLM: short model comparison

Status: desk comparison from the official model cards. The practical three-case run on Hestia (`python3 -m critic.compare_models`) has not been run yet, so the choice below is provisional until it has.

## What the Critic needs from a model

Read a GSN argument and a small evidence list, spot unsupported reasoning in node statements, return valid JSON, cite only IDs it was given, and not invent problems in a correct unresolved argument. The rule-based checks already catch ID, scope, coverage and aggregation errors, so the model's job is the wording-level problems (C05, C06, C09, C10, C12, C13). A prompt is about 5k tokens plus up to 8k for the reply, which fits every candidate's context (Qwen3-32B has the smallest: 32k native).

## Candidates

| | gpt-oss-20b | Qwen3-32B | DeepSeek-R1-Distill-Qwen-14B |
|---|---|---|---|
| Size | 21B total, 3.6B active (MoE) | 32.8B dense | 14B dense (Qwen2.5-14B base) |
| Memory | Runs in 16 GB (MXFP4 weights) | About 66 GB of weights in BF16 (estimate: 32.8B × 2 bytes); needs an 80 GB GPU, two GPUs, or an FP8/AWQ build | About 30 GB in BF16 (estimate) |
| License | Apache 2.0 | Apache 2.0 | MIT |
| Reasoning control | Low / medium / high, set in the system prompt | Thinking on by default; `/no_think` or `enable_thinking=False` to turn off | Always reasons in `<think>`; card says it sometimes skips it |
| Structured output | Card lists Structured Outputs and function calling | Not stated on the card; works with vLLM guided decoding | Not mentioned on the card |
| Prompting caveats | Must use the harmony format (vLLM's chat template does this) | Card says do not use greedy decoding; use temperature 0.6, top_p 0.95, top_k 20 | No system prompt; temperature 0.5–0.7 |
| vLLM | `vllm serve openai/gpt-oss-20b` (needs a recent vLLM) | `vllm serve Qwen/Qwen3-32B --reasoning-parser deepseek_r1` (older vLLM also needs `--enable-reasoning`) | `vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` |

The model-card sampling settings are built into `critic/llm.py` (`MODEL_PRESETS`), so each model is run the way its authors recommend.

## Provisional choice: gpt-oss-20b

- It is the only candidate that fits on any single GPU with 16 GB or more, so it will run on Hestia whatever is free, and it is fast (3.6B active parameters).
- Its card documents structured outputs and adjustable reasoning, which matter most for a Critic that must return clean JSON.
- Apache 2.0, like the Qwen model the project already serves.

Second choice: Qwen3-32B, if an 80 GB GPU (or an FP8 build) is available. It is the closest relative of the Qwen model the team already uses for requirement generation, and worth comparing against gpt-oss-20b after the midpoint.

Not taken forward for Friday: DeepSeek-R1-Distill-Qwen-14B. It is built on the older Qwen2.5, its card asks for no system prompt and documents no structured-output support, and it can skip its reasoning step.

The handoff also mentions the Qwen3.8-27B model already used earlier in the project. I could not check its card from here. If it is already being served on Hestia, it is the cheapest extra comparison point: pass it as another `--model` and the Qwen3 sampling preset applies automatically.

## How to run the practical comparison on Hestia

```bash
# terminal 1 (and a second port for each extra model)
vllm serve openai/gpt-oss-20b --port 8000
vllm serve Qwen/Qwen3-32B --port 8001 --reasoning-parser deepseek_r1

# terminal 2, from the repository root
python3 -m critic.compare_models \
  --model openai/gpt-oss-20b=http://localhost:8000/v1 \
  --model Qwen/Qwen3-32B=http://localhost:8001/v1 \
  --repeats 3 --out critic/examples/model_comparison.md
```

It writes a table with JSON validity, whether the expected issue was found in Case A, false positives on Case C, invented IDs and latency per model. Three synthetic cases make this an exploratory comparison, not a benchmark.

## Sources

- [openai/gpt-oss-20b model card](https://huggingface.co/openai/gpt-oss-20b)
- [Qwen/Qwen3-32B model card](https://huggingface.co/Qwen/Qwen3-32B)
- [deepseek-ai/DeepSeek-R1-Distill-Qwen-14B model card](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B)
