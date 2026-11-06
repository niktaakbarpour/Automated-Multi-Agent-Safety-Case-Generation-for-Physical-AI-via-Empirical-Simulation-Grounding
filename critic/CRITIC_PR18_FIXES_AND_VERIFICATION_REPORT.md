# Critic PR18 fixes and verification

## A. Summary and revision identity

Verification date: 2026-11-05 (America/Toronto; individual artifact timestamps are authoritative). All evaluation, synthetic probes, retrieval, and inference ran on Hestia. Indigo provided SSH transport only. No Alliance computation or Sea NFS was used.

Starting PR18 head: `5565a1e101eee5c11929166f248222569830b69b`; actual PR base: `a3c29a7b68edae3a58e415b5bccf60dc8ecad6e6`. Repairs started on a separate branch, `fix/critic-pr18-r3-audit-corrections`, from that head. Upstream subsequently merged PR18 independently: `main` became `f7de24a86a8b1565bb0ee204635d724bb90ada7d`. Its Critic tree matches the original PR head. This work did not merge PR18. Delivery must therefore be a **follow-up fix PR against main**, not a force-push to the teammate's branch.

Authoritative prior audit, read before repairs: `/disk/1/data/niktakbr/critic-r3-pr18-audit-20261105/AUDIT_REPORT_PR18_R3.md`, including preserved scripts and counterexamples. Those artifacts remain intact. New artifacts: `/disk/1/data/niktakbr/critic-r3-fixes-verification-20261105/` (abbreviated **B** below); final inference: `B/inference-final/` (**F**). Production checker, shared GSN contracts, frozen retrieval release/database, Drafter, and human judgments were not edited.

**CONDITIONAL PASS for bounded, human-reviewed integration.** All six reported software defects are corrected and their original failure modes independently retested. No confirmed blocking defect remains in the supported analytical-checker and verified-retrieval consumer scope. Real model recall and precision remain imperfect; autonomous review and scientific reliability are not established. Code commit: `25a7e25d9fc82184f2a6285d75189b8d7387075d` (rebased onto the externally merged main without changing tested Critic bytes). No changes were pushed. The final documentation commit is recorded in the delivery manifest and Git history.

## B. Fix-by-fix verification

| Finding | Root cause and correction | Before / after and independent evidence | Verdict |
|---|---|---|---|
| 1. Checker admission | Consumer checks of hashes, rows and ledger fields did not reproduce the authoritative checker's dependency and measurement semantics. `checker_replay.py` now requires the original inline `{configuration, artifacts, evidence}` input, verifies configuration equality and its checker `input_hash`, executes unmodified `evaluation.r1_v4.runtime.assess`, and compares the **entire** result. `assessments.py` rejects any mismatch as `CHK-REPLAY` before inference. Diagnostics include differing fields and authoritative rejection reasons. | Preserved dependency-cycle, missing-foundation and malformed-measurement assessments were admitted before. Afterward the altered results reject; correctly resealing an invalid source cannot turn its rejected records into verified evidence. Genuine positive and negative checker outputs remain admissible. Missing source or changed source hash rejects. Invalid assessments cannot support C07. Real checker calls on two contradictory synthetic selections admit both results and retain the positive violation and conflict. | PASS for the supported analytical route. |
| 2. C09 false negatives | The blanket unresolved-status exemption confused structured uncertainty with cautious prose. `llm.py` now anchors concerns in the targeted statement; full-statement quotation or positive overclaim cues retain proposals for human review. Ambiguous, unanchored objections against unresolved conclusions remain explicit as `C09_UNRESOLVED` in both deferred/rejected findings and unresolved concerns. Prompt v5 explains this distinction. | All four exact genuine C09 counterexamples now admit their scripted concerns, including the original unquoted execution-wide example. All three old Qwen Case C false positives are not promoted. Additional cautious prose, strategy/solution overclaims, geometric-contact-as-support, absence-of-violation-as-safety and ambiguous cases are covered. No unresolved status automatically suppresses an anchored criticism. | PASS for deterministic screening; semantic correctness still needs human review. |
| 3. Phase5 public semantics | The consumer's manually copied subset omitted public request restrictions. `phase5_request.py` executes database-independent predicates from frozen `StructuredRetriever.prepare`, the frozen schema/constants and the actual aggregate sample-budget guard; `retrieval.py` also binds explicit record/source/object selectors. Database-dependent authenticity is not simulated. Case E now requests supported global recorded contacts and keeps missing settling-action evidence explicit. | The exact object-filtered-contact request returns UNSUPPORTED from the actual frozen API. Its authentic refusal is preserved; a forged COMPLETE bundle now rejects `RET-QUERY` before inference. All five actual statuses, supported requests, public selector/assurance boundaries, aggregate budgets, and source/object tampering tested. | PASS within the documented consumer validation boundary. |
| 4. Non-finite model JSON | Python's permissive JSON decoder admitted NaN/Infinity and overflowing float tokens. Strict decoder hooks reject them before findings enter reports; canonical report checking and CLI `allow_nan=False` enforce finite output. | NaN, Infinity, -Infinity, 1e999 and nested malformed findings produce a failed model step with useful diagnostics and strict JSON reports. Original response text/hash remains available when it was returned as content; wire envelopes are separately preserved in inference artifacts. | PASS. |
| 5. Empty aliases | An empty returned identity could match an explicitly empty accepted alias. Alias configuration now requires nonempty trimmed strings and exact explicit matching, deduplicates aliases, and independently rejects empty returned identity. | Empty/whitespace/malformed aliases fail at configuration (CLI2); unexpected model identities fail the model step; valid explicit aliases still work. | PASS. |
| 6. Mutable settings traces | Nested options/settings and returned provenance shared mutable references. Constructor options, invocation settings, response metadata and returned reports are now deep snapshots. Core/authentication request overrides through `extra_body` reject; URL credentials, sensitive query values and fragment are excluded from trace settings. | Mutating caller settings, nested extra options, backend metadata or original request after a call does not rewrite the saved trace. Wire settings, request/prompt/content hashes and seeds independently checked. | PASS for tested sequential invocation. |

