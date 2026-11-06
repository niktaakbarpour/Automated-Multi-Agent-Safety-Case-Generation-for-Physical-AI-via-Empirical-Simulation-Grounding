# Drafter PR20 Phase 5 ordering correction and final verification

## Verdict

**PASS within the tested software and controlled-integration scope. MERGE recommendation for the repaired implementation after its commits are incorporated; DO NOT MERGE the unchanged PR20 head.** The previous CONDITIONAL PASS report is retained unchanged. Three actual Phase5→Qwen3-32B drafts now pass every required software stage. This does not establish physical safety or scientifically correct reasoning.

## Revisions and scope

- PR20 head: `77012ca6c82cdc5b813e74c4f8ce5f6bed4029d9`, branch `fix/drafter-audit-and-phase5`.
- Latest main fetched and independently checked remotely: `cc0c9be2695948178fe5b23af0ec740e4331be1a`, including merged Critic corrections. No newer main commits were present.
- Dedicated repair branch: `fix/drafter-pr20-independent-corrections`.
- Existing repairs incorporated as ancestors: `85dcbbfed07f87a8549845ab6c71589eee0fae8d`, `9d9dd6cd28aed9529c7b4978123c5cac67add117`, `a1835705adc5c1ed85bf800c49d195e1d9f743e2`. Main was already incorporated by `b0dce092564f843a524062ce4cccf5f022349622`; no redundant merge was created.
- New artifact root **N**: `/disk/1/data/niktakbr/drafter-pr20-phase5-order-verification-20261106/`.
- Source: `/disk/1/data/niktakbr/drafter-pr20-verification-20261105/repo`; matching local isolated checkout `/Users/nikta/drafter-pr20-verification/source`.

The complete preceding `DRAFTER_PR20_AUDIT_AND_COMPLETION_REPORT.md`, actual B-01 request/plan/schema/report and model trace were read. Prior artifacts remain unchanged. No frozen data, checker, Critic, shared GSN or human judgments were modified. No GitHub push, review or PR merge was performed. All test/retrieval/grammar/inference computation ran on Hestia; Indigo carried SSH traffic only. Neither Alliance nor Sea NFS was used.

## Root cause and general correction

The prior request-specialized graph schema constrained only total graph count and membership in the global object roster. Every array position accepted every object. Namespaces and Solution IDs were also drawn from the entire request. The host serializer correctly required exact roster order. Thus a complete alphabetical response could satisfy the decoder schema yet fail `plan_object_roster_or_order`.

The preserved actual response ordered graphs as `butter_1, cream_cheese_1, ketchup_1, milk_1, orange_juice_1`; the configuration order was `cream_cheese_1, ketchup_1, orange_juice_1, milk_1, butter_1`. Old schema acceptance and new schema rejection are recorded in `N/artifacts/preserved-counterexample.json`. No graph was missing, but ordering was an existing contract requirement.

`drafter/plan_schema.py` now constructs Draft2020-12 `prefixItems` in exact configuration list order, with `items:false` and exact length. Each position has:

- Its exact `object_id` constant.
- Escaped exact object prefixes for root, node and edge endpoint IDs.
- Only eligible original registry evidence IDs belonging to that object.
- No Solution alternative if that object's eligible catalogue is empty.

This acts **before sampling**, rather than sorting an invalid model result. The host serializer's independent roster/order, endpoint, evidence-owner, scope, prose and graph checks remain unchanged. The standalone graph projection selects the same object's positional schema. Generation never renames an object, rewrites a citation, invents a registry record or repairs a returned graph.

Decoder schema and prompt versions are0.2.2; serializer remains0.2.0. The prompt explicitly distinguishes configuration order from alphabetical or retrieval-group order. The run-report schema retains historical prompt versions for prior traces; accepted current output still requires the current prompt. Wrapper/shared GSN contracts remain unchanged. README and CONTRACT describe this boundary.

## Regression and decoder verification

Eight new test methods cover arbitrary two-, four- and five-object rosters and reversed configurations; reordered outputs rejected without mutation by both schema and host; missing/duplicate/extra/unknown objects; root/node/edge cross-object namespaces; escaped regex punctuation; cross-object Solution leakage; evidence ownership and exact original record provenance after configuration reorder; independent schema copies and unchanged input configuration.

| Set | Discovered / passed | Failed / errored / skipped | Artifact |
|---|---|---|---|
| Full Drafter suite, jsonschema4.25.1 |209 /209|0 /0 /0|`artifacts/tests-client425.json`, `.log` |
| Full Drafter suite, integrated jsonschema4.19.1 |209 /209|0 /0 /0|`artifacts/tests-integrated419.json`, `.log` |
| New ordered-plan tests |8 /8|0 /0 /0|`artifacts/ordered-regressions.log` |
| Actual Qwen tokenizer / XGrammar CPU cases |13 /13|0 failures|`artifacts/qwen-tokenizer-grammar.json` |

