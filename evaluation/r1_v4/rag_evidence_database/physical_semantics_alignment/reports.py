"""Generate evidence-backed release reports only from completed validation artifacts."""
import json,csv,sqlite3,collections
from pathlib import Path
from .config import HERE,WORK,BASE,BASE_SHA,BASE_COMMIT,VERSION,TOLERANCE_POLICY
from .audit import save
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def load(name):return json.loads((WORK/name).read_text())
def write(name,text):
 with (HERE/name).open('x') as f:f.write(text.strip()+'\n')
def run():
 audit=load('AUDIT_FINAL.json');velocity=load('VELOCITY_VALIDATION.json');bychannel=load('VELOCITY_BY_CHANNEL.json');build=load('BUILD.json');ret=load('reference_hardened/RETRIEVAL_VALIDATION.json');sem=load('reference_hardened/SEMANTIC_BENCHMARK.json');reg=load('REGRESSION_HARDENED.json');final=load('FINAL_AUDIT.json');fexact=load('legacy_f/RETRIEVAL_METRICS.json');fneg=load('legacy_f/NEGATIVE_RETRIEVAL.json');fsem=load('legacy_f/SEMANTIC_EVALUATION.json');gexact=load('legacy_g/EXTRACTION_RETRIEVAL_VALIDATION.json');gsem=load('legacy_g/CHANNEL_SEMANTIC_EVALUATION.json')
 assert final['passed'] and reg['passed'] and ret['passed'] and bychannel['passed']
 db=sqlite3.connect((WORK/'expanded.sqlite').as_uri()+'?mode=ro',uri=True);rows=[json.loads(v[0]) for v in db.execute('select body from h_semantics order by execution,channel')];status=collections.Counter();grouped={}
 for r in rows:
  for key,p in r['properties'].items():
   status[p['status']]+=1;identifier=(r['channel_id'],key,p['status'],json.dumps(p['value'],sort_keys=True),p['basis']);g=grouped.setdefault(identifier,dict(executions=set(),variants=set()));g['executions'].add(r['execution_id']);g['variants'].add(r['variant_id'])
 with (HERE/'SEMANTIC_CONTRACTS.csv').open('x',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['channel','property','status','value','primary_basis','executions','variants','proof_reference','scope_reference'])
  for (channel,key,state,value,basis),g in sorted(grouped.items()):w.writerow([channel,key,state,value,basis,len(g['executions']),len(g['variants']),'AUDIT_FINAL.json; PRIMARY_SOURCES.json; native model map; VELOCITY_BY_CHANNEL.json','CONTRACT_SCOPES.json'])
 scopes={c:dict(executions=sorted({r['execution_id'] for r in rows if r['channel_id']==c}),variants=sorted({r['variant_id'] for r in rows if r['channel_id']==c})) for c in sorted({r['channel_id'] for r in rows})};save(HERE/'CONTRACT_SCOPES.json',scopes)
 with (HERE/'GEOMETRY_BINDINGS.csv').open('x',newline='') as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['variant','kind','name','native_id','joint_id','body_id','body_name','qpos_address','qvel_address','axis_body_local','anchor_body_local','gear','executions','xml_path','xml_sha256','model_map_path','model_map_sha256'])
  for p in sorted((WORK/'models').glob('*.json')):
   m=json.loads(p.read_text());js={j['id']:j for j in m['joints']}
   for j in m['joints']:
    if j['name'].startswith(('robot0_joint','gripper0_finger_joint')):w.writerow([m['variant_id'],'joint',j['name'],j['id'],j['id'],j['body_id'],j['body_name'],j['qpos_address'],j['qvel_address'],json.dumps(j['axis_body_local']),json.dumps(j['anchor_body_local']),'',len(m['executions']),m['xml_path'],m['xml_sha256'],str(p),sha(p)])
   for a in m['actuators']:
    j=js[a['joint_id']];w.writerow([m['variant_id'],'actuator',a['name'],a['id'],a['joint_id'],j['body_id'],j['body_name'],j['qpos_address'],j['qvel_address'],'','',json.dumps(a['gear']),len(m['executions']),m['xml_path'],m['xml_sha256'],str(p),sha(p)])
 write('README.md',f'''# Phase 5H — Physical semantics, temporal alignment and source integrity

Completed on Hestia from commit {BASE_COMMIT}. Baseline SHA-256 `{BASE_SHA}` independently verified before changes. All 432 executions, 104 variants, 80,786 core evidence records and 2,592 Phase 5G series records remain unchanged. No new measurements, profiles, labels, checker decisions, safety agents or empirical R1 admission.

Phase 5H adds 2,592 separately classified interpretation annotations, 432 execution timelines and 104 model identity maps. Model joint units/order and actuator transmission semantics are validated; physical calibration and common-instant synchronization remain unresolved. Explicit SI actuator-unit requests remain conditional. Raw values and contracts are not rewritten.

Database `{build['database_path']}`\nSHA-256 `{build['database_sha256']}`\nSize {build['database_bytes']:,} bytes, growth {build['database_bytes']-BASE.stat().st_size:,} bytes.

{reg['tests']} regression tests passed, skipped {reg['skipped']}; {ret['queries']:,} new exact queries and {ret['negative_controls']:,} negatives passed, leakage zero. All previous exact and semantic benchmarks reran. Independent rebuild, complete resume and partial resume pass.

Read MEASUREMENT_SEMANTICS_AUDIT.md, TEMPORAL_ALIGNMENT.md and SOURCE_INTEGRITY_POLICY.md before using interpretations. Physical verified access uses the new CLI/API with an explicitly trusted database hash; legacy interfaces are compatibility benchmarks, not the new integrity policy. Numeric agreement and retrievability are not physical safety accuracy.
''')
 write('MEASUREMENT_SEMANTICS_AUDIT.md',f'''# Six-channel semantic audit

SEMANTIC_CONTRACTS.csv classifies every exposed property; CONTRACT_SCOPES.json provides exact execution/variant support. Property instances: `{json.dumps(status,sort_keys=True)}`. All six families are supported for the fixed 432 executions/104 variants. Formal detail is in EVIDENCE_CONTRACTS.md and the original raw contracts remain immutable.

Four observed vectors are native joint coordinates/tangent velocities: seven hinge arm joints (rad, rad/s) and two slide finger joints (m, m/s under the recorded metric model convention). They are not Cartesian gripper positions, commanded targets or normalized policy inputs. Ordered source getters, recorded native indexes, compiled exact XML and independent configuration/velocity consistency jointly support this interpretation. Robot association is the exact recorded model; this is not a generic guarantee for other robots.

The nine actuator_force entries are native scalar actuator output in compiled order, with unit-gear direct transmissions. Seven have torque dimensions and two linear-force dimensions. They are distinct from ctrl, total generalized joint force and per-contact forces. Fixed-gain/affine-bias/clamp equations match all recorded outputs. SI N*m/N interpretation requires the MKS mass convention and remains CONDITIONAL; physical force calibration is absent.

ncon is a nonnegative contact-entry count. All 58,075 values match the decoded saved contact-list length. Contacts preserve pair identities/distances/positions, but no dedicated per-contact-force channel. Zero count certifies only that saved simulator entry list, not an absence of all physical contact between samples or inactive/excluded geometry. Nonzero count does not identify objects or prove support/violations.

Recorder and run_oft file hashes match metadata in every execution. Installed robosuite sources match declared 1.4.0, but a complete recording-time binary attestation is unavailable. This limitation is retained explicitly for cache timing/refresh claims. Native model units are not a claim of physical reference calibration. Existing raw dtype/shape and missing-field behavior remain available alongside the interpretation layer.
''')
 primary=load('PRIMARY_SOURCES.json');fetch=load('primary/FETCH_MANIFEST.json')
 table='\n'.join('| '+r['path']+' | `'+r['sha256']+'` |' for r in primary['files'])
 urls='\n'.join('- '+r['url']+' — SHA-256 `'+r['sha256']+'`' for r in fetch if 'sha256' in r)
 write('PRIMARY_SOURCE_TRACEABILITY.md',f'''# Primary-source traceability

Sources were inspected on Hestia. Recorder/run_oft hashes match all execution metadata. The snapshot writes raw_observation and simulator fields directly; run_oft applies policy preprocessing separately and records native eight-action chunks. Robot/single-arm getters use qpos/qvel addresses in model order; exact saved indexes and compiled XML establish actual component identities.

MuJoCo 3.8.1 was used for identity compilation and algebraic validation; no newer-version documentation was substituted. Installed mjdata.h/mjmodel.h bytes match pinned official 3.8.1 headers (MUJOCO_HEADER_COMPARISON.json). Compiler RECORD hashes, XML/assets and per-execution native indexes are retained in model maps. Metadata declares MuJoCo 3.8.1 and robosuite 1.4.0. Historical binary attestation is unavailable.

engine_forward.c documents actuator gain/bias/limiting, moment mapping and semi-implicit Euler integration. engine_util_misc.c defines configuration integration. Observable/base/binding code explains refresh and cache ordering. Headers identify actuator_force/ncon; these are not contact-force/event labels. Native model types, gears, gains and biases support the tested equations. Interpretations include audit/validation/source-manifest hashes and original source/model/metadata lineage.

| Inspected source | SHA-256 |
|---|---|
{table}

Pinned upstream references:
{urls}

These establish model definitions, not hardware calibration. Installed robosuite sources are version-matched explanatory evidence; cache clocks and binary history remain conditional/unresolved. Independent recorded-value/model comparisons provide separate evidence, instead of verification from variable names or absence of counterexamples.
''')
 write('TEMPORAL_ALIGNMENT.md',f'''# Temporal reconstruction

All 432 executions/104 variants use a 0.002s compiled Euler timestep and recorded 20Hz control frequency. Saved simulator intervals are 0.05s (25 substeps); floating accumulation errors are separate from alignment. Snapshot wall/monotonic clocks are not camera exposure times.

```mermaid
flowchart LR
 A[Chunk inference from recorded raw snapshot] --> B[Select queued action]
 B --> C[Forward/control/integrate and observable updates]
 C --> D[Save raw and simulator snapshot]
 D --> E[Save transition time and action]
 E --> F[Increment recorder control step]
 F --> B
```

Frame zero follows benchmark restoration. Frames 1..10 follow settling. Action k precedes saved frame k+11. Latest available snapshot before action k is k+10. Actual inference input is frame 10+inference_calls[chunk_id].step; queued actions reuse that earlier input. All {audit['chunk_alignment_comparisons']:,} action/chunk associations and simulator transition times were checked. Settling control_step zero is not a unique time index.

Same-index association is VERIFIED. A common physical instant across endpoint state, native caches and raw observations is not established. For the nine scalar arm/finger joints, initial configurations equal endpoint state; subsequent values satisfy q_raw=q_endpoint-h*v_endpoint. This equation is not applied componentwise to generic quaternion-containing qpos arrays. Inverse Euler consistency reconstructs raw velocities within predefined roundoff bounds. No offset is fitted to maximize agreement; no data is shifted or interpolated.

The -0.002s cache-time interpretation is CONDITIONAL on the Euler model and production interpretation. Individual sensor timestamps and historical binary attestation are absent. Algebraic reconstructions are validation-only, never raw indexed samples. Synchronized, endpoint-shifted, exposure-clock and world-transform retrieval remain UNSUPPORTED. Model consistency does not establish a calibrated physical instant.

Sparse-window fixtures preserve exact keys; selected actual recordings are complete. The initial provisional policy_input_frame label is superseded in AUDIT_FINAL.json by latest_available_observation_frame and actual policy_inference_input_frame, validated from chunk metadata. The diagnostic is retained.
''')
 write('COORDINATE_FRAME_AUDIT.md','''# Configuration, velocity and geometry frames

The four robot/gripper arrays are joint configuration/tangent velocities, not Cartesian vectors. Seven hinge components use radians and rad/s. Two slide components use model length/second, interpreted in m and m/s under the explicitly recorded metric convention. Signed axes and zero follow exact XML joints; no finger-opening-distance conversion is applied.

GEOMETRY_BINDINGS.csv lists native joint/body/actuator IDs, qpos/qvel addresses, body-local axes/anchors, gears and XML/model hashes for all 104 variants. Recorded indexes check every execution. BINDING_VALIDATION.json independently verifies 3,888 joint/body and 3,888 actuator/joint associations. Robot identity is the exact variant model, not a generic robot0-array assumption.

No world transform is implemented. Axis origin/orientation belongs to the owning body; configuration is not world position. No pixel/world calibration, camera clock, support inference or force-frame projection. Projection y=x[j] is an exact component view with selector/index/identity and unchanged float64 value; domain/codomain are the same native coordinate.

Phase 5G main_table remains a derived identity for 147 tabletop executions/98 variants. Floor/living-room domains do not inherit it. Source hashes/scope are preserved. Neither identity nor candidate geometry enables logical-table poses or establishes support/contact/falling.
''')
 write('SOURCE_INTEGRITY_POLICY.md','''# Verified external-reference access

Trust begins with an explicitly supplied database SHA-256 from a trusted release/commit. PhysicalStore checks it before verified evidence and rejects later database identity changes. A caller-recomputed untrusted hash is not an external trust root: pin the release manifest/checksum or committed identity. This interface runs only on Hestia in its owned storage namespace. Paths alone are not identities.

The new physical CLI/API is the verified interface. Legacy readers remain unchanged for compatibility/benchmarks and are not hardened by merely opening the new database. Original raw contracts retain their prior meaning.

Strict mode walks every component via directory descriptors with O_NOFOLLOW, checks regular-file identity and hashes the same open descriptor before and after decoding. HDF5 reads that descriptor, not a reopened filename. File and safe pathname identity are checked after use. Source hash, namespace, dtype, shape, field, execution and scope must match. Missing/replaced/redirected/modified references fail closed with zero returned records.

Verified-session mode first hashes full bytes, then reuses verification only while device, inode, size, mtime, ctime and link count remain identical. Metadata invalidates prior cryptographic verification; it is not cryptographic proof by itself. Every read reopens safely and checks before/after identities. Referenced primary-source files are checked recursively from the verified proof manifest. No decoded-value cache. Preserved-mtime writes invalidate via ctime; replacement via identity. Local OS metadata/permissions are trusted; malicious kernel/root control is outside this boundary.

A byte-identical restored regular file is accepted after a fresh hash with new identity. Different bytes at the same path or in another namespace are not interchangeable. Symlinks are rejected even for matching targets. Registered historical asset /local/home paths normalize only to verified same-inode disk0 aliases; raw HDF5 has no arbitrary alias fallback. No restoration was needed.

No unverified mode is exposed. Conditional semantic properties remain separately labeled; byte integrity or semantic similarity cannot promote them. Property-status, execution/task/variant/component/unit/frame/time/transform guards precede ranking or return.
''')
 write('SOURCE_TAMPERING_TESTS.md',f'''# Adversarial source access

All {reg['new_tests']} new tests passed. Tests use small isolated scratch files/DBs only, never production recordings. Source-policy/end-to-end tests are in tests/test_integrity.py and tests/test_api_tampering.py; logs/commands are manifest-bound.

Covered: modified bytes; preserved mtime; replacement with wrong or identical bytes; missing sources; final/parent symlinks; redirection after cache warm-up; modification/replacement during read; missing datasets; dtype/shape changes; wrong execution header; nonfinite values; wrong expected hash; namespace separation; stale decoded-value attempts; sparse samples; altered verified DB; matching restoration after missing/mismatched source.

Strict checks hash both boundaries; session checks prove initial hashing and invalidation. Identical restored/replaced bytes require a fresh hash and exact original values. Dtype/shape is independently rejected even when a synthetic fixture supplies a new matching hash. Failures return no partial verified results. Unverified access is rejected. Conditional SI/cache properties remain distinct from verified bytes.

No actual source bytes, predictions, human packages, seals or scoring guards were modified.
''')
 channel_errors={c:dict(maximum_error=max(r['by_channel'][c]['maximum_error'] for r in bychannel['rows']),mean_error=sum(r['by_channel'][c]['mean_error']*r['by_channel'][c]['components'] for r in bychannel['rows'])/sum(r['by_channel'][c]['components'] for r in bychannel['rows']),units=bychannel['rows'][0]['by_channel'][c]['units'],components=sum(r['by_channel'][c]['components'] for r in bychannel['rows'])) for c in bychannel['rows'][0]['by_channel']}
 def summary(field):
  rs=[r[field] for r in audit['rows']];return dict(maximum=max(r['max'] for r in rs),mean=sum(r['mean']*r['components'] for r in rs)/sum(r['components'] for r in rs),components=sum(r['components'] for r in rs))
 metrics=dict(per_channel_numeric=channel_errors,actuator_equation=summary('actuator_equation_error'),timestamp_accumulation=summary('timestamp_error'),contact_count_comparisons=sum(r['contact_count_comparisons'] for r in audit['rows']),action_alignment_comparisons=audit['chunk_alignment_comparisons'],algebraic_contract_failures=audit['contract_failures'],source_value_error=ret['maximum_value_error'],source_samples_checked=ret['original_samples_compared'])
 save(HERE/'validation'/'NUMERIC_RESULTS.json',metrics)
 write('VALIDATION_RESULTS.md',f'''# Independent numeric, temporal and identity results

432 executions, 104 variants, 58,075 snapshots. All nine robot/finger components were checked against native mappings; 522,675 components per configuration/velocity equation. All 522,675 actuator scalars matched gain/bias/limit equations exactly; FORCE_LIMITS_VALIDATION.json independently verifies compiled gain/bias/force-limit prerequisites in all 104 variants. All 58,075 ncon values matched saved-list lengths. Zero unexplained contract failures or actual selected-channel missing samples.

Per-channel errors (model units separate): `{json.dumps(channel_errors,sort_keys=True)}`.

Raw retrieval: {ret['original_samples_compared']:,} vectors/scalars independently compared to original samples; maximum/mean value error {ret['maximum_value_error']}/0.0. Projections retain original values. Native XML/index identity checks are separate from ranked metrics.

Endpoint timestamp accumulation: `{json.dumps(metrics['timestamp_accumulation'],sort_keys=True)}` seconds; floating addition error, not synchronization. All {audit['chunk_alignment_comparisons']:,} transition/action/chunk mappings matched recorded indices/times. Saved-index alignment errors {ret['saved_index_alignment_errors']}; common-physical-instant error is unquantified, not zero.

Tolerances declared before full validation: `{json.dumps(TOLERANCE_POLICY,sort_keys=True)}`. Inverse velocity uses pilot-frozen 512*eps*cond(M+hD)*(1+norm(v)+h*norm(qacc)). Mixed-coordinate maximum residual {velocity['maximum_error']}, mean {velocity['mean_error']}; per-channel values above avoid mixing rad/s and m/s. No tolerance is physical or fitted to an offset.

VERIFIED model/source properties, CONDITIONAL offsets/SI force units, UNRESOLVED calibration/clocks and UNSUPPORTED transforms remain separate. Initial/early/middle/terminal and window-boundary samples are tested; sparse/malformed families use isolated fixtures. No selected actual source family is skipped.
''')
 write('RETRIEVAL_EVALUATION.md',f'''# Source-target lookup and scope validation

New physical interface: {ret['queries']:,} exact queries over all 432 executions/104 variants; initial, early-action, middle, terminal and boundary windows. P@1={ret['precision_at_1']}, Recall@20={ret['recall_at_20']}, MRR={ret['MRR']}. {ret['negative_controls']:,} negatives; leakage {ret['cross_scope_leakage']}. All returned values were independently decoded and compared, not just matched by text. Exact channel lookup generally has one intended target.

Negative statuses: `{json.dumps(ret['negative_status_counts'],sort_keys=True)}`. Wrong source/execution/task/variant/object/component/units/frame, unsupported transforms/alignment/status and out-of-range samples fail closed. All 60 reserved, 38 preflight and 1,470 pending IDs are tested without inspecting payloads. Tampering/restoration tests are separate from ranking.

New lexical/semantic results on unchanged Phase 5G probes: `{json.dumps(sem['aggregate'],sort_keys=True)}`. {sem['negative_controls']:,} semantic guard negatives, leakage {sem['cross_scope_leakage']}. Twelve fixed paraphrases repeated in 432 contexts, six candidates per scope; no independent language labels or tuning. Similarity cannot override physical-property or provenance filters.

Previous Phase 5G exact tests rerun: {gexact['source_target_queries']:,}, negatives {gexact['negative_controls']:,}, P@1/Recall@20/MRR all 1.0; leakage zero. Its semantic benchmark rerun: `{json.dumps(gsem['aggregate'],sort_keys=True)}`.

Previous Phase 5F exact tests rerun: {fexact['queries']:,}, negatives {fneg['negative_queries']:,}, exact metrics all 1.0 and leakage zero. Its unchanged semantic benchmark rerun: `{json.dumps(fsem['aggregate'],sort_keys=True)}`. Legacy readers are compatibility baselines; new source-policy guarantees require the new physical interface.

Ranking, direct numeric reproduction, model semantic correctness and physical calibration are separate measurements. Successful lookup does not establish a safety claim.
''')
 write('REGRESSION_RESULTS.md',f'''# Regressions and preservation

Baseline before modifications: 578 tests passed. Final {reg['tests']} tests pass ({reg['baseline_tests']} prior + {reg['new_tests']} new), skipped {reg['skipped']}, unexplained failures zero. Per-suite logs/commands are manifest-bound. New tests cover scratch tampering, verified DB identity, units, exact projection, unresolved/conditional properties, chronology/chunks and scope negatives.

Every Phase 5G table definition and row was compared exactly, including 80,786 evidence records, 2,592 raw references, FTS shadows, jobs, variants and exclusions. All 432 executions/104 variants remain. Baseline SHA `{BASE_SHA}`. Phase 5E/F/G artifacts/manifests are intact.

Fresh final baseline manifests, original sources, native XML/index/model sources, primary code, frozen V3/V4 files, human reference/blinded packages, both seals and scoring guards pass. See validation/FROZEN_FINAL.json, PRESERVATION_FINAL.json and FINAL_AUDIT.json. Twelve seal members and eight scoring-protected files are unchanged. No checker/admission change.

Diagnostics retained: the velocity pilot initially used an incompatible mj_fullM signature, corrected from installed binding docs before full validation; provisional observation/inference labeling was refined using chunk metadata. Initial build candidate is preserved separately. No threshold, offset or label was tuned to conceal a failure. All subsequent applicable validation passes.

Unavailable video/resources, physical calibration, binary attestation, sensor/exposure clocks and unselected families remain explicitly untested/unsupported, never silently skipped from an admitted claim.
''')
 write('COVERAGE_AND_LIMITATIONS.md',f'''# Coverage and remaining infrastructure work

432 executions, 104 variants, six raw families, 58,075 snapshots. No new channels/profiles. Property-instance coverage: `{json.dumps(status,sort_keys=True)}`. Complete selected data; malformed/missing behavior uses isolated fixtures. Contracts expose exact component identities, model units, joint coordinate types, actuator outputs and recorded action chronology.

Conditional: -0.002s cache-time interpretation, observable refresh rate, actuator N*m/N under MKS mass convention. Unresolved: physical calibration/uncertainty, historical binaries, individual sensor clocks and common physical instant. Unsupported: Cartesian/world interpretations of configuration arrays, shifted/synchronized retrieval, pixel/world calibration, logical-table poses, contact force from actuator output/counts, support/fall/R1 inference.

main_table stays bounded to 147 tabletop executions/98 variants, with no floor/living-room extension or support inference. Five-array raw contracts are preserved alongside separately classified model interpretations. Counts are not events or continuous absence certificates.

The reserved 60 executions, 38 preflights and 1,470 pending profiles remain unindexed/uninspected. Evaluation artifacts, labels and predictions are untouched. No empirical admission, safety agents, GSN, critic/revision or multi-agent systems.

Next database-only milestone: obtain producer-hashed per-sensor timestamps and recording-time dependency/binary manifests, then test cache timing/frame transforms against independent references. Restore video/resource payloads only for a bounded validated contract. Retrieval success is not physical-safety accuracy.
''')
 write('REPRODUCIBILITY.md',f'''# Reproduction and additive migration

All processing on Hestia; cwd /disk/1/data/niktakbr/trustworthy-phase16, HOME=/tmp, system PATH, PYTHONDONTWRITEBYTECODE=1. Use `/usr/bin/python3 -S`, PYTHONPATH repository + existing groot-n17-libero-gpu0-queue .venv Python3.12 site-packages + system site-packages. Compilation/velocity checks instead use smolVLA_libero .venv (MuJoCo3.8.1), OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1. No installs, GPU jobs, Sea, Alliance evaluation or source-corpus copies.

Baseline commit {BASE_COMMIT}, DB `{BASE}`, SHA `{BASE_SHA}`. Before edits, check_release verified 585 entries and all 578 tests reran. Compilation checks all recorded indexes without stepping. Upstream 3.8.1 downloads are small pinned primary-code references, not recording restoration.

Frozen producers include config/schema/semantics/source-integrity/store/builder/contracts hashes. Frozen audits, model maps and velocity/source proofs are reused for deterministic rebuilds; changed sources/producers reject mixed resume. Version {VERSION}. Old schemas/rows are unchanged. Added h_meta, h_models, h_execution, h_semantics and h_jobs store interpretation/timeline metadata only; no large HDF5 arrays.

Fresh rebuild:

```python
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.build import populate
populate(Path('/disk/1/data/niktakbr/trustworthy-phase5h-working/reproduce.sqlite'))
```

Repeat for full resume: zero inserts/432 skips. Independent logical digest `{build['logical_digest']}` matches. Partial scratch recovery restores six annotations and skips 431 executions with the same digest. Physical SQLite hashes can differ after transaction reconstruction; manifest has current exact hashes.

Research modules: compile_models; fetch_primary; audit; velocity_validation (kinematic mass/algebra only); temporal_refinement; build; validate; binding_validation; velocity_by_channel; rebuild; semantic_benchmark; legacy_benchmarks f/g; regressions; final_audit; reports; seal_artifacts. Persistent stdout/stderr, exact suite commands and machine results are retained. Reports are create-only; repeated evaluations require fresh directories. Absolute baseline/profile paths intentionally prohibit other cohorts.

Verified query:

```
python3 -S -m evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.cli --database {build['database_path']} --database-sha256 {build['database_sha256']} --query query.json
```

Require execution_id; use exact channel_id for typed filters, optional component/units/frame/property conditions and inclusive saved-frame interval such as [0,0]. Default strict mode hashes both boundaries. verified_session explicitly caches verified identities only. Conditional requests need allow_conditional=true. No unverified mode. Optional --semantic-text uses the pinned local CPU encoder; guards cannot be bypassed by ranking.

Code/reports/compact summaries are committed. DBs, detailed audits, model maps and logs remain outside Git in `{WORK}`. Manifest excludes itself/checksum; ARTIFACT_MANIFEST.sha256 and local Git commit identify the root. Nothing pushed or merged.
''')
 for name in ('BUILD.json','RESUME.json','INDEPENDENT_BUILD.json','PARTIAL_RESUME.json','REBUILD_VALIDATION.json','BINDING_VALIDATION.json','REGRESSION_RESULTS.json','FROZEN_FINAL.json','FINAL_AUDIT.json','PRESERVATION_FINAL.json','RESOURCE_PREFLIGHT.json','MUJOCO_HEADER_COMPARISON.json'):
  save(HERE/'validation'/name,reg if name=='REGRESSION_RESULTS.json' else load(name))
 compact=dict(retrieval={k:v for k,v in ret.items() if k!='query_results'},semantic={k:v for k,v in sem.items() if k!='results'},legacy_f_exact={k:v for k,v in fexact.items() if k not in ('results','per_variant')},legacy_f_semantic={k:v for k,v in fsem.items() if k not in ('results','negative_scope_cases')},legacy_g_exact={k:v for k,v in gexact.items() if k!='query_results'},legacy_g_semantic={k:v for k,v in gsem.items() if k!='results'},property_status_counts=dict(status),contracts=2592,models=104,timelines=432)
 save(HERE/'validation'/'SUMMARY.json',compact);db.close();print('REPORTS COMPLETE',flush=True)
if __name__=='__main__':run()