`critic/tests/test_pr18_corrections.py` contains 29 regression tests. Changes also touch CLI strict serialization, finite/cyclic Python-input checks, request schema, fixture generation, synthetic D/E source envelopes, README, requirements and comparison documentation. Existing R1/GSN/frozen Phase5 contracts remain unchanged. The new optional schema property for `input_bundle` does not grant admission: result-only legacy pairs are deliberately rejected at semantic admission. Producers must retain the original hash-bound source input; the Critic cannot reconstruct it from an output assessment.

The authoritative replay is validation of analytical consistency, **not authentication of a producer**. Synthetic inputs remain fixture-only and empirical checker admission remains disabled. Merely recomputing hashes never proves observations occurred.

## C. Tests and independent re-audit

| Verification | Actual result | Saved evidence |
|---|---|---|
| Complete default suite | 189 discovered/run/pass; 0 failures/errors/skips; no duplicate IDs | `B/artifacts/tests-default-complete.json` and log |
| Complete strict suite | 189 discovered/run/pass; 0 failures/errors/skips | `B/artifacts/tests-strict-complete.json` and log |
| New regression module alone | 29/29, no skips | `B/artifacts/tests-regressions-complete.log` |
| Independent adversarial set | 59/59 | `B/release-proof/artifacts/adversarial-summary.json` |
| Instrumented fake HTTP boundary | 26/26, including invalid API/CLI inputs producing zero model requests | `B/verified-final/artifacts/http-probes-summary.json` |
| Exact historical saved inputs | 139 file inputs replayed, no internal errors; expected rejection/migration separated | `B/artifacts/exact-replay-summary.json` |
| Guard-removal mutation checks | 8/8 deliberate mutants detected; unmodified control passes | `B/artifacts/mutation-summary.json` |
| Genuine checker conflicts | Six admitted per-object rows from two actual checker results; violation and conflict retained | `B/artifacts/genuine-conflicts-verified/` |

These sets overlap; their counts must not be added as independent scientific trials. Earlier development failures and partial runs remain saved, not presented as final passes. Four oversized-integer generator probes have no saved JSON file and are covered by the adversarial harness, explaining why file replay count is 139 rather than its generator's larger probe count.

The conflict-isolation unit class deliberately edits rows and therefore stubs only replay; comments identify this boundary. The separate new regression and `genuine-conflicts-verified.py` produce legitimate conflicting outputs through the actual checker without that stub. Mutation tests disable each guard only inside isolated test subprocesses, never in production source. A deliberately old cyclic-input scanner hangs and is detected by timeout.

