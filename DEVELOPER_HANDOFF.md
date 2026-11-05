# Drafter developer handoff: actual Qwen3-32B response

Actual full BF16 `Qwen/Qwen3-32B` revision `9216db5781bf21249d130ec9da846c4624c16137` ran through the existing `--generate` pathway on Hestia GPUs 0/3. Code remains merged main `e7839d64f8ad902e194304e982573b05794f3471`. The original archived fixture, prompt, JSON schema and validators were unchanged.

**Outcome:** one complete actual draft response, schema passed, serializer rejected. The exact run UUID is preserved in `artifacts/attempt-02.run.json`. The response has 7,155 prompt tokens, 2,756 completion tokens, zero reasoning tokens, finish_reason `stop`, and elapsed time 138.356 seconds. No accepted GSN exists.

Observed issues:

- Official rejection: `plan_invalid_edge_endpoint:cream_cheese_1`. Four edges target `ev:` registry IDs that are not declared graph nodes. The existing serializer stops before `validate_argument`/`Graph.validate`.
- The cream-cheese solution node has `evidence_id=null`. All 26 nodes have null evidence IDs; valid node citations total zero. Four registry IDs appear only as invalid edge targets. They are original graph-eligible IDs, so the issue is their use in the plan rather than invented registry identities.
- All 26 statements, the summary and the sole limitation are exactly `R`. No meaningful R1 scope, missing-evidence reasoning or uncertainty is expressed in that prose. The five object IDs and order are correct; the plan has 26 nodes and 25 edges.
- Decoder diagnostic: XGrammar 0.1.25 compiles the full original schema, but its conversion of the original text schema `pattern: "\\S"` rejects schema-valid strings such as `R1` or `R1 remains unresolved for all protected objects.` while accepting `R` through EOS. See `TEXT_GRAMMAR_DIAGNOSTIC_EOS.json`. This constrains the output language, so the prose cannot be used to judge unconstrained Qwen reasoning ability. No schema change was made.
- The successful serving route was unmodified SGLang 0.5.4.post3 with XGrammar, Triton attention and PyTorch sampling. Prior vLLM 0.31.0 and isolated 0.9.2 V1 rejected `uniqueItems`; a V0 processor preflight also reported it as a matcher error. Outlines previously timed out. All failures remain preserved.
- SGLang 0.5.4.post3 accepts but does not apply the OpenAI per-request `seed`. This attempt used explicit server `--random-seed 42`; the requested client seed was also 42. Additional independently started servers with seeds 43/44 were prepared but not run because the first actual draft was rejected.
- Driver flags `graph_semantics=failed` and `evidence_references=failed` are coarse rejection-stage flags here. They do not mean the shared graph validator independently executed both checks. The response did pass the graph-plan JSON Schema.

Artifacts: `attempt-02.run.json` (full original trace), `attempt-02.model-content.txt` (exact assistant content), `attempt-02.model-plan.json` (parsed copy), `attempt-02.model-plan.review.md` (readable rejected plan), `REAL_PLAN_AUDIT.json`, and `TEXT_GRAMMAR_DIAGNOSTIC_EOS.json`, all under `artifacts/`.

No graph was repaired or promoted to accepted. No generation/validation, RAG, Critic, checker or frozen evaluation code was modified. The server is stopped. Investigate serving/schema compatibility and evidence-ID placement before drawing model-quality conclusions. No message was sent automatically.
