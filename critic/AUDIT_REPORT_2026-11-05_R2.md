# Independent Critic R2 audit — 2026-11-05

## Executive verdict: FAIL

The merged implementation is substantially improved, but not all November 4 findings are resolved. Both existing test modes really pass 134 tests, with no skips. Independent probes nevertheless demonstrate incomplete checker-output admission, a shared-graph-validation discrepancy that permits a model call, an uncaught input exception, insufficient temporal/graph grounding of model findings, and an unvalidated Phase 5-to-GSN crosswalk. The HTTP client also ignores response model identity and termination reason.

Real frozen Phase 5 retrieval was exercised successfully, including all five structured statuses. Successful retrieval remained informational and did not establish R1 satisfaction. Actual model results and limitations are recorded below and in the appended execution supplement. Passing a software validator or obtaining model criticisms does not establish a scientifically trustworthy argument or physical safety.

This was an audit, not a repair. No production implementation, contract, checker, evidence record, frozen database, or workflow was changed. No commit, push, or merge was performed. The report is a new uncommitted file. Temporary harnesses and artifacts are outside the project sources.

## Audited source and method

Audited `origin/main` is `0ffe1511bd328ab6be0f7cf49524b17f24c007e9`, the merge of PR #16, `feature/critic-agent-r2`. Its first parent is `e7839d64f8ad902e194304e982573b05794f3471`. The original report audited `7085fb7b341b847ba903a4f93da6407244d19b34`. The November 4 report was read in full before constructing these probes. Source line references below refer to the audited merge, not the old report's line numbering.

The R2 branch introduced: `c0da2b4` checker admission; `6d036bd` conflicts/applicability/gaps; `2c0f1a7` validation/status/exit codes; `d6aa415` configuration binding; `93b8467` model parsing/grounding/traces; `33a9ab4` Phase 5 integration; and `6c5aa85` tests/strict oracles. Exact merge metadata, patch, and diffstat are archived as `artifacts/merge.txt`, `r2.patch`, and `r2-diffstat.txt`.

All tests, retrieval, oracle comparisons, and inference ran on Hestia. Indigo was only an authenticated SSH relay. No Alliance machine or Sea NFS was used. Static inspection and report authoring also used a Mac source snapshot. Hestia's isolated source checkout is at:

```
/disk/1/data/niktakbr/critic-r2-audit-20261105/repo
```

The experiment root, abbreviated **AUDIT** below, is its parent. `harness/` contains external audit scripts; `artifacts/` contains inputs, outputs, stdout/stderr, reports, and diagnostics. Synthetic inputs and scripted/fake-server replies are explicitly identified as such. Actual Phase 5 bundles and actual model HTTP traffic occupy separate directories. Neither a synthetic checker assessment nor an actual model response is presented as empirical physical evidence.

## Original finding verification matrix

PASS in this table concerns the stated original issue and tested variations; it is not an implementation-wide endorsement.

