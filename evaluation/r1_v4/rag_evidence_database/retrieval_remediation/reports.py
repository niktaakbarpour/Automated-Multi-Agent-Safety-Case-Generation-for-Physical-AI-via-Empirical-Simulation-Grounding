"""Generate transparent reports from frozen cases and saved results, including failures."""
import json,collections,statistics,subprocess
from pathlib import Path
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def read(name):return json.loads((WORK/name).read_text())
def put(name,text):(HERE/name).write_text(text.strip()+'\n')
def table(metrics,common=False):
 lines=['| Mode | N | P@1 | R@5 | R@20 | MRR | Complete multi-source |','|---|---:|---:|---:|---:|---:|---:|']
 for mode in MODES:
  r=metrics[mode]['common_channel_only'] if common else metrics[mode]
  lines.append('| '+mode+' | '+str(r['eligible'])+' | '+' | '.join(f'{r[k]:.3f}' if r[k] is not None else '—' for k in ('precision_at_1','recall_at_5','recall_at_20','MRR'))+f" | {r['multisource_complete_count']}/{r['multisource']} |")
 return '\n'.join(lines)
def run():
 m=read('holdout_guard_v2_METRICS.json');dev=read('development_guard_METRICS.json');a=read('FINAL_ASSESSMENT.json');b=read('BUILD.json');repro=read('REPRODUCIBILITY_RESULTS.json');rest=read('RESTORATION_RESULTS.json');bench=read('BENCHMARK.json');base=read('FINAL_BASELINE_VERIFICATION.json');freeze=json.loads((HERE/'HOLDOUT_FREEZE.json').read_text());q=[json.loads(l) for l in (HERE/'FROZEN_HOLDOUT_DATASET.jsonl').read_text().splitlines()];cases=[json.loads(p.read_text()) for p in sorted((WORK/'holdout_guard_v2').glob('*.json'))];bundle=[r for r in cases if r['mode']=='bundle'];critical=[r for r in bundle if r['metrics']['critical_abstention']];challenges=[json.loads(p.read_text()) for p in (WORK/'challenges_guard').glob('*.json')];assert len(challenges)==24 and all(r['metrics']['correct_abstention'] for r in challenges)
 summaries=[]
 for r in cases:
  p=WORK/'holdout_guard_v2'/(r['case_id']+'-'+r['mode']+'.json');summaries.append({k:r[k] for k in ('case_id','category','mode','query','status','returned_families','metrics','canonical_digest')}|dict(full_case_path=str(p),full_case_sha256=sha(p),record_ids=[i['id'] for i in r['items']]))
 (HERE/'HOLDOUT_RETRIEVAL_RESULTS.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in summaries))
 put('README.md',f'''# Phase 5K retrieval remediation

**Implementation complete; recommendation B — FOCUSED CORRECTION STILL REQUIRED.** Aggregate gates pass, but three temporal questions omit a requested joint family while reporting a complete interpreted plan. The general natural-language completeness contract must not be frozen yet. No downstream implementation is authorized.

The final assurance-guard-1 assessment has 216 question-scope instances on 24 fresh executions / {freeze['variants']} variants, nine categories, 72 authored templates. P@1={m['bundle']['precision_at_1']:.3f}; R@20={m['bundle']['recall_at_20']:.3f} on 136 eligible cases. Multi-source completeness=24/24; required family coverage=84/84; critical abstentions=80/80. Source-value/scope/unsupported-assurance errors observed=0. See REMAINING_LIMITATIONS.md for the three false-complete plans.

The first frozen assessment is preserved in evaluation_v1/ and external work outputs. A metadata-only assurance defect invalidated V1 as a release candidate. A narrow fail-closed guard, four tests and a second freeze preceded V2. V2 uses new scopes but the same question-template bank; it is not an untouched linguistic holdout. No ranking or vocabulary changes followed either holdout.

Database: `{DATABASE}` (unchanged SHA-256 `{DATABASE_SHA}`). Additive catalogue: `{WORK/'catalogue.sqlite'}` ({b['bytes']:,} bytes; `{b['sha256']}`). Reports and code: this directory. Complete machine results are referenced and hashed in ARTIFACT_MANIFEST.json; case-level summaries are in HOLDOUT_RETRIEVAL_RESULTS.jsonl. No copied corpus/database is in Git.

Read BASELINE_VERIFICATION.md, FAILURE_TAXONOMY.md, RETRIEVAL_DESIGN.md, EVIDENCE_BUNDLE_CONTRACT.md, ABLATION_RESULTS.md, MULTISOURCE_COMPLETENESS.md, ABSTENTION_AND_INTEGRITY.md and REPRODUCIBILITY.md. Frozen questions/criteria/configuration are checked before assessment. No new executions, channels, checker decisions, empirical admission or safety agents were introduced; nothing is pushed or merged.''')
 put('BASELINE_VERIFICATION.md',f'''# Baseline and preservation

Baseline commit `{BASE_COMMIT}` on feat/rag-evidence-database-readiness-evaluation was independently inspected before edits. Database hash `{DATABASE_SHA}`; 1,411,190,784 bytes. Read-only counts: 432 executions, 104 variants, 80,786 original evidence rows, 2,592 channel references and 58,075 saved-frame clock labels.

The Phase 5J manifest trust root is `375989a36a5c2390987e88a5228701682d51e5127b5de2b275cac2fb7bf16b25`. Its 2,220 declared evaluation artifacts and Phase 5I parent release were verified as bytes before design; final outputs were not parsed for tuning. The baseline and final checks are stored as BASELINE_VERIFICATION.json and FINAL_BASELINE_VERIFICATION.json under `{WORK}`. The original database is unchanged, which preserves every row and association, not merely counts. Old source files/releases were not rewritten.

Inherited integrity verification covers frozen V3/V4 artifacts, both seals, human archives and scoring safeguards. All 718 inherited tests passed; seven Phase 5J metric tests and 39 new contract/integrity tests passed, total 764 with zero failures or skips. Eligible development payloads only were read. Reserved and excluded scope controls remain in the inherited suite; no reserved/preflight recordings or 1,470 candidates were opened or indexed.''')
 put('FAILURE_TAXONOMY.md','''# Failure taxonomy and independence

Design used only the original 36 Phase 5J development questions/results plus 72 new source-grounded development instances. Original development diagnostics were 108 case-mode records: 45 successes, 39 correct contract restrictions, 10 incorrect top families, eight lexical mismatch/unindexed-family cases, three known-invalid completeness references, two typed-property/intent cases and one missing decomposition/unsupported obligation. Exact IDs/queries are in DEVELOPMENT_DIAGNOSIS.json. These are mechanical diagnostic categories, not independent human judgments.

| Failure | Mechanism | Remedy or boundary |
|---|---|---|
| Incorrect semantic ranking | Similar descriptions of six arrays do not identify an exact physical field | Deterministic field proposal; unchanged semantic baseline retained |
| Lexical mismatch/paraphrase | Source selectors differ from finger aperture, joint speed and motor effort terminology | Separate normalized schema vocabulary; never alter source text |
| Object/fixture terminology | Ambiguous category names and variant-specific identities | Exact recorded names or uniquely supported categories; abstain otherwise |
| Temporal phrases | Typed API expects resolved scope; matching indices are not synchronization | Explicit saved-index/action plan, verified labels, no interpolation |
| Missing multi-source families | One relevant record does not fulfill all obligations | Fetch/check every family; separate temporal coverage |
| Relevant but insufficient | Raw arrays cannot establish Cartesian/contact/support/synchrony claims | Unsupported/partial with limitations; no sufficiency classifier |
| Correct source/scope restriction | Invalid variants, missing sources, unavailable assurance | Expected fail-closed behavior, not ranking defects |
| Invalid completeness reference | C7-06 development; C7-20 final | Preserve historical labels/outputs; document without score repair |
| Residual intent omission | KH2-C2-02/10/18 miss standalone joint configuration, leaving recorded_time | Blocking issue 001; no post-holdout vocabulary patch |

Stage A's complete-output inspection was subordinated to Stage B's mandatory independence rule: final outputs were quarantined during design. All 486 final case-mode diagnostics were inspected only after implementation freeze; HISTORICAL_FAILURE_TAXONOMY.json records cases, missing facets and hypotheses. They did not select rules or thresholds. Historical cases were already exposed in Phase 5J and are never a new holdout. Taxonomy counts alone do not establish causality.''')
 put('RETRIEVAL_DESIGN.md','''# Retrieval design

`planner.py` makes bounded deterministic schema-guided proposals from original query and typed context. It recognizes finger/gripper joint displacement and velocity, arm configuration/rates, native actuator output, contact-entry count and existing metadata/reference families. Clause-level interpretation keeps finger position and arm velocity distinct. Original text is retained. No LLM, training, answer generation or source-text instruction execution is involved.

The 2.57 MB catalogue contains 432 execution/variant/object/source references and hashes; it adds no measurements or arrays. `build.py` checks prior manifest identities and resumes only matching input/row digests. A descriptor-verified SQLite snapshot and identity-change checks protect the catalogue. Database/source proofs remain pinned. Metadata facets expose existing policy/inference/time/geometry/camera/contact references; action arrays remain references, not new measurement channels.

Scope, variant, object, temporal and assurance constraints precede ranking. Unknown scopes never open payloads. Object categories resolve only when uniquely supported by original scene/native mappings. Main-table identity reuses the existing 147-execution/98-variant symbolic audit, never support or pose.

Every proposed family is fetched separately. Missing samples, unsupported properties and conditional interpretations remain explicit. Saved snapshots around action k use the established k+10/k+11 association; no simultaneity is inferred. Decimal simulator labels resolve to recorded labels within a binary64 summation bound: gamma_n=n*eps/(1-n*eps), tolerance=(2*gamma_n+4*eps)*max(1,abs(query endpoints)), n=ceil(maximum recorded time/verified native timestep)+1. XML explicit timestep and the hashed Phase 5H compiled-model map must agree; the map supplies the verified default when XML omits it. This bounds addition roundoff under the recorded-step model, not physical timing uncertainty. Absent/multiple point matches abstain; no shifting/interpolation. Initial failed diagnostics are retained.

Ablations test field matching alone, fixed RRF k=60 over lexical/schema-label cosine candidates, and full decomposition. Hybrid fusion did not improve development results and is not the default. Constraints cannot be overridden by ranking.

Assurance-guard-1 rejects typed measurement requirements without a measurement family. This security correction followed V1 and preceded a new freeze/fresh-scope assessment. No exposed vocabulary error was fixed. Standalone joint-configuration intent remains a blocker; completeness is experimental outside explicit reviewed plans.''')
 put('EVIDENCE_BUNDLE_CONTRACT.md','''# Evidence bundle contract

Machine schema: EVIDENCE_BUNDLE.schema.json. Entry point: `Retriever(index_path, expected_index_sha256).retrieve(BundleRequest(...))`. Database and catalogue are separately pinned. Strict is default; verified_session explicitly reuses cryptographically verified identity only while descriptor/file signatures remain stable.

Output preserves original query, resolved execution/task/variant, interpretation, requested families, per-family items/coverage, original evidence IDs or explicitly derived source-reference IDs, artifact paths/hashes/selectors, units/semantic properties, integrity/assurance, assumptions, missing evidence and uncertainties. Source references are not new measurement records. Direct values remain direct; symbolic identity/physical annotations remain derived/conditional as inherited.

Global states: COMPLETE WITHIN VERIFIED CONTRACT, PARTIAL, UNAVAILABLE, UNSUPPORTED, AMBIGUOUS, INVALID SCOPE. Completeness concerns requested retrieval obligations, never a safety claim. Every required family must be AVAILABLE and every requested saved sample present. Action/inference metadata have separate action coverage. Camera/contact records remain references; no calibrated images, physical event or support inference. Known issue 001 can omit an obligation before this check: unreviewed natural-language COMPLETE is not yet a dependable query-completeness guarantee.

Typed frame/clock intervals cannot conflict; unknown/contradictory object or scope context abstains. Channels retain inherited raw/source semantics, revolute/prismatic units under the recorded metric convention, conditional actuator SI interpretation and conditional cache offset. World transforms, sensor synchronization, historical binary attestation and new action values are not enabled. Metadata-only typed measurement requests fail closed in guard-1.

Source text/BDDL/instruction-like bytes are data. safety_claim_sufficiency=NOT_EVALUATED, safety_claim_verified=false and empirical_admission_enabled=false. There is no production factual/safety judge. Values permit checking narrow facts under contracts; no R1 judgment is produced.''')
 put('ABLATION_RESULTS.md',f'''# Development and frozen assessments

Development-only results (72 new instances, plus separate original-36 diagnostics):

{table(dev)}

The full planner/family fetching completed 8/8 development multi-source cases; field_single and hybrid_single completed 0/8. These share the proposal layer and isolate independent family execution. Hybrid is a bounded one-family ranking experiment, not a full hybrid baseline; it did not improve development accuracy. No learned thresholds or post-holdout vocabulary changes.

V2 on the common channel-only subset, supported by the unchanged Phase 5I primary endpoint:

{table(m,True)}

All eligible V2 obligations, including metadata/geometry/reference families:

{table(m)}

The broad baseline rows deliberately call the existing six-channel endpoint without adding routing/decomposition; they cannot answer every new family. They are endpoint-coverage diagnostics, not evidence that the complete historical system has these aggregate accuracies. Use common-channel rows for a fair field-retrieval comparison. Existing exact baseline receives oracle channel IDs for single-family requests and oracle frame windows; improved retrieval parses natural language. Original full legacy/physical interfaces are separately replayed in HISTORICAL_5J_COMPARISON.md.

Metrics rank distinct required families, not historical record IDs or generated answers. P@1 can be 1.0 while another requested family is omitted. C2-2 demonstrates that limitation. Every case remains in its predefined denominator.''')
 lines=['| Category | Eligible | P@1 | R@20 | Required-set failures |','|---|---:|---:|---:|---:|']
 for cat,r in m['bundle']['categories'].items():lines.append(f"| {cat} | {r['eligible']} | {r['precision_at_1'] if r['precision_at_1'] is not None else 'N/A'} | {r['recall_at_20'] if r['recall_at_20'] is not None else 'N/A'} | {sum(x['case_id'].startswith('KH2-'+cat+'-') for x in a['missing_family_cases'])} |")
 put('MULTISOURCE_COMPLETENESS.md',f'''# Multi-source completeness and remaining boundary

C4: 24/24 complete required sets; 84/84 required-family obligations retrieved. Eight authored combinations repeat across three disjoint scopes: two robot fields; gripper state/action/time; joint/inference/geometry; actuator/count/source; velocity/camera/time; joint/contact/source; all six arrays; action/inference/execution/source metadata. Per-source temporal coverage stays separate. No shared physical instant is inferred.

Descriptive Wilson 95% interval for 24/24 is {m['bundle']['multisource_wilson95']}; authored formulations are not a random linguistic population. Only eight distinct C4 templates were tested, not 24 independent linguistic cases.

Per-category final bundle metrics:

{chr(10).join(lines)}

Three C2 instances of one formulation omit raw.robot0_joint_pos while returning correct recorded_time and marking the reduced plan complete. This is a genuine query-to-plan completeness defect, not a missing source or corrected reference. Exact cases are in FINAL_ASSESSMENT.json and issue 001. The external audit identifies it; the production bundle cannot currently detect it. No safety-sufficiency classifier was added. Aggregate gates pass, but the requested-obligation contract does not yet justify freezing the general interface.''')
 put('ABSTENTION_AND_INTEGRITY.md',f'''# Abstention, integrity and compatibility

V2: 80/80 critical requests abstained, zero incorrect abstentions on 136 supported-family cases, zero returned source-value/scope errors, zero unsupported assurance escalation in tested contracts. The 80 include nine metadata-only typed negatives for the guard. The separate 24 frozen challenges also abstained: wrong unit/frame/property/assurance/task/time, conflicting anchors and an instruction-bearing tampered HDF5. Abstention means no items, not a decision by an external rubric. Raw evidence under a clearly unsupported extra interpretation is partial evidence, not unsupported-claim acceptance.

All returned arrays, including irrelevant baseline arrays, were independently decoded from original sources. Final bundle: {a['unique_returned_source_samples']} unique source selectors, {a['returned_numeric_components']} scalar components, exact maximum numeric error 0, {a['unit_comparisons']} unit comparisons and zero unit errors. No interpolation/offset change. Machine references were independently built from HDF5/JSON/XML, not copied retriever outputs. They are not human evaluation.

Strict descriptor-bound hashing/no-follow checks cover source and primary proof reads, native XML/map/assets and metadata. Catalogue mutation is detected despite an in-memory snapshot. Cached verification invalidates on identity changes. Tests cover changed bytes with restored mtime, atomic replacement, deletion, same-hash symlinks/parent redirection, matching recovery, stale identities and unsafe/mismatched restoration maps. Actual recordings were never modified.

The historical legacy geometry verifier accepts same-content symlinks; the newer reader rejects them. Old releases remain byte-identical. `compat.py` supplies a separate strict legacy record-reference route: original IDs preserved, descriptor-bound XML/map/assets/record/dependency checks. It explicitly declines comparative/time-domain modes outside that compatibility contract; it is not a silent replacement for every legacy semantic/comparative operation. The inherited legacy route remains legacy and must not be advertised as enforcing the new no-follow policy.

Trusted restoration is explicit canonical path+hash+execution+variant mapping. It never falls back to original paths. Restored contents still pass no-follow/hashes; no untrusted symlink redirection is accepted. The bounded test restored {rest['mapped_artifacts']} mappings / {rest['unique_contents']} unique contents for one development execution/variant, {rest['mapped_bytes']:,} mapped bytes, and passed three retrievals. The original separately pinned database and catalogue were prerequisites, not duplicated or claimed independently restored. Historical binary attestation remains unavailable.''')
 hist=json.loads((WORK/'HISTORICAL_5J_COMPARISON_RESULTS.json').read_text());original=[json.loads(p.read_text()) for p in (WORK/'historical_original_target/original_final_replay').glob('*.json')];ht=['| Original mode | N | P@1 | R@5 | R@20 | MRR |','|---|---:|---:|---:|---:|---:|']
 for mode in ('exact','lexical','semantic'):
  rr=[r['assessment'] for r in original if r['mode']==mode and r['assessment']['relevance_eligible']];ht.append('| '+mode+' | '+str(len(rr))+' | '+' | '.join(f'{statistics.mean(x[k] for x in rr):.3f}' for k in ('precision_at_1','recall_at_5','recall_at_20','MRR'))+' |')
 put('HISTORICAL_5J_COMPARISON.md',f'''# Exposed historical comparison, not generalization evidence

After both implementation freezes, the unchanged original full Phase 5J target was replayed once: 162 questions / 486 mode instances, using read-only old database/index/contracts with all outputs/scratch redirected to Phase 5K. Frozen historical artifacts/labels were not changed. Original record-ID relevance:

{chr(10).join(ht)}

The original reported exact/semantic/lexical completeness was 10/18, 10/18, 8/18. C7-20's invalid completeness annotation remains invalid; no historical output/label was rewritten. The source-target record ranking metrics remain distinct from K family-obligation metrics.

One corrected-bundle historical comparison covers {hist['questions']} questions and saves case outcomes, unmapped old obligations and the invalid annotation flag in HISTORICAL_5J_COMPARISON_RESULTS.json. Mapped-family success is not a replacement score for unmapped obligations; no apples-to-oranges claim of historical completeness improvement is made. All 486 old final diagnostics are in HISTORICAL_FAILURE_TAXONOMY.json. The exposed cases did not select retrieval rules, thresholds, prompts or rankings. New scope assessments, not this comparison, support the reported remediation results.''')
 put('REGRESSION_RESULTS.md',f'''# Regression and preservation results

718 inherited tests, seven Phase 5J metric tests, and 39 new tests: **764 passed, zero failures/skips**. Test logs and inherited machine reports are manifested. Separately: 216 bundle schema validations, 24 critical challenges, 141 source-reference comparison operations and 90 source artifact hashes during reference construction, 1,296 mode instances per final assessment pass, and the external factual/unit audit. These are different denominators, not additional independent linguistic or human tests.

Fresh catalogue rebuild logical digest `{b['logical_digest']}` matches the original; full resume recognizes 432/432 jobs, partial resume recognizes 37 and builds 395. Source database stays `{DATABASE_SHA}` with 432/104/80,786/2,592/58,075 counts and every byte/association unchanged. V3/V4, human archives, both seals and scoring protections passed final integrity verification.

Three fresh/full/partial V2 assessment passes match exact canonical outputs; 3,888 saved case files were independently rehashed/rebound. Full evaluation resume reused 1,296 instances; partial reused 37. A forged saved-output negative control was detected. Saved-output verification is required before trusting a resumed evaluation; resume alone is not cryptographic release validation.

Initial failed catalogue construction, prototype timestamp diagnostics, an audit selector harness failure, and a mismatched test expectation are retained. V1's metadata-assurance defect is archived with its original results, fixed by guard-1 and assessed under a new freeze. A reporting bug initially grouped correct unsupported-table cases as retrieval misses; the reporting-only correction preserved all labels/results and now separates these from the three actual C2 omissions. All failures are explained. The remaining three omissions are product findings, not hidden test-suite failures; recommendation B reflects them.''')
 put('REPRODUCIBILITY.md',f'''# Reproduction and release verification

Run on Hestia, repository `/disk/1/data/niktakbr/trustworthy-phase16`, Python `/usr/bin/python3 -S`. Dependencies are recorded in ENVIRONMENT_AND_RESOURCES.json and prior pinned manifests. Set PYTHONDONTWRITEBYTECODE=1; PYTHONPATH includes repository plus `/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages` and installed `/usr/local/lib/python3.12/site-packages`, `/usr/lib64/python3.12/site-packages`, `/usr/lib/python3.12/site-packages`. Use K-owned HF_HOME/XDG_CACHE_HOME. The existing local encoder is offline/pinned; no installation/training.

All module names below use prefix `evaluation.r1_v4.rag_evidence_database.retrieval_remediation.`:

```text
python3 -S -m <prefix>verify_release
python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/retrieval_remediation/tests
python3 -S -m <prefix>run_eval --dataset evaluation/r1_v4/rag_evidence_database/retrieval_remediation/FROZEN_HOLDOUT_DATASET.jsonl --run <new-label>
python3 -S -m <prefix>verify_outputs
python3 -S -m <prefix>final_assessment
```

`verify_outputs` checks the three documented run names; another operator can use its check_record routine and frozen binding formula with new paths. Verify ARTIFACT_MANIFEST.json against committed Git bytes before trusting results/cached progress. Each case binds request/reference, mode, database, catalogue and code. Dataset SHA `{freeze['dataset_sha256']}`; implementation SHA `{freeze['implementation_sha256']}`; acceptance SHA `{freeze['acceptance_sha256']}`. Never regenerate frozen inputs during replay.

For a fresh catalogue call `build.populate(new_path)` and compare logical contents with BUILD.json. Resume validates every job input/row digest. `reproducibility.py` documents fresh/full/partial runs/catalogues; use new paths for another repetition because assertions distinguish fresh/resumed states. Automated decoding/replay is not independent human replication. Three final passes share canonical digest `{repro['independent_replay']['canonical_digest']}`. Only latency and fault-scratch path spelling are removed; IDs/values/scopes/statuses/uncertainties must match.

Restoration uses separately pinned database/catalogue plus RESTORATION_RESULTS.json's manifest. A trusted caller pins the manifest hash; canonical path/hash/execution/variant entries map to contained relative paths. No fallback/symlinks/traversal. Full-corpus or historical binary reproducibility is not claimed.

Preflight projected ≤2 GiB additive disk and ≤4 GiB/process memory with about 1.615 TB free. No corpus/database duplication or destructive cleanup. ENVIRONMENT_AND_RESOURCES.json and BENCHMARK.json capture resources/latency. Strict median {bench['summary']['strict']['median']:.3f}s vs verified-session {bench['summary']['verified_session']['median']:.3f}s on 16 calls each, shared Hestia load, descriptive only. Default strict requirements remain.

Chronology: development → V1 implementation/criteria freeze → source-grounded V1 freeze/evaluation/replay → typed diagnostic → archive V1 → narrow guard/tests → V2 implementation/criteria freeze → fresh-scope question freeze → evaluation/challenges/replay. Template overlap disclosed; no ranking/vocabulary tuning after V1. verify_release.py represents baseline checks. Original-36 selection filters development lines before parsing. Historical final cases are read only after freeze.''')
 put('REMAINING_LIMITATIONS.md',f'''# Limitations and decision

**B. FOCUSED CORRECTION STILL REQUIRED.** Numerical gates pass unchanged, with no post-result exclusions. General readiness still fails the requested-obligation contract: KH2-C2-02/10/18 omit joint configuration while reporting a complete reduced plan. Three instances, one formulation. Time labels/values are correct. Issue 001 proposes a correction, not an applied holdout-specific patch.

Do not freeze unrestricted downstream retrieval or automatically proceed to Phase 5L. The next database-only correction should validate intent/obligation coverage, abstain on unresolved measurement-bearing clauses, and use fresh independently authored assessment questions. Explicit reviewed plans and existing strict source-value APIs retain tested utility; downstream agents are not authorized.

V1 was ineligible because metadata-only typed requirements were ignored. Guard-1 fixes that scoped defect; V1 is preserved, not mixed into V2. V2 uses 24 new executions/18 variants excluding 54 prior scopes, but repeats 72 templates. This is not independent linguistic/human validation. Four suites/length strata are covered; all possible queries and 104 variants are not exhaustively reevaluated. Wilson/bootstrap intervals are descriptive for clustered authored data.

P@1 is any relevant first family, not a complete answer. C4 has eight templates despite 24 instances. Broad baseline rows use a six-channel endpoint; they are not the complete legacy system. J record-ID and K family metrics differ. J final labels did not guide tuning; historical exposure is disclosed.

Physical calibration, world transforms, sensor clocks, historical binaries, conditional cache timing and actuator SI assumptions remain unchanged. Gripper values are finger joints; native actuator output is not contact force; contact-entry count is not contact/support judgment; geometry identity is not support. Contact/camera references need not support force/exposure/calibrated interpretations. No new arrays/channels were indexed. Restoration is bounded with separately pinned prerequisites.

The original legacy geometry route still accepts same-content symlinks; use the scoped strict compatibility route where applicable. Comparative/legacy semantic combinations outside that route were not redesigned. No R1/checker/admission/GSN/agents or frozen label changes. Nothing pushed or merged.''')
 put('READINESS_DECISION.md',f'''# Readiness decision

{a['recommendation']}

Aggregate gates: {json.dumps(a['aggregate_gates'],sort_keys=True)}. Passing gates are reported unchanged. B follows the separate pre-existing bundle requirement that completeness reflect requested obligations. Three C2 instances violate it; no new numerical threshold or exclusion was invented.

| Capability | Status | Basis |
|---|---|---|
| Exact source values | READY WITH CONDITIONS | Source/scope contracts; unchanged historical replay and numeric checks |
| Natural-language relevance | READY WITH CONDITIONS | P@1 1.000 / R@20 0.989 on 136 authored scope instances |
| C4 multi-source sets | READY WITH CONDITIONS | 24/24 over eight templates; no universal coverage claim |
| General query completeness | NOT READY | Three reduced plans falsely complete |
| Scope/source integrity | READY WITH CONDITIONS | Zero observed errors; strict checks/negative controls |
| Assurance | READY WITH CONDITIONS | Guard-1 metadata negatives; inherited uncertainty/provenance |
| Physical interpretation | READY WITH CONDITIONS | Existing supported/conditional contracts only |
| Replay | READY WITH CONDITIONS | Automated exact replay, no independent human replication |

Implementation/evaluation complete; readiness success not claimed. Do not automatically proceed to Phase 5L.''')
 print('REPORTS GENERATED',flush=True)
if __name__=='__main__':run()
