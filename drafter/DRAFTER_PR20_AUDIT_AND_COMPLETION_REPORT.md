# Drafter PR20 audit and completion report

## A. Executive verdict and revision identity

**CONDITIONAL PASS for the repaired branch; DO NOT MERGE the unchanged PR20 head.**

The reproduced software defects have been corrected and verified. Actual Qwen3-32B produced three accepted archived arguments. The genuine Phase5 drafting attempt completed but failed the required graph roster order, so accepted end-to-end Phase5 drafting remains undemonstrated. Incorporate the local repair commits and current-main dependency before reconsidering merge; do not interpret this report as approval of the unchanged PR. No physical safety or scientific argument quality is established. Both interruptions were recovered and OpenVLA made new progress.

- Repository: Automated Multi-Agent Safety-Case Generation for Physical AI via Empirical Simulation Grounding.
- PR20: `fix/drafter-audit-and-phase5`, head `77012ca6c82cdc5b813e74c4f8ce5f6bed4029d9`.
- Actual PR base: `f7de24a86a8b1565bb0ee204635d724bb90ada7d`.
- Current main at inspection and recheck: `cc0c9be2695948178fe5b23af0ec740e4331be1a`, including the independently repaired Critic via PR21.
- Isolated branch: `fix/drafter-pr20-independent-corrections`. Main was brought into this own branch by local integration commit `b0dce092564f843a524062ce4cccf5f022349622`. PR20 itself was not merged, pushed or edited remotely. Critic files equal current main; no Critic implementation was changed to make Drafter pass.
- Local checkout: `/Users/nikta/drafter-pr20-verification/source`.
- Hestia root (**B**): `/disk/1/data/niktakbr/drafter-pr20-verification-20261105/`; source `B/repo`.

All tests, adversarial evaluation, retrieval, grammar checking and inference ran on Hestia. Indigo carried SSH traffic only. No Alliance computation or Sea NFS was used. The root's date is an experiment label; actual timestamps in logs/run reports distinguish November5 preparation from November6 inference. The complete PR diff, original handoff, contracts, changed source/prompts/schemas/tests, actual shared Graph/R1 contracts and frozen Phase5 API were inspected. The previous failed real-run reports and artifacts remain unchanged.

## B. Original findings and independent verification

| Original problem | Developer correction | Independent observation / remaining concern | Verdict |
|---|---|---|---|
| Evidence IDs used as graph edge endpoints | Namespaced node IDs in decoder schema and explicit prompt examples; declared endpoints checked by host | Original real plan replay rejects; mutated `ev:` endpoints reject in grammar and host; undeclared valid-looking node IDs also reject. No repair of model output. | PASS; actual accepted outputs assessed below. |
| All statements, summary and limitation were `R` | Remove incompatible substring regex; length-constrained text plus host usability checks | Original text schema accepts `R` through EOS but rejects longer valid sentences under recorded XGrammar; corrected schema rejects `R` and accepts a sentence and complete plan through EOS. Additional repeated-word/whitespace gaps were repaired here. | PASS for decoder-language boundary; actual full-sentence prose observed; semantic review remains necessary. |
| Decoder/schema incompatibility | Omit unsupported decoder `uniqueItems`; retain host uniqueness | Exact XGrammar0.1.25 compiles the complete schema. Both tiny-ASCII and actual-Qwen-tokenizer checks pass. Duplicate items/IDs and endpoints remain host responsibilities. No dependency substitution. | PASS CPU and actual inference. |
| No accepted real GSN argument | Existing serializer/final validators retained and strengthened | Prior real response remains rejected, never relabelled accepted. Eight fresh drafting attempts were performed, including four after the final guidance correction. | PASS archived generation; Phase5 generation rejected, as detailed below. |
| Contradictory model prose could appear authoritative | Host-controlled summary/conclusion/limitations; attributed original model reasoning and review markers | Scripted contradictory prose remains visible with explicit warning, unchanged insufficient-information outcomes and host conclusions. Removing markers or replacing host text rejects. Review flags do not semantically certify the model's claims. | PASS within documented attribution boundary. |
| Standalone validation weaker than generation | Shared structural helper plus actual Graph.validate | Missing root/strategy/context/subclaims, disconnected nodes, bad edges/citations/scope reject. Additional decoder-shape, provenance and oversized-graph gaps were found and corrected here. | PASS after repairs, tested scope. |
| Missing checkpoint crashed | Check required checkpoint before indexing | Original missing-field case rejects before client construction; API/CLI failure reports and exit1 verified. Additional huge-number crashes were repaired here. | PASS after repairs. |
| Only archived configuration accepted | supplied_registry and phase5_structured profiles | Four-object, five-object and alternate-name configurations are accepted within their explicit saved-frame scope. Archive hashes/derivation remain strict. Empty R1 scope is valid under shared R1 but unsupported by this Drafter and now rejects before inference. | PASS for supported profiles. |
| Missing genuine Phase5 integration | Adapter composes Critic consumer and retains exact context | Fresh frozen retrievals exercise five actual statuses; exact request/bundle/citation/value/provenance semantics retained. Original PR's older dependency allowed the known unsupported-request forgery; corrected below. | PASS after current-main dependency and fail-closed guards; consumer consistency is not source authentication. |

