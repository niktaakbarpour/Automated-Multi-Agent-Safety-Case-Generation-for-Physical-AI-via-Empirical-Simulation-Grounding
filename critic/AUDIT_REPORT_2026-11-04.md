# Independent Critic audit

## 1. Executive verdict

**FAIL — Handoff not satisfied.** Audited merged main commit `7085fb7b341b847ba903a4f93da6407244d19b34`, not the historical Phase 5L feature branch. The implementation is a meaningful midpoint prototype, with deterministic graph checks, execution bundles, JSON schemas, an actual configurable HTTP LLM client, typed criticism and offline demonstrations. It is not an acceptable completed Critic: checker authority is self-asserted, scope/applicability conflicts are missed, declared schemas are not enforced at runtime, malformed graphs still reach the model, malformed model findings can crash review, and the accepted structured evidence interface is not connected.

No source, tests, schemas, documentation, Git refs or project evidence were changed. A separate snapshot and audit artifacts were created under `/private/tmp/critic-audit-7085fb7`. No external LLM API, simulation or HPC workload was invoked. The local fake HTTP server test was run. Findings below distinguish confirmed behavior from unverified real-model behavior.

All paths/lines below are relative to the audited repository revision. The snapshot is also available through `/private/tmp/critic-audit-repo`.

## Inspection: entry points and data flow

- `critic/__init__.py:8` exports `review` and `CRITIC_VERSION`; `critic/critic.py:14–56` implements review.
- `critic/__main__.py:25–59` exposes CLI; default backend is rules only, with explicit scripted and OpenAI-compatible choices.
- `critic/checks.py:576–588`: top-level shape -> index records -> bundle coverage -> each object graph -> claimed conclusions. Only top-level shape failures set fatal.
- `critic/llm.py:64–103`: actual standard-library chat-completions HTTP client; URL/model/key configurable, timeout supplied to urlopen. No model library, GPU or external service is needed for rules-only use.
- `critic/llm.py:116–140`: compact model input and inspectable prompt `critic/prompts/critic_system_v1.md`; `221–241`: invocation, parsing and screening.
- `critic/contract.py`: copied graph/record vocabularies, content-ID hashing and R1 outcome precedence. Runtime does not call Graph.validate or Record.parse.
- Inputs wrap one graph per protected object at execution level. Evidence is legacy registry records. Checker assessments use a newly declared envelope, not the current ObjectAssessment contract.
- Report has stable per-report CRIT numbers, categories C01–C13, node/object, cited IDs, rule refs, explanation, suggested action, source, blocking and human-review flags. No revision agent is implemented or required here.
- Schemas, all three fixtures, generator, scripted replies, example reports, tests, prompt, README and desk model comparison were inspected. No separate repository AGENTS.md was found in the downloaded snapshot.

## 2. Requirement-by-requirement checklist

