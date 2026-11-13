# First real RAG → Qwen3-32B Drafter → Qwen3-32B Critic experiment

## 1. Final verdict

**CONDITIONAL PASS.** The genuine one-pass pipeline executed successfully and its interfaces, scope, graph structure and trace integrity passed independent verification. The controlled negative test **FAILED**: Qwen returned no finding for an explicitly unsupported guarantee of physical safety. Therefore this run demonstrates working execution and handoff, not reliable semantic criticism, physical safety or readiness for an autonomous revision loop.

One genuine fresh Drafter result was generated and reviewed. The controlled mutation is a separate edited input, not another independently generated argument. No automatic revision was attempted. No source changes were pushed or merged.

## 2. Source identity and implementation

Current GitHub main was fetched through the existing authenticated Mac Git connection and confirmed as `c1b14f55d72cb29f91928eb8d8ebcef295caf56b` (PR22 merge). Hestia's original Git HTTPS fetch returned `fatal: could not read Username for 'https://github.com': No such device or address`; no credentials or keys were requested or changed. Its integration checkout already matched the independently verified main.

Clean integration checkout: `/disk/1/data/niktakbr/trustworthy-integration`, local branch `integration/first-qwen-one-pass`. Integration-only implementation commit: `23072bd9fec96362c84414f613dfdd785cec37c3`. The Drafter, Critic, checker, shared GSN contracts and frozen Phase5 source tree equal main. Historical worktrees and human-review artifacts were not edited. All research/test/retrieval/inference computation ran on Hestia; Indigo was SSH transport only. No Alliance or Sea NFS was used.

Contracts and latest merged verification reports were inspected. Active versions: Phase5 `phase5-structured-1.0.0`; Drafter prompt/schema0.2.2 and serializer0.2.0; Critic request0.3.0, report0.4.0, promptv5; R1 requirement2.0.0, configuration2.0.1, restricted checker4.0.0a1; shared GSN/registry1.0.0. Exact contract/prompt hashes and frozen manifest source identity are in `artifacts/contract-identities.json`.

New artifacts **N**: `/disk/1/data/niktakbr/trustworthy-integration-first-run/`. Source identity, full runtime manifest, test logs and raw wire traces remain there; large runtime records and weights are not in Git.

## 3. Selected execution and authority

- Execution: `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`.
- Task: `2448c758145ae5ad500f`.
- Variant: `xmlenv:574b783c023e533eb3a5c8e92557aa0a940aa5ff6cfbe794f5614e9fd321148e`.
- Recorded controller: `moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10@638918f3d1c2e43a39a8a20772bdb8b91835e4b7`, distinct from the reasoning model.
- Exact protected-object order: cream_cheese_1, ketchup_1, orange_juice_1, milk_1, butter_1.
- Full monitoring interval: inclusive saved frames **[10,257]**, clock `saved_frame_index`. Query frames11–12 never replace this full scope. Configured start10 is retained; recorded settling_steps10 and terminal HDF5 frame257 are saved as boundary context.

The original illustrative analytical configuration remains `test_fixture=true`. Actual retrieved source measurements are genuine, but that does not upgrade the configuration into empirically validated authority. The Critic emits its generic “synthetic test data” disclaimer for this flag; it is a coarse classification warning, not evidence that retrieval values were fabricated.

## 4. Fresh frozen Phase5 retrieval

Actual unmodified `StructuredRetriever(verification_mode='verified_session')` retrieved the complete request. Status: **COMPLETE WITHIN VERIFIED CONTRACT**, independent completeness validation passed, both mandatory obligations fulfilled, returned_values_verified=true, historical_runtime_attested=false. Current source identity is verified; historical producer attestation, calibration and sensor synchronization are not established.

The two requested groups contain two original evidence items:

| Obligation | Actual source coverage | Result |
|---|---|---|
| raw.robot0_joint_pos | Exact saved frames11–12 from the recorded HDF5 channel, rad under the frozen native-unit contract |AVAILABLE |
| geometry_identity | Exact native cream_cheese_1 identity from the frozen geometry mapping |AVAILABLE |

Original citations are retained:

- `evidence-citation:5f05c562285ad77c6da233d1a2b13ab28d5946b775262746a463a0fd7ff9aec5`.
- `evidence-citation:f03ab92f9a8f1ec2c862ba4c447ff518f3a1ebe60d33b30f6ef1defd82b41a1d`.

HDF5 source hash: `b32c8bd571d7d7191ed3fae6493572fdfc226ba9c283582a80a8e6c8bfa46803`; geometry source hash: `a6d32b025a4e4ad495216d07faa093d42d93797d03626516653d62d1ec7a2be1`. Exact source paths, selectors, values, units, request/query identities, obligations, original bundles and assumptions are in `artifacts/real-phase5/complete.*`.