The old actual failed plan is `.../drafter-qwen3-32b-20261105-continuation-01/artifacts/attempt-02.model-plan.json`: five graphs,26 nodes,25 edges,26 statements `R`, zero non-null node citations and four evidence IDs in edge positions. These are **rejected-plan counts**, not accepted shared GSN artifacts. Replay in this audit uses a scripted transport and is explicitly not new inference.

## C. Newly confirmed defects and corrections

| ID | Before-fix reproduction and root cause | Correction / evidence |
|---|---|---|
| P20-01 | Forging any reasoning node's run ID, request/prompt hash, role or serializer still passed standalone validation. Graph.validate checks nonempty provenance but cannot bind it to a Drafter run. Nonphysical context status could also be promoted. | Exact reasoning provenance is bound to the envelope/run, request and supported serializer/prompt. Non-Solution statuses must match proposed/unresolved. Existing missing-review-marker diagnostics remain. New regressions cover removal, tampering and multiple node kinds. |
| P20-02 | Standalone accepted overlong statements and decoder-incompatible graph shapes; an1100-node chain raised an uncaught RecursionError in the shared recursive validator. | A non-mutating projection checks the same compiled graph-plan shape/ID/text limits. More than24 nodes or80 edges rejects before the shared recursive validator. The actual shared validator remains unchanged and is still used for supported-size graphs. Original chain and additional identifier/edge/node variations tested. |
| P20-03 | `TODO TODO TODO`, `placeholder placeholder` and `TBD TBD TBD` were accepted as generated prose. A raw-length limit could also be evaded by a long whitespace span normalized away in model-review text. | Host usability checks reject repeated placeholder labels and require8–1600 normalized characters, at most1600 original characters and at least two distinct alphabetic words. This is not semantic validation. Regression covers summaries, node statements, limitations and standalone model-review text. |
| P20-04 | A supplied `10**1000` monitoring endpoint reached client discovery; scripted generation and standalone validation raised uncaught OverflowError. Upstream interval logic converts integers to finite doubles. | Iterative JSON/Python preflight checks supported numeric range, cycles, key types and depth before hashes/shared validators/client access. Large integers are described as unsupported runtime values, not falsely declared invalid JSON. API/CLI reports remain finite and schema-valid. |
| P20-05 | Supplied builder accepted an empty object roster although the final output contract requires a nonempty argument. | Reject unsupported empty Drafter scope before client access; do not change shared R1's empty-scope semantics or claim a pass for empty scope. |
| P20-06 | The exact authentic Phase5 request refused as UNSUPPORTED could be paired with a forged COMPLETE response and accepted by the original PR's older Critic consumer. | Integrate current main's repaired consumer without modifying Critic; fail closed if its frozen-public-request validator is unavailable and apply that public refusal preflight. Reuse source predicates, not another copied rule set. Fresh real API refusal and forged-pair rejection are preserved. |
| P20-07 | Drafter pinned jsonschema4.25.1 while current Critic's runtime/checker pins4.19.1, preventing a straightforward combined dependency resolution. | Drafter supports `>=4.19.1,<=4.25.1`; full suite passes with both installed endpoints. SGLang/XGrammar/weights unchanged. |

**P20-08, discovered through actual inference:** schema allowed three nodes although root, strategy, context and physical subclaim require four distinct roles. All four first-series outputs passed JSON/schema but failed host serialization. Corrected only this necessary lower bound to four and added a complete four-role prompt example with legal connections. No fixed node order, node injection, output repair or weakened graph check. Schema and prompt are0.2.1; serializer remains0.2.0. Reversed legal node order remains tested. Three additional tests cover the lower bound, order independence and historical prompt provenance.