Earlier protections remain exercised: full configuration binding, applicability/conflicts, pre-LLM schema and shared graph validation, huge integers, malformed responses, temporal/object/node evidence grounding, Phase5 crosswalk, model identity, finish reason and C07 assessment admission. `CRITIC_STRICT_TESTS=1` continues making unavailable reference oracles fail rather than skip. Runtime now requires Python 3.10+ and the pinned jsonschema dependency; verification used Python 3.12.14 / jsonschema 4.19.1 on Hestia. No other Python version is claimed empirically verified.

## D. Real frozen Phase5 verification

Used unmodified `phase5-structured-1.0.0` and the real database with `StructuredRetriever(verification_mode='verified_session')`. Execution: `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`. Protected objects: cream_cheese_1, ketchup_1, orange_juice_1, milk_1, butter_1. Monitored saved-frame interval: **[10,257]**, from recorded first-policy boundary to terminal snapshot; boundary provenance saved. A manually authored unresolved GSN scaffold was used for integration testing, not claimed to be a Drafter output.

| Actual retrieval status | Groups/items | Critic behavior |
|---|---:|---|
| complete | 2/2 | completed, CLI0; physical outcome remains insufficient_information |
| partial | 3/4 | completed, CLI0; unfulfilled obligations retained |
| unsupported | 2/0 | completed, CLI0; original refusal retained |
| unavailable | 1/0 | completed, CLI0; absence remains explicit |
| invalid-scope | 2/0 | rejected_invalid_input, CLI3, RET-SCOPE |

Original request/bundle identities, statuses, obligations, selectors, provenance, limitations and citation IDs remain intact. Frozen database SHA256: `f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8`; catalogue SHA256: `ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e`. Final hashes, inode/size/mtime/ctime match the preserved baselines (`B/artifacts/frozen-database-final-integrity.json`). The exact formerly unsupported request and its forged completion are saved under `B/release-proof/artifacts/phase5-refusal.*` and associated subdirectories. Real geometry/execution/contact/camera crosswalk tests produce **31 linked solutions**; wrong-object, wrong-family and out-of-window mappings reject. These are links to genuine registry IDs, not renamed or invented `ev:` IDs. `evidence-citation:` remains separate from GSN solution references.

The consumer does not reopen the frozen database for every review and does not authenticate arbitrary supplied values. It reuses public rules independent of database rows and validates returned scope/source/citation/crosswalk consistency. Database-dependent catalogue/channel existence and original value verification remain the verified producer's responsibility. Supplied hashes alone are not authenticity. Full provenance authentication or direct GSN citation migration requires a separate shared integration decision. No complete retrieval result becomes a no-violation assessment or evidence of physical safety.

## E. C09 evaluation

The four preserved genuine cases target G1, U1, D1 and the execution conclusion. Scripted original responses now retain all four criticisms. The three criticisms from the prior actual Qwen Case C response, replayed separately **as scripted tests**, are deferred/not promoted; they are not counted as new inference. Ambiguous cases remain human-review concerns, not automatically cleared claims. Strategy and solution statements do not inherit an unrelated cautious conclusion as an exemption.

Actual v5 inference retained a targeted C09 in all **12/12 Qwen genuine-case attempts**. GPT retained targeted C09 in 7/12 attempts, and recognized the execution-wide reasoning flaw as C05 in two further attempts: **9/12 reasoning detections**. On D1 it returned no relevant finding in one normal attempt and hit the token limit in two others. These are generation misses/failures, not deterministic filter suppressions.

Both models offered **zero C09s on the three unchanged Case C attempts**. Qwen offered no objections there. GPT nevertheless offered six C06 objections across two attempts, incorrectly treating unresolved formal goal statements as established safety conclusions. All six were accepted only as nonblocking, human-review-required proposals. This is a real semantic false-positive limitation and worse than the earlier Case C reference runs; it must not be concealed by reporting C09 alone. In the mutated G1 cases, Qwen also offered four C09s against the unchanged cautious other-object graphs; these were deferred rather than promoted, while the genuine target concern survived. The screening rule therefore does not achieve perfect semantic precision.

The screening tests prove software behavior, not that a model naturally discovers every flaw. Categories and target IDs are measured separately from substantive reasoning; a C05 objection may recognize a problem without being a C09 finding. Reference-relative assessments here use synthetic fixture intent and assistant inspection of actual texts, **not a new independent human-adjudicated reference set**. No existing human judgments were altered.

## F. Real model evaluation

Final verification uses 24 fresh requests per model: Cases A/C/D/E, three attempts each, plus four preserved genuine C09 interventions, three attempts each. Seeds 43001–43024 are recorded per model; requests go to actual local vLLM, not cached/saved responses. Identical greedy output across seeds remains possible, especially GPT temperature0.