| Requirement | Status | Repository evidence | Finding |
|---|---|---|---|
| Machine-readable input/output definitions | PARTIAL | critic/schemas/critic_request.schema.json:1–128; critic_report.schema.json:1–98 | Present, but not runtime enforced; graph/record children are opaque objects rather than enforced schema refs. |
| Claim/graph and requirement input | PARTIAL | request schema:14–40,43–76; checks.py:105–118 | IDs/version and graph wrapper exist; full authoritative R1 configuration is neither required nor bound. |
| Evidence/provenance input | PARTIAL | checks.py:142–173,356–414 | Legacy record metadata/hash checks; no actual Phase 5 bundle handling or verified-source attestation boundary. |
| Checked empirical records | FAIL | checks.py:457–461,498–541 | Caller-provided authority string is treated as validated; admissibility, requirement/time/clock/task/variant and conflicts not established. |
| Execution/task/variant identity | PARTIAL | request schema:14–40; checks.py:325–334,382–403 | Execution/object checks exist; task/model not compared; variant has no validated contract. |
| Complete R1 protected-object configuration | FAIL | checks.py:105–118,178–215 | Completeness checked against caller's list only; omitted configuration cannot be detected. |
| One graph per protected object | PARTIAL | checks.py:193–214 | Detects missing, duplicate and extra graphs relative to declared list; unresolved/NA objects can be retained. No trusted full-list binding. |
| Pre-LLM structural validation | FAIL | critic.py:24–31; checks.py:576–588 | Errors collected, but invalid graphs/references do not set fatal and still invoke LLM. |
| Graph.validate consistency | PARTIAL | checks.py:220–414; gsn.py:33–76 | Broad rule mirroring is present, but neither actual validator nor full schema/canonical validation is called. Oracle tests could not run in local Python 3.9. |
| Invalid input explicit failure | PARTIAL | critic.py:25–29; __main__.py:43–55 | Fatal shape errors produce C01; deeper invalid data proceeds; CLI returns zero even for rejected input/model failure. |
| Configurable working LLM client | PASS | llm.py:64–103; __main__.py:16–22 | Actual HTTP client and model/provider URL configuration. Fake-server test passed. Real inference unverified. |
| Inspectable prompt | PASS | llm.py:23–24,116–140; prompts/critic_system_v1.md | Explicit versioned prompt and compact JSON context. |
| Parsed/validated model output | FAIL | llm.py:148–218,231–240 | Manual ID screening, no schema enforcement; malformed category list crashes outside protected try block. |
| API errors/timeouts | PARTIAL | llm.py:73,98–103,231–238 | Timeout and exception reporting exist. Prompt construction and screening exceptions escape; live provider behavior not tested. |
| Three objection types | PARTIAL | contract.py:60–74 | C07 contradiction, C04 gap, C01/logical categories are represented. C07 grounding is not sound. |
| Reject fabricated/unsupported objections | FAIL | llm.py:180–218 | Unknown IDs rejected; empty or irrelevant known citations can be accepted. All LLM findings are correctly labeled proposals needing review, not independently verified. |
| Preserve uncertainty | PARTIAL | critic.py:80–96; checks.py:516–553 | Good unresolved default, disclaimers and gaps; invalid checker inputs defeat it. |
| R1 applicability/coverage/outcomes | FAIL | checks.py:498–553 | Correct outcome vocabulary, but applicability is ignored and positive scope is unchecked; contradictions can be fabricated or missed. |
| R1 execution aggregation | PARTIAL | contract.py:95–103; checks.py:477–494 | Correct basic precedence over claimed outcomes; incomplete vectors are filtered, conflicts ignored, empty/global-invalid handling incomplete. |
| Five-object LIBERO profile and policy-to-terminal interval | PARTIAL | request schema:14–40; checks.py:105–118 | Can carry names and interval, but no authoritative configuration or boundary validation; fixtures exercise three synthetic objects only. Generalization is valid, hardcoding five universally is not the remedy. |
| Supported structured retrieval compatibility | FAIL | README.md:87–95; final_phase5_release/api.py:18–23 | Explicitly unimplemented adapter; bundle items and IDs are not registry records/ev IDs. |
| Partial/unsupported/invalid retrieval handling | FAIL | critic.py:88–93; README.md:91–93 | Boolean/gaps abstraction cannot preserve actual statuses, obligation identities, assurance, interpretation conditions and scope verification. |
| Tests and runnable demonstration | PARTIAL | tests/test_critic.py; __main__.py; cases | 32 discovered; 29 passed, 3 skipped in feasible local run. Four CLI demos succeeded. No live LLM or end-to-end evidence integration demonstrated. |
| Model comparison | PASS (documentation only) | MODEL_COMPARISON.md:1 onward; compare_models.py | Desk comparison and exploratory runner exist; explicitly not measured. Model-card accuracy was not independently researched in this code audit. |
| Reproducible model trace | PARTIAL | critic.py:44–55; llm.py:223–224; compare_models.py:35–51 | Model/backend/prompt-version/latency/error recorded; full prompt, raw response, request digest and effective model settings not preserved. |
| Revision-consumable output | PARTIAL | critic_report schema; critic.py:33–56 | Useful structured shape; runtime validity and grounding are insufficient for reliable automatic consumption. |
| Integration readiness | FAIL | README.md:87–102 | Existing prototype contracts need explicit adapters, trust enforcement and negative integration tests. Missing Drafter/revision implementations are not counted as defects. |

## 3. Issues found