Additional improvements: published generation-run and early CLI rejection schemas make failure-report validity testable; the optional supplied-plan EOS diagnostic now includes schema/grammar agreement in its overall result. These are not evidence that arbitrary model prose or sources are trustworthy.

Minimal counterexamples and outputs are in `B/baseline/probes-v2/`, `B/baseline/oversized-chain.*` and `B/artifacts/probes-corrected-02/`. The corrected-probes set before the final whitespace guard is supplemented by the final regression test. The temporary audit harness is outside production sources. No frozen evidence, checker outputs, human judgments or shared GSN contract were edited.

## D. Complete tests and test quality

| Set | Actual result | Evidence |
|---|---|---|
| Original PR, original dependency tree |183/183 pass;0 failures/errors/skips | `B/baseline/tests.json`, `.log` |
| Original Drafter on current main dependency |183 run;1 failure and7 errors | `B/baseline/tests-current-main.log`; the original result-summary harness itself initially failed to serialize unittest objects; its traceback is preserved and was corrected separately. These were stale fixture assumptions, not eight independent production defects. |
| Final repaired suite, jsonschema4.25.1 |201/201 pass;0 failures/errors/skips | `B/artifacts/tests-client425-delivery.json`, `.log` |
| Final repaired suite, integrated jsonschema4.19.1 |201/201 pass;0 failures/errors/skips | `B/artifacts/tests-integrated419-delivery.json`, `.log` |
| Independent additional adversarial set |47/47 pass | `B/artifacts/adversarial/summary.json` |
| Exact XGrammar0.1.25 tiny-tokenizer check |Full schema compiles; full sentence and scripted full plan accepted through EOS; `R` rejected | `B/baseline/xgrammar-compatibility.json`, `B/artifacts/xgrammar-full-plan.json` |
| Actual Qwen tokenizer CPU checks |9/9 pass across archived and real-Phase5 schemas | `B/artifacts/qwen-tokenizer-grammar.json` |

The developer's183 tests were genuinely run. The repair adds15 test methods, with additional subtests. Test groups overlap and must not be added as independent scientific samples. Earlier development failures remain saved. No test was skipped to obtain a pass.

The47 independent probes compare mutated final graphs with both actual shared Graph.validate and the stronger Drafter contract, and exercise direct API, CLI, zero-network prevalidation and synthetic HTTP malformed replies. Fake transport tests are explicitly labelled and do not count as Qwen inference. A temporary harness initially constructed a scripted plan from a deliberately null input before invoking production; that harness error is preserved separately and fixed, not reported as a Drafter crash. The original PR's typed checker/GSN references, input/prompt injections, source forgery and malformed-response tests remain active.

The Phase5 tests formerly assumed an object-filtered contact fixture which the real public API rejects. They now use main's corrected global-contact fixture, retain distinct missing mandatory/optional obligations and keep synthetic registry construction labelled synthetic. The production API and frozen data were not weakened. The actual retrieval experiment below is independent of those synthetic fixtures.

CPU grammar checks use XGrammar0.1.25. The real-tokenizer check feeds actual Qwen tokens through the matcher, including EOS151645/151643 configuration. Positive plans are explicitly scripted test objects. Truncated plans, `R`, evidence-as-edge endpoints and null Solution citations reject as appropriate. These checks do not constitute model execution or prove arbitrary schema keywords/semantics are enforced; host uniqueness, membership, evidence and scientific review remain necessary.

## E. Real Qwen evaluation

### Environment and deployment

Full `Qwen/Qwen3-32B`, recorded model/tokenizer revision `9216db5781bf21249d130ec9da846c4624c16137`,17 weight shards totalling65,524,328,560 bytes. Existing checkpoint reused; no smaller model/quantization substituted. Metadata/tokenizer/index hashes and download revisions are recorded; a fresh complete weight hash is not claimed.

Hestia has four NVIDIA L40S with46,068MiB each. Serving environment actually inspected: Python3.12.14, SGLang0.5.4.post3, XGrammar0.1.25, PyTorch2.8.0/CUDA12.8, transformers4.57.1, huggingface-hub0.36.0, sgl-kernel0.3.16.post4, flashinfer-python0.5.0. Driver595.99.02 supports CUDA13.2. Source/client version and both JSON-schema environments are separately recorded.