| Original issue | R2 correction and current source | Independent procedure and expected behavior | Observed behavior | Verdict |
|---|---|---|---|---|
| I1: fabricated `validated_checker` authority | Explicit `{configuration,result}`, hashes, producer/version, identities, synthetic-only admission. `critic/assessments.py:119`, `:233`, `:288` | Replayed old forged assessment; changed requirement, execution, object, evidence, producer, hashes; then supplied rehashed results violating the checker's own schema and admission semantics. Invalid evidence must not be admitted. | Old authority flag and common identity attacks reject with no model call. However invalid manifests/outcomes/schema versions and missing `rejected_evidence` still admit three synthetic assessments; contradictory evidence-admission rows and distant evidence intervals also survive. | **FAIL — partially fixed** |
| I2: conflicting assessments/applicability allow negative endorsement | Admissibility checks, explicit conflicts, positive precedence. `assessments.py:257`; `checks.py:832` | Positive versus negative, applicable versus non-applicable, unresolved outcomes, alternate objects/scopes; expected positive retained and disagreements explicit. | Tested valid-fixture conflicts are flagged; negative results do not erase the admitted violation. Invalid applicability is rejected; unresolved assessments remain uncertainty. This assumes admission is valid; I1 remains separate. | **PASS within tested admitted-fixture semantics** |
| I3: schemas not enforced | Request/record/config/graph schema checks before review. `checks.py:100`, `:156`, `:301`, `:1036`; `schema.py:82` | Missing fields, wrong types, malformed records, full original checker-schema oracle, and nonfinite graph metadata. | Ordinary invalid requests reject. Checker own-schema violations remain accepted; opaque graph provenance containing NaN bypasses canonical shared-validator requirements. | **FAIL — partially fixed** |
| I4: invalid graphs still invoke LLM | `input_valid` gate in `critic.py:30`; graph checks at `checks.py:496` | Instrumented backend and HTTP counter, dangling nodes, invalid edges/scopes/evidence, plus graph rejected by the actual shared validator. Expected zero calls for invalid input. | Six independent HTTP-gate attacks return invalid input, CLI 3, zero calls. NaN provenance is rejected by actual `Graph.validate` but accepted by Critic, which calls the spy once. | **FAIL — validation discrepancy remains** |
| I5: malformed model category crashes | Finding schema and defensive parsing/screening. `llm.py:219`, `:236`, `:309` | Original list-valued category, invalid/empty JSON, missing fields, wrong types, unknown categories/nodes/citations, nested and truncated text. | Original crash is fixed. Tested malformed findings are rejected with reasons; unusable replies produce `completed_llm_failed`. Embedded-object extraction is deliberately permissive, not a new schema guarantee. HTTP truncation metadata remains a separate defect. | **PASS for original malformed-finding crash** |
| I6: configuration and boundaries unbound | Full config hash, scope and interval/boundary checks. `checks.py:301`, `:332`, `:373`, `:454` | Original reduced/empty scope probes plus real-wrapper five-object shortening, replacement, duplicates, reordering, config mutation, shifted start. | Altered sets/config/boundaries reject, zero calls, CLI 3. Reordering the same set is accepted. Full real scaffold keeps all five objects over saved frames 10–257. Binding is to caller-supplied configuration, not independent authentication of an approved configuration. | **PASS for binding; trust boundary limitation remains** |
| I7: absent/lossy structured retrieval integration | Frozen-contract-aware admission, retained citations/obligations/status. `retrieval.py:63`, `:113`, `:255`, `:386`, `:407` | Synthetic five-status probes, actual frozen requests/bundles, mismatched scope, complete retrieval plus unsupported negative, forged original-ID crosswalk. | Real statuses/identities retained; invalid scope rejected; completeness does not prove safety. But changing a source item's original IDs can falsely link it to another object's GSN solution. | **FAIL for complete integration assurance; real read-only pathway works** |
| I8: known IDs mistaken for supported criticism | Same-object/execution checks, rule-only categories, admitted C07 requirement. `llm.py:236`, `:271` | Known but temporally irrelevant evidence; object-null repeated-node ambiguity; C07 admitted/wrong-object/invented assessment controls. | C07 controls work for valid admission. Out-of-period evidence and ambiguous cross-object node citations still become accepted model proposals. Accepted proposals are nonblocking and require human review. | **FAIL — partly grounded, not sufficiently scope-bound** |
| I9: automation lacks explicit statuses | Four review statuses and CLI exit mapping. `critic.py:15`, `:71`; `__main__.py:22` | API/CLI invalid inputs, malformed replies, huge valid-JSON integer. Expected diagnostics and documented statuses/codes. | Ordinary invalid inputs return 3 and model failures return 4. A 1001-digit interval endpoint raises uncaught `OverflowError`, yielding CLI 1 with no review report. | **FAIL for documented never-raise/automation contract** |
| I10: incomplete reproducibility and acceptance evidence | Prompt/input/request/response hashes/settings, strict oracle checks, comparison runner. `llm.py:154`, `:309`; `tests/oracles.py:60`; `compare_models.py:25` | Reproduced both suites; removed site packages in child interpreter; inspected actual response envelopes and comparison traces. | Traces and strict missing-oracle behavior work. Actual comparison was attempted and results archived; HTTP response model/finish metadata are neither checked nor retained by the Critic itself. See execution supplement for actual results. | **PARTIAL / FAIL for complete execution assurance** |
| I11: irrelevant gaps cause coverage criticism | Obligation/interval-aware gap filtering. `checks.py:995` | Out-of-window, optional, and mandatory in-window gaps using the actual fixture interval. | Outside/optional gaps do not produce `CONCL-GAP`; mandatory in-window gap does. Initial audit harness used the wrong interval and was corrected, with both versions retained. | **PASS** |

The original probe scripts were preserved verbatim under `harness/original-20261104/`. `reproduce-legacy.py` ran literal old inputs and the same mutation logic adapted to current fixtures. Literal old-schema requests are correctly rejected; this alone was not counted as root-cause verification. Semantic-equivalent probes supplied the current schema/configuration and confirmed the behaviors above. Results are in `legacy-literal.*`, `legacy-current.*`, and `legacy-more-current.*`.

## Confirmed remaining defects and minimal reproductions

### R2-01 — checker own output contract is incompletely enforced (blocking)

Start from valid current Case D's full synthetic checker result. Delete `result.rejected_evidence`, or assign `result.assessment_manifest=[]`, `result.execution_outcome="safe"`, `result.evidence_schema_version="999"`, or `result.manifest_version="999"`. Recompute the synthetic content hashes using the published serialization; retain the exact reviewed configuration. These are deliberately forged audit inputs, not observed checker outputs.

The independent original-schema oracle rejects these results. Critic instead returns `completed`, admits three object assessments, and produces `CONCL-HIDES-VIOLATION` from them. A spy model is called. Representative CLI runs exit 1 for completed blocking review, rather than 3 for rejected input. Artifacts: `independent/checker-missing-rejected_evidence/`, `checker-invalid-assessment_manifest-list/`, related version/outcome directories, and `checker-own-contract-oracle.json`.

