# RQ3 experiment configuration (M4 task A3)

This file fixes how the model-only T/R/C comparison is run and scored, before any model output exists. If a run has to differ from what is written here, the difference goes in the run notes and in RQ3_LIMITATIONS.md. The configuration is not edited after the fact.

Status: development only. The benchmark is two R1 parent executions, so there are 0 independent cases, and the numbers this produces describe these 12 cases. They do not estimate how well the Critic does in general.

## What is frozen

| Item | Value |
|---|---|
| Critic | 0.5.0 (PR #29), with the rule-blind RQ3 path from PR #30; file hashes in `freeze/CRITIC_FREEZE.json` |
| Prompt | `critic-prompt/v5`, system prompt sha256 `6e93b4c00e4fc042e281c319b44c798e9b43bc77b82aa366d5edd181ece7ede2` |
| Benchmark | `rq3-mutations/0.1.0` (`MUTATION_MANIFEST.csv`, `mutations/gold_labels.json`) |
| Batch | `rq3-batch/0.1.0`, `experiment/batch/requests.jsonl` sha256 `ce93244c01a0a4eb2741b59807014aed9411668b3880cc1a096071f8ad1d9746` |
| Run manifest | `MATCHED_RUN_MANIFEST.csv`, one row per request |
| Requests | 12 cases x 3 conditions x 3 repeats = 108 |

`build_batch.py --check` rebuilds the batch from the case files and fails if anything differs. `run_batch.py` refuses to start if the batch files do not match the hashes in `BATCH.json`.

## Cases

The 12 semantic-stratum cases go to the model: 8 mutations (M1 unsupported guarantee x3, M2 evidence mismatch x2, M3 scope drift x3) and 4 clean controls (an unchanged copy and a meaning-preserving paraphrase of each parent). Parents are P1 (the real one-pass LIBERO execution, group `original_reviewed:libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`) and P2 (synthetic Case C, group `synthetic:critic_case_c:SYNTH-EXEC-001`).

The 3 validation-stratum cases (missing evidence ID, wrong object, wrong execution) never reach a model. They fail the Critic's input checks, and that rejection is their expected result. They are reported separately as validation rejections. `score.py` does not score them.

Mutations, clean controls and repeats of one parent are paired observations of one execution. They are not independent samples. The independence unit is the canonical source execution group, and every summary row reports `n_groups`.

## Conditions

All three conditions get the same system prompt and the same user-message wording, built by the Critic's own `critic.llm.build_messages`. The model never sees a rule-based finding: `already_found` is empty in every request (the rule-blind setting agreed with Nikta). What changes is how much of the evidence package the model can see.

| Condition | Graphs, conclusion, evaluation context | Evidence records | Retrieval context | Checker admission log | Checker status |
|---|---|---|---|---|---|
| T, text only | yes | no | no | no | no |
| R, retrieval | yes | yes | yes | no | no |
| C, requirement-checked | yes | yes | yes | yes | yes |

C adds one key, `checker_status`. In R1 no checker assessment is admitted (admission of R1 checker results as physical evidence is blocked), so for both parents the admission log is empty and C carries only this status sentence:

> No checker assessment is admitted for this execution. Admission of R1 checker results as physical evidence is blocked in this project, so no requirement-checked verdict is available.

So C is "status only" here. It tests whether being told that no verified verdict exists changes the model's objections. It does not test the model with a requirement-checked verdict, and the write-up cannot claim it does.

With an empty admission log, the R request is byte-identical to what `critic.llm.run(..., rq3_rule_blind=True)` sends, and C minus its status line is the same view. A test checks this against the production path.

Model findings are screened by the Critic's own `critic.llm.screen` against the full case in every condition. So the grounding gates are the same for T, R and C: a T finding that cites a real evidence ID is accepted even though T never saw that record.

## Model and decoding settings

Taken unchanged from the saved one-pass Qwen run (`integration/fixtures/one_pass_20261113/artifacts/models/critic.qwen.report.json`, `llm.settings`). A test checks that the runner builds exactly these settings.

| Setting | Value |
|---|---|
| model | `Qwen/Qwen3-32B` |
| temperature | 0.6 |
| top_p, top_k | 0.95, 20 |
| max_tokens | 8192 |
| response_format | `{"type": "json_object"}` |
| thinking | off (`chat_template_kwargs.enable_thinking: false`) |
| timeout | 600 s |
| repeats | 3 per case and condition |
| per-request seed | none sent |

The largest request is about 23,800 characters with the system prompt (the saved one-pass input was about 19,900 characters and 4,657 prompt tokens), so prompt plus 8192 output tokens should fit the 24,576-token context in the documented Qwen3-32B serving command (DRAFTER_QWEN3_32B_EXECUTION_REPORT.md). If the server runs with a smaller context, long replies may stop at the limit and come back as invalid outputs.

The three repeats are three samples at temperature 0.6 from identical inputs, so they measure sampling variation only. No per-request seed is sent. If the server is launched with a fixed random seed, that goes in the run notes.

## Commands for the GPU run (Nikta)

Serve Qwen3-32B as before, with `--served-model-name Qwen/Qwen3-32B` so the reply names the requested model. If the server answers under another name, add `--accept-model THAT_NAME` to the commands below. Save the exact server launch command in a text file next to the outputs.

From the repo root, on the branch with this tooling:

```sh
# 0. check the batch (CPU, a few seconds)
PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/build_batch.py --check

# 1. smoke test: 3 requests
PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/run_batch.py \
    --batch evaluation/m4_20261127/rq3/experiment/batch \
    --out RQ3_RESPONSES.jsonl \
    --base-url http://127.0.0.1:PORT/v1 \
    --model-revision "CHECKPOINT_OR_REVISION" \
    --limit 3

# 2. the full run: the same command without --limit (skips the 3 already done)
PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/run_batch.py \
    --batch evaluation/m4_20261127/rq3/experiment/batch \
    --out RQ3_RESPONSES.jsonl \
    --base-url http://127.0.0.1:PORT/v1 \
    --model-revision "CHECKPOINT_OR_REVISION"

# 3. only if some requests got no server reply at all (connection error, HTTP error, timeout)
PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/run_batch.py \
    --batch evaluation/m4_20261127/rq3/experiment/batch \
    --out RQ3_RESPONSES.jsonl \
    --base-url http://127.0.0.1:PORT/v1 \
    --model-revision "CHECKPOINT_OR_REVISION" \
    --retry-transport-errors
```

Send back `RQ3_RESPONSES.jsonl`, `RQ3_RESPONSES.jsonl.meta.jsonl` and the server launch command. Nothing else is needed. Scoring runs on CPU.

How the runner behaves:

- Every attempt is appended as one JSON line with the request hashes, settings, raw reply, server metadata (response id, model name, finish reason, token usage), latency and any error. If the run stops, the same command picks up where it left off.
- A request that got any reply is never sent again, whatever the reply was. An unusable reply is a result, not something to retry.
- A request with no server reply is retried only with `--retry-transport-errors`, and every attempt stays in the file. The scorer uses the first attempt that got a reply.
- Each start of the runner writes one line to the `.meta.jsonl` file: arguments, GPU (`nvidia-smi`), Python and platform, the model revision given, and any setting that differs from the frozen values.
- No API key is needed for a local server. Do not put one on the command line. If one is needed, set `CRITIC_LLM_API_KEY` in the environment. The runner never writes it to the output.

## Scoring

```sh
PYTHONPATH=. python3 evaluation/m4_20261127/rq3/experiment/score.py \
    --responses RQ3_RESPONSES.jsonl --out-dir evaluation/m4_20261127/rq3
```

This writes `RQ3_PER_CASE_RESULTS.csv` (one row per request, 108 rows) and `RQ3_SUMMARY.csv`.

Output status, per request:

- `missing`: no line for this request in the responses.
- `no_reply`: the server never replied, or replied with something that is not a chat completion.
- `invalid_output`: a reply that did not finish normally (`finish_reason` other than `stop`), names a model that was not requested, or holds no JSON object with a `findings` list.
- `valid`: everything else, including an empty findings list.

Missing, no-reply and invalid outputs are counted and reported as the `valid_output` rate per condition. They are never counted as negatives. Detection, false-positive and abstention rates use valid outputs as the denominator, so if validity differs between conditions it must be reported next to the rates.

Definitions:

- **Target hit**: an accepted model finding on the labelled node (same `node_id`, and the labelled `object_id` or none). P2 node IDs are not prefixed with the object, so a P2 finding without `object_id` is rejected by screening as ambiguous.
- **Detection** (mutations): a target hit whose category is acceptable for the operator. M1: C05, C06 or C12. M2: C05, C06 or C13. M3: C08, C10 or C13.
- **Target hit, any category**: also reported, so a right-place, wrong-category finding is visible.
- **Clean-control false positive**: a valid output on a clean control with at least one accepted finding.
- **Abstention**: a valid output with an empty findings list.
- **Hallucinated citation**: a finding rejected for citing an evidence ID that is not in the package. Reported as the share of valid outputs with at least one.
- **Rule-only category at target**: the model put a rule-only category (C01, C02, C03, C04, C11) on the target. Screening rejects it, and the per-case file records it.

Three channels:

1. **Rule-only**: `critic.checks.run_all` on each case, with no model. Deterministic, so one result per case and no repeats. It flags P1-M1a and P2-M1c (CLAIM-ABSOLUTE-SAFETY, C12) and nothing on the clean controls.
2. **Model-only, T/R/C**: as above, per condition.
3. **Rules + model**: a mutation counts as detected if the rule-only channel or the model detected it, so a defect found by both counts once. A clean control is a false positive if either produced a finding.

Each summary row gives the pooled rate over all valid outputs, the mean and SD of the per-repeat rates (SD only with at least 2 repeats), `n_cases` and `n_groups`. The SD is over the 3 repeats only. It describes sampling variation on these cases, not uncertainty about other executions.

## Limitations known before the run

- 2 parent groups and 0 independent cases. No significance test is run, and none should be reported.
- C is status only for both parents, as described above.
- P1 has no registry evidence records, so for P1 cases R differs from T only by the retrieval context. Only the P2 cases give R evidence records (9 per case).
- None of the 12 cases has a Phase 5 `structured_evidence` entry, so no structured retrieval bundle is part of this comparison (and `build_messages` would not show one to the model). The P1 retrieval context only mentions in its text that Phase 5 context is kept separately.
- The labels come from one author's construction with a blind review still pending (see GOLD_LABELS_AND_REVIEW.md). The R1 checker itself has not been independently validated, which is why nothing in C relies on its verdicts.
- One model (Qwen3-32B) with one prompt and one set of decoding settings.

## Tests

```sh
PYTHONPATH=. python3 -m unittest discover -s evaluation/m4_20261127/rq3/tests -p 'test_*.py' -v
```

`tests/test_experiment.py` checks that the saved batch equals a fresh build, that every semantic case appears in every condition and repeat, and that no case ID, label or rule-based finding reaches the model. It checks the T/R/C views, the match with the production rule-blind input, and the settings against the saved run. Then it does a dry run through `run_batch.py` and `score.py` with fixed test replies, one per scoring path: a detection, the right node with the wrong category, the right category on the wrong node, an invented evidence ID, an empty list, a non-JSON reply, a rule-only category, a clean-control false positive, a missing output and a request with no reply. Those replies are labelled backend `scripted`, the scorer prints a warning when it sees them, and they are never model results.