- GPT-OSS: `openai/gpt-oss-20b`, checkpoint `6cee5e81ee83917806bbde320786a8fb61efebee`; GPU0, tensor parallel1, context32768, max8192, medium reasoning, temperature0.
- Qwen: full `Qwen/Qwen3-32B`, checkpoint `9216db5781bf21249d130ec9da846c4624c16137`; GPUs0,3, BF16, tensor parallel2, context32768, max8192, temperature0.6/top_p0.95/top_k20, default thinking enabled, qwen3 reasoning parser.
- Hestia: four NVIDIA L40S, 46068 MiB each; driver595.99.02; serving environment Python3.12.14, vLLM0.31.0, PyTorch2.13.0/CUDA13.0 (captured distribution versions). FlashInfer sampler disabled because nvcc is unavailable; no model substitution.

Server binds 127.0.0.1:18020; a local transparent recording proxy at127.0.0.1:18021 records actual prompts/request bodies and server response envelopes without authorization headers. Commands/config/discovery/logs are under `F/artifacts/models/`; per-call reports and inputs under model subdirectories; wire artifacts under `http-NNN/`. No public endpoint. Failures/truncated outputs are retained.

| Model | Fresh HTTP calls | Normal / parseable / usable | Failed model step | Accepted proposals | Rejected/deferred proposals | Case C accepted false positives |
|---|---:|---:|---:|---:|---:|---:|
| GPT-OSS-20B | 24/24 HTTP200 | 22/24 | 2 length | 81 | 1 | 6 C06 |
| Qwen3-32B | 24/24 HTTP200 | 24/24 | 0 | 41 | 6 | 0 |

Counts in the proposal columns exclude deterministic findings. The two length responses have empty content after reasoning exhausts8192 tokens; full server envelopes remain saved. All46 normal replies are strict JSON as returned, not merely recoverable objects inside extra prose. All48 reports satisfy the report schema and strict finite serialization, including failed-model reports. Independent checks find zero model-identity/usage/seed mismatches, zero unknown/ambiguous-node or out-of-scope evidence citations among admitted proposals, zero C07 admissions without a valid assessment, and zero prompt/message/request/content-hash or effective wire-setting mismatches. This does not prove that a citation logically supports its associated criticism.

| Case / intervention | GPT usable | GPT accepted / rejected | Qwen usable | Qwen accepted / rejected |
|---|---:|---:|---:|---:|
| A | 3/3 | 51 / 0 | 3/3 | 12 / 0 |
| C | 3/3 | 6 / 0 | 3/3 | 0 / 0 |
| D | 3/3 | 1 / 0 | 3/3 | 4 / 0 |
| corrected E | 3/3 | 4 / 1 | 3/3 | 7 / 0 |
| genuine G1 | 3/3 | 8 / 0 | 3/3 | 3 / 4 |
| genuine U1 | 3/3 | 6 / 0 | 3/3 | 7 / 0 |
| genuine D1 | 1/3 | 0 / 0 | 3/3 | 3 / 2 |
| genuine execution | 3/3 | 5 / 0 | 3/3 | 5 / 0 |

The GPT rejection in E and two Qwen rejections in D1 lack the required assessment citation for C07. Four Qwen G1 proposals are unanchored C09s against unchanged cautious objects and remain explicit unresolved concerns. No blanket filter suppresses the genuine overclaims. The corrected E source/request and promptv5 differ from v4, so this is not a controlled causal estimate of prompt improvement. Earlier v4 standard series: Qwen12/12 normal, GPT10/12; current standard series: both12/12 normal. Prior v3 Qwen had three unsupported Case C C09s; v4 and current v5 both have zero there. Current GPT's C06 false positives mean overall semantic quality has not uniformly improved.

Per-call seeds, inputs, parse status, accepted/rejected findings, target detection, timing, token usage and paths: `F/artifacts/models/independent-summary.json`, `independent-report-contract-check.json`, `independent-trace-hashes.json`, each model's `comparison.json` / `c09-extra-comparison.json`, and `reference-relative-review.json`. The latter records per-call reference scope and what remains unadjudicated. GPT also repeated two C06 objections against unchanged other-object goals in one G1 intervention. Additional Qwen applicability and goal-target objections require review; the six Case C false positives are not an exhaustive all-case error count. Numeric reference-relative detection is limited to the deliberately introduced flaws; no comprehensive precision/recall score is justified. A separate aborted development series exists under `B/artifacts/models/`; it is excluded from this final frozen-source comparison. Final source manifest is `F/artifacts/runtime-source-manifest.json`.