Root cause: `assessments.py:59` and `:119` implement a subset of the result contract; the full `evaluation/r1_v4/assessment.schema.json` is not enforced. The test comparing copied vocabulary with the original schema does not establish complete instance validation.

### R2-02 — evidence admission and temporal dependencies can contradict the admitted assessment (blocking)

Against the same synthetic fixture, clear `evidence_admission`, or mark a cited dependency rejected while leaving it in `admitted_evidence_ids`; alternatively move cited checker evidence intervals to `[10000,10001]`, or set an object assessment's `scope_mismatch=true`, then rehash. These variations remain admitted. The original output schema is not sufficient to detect every semantic inconsistency, so this is distinct from R2-01.

`assessments.py:269` checks cited IDs and execution/object membership, but not consistency with admission decisions or temporal dependencies. At `:318–331` admitted assessment intervals are assigned from the reviewed context, rather than established from the cited evidence. Artifacts: `checker-admission-list-empty`, `checker-admission-contradicts-ids`, `checker-far-evidence-interval`, and `checker-object-scope_mismatch` under `artifacts/independent/`.

Mitigation and precise scope: these counterexamples affect the **synthetic analytical fixture route**. Empirical admission remains disabled; the old fabricated empirical `validated_checker` probe and synthetic evidence supplied as a real run are rejected. No experiment showed forged evidence becoming authenticated empirical evidence. Recomputed hashes establish content consistency, not producer authenticity or physical truth. The Critic does not independently replay the checker or authenticate a producer/source merely because a digest matches.

### R2-03 — nonfinite graph provenance bypasses shared validation and reaches the model (blocking)

Add `float('nan')` inside a graph node's opaque `provenance` on an otherwise valid current unresolved request. Python's standard JSON loader accepts the serialized NaN token. The actual shared `Graph.validate(registry)` rejects canonical nonfinite JSON, whereas Critic accepts the graph and invokes the spy model once; CLI returns 0. The exported request hash can become null rather than causing rejection.

Evidence: `artifacts/independent/graph-nan-provenance/` and `nonfinite-graph-oracle.json`. Source: `checks.py:496` mirrors graph checks but omits the final canonical serialization enforced by `evaluation/r1_v4/evidence_registry_gsn/gsn.py:76`. The NaN token is not standards-compliant JSON; this matters because both the public Python API and the actual CLI currently accept it and fail to enforce the shared graph contract before inference.

### R2-04 — large integer input crashes instead of returning an invalid-input report (blocking)

Set the monitored interval endpoint to `10**1000`. This is an integer representable in JSON and accepted by Python's parser. `math.isfinite` converts it to float and raises `OverflowError: int too large to convert to float`. `review()` raises, CLI exits 1 with a traceback, and no documented review report is returned. The spy counter stays zero.

Evidence: `artifacts/independent/huge-json-integer/`. Source: `schema.py:82–96`, analogous numeric checks at `checks.py:62`, and unguarded validation call at `critic.py:30`. This contradicts `review()`'s documented “Never raises on bad input” contract. This is an input-validation failure, not malformed model output.

### R2-05 — citation screening misses time and unique graph scope (blocking before automatic integration)

Append a properly hashed, otherwise admissible registry record for the same object/execution but interval `[10000,10001]`. A C05 model finding citing it against current `G1` is accepted. Separately set `object_id=null`, use `node_id="G1"` shared by several graphs, and cite another object's record: accepted again. `llm.py:271–297` checks existence and selected identity fields but not interval/clock compatibility or a uniquely scoped graph target.

Evidence: `independent/model-known-outside-time-citation/` and `model-ambiguous-node-cross-object/`. These are scripted adversarial proposals. They remain `llm_proposed`, nonblocking, and human-review-required; they do not become physical conclusions. Nevertheless admission of the criticism overstates its grounding. C07 now requires a same-object admitted assessment, which is a real improvement, but that guarantee inherits R2-01/R2-02's admission weaknesses.

### R2-06 — Phase 5 original-ID crosswalk can falsely associate another object's solution (blocking)

Using the synthetic structured fixture, change a `source-ref:` geometry item's `original_evidence_ids` to the existing `ev:` ID of object_02's pose solution E1. Preserve its unchanged citation basis and citation ID. The bundle is accepted and the report emits `linked_solutions=[{object_id:"object_02",node_id:"E1",...}]` for that unrelated citation. No matching source/selector/object/measurement proof is required by `retrieval.link` at `retrieval.py:90–108`.

Definitive reproduction: `harness/crosswalk.py`, `artifacts/crosswalk/{input.json,report.json,observation.json}`. The earlier `phase5-unvalidated-original-id-link` probe selected a registry record absent from the solutions and produced no link; it showed accepted altered metadata, not the false-link effect. The follow-up deliberately selected an actual solution and demonstrated that effect. No observed safety conclusion resulted, but the traceability association is false and can influence downstream coverage/criticism. This was a synthetic tampering test, not an allegation that the frozen retriever generated the forged mapping. `critic/README.md:126` explicitly discloses that recorded-metadata original IDs are not authenticated and links follow what the bundle says. This is therefore a **documented trust-boundary limitation demonstrated adversarially**, rather than an undisclosed promise of database authentication; it still prevents treating this pathway as a validated evidence bridge.