### I1 — Critical: self-asserted checker authority becomes a verified contradiction

**Location:** `critic/checks.py:457–461,507–515,530–541`; `critic/contract.py:57`; request schema:86–105.

Current: checks accept assessments based on execution ID, object ID and an `authority` string. Assessment IDs need not refer to checked records or authenticated outputs. Requirement/version, task, variant, clock/domain, applicability, producer/admission status and positive temporal overlap are not validated. A synthetic assessment is accepted even with `test_fixture=false`.

Reproduction: an assessment labeled `validated_checker`, with nonexistent ID `made-up`, requirement R999/version 999, wrong task/variant and interval [10000,10001], generated C07 `CONCL-HIDES-VIOLATION` against a monitored [8,120] unresolved claim. Its explanation called the result a validated assessment and suggested reporting the verified violation. A synthetic assessment in a request marked real did the same.

Required: consume an explicit trusted checker-output contract, validate source/producer/admission and requirement/configuration/execution/object/task/variant/temporal scope, require evidence dependencies, separate synthetic routes and reject unsupported empirical authority. Do not enable empirical admission. An unavailable admitted physical checker must leave the result unresolved, not be replaced by a caller flag. This is not a requirement for a cryptographic service if the project uses a trusted in-process boundary; that boundary must actually exist and enforce the contract.

### I2 — High: conflicting assessments and inapplicability can endorse a negative

**Location:** `critic/checks.py:507–541`; R1 authority `requirements/r1_generalized_v2/FORMAL_SEMANTICS.md:159–165,177–192`.

Current: the claimed outcome is accepted if it appears anywhere in the reported set. Applicability is not inspected. Negative coverage only checks numeric containment, without clock/domain or applicability.

Reproduction: all three objects claimed no violation, with assessments declaring `applicability=not_applicable`, wrong requirement/clock, covering [8,120], produced no criticisms. Adding an assessment reporting a violation for the first object still produced no criticisms and recomputed the execution as no violation.

Required: validate admissibility first, retain conflicts and uncertainty, prevent negative evidence overriding admissible positives, enforce applicability and clock-aware coverage. Match actual claim semantics; an insufficient assessment is a gap, not automatically a physical contradiction. Do not simply choose a matching outcome from a set.

### I3 — High: supplied JSON schemas are not enforced

**Location:** `critic/checks.py:87–137,142–173`; `critic/critic.py:14–56`; request schema:8,18,43–48; record authority `evaluation/r1_v4/evidence_registry_gsn/models.py:47–82`.

Current: hand-written shape checks omit declared mandatory fields, types, constants, uniqueness and additional-property rules. Record checks require keys/hash/version but do not enforce Record.validate semantics; hashing a fabricated envelope does not establish authenticity or permitted measurement semantics. Output is not runtime-schema validated.

Reproduction: removed `test_fixture`, benchmark, task, checkpoint, surfaces and contract versions. The request still reached the scripted LLM with no findings, and output `test_fixture=false` although the payload remained synthetic. Consistently changed node and record requirement IDs to R999 with recalculated IDs while context stayed R1; no finding resulted.

Required: enforce request and nested graph/record schemas plus semantic validators before review/model call; validate output schema and explicit error state. Validate requirement IDs against context, not merely mutual graph consistency. Synthetic exemptions must be explicit and cannot silently turn real. Use the existing registry validation contract rather than only its key list.

### I4 — High: malformed GSN/references do not stop LLM execution

**Location:** `critic/checks.py:576–588`; `critic/critic.py:24–31`.

Current: fatal reflects top-level shape only. Graph, record and scope failures are added to findings and then sent to the LLM.

Reproduction: appended G1 -> MISSING edge; C01 was recorded but `llm.called=true`.

Required: distinct validation phase; reject structurally/referentially invalid input before model invocation, retain explicit diagnostics and distinguish rejection from a completed critique. Critic logical concerns on a structurally valid argument can still be reviewed. The existing suite tests flagging invalid graphs, not the mandatory no-call condition.

### I5 — High: malformed model findings crash the Critic

**Location:** `critic/llm.py:199–215,231–240`.

Current: screening occurs outside the exception handler. `category not in K.CATEGORIES` hashes arbitrary JSON types.