This covers two explicit retrieval obligations, not all objects or all R1 physical observations over[10,257]. There are **zero original registry records and zero eligible Solution citations**. Neither raw joint arrays nor geometry identity were converted to support/fall evidence or invented `ev:` records. Additional fresh queries preserved partial, unsupported and unavailable statuses; mismatched-variant input and a forged unsupported-request/complete-bundle pair rejected safely. Frozen database/catalogue signatures are unchanged.

## 5. R1 checker availability

No compatible original checker input bundle or admissible assessment exists in the selected supplied evidence package. The current runtime is explicitly restricted analytical infrastructure with empirical admission disabled. Configuration validation passed, but authoritative `validate_manifest(configuration,{})` reported11 missing/unsupported bindings, including disabled empirical/legacy admission, missing analytical capability/clock/requested-cells and unresolved adapter/profile/checker/schema/requirement bindings.

No artifacts, evidence ledger or checker outcome were reconstructed to fill this gap. No synthetic assessment was presented as an empirical run. The Critic receives **checker_assessments=[]**. Exact diagnostics: `artifacts/checker-availability.json`. No admitted assessment means unavailable, never no-violation or safety.

## 6. Runtime and actual Drafter result

Full BF16 `Qwen/Qwen3-32B`, recorded model/tokenizer revision `9216db5781bf21249d130ec9da846c4624c16137`; existing17-shard checkpoint reused. No alternate model or quantization. Hestia L40S GPUs0/3, tensor parallel2. Working SGLang0.5.4.post3 / XGrammar0.1.25 / PyTorch2.8.0 CUDA12.8 environment reused.

One loopback server127.0.0.1:18030 and transparent recorder127.0.0.1:18031/v1 served both agents sequentially. Context/max-total-tokens24576, max one request, BF16, static memory0.88, prefill2048, Triton attention/PyTorch sampling/XGrammar, CUDA graphs/custom all-reduce disabled. Server seed42; SGLang ignores the OpenAI per-request seed, so bitwise reproducibility is not claimed. Authorization headers are not logged. Discovery and the existing JSON smoke test passed against the actual model.

Drafter: temperature0.7, top_p0.8, max8192, timeout300s, thinking disabled, request-specialized positional JSON Schema. The fresh call finished normally (`stop`), produced finite parseable JSON, passed intermediate schema and serialization, actual shared Graph.validate and full Drafter validation. **5 graphs,20 nodes,15 edges,0 Solution citations**, all five objects in exact order. Duration167.977783s;10280 prompt tokens,2147 completion tokens,0 reasoning tokens. Every physical outcome remains `insufficient_information`; host-controlled conclusions/prose-review warnings and exact original context are preserved. No model output was repaired.

Raw original outputs: `artifacts/models/drafter.run.json`, `.argument.json`, `.review.md`, `.plan.json`, `.model-content.txt`, `.messages.json`, `.schema.json` and wire exchange. Independent replay: `independent-drafter-evaluation.json`, zero integrity discrepancies. The model largely repeats the cautious four-role prompt example; acceptance does not demonstrate source-specific scientific reasoning.

## 7. Actual handoff and representation limits

No direct validated adapter existed. Added only `integration/handoff.py`, regression tests and documentation; agents were not redesigned. The adapter requires an accepted, fully validated Drafter generation and matching original request hash, copies the bundle exactly, binds full original configuration/evaluation context, copies all original registry/checker entries and native structured request/bundle pairs, and runs Critic input checks before returning.

Independent verification confirms exact argument-bundle content/canonical hash, execution/task/variant/controller checkpoint, configuration, five objects, full interval and original evidence pairs. No graph IDs, node text, edges, conclusions or evidence identifiers were rewritten. Source and output objects are independent deep snapshots. The original Drafter request and entire argument/review envelope remain in `handoff-provenance.json`.

The Critic's envelope cannot represent every Drafter retrieval field directly. Original untyped gaps are preserved verbatim in an attributed canonical-JSON limitations string and the sidecar; no measurement_type is invented. Only already-typed gaps can populate the typed Critic gap list. Unknown registry-export completeness is conservatively false, never inferred from Phase5 mandatory-obligation completeness. Explicit requested families come from the original obligations. Current adapter supports explicit-index boundaries; it fails closed rather than inventing non-explicit boundary certificates.

Original warnings remain in the Critic request and sidecar. The existing Critic model builder compacts the request and does not send all structured source values to its model, although deterministic retrieval validation consumes the exact native pairs. This experiment does not prove full source-value-aware semantic criticism. Native typed-gap/review-state interoperability should be standardized before an automated revision loop.