### R2-07 — HTTP completion identity and termination are ignored (required before scientific evaluation)

An instrumented fake HTTP server returning valid `{"findings":[]}` with `finish_reason="length"` produces `completed` and `llm.ok=true`. So does a response whose `model` is `ANOTHER-MODEL` rather than the requested identifier. `llm.py:161–174` extracts only message content. Evidence: `artifacts/refined/synthetic-http-*` and `refined-summary.json`.

These protocol tests are synthetic. A parseable inner object is not proof of a complete response, and the reported requested model is not proof of the returned model. A supported alias policy may be necessary, rather than naive exact-string rejection. Production traces should preserve actual response identity, finish reason, usage, and failures. The real inference proxy independently archives those fields for this audit. Permissive embedded-JSON extraction itself is documented behavior; an initial assertion expecting all nested wrappers to reject is not counted as a separate confirmed bug.

## Test results and isolation

| Execution on Hestia | Discovered/run | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|---:|
| Existing complete suite, default | 134/134 | 134 | 0 | 0 | 0 |
| Existing complete suite, `CRITIC_STRICT_TESTS=1` | 134/134 | 134 | 0 | 0 | 0 |

Python was 3.12.14, with the project's pinned `jsonschema==4.19.1`. Durations were 11.802 s and 11.230 s. Both test-ID inventories have zero duplicate IDs. Separate processes ran each mode in an isolated checkout, with bytecode writes disabled. Shared-validator mutation checks and the real-demo graph test genuinely executed. The former `ThreeCases.test_reports_match_schema` now appears as `Cases.test_reports_match_schema` and executed too. Evidence: `suite-default.json`, `suite-strict.json`, and their verbose logs.

Strict-mode independence was tested by launching a child interpreter with `-S`, genuinely making jsonschema unavailable: default mode skipped the oracle check (exit 0), while strict mode recorded a failure, no skip (exit 1). This is in `artifacts/gates/`, not inferred solely from the developer's monkeypatch test.

Independent probe batches, separate from those 134 tests:

| Batch | Recorded checks | Passed expected assertions | Differing assertions | Interpretation |
|---|---:|---:|---:|---|
| `independent.py` | 83 | 63 | 20 | Raw exploratory expectations, not 20 confirmed bugs |
| `refined.py` | 12 | 9 | 3 | Corrected hash/gap expectations; two confirmed protocol defects; nested extraction expectation not an additional defect |
| `extra-gates.py` | 8 | 8 | 0 | Six invalid API+CLI HTTP gates and two missing-oracle controls |
| `full-scope-v2.py` | 7 | 7 | 0 | Actual five-object scaffold scope controls and unsupported negative using a real complete bundle |
| `crosswalk.py` | 1 | 0 | 1 | Confirmed wrong-object solution association |

These batches overlap and are not a statistical benchmark. Inputs, outputs, call counters, CLI codes, and exceptions are preserved. Raw differing expectations were adjudicated by source inspection and independent oracles. In particular, the initial missing-config-hash helper restored that field during rehashing; a corrected deletion rejects. The first gap test used a different fixture's interval; corrected in-window/optional/outside controls pass. Empty surface lists and the changed top-level status have not been counted as independently established schema violations. The first full-scope harness used a bad CLI invocation and an incorrect outcome literal; its artifacts are preserved, and v2 uses `--request` and the actual defined outcome. None of these harness corrections changed production code.

Malformed model tests included empty/unparseable/truncated text, missing findings or required finding fields, wrong field types, unknown categories, unknown nodes, hallucinated citations, and model-supplied status assertions. They did not reproduce the original crash. Accepted findings cannot override Critic's computed status. Content extraction can accept a complete nested `findings` object from otherwise incomplete surrounding text; response termination must be handled separately. Scientific truth or semantic entailment is not established by this screening.

## Actual frozen Phase 5 integration

Used unchanged release `phase5-structured-1.0.0` with descriptor/source validation in `verified_session` mode. This verifies current source identity once per session; it is not historical runtime attestation or physical calibration. Database and catalogue were opened through the existing read-only interface; their before/after file signatures were unchanged.

- Database: `/disk/1/data/niktakbr/trustworthy-phase5i-working/expanded.sqlite`, 1,411,190,784 bytes, SHA-256 `f6dbea047ad16c5420c34ff002e068e4ade41ab52806c936816aaf7019f303c8`.
- Catalogue: `/disk/1/data/niktakbr/trustworthy-phase5k-working/catalogue.sqlite`, SHA-256 `ff9fe4d422c274f3f109d76ae21b91d9d6364fd568f52ce7b5fa1501bbcbae0e`.
- Execution: `libero_long_openvla_oft_task00_seed1000_trial000_cfafd9ddc3db`.
- Task: `2448c758145ae5ad500f`; variant: `xmlenv:574b783c023e533eb3a5c8e92557aa0a940aa5ff6cfbe794f5614e9fd321148e`.
- Full R1 review interval: saved frames `[10,257]`, first policy boundary after ten settling commands through terminal recorded snapshot. Evidence retrieval can cover a selected subwindow without shortening the reviewed requirement.
- Protected objects: `cream_cheese_1`, `ketchup_1`, `orange_juice_1`, `milk_1`, `butter_1`.