Passing JSON/schema/identity/scope checks is software acceptance, not human-validated scientific correctness. Accepted LLM proposals are nonblocking and require human review. In particular, no absence of criticisms proves safety or scientific reliability.

## G. GPU recovery

Initial audit snapshot: GPU0 used2044MiB and GPU3 used15989MiB (OpenVLA); GPUs1/2 used25022/23222MiB. GR00T on GPU0 had completed2500/2500 episodes before this work; it was not restarted. OpenVLA on GPU3 was active and owned by this account. GPUs1/2 were occupied by other users and were left untouched. GPT ran on available GPU0 without interrupting OpenVLA. Qwen's full BF16 weights required GPUs0+3.

Before stopping OpenVLA, its launch/configuration/environment/cwd, process/session identities and logs were saved, and the official per-episode reset/seed behavior, completion metadata and skip-completed adapter were inspected. Initial324 completed episode manifests/artifacts were fully verified. Interruption waited for a completed episode boundary at **354 completions**. The CPU-only controller was briefly stopped to prevent new suite dispatch; this was not used to release VRAM. The owned resumable worker/session was then terminated, freeing GPU3. One next-episode partial directory was renamed to `.pr18-fixes-interrupted-episode_004`, preserving its content. Existing results/checkpoints were not deleted or changed.

The Qwen driver has a finally/recovery path and an independent watchdog with an idempotent restoration lock. Recovery relaunches the saved workload configuration through the resume adapter, checks the same experiment/model configuration identity and waits for a new successfully completed episode. Exact before/restart/final process details and logs are in `F/artifacts/gpu-recovery/`.

**Restored and verified:** supervisor PID331860, worker PID335985, GPU3. `restored-verified.json` records a genuine new completion **355 > 354**. Independent inspection verifies the same experiment `openvla-base-transfer-0023d0d945b7ea75` and model configuration `12c6fc0cfd3263e70043`, unchanged identities/manifests for the324 fully prehashed episodes, live worker, and no listeners on18020/18021. Initial final snapshot: GPU0 ~2044MiB used /43417MiB free; GPU3 ~15989MiB used /29471MiB free, occupied by restored OpenVLA. These are timestamped observations, not a guarantee of future allocation. The driver and watchdog exited after recovery. No original job remains paused. Final preservation check repeats manifest/identity checks, not all large trajectory hashes; the full content hash verification was performed before interruption.

## H. Limitations and remaining work

- **Blocking correctness defects from this audit:** none reproduced after the repairs within the supported scope. This is not proof against every possible adversarial input.
- **Nonblocking engineering:** migration to original source envelopes, dependency installation, consumers displaying C09 unresolved concerns; frozen-source adapter is intentionally tied to this release and must be revalidated if upstream API changes. Runtime validation may fail closed if those dependencies/source predicates are unavailable.
- **Scientific evaluation:** synthetic checker/model cases do not authenticate real physics; empirical checker admission remains disabled. LLM recall and semantic precision are imperfect; no general reliability claim from a few seeded cases. Token-budget failures are explicit failed model steps. Human review remains mandatory.
- **Shared integration:** authenticated producer/source transfer, database-dependent provenance assurance, broader benchmark/configuration coverage and any GSN direct citation migration remain separate work. Do not turn model proposals, task success or retrieval completeness into safety findings.

## I. Reproduction and final recommendation

Run on Hestia only, from the isolated repaired checkout; do not blindly start duplicate inference servers or interrupt another job. Exact original commands and environment are in the saved harnesses.

```bash
B=/disk/1/data/niktakbr/critic-r3-fixes-verification-20261105
source "$B/harness/env.sh"
cd "$REPO"
"$AUDIT_PY" -m unittest discover -s critic/tests -t . -v
CRITIC_STRICT_TESTS=1 "$AUDIT_PY" -m unittest discover -s critic/tests -t . -v
"$AUDIT_PY" -m unittest critic.tests.test_pr18_corrections -v
```

Independent reproduction scripts: `B/harness/adversarial.py`, `http-probes.py`, `exact-replay.py`, `mutations.py`, `genuine-conflicts-verified.py`. Use a **new** AUDIT output directory for scripts opening unique artifacts; preserve REPO at the repaired checkout. `release-offline.sh` records calls to the frozen real retrieval/crosswalk/refusal probes. For inference, `F/harness/run-gptoss.py`, `qwen-and-recover.py`, `compare-real.py`, `recording-proxy.py` and recovery helpers record the commands and sequencing actually used. GPU recovery is workload-specific: inspect current jobs/checkpoints before reuse. `summarize-models.py` and `verify-real-reports.py` independently summarize saved final reports.