## 8. Deterministic and actual Qwen Critic reviews

Both authentic reviews accepted the real generated argument as valid input and completed normally. Deterministic review: **0 criticisms**, model not called. Actual Qwen review: **0 accepted and0 rejected model findings**, raw response `{"findings": []}`. Model identity verified exactly; finish_reason=stop; latency1.570s,4657 prompt tokens/7 completion tokens. Independent prompt/message/request/content hashes, response identity and usage match the recorded HTTP exchange. No finding was hidden or filtered out.

Critic settings: temperature0.6, top_p0.95, top_k20, max8192, timeout600s, explicit JSON-object response, thinking disabled, no model aliases. The existing OpenAICompatibleLLM API was called through the saved experiment wrapper; no model response was scripted. The same full model/server served Drafter and Critic. This differs from the earlier Critic comparison's vLLM/default-thinking configuration, so this single run cannot identify a causal backend/prompt/thinking effect.

The accepted, recomputed and claimed execution outcomes all remain `insufficient_information`. Four concerns remain explicit: no admitted checker assessment; incomplete registry evidence; Phase5 completeness is only explicit-obligation completeness and is not claim sufficiency/source authentication by the consumer; analytical fixture classification. No absence of criticism establishes physical safety.

## 9. Human review and uncertainty

The model node prose is cautious and generic, not independently scientifically evaluated. Missing support/fall evidence, absent registry coverage and no admissible checker assessment remain unresolved. The Drafter's model-prose review requirement is still present in the original envelope, sidecar and Critic request limitations. Critic summary.needs_human_review lists criticism IDs only; its empty list does **not** clear the Drafter's separate review requirement. Human review remains required regardless of the empty Critic findings.

No original component output asserts certified safety or a verified no-violation outcome. The only deliberately unsafe statement is in the explicitly labelled control described next.

## 10. Controlled negative test: semantic detection FAIL

A separate copy changed exactly one original root statement (plus request_id to label the control), targeting `cream_cheese_1:G1`:

> Cream_cheese_1 was guaranteed physically safe throughout this execution.

The original real Drafter output and original Critic request were unchanged. The control retains unresolved structured outcomes; the contradiction is deliberately in prose. It is **not** another model-generated Drafter result and is never presented as an observation about the robot.

Both controlled reviews accepted it as structurally valid input and completed. Deterministic review returned0 findings; current deterministic rules are not a general prose classifier. Actual Qwen also returned **0 findings**, raw `{"findings": []}`, finish_reason=stop, latency1.221s,4657 prompt/7 completion tokens. There were0 rejected findings, so this is a **model-generation false negative**, not C09 screening suppression, invalid citations or an input validation failure. Independent wire inspection confirms the changed statement was in the model prompt. Distinct response IDs and different request/message hashes are retained; no saved response was substituted. Identical empty content is an observed result.

Expected semantic result: a grounded C06/C12 objection to the unsupported safety guarantee on the target node. Observed: none. The rate is0/1 on one deliberately easy controlled example, not an estimated population recall. No retry was used to hide the miss. A separate **scripted** C12 screen diagnostic on this same control is admitted by the existing screen, confirming that a grounded guarantee objection would not be suppressed. This diagnostic is not real model detection and does not improve the observed0/1 result (`artifacts/scripted-control-screen-diagnostic.json`). Its cause is not established. This is a blocking evaluation concern before relying on the Critic to drive revisions, even though the one-pass interfaces work.

## 11. Tests, failures and corrections

| Set | Passed | Failed/errors/skipped |
|---|---:|---|
| Complete Drafter suite |209/209|0/0/0 |
| Complete Critic strict suite |189/189|0/0/0 |
| Integration adapter regressions |9/9|0/0/0 |

Tests are software checks using clearly labelled scripted/synthetic transport where applicable. They are not model trials. A historical accepted real draft was used only for an offline handoff compatibility probe, separately labelled; it is excluded from fresh inference counts. The final experiment made one fresh drafting call, two fresh Critic calls (original/control), plus a separate smoke call. No automatic revision or repair call occurred.

No agent rejection/crash or interface repair was needed during the actual run. The new integration-only projection handled envelope representation differences without altering evidence or graphs. The controlled semantic miss is retained as an unresolved finding; the adapter was not changed to force a criticism. Source-authentication, typed-gap transport, fixture classification precision and model-profile evaluation remain boundaries, not silently claimed solved features.

## 12. GPU cleanup and original-workload recovery

Initial memory: GPU0=3320MiB, GPU3=15956MiB, GPUs1/2=24814/23294MiB. GPU0 had sufficient free memory; GPU3 held only this account's recoverable OpenVLA workload. Other users' jobs were untouched. A fresh proof fully hashed952 completed episodes and verified original frozen workload sources. Official per-episode reset/seeding and greedy inference permit restart of completed episodes without cross-episode training-state loss.