The request used explicit obligations for recorded robot joint positions and object geometry identity; it did not request or invent a qualified physical safety certificate. The GSN supplied to Critic was a **manually authored unresolved audit scaffold**, not a Drafter/model output, with no invented registry measurements or checker assessments. `test_fixture=false` does not make that scaffold an empirical assessment. Its actual structured bundles came from the frozen retriever.

| Actual request | Frozen response status | Critic result | CLI | Accepted physical outcome |
|---|---|---|---:|---|
| Legitimate joint positions at frames 11–12 plus cream-cheese identity | `COMPLETE WITHIN VERIFIED CONTRACT` | Accepted | 0 | `insufficient_information` |
| Additional mandatory action metadata covering settling boundary | `PARTIAL` | Accepted; missing obligations retained | 0 | `insufficient_information` |
| Unsupported historical producer-attestation obligation | `UNSUPPORTED` | Accepted informational refusal | 0 | `insufficient_information` |
| Requested samples after terminal frame | `UNAVAILABLE` | Accepted; missing evidence explicit | 0 | `insufficient_information` |
| Deliberately wrong variant | `INVALID SCOPE` | Rejected, `RET-SCOPE` | 3 | None |

The legitimate response had two groups/two items; the partial response three groups/four items. Unsupported/unavailable/invalid-scope responses supplied no fabricated items. Request/response IDs, exact citations and original evidence IDs, selectors, source integrity, assurance, limitations, fulfillment/missing obligations, and scope were retained in the archived input pairs and report representation. After each review the supplied original request and bundle remained equal to their pre-review values. The report is a summary rather than a lossless copy of the bundle; retain the archived pair for complete provenance.

The initial audit wrapper omitted two required retrieval-context fields and was correctly rejected by the request schema. Its failed reports are preserved. The v2 wrapper adds only those required context fields; it does not alter the real request/bundle. The corrected legitimate/partial/unsupported/unavailable wrappers all pass, while variant mismatch is rejected. A deliberate no-violation vector attached to the real complete bundle produces five `CONCL-UNSUPPORTED` findings, CLI 1, and accepted outcome `insufficient_information`.

Evidence: `harness/real_phase5.py`, `artifacts/real-phase5/*.request.json`, `*.bundle.json`, `*.critic-input-v2.json`, `*.critic-report-v2.json`, `*.cli.*`, `review-summary-v2.json`, source verification/before-after metadata, and `full-scope-v2/retrieval-complete-claims-negative/`. This establishes real informational integration for the exercised scope, not universal compatibility or the correctness of the crosswalk in R2-06.

## Actual LLM evaluation: setup and limits

Hestia has four NVIDIA L40S GPUs, 46,068 MiB each; driver 595.99.02 reports CUDA 13.2. Only physical GPUs **0 and 3** were assigned to this audit (`CUDA_VISIBLE_DEVICES=0,3`); GPUs 1 and 2 were left to their existing users. Both model endpoints were bound to `127.0.0.1`, never publicly exposed. No inference ran on Indigo.

Runtime: existing Hestia Python 3.12 environment, vLLM 0.31.0, PyTorch 2.13/CUDA 13.0; exact package versions in `artifacts/models/runtime-pip-freeze.txt`. Model identifiers and pinned revisions:

| Model | Revision | Checkpoint form |
|---|---|---|
| `Qwen/Qwen3-32B` | `9216db5781bf21249d130ec9da846c4624c16137` | Full original BF16, existing local weights |
| `openai/gpt-oss-20b` | `6cee5e81ee83917806bbde320786a8fb61efebee` | Original configured checkpoint, native MXFP4; downloaded to AUDIT/models |

Used unchanged `critic.compare_models` criteria and fixtures A/C/D/E, one repeat per eligible case/model, max output 8192 tokens. Case B is skipped by the implemented runner because validation rejects it before inference. This is a small exploratory comparison on **synthetic argument inputs with real model inference**, not real physical evidence or a reliability benchmark. One repeat is an explicit CLI setting, fewer than the documented example's three. No model substitution occurred.

Qwen's Critic preset uses thinking-mode defaults, temperature 0.6, top_p 0.95, top_k 20. GPT-OSS uses temperature 0 and the configured `Reasoning: medium` suffix. No forced JSON mode was added. Both used tensor parallelism 2, maximum context 32768, one active sequence and eager execution. Qwen used the qwen3 reasoning parser. The initial Qwen sampling attempt failed inside FlashInfer because nvcc and `/usr/local/cuda` were absent. All four failed requests and reports were preserved; they are not successful model generations. A same-checkpoint retry disables FlashInfer sampling through supported `VLLM_USE_FLASHINFER_SAMPLER=0`, retaining the sampling parameters.

