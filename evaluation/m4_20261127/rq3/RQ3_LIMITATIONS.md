# RQ3 limitations (M4 task A4)

Part A was written on November 22, before any GPU output existed, so it cannot be shaped by the results. Part B is filled in from the run files after the GPU run. Each line in Part B points to the file it came from.

## A. Known before the run

**Sample.** 12 semantic cases (8 mutations, 4 clean controls) built from 2 parent executions. Mutations, controls and the 3 repeats of a parent are paired observations of one execution, so there are 0 independent cases. Both parents were already used in Critic development (P1 is the saved one-pass LIBERO request, P2 is the synthetic Critic Case C). Results describe these 12 cases. They do not estimate performance on new executions, and no significance test is reported.

**Per operator.** M1 has 3 cases, M2 has 2 and M3 has 3. One case changing from missed to detected moves a per-operator rate by a third or a half.

**Labels.** The mutations and their expected objections were written by the Critic owner, and the blind review (GOLD_LABELS_AND_REVIEW.md) was not complete when this was written. Ryiad's CPU validation (RQ3_GSN_INPUT_HANDOFF.md) confirms that the inputs are structurally valid and that the 3 validation cases fail the input gate as intended. It gives no verdict on the semantic labels.

**Condition C.** No checker assessment is admitted for either parent, because admission of R1 checker results as physical evidence is blocked and the R1 checker has not been independently validated. C adds only a status sentence saying that no requirement-checked verdict exists. RQ3 therefore cannot say how the model behaves when given a verified checker verdict.

**Condition R.** P1 has no registry evidence records, so for the 6 P1 cases R differs from T by the retrieval context only. P1 also carries one admitted Phase 5 structured retrieval (robot joint positions for frames 11 to 12, identity of cream_cheese_1). The production Critic does not show structured evidence to the model, and RQ3 keeps the production view, so the model never sees those values in any condition. The 6 P2 cases give R 9 synthetic registry-shaped records each.

**Screening.** Model findings are screened against the full case in every condition, so a T finding can cite an evidence ID that T never saw and still be accepted. P2 node IDs are not prefixed with the object, so a P2 finding without `object_id` is rejected as ambiguous, which can turn a correct objection into a miss.

**Rule-only channel.** The rules detect exactly 2 of the 8 mutations (P1-M1a and P2-M1c, both CLAIM-ABSOLUTE-SAFETY, C12) and nothing on the clean controls. Both are M1 cases that use absolute safety wording, which the lexical rule was written to catch. The rule-only detection rate says nothing about M2 or M3 beyond these cases.

**Model and settings.** One model (Qwen3-32B), one prompt (critic-prompt/v5) and one set of decoding settings, taken from the November 13 one-pass run. The 3 repeats are samples at temperature 0.6 from identical inputs. They measure sampling variation only. No per-request seed is sent.

**Exposure.** The P1 parent and an earlier controlled guarantee mutation were reviewed during development, and the November 13 Qwen run already returned zero findings on both. The mutation design was made with that run known.

## B. From the run

- Server, revision and hardware: Qwen/Qwen3-32B revision 9216db5781bf21249d130ec9da846c4624c16137; two NVIDIA L40S GPUs (devices 1 and 2), BF16, driver 595.99.02; see RQ3_RESPONSES.jsonl.meta.jsonl and server_launch_retry3_command.txt.
- Settings differing from frozen values: the five run metadata records have an empty settings_deviate_from_frozen object. The runtime used vLLM's native top-k/top-p sampler through VLLM_USE_FLASHINFER_SAMPLER=0; see the runtime note below. Model, prompts, batch inputs and frozen decoding parameters were retained.
- Output validity: 108/108 scored responses valid, 36/36 in each of T, R and C. All successful responses finished with stop; none was cut off at the token limit. See scored/RQ3_PER_CASE_RESULTS.csv and scored/RQ3_SUMMARY.csv.
- Retry history: the raw JSONL retains 117 attempts: 108 successful responses and 9 failed attempts. Those failures belong to three logical requests, each of which subsequently succeeded on attempt 4; the other 105 requests succeeded on attempt 1. The failed attempts were three HTTP 400 structured-output backend rejections and six HTTP 500 engine errors. They are not nine failed logical requests.
- C interpretation: C is checker-admission status only. No independently verified physical checker evidence was admitted; do not claim a checked-evidence effectiveness result.
- Mutation detection across 8 cases and 3 repeats per condition: rule-only 2/8; model-only T 8/24, R 9/24, C 10/24; rules-plus-model T 10/24, R 10/24, C 11/24. Clean-control false positives: T 0/12, R 1/12, C 3/12. C remains status-only. Exact stratified results are in scored/RQ3_SUMMARY.csv.
- Labels and scope: mutation labels remain developer-authored; Ryiad's independent mutation-label audit is pending. Two parent groups were used, both development-exposed; there are zero independent groups. These results do not estimate performance on new executions.

## C. Runtime implementation limitation

The successful run used the installed vLLM native top-k/top-p sampler (VLLM_USE_FLASHINFER_SAMPLER=0). FlashInfer JIT could not compile with the installed CUDA 13.4 compiler and bundled headers. The frozen JSON response format was rejected by Outlines; XGrammar accepted it, but the FlashInfer sampler path failed. The native sampler fallback completed the real run. The model, prompt, inputs and frozen decoding values were unchanged. The exact successful server command is preserved in server_launch_retry3_command.txt; full diagnostic logs remain in the original Hestia worktree and are not included in this publication set.
