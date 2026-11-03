"""Render observed results and predeclared capability decisions, without rescoring criteria."""
import json,collections,statistics
from pathlib import Path
from .config import *
from .metrics import calculate
from .decision import decide

def load(n):return json.loads((WORK/n).read_text())
def write(n,s):(HERE/n).write_text(s.strip()+'\n')
def fmt(x):return 'N/A' if x is None else f'{x:.3f}'
def generate():
 cases={q['id']:q for q in map(json.loads,(HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines())};rows=[]
 for name in ('dev_v3','final_v1'):rows += [json.loads(p.read_text()) for p in sorted((WORK/name).glob('*.json'))]
 assert len(rows)==594;replay=load('REPLAY_VALIDATION.json');assert replay['passed'];metrics=calculate(rows,cases);criteria=json.loads((HERE/'ACCEPTANCE_CRITERIA.json').read_text());component=load('ADVERSARIAL_COMPONENT_RESULTS.json');decision=decide(metrics,rows,cases,replay,component,criteria)
 (WORK/'METRICS.json').write_text(json.dumps(metrics,sort_keys=True,indent=2));(WORK/'READINESS_DECISION.json').write_text(json.dumps(decision,sort_keys=True,indent=2))
 with (HERE/'RETRIEVAL_RESULTS.jsonl').open('w') as f:
  for r in sorted(rows,key=lambda r:(r['case_id'],r['mode'])):f.write(json.dumps(r,sort_keys=True,allow_nan=False)+'\n')
 validity=load('REFERENCE_VALIDITY_AUDIT.json');invalid_refs=set(validity['invalid_case_annotations']);final=[r for r in rows if r['split']=='final'];finalcases=[q for q in cases.values() if q['split']=='final'];freeze=json.loads((HERE/'DATASET_FREEZE.json').read_text());reg=load('REGRESSION.json');fault=[r for r in final if cases[r['case_id']]['fault']];missing=collections.Counter(k for r in final for k in r['assessment']['missing_facets'])
 table=['| Category | Mode | IR n | P@1 | R@5 | R@20 | MRR | Complete / 18 | Correct / required abstentions |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for cat in sorted({q['category'] for q in cases.values()}):
  for mode in MODES:
   m=metrics['final'][mode]['per_category'][cat];table.append(f"| {cat} | {mode} | {m['relevance_denominator']} | {fmt(m['precision_at_1'])} | {fmt(m['recall_at_5'])} | {fmt(m['recall_at_20'])} | {fmt(m['MRR'])} | {m['complete_cases']} / {m['mode_instances']} | {m['correct_abstentions']} / {m['required_abstentions']} |")
 headline=['| Mode | IR n | P@1 | R@5 | R@20 | MRR |','|---|---:|---:|---:|---:|---:|']
 for mode in MODES:
  m=metrics['final'][mode];headline.append(f"| {mode} | {m['relevance_denominator']} | {fmt(m['precision_at_1'])} | {fmt(m['recall_at_5'])} | {fmt(m['recall_at_20'])} | {fmt(m['MRR'])} |")
 write('README.md',f'''# Phase 5J: independent RAG readiness gate

Recommendation **{decision['recommendation']}: {decision['interpretation']}**.

This is an evaluation of the unchanged Phase 5I release, not a corpus/model/channel expansion. All 432 indexed executions and 104 variants remain intact. No downstream agents, R1 decisions, predictions or human labels were changed; empirical admission remains disabled.

198 unique authored questions (22 per category), 36 development / 162 final, over 22 indexed executions and 17 variants. Three existing modes produce 594 main case-mode results; repeated modes/replays are not independent language questions. Final source/attribution/numeric errors were zero. Natural-language and multi-source completeness limitations prevent treating exact lookup success as downstream readiness.

Read READINESS_DECISION.md, RETRIEVAL_METRICS.md, EVIDENCE_SUFFICIENCY_AUDIT.md and LIMITATIONS.md. Frozen data/configuration, source references and case-level outputs are included. Machine-readable metrics and replay records are in `{WORK}` and covered by ARTIFACT_MANIFEST.json. The assessment is mechanically checked and assessor-authored, not independent human evaluation or a physical-safety accuracy study.''')
 write('RETRIEVAL_METRICS.md','''# Retrieval results

Final assessment: 162 unique questions, 18 per category, 486 case-mode instances. IR metrics apply to the 96 questions with a predefined nonempty relevance set and no required abstention; unsupported/ambiguous cases are not assigned fictitious zero relevance. Required-facet coverage and negative controls have separate denominators.

'''+ '\n'.join(headline)+'''\n
Exact is a manually structured diagnostic, not a natural-language parser. Channel NL ranking sees six candidates within supplied execution/task/variant/temporal constraints, without positive target-channel labels. Legacy geometry/document questions use the existing variant-aware endpoint and frozen explicit family/object scopes; these are different supported interfaces. No hybrid implementation exists or was added.

'''+ '\n'.join(table)+'''\n
Completeness columns retain raw frozen-rubric output. C7-20 has an invalid superseded facet; use the separate validity overlay for C7 completeness/sufficiency (17 valid final C7 questions). IR relevance labels, all 96-question ranking denominators and factual/source audits are unaffected.

All case-level values, source bindings, ranking lists, unsupported statuses and missing facets are in RETRIEVAL_RESULTS.jsonl. Source association correctness uses the frozen registry binding map; numeric/geometry factual answers use independently inspected original artifacts. Per-category N/A means IR is not defined, not perfect or zero accuracy.

Suite-stratified execution-cluster bootstrap intervals (2,000 replicates) are in METRICS.json. They describe resampling these selected execution clusters, not population coverage, human relevance judgments or independent linguistic sampling. The final questions share 18 execution contexts. Repeated model modes are never pooled as independent observations. No universal zero-error guarantee follows from the observed zero attribution errors.''')
 suff=['| Mode | Sufficient | Conditional | Insufficient | Unavailable | Ambiguous | Invalid |','|---|---:|---:|---:|---:|---:|---:|']
 for mode in MODES:
  counts=metrics['final'][mode]['sufficiency_counts'];suff.append('| '+mode+' | '+' | '.join(str(counts.get(k,0)) for k in ('SUFFICIENT','CONDITIONALLY_SUFFICIENT','INSUFFICIENT','UNAVAILABLE','AMBIGUOUS','INVALID'))+' |')
 write('EVIDENCE_SUFFICIENCY_AUDIT.md','''# Narrow-fact evidence sufficiency

The production APIs do not classify sufficiency. All categories below come from the external predeclared rubric, not retriever assertions or an LLM judge. There is no physical-safety sufficiency result.

'''+ '\n'.join(suff)+f'''\n
Each case records separate relevance, completeness, credibility, attribution, numerical matching and uncertainty requirements. Required facets must all be present for a sufficient result. Conditional sufficiency is explicitly limited to a documented cache assumption or verified metadata document requiring field inspection. An answerable false candidate number may be contradicted by sufficient source evidence; sufficient does not mean the candidate assertion is true.

Missing-facet counts across final modes: `{json.dumps(dict(missing),sort_keys=True)}`. Counts include repeated modes and deliberately unsupported requests; they are not prevalence estimates.

The six exposed measurement families do not form an automatic cross-interface evidence assembler. Frame/action/chunk association summaries are available, but do not substitute for original action vectors, original policy/inference entries and their source fields in the stricter completeness checklist. Camera exposure clocks, calibration and physical event claims remain unsupported. Contact-pair references exist in the legacy corpus; missing pair-force/physical-time interpretation must not be described as absence of all contact data.

A verified main_table symbolic mapping exists in bounded tabletop source audits, but direct logical alias retrieval remains a gap in the evaluated interfaces. Geometry identity references can support native identity without establishing pose, support, contact or safety. No geometric identity has been promoted to a physical-event conclusion.

A zero-hit lexical/semantic result is classified unavailable at that interface/query, not evidence that the source artifact never existed. Source absence claims rely on the independent source/contract audit, not search failure.''')
 abst=['| Mode | Required abstentions | Correct | Incorrect on positive references | Unsupported evidence returned | False assurance |','|---|---:|---:|---:|---:|---:|']
 for mode in MODES:
  m=metrics['final'][mode];abst.append(f"| {mode} | {m['required_abstentions']} | {m['correct_abstentions']} | {m['incorrect_abstentions']} / {m['positive_reference_denominator']} | {m['unsupported_evidence_returns']} | {m['false_assurance']} / {m['mode_instances']} |")
 write('ABSTENTION_AND_UNCERTAINTY.md','''# Abstention and uncertainty

'''+ '\n'.join(abst)+'''\n
Genuine API abstention means no returned records. It is reported independently from the external rubric deciding that raw evidence is insufficient. Raw arrays returned for untyped support/calibration questions are not counted as acceptance of those interpretations when the result preserves native units, conditional/unresolved properties and false safety/synchronization flags.

False assurance is measured through explicit assurance contracts and returned flags, not generated natural-language answers: there is no answer generator. The observed zero rate does not measure hypothetical drafter hallucinations. Typed missing fields, wrong scope, unsupported transforms, unknown sensor clocks and unavailable historical attestation are evaluated separately from questions that require natural-language clarification.

Conditional cache queries require an explicit channel to use typed property filters. NL-only modes do not supply that positive channel oracle, so some fail at interface validation before ranking. Those are interface/intent coverage gaps, not evidence that the semantic embedding ranked the right field incorrectly. Untyped exact-instant ambiguity cannot be automatically resolved; the external rubric records ambiguity instead of inventing a timestamp.

All uncertainty labels and contract-status errors are retained per case. Explicit wrong-execution denial appears in the development challenge subset; final tests exercise wrong task, variant, source and temporal scopes plus cross-execution attribution. This is a final-suite coverage limitation, not a claim of final unknown-ID replication.''')
 write('ADVERSARIAL_TEST_RESULTS.md',f'''# Adversarial robustness

{len(fault)} final case-mode fault instances cover missing, corrupted, replaced, symlinked and instruction-bearing scratch source data. Original canonical files are hash-checked before/after injection and never modified. The unchanged Phase 5I target is called with a documented I/O fault adapter below retrieval logic; this is not a modified ranking algorithm or a compromised-release experiment.

Semantic, lexical and exact modes also test wrong task/variant/source, wrong units, impossible/reversed time windows, ambiguous names, unsupported assurance levels, calibration/world-frame requests and conditional timing. Detailed failures and empty-result reasons remain in RETRIEVAL_RESULTS.jsonl.

Component probes: `{json.dumps(component['rows'],sort_keys=True)}`.

The legacy hash-matching XML symlink acceptance is a measured contract-policy difference. Strict Phase 5I rejects the same alias. The probe uses a verified-binding fixture and does not establish an end-to-end ability to forge a trusted release. It is nevertheless a blocker to promising a uniform descriptor-bound integrity policy across the legacy and modern interfaces.

Instruction-note injection changes scratch HDF5 bytes and is rejected by hash verification. No source text is executed as harness instructions. This is an integrity/instruction-boundary probe, not an LLM prompt-injection resistance benchmark; no downstream model exists in scope.''')
 audit=load('PRODUCER_DISCREPANCY.json')
 write('PRODUCER_DISCREPANCY_AUDIT.md',f'''# Outstanding producer file

The file is `oft_adapter.py`. All {audit['executions']} executions declare SHA256 `cc326e61cdf5c2058905f9774175aa17e03d5fb2e8d0b16eb8c5bb8aec3208b5` for that relative file. Its name/hash are specified, but matching bytes are unavailable in the registered original project roots, preserved source package and checked local archive. No hash-mismatched replacement was found. This is missing available bytes, not demonstrated corruption or an inferred implementation.

Exact candidates/archive checks and original archive-marker metadata are in PRODUCER_DISCREPANCY.json. The search is bounded, not an assertion that no copy exists anywhere. No Alliance restoration was needed for current source-value evaluation; no newly written adapter or alternate source was substituted.

Blocking: exact historical producer source/runtime attestation and any assertion that this adapter's running bytes are authenticated. Nonblocking: independently hash-verified raw HDF5 value retrieval and the explicitly bounded current provenance scope, which never claims historical runtime completeness. The whole historical binary/environment remains unattested for other reasons too; recovering one file would not prove a clean checkout, running binary or container identity.

All 432 executions share this limitation. No individual raw value is invalidated merely by unavailable historical runtime attestation. Existing conditional physical/temporal interpretations are not promoted to compensate. For a release consumer requiring complete historical producer attestation, this is a specific assurance blocker; it is not silently waived.''')
 write('REFERENCE_CONSTRUCTION.md',f'''# Reference construction and separation

Deterministic SHA256 selection within suite-specific recording-length strata selected 22 indexed development executions: six goal, five long, six object, five spatial. Where possible a new XML variant was selected before reusing one. The resulting 17 variants are the observed coverage, not a claim to cover all 104. One scope per suite is development; the other 18 scopes form the final assessment. All nine categories have 22 authored formulations, with 4 development and 18 final cases each. Query order is a fixed seed hash.

EVALUATION_SELECTION.json and DATASET_FREEZE.json give exact IDs, lengths, strata and hashes. References use direct original HDF5 indexing, recorded metadata, XML body/geom definitions, native mapping files and existing verified contracts. No reference value is copied from a target retrieval response. This is an independent inspection path using the same h5py dependency, not an independent decoder library or independent human judgment. Seven evaluator unit tests validate denominator, canonicalization and bootstrap mechanics; original-source checks validate the references themselves.

Source IDs and ID-to-source associations necessarily use frozen index links. They do not provide the numerical/geometry truth oracle: those facts come from original artifacts. SOURCE_ASSOCIATIONS.json freezes 168 candidate/source bindings and 38 artifact identities before final evaluation. Numeric comparisons use exact raw representation identity, not fitted tolerances. False candidate numbers differ by fixed 1 and are not assertions made by the retriever.

Version history: dataset v1 and development outputs are preserved under reference_v1/dev_v1. Independent source/contract review corrected 13 case specifications before any final target query: provenance-field specificity, existing metadata endpoint, first/last-frame scope and ambiguous relevance. All 198 question texts and acceptance thresholds remained byte-for-byte unchanged. Final dataset v2 SHA256: {freeze['dataset_sha256']}. REFERENCE_REVISIONS.json identifies affected cases. Development was rerun; final references were then frozen. The harness also corrected scratch-path canonicalization before any final query, consistent with the predeclared replay policy.

Mechanically verifiable: values, dtype/shape, sample indices, declared source hashes, metadata declarations and native identity bindings. Assessor-authored judgments: what evidence facets the wording requires, whether a source reference requires further inspection, and the narrow sufficiency checklist. No independent expert review was performed. A post-run audit found a residual superseded raw-channel facet in C7-06 (development) and C7-20 (final). Their completeness/sufficiency judgments are invalid, explicitly reported apart from valid relevance and source checks; frozen data/results were not changed. Ambiguous interpretations and unsupported physical claims remain explicit; no existing human labels were accessed as answer labels or changed.''')
 captable=['| Capability | Decision |','|---|---|']
 for name,data in decision['capabilities'].items():captable.append('| '+name.replace('_',' ')+' | '+data['status']+' |')
 write('READINESS_DECISION.md',f'''# Formal readiness decision

**Recommendation {decision['recommendation']}: {decision['interpretation']}. Do not freeze this as a general natural-language, multi-source safety-case retrieval interface yet.** No downstream implementation is authorized.

'''+ '\n'.join(captable)+f'''\n
Criteria were frozen before questions/target results in ACCEPTANCE_CRITERIA.json. There is no weighted overall score. Zero source/scope/value error and false-assurance tolerances follow from the need for auditable factual citations. NL targets (P@1/R@5 >=0.90, R@20 >=0.95) and multi-source complete-case target >=0.95 are predeclared engineering pilot gates, not universal safety standards; they bound manual citation-repair and missing-evidence burden. They cannot establish physical-safety sufficiency.

Structured narrow-value diagnostic: {decision['capabilities']['exact_source_value_retrieval']['basis']['complete']} / {decision['capabilities']['exact_source_value_retrieval']['basis']['eligible_cases']} complete. Multi-source complete cases by mode: {decision['capabilities']['multi_source_completeness']['basis']['by_mode']}. Full quantitative capability evidence is saved in READINESS_DECISION.json under the working-artifact directory; per-category results are in RETRIEVAL_METRICS.md.

Strengths: faithful structured raw values, preserved execution/variant/time scope, strict modern source verification, explicit unavailable historical attestation, and reproducible results. Blockers: natural-language discoverability/interface coverage, incomplete multi-source composition, direct symbolic-alias access, and nonuniform integrity contracts across legacy and modern routes. Natural-language questions with typed property filters can require channel intent resolution before ranking; the evaluated release supplies no such parser.

Nonblocking under bounded raw retrieval: missing historical adapter/binaries when not requested, conditional cache semantics clearly labelled, and absent calibrated sensor/world evidence explicitly refused. These become blockers whenever the consumer requires those stronger claims. Physical-safety sufficiency is NOT_EVALUATED.

Next step: a separately authorized focused database/retrieval-only corrective phase, then a new frozen independent assessment. See ISSUES.md. Do not change this benchmark or its rankings to make the current release pass. No GSN, drafter, critic, R1 admission or downstream agent work is authorized by this recommendation.''')
 failures=[]
 for r in final:
  q=cases[r['case_id']];a=r['assessment']
  if a['relevance_eligible'] and (a['precision_at_1']<1 or (q['expected_status'] in ('SUFFICIENT','CONDITIONALLY_SUFFICIENT') and not a['complete_required_evidence'] and q['id'] not in invalid_refs)):
   reason=('TOP_RANK_IRRELEVANT' if a['precision_at_1']<1 else 'MISSING_REQUIRED_FACETS') if r['output']['items'] else ('PRE_RANKING_INTENT_OR_INTERFACE_GAP' if r['output']['status']=='invalid_query' else 'NO_MATCH_OR_UNINDEXED_FAMILY');failures.append(dict(case_id=r['case_id'],mode=r['mode'],category=r['category'],status=r['output']['status'],reason=r['output']['reason'],root_cause_class=reason,missing_facets=a['missing_facets'],returned_ids=[x['id'] for x in r['output']['items']],sufficiency_annotation_valid=q['id'] not in invalid_refs))
 (WORK/'FAILURE_CASES.json').write_text(json.dumps(failures,sort_keys=True,indent=2))
 write('ISSUES.md',f'''# Corrective work proposals — not implemented

1. **J-01: Natural-language intent/family coverage.** FAILURE_CASES.json contains {len(failures)} final case-mode failures. Separate pre-ranking typed-interface gaps from wrong lexical/semantic rankings. A future authorized phase should define a bounded interface and a new frozen assessment; do not train/tune to these final cases.

2. **J-02: Multi-source completeness.** Associations do not automatically return every original policy/inference/action or geometry artifact requested together. A future evidence-bundle contract needs independent field/completeness tests and preserved temporal uncertainty. Missing sensor clocks/calibration must stay unavailable.

3. **J-03: Uniform strict source access.** The legacy geometry guard uses path-based sha(path); Phase 5I uses descriptor-bound no-follow access. A hash-identical scratch symlink was accepted only by the legacy component. Proposed patch: legacy verification primitive and explicit assurance compatibility, with path/redirection/race tests. No production patch is made here.

4. **J-04: Searchable symbolic identity.** The bounded main_table audit is not a direct logical-alias endpoint. A future metadata proposal must not widen domains or silently enable pose/support claims.

5. **J-05: Historical provenance.** Recover matching oft_adapter.py if bounded restoration is justified. This alone cannot authenticate historical binaries, checkout cleanliness or a container. Keep historical assurance failing closed.

6. **J-06: Consumer sufficiency/ambiguity.** No production narrow-fact classifier or NL clarification mechanism exists. Any future consumer or safety-case implementation requires separate authorization; do not hide it in evaluation helpers.

7. **J-07: Reference-schema consistency.** Before future freezes, reject superseded raw-channel facets on metadata-only questions. The post-run validity audit identifies C7-06/C7-20; preserve their raw outputs but do not use those completeness judgments as production failures.

No external issue was posted or message sent. These local proposals preserve the evaluated implementation.''')
 write('REPRODUCIBILITY.md',f'''# Automated replay

All computation ran on Hestia. No Alliance compute, Sea NFS, new simulations, global dependency changes, full source copies or new database. RESOURCE_PREFLIGHT.json budgeted 2 GiB disk and 3 GiB/process; sources remain external. HF/XDG caches use the new owned working directory.

Baseline commit: {BASE_COMMIT}. Database: {DATABASE}; SHA256 {DATABASE_SHA}. FROZEN_EVALUATION_CONFIGURATION.json pins implementation files, model, sidecar, package versions, ranking, filters, top-k and preprocessing. Phase 5I's manifest anchors selected dependency bytes; versions alone are not binary attestation. verification_mode describes the modern route; legacy retains its frozen hash-based guard, audited separately.

On Hestia, from repository root with python3 -S and the recorded explicit PYTHONPATH:

```sh
python3 -S -m evaluation.r1_v4.rag_evidence_database.readiness_evaluation.run --split final --run operator_replay
```

RUN_REPLAY.sh supplies the exact environment and validates a simple run label. A new run name starts a fresh pass; the same name validates/resumes case files. Frozen database, code, dataset, criteria, model and sidecar identities are checked before execution. No fallback, rewriting, query decomposition or hybrid ranking is inserted.

REPLAY_VALIDATION.json records two full automated final passes, full resume with 486 cached cases and partial resume with 37 seeded files / 449 new evaluations. All 486 canonical outputs agree. Only scratch diagnostic hash/path differences are excluded, never values, ranks, identities, statuses or rubric findings. This is same-host automated replication, not independent human/cross-platform replication.

METRICS.json uses fixed denominators and frozen metrics.py, including reproducible 2,000-replicate cluster intervals. Pre-final reference/harness revisions and development artifacts are retained. Final wording/criteria were not changed after final outputs. All {reg['total_tests']} inherited regressions and seven evaluator checks passed. Baseline/frozen identities are verified again before local commit.''')
 write('LIMITATIONS.md',f'''# Limitations

This is assessor-authored development evaluation, not independent human review. There are 198 formulations, 22 executions and 17 variants overall; final assessment has {len({q['execution_id'] for q in finalcases})} executions / {len({q['variant_id'] for q in finalcases})} variants. It does not exhaust all 432 executions / 104 variants or future language. Four suites/length strata are represented by a fixed non-outcome-based seed.

Explicit execution/task/variant/time/object constraints are supplied. Exact receives a field oracle; NL modes do not receive positive channel labels. Legacy family/object filters still encode user scope. Pools are bounded (six channels or constrained legacy candidates); Recall@20 may be uninformative in small pools. No autonomous NL-to-scope parser or hybrid retrieval was evaluated.

References use an independent inspection path but the same h5py runtime. Sufficiency and metadata follow-up checklists are authored assumptions, not expert labels. Distinct wording is not independent human sampling. Cluster intervals describe selected source contexts only. The unknown-ID challenge is not independently replicated outside its development case.

No answer generator exists: unsupported acceptance/false assurance concern explicit contracts/flags, not hypothetical hallucination. The source-note test measures integrity rejection, not LLM prompt-injection resistance. Legacy verification is weaker than descriptor-bound access; release-level verification does not create a uniform per-request strict guarantee.

Historical runtime identity, missing adapter bytes, calibrated world transforms, sensor synchronization and physical calibration remain unresolved/unavailable. Current verification is retrospective. Cache offset stays conditional. Raw contacts may include pair references, but counts, actuator outputs and geometry alone do not establish support, falling, collision outcomes or safety.

No R1 judgments/admission, safety cases, GSN, downstream agents, training, corpus/channel expansion, frozen predictions or human labels changed. No final query or acceptance criterion was tuned after final performance was observed. One final completeness annotation (C7-20) and its development counterpart are invalidated in a post-hoc validity audit; raw frozen outputs remain untouched. This limits sufficiency conclusions to 161 final questions per mode, while relevance/attribution results are unaffected.''')
 with (HERE/'EVIDENCE_SUFFICIENCY_AUDIT.md').open('a') as f:
  f.write('\nReference-validity qualification: the table above preserves raw frozen-scorer output. C7-20 (final) retained an unrelated arm-position requirement after its metadata-only reference revision; its sufficiency judgment is invalid. C7-06 is the analogous development annotation. Do not interpret either as a demonstrated production failure. The dataset, criteria and raw results are unchanged. The following post-hoc validity overlay excludes only these completeness judgments, not relevance/source/assurance measurements, and does not change recommendation B.\n')
  f.write('\n| Mode | Valid final sufficiency n | Counts after validity exclusion |\n|---|---:|---|\n')
  for mode in MODES:
   v=validity['validation_counts']['final'][mode];f.write('| '+mode+' | '+str(v['valid_denominator'])+' | '+json.dumps(v['validated_sufficiency_counts'],sort_keys=True)+' |\n')
 with (HERE/'READINESS_DECISION.md').open('a') as f:f.write('\nEvaluation-quality caveat: one final completeness annotation (C7-20) is invalid, as recorded in REFERENCE_VALIDITY_AUDIT.json. It is excluded from validated sufficiency interpretation. Natural-language relevance, C4 multi-source completeness, integrity and source-value gates are unchanged; recommendation B does not depend on that annotation.\n')
 with (HERE/'README.md').open('a') as f:f.write('\nKnown evaluation defect: C7-20 final completeness annotation (and C7-06 development) contains a superseded unrelated requirement. Validated final sufficiency has 161 questions per mode; raw frozen results and all retrieval/source metrics are retained. See the sufficiency/validity audit; the readiness decision is unchanged.\n')
 audit_values=load('INDEPENDENT_OUTPUT_AUDIT.json');assert audit_values['passed']
 with (HERE/'RETRIEVAL_METRICS.md').open('a') as f:
  f.write('\nIndependent audit of all returned final records/samples (separate from relevance): `'+json.dumps(audit_values['counts'],sort_keys=True)+'`. All source/execution/task/variant/object, numeric, unit and checked temporal errors were zero. This does not validate a common physical sensor instant.\n')
  f.write('\n| Mode | P@1 interval | R@5 interval | R@20 interval | MRR interval |\n|---|---|---|---|---|\n')
  for mode in MODES:
   intervals=metrics['final'][mode]['cluster_intervals'];cells=[f"{intervals[k]['lower']:.3f}–{intervals[k]['upper']:.3f}" for k in ('precision_at_1','recall_at_5','recall_at_20','MRR')];f.write('| '+mode+' | '+' | '.join(cells)+' |\n')
 print('REPORTS',decision['recommendation'],{m:metrics['final'][m]['precision_at_1'] for m in MODES},flush=True)
if __name__=='__main__':generate()