Reproduction: `{"findings":[{"category":[], ...}]}` raises `TypeError: unhashable type: 'list'`. The report is not returned. Existing random-corruption tests mutate requests, not this output case.

Required: enforce finding schema and safe type checks, contain screening failures, return explicit failed/rejected LLM review status. Keep successful deterministic diagnostics. Do not silently convert model failure into a successful empty critique.

### I6 — High: original R1 configuration and temporal boundaries are unbound

**Location:** `critic/checks.py:105–118,178–215,477–494`; request schema:14–40; `critic/tests/test_critic.py:88–95`.

Current: both context and bundle can share a reduced protected-object list and pass. No complete R1 config/hash, support rules, object-surface mapping or first-policy/terminal boundary validation is required. An empty configuration produces no findings and no explicit empty-scope classification.

Reproduction: reduced all caller lists/graphs/outcomes to one object; no findings. Empty lists also gave no findings and null recomputed outcome. These are not proof that smaller generalized configurations are invalid; they prove there is no way to detect unauthorized reduction from the intended configuration.

Required: bind a validated authoritative configuration and resolved boundary provenance, compare its complete list with all object graphs/outcomes, retain NA/unknown objects and distinguish valid generalized profiles, empty scope and invalid configuration. Add the real five-object LIBERO profile test, without globally hardcoding those names. Aggregate the full validated vector, not only values remaining after missing/invalid entries are filtered.

### I7 — High: Phase 5 structured evidence integration is absent; proposed mapping is lossy

**Location:** `critic/README.md:87–95`; `critic/checks.py:142–173,356–414`; `evaluation/r1_v4/rag_evidence_database/final_phase5_release/api.py:18–23,68–83`; `DOWNSTREAM_HANDOFF.md:5–18` in that directory.

Current: Critic accepts flat `ev:` registry records. Phase 5 returns grouped items, original IDs, `evidence-citation:` IDs, obligation IDs, assurance, interpretations, exact source references, completeness and missing statuses. Groups are not registry records and cannot simply be assigned to `records`. A missing-obligation entry is not the Critic's object/measurement/interval gap schema. COMPLETE covers explicit mandatory obligations only, not complete R1 observations.

Required: a tested, lossless adapter or versioned consumer schema: retain canonical citations/original IDs, source hashes/selectors, execution/task/variant, requested and fulfilled obligations, timing, assurance/integrity and conditional interpretations. Define how graph solution references resolve to authoritative registry/citation identities. Preserve PARTIAL/UNAVAILABLE/UNSUPPORTED/INVALID SCOPE/UNVERIFIED PLAN distinctly. Never promote observations into checked physical events. No production end-to-end integration was demonstrated.

### I8 — Medium: LLM objection screening validates existence, not support

**Location:** `critic/llm.py:165–218`.

Current: known IDs are pooled across records and all checker assessments. No evidence-to-target object/requirement/time/support relationship is checked for model findings. C07 can cite no evidence. Reproduction: a scripted C07 saying evidence proves a violation with `evidence_ids=[]` was accepted.

Mitigation already present: accepted findings are always `llm_proposed`, nonblocking and require human review. Therefore this is not evidence that generated findings are automatically marked empirically verified. It is still insufficient to meet the requirement to reject unsupported empirical objections.

Required: distinguish reasoning proposals from evidence-grounded empirical objections, require admitted matching checked evidence for C07, reject or explicitly quarantine unsupported categories and wrong-scope known citations. Do not implement a general safety judge.

### I9 — Medium: validation/review status is insufficiently explicit for automation

**Location:** `critic/critic.py:44–76`; `critic/__main__.py:43–55`; report schema:76–98.

Current: report has findings and model status, but no explicit overall validated/rejected/failed review state. CLI always returns zero for a generated report, including fatal request errors/model failure. Some Graph-invalid conditions such as duplicate edges are low severity/nonblocking (`checks.py:261–264`); an unsupported goal is medium/nonblocking (`279–284`).

