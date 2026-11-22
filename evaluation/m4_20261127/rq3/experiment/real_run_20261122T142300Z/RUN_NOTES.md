# RQ3 run notes — development only

- Commit: `d6a522af7e0f1e92591b3b450522feaa1d6b8de6` (`origin/main` after PRs #30–#33).
- Checkpoint: `Qwen/Qwen3-32B`, revision `9216db5781bf21249d130ec9da846c4624c16137`.
- Batch: frozen `rq3-batch/0.1.0`, 108 requests; original smoke replies and failed attempts are retained in `RQ3_RESPONSES.jsonl`.
- Server used GPUs 1 and 2 (L40S, driver 595.99.02), loopback port 8000, BF16, TP=2, 24,576 context, one sequence, 0.90 GPU memory utilization, thinking disabled.
- Runtime compatibility deviation: Outlines rejected the frozen `json_object` format (HTTP 400). XGrammar accepted it but FlashInfer sampling JIT failed because the installed CUDA 13.4 compiler and bundled toolkit headers were incompatible. The successful smoke used installed vLLM's native top-k/top-p sampler via per-process `VLLM_USE_FLASHINFER_SAMPLER=0`. Frozen model, prompt, temperature 0.6, top_p 0.95, top_k 20, max_tokens 8192, JSON response format, and request inputs were unchanged. See the three saved server launch commands and logs.
- The mutation benchmark is development-only: two source groups (one previously exposed real execution and one synthetic), zero independent groups, and developer-authored labels pending blind review.
- Condition C is checker-admission status only. It does not test independently verified physical checker evidence and supports no checked-evidence advantage claim.