An external transparent local proxy recorded the exact requests and real upstream responses in `artifacts/models/http-*/`. It generated no synthetic responses and omitted authorization headers. The unchanged review function produced the saved complete reports; an external recording wrapper saved them without altering review behavior. See the appended final execution supplement for observed model outputs and cleanup.

## GSN `ev:` versus `evidence-citation:` compatibility

The developer's statement is correct about the **current semantic pipeline**, but too broad if interpreted as a literal JSON-schema prefix prohibition.

1. `evaluation/r1_v4/evidence_registry_gsn/gsn_graph.schema.json:1` permits any string or null for `evidence_id`; it has no `ev:` pattern and does not itself prohibit `evidence-citation:`. The current shared runtime is stricter: `gsn.py:33–56` requires every solution to resolve through the Registry and match source, selector, temporal scope, identity, origin and status. `models.py:74` generates registry IDs as `ev:` plus the content digest. Simply inserting a Phase 5 citation therefore does not work through the current Registry/Graph semantics.
2. Critic can already retain exact Phase 5 citations alongside GSN registry references, through the original request/bundle and structured report rows. No GSN evidence-node migration is needed for that informational preservation. The actual real-bundle audit demonstrates it.
3. A separately validated crosswalk can preserve both namespaces without changing the graph's string schema. It must prove source/selector/component/units, requirement/execution/task/variant/object, clock/domain/interval, admitted capability and uncertainty compatibility. Current `retrieval.link` only joins declared original IDs and is not that proof, as R2-06 demonstrates.
4. Direct Phase 5 solution references would require a versioned semantic resolver/admission contract, updates to Registry/Graph validation or a new compatible resolver, Critic evidence admission, Drafter graph-eligible evidence selection/serialization, and cross-component regression tests. Drafter `CONTRACT.md:123` currently requires original graph-eligible `ev:` records; `:143–149` forbids repairing/renaming model citations. The Phase 5 `EVIDENCE_CITATION_CONTRACT.md:3` defines its own citation basis over frozen database/source identity and exact retrieval interpretation. These identities must not be silently renamed or invented.
5. Risks include false crosswalk associations, identity laundering, scope/time/unit/selector mismatch, lost uncertainty, source-integrity mistaken for capability, successful retrieval mistaken for safety, and backward incompatibility with frozen consumers. An authenticated source or content digest does not certify a physical conclusion. No contract migration was implemented here.

## CI recommendation

CI can be added now as a regression guard, using strict mode for its offline gate; a green run must not be treated as resolution of this audit. The current 134 tests are suitable for ordinary CPU CI with Python 3.12 and pinned jsonschema; they require no model credentials or GPU. Fake HTTP integration uses loopback and must remain labeled synthetic. Keep installation dependencies pinned and run from a clean checkout with explicit test discovery and zero-skip assertions. Python 3.9's annotation-import shim is not needed for the recommended supported interpreter.

Include independent regressions for the exact counterexamples above, schema-oracle agreement, full checker-result validation, admission decision consistency, shared graph canonical validation, numeric exception containment, uniquely scoped/temporal citations, completion metadata, and validated crosswalks. Preserve failing inputs; do not weaken rules to pass the suite. Strict mode genuinely fails when an oracle is absent; it does not prove test coverage is adequate.

Separate protected Hestia jobs should cover real frozen Phase 5 data with read-only access and pinned database/source hashes. Separate manual or scheduled Hestia GPU jobs should deploy pinned checkpoints and save actual request/response metadata, prompts and outputs. Do not place private evidence/model weights in ordinary GitHub artifacts or require GPU inference on every pull request. Scientific quality evaluation needs a predefined corpus, adjudication protocol, repetitions/seeds and uncertainty reporting beyond the small comparison. No GitHub Actions workflow was created or modified.

## Remaining work and owners

| Work | Classification | Suggested owner |
|---|---|---|
| Enforce complete checker schema and semantic admission consistency; keep empirical admission disabled | Blocking before integration | Critic; shared checker-contract coordination |
| Make Critic graph validation agree with canonical shared validator before every model call | Blocking before integration | Critic |
| Contain malformed numeric/request failures with documented report/status/exit semantics | Blocking before integration | Critic |
| Require unique graph targets and temporal/clock-aware admitted citations | Blocking before automatic integration | Critic |
| Validate or explicitly reject unsupported Phase 5-to-registry crosswalks | Blocking before evidence-linked integration | Critic + RAG + shared integration |
| Preserve/validate actual completion identity, termination and usage; support documented aliases | Required before scientific evaluation | Critic |
| Integrate original Phase 5 pair without lost obligations, using a versioned validated evidence bridge | Required before full Drafter–RAG–Critic evaluation | Shared integration + Drafter + RAG |
| Define trustworthy producer/configuration boundary and physical-checker admission before empirical safety claims | Required before scientific evaluation | Shared integration |
| Expand adversarial regressions and strict CPU CI; separate real-data/GPU gates | Required before scientific evaluation | Critic + shared integration |
| Clarify comparison metric labeling (`false_positive` also computed for nonblocking E), publish seeds/repetitions and evaluation protocol | Non-blocking improvement for exploratory use; required for comparative scientific claims | Critic |