Server: loopback127.0.0.1:18030, physical GPUs0/3, TP2, full BF16, context24576, max total tokens24576, one request, static memory fraction0.88, prefill2048, Triton attention, PyTorch sampling, XGrammar grammar, CUDA graphs/custom all-reduce disabled, model sampling defaults and server seed42. Client: loopback transparent recorder18031/v1, temperature0.7, top_p0.8, max8192, timeout300s, JSON Schema, thinking disabled, recorded checkpoint revision. Full command/environment is in `B/harness/model-env.sh` and `B/artifacts/models/server-command.json`.

SGLang0.5.4.post3 ignores per-request OpenAI seeds. The three attempts are fresh stochastic requests under recorded server seed42, not cached/saved replies or claimed bitwise reproducible seeds43/44. Server warm-up/probe can advance RNG state; this limit is explicit. No prompt/schema or output fallback is automatic. The recorder forwards actual requests, keeps raw envelopes and HTTP failures and does not synthesize model findings. No authorization headers are saved.

### Per-attempt results

All eight fresh model calls completed with `finish_reason=stop`, correct model identity, parseable finite JSON and valid requested intermediate schemas. Independent replay found zero trace/hash integrity failures. Discovery and smoke tests passed in both series. Raw original outputs are retained; rejected plans have no accepted GSN counts.

| Series / case | JSON / plan schema | Serialization / shared / full validation | Raw plan graphs/nodes/edges | Accepted GSN graphs/nodes/edges | Result |
|---|---|---|---|---|---|
| Initial A1 |PASS/PASS|FAIL / not reached / not reached|5/16/11|0/0/0|Missing strategy/context |
| Initial A2 |PASS/PASS|FAIL / not reached / not reached|5/26/15|0/0/0|Disconnected nodes; strategy lacks subclaim |
| Initial A3 |PASS/PASS|FAIL / not reached / not reached|5/20/10|0/0/0|Disconnected; missing strategy/context |
| Initial B1, real Phase5 |PASS/PASS|FAIL / not reached / not reached|5/25/20|0/0/0|Strategy lacks subclaim |
| Final A1 |PASS/PASS|PASS/PASS/PASS|5/21/16|5/21/16|ACCEPTED |
| Final A2 |PASS/PASS|PASS/PASS/PASS|5/21/16|5/21/16|ACCEPTED |
| Final A3 |PASS/PASS|PASS/PASS/PASS|5/21/16|5/21/16|ACCEPTED |
| Final B1, real Phase5 |PASS/PASS|FAIL / not reached / not reached|5/20/15|0/0/0|`plan_object_roster_or_order` |

Final B alphabetized `butter_1, cream_cheese_1, ketchup_1, milk_1, orange_juice_1` rather than preserving the request roster. All objects were present, but strict ordering is contractual; no reorder was applied. Its zero Solution citations correctly reflect zero eligible registry records. This is an observed model constraint failure, not evidence that the adapter failed to retrieve/admit genuine context.

Each accepted A contains one eligible original cream-cheese registry citation, exact provenance and all five unresolved object outcomes. Execution outcome remains `insufficient_information`. Host conclusions, attribution and all required review warnings pass. Accepted prose contains full sentences, legal endpoints and distinct required roles. Independent shared Graph and full Drafter replay passed all three accepted outputs. Prompt examples heavily influence the prose, which does not demonstrate novel or scientifically sound reasoning.

A qualitative concern remains: all three accepted drafts copied the input caveat “No checker assessment, LLM generation, argument graph or real-run safety conclusion is supplied.” into model limitations. Read as a statement about the new output, this is stale/misleading; it belongs to the input archive context. The original text and review attribution remain visible. No affirmative physical-safety conclusion was observed in the reviewed accepted prose. This review is an assistant inspection, not an independent human reference judgment or semantic proof.

Final trace prompt is `draft-argument-prompt/0.2.1`, decoder schema0.2.1, serializer0.2.0. Exact raw HTTP exchanges, request/response identities, usage, elapsed time, intermediate plans, schemas/messages, run reports, accepted JSON and Markdown reviews are in **F**=`B/inference-final/artifacts/models/`; initial series in `B/artifacts/models/`. Summary files are `independent-evaluation-final.json` and `independent-evaluation-series01.json`. Final production source hashes are frozen in `F/effective-runtime-source-manifest.json` within the models directory.

A required human review must inspect unsupported/contradictory claims even after all software checks pass. Host-controlled outcome text and exact original provenance do not prove that model reasoning is meaningful or scientifically correct.

## F. Genuine Phase5 integration