The eight new methods are included in209, not additional independent samples. Grammar cases are scripted CPU probes, not model results. Exact XGrammar0.1.25 rejects the preserved alphabetical response through EOS, accepts valid full plans, and rejects reordered objects, cross-object node IDs, evidence-as-edge endpoints, truncated JSON, single-character text and null Solution citations. The real-tokenizer checks cover archived and real-Phase5 requests. No dependency version was changed to conceal a failure.

## Fresh real Phase 5 verification and compatibility

Actual `phase5-structured-1.0.0` `StructuredRetriever(verification_mode='verified_session')` was rerun against the unchanged frozen release and databases. Exact commands and source are in `N/harness/real-phase5.py`. Previous real bundles are separately preserved in `artifacts/prior-real-phase5`; fresh results are `artifacts/real-phase5`.

The legitimate execution remains `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`, task `2448c758145ae5ad500f`, variant `xmlenv:574b783c023e533eb3a5c8e92557aa0a940aa5ff6cfbe794f5614e9fd321148e`. All five objects, the recorded controller checkpoint and full saved-frame monitoring window[10,257] remain bound. Query frames11–12 do not narrow the monitoring window. Original analytical configuration classification and `test_fixture=true` are retained; this does not relabel actual retrieved measurements as fabricated data or establish empirical checker authority.

Fresh complete, partial, unsupported and unavailable responses are preserved as attributed context; a mismatched-variant invalid-scope pair rejects. The exact previously unsupported object-filtered request still receives an authentic refusal; pairing it with forged completeness rejects. Complete context contains two groups/two actual items (raw joint positions and geometry identity), zero original registry records and zero eligible GSN Solution IDs. This limitation is retained, not filled with fabricated records. No authentic unverified-plan status was manufactured.

Original request/bundle identities, source selectors/values/hashes, obligations and missing statuses, assumptions, limitations and `evidence-citation:` IDs remain intact. Existing `ev:` IDs are not invented or renamed. Critic files equal current main; the adapter still composes the repaired current-main retrieval consumer and its public-request validation. Consumer consistency is not independent authentication; source verification here was performed by the actual frozen producer. Retrieval completeness is not evidence that R1 holds.

## Actual Qwen3-32B evaluation

Full BF16 `Qwen/Qwen3-32B`, model/tokenizer recorded revision `9216db5781bf21249d130ec9da846c4624c16137`, reused existing17-shard weights; no substitute model or quantization. Existing serving environment: Python3.12.14, SGLang0.5.4.post3, XGrammar0.1.25, PyTorch2.8.0/CUDA12.8, transformers4.57.1. Hestia L40S GPUs0/3,46068MiB each, tensor parallel2. Loopback server18030 and transparent recording proxy18031; neither exposed publicly.

Inference settings: temperature0.7, top_p0.8, max8192 completion tokens, timeout300s, thinking disabled, JSON Schema constraints. Server seed42, context/max-total-tokens24576, one running request, BF16, static memory0.88, prefill2048, Triton attention/PyTorch sampling/XGrammar, CUDA graphs and custom all-reduce disabled. SGLang ignores the OpenAI per-request seed; these are fresh stochastic calls sharing a recorded server seed, not bitwise reproducible separate seeds or reused responses.

Model discovery and the existing JSON smoke test passed against the actual server. All three fresh drafting calls completed with the configured model identity and `finish_reason=stop`; each parsed as finite JSON, passed its positional intermediate schema, serialized successfully, passed actual shared `Graph.validate` and passed full Drafter validation. Independent wire/request/prompt/response/source hash replay reports zero integrity errors.

| Attempt | JSON / plan schema | Serialization / shared GSN / full Drafter | Accepted graphs/nodes/edges | Eligible Solution citations | Physical outcomes | Seconds | Prompt/completion tokens |
|---|---|---|---|---|---|---|---|
| B-01 |PASS/PASS|PASS/PASS/PASS|5/20/15|0|all insufficient_information|167.372029|10280/2147 |
| B-02 |PASS/PASS|PASS/PASS/PASS|5/20/15|0|all insufficient_information|164.204981|10280/2145 |
| B-03 |PASS/PASS|PASS/PASS/PASS|5/20/15|0|all insufficient_information|166.881433|10280/2160 |

Exact graph order in all three: `cream_cheese_1, ketchup_1, orange_juice_1, milk_1, butter_1`. No reordered output, inferred citation or missing node was repaired. There were zero new rejected drafts; the prior rejected actual response and new negative decoder/host tests remain preserved.

The model receives the exact original structured context, and the accepted envelope retains it unchanged. With no eligible registry records, all graphs correctly omit Solutions. Scope/provenance remain bound to the original request, configuration and full monitoring interval. Required prose-review markers remain present; no outcome is promoted from `insufficient_information`.

The 20 model-written node statements in each accepted draft closely repeat the prompt's cautious four-role example. They are full sentences, but these experiments do not demonstrate novel, source-specific scientific reasoning. The three model summaries differ and acknowledge missing support/fall evidence. B-03 says “No evidence of falling or handling exclusion is present”; this must be read as a limitation of the supplied/admitted evidence, not a conclusion that no physical falling occurred. No affirmative safety conclusion was observed in the inspected prose. This is assistant qualitative inspection, not independent human reference evaluation or proof that every interpretation is sound.