## Reproduction and artifact locations

Connect using the already-authenticated Mac control socket and use Indigo only as relay. Do not change keys/passwords. On Hestia:

```bash
cd /disk/1/data/niktakbr/critic-r2-audit-20261105
source harness/env.sh
cd "$REPO"
git rev-parse HEAD
"$AUDIT_PY" -m unittest discover -s critic/tests -t . -v
CRITIC_STRICT_TESTS=1 "$AUDIT_PY" -m unittest discover -s critic/tests -t . -v
```

Original exact runners and invocation scripts are `harness/run-suites.sh`, `run_suite.py`, `run-independent.sh`, `independent.py`, `refined.py`, `extra-gates.py`, `full-scope-v2.py`, `crosswalk.py`, `verify-counterexamples.py`, `reproduce-legacy.py`, and `real_phase5.py`. They save request/response/report/call/exit details. Many audit scripts intentionally create unique artifact directories and refuse to overwrite them; reproduce in a fresh audit root or a fresh copied output directory, preserving the same source revision and recorded input files. Do not rerun into existing artifacts.

For the real retriever, `real_phase5.py` is the complete executable structured-interface recipe with frozen DB/catalogue paths, `verified_session` setup, actual execution selection, explicit obligations, and source validation; its saved requests can be replayed unchanged using the same frozen interface. Corrected v2 wrappers are archived rather than silently replacing the initial invalid wrapper.

Model deployment/invocation commands are executable in `harness/model-env.sh`, `serve-qwen.sh`, `serve-gptoss.sh`, `serve-qwenretry.sh`, `run-models.sh`, `retry-qwen.sh`, `run-proxy.sh`, `recording-proxy.py`, and `compare-real.py`. Checkpoints, runtime packages, served identifiers, discovery responses, GPU state and raw traffic are archived separately from source. The underlying comparison command is:

```bash
"$AUDIT_PY" -m critic.compare_models \
  --model MODEL_IDENTIFIER=http://127.0.0.1:18015/v1 \
  --repeats 1 --max-tokens 8192 --out NEW_OUTPUT/comparison.md
```

The proxy forwards to the selected real server at loopback port 8000. Run one selected model at a time, using GPUs 0 and 3 and the exact recorded deployment script; stop only verified audit-owned processes. Large model weights, caches, venvs and raw runtime outputs remain outside Git.

A bulk export of all artifacts to the Mac was rejected by automatic approval review because it could include sensitive real evidence/raw outputs beyond a specifically approved transfer. The audit continued without bypassing that rejection. Full reproducible artifacts remain on Hestia. The report itself is independently authored and can be reviewed without exporting private evidence.

## Final recommendation

1. **Are all November 4 findings fixed? No.** I2, the original I5 crash, I6 binding, and I11 filtering pass the tested controls; I1/I3/I4/I7/I8/I9 retain independently reproduced weaknesses.
2. **Is the Critic correct within its documented scope? Not yet.** Admitting schema-invalid checker results, diverging from shared graph validation, and raising on bad input contradict that scope.
3. **Does it safely reject invalid/misleading evidence? Many cases, but not comprehensively.** The original fabricated authority is blocked and empirical admission stays disabled; the confirmed dependency/scope/crosswalk counterexamples remain.
4. **Is Phase 5 integration correct? The actual informational request-and-bundle pathway works for the tested execution/statuses. Full evidence-link correctness fails the adversarial crosswalk test.** Retrieval completeness did not become safety assurance in the exercised tests.
5. **Has real LLM behavior been demonstrated? Yes, for both configured comparison models on four synthetic fixtures each.** All eight successful actual completions parsed; Qwen also generated false positives on the correct unresolved case. Synthetic model tests prove software control behavior only; actual HTTP traces are separate. See the final execution supplement.
6. **Ready for Drafter–RAG–Critic integration? Not for trusted evidence-linked integration.** A deliberately unresolved, informational research scaffold can be exercised with the stated limitations; the blocking admission/validation/grounding issues must be fixed first.
7. **Ready for scientific evaluation? Not as a validated integrated system or basis for reliability/safety claims.** These exploratory executions can inform evaluation design; a preregistered broader protocol and completion/provenance controls are still needed.
8. **Before proceeding:** address R2-01 through R2-06, add independent regression tests and rerun strict mode/real frozen integration; then complete response-metadata assurance and a controlled repeated real-model evaluation. Preserve the disabled empirical promotion boundary. The Critic developer should fix the Critic issues; no silent fixes were made by this audit.

## Final actual-model execution supplement

