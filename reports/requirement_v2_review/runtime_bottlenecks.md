# Runtime bottlenecks (analysis only; no setting changes applied)

The completed pilot used Qwen/Qwen3.8-27B revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0, original BF16 weights (55,563,006,776 bytes), 20 GiB CPU weight offload, eager execution, and one concurrent sequence. Thinking was enabled at medium reasoning effort. The three recorded calls lasted 1570.55, 1929.66, and 4036.22 seconds, producing 1441, 1893, and 3960 tokens respectively. These are end-to-end rates of about 0.92, 0.98, and 0.98 output tokens/s; logs show about 0.9–1.0 tokens/s during decoding. Reasoning-token counts were 1149, 1597, and 2445.

CPU offloading is a likely principal bottleneck: it requires repeated CPU/GPU weight access during forward passes. This is inferred from the configuration and throughput, not an isolated performance benchmark. Eager execution and single-sequence serving also constrain optimization. A long prompt affects prefill and cache use; reducing it does not guarantee faster per-token decoding. The v2 offline request uses 3584 prompt tokens instead of 13383 (73.2% fewer).

Possible later improvements, requiring separate review/measurement:
- Use a GPU with sufficient VRAM, or tensor parallelism across suitable GPUs, to hold BF16 weights without CPU offload. Check memory headroom and interconnect topology first.
- Benchmark CUDA graphs/compilation after validating startup and output behavior; do not silently remove eager execution from the comparison.
- Benchmark asynchronous offload prefetch if supported and compatible with the pinned backend.
- Keep concise, shared-prefix inputs while retaining complete provenance separately.
- Quantization, smaller models, disabling thinking, or changing reasoning/sampling are separate experimental changes, not part of the planned v2 comparison.

The comparison configuration preserves model revision, BF16 precision, no quantization, all reasoning and generation settings, the same task, and seeds 1000/1001/1002. No GPU job was launched for this review.

References: https://docs.vllm.ai/en/v0.31.0/cli/serve/ ; https://mujoco.readthedocs.io/en/stable/python.html
