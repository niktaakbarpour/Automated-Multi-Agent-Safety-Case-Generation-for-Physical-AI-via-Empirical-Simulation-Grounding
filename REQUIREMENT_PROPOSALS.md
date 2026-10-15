# Safety requirement proposals — pilot v1

This component generates unreviewed requirements only. It does not implement safety
cases, events, retrieval, critics, revisions, or policy changes. The original inventory,
recordings, and reviewed requirement collections remain unchanged.

## Input and provenance

`src/requirement_proposals.py prepare` reads the actual `data/tasks.json` and existing
BDDL evidence. It preserves the existing task ID. No designated development task was
found, so selection uses stable task-ID order among verified exact instruction matches;
outcomes are never used. The development task is `2448c758145ae5ad500f` (LIBERO Long
task 0): put both the alphabet soup and the tomato sauce in the basket.

The input is saved in `data/requirement_inputs/development.json`, with source-file
hashes, JSON pointers, and `provenance.json`. It excludes outcome records, trajectories,
videos, frame counts, measured initial poses, and observed failures. Native entity
bindings retain their reference run ID, because native IDs are run-specific. BDDL
initial predicates and declared regions are task declarations, not executed outcomes.
Measurement inventory is a list of field names and limitations, with no measured values.

The required measurement list allows explicit missing measurements with null IDs.
Structural validation reports inventory coverage; it never establishes scientific
validity, compliance, or approved safety limits. Proposed IDs are deterministic
`proposal-<20 hex characters>` allocated in application code. Reviewed `requirement_id`
records and the existing registry are left untouched until a separate review workflow.

## Model and backend

Exact official repository: https://huggingface.co/Qwen/Qwen3.8-27B
Resolved revision: `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`.
Original BF16 weights: 55,563,006,776 bytes. GPU 1 has about 45 GiB, so this
configuration uses BF16 plus 20 GiB of vLLM CPU weight offload; no quantization.
CPU offload may be slow on PCIe. A larger GPU or multiple GPUs would avoid offload;
quantization is a separate change requiring an explicit choice.

Official references consulted:
- Model card: https://huggingface.co/Qwen/Qwen3.8-27B
- Serving recipe: https://recipes.vllm.ai/Qwen/Qwen3.8-27B
- Offload: https://docs.vllm.ai/en/latest/configuration/engine_args/#cpu-offload-gb
- Pinned backend request handling: https://github.com/vllm-project/vllm/blob/v0.31.0/vllm/entrypoints/openai/chat_completion/protocol.py

Backend: vLLM 0.31.0 with Transformers 5.19.0 in `.venv-requirements`. Installation,
dependency checking, full package versions, immutable weight hashes, commands, server
logs, and backend settings assertions are saved under `reports/requirement_pilot_queue`.
No setup or download runs until storage is sufficient. GPU use is restricted to physical
GPU 1 through `CUDA_VISIBLE_DEVICES=1`; no project work uses GPUs 0 or 2. The server
binds only to `127.0.0.1:8027` and is stopped after this pilot by its own supervisor.

Persistent model cache: `/local/home/niktakbr/.cache/huggingface`. The queue requires
roughly 222 GiB free before installation/download, preserving the existing experiments'
150 GiB reserve plus model and environment budgets. Downloads pause if the reserve
is approached. No results or unrelated files are removed to make space.

Thinking enabled, medium reasoning effort, temperature 1.0, top_p 0.95, top_k 20,
min_p 0, presence_penalty 0, repetition_penalty 1. Context: 32,768 tokens;
combined reasoning/final output budget: 6,144 tokens. Seeds: 1000, 1001, 1002.
Inputs are rejected rather than truncated. Output truncation is a failure. The backend
audit asserts actual request-to-sampling/template handling; smoke checks the exact
rendered template, token usage, reasoning separation, and complete final answer.

## Commands on Hestia

```bash
cd /local/home/niktakbr/trustworthy_project
# Already prepared; do not overwrite an existing input directory:
python3 src/requirement_proposals.py --project "$PWD" prepare
# Queue: lightweight process; setup waits for GPU 1 and persistent storage:
python3 src/queue_requirement_pilot.py
# Repeat once the pinned backend is serving (choose a new output directory):
.venv-requirements/bin/python src/requirement_proposals.py --project "$PWD" pilot \
  --config reports/requirement_pilot_queue/resolved_config.json \
  --output data/requirement_pilots/repeat-unique-name
```

Persistent session: `tmux -L trustworthy-requirements-gpu1`, session `pilot`.
Live status: `reports/requirement_pilot_queue/status.json`.
Outputs: `data/requirement_pilots/<UTC timestamp>/generation_01` through `generation_03`.
Each generation stores raw responses, final text, validation reports, original parsed
proposals, allocated candidate IDs, and an editable `human_review.json`. At most one
format/reference correction is allowed and both attempts are preserved. No best-output
selection or task expansion occurs. Humans alone fill review decisions.

Missing information includes approved contact policy, force limits, sensor channel
mapping/calibration, collision extents/support bindings, continuous substep contact
history, fragility, damage, and human/restricted-region annotations. These remain unknown.
The initial preparation's inventory scans only selected frame keys; no claim is made that
every potential measurement exists on every transition. Safety requirements may be zero.