Both configured models completed the comparison on Hestia. There were **12 real client HTTP attempts**: four initial Qwen deployment failures (two upstream HTTP 500 errors followed by two proxy HTTP 502 errors after the upstream stopped), four successful GPT-OSS completions, and four successful Qwen retry completions. All failed calls were reported as `completed_llm_failed`, without a Critic crash. All eight successful envelopes were HTTP 200, identified the requested model, and ended with `finish_reason="stop"`; none was an observed truncated generation. This metadata was independently verified from actual proxy recordings, because Critic itself currently ignores it.

| Real model | Case | Critic status / JSON | Accepted model criticisms | Implemented expected-hit / false-positive metric | Latency s |
|---|---|---|---|---|---:|
| GPT-OSS-20B | A unsupported claim | completed / parsed | 7: C05, C09, C12 | Expected issue hit | 89.162 |
| GPT-OSS-20B | C correct unresolved | completed / parsed | 0 | No false positive | 47.968 |
| GPT-OSS-20B | D hidden checker result | completed / parsed | 1: C06 | No expected-hit metric defined | 164.088 |
| GPT-OSS-20B | E partial retrieval | completed / parsed | 0 | Runner flags no false positive | 76.162 |
| Qwen3-32B | A unsupported claim | completed / parsed | 4: C09, C12 | Expected issue hit | 70.242 |
| Qwen3-32B | C correct unresolved | completed / parsed | 3: C09 | **False-positive case flagged** | 66.079 |
| Qwen3-32B | D hidden checker result | completed / parsed | 2: C07 | No expected-hit metric defined | 124.290 |
| Qwen3-32B | E partial retrieval | completed / parsed | 3: C07 | Runner flags false positive; see interpretation below | 109.856 |

All twenty accepted model findings were nonblocking, human-review-required proposals. None cited a nonexistent record/node under the implemented identity checks; no findings were screened out in these eight successful runs. Qwen's five C07 proposals cited genuinely admitted same-object **synthetic** checker assessments from the supplied fixture. GPT-OSS's D finding used `object_id=null` with node `D1` repeated across graphs and cited assessments for several objects: this is an actual example of the graph-target ambiguity exposed by R2-05. An independent original Draft202012 report-schema check and ID/admission screen were run on the saved reports; their results are archived in the final model summary.

Qwen's Case C explanations assert that geometric-contact uncertainty was not propagated to the final conclusion. The actual fixture's conclusion at `critic/cases/case_c_correct_unresolved.json:1011` explicitly says R1 cannot be determined, initial support and falling remain unresolved for every object, and no admitted checker assessment exists. Its per-object outcomes are all `insufficient_information`. The three C09 criticisms therefore demonstrate over-criticism of the intended correct unresolved case, despite valid cited IDs and parseable JSON. This is an observed model-quality limitation, not proof that the code promised to solve semantic entailment. Human review remains necessary.

The comparison runner's E “false positive” is a coarse metric: it treats any accepted model finding in a nonblocking expected case as false positive. E also contains generic D1 defeaters alongside admitted synthetic checker results, so some criticisms of internal wording can be arguable. Do not automatically equate that flag with an independently adjudicated false criticism. The table header says “on Case C” even though the implementation also applies it to E. Likewise `json_ok` is actually `llm.ok`, not a pure JSON-syntax metric. Raw reports are needed to interpret these scores.

The synthetic E fixture's accepted execution outcome is `violation_observed` because it contains an admitted synthetic positive checker result; this was already present during the initial failed model pass. It is **not** a real physical observation or a conclusion derived from retrieval completeness. The actual frozen Phase 5 audit scaffold, which has no admitted checker result, remained `insufficient_information` throughout.

Saved evidence:

- `artifacts/models/gptoss/` and `qwenretry/`: exact inputs, complete reports, comparison JSON and Markdown.
- `artifacts/models/qwen/`: all initial failed reports, retained separately.
- `artifacts/models/http-001` through `http-012`: exact real requests/responses, body hashes, HTTP status and elapsed time. These requests contain the actual system/user prompts; response envelopes retain reasoning/content, model IDs, usage and termination fields.
- `artifacts/models/*-discovery.json`, `gptoss-checkpoint.json`, runtime package freeze, deployment/readiness/server logs, cleanup records, and final NVIDIA state.
- `harness/summarize-real-models.py`: independent report-schema and admitted-ID checks; the final summary distinguishes failed attempts from successful completions.

The only deployment adaptation for the successful Qwen retry was the supported compiler-free sampler setting; the checkpoint, Critic prompt, thinking mode and sampling preset were retained. No explicit per-request seeds were supplied; this audit records a single run per fixture, not exact-output determinism. The server's resolved launch configuration and every request are retained for reproduction. DeepSeek was a desk-comparison candidate explicitly not taken forward in `MODEL_COMPARISON.md`; it was not substituted or run.

All audit-owned model server processes were stopped after the final run. GPUs 0 and 3 returned to their previous display-only memory footprint; GPUs 1 and 2 were untouched. The local recording proxy was also shut down after recording completed. The real inference pathway is now demonstrated, but these eight exploratory completions neither establish general model reliability nor resolve the confirmed code/admission defects. **Final verdict remains FAIL.**