1. **All three blocking findings fixed? Yes**, for their documented analytical/consumer scope: actual-checker replay, uncertainty-preserving C09 screening and authoritative public retrieval request semantics have direct counterexample evidence.
2. **All three additional defects fixed? Yes:** finite model JSON, strict aliases and immutable saved trace snapshots pass direct API/CLI/HTTP/mutation tests.
3. **Earlier fixes preserved? Yes within the exercised suite and historical probes**, including real crosswalk and pre-call validation checks.
4. **Checker admission enforced? Yes for the supported analytical route.** Source-bound full replay is mandatory; empirical admission remains disabled and source authenticity is not inferred from hashes.
5. **C09 balanced? The blanket false-negative bug is fixed.** Genuine targeted criticisms survive, old unsupported objections are not promoted, and ambiguous concerns remain visible. Automatic semantic precision is not proved.
6. **Phase5 authoritative semantics followed? Yes for the tested request/status/selector/obligation paths**, including the exact prior mismatch against the actual frozen API. Database-dependent producer authenticity remains outside consumer validation.
7. **Actual inference works? Yes:** both original models ran locally on Hestia;46/48 usable completions, two safely rejected length responses, all artifacts retained.
8. **Ready for integration? Yes for a bounded integration with explicit source-envelope migration, verified producer bundles, surfaced unresolved concerns and human review.** Not ready for unattended scientific safety assessment. Broader reference-based evaluation and authenticated provenance transfer remain required before scientific claims.
9. **Safe to merge? Recommend MERGE of a follow-up repair PR after review**, with the limitations above documented. PR18 itself has already been merged externally. Do not interpret this recommendation as scientific approval or an instruction to merge automatically.

Prioritized remaining work: shared integration must carry original checker inputs and expose unresolved/model-proposed concerns; Critic evaluation must measure and address semantic false positives and generation misses before scientific comparison; RAG/shared integration must define producer authentication if untrusted bundles are in scope. These are not silently treated as completed features.

The local repair branch is `fix/critic-pr18-r3-audit-corrections`; code commit `25a7e25d9fc82184f2a6285d75189b8d7387075d`. The report-only commit follows it; its exact identity is in `B/DELIVERY.json` and the delivered Git log. After explicit approval, the safe publication steps are:

```bash
git push -u origin fix/critic-pr18-r3-audit-corrections
gh pr create --base main --head fix/critic-pr18-r3-audit-corrections \
  --title "Critic: enforce audited admission and preserve grounded concerns"
```

Inspect the focused diff against current main and the report first. No force-push, teammate-branch overwrite or automatic merge is needed. Reproducibility index: `B/ARTIFACT_SHA256SUMS.json` records hashes of saved audit outputs; large weights/caches/Git internals and the live original-workload log are excluded. Runtime source manifest, exact commands, actual wire envelopes and frozen-source integrity records remain separately traceable. No changes have been pushed. Do not force-push or reopen/overwrite the merged teammate branch. After approval, publish the dedicated branch and open a follow-up PR to main.

### Source index (repair tree)

- Checker source/hash/replay: `critic/checker_replay.py:12`, invoked at `critic/assessments.py:243`; source envelope documentation in `critic/schemas/critic_request.schema.json:133`.
- C09 statement grounding: `critic/llm.py:404`, positive retention cues at431; unresolved concern propagation at `critic/critic.py:93`; prompt `critic/prompts/critic_system_v5.md`.
- Frozen public request predicates: `critic/phase5_request.py:19`; returned-window budget at84; integration at `critic/retrieval.py:150`; returned source/object binding at309.
- Strict numeric decode: `critic/llm.py:287`, report canonicalization `critic/critic.py:102`, CLI serialization `critic/__main__.py:76`.
- Alias validation: `critic/llm.py:150`, returned identity check at196.
- Snapshot capture: `critic/llm.py:185` and477; returned report copy `critic/critic.py:32`; cyclic input scanner `critic/checks.py:154`.
- Regressions: `critic/tests/test_pr18_corrections.py`; existing test adjustments `critic/tests/test_critic.py` identify isolated logical-row tests versus full producer replay.