Used the actual unmodified `phase5-structured-1.0.0` public StructuredRetriever with `verification_mode=verified_session`, not a constructed response. Execution `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`; task `2448c758145ae5ad500f`; variant `xmlenv:574b783c023e533eb3a5c8e92557aa0a940aa5ff6cfbe794f5614e9fd321148e`. Original controller checkpoint read from recorded metadata: `moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10@638918f3d1c2e43a39a8a20772bdb8b91835e4b7`, distinct from the Qwen drafting model.

All five protected objects remain configured: cream_cheese_1, ketchup_1, orange_juice_1, milk_1 and butter_1. Full monitoring interval **[10,257]** retains the original configured start10 and terminal HDF5 snapshot257 (258 frames total); query windows11–12 do not shrink that scope. Recorded settling_steps10 and source identities are saved. The original illustrative analytical configuration is preserved, so the Drafter request retains `test_fixture=true`; this does not relabel the genuine retrieved measurements as synthetic or claim empirical checker authority.

| Actual request | Frozen status | Adapter behavior |
|---|---|---|
| Raw joint positions11–12 plus cream-cheese geometry identity |COMPLETE WITHIN VERIFIED CONTRACT,2 groups/2 items |Accepted as exact attributed context;0 registry records and0 eligible Solution IDs |
| Single-frame raw joint-position query |COMPLETE WITHIN VERIFIED CONTRACT,1/1 |Accepted; separately saved smaller valid context |
| Complete query plus action metadata10–12 |PARTIAL,3/4 |Accepted with missing settling-frame obligation explicit |
| Action metadata at settling frame10 |UNAVAILABLE,1/0 |Accepted as unresolved missing context within the monitoring interval |
| Historical producer attestation request |UNSUPPORTED,2/0 |Original refusal preserved; no physical conclusion |
| Wrong variant |INVALID SCOPE,2/0 |Rejected against legitimate target scope |
| Exact original object-filtered-contact request |UNSUPPORTED |Authentic refusal retained; its forged complete bundle rejected |

Exact requests, bundles, IDs, citations, obligations, assumptions, source selectors/values/hashes, fulfillment/missing statuses and adapter output context are under `B/artifacts/real-phase5/`. Original `evidence-citation:` IDs are not renamed. Any existing `ev:` identities remain attributed links; no registry records are fabricated from raw channels or geometry metadata. Complete context does not establish R1 sufficiency. The actual draft experiment uses the complete two-item bundle with no eligible registry Solution evidence.

No authentic UNVERIFIED PLAN was naturally produced by these queries. Its explicit preservation is covered by the clearly synthetic response-contract tests, not labelled real retrieval. The frozen independent validator was not patched to manufacture that status. Before/after frozen database signatures are equal. Final full database hashes and stat signatures match the originals (`B/artifacts/frozen-final-integrity.json`); neither frozen database was changed.

The consumer validates consistency and public request semantics, not arbitrary caller source authenticity. Actual source verification here was performed by the frozen producer. GSN Solutions still use existing registry IDs; direct Phase5 citations are context until an approved shared contract says otherwise. No multi-agent revision loop was implemented.

## G. GPU scheduling and recovery

At initial inspection GPU0 had ample free memory and GPU3 held this account's OpenVLA base custom-transfer LIBERO job; GPUs1/2 were occupied by other users and left untouched. GR00T's prior GPU0 run was already complete and was not restarted. Full Qwen requires both selected GPUs; freeing GPU3 alone would not imply a one-GPU deployment.

The existing OpenVLA supervisor/worker, command/cwd, selected non-secret environment, experiment/model configuration, logs and checksum-finalized episode checkpoint were inspected. Its official episode reset/seed and greedy policy allow completed-episode resume without cross-episode learning state. A first full proof checked401 episodes; after the authentication gap, a refreshed proof fully hashed892 completed episodes and verified frozen source files.

Immediately before interruption, the current supervisor was331860 and worker416296 on GPU3. The controller prevented new suite dispatch, waited for the current episode to finish, and checkpointed **896 completed episodes** with all previous completions retained. It terminated only that owned resumable process group to release VRAM; SIGSTOP was used briefly for the CPU controller, not as a GPU-memory release mechanism. The nascent next episode was preserved by rename to `.pr20-verification-interrupted-episode_046`; no completed output/checkpoint was deleted.

Persistent audit driver662588 and independent watchdog662589 own cleanup/recovery. Model serving options are removed before restarting the saved VLA environment. The recovery path runs even after deployment/evaluation errors and requires a new actual completed episode. Exact process/environment/checkpoint records and restart scripts are in `B/artifacts/gpu-recovery/` and `B/harness/`.