Required: expose machine-checkable input-validity and review-completion states, clearly distinguish diagnostic findings from successful review, and document or implement CLI failure semantics. A consumer must not treat `blocking_defects=false` or process exit zero as validated acceptance. Low-severity logical suggestions may remain nonblocking, but structural validity cannot be inferred from severity.

### I10 — Medium: model reproducibility and final acceptance evidence are incomplete

**Location:** `critic/llm.py:72–103,116–140,221–241`; `critic/compare_models.py:35–51`; `critic/MODEL_COMPARISON.md:1–5`; tests:25–28,53–55.

Current: model/backend/prompt-version/latency/errors recorded, but not effective settings, prompt bytes/hash, raw output or input/evidence/configuration identity. Real-model comparison has not run. Oracle imports catch any Exception and skip, so test totals alone can hide missing validator coverage.

Required before formal evaluation: reproducible request/config/prompt/output trace, mandatory validation dependencies and a supported Python runtime in CI, negative tests for the demonstrated trust/scope/schema failures, and measured behavior on authorized local models. A desk comparison already satisfies the brief documented comparison component; absence of paid-provider experiments is not itself a handoff violation.

### I11 — Medium: all object gaps are treated as negative-claim coverage failures

**Location:** `critic/checks.py:542–553`; authoritative claim-specific validity: `requirements/r1_generalized_v2/FORMAL_SEMANTICS.md:16–22`.

Current code flags every supplied gap for the object whenever its claim is qualified negative; it checks neither temporal overlap nor whether that measurement is required by the admitted evidence route. A missing optional camera or an unrelated interval is therefore treated as a required coverage defect. The existing test checks that gaps produce findings, not that irrelevant gaps are excluded.

Required: intersect with the actual claim/assessment scope and required evidence dependencies. Preserve unrelated missing data as a limitation where appropriate without asserting it invalidates an independently admitted witness. This follows direct code inspection; no additional physical checker behavior is claimed.

## 4. Test results

