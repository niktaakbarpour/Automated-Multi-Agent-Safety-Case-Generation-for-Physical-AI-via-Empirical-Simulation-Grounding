"""Reports from frozen case outputs, including every failed acceptance gate."""
import json,collections,statistics
from pathlib import Path
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def read(name):return json.loads((WORK/name).read_text())
def put(name,text):(HERE/name).write_text(text.strip()+'\n')
def run():
 m=read('final_v2_METRICS.json');v=m['checked'];old=m['legacy_k'];a=read('FINAL_AUDIT.json');cfg=json.loads((HERE/'FROZEN_CONFIGURATION.json').read_text());replay=read('REPLAY_RESULTS.json');reg=read('FINAL_REGRESSIONS.json');pres=read('FINAL_PRESERVATION.json');historical=read('HISTORICAL_K_REGRESSION.json');assert reg['total_tests']==813 and reg['passed'];cases=[json.loads(p.read_text()) for p in sorted((WORK/'final_v2').glob('*.json'))];qs={q['id']:q for q in map(json.loads,(HERE/'FROZEN_EVALUATION_DATASET.jsonl').read_text().splitlines())}
 summary=[]
 for r in cases:
  p=WORK/'final_v2'/(r['case_id']+'-'+r['mode']+'.json');summary.append(dict(case_id=r['case_id'],mode=r['mode'],query=r['query'],status=r['output']['completeness_status'],metrics=r['metrics'],canonical_digest=r['canonical_digest'],full_case_path=str(p),full_case_sha256=sha(p)))
 (HERE/'CASE_RESULTS.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in summary))
 put('README.md',f'''# Phase 5K.1 obligation preservation

**Implementation complete. B — FOCUSED CORRECTION STILL REQUIRED.** Version {VERSION} prevents observed false completeness, but does not meet every frozen obligation-recognition/readiness gate. No downstream phase is started.

Final corrected assessment: 144 source-scope instances, 72 newly authored formulations (each on two scopes), 24 fresh executions / {cfg['variants']} variants, six categories. These formulations and execution scopes were not reused from the failed V1 assessment. Measurements and conjunctions are retained in all evaluated cases; strict false-complete bundles=0/144; critical abstentions=30/30. Six canonical reference obligations remain missing: four temporal selectors and two reverse-worded source-hash requirements. Extra conservative unresolved markers reduce exact-set agreement to {v['exact_obligation_set']:.3f}. See LIMITATIONS.md.

Mandatory recall: {a['preserved_obligations']}/{a['reference_obligations']}={a['micro_recall']:.4f} micro; {v['obligation_recall']:.4f} macro. P@1/R@20={v['precision_at_1']:.3f}/{v['recall_at_20']:.3f} on 114 relevance-eligible cases. Inspection-only evidence remains noncomplete and cannot establish query fulfillment. No observed source-value, execution/variant or assurance errors. All 813 applicable tests passed, including the original 764; full/fresh/partial replay agrees.

The failed first assessment and frozen implementation are preserved in assessment_v1/ and external work outputs. A separately frozen correction made selector proof dependencies explicit, enforced actual selector fulfillment, and allowed clearly labelled noncomplete raw inspection. No ranking weights, thresholds, historical labels or outputs were changed.

Database `{DATABASE}` and catalogue `{CATALOGUE}` are unchanged. Database SHA-256 `{DATABASE_SHA}`. This package adds code/query metadata only: 432 executions, 104 variants, 80,786 evidence rows, 2,592 channel references preserved. Reports, frozen questions/references/configuration, case summaries and exact artifact hashes are in this directory; full machine outputs are under `{WORK}`. No push/merge, corpus/channel expansion, R1 changes or downstream agents.''')
 put('BASELINE_VERIFICATION.md',f'''# Baseline verification and resources

Verified clean branch feat/rag-evidence-retrieval-remediation at `{BASE_COMMIT}` before changes. New branch: feat/rag-evidence-query-obligation-verification. Phase 5K manifest `{BASE_MANIFEST_SHA}` verified 10,813 declared artifacts using descriptor-bound no-follow reads, including database/model trust roots. Phase 5J/5I nested manifests and frozen safeguards were independently reverified; machine results: FINAL_PRESERVATION.json. All 764 inherited tests passed before implementation and again after it.

Database `{DATABASE_SHA}`; catalogue `{CATALOGUE_SHA}`. Read-only counts: 432 executions /104 variants /80,786 evidence /2,592 channel references /58,075 frame labels. Whole-database identity preserves rows and source associations, not merely counts. Earlier releases, sources, variant geometry, human archives, V3/V4, both seals and scoring files were preserved.

All computation used Hestia. Before source scans/builds the budget was ≤1 GiB additional disk and ≤4 GiB memory per process, with about 1.615 TB free. No corpus/database duplication, Sea NFS, Alliance computation or destructive cleanup. Fault tests use bounded scratch copies; original source bytes are never modified. Reserved/excluded IDs are used only as registry metadata in negative controls, with no payload access; no candidates are indexed. Exact preflight/resource records are in RESOURCE_PREFLIGHT.json and FINAL_PRESERVATION.json.''')
 put('ROOT_CAUSE_ANALYSIS.md','''# Original failure path

Exposed K cases KH2-C2-02/10/18 ask for joint configuration at a simulator label. The planner's position vocabulary contains configuration, but its arm-entity expression recognizes joint angle/position/velocity forms and omits joint configuration. The temporal expression separately recognizes simulator label. The resulting plan contains only recorded_time. Retrieval correctly fetches that family. Completeness counts AVAILABLE groups against that same reduced plan and returns COMPLETE.

The loss occurs during measurement/entity recognition, before evidence retrieval. Time does not explicitly override the measurement; it survives independently after the measurement drops. The schema permits a family list without the original obligations, and the checker trusts that list. Correct time values therefore mask a lost measurement request. This is not primarily ranking, missing raw data, variant attribution or physical semantics.

The exposed cases are regression tests only. Version 1 added structured original obligations, a separate token-relation validator, and obligation fulfillment. Its fresh 144-formulation assessment retained the failed implementation/results. One strict completeness flag arose because time proof was represented as a selector dependency but not as the separately required source-family node; six quantified measurement obligations were also unresolved. Excess residual-word rejection degraded retrieval.

Corrected version 2.1 explicitly expands selector proof families into source-family obligations, bounds registry quantifier grammar, compares actual selected scope to the original selector, and returns identified verified data only as UNVERIFIED PLAN inspection when residual wording remains unresolved. Unsupported comparisons/interpretations cannot become complete. No rules/thresholds were tuned against the corrected final assessment. The remaining failures are reported unchanged.''')
 put('OBLIGATION_SCHEMA.md','''# Obligation schema

Machine schema: OBLIGATION.schema.json. query_obligations contains stable IDs, original query spans/text or typed request paths, type/target, required families, temporal obligation references, execution/task/variant/object scope, mandatory flag, resolution status, uncertainty, verification requirements and contract references. IDs anchor identity (type/target/basis/scope); frozen artifact hashes protect the complete serialized object. IDs alone are not content attestations.

Types: measurement, temporal/temporal_uncertainty, scope, entity, component, source_family, assurance, interpretation, comparison, factual_support, availability and unresolved request content. A timestamp is a selector/proof requirement, never a substitute measurement. Conjoined entities/properties create distinct obligations. Duplicate canonical requirements merge, retaining traceable basis. Multiple instants without supported per-clause binding stay ambiguous. Components reference existing native array order; full raw arrays remain unchanged.

Resolution states: RESOLVED, CONDITIONAL, AMBIGUOUS, UNRESOLVED, UNSUPPORTED. Unsupported/unparsed content is retained. Comparisons/factual-support judgments are not computed: operands may be partial evidence while the comparison remains unfulfilled. Unknown clock/window/entity semantics cannot become completeness.

CONTRACT_REGISTRY.json resolves inherited labels to exact files/hashes. Raw IDs, derived interpretation IDs and source hashes retain original lineage. Registry metadata is retrospective release identity, never historical producer attestation. No observations are rewritten, re-normalized or newly indexed.''')
 put('INDEPENDENT_VALIDATOR_DESIGN.md','''# Independent validator

The planner uses a source-grounded entity/property vocabulary and clause composition. The validator does not import that planner, vocabulary file or old K parser. It independently tokenizes original requests, reads measurement heads and nearest entity/property relations, checks bounded quantifiers/numeric selectors, and derives its own expected requirements from shared canonical contracts. It checks typed scope/assurance, families, selector values, attachments and registry object identities. Reducing both model and plan fails this path.

Residual content outside recognized semantic spans is retained unresolved. Metadata/property spans are bounded so actuator output or clock proof cannot swallow an unknown conjunct. Attributed source quotations are independently excluded by each parser; user-quoted field requests remain requests. Unsupported aliases do not acquire physical meanings.

The second gate compares actual selected indices/clock proof with the original selector and checks required family/sample coverage/source identity. It catches inconsistent backend selection even when the linguistic parsers share a limitation. A relevant record alone is insufficient.

Independence is methodological, not statistical/human: two deterministic implementations share verified semantics, finite vocabulary and the same author/environment. Correlated omissions remain possible. Both assessments expose this boundary; remaining time/source-hash forms are not declared solved. Preservation uncertainty requires a noncomplete status. No universal language-completeness theorem is claimed.''')
 put('COMPLETENESS_CONTRACT.md','''# Two-check completeness and migration

Use obligation_preservation.retrieve.Retriever with the existing BundleRequest. Historical K API remains unchanged; callers must migrate explicitly. Database/catalogue stay read-only/pinned, with source/variant/assurance constraints enforced.

COMPLETE requires (1) independent preservation of every mandatory original obligation and (2) verified fulfillment of every mandatory obligation. Missing families, changed selector attachments or unknown content cannot be excused by a reduced plan. Each source retains separate temporal coverage; no simultaneity, interpolation or shifting.

Statuses: COMPLETE WITHIN VERIFIED CONTRACT, PARTIAL, AMBIGUOUS, UNAVAILABLE, UNSUPPORTED, INVALID SCOPE, and new UNVERIFIED PLAN. Separate obligation_preservation/evidence_fulfillment results and unsatisfied IDs are exposed. No status means safety sufficiency.

UNVERIFIED PLAN may carry identified verified raw data only for residual-content uncertainty under verified_source_values. It is labelled inspection_only, assurance_satisfied_for_original_request=false and fulfillment=false. The original request is not accepted as answered. Explicit reduced plans, ambiguous selectors, unsupported physical/strict assurance requests and wrong scopes get no fallback. Consumers must not infer completeness from items. Hard typed scopes/source checks remain mandatory.

PARTIAL may carry comparison operands or explicitly requested raw values with an unsupported transform; the comparison/interpretation stays unsatisfied. No comparison answer, support/contact/safety judgment or escalation is produced. Conditional cache/native/SI distinctions remain inherited. Recorded labels associate samples, not shared physical instants.

Old fields remain; obligations/gates and UNVERIFIED PLAN require compatibility changes. Default verification stays strict; evaluation explicitly uses verified_session with identity invalidation. Empirical admission and safety_claim_verified remain false.''')
 put('DEVELOPMENT_TESTS.md','''# Development and separation

New development: 96 scope instances of 12 forms on eight eligible executions, excluded from both final assessments. Exposed K failures are regressions only. No final cases became an unlabelled development set.

49 corrected-version test methods passed, plus 28 detected mutation trials. Coverage includes configuration/time/action, positions+velocities, arm+gripper configurations, gripper state+actuator output, parentheses, singular/plural registry heads, word order, unsupported world/clock/calibration/comparison requests, missing instants, unknown conjuncts, quotations, components, conditional cache, scope and tampering. Mutations remove model obligations AND plan families, alter scopes/attachments/clock values, and forge actual selected indices. These are finite automated tests, not human evaluation.

Initial diagnostics remain: a baseline extra-test output directory was missing; registry fixture names were corrected to excluded_reserved/excluded_preflight; a genuine coverage bug let request.query cover the entire request. Fixed before final freezing. Failed V1 results are preserved. The correction was separately frozen and assessed on fresh scopes/new wording. A secondary V1 audit explains a missing-default assurance scorer bug; original bad counters and outputs remain intact.''')
 put('OBLIGATION_EVALUATION.md',f'''# Obligation recognition

Corrected assessment: 144 instances /72 authored formulations, two scopes each; 24 new executions /{cfg['variants']} variants. No earlier development/final execution scope was reused. References were authored from original questions and source contracts, then validated with original HDF5/XML/JSON. No target output created labels; no human evaluation is claimed. Both freezes precede final execution. V1 used 144 different formulations and is separately preserved.

| Metric | Result |
|---|---:|
| Mandatory reference obligations retained | {a['preserved_obligations']}/{a['reference_obligations']} |
| Micro recall | {a['micro_recall']:.6f} |
| Macro recall | {v['obligation_recall']:.6f} |
| Micro precision | {a['micro_precision']:.6f} |
| Macro precision | {v['obligation_precision']:.6f} |
| Exact obligation-set match | {int(round(v['exact_obligation_set']*144))}/144 |
| Measurement-family obligation recall | {v['measurement_family_recall']:.3f} |
| Temporal preservation | {int(round(v['temporal_preservation']*144))}/144 |
| Scope/entity preservation | 144/144 |
| Conjunction preservation | 26/26 |

Six canonical obligations are missing: two 'time is T' selector forms, two frame windows expressed with 'and', two reverse-worded 'hash of ... source' requirements. All six stayed noncomplete. Their original spans and uncertainty remain visible, but that is not counted as successful canonical recognition. Extra unresolved-content markers lower precision/exact match. No labels, thresholds or exclusions changed after results. Case-level outcomes are in CASE_RESULTS.jsonl and FINAL_AUDIT.json.

The original frozen V1 scorer incorrectly counted omitted assurance defaults as None. Its 69 checked/107 baseline false-assurance counters remain archived. A separate audit of actual output assurances found zero; the corrected scorer uses the documented default. V1's strict false-complete flag remains 1/144, not retrospectively removed. V2's zero is from a genuinely new assessment.''')
 table=['| Mode | Eligible | P@1 | R@20 | MRR |','|---|---:|---:|---:|---:|']
 for mode,r in [('Unchanged K',old),('Obligation checked',v)]:table.append(f"| {mode} | {r['eligible']} | {r['precision_at_1']:.3f} | {r['recall_at_20']:.3f} | {r['MRR']:.3f} |")
 put('EVIDENCE_COMPLETENESS.md',f'''# Evidence fulfillment and retrieval

Strict false-complete bundles: **0/144**, descriptive Wilson 95% interval {v['false_complete_wilson95']}. This finite authored sample does not bound all natural-language queries. Full-capable requests completed: {a['complete_full_capable']}/{a['full_capable_cases']}. The relevance denominator is 114 and intentionally includes six PARTIAL operands and two permitted UNVERIFIED inspection requests; those must not be called complete. Raw evidence availability is separate from query fulfillment.

{chr(10).join(table)}

Required evidence-family recall: {v['family_recall']:.6f}. Measurement/conjunction obligation retention is 1.0, but {a['inspection_cases']} residual-content requests use noncomplete inspection. There are four relevance-eligible abstentions; exact status matches are {v['status_correct']}/144. All 30 critical no-item requests abstained. Unavailable sources may be masked by earlier plan uncertainty; separate direct tampering tests verify actual integrity rejection. No unsupported claim is accepted merely because raw evidence exists.

Source-value checks decoded {a['unique_returned_source_samples']} unique returned selectors /{a['returned_numeric_components']} scalar components, {a['unit_comparisons']} unit comparisons, zero unit/value errors and exact maximum error 0. No execution/variant/temporal-scope errors observed in the checked mode. The unchanged K control had two temporal-scope diagnostics; these are preserved, not blamed on the correction.

Historical exposed K regression: P@1={historical['precision_at_1']:.6f}, R@20={historical['recall_at_20']:.6f}, 80/80 abstentions, zero source errors. Baseline 1.000/0.988971: P@1 drops 0.022059, exceeding the frozen 0.02 tolerance; recall drop is within tolerance. This is an additional failed readiness gate. No historical question is independent generalization evidence; the old APIs/outputs remain byte-identical.''')
 put('ADVERSARIAL_AND_METAMORPHIC_TESTS.md','''# Adversarial, metamorphic and mutation validation

49 new methods cover clause order, shared subjects/properties, parentheses, singular/plural families, entities, conditional cache, unsupported physical claims, quoted source instructions and quoted field names. Five additional broad development probes stay noncomplete (BROAD_EXAMPLE_RESULTS.json); they are not part of the independent holdout denominator.

All 28 mutation trials were detected: removing BOTH model obligations and plan families, changing executions and removing attachments. Tests also forge clock values/actual selected indices. This tests independence from reduced plans. Word-order permutations preserve measurement sets. Bounded actuator/clock spans cannot hide an unknown conjunct.

Scratch-only missing/modified/replaced/symlinked/instruction-bearing HDF5 tests pass; matching recovery succeeds. Wrong tasks/variants and reserved/excluded registry IDs reject before payload access. No recording is modified. Metadata-only physical assurance rejects; unit/geometry/source safeguards inherit prior suites.

All 30 final strict cases abstained. Noncomplete raw inspection is not strict assurance acceptance. Availability, fulfillment and original-query correctness are separate metrics. Finite shared ontologies/quotation syntax remain limitations; source text never becomes instructions or proof of a physical event.''')
 put('REGRESSION_RESULTS.md',f'''# Regression results

**813 passed; zero skips/unexplained failures:** 718 inherited Phase 5I tests, seven Phase 5J, 39 Phase 5K, 49 new methods. The inherited 764 passed before implementation, and all 813 passed after correction. Commands/logs: FINAL_REGRESSIONS.json and post_implementation/.

Separate denominators: 28 detected mutations; five broad noncomplete probes; 154 V2 source-reference comparisons/90 artifact hashes; 144 cases ×2 modes per pass; 864 files validated over final/fresh/partial replay. Modified cached output is detected. These are not human/independent language cases.

Database/catalogue hashes and 432/104/80,786/2,592/58,075 associations remain unchanged. Parent K/J/I artifacts, previous releases/sources, V3/V4/human archives, seals and scoring safeguards passed verification. No database rebuild/migration was needed; original exact retrieval remains byte-identical and tested.

Acceptance failures are preserved product findings: six canonical obligations missing, excessive extra unresolved markers, historical P@1 tolerance failed. V1 raw results, its strict false-complete flag and bad assurance counters remain archived with the independent audit. No frozen labels/outputs changed.''')
 put('REPRODUCIBILITY.md',f'''# Reproduction

Hestia, repository `{REPO}`, work `{WORK}`. Use /usr/bin/python3 -S, PYTHONDONTWRITEBYTECODE=1, repository plus recorded Python 3.12 site-packages in PYTHONPATH. HF_HOME/XDG_CACHE_HOME use phase5k1-owned caches. No installs/training/model changes. Existing semantic model is pinned by the K manifest. No Alliance computation or Sea NFS.

RESOURCE_PREFLIGHT.json budgeted ≤1 GiB added disk/4 GiB per process before work. FINAL_PRESERVATION.json records used/free space. No destructive cleanup/full-corpus copying. Faults use isolated bounded scratch copies.

Module prefix: evaluation.r1_v4.rag_evidence_database.obligation_preservation.

```text
python3 -S -m <prefix>.validate_references
python3 -S -m <prefix>.evaluate --dataset evaluation/r1_v4/rag_evidence_database/obligation_preservation/FROZEN_EVALUATION_DATASET.jsonl --run <new-label>
python3 -S -c "from evaluation.r1_v4.rag_evidence_database.obligation_preservation.metrics import run; run('final_v2')"
python3 -S -m <prefix>.preservation
python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/obligation_preservation/tests
```

Do not regenerate inputs. Dataset `{cfg['dataset_sha256']}`; implementation `{sha(HERE/'FROZEN_IMPLEMENTATION.json')}`; references `{cfg['references_sha256']}`; criteria `{cfg['criteria_sha256']}`. Git-bound ARTIFACT_MANIFEST.json is the trust root. Cases bind request/reference, mode, database, catalogue and code. Resume validates canonical bytes.

All three passes share `{replay['fresh']['canonical_digest']}`. Full resume 288/288; partial 37 reused/251 completed. All 864 files match after removing only latency/scratch spelling; all values/IDs/obligations/status/uncertainty remain. Modified-output control fails. Automated replay/source decoding is not human replication.

Checkout parent `{BASE_COMMIT}` and verify K manifest `{BASE_MANIFEST_SHA}`. This branch adds an opt-in wrapper; unchanged database/catalogue remain hash-pinned prerequisites. V1 is archived, not replaced. Each assessment was frozen first; V2 uses fresh scopes and 72 new formulations repeated twice. No corrected-final tuning/exclusions.''')
 put('LIMITATIONS.md',f'''# Limitations and readiness

**{a['recommendation']}**. Zero-error integrity/false-complete gates pass, but all-mandatory recall, exact sets, precision and historical P@1 tolerance fail (FINAL_AUDIT.json). Thresholds unchanged. Do not freeze the general interface or start Phase 5L.

Four temporal requirements fail canonical recognition: 'time is T' (two scopes) and windows with 'and' (two scopes). Actual-window consistency keeps the latter PARTIAL; the former stays UNVERIFIED. Two reverse source-hash forms are unrecognized. Measurement/conjunction obligations are retained. Extra residual markers create inspection on 56 cases; relevant raw data alone never justify completeness. Next: selector/source normalization and harmless-discourse vs mandatory-content distinctions, with fresh assessment questions.

Validator independence is methodological; shared semantics/language/author assumptions can correlate. Unsupported quotations, negation and aliases remain bounded risks. Only finite observed protection is claimed. Natural-language inspection is not a verified temporal/entity answer; consumers must enforce typed scope and reject unverified fulfillment. Comparisons, inventory and unsupported physical interpretations remain unfulfilled; no safety/factual judge.

Final V2 has 72 authored forms, not 144 independent linguistic cases; each repeats on two scopes. References are source-grounded/mechanical, not human labels. Wilson intervals do not prove universal performance. Relevance includes partial/inspection data, separate from 54/106 completed full-capable requests. Historical K regression is exposed/nonindependent.

Inherited units/frames/calibration, conditional cache, native actuator-vs-contact distinctions, historical binaries and sensor clocks stay unchanged. No world transforms, table-support/falling inference, channels/corpus expansion, R1/admission/GSN/downstream agents. Callers must opt in; preserved legacy K retains historical semantics. Nothing pushed or merged.''')
 print('REPORTS WRITTEN',flush=True)
if __name__=='__main__':run()