First restoration: supervisor672218/worker676667 resumed and completed episode897 (>896). Final guidance series used a new audited checkpoint906; supervisor672218/worker676667 were stopped after episode completion. The nascent episode006 was preserved as `.pr20-final-interrupted-episode_006`. The final persistent controller724418/watchdog724419 cleaned up all temporary servers and restarted OpenVLA with supervisor732699. Recovery verified episode907 (>906), genuine new progress, with the saved experiment configuration. Evidence: `B/artifacts/gpu-recovery/restored-verified.json` and `B/inference-final/artifacts/gpu-recovery/restored-verified.json`.

After restoration GPU0 used2608MiB, GPU3 used15939MiB and the OpenVLA supervisor was running. No listener remained on audit ports18030/18031. GPUs1/2 retained the other users' workloads (24798/23278MiB observed); none were interrupted. The final GPU snapshot and process state are saved separately.

## H. Final integration recommendation and delivery

1. Earlier software findings: fixed within the documented tested scope; original real failure remains preserved.
2. Standalone validation: now enforces the same supported structural/provenance requirements, in addition to unchanged shared Graph validation; not a semantic proof.
3. Alternative configurations: supported four/five-object supplied and Phase5 profiles pass; archived bindings remain strict.
4. Phase5: genuine public API statuses and exact context preserved; unsupported completeness forgery rejects. Requires current-main repaired Critic consumer.
5. Decoder: original single-character incompatibility fixed under exact recorded XGrammar/SGLang versions and actual Qwen inference.
6. Accepted actual Qwen GSN: **YES, three archived drafts**; **NO accepted real Phase5 draft**, despite completed inference and valid intermediate JSON/schema.
7. Uncertainty/provenance: retained in accepted outputs; model prose still requires review.
8. Controlled integration: repaired code is suitable for further controlled tests; complete end-to-end Phase5 acceptance is still an empirical follow-up.
9. Further work: retain explicit input-versus-output attribution in model reasoning review; improve/measure roster-order compliance without repairing outputs or weakening contracts. Broader scientific evaluation remains separate.
10. **DO NOT MERGE unchanged PR20.** Incorporate these verified repairs and main dependency, then review the remaining Phase5 inference limitation. This report gives a **CONDITIONAL PASS**, not unconditional merge approval.

Local branch `fix/drafter-pr20-independent-corrections` contains core repair commit `85dcbbfed07f87a8549845ab6c71589eee0fae8d`; final guidance and report commits are recorded in `delivery.json` and the final response. No push, force-push, GitHub review or PR merge was performed. Safe incorporation: after explicit push approval, publish this separate branch and open a replacement/follow-up PR, or have the PR owner merge current main and cherry-pick the focused repair/guidance/report commits. Do not overwrite the teammate branch.

### Reproduction

On Hestia, using fresh output filenames/directories:

```bash
B=/disk/1/data/niktakbr/drafter-pr20-verification-20261105
source "$B/harness/env.sh"
cd "$REPO"
"$AUDIT_PY" -m unittest discover -s drafter/tests -t . -v
/disk/1/data/niktakbr/critic-r2-audit-20261105/venv/bin/python \
  -m unittest discover -s drafter/tests -t . -v
```

`run-suite.py`, `probes.py`, `adversarial.py`, `original-large-graph.py`, `real-phase5.py` and `qwen-tokenizer-grammar.py` preserve exact audit procedures. Many refuse existing outputs; use a new audit output root. `run-real-drafter.py`, `model-env.sh`, `recording-proxy.py`, `gpu-recovery.py`, `restore-openvla.sh` and `recovery-watchdog.py` record actual serving/CLI/recovery commands. Reassess current ownership, checkpoint and ports before any repeat; do not blindly launch duplicate servers or reuse stale interruption state.

No model weights, virtual environments, credentials or large raw runtime records belong in Git. Raw results remain in B. Source and final report commits will be limited to Drafter files relative to current main.

### Final verification addendum

Final complete suite after all production/test changes: 201 tests in jsonschema4.25.1 and201 in4.19.1; exact final counts saved as `B/artifacts/tests-client425-delivery.json` and `tests-integrated419-delivery.json`. Independent adversarial suite47/47; actual-tokenizer grammar checks9/9. These sets overlap and are not additive independent model samples. Drafter documents no separate strict-mode switch; both supported dependency versions were tested. No tests run on the Mac or Indigo. All large raw records and weights remain outside Git.