Environment: macOS isolated snapshot, `/usr/bin/python3` 3.9. The README specifies Python >=3.10; this interpreter can execute core Critic code but cannot import existing union-annotated GSN types. This limits verification and is not counted as a Critic source defect.

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s critic/tests -t . -v`.

- Discovered/run: 32 tests. Final feasible run: **29 passed, 0 failed/errors, 3 skipped**.
- Skips: two original-Graph oracle tests (module incompatible with Python 3.9); one schema-validation test (`jsonschema` unavailable). Those tests are UNVERIFIED, not passes.
- Initial sandbox run: 28 passed, 1 environment error, 3 skips. The error was local socket bind denied. Repeating with local socket permission made the fake-server test pass. No external model service was contacted.
- The passing tests include deterministic examples, checker-envelope contradictions, aggregation precedence, relative missing-object detection, tampered content-ID detection, LLM invented-ID rejection, malformed/empty reply handling, local HTTP-client mechanics, 400 request-mutation subcases and copied vocabulary/hash checks. Subcases are not independent model-evaluation cases.
- Four CLI demonstrations executed successfully, output redirected outside the repository: rules A -> 3 criticisms/blocking; B -> 3/blocking; C -> 0/nonblocking. Scripted A -> 5 criticisms, 2 fabricated-reference findings rejected. No real model was used.
- Twelve targeted independent diagnostic probes executed (seven initial plus five additional). They reproduce schema omissions, LLM invocation despite invalid graph, forged wrong-scope checker objection, synthetic authority accepted as real, empty-citation C07 acceptance, malformed-category crash, root mismatch flagging, negative/applicability conflict acceptance, conflicting positive/negative acceptance, reduced-list trust, empty scope and consistent wrong-requirement acceptance. Probe outcomes are saved verbatim. These are targeted diagnostic counterexamples, not a generalization benchmark.
- Not run: real paid/local LLM inference, exploratory model comparison, simulations, full RAG database/source integration or unrelated expensive regressions. No real checked physical contradiction is demonstrated; the successful checker tests use synthetic dictionaries.

Artifacts: `tests.log`, `tests-unrestricted.log`, `probes.py`, `probes.jsonl`, `more_probes.py`, `more_probes.jsonl`, `demo-*.json` beside this report. Test execution used no bytecode writes. Original source archive and content manifest identify the reviewed snapshot.

## 5. Integration assessment

**GSN/evidence registry:** partially compatible in shape and copied vocabularies; not fully integrated. Original Graph.validate enforces node/edge identity/types, allowed origins/statuses, physical promotion restrictions, scope/time consistency, registered solution identities, provenance/status matching and cycle absence (`gsn.py:33–76`). It does not verify arbitrary statement truth or physical support. Critic mirrors many rules, adds unsupported-goal diagnostics, and does not invoke the validator. Record.parse additionally validates permitted kinds/measurements/metadata/source binding; Critic does not reproduce all of that. Never infer scientific truth from passing Graph.validate.

**Current R1 checker:** incompatible direct input. `evaluation/r1_v4/contracts.py:162–179` ObjectAssessment carries surfaces, reasons, evidence_ids, Coverage, uncertainty, completeness, scope_mismatch, versions and `validation_status=synthetic_analytical_only`. It does not directly provide the Critic's assessment_id/authority/flat interval envelope. An adapter must preserve scope, admitted evidence and synthetic status, not merely add `authority=validated_checker`. The current registry availability adapter explicitly keeps physical checking/admission false (`evidence_registry_gsn/adapter.py:5–16`).

**Restricted structured retrieval:** incompatible direct input; no implementation connection exists. Required mapping is substantive and must be validated, not a field rename. In particular preserve explicit obligations and assurance failure, immutable source references, record identity and the distinction between a measurement and a physical-event assessment. Natural-language retrieval remains experimental.

**Revision consumer:** report is a useful starting schema, but not yet reliable for automatic revision. It must distinguish rejected review, model proposal, admissible empirical objection and unresolved gap. Stable graph/object references help, but current C07 and failure-handling defects block trustworthy automatic consumption. Missing Drafter/revision components are outside the Critic's responsibility and are not counted as failures.

## 6. Prioritized required action plan

### Must fix before integration
1. Establish a validated checker-assessment trust/admission boundary, synthetic isolation and exact scope/applicability/coverage checks. Reject forged, unsupported and conflicting authority.
2. Enforce request/graph/record/output schemas and semantic validation. Stop the model before structural/referentially invalid input. Make rejection/review failure explicit.
3. Fix malformed LLM output handling; require grounded matching checked evidence for empirical contradictions and quarantine unsupported proposals.
4. Bind complete authoritative R1 configuration/protected-object list and resolved policy-to-terminal boundary. Preserve the full object vector and conflict-aware aggregation.
5. Implement and test explicit Phase 5 bundle/citation and current ObjectAssessment adapters, with no observation-to-event promotion or admission changes.

### Should fix before formal evaluation
6. Add regression cases reproducing all confirmed counterexamples and real five-object profile/partial/unsupported assurance cases. Run actual Graph/schema oracle checks on supported Python with dependencies installed.
7. Preserve reproducible model traces and conduct an authorized local-model evaluation on independent cases. Report synthetic/offline and real integration results separately.

### Optional improvements
- Document narrower command/API usage and automate contract-vocabulary drift checks beyond enum copying. The desk model comparison already exists; broader provider support or new agents are not required.

## 7. Final answers

1. **Did the team member implement the originally requested completed Critic? NO.** They implemented a substantial midpoint prototype covering many structural and interface concepts.
2. **Functionally correct? Partially.** Intended synthetic examples run, but confirmed trust, scope, schema and malformed-response defects prevent overall correctness.
3. **Follows current GSN/R1 contracts? Partially.** Much graph vocabulary and outcome precedence agree; full validation, configuration binding, admissibility, applicability and conflict semantics do not.
4. **Consumes supported structured evidence correctly? No.** A compatible production adapter is absent, and the documented simplified mapping loses required semantics.
5. **Outputs suitable for future revision? As a design starting point, yes; for reliable automatic integration, no.** Grounding and review-status enforcement must be corrected.
6. **What remains?** The seven prioritized items above, with successful supported-runtime/schema tests and independent integration evidence. No Drafter or revision implementation is required to close these Critic defects.
7. **Accept as completed Critic deliverable? No.** It can be acknowledged as a working prototype, but completion and integration acceptance should wait for the mandatory corrections and validation.