Prompts, full schema, raw envelopes and model text, intermediate plans, final reports/arguments and Markdown reviews are retained under `N/artifacts/models/`. `independent-evaluation-final.json` records stage outcomes, token usage, response identities and hashes. The recorded runtime production manifest matches all27 recorded production files. Scripted EOS/unit tests are not counted as actual inference; there were three fresh drafting calls and one separate smoke call in this follow-up.

## GPU scheduling and restoration

Initial GPU0 had2608MiB in use and sufficient free memory. GPU3 held this account's OpenVLA workload,15939MiB; GPUs1/2 were occupied by other users and left untouched. Full Qwen requires both0/3. Original supervisor732699/worker736770, command/environment/cwd/configuration/logs and restart procedure were inspected. A fresh proof fully hashed916 completed episodes and verified original frozen workload sources. Episode reset/seeding and greedy inference permit independent completed-episode restart without training-state loss.

The controller waited for an episode boundary, checkpointed919 completed episodes and stopped only the owned recoverable group. Any nascent partial attempt is preserved by rename, not deleted. Driver747064 and independent watchdog747065 guarantee server cleanup and recovery even on an inference error. Exact before/checkpoint/restoration records are in `artifacts/gpu-recovery`; no VLA experiment configuration was changed. CPU-supervisor SIGSTOP is only a dispatch guard, not a GPU-memory release mechanism.

Both temporary servers stopped and audit ports18030/18031 are closed. OpenVLA restarted with supervisor754495 and worker759028 on GPU3. Recovery verified **920 completed episodes, beyond checkpoint919**, and the worker remains active with the original experiment settings. Its interrupted nascent `object/task_08/episode_019` was preserved as `.pr20-order-interrupted-episode_019`; completed outputs were retained. Evidence: `artifacts/gpu-recovery/restored-verified.json`, `checkpoint.json`, `original-job.json`, `restored-launch.json`, logs and final GPU/process snapshots. Final observed GPU memory:0=2608MiB,3=15939MiB; other users' GPUs1/2 remain24798/23278MiB. No original workload is left paused.

## Reproduction and delivery

Use a fresh output directory; existing artifacts are never overwritten:

```bash
N=/disk/1/data/niktakbr/drafter-pr20-phase5-order-verification-20261106
source "$N/harness/env.sh"
cd "$REPO"
"$AUDIT_PY" -m unittest discover -s drafter/tests -t . -v
/disk/1/data/niktakbr/critic-r2-audit-20261105/venv/bin/python \
  -m unittest discover -s drafter/tests -t . -v
```

`harness/model-env.sh`, `run-real-drafter.py`, per-attempt `*.command.json`, `recording-proxy.py`, `gpu-recovery.py`, `verify-openvla-resumable.py`, `restore-openvla.sh` and `recovery-watchdog.py` preserve exact serving, CLI and recovery commands. Before repeating the controller, create fresh state/output paths and reassess ownership, episode checkpoint and occupied ports; do not replay stale interruption metadata. Raw model weights, credentials, environments and large logs remain outside Git.

The existing three repair commits are incorporated. Ordering correction and regression commit: `976f7b48367755f240ab49de3c08359d1d96a424`. New focused local source and report commits are listed in `N/delivery.json` and the final delivery response. No push or merge was performed.

**Recommendation: MERGE the repaired implementation for controlled integration once these local commits are incorporated into the reviewed PR. DO NOT MERGE the unchanged remote PR20 head.** A safe route, after explicit push approval, is to publish `fix/drafter-pr20-independent-corrections` as a separate branch and open a follow-up/replacement PR. Alternatively, the PR owner can bring current main into PR20 and cherry-pick the earlier three focused commits plus the new ordering-fix/report commits; do not force-push over the teammate's branch.

Remaining limitations are non-blocking for this bounded software integration: only three stochastic attempts on one genuine bundle; generic example-derived model reasoning; no new eligible registry Solution evidence; no general empirical reliability claim; arbitrary prose still requires review; external source authentication and scientific argument evaluation remain separate responsibilities. The ordering failure is corrected before generation, the actual frozen API remains compatible, and genuine Phase5→Drafter generation has now been demonstrated.

## Final answers

1. Root cause corrected generally: **YES**, exact request positions are enforced before sampling, with object-specific namespaces and evidence catalogues.
2. Regression/full suites: **PASS**,209/209 in both environments; original failing response rejects without alteration.
3. Genuine Phase5→Drafter: **YES**, three actual Qwen3-32B drafts accepted through all software stages.
4. Scope, identity, provenance and uncertainty: **PRESERVED** within the validated contracts; zero fabricated Solution records.
5. Current-main/Critic compatibility: **VERIFIED** with fresh actual retrieval; no Critic/checker/RAG modifications.
6. GPU cleanup and job restoration: **VERIFIED**, completed count919→920 and active resumed worker.
7. Ready to merge: **YES for this repaired branch in controlled integration after review/incorporation; NO for unchanged remote PR20.** No blocking defect remains in this tested scope; scientific quality and broader empirical reliability remain unestablished.
8. Pushed or merged: **NO**.
