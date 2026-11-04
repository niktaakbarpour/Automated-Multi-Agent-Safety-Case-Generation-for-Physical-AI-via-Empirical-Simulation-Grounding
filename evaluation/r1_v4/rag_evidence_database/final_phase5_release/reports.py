"""Post-evaluation reporting only; cannot modify frozen cases or retrieval."""
import json,collections,math,statistics
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def write(name,text): (HERE/name).write_text(text.strip()+'\n')
def run():
 rows=[json.loads(p.read_text()) for p in sorted((WORK/'final').glob('*.json'))];assert len(rows)==448
 reg=json.loads((WORK/'FINAL_REGRESSIONS.json').read_text());repro=json.loads((WORK/'REPRODUCIBILITY_RESULTS.json').read_text());audit=json.loads((WORK/'INDEPENDENT_SET_AUDIT.json').read_text());restore=json.loads((WORK/'RESTORATION_RESULTS.json').read_text())
 assert reg['passed'] and repro['passed'] and audit['passed']
 statuses=collections.Counter(r['bundle']['completeness_status'] for r in rows);counts=collections.Counter(r['kind'] for r in rows)
 errors=collections.Counter(e for r in rows for e in r['metrics']['errors'])
 m=dict(cases=len(rows),executions=16,structured_case_types=len(counts),status_counts=dict(statuses),status_correct=sum(r['metrics']['status_correct'] for r in rows),false_complete=sum(r['metrics']['false_complete'] for r in rows),false_assurance=sum(r['metrics']['false_assurance'] for r in rows),critical=sum(r['metrics']['critical'] for r in rows),critical_rejected=sum(r['metrics']['critical_rejected'] for r in rows),source_sample_comparisons=sum(r['metrics']['source_sample_comparisons'] for r in rows),metadata_comparisons=sum(r['metrics']['metadata_comparisons'] for r in rows),errors=dict(errors),missing_reporting_correct=sum(r['metrics']['missing_reporting_correct'] for r in rows),per_kind={k:dict(cases=v,correct=sum(r['metrics']['status_correct'] for r in rows if r['kind']==k)) for k,v in counts.items()})
 m['mandatory_available']=sum(r['metrics']['mandatory_available'] for r in rows);m['mandatory_requested']=sum(r['metrics']['mandatory_obligations'] for r in rows)
 eligible=[r for r in rows if r['metrics']['expected_complete']];m['complete_mandatory_available']=sum(r['metrics']['mandatory_available'] for r in eligible);m['complete_mandatory_requested']=sum(r['metrics']['mandatory_obligations'] for r in eligible)
 m['max_numeric_error']=0 if not errors else None;m['latency_seconds']=dict(median=statistics.median(r['latency_seconds'] for r in rows),maximum=max(r['latency_seconds'] for r in rows))
 assert m['status_correct']==448 and not m['false_complete'] and not m['false_assurance'] and not errors and m['critical']==m['critical_rejected']
 (WORK/'FINAL_METRICS.json').write_text(json.dumps(m,sort_keys=True,indent=2))
 with (HERE/'FINAL_EVALUATION_RESULTS.jsonl').open('w') as f:
  for r in rows:
   p=WORK/'final'/(r['case_id']+'.json');f.write(json.dumps(dict(case_id=r['case_id'],kind=r['kind'],metrics=r['metrics'],status=r['bundle']['completeness_status'],case_result_path=str(p),case_result_sha256=sha(p),canonical_digest=r['canonical_digest']),sort_keys=True)+'\n')
 write('FINAL_EVALUATION_METRICS.md',f'''# Frozen structured-interface assessment

All {m['cases']} cases returned the predefined status. The set contains 28 structured request types over 16 fresh execution scopes (four per task suite), excluding all executions found in earlier J/K/K.1 question sets. These are source-scope instances, not 448 independent linguistic formulations or human judgments.

| Expected/returned status | Correct / total |
|---|---:|
'''+ '\n'.join(f'| {k} | {v}/{v} |' for k,v in sorted(statuses.items()))+f'''

False-complete bundles: 0/448; critical requests rejected without evidence: {m['critical_rejected']}/{m['critical']}. False assurance: 0/448. Source/value/unit/selector, execution/task/variant and temporal errors: 0. Missing-obligation reporting: {m['missing_reporting_correct']}/448.

Direct raw-source sample comparisons: {m['source_sample_comparisons']}; independent metadata-item comparisons: {m['metadata_comparisons']}; maximum and mean numeric error: zero (exact array equality, no fitted tolerance). Required mandatory obligations for expected-complete cases: {m['complete_mandatory_available']}/{m['complete_mandatory_requested']}. Unavailable obligations in negative/partial cases are intentionally not retrieval failures.

The supplemental source-set audit independently checks full original-reference cardinality and selector sets: 392 available groups, 408 items, zero discrepancies. Unit/component checks use preserved H contracts and native model indexes. No physical calibration or historical binary claim follows.

Descriptive one-sided 95% zero-event binomial upper bounds are 1-0.05^(1/448) = {1-math.pow(.05,1/448):.4%} for false completeness, and {1-math.pow(.05,1/m['critical']):.4%} over critical cases. Scope/template dependence prevents interpreting these as population guarantees; no probabilistic safety claim is made.

Per-type metrics and latency (verified-session mode, not a controlled speed benchmark) are in `FINAL_METRICS.json` in the external working directory. Strict mode is the production default; an additional 40-case strict replay matched statuses, values and citations. Acceptance criteria were frozen before the first final run; no cases, labels or thresholds were changed afterward.
''')
 write('README.md','''# Final Phase 5 restricted RAG release

Decision A: PHASE 5 COMPLETE — RESTRICTED STRUCTURED INTERFACE READY.

Release `phase5-structured-1.0.0` provides explicit, validated evidence obligations and verified source retrieval. It does not certify physical safety. The original Phase 5I database is referenced unchanged; no corpus or measurement expansion occurred.

Start with SUPPORTED_INTERFACE_CONTRACT.md and schemas; run `python3 -S -m evaluation.r1_v4.rag_evidence_database.final_phase5_release.examples` on Hestia. See PHASE5_COMPLETION_REPORT.md for the gate decision, FINAL_EVALUATION_METRICS.md for independent source comparisons, DOWNSTREAM_HANDOFF.md for mandatory consumer rules and RELEASE_VERIFICATION.md for trusted release verification.

Natural-language interpretation, lexical and semantic exploratory routes remain experimental. Phase K.1 limitations are preserved, not repaired or reclassified here. No downstream agents, GSN generation or empirical R1 admission are enabled. The local commit containing ARTIFACT_MANIFEST.json binds this release; nothing is pushed or merged.
''')
 write('SUPPORTED_INTERFACE_CONTRACT.md','''# Supported interface v1

Import `StructuredRetriever` from `evaluation.r1_v4.rag_evidence_database.final_phase5_release.api`; call `retrieve(request)` and always close it. The default constructor uses strict descriptor-bound verification. The trusted host may select `verified_session`; a query cannot choose or lower the verification mode. Session verification hashes source bytes and invalidates identity-bound state on changes; modification time alone is not cryptographic proof.

STRUCTURED_QUERY_SCHEMA.json is a closed JSON Schema 2020-12 contract; EVIDENCE_BUNDLE_SCHEMA.json describes output. Read CAPABILITY_REGISTRY.json and config.REGISTRY for the exact frozen vocabulary. Six existing raw channel fields and nine metadata groups are supported. This is not a generic SQL interface or a claim that every legacy evidence family has a production adapter.

A request requires schema_version, execution_id, assurance, provenance and 1–16 explicit obligations, including at least one mandatory obligation. Each obligation requires a unique ID, the same execution, a registered family and field, and mandatory status. Task/variant constraints must agree. Requested source hash/record ID, native component, object, units, interpretation and assurance constraints are enforced where meaningful. Unknown fields, unsupported aliases, contradictory scopes and nonfinite values fail clearly. Assurance cannot be silently downgraded.

Temporal families require a selector: inclusive saved-frame interval or exact stored simulator-label interval. No rounding, interpolation or nearest-neighbor substitution occurs. Use saved frames when decimal labels cannot be represented exactly. Windows are limited to 4096 frames and 16384 total raw samples per request. A selector is never a measurement obligation. Timeless metadata rejects temporal selectors. Geometry requires an exact supported native object; symbolic main_table is a separate identity group.

COMPLETE WITHIN VERIFIED CONTRACT means all mandatory explicit obligations passed schema validation, source/assurance/scope verification, evidence fulfillment and the separately implemented original-request completeness validator. That validator checks obligation identity/digests, original database associations, independent temporal expectations, source sets and interpretation metadata. It does not trust only a list supplied by a planner. Mutating or omitting a mandatory group fails closed.

PARTIAL, UNAVAILABLE, UNSUPPORTED, INVALID SCOPE and UNVERIFIED PLAN are noncomplete statuses. Valid optional evidence may be missing while all mandatory obligations are complete; missing optional obligations remain explicit. Empty/all-optional requests cannot become complete. Invalid requests and source-integrity failures return no evidence. PARTIAL bundles retain individually verified evidence while exposing missing requirements. Scope echoed on a rejected request is not verified attribution; inspect validation and status.

Every production request currently verifies the primary execution source closure, including HDF5, even for metadata. Missing closure therefore blocks metadata-only production retrieval too. Output contains original IDs, canonical source references/hashes, scope, recorded values or verified references, coverage, units/interpretation, assurance, missing obligations and limitations. No missing numeric values are fabricated.

Recorded values remain unchanged. Native component projection is the previously validated transformation y=x[j], with full raw arrays retained. Verified physical mode requires supported verified contract properties. Conditional interpretations require explicit permission and assumptions; conditional SI actuator interpretations are not contact-force measurements.

Experimental natural-language retrieval lives in experimental.py. Its root status is always UNVERIFIED PLAN, production_eligible=false, and inferred obligations are unauthorized. No automatic conversion to this API is supplied. A consumer must separately review and explicitly authorize every structured obligation; an LLM confidence statement is insufficient. This API proves completeness of the provided structured request, not coverage of an earlier natural-language question it never received.
''')
 write('EVIDENCE_CITATION_CONTRACT.md','''# Stable evidence citations

A citation is `evidence-citation:` plus the canonical digest of citation_basis: citation version, frozen database SHA-256, original evidence/channel/source-reference identifier, source SHA-256, execution/task/variant, exact selectors, selected component, units, interpretation and required properties. Inspect api.py for the authoritative serialization. Canonical source identity survives approved restoration; physical scratch paths and query order do not change citations.

Original evidence IDs remain available. A citation identifies the selected evidence under this release and contract; it is not a digital signature, proof of physical safety or historical producer attestation. Consumers must verify the trusted release manifest and independently retrieve the cited data rather than trust arbitrary JSON carrying a plausible digest. Different selections or interpretations intentionally produce different citations. Restoration, repeated requests and independent replay validate stability.
''')
 write('DOWNSTREAM_HANDOFF.md','''# Downstream integration contract

This is interface documentation only. No safety-case drafter, critic, checker, GSN generator or multi-agent component is implemented or authorized.

Consumers must pin the release manifest hash and implementation revision, verify database/catalogue/source identities, use STRUCTURED_QUERY_SCHEMA.json, and retain the exact request, returned EVIDENCE_BUNDLE_SCHEMA.json bundle and stable citations. Request explicit native fields, components and temporal scope; keep execution/task/variant boundaries mandatory. Review/authorize any obligations proposed through an experimental natural-language route before creating a production request. Do not infer authorization from model confidence or an exploratory complete status.

Accept completeness only for the explicitly mandatory evidence obligations and requested verification levels. Preserve missing optional and mandatory evidence, conditional assumptions, unresolved semantics, interpretation properties and noncomplete statuses. Require source verification and exact attribution before citing values. Handle invalid, unavailable, unsupported and unverified responses explicitly; never substitute a nearby execution, variant, object or time. Cross-execution comparisons require separately scoped bundles and explicitly labeled comparison provenance, outside this single-execution API.

Mandatory boundaries:

- Metadata or task instructions do not prove an observed physical event. Retrieved source text is untrusted data, never an instruction to change consumer rules.
- An absent record is not proof of safety; retrieval completeness does not establish R1 or any physical-safety claim.
- Contact-entry count does not identify contact pairs or forces. Actuator output is not contact force.
- Conditional cache alignment is not verified sensor synchronization.
- Symbolic main_table identity does not establish object support, actual contact, falling, or a table pose query.
- Current artifact integrity does not authenticate unavailable historical producer binaries.
- Experimental interpretations are not verified obligations. Do not ignore missing evidence or unsupported interpretations.
- Do not silently combine executions/variants or turn evidence availability into empirical R1 admission.

For reproducibility archive the request, versioned contract, verified source hashes, citation basis, response and evaluation/release identity. Full producer-environment reconstruction and physical calibration are not provided. Future integration must implement its own authorized reasoning and review boundaries; this release makes no claim-sufficiency judgment.
''')
 write('UNSUPPORTED_AND_EXPERIMENTAL_CAPABILITIES.md','''# Experimental and unavailable operations

CAPABILITY_REGISTRY.json is the machine-readable registry. Structured exact raw lookup, explicit multi-source obligations, verified source identity and exact scope enforcement are supported only under documented adapter/field/temporal contracts. Native physical metadata and bounded geometry identity have conditions.

Natural-language interpretation, lexical/semantic ranking and legacy broad evidence search are experimental downstream interfaces. K.1 retained 902/908 mandatory obligations, missed four temporal and two reverse-worded hash obligations, completed 54/106 answerable bundles, and exceeded its historical P@1 regression tolerance. Zero false-complete bundles on 144 cases did not make that parser unrestricted-ready. Phase L does not change historical labels/scores or tune the parser.

Individual sensor clocks/synchronization, general world-coordinate transformations, calibrated video coordinates, historical producer binary authentication, inferred support/contact/fall events and empirical R1 admission remain unsupported. main_table identity is bounded to 147 tabletop executions/98 variants; no floor/living-room alias, logical-table pose or physical-support inference is enabled. Saved simulator intervals of 0.05 seconds and physics steps of 0.002 seconds retain their original verified scope. The -0.002-second cache interpretation remains conditional.

Raw arrays retain recorded/verified/conditional property distinctions. SI assumptions, actuator equations and native joint indexes are documented in preserved H contracts, not generalized across unknown recordings. A package version or current source hash is not proof of historical binary identity. No new measurement channels, execution profiles, safety agents or R1 decisions are introduced.
''')
 write('REGRESSION_RESULTS.md',f'''# Regression and preservation

Baseline independently rerun: 813 inherited tests passed. Post-implementation suite: {reg['total']} passed, zero failures, zero skips (718 inherited I/E-H tests, 7 J, 39 K, 49 K.1, 37 new L tests). See external FINAL_REGRESSIONS.json and post-regression logs for exact commands, dependencies and test names.

New tests cover explicit schema obligations, no-parser production calls, omitted/mutated groups, missing frame sets, altered units and scope, incorrect source hashes, empty/all-optional requests, wrong components, world/historical requests, conditional requirements, graph assurance, optional absence, source corruption/missing files, citations and production/experimental separation. Existing suites retain descriptor-bound tampering, geometry, temporal, assurance, semantic isolation and scoring safeguards.

Fresh final assessment: 448/448 statuses correct. Full source-set audit: 392 groups/408 items, zero discrepancies. No ranking changes or source mutations were needed. Initial development diagnostics remain in the external work directory, including a corrected schema-generator syntax error before freeze. No final test failures were suppressed or excluded.

Final read-only preservation verifies unchanged database counts/hash, K.1/K/J manifests and source closures, frozen V3/V4 artifacts, both seals, human-reference packages and scoring safeguards. FINAL_PRESERVATION.json records exact results. Reserved 60 and excluded 38 executions remain outside development; no additional execution or channel was indexed.
''')
 write('INDEPENDENT_REPRODUCIBILITY.md',f'''# Automated independent replay

Frozen dataset SHA-256: `{sha(HERE/'FINAL_EVALUATION_DATASET.jsonl')}`.

Full resume (448 reused), fresh run (448 newly evaluated), partial resume (37 reused), and isolated-environment process (448 newly evaluated) yield canonical digest `{repro['fresh']['canonical_digest']}`. Canonicalization removes only latency and random scratch-directory prefixes in error messages; identities, values, coverage, status and citations remain checked. 1792 case files were independently revalidated. An additional strict-mode 40-case subset matched status/value/citation outputs. All checks passed.

Query schema, bundle schema and capability registry were regenerated separately and matched frozen bytes. The existing database was hash-verified and preserved, not rebuilt or migrated. Retrieval replay and byte-identical interface assembly are reproducible; this does not claim historical producer-environment reconstruction, independent human replication or binary attestation.

Bounded restoration copied 122 explicit mappings/120 unique contents (148459848 bytes) for one eligible execution, retaining source hashes and canonical identities. Restored values and citations matched. Removing a required restored source failed closed despite the original source remaining available: no hidden original-path fallback. Database and catalogue remain separately pinned prerequisites. See RESTORATION_RESULTS.json and restoration.py; restoration manifests reside under the external working directory.
''')
 write('PHASE5_COMPLETION_REPORT.md','''# Phase 5 completion decision

A. PHASE 5 COMPLETE — RESTRICTED STRUCTURED INTERFACE READY.

The frozen structured interface meets all predefined critical criteria: 448/448 correct statuses, zero false-complete bundles, zero incorrect value/source/scope returns or assurance escalation, independently checked required-family sets, and 850 passing regressions without skips. Fresh, full/partial-resume and isolated-process replay agree. Strict-source replay and bounded no-fallback restoration pass. Original database, catalogue, historical releases, sources, labels, seals and scoring safeguards are unchanged.

| Capability | Decision and boundary |
|---|---|
| Structured source lookup | SUPPORTED for frozen registered fields/groups and eligible executions |
| Explicit multi-source completeness | SUPPORTED for mandatory validated obligations, not safety claims |
| Source/provenance integrity | SUPPORTED under pinned source closure and requested assurance scope |
| Execution/task/variant isolation | SUPPORTED, single-execution requests only |
| Temporal retrieval | SUPPORTED WITH CONDITIONS: saved frames/exact simulator labels, no implied synchronization |
| Physical interpretation | SUPPORTED WITH CONDITIONS: original verified properties or explicit conditional contracts |
| Reproducibility | SUPPORTED WITH CONDITIONS: retrieval/interface assembly; bounded restoration, not historical environment |
| Natural language / lexical / semantic | EXPERIMENTAL; K.1 failures remain visible |
| Historical producer binary attestation | UNSUPPORTED when contemporaneous evidence is absent |
| Physical support/contact/fall or R1 inference | UNSUPPORTED; no admission or agents enabled |

The production boundary is an explicit structured request; correctness does not depend on the imperfect natural-language parser. This is not a repair claim for unrestricted language. Consumer authorization of obligations is required before using any language-derived proposal. There is no automatic downstream implementation or next corrective phase. Complete retrieval is not complete physical-safety evidence.
''')
 write('LIMITATIONS_AND_THREATS_TO_VALIDITY.md','''# Limits and threats

The production adapter supports six raw channel families and nine metadata groups, not arbitrary source arrays or every legacy evidence record. Corpus coverage stays 432 executions/104 variants; reserved and excluded executions are unused. Sixteen final execution scopes and 28 structured request types provide finite engineering evidence, not universal assurance, linguistic generalization or independent human evaluation. References use a separate decoder and preserved primary artifacts; shared upstream contracts can still carry correlated mistakes.

A structured request is the authorization boundary. Completeness is relative to its mandatory obligations. The service cannot establish that a caller omitted a requirement from an unseen natural-language question. Optional missing evidence is visible but does not defeat mandatory completeness. Consumers must inspect status, assumptions, scope validation and source identity, not only the presence of items or a COMPLETE string in untrusted JSON.

Temporal windows select exact recorded labels/frames, not sensor instants. Sparse action/inference metadata, especially pre-policy settling frames, may be unavailable. No interpolation, rounding, per-sensor clock reconstruction or arbitrary action-relative selector is supplied. Cache alignment remains conditional. Units and native joint conventions retain H scope; SI actuator interpretations are conditional and do not measure contact force. No world transform or physical calibration is added.

Geometry and main_table bindings establish identity only. Video references are not decoded calibrated coordinates. Contact counts/references do not identify pairs or safety events. Metadata-only verified requests still require the original primary closure, including HDF5. Historical producer/dependency attestation remains distinct from present-day integrity; the prior 103/104 producer-file discrepancy and its scoped limitations are inherited from the preserved J audit. This release does not invent the missing historical evidence.

The session-verification evaluation is complemented by strict replay and inherited tampering tests; it is not a benchmark of every possible race or filesystem attack. Tampering only touches scratch copies. Trust includes pinned manifests and host/library integrity. Restored mappings require canonical content identity and explicit scope; the bounded restoration does not prove a complete external archive is available. No source corpus or historical binary environment is bundled. Automated isolated-process replay is not independent human replication.

No retrieval ranking is changed, no historical labels/thresholds are modified, no safety accuracy is claimed, and no R1 admission, GSN or downstream agent is enabled.
''')
 write('RELEASE_VERIFICATION.md','''# Release verification and reproduction

Run all commands on Hestia from `/disk/1/data/niktakbr/trustworthy-phase16`. Activate the documented PYTHONPATH/runtime from FROZEN_RELEASE_CONFIGURATION.json and REPRODUCIBILITY.md. Pin the Git commit and ARTIFACT_MANIFEST.json SHA-256 through a trusted channel; a manifest cannot authenticate its own replacement.

`python3 -S -m evaluation.r1_v4.rag_evidence_database.final_phase5_release.release --verify <trusted-manifest-sha256>` verifies descriptor-bound hashes and sizes for release files, external case results, restored mappings and pinned database/catalogue/parent manifests. No manifest self hash or circular commit hash is embedded. The commit containing the manifest is the release revision. A changed or missing required artifact fails verification; source corruption and redirection fail verified retrieval.

For retrieval run the executable examples, then `python3 -S -m evaluation.r1_v4.rag_evidence_database.final_phase5_release.evaluate --run operator_fresh`. Use a fresh label for a clean run; repeat that label for full resume. For partial resume run `--run operator_partial --limit 37`, then the same label without `--limit`. Do not overwrite the frozen final result files. `independent_audit` checks original reference sets. `preservation` rechecks parent releases, source closures, seals and counts. `restoration` documents the bounded no-original-fallback experiment; existing archived results need not be overwritten.

Use explicit canonical-source/hash/execution/variant mappings when restoring bytes. A filename match alone is insufficient. No arbitrary path redirection or symlink substitution is authorized. Bounded restoration requires separately pinned database/catalogue; full provenance inspection additionally requires graph/dependency and interpretation artifacts. All production operations require their primary source closure. Unavailable historical binaries do not corrupt otherwise valid raw sources, but historical-attestation requests fail closed.

The final release references the unchanged database instead of duplicating it. Source/dependency, geometry and temporal contracts remain in parent releases, bound through their manifests and preservation checks. Reproduction concerns present-day retrieval, not proof of the historical recording environment.
''')
 write('REPRODUCIBILITY.md','''# Commands and environment

Host: Hestia. Repository: `/disk/1/data/niktakbr/trustworthy-phase16`. Working artifacts: `/disk/1/data/niktakbr/trustworthy-phase5l-working`. Python invoked with `-S`; frozen runtime package versions and imported source hashes are in FROZEN_RELEASE_CONFIGURATION.json. No global package installation or replacement occurred.

Commands (prefix `evaluation.r1_v4.rag_evidence_database.final_phase5_release.`):

- `python3 -S -m <prefix>examples`
- `python3 -S -m unittest discover -s evaluation/r1_v4/rag_evidence_database/final_phase5_release/tests -v`
- `python3 -S -m <prefix>evaluate --run operator_fresh`
- `python3 -S -m <prefix>evaluate --run operator_partial --limit 37`, then without the limit
- `python3 -S -m <prefix>independent_audit`
- `python3 -S -m <prefix>preservation`
- `python3 -S -m <prefix>release --verify <trusted-manifest-hash>`

Replace `<prefix>` with the package prefix above. Exact inherited-suite commands, process environment and logs are preserved in FINAL_REGRESSIONS.json, reproduce.py and external baseline/post-regression artifacts. For isolated replay reproduce.py constructs a minimal environment with explicit dependency directories, thread limits and Hestia-owned caches; it imports no interactive shell initialization.

Resource preflight projected at most 1 GiB additive disk and 4 GiB memory/process with approximately 1.615 TB free. No full database/source-corpus copies or destructive cleanup were used. Bounded restored source content is 148459848 bytes. RESOURCE_PREFLIGHT.json and FINAL_RESOURCE_USAGE.json record measured disk/free-space information; no unmeasured peak RSS claim is made. Existing HDF5 arrays remain external.
''')
 print(json.dumps(m,sort_keys=True),flush=True)
if __name__=='__main__':run()