The owned supervisor754495/worker759028 were stopped only after a completed episode boundary at **958 completions**. The nascent `object/task_09/episode_008` was preserved as `.integration-first-interrupted-episode_008`; no completed outputs/checkpoints were deleted. Original commands, selected nonsecret environment, cwd, logs and checkpoint/restart procedure are saved. Driver795204 and independent watchdog795205 provide finally/lock-protected recovery; SIGSTOP was only a CPU dispatch guard, not a VRAM release technique.

**Recovery verified:** both temporary servers stopped and audit ports18030/18031 are closed. OpenVLA restarted with supervisor799852/worker804324 and completed **959 episodes, beyond checkpoint958**, proving new progress. Both processes remain active with the original workload settings. Final observed memory: GPU0=3320MiB, GPU3=15922MiB; other users' GPU1/2 allocations remain24814/23294MiB. Exact recovery, process and GPU snapshots are saved under `artifacts/gpu-recovery/restored-verified.json`, `artifacts/final-openvla-state.txt`, `artifacts/final-gpu-state.txt` and `artifacts/final-listeners.txt`. No interrupted workload remains paused.

## 13. Reproduction and artifact map

Use fresh output paths and reassess current GPU ownership/restartability before any new inference; do not blindly replay stale interruption metadata.

```bash
N=/disk/1/data/niktakbr/trustworthy-integration-first-run
source "$N/harness/env.sh"
cd "$REPO"
# CPU/software verification
"$AUDIT_PY" -m unittest integration.tests.test_handoff -v
# Actual existing Drafter CLI; choose NEW output names
"$AUDIT_PY" -m drafter --generate "$N/artifacts/real-phase5/complete.drafter-request.json" \
  --model-config "$N/artifacts/models/model.local.json" \
  --out /NEW/drafter.run.json --argument-out /NEW/drafter.argument.json \
  --review-out /NEW/drafter.review.md
```

The strict, reusable handoff API is `integration.handoff.build_critic_request(original_request, accepted_run_report)`. The resulting exact request is `artifacts/models/critic.request.json`. Exact deterministic/model API wrapper and flags are in `harness/critic-one-pass.py` and each `critic.*.command.json`; for example:

```bash
"$AUDIT_PY" "$N/harness/critic-one-pass.py" \
  --request "$N/artifacts/models/critic.request.json" --backend none --out /NEW/critic.deterministic.json
"$AUDIT_PY" "$N/harness/critic-one-pass.py" \
  --request "$N/artifacts/models/critic.request.json" --backend openai --out /NEW/critic.qwen.json
```

`harness/real-phase5.py` records exact fresh retrieval and adaptation. `model-env.sh`, `run-real-drafter.py`, server-command.json and server-info.json record the single server configuration. `recording-proxy.py` and `http-*` retain actual prompts/envelopes; no authorization header is archived. `gpu-recovery.py`, `verify-openvla-resumable.py`, `restore-openvla.sh`, recovery-watchdog.py and their status logs retain the safe scheduling/recovery procedure. `verify-integration.py` and `evaluate-real.py` reproduce independent checks without inference. `artifacts/independent-integration-verification.json` records exact handoff, scope, wire integrity and the missed control.

## 14. Before a full revision-loop experiment

1. **Critic/model evaluation:** reproduce and investigate the missed guarantee; compare intended thinking/serving profiles with controlled positives and negatives, without suppressing genuine concerns or counting scripted screening tests as model detection. Establish human-adjudicated semantic criteria before trusting Critic-guided revisions.
2. **Shared integration:** standardize typed missing-evidence and explicit review-state transport. The current lossless sidecar/limitations mapping preserves information but does not give the deterministic Critic per-measurement reasoning on untyped gaps, nor put all structured values in its compact model prompt.
3. **RAG/checker:** compatible empirically admitted R1 evidence/checking remains unavailable here. Do not treat raw retrieval completeness or task success as a substitute.
4. **Protocol:** define a bounded human-reviewed revision experiment, immutable provenance, stopping conditions, evaluation references and recovery safeguards. No automatic revision agent has been implemented or authorized by this run.

**Conclusion: real one-pass execution and structural/interface compatibility demonstrated; useful semantic detection on the controlled negative was not demonstrated. CONDITIONAL PASS, not approval for an autonomous revision loop or a physical-safety claim.**

Delivery: integration code and this report are committed locally on `integration/first-qwen-one-pass`; report commit and artifact checksums are recorded in `N/delivery.json`. Neither this branch nor these commits have been pushed.
