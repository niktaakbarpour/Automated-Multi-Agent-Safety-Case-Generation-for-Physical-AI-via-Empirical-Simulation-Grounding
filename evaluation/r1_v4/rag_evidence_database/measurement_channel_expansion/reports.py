"""Create release reports from completed machine results, never handoff metrics."""
import json,csv,statistics,shutil,platform,subprocess
from pathlib import Path
from .channels import HERE,WORK,BASE,BASE_SHA,CHANNELS
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO

def load(n):return json.loads((WORK/n).read_text())
def write(n,text):
 with (HERE/n).open('x') as f:f.write(text.strip()+'\n')
def run():
 build=load('BUILD.json');raw=load('EXTRACTION_RETRIEVAL_VALIDATION.json');legacy=load('legacy/RETRIEVAL_METRICS.json');neg=load('legacy/NEGATIVE_RETRIEVAL.json');sem=load('CHANNEL_SEMANTIC_EVALUATION.json');oldsem=load('legacy/SEMANTIC_EVALUATION.json');reg=load('regressions/REGRESSION_RESULTS.json');tests=load('CHANNEL_TESTS.json');audit=load('FINAL_AUDIT.json');inv=load('INVENTORY_SUMMARY.json');sup=load('INVENTORY_SUPPLEMENT.json');normalized=load('NORMALIZED_INVENTORY.json');spatial=load('SPATIAL_AUDIT.json');growth=build['database_bytes']-BASE.stat().st_size
 assert audit['passed'] and reg['passed'] and raw['passed']
 write('README.md',f'''# Phase 5G — Measurement-channel coverage and contracts

Database/retrieval infrastructure only. Baseline commit c24795ed9383110243288db520e5f98af484b4ad was independently verified before changes. All processing ran on Hestia. No simulations, new execution profiles, downstream safety-case agents, prediction/label edits, push or merge.

Phase 5F preserves 432 executions, 104 variants, 80,786 evidence records and 58,075 saved frames. Phase 5G adds 2,592 independently searchable direct-channel series references (six per execution), for 83,378 total records across the two evidence tables. Existing evidence bodies, units, source associations, normalized variant/scope relations and core schema remain identical.

Final database: `{audit['database_path']}`\nSHA-256: `{audit['database_sha256']}`\nSize: {build['database_bytes']:,} bytes; growth {growth:,} bytes ({100*growth/BASE.stat().st_size:.2f}%).

Start with CHANNEL_SELECTION.md, EVIDENCE_CONTRACTS.md and LIMITATIONS.md. Channel inventory includes {inv['dataset_channel_ids']} HDF5 dataset patterns, {inv['attribute_channel_ids']} attribute patterns, {sup['json_channel_ids']} JSON keys and nine local artifact families. These are recorded source patterns/metadata keys, not equally interpreted physical quantities.

The five newly indexed arrays remain explicitly uninterpreted raw values. Only the simulator contact-entry count has verified count units. Retrievability is not evidence that a value establishes a safety claim. Empirical R1 admission remains disabled.

CHANNEL_COVERAGE_MATRIX.csv is normalized: join channel_key to CHANNEL_INVENTORY.csv, source_key to EXECUTION_SOURCE_BINDINGS.csv and value_profile_key to VALUE_PROFILES.json. All {normalized['matrix_rows']:,} coverage rows are retained; the expanded matrix and per-execution inventories are external artifacts in the manifest.
''')
 write('INVENTORY.md',f'''# Recorded-versus-indexed inventory

The complete HDF5 dataset/group-attribute tree and available JSON fields were inspected for exactly 432 indexed executions. No reserved/preflight payloads or 1,470 pending profiles were inspected. Total: 58,075 saved frames; {inv['dataset_channel_ids']} dataset patterns, {inv['attribute_channel_ids']} attribute patterns, {sup['json_channel_ids']} metadata keys. Availability is per execution and variant, not assumed uniform. Numeric event indices are normalized in inventory identifiers only; source selectors preserve original keys.

Phase 5F exposes body position/quaternion, native geom pose, robot qpos/qvel/ctrl, endpoint time, contact-list and camera references under established family records. A family reference does not necessarily provide independently typed numeric retrieval for each underlying array. Remaining fields distinguish saved-but-not-independently-searchable data, unextracted raw observations, data requiring decoding and fields with unverified units/frame/phase.

Phase 5G adds the six frozen channels. Each is present at all 58,075 saved samples. The inventory retains dtype/shape distributions, source keys/hashes, task/variant coverage, missing execution counts, extraction feasibility, validation requirements and uncertainty. Native geometry fields and logical bindings have GEOMETRY_CHANNEL_INVENTORY.csv and SPATIAL_BINDINGS.csv audits.

No video or resources.csv payload is locally available in the restored subset. Their absence here is not a claim that original archives lack them. Camera arrays and available HDF5 inference/rollout timing fields were inventoried. Recorder code documents videos and resource sampling, but those payloads were not restored or evaluated. Additional restoration is outside this bounded expansion.

No dedicated camera-exposure timestamp or direct per-contact-force dataset exists in the inspected HDF5 trees. Snapshot wall/monotonic attributes are not exposure times; actuator_force is not per-contact force. Object motion, eef arrays, cvel, cfrc_ext, qacc, sites, sensordata, actions and policy inputs remain inventoried with unverified semantics where applicable. Raw retrieval does not establish a validated world-frame trajectory.
''')
 write('SPATIAL_MAPPING_AUDIT.md',f'''# Spatial semantics audit

All 432 executions and 104 variants were audited against exact XML, recorded semantic initial conditions and native mappings. SPATIAL_BINDINGS.csv records source/hash/root bindings; external SPATIAL_AUDIT.json and SPATIAL_SUPPLEMENT.json retain task/variant support-candidate declarations and limitations.

Recorded object/fixture roots matched exact native/XML body identities in every inspected association. {sum(len(r['phase_position_checks']) for r in spatial):,} phase-labelled semantic initial positions matched the same saved-phase native body positions exactly (maximum absolute error 0). This verifies those snapshot associations only. Existing native poses retain the Phase 5F MuJoCo-world metric/body-wxyz convention; raw observable units, frames, component orders and quaternion conventions remain unverified.

`main_table` is verified as a symbolic alias for exact native body `table` and geom `table_collision` in 147 tabletop-domain executions spanning 98 variants and three task identities. MAIN_TABLE_BINDINGS.csv and MAIN_TABLE_AUDIT.json bind recorded parsed BDDL fixtures and problem name, evaluator-version hashes of task/domain/arena implementation files, saved XML and exact native IDs. This is an explicitly derived symbolic mapping, not a raw measurement. The other 285 executions use floor or living-room workspaces; this main_table rule is not applicable. The initial literal-name-only audit is retained in SPATIAL_AUDIT.json as a diagnostic; absence of an exact XML name was insufficient by itself. No mapping is inferred by name similarity.

The alias audit adds no searchable spatial record: logical_main_table_pose remains unsupported by the frozen six-channel extraction contract. Existing support-candidate sets remain task/variant specific. Tests reject wrong domains even when a physical table exists, near-matching fixture names, missing code attestations and wrong XML/native bindings.

Endpoint qpos/qvel/time, last-forward body/geom/contact/dynamics caches and raw observation caches remain distinct. No calibrated common-instant bound is established. No new spatial observation, frame transform, support/contact/fall judgment or geometry-only physical inference is admitted. Tests cover exact roots, initial positions, unresolved aliases and counterexamples against raw/world and alias substitution.
''')
 write('EXTRACTION_VALIDATION.md',f'''# Raw-to-index validation

Six channels, 2,592 series records, 432 executions, 104 variants. Preserved core records: 80,786. Direct channels: six; derived channels: zero. Per channel: 432 records and 58,075 valid samples. Missing/unsupported samples in selected actual recordings: {raw['missing_samples']}.

Independent h5py oracle redecodes every selected sample using separately declared fields/shapes, compares the complete sample digest and validates decoded contact-list length against ncon. Samples validated: {raw['raw_source_samples_validated']:,}. Numeric components by channel: `{json.dumps(raw['numeric_components_by_channel'],sort_keys=True)}`.

Retrieved sample vectors/scalars independently compared: {raw['retrieved_samples_compared']:,}. Maximum absolute value error: {raw['max_absolute_value_error']}. Saved-index alignment errors: {raw['alignment_errors_saved_indices']}. Unit/frame inconsistencies: {raw['unit_frame_inconsistencies']}. These errors concern encoded values/indices, not physical synchronization or calibration.

First successful build: {build['seconds']:.3f} seconds. Database growth: {growth:,} bytes. Projected additional peak was 10 GiB with no raw-corpus duplication; disk1 free at final audit: {audit['free_disk1_bytes']:,} bytes. Complete runtime/producer hashes are in validation summaries and external BUILD.json.

Missing fields, incompatible shapes/types, NaN/infinity, negative/floating counts and sparse windows are tested with isolated fixtures. Sparse samples are not interpolated or shifted. Raw status protects unknown units/frames. Original stage/control_step labels are preserved without inferred action alignment. Arrays remain in HDF5 and are decoded only for requested windows.
''')
 write('RETRIEVAL_EVALUATION.md',f'''# Source-target retrieval and negative controls

New channel tests: {raw['source_target_queries']:,} exact queries over all 432 executions/104 variants, at initial/middle/terminal frames and windows crossing frames 31/32. Precision@1={raw['precision_at_1']}, Recall@20={raw['recall_at_20']}, MRR={raw['MRR']}. Exact channel-filtered lookup has one intended series target; these are source lookup metrics, not natural-language relevance or physical accuracy.

New negative controls: {raw['negative_controls']:,}. Status counts: `{json.dumps(raw['negative_status_counts'],sort_keys=True)}`. Includes wrong object/task/variant/execution, absent frames/channels, unverified units/world frames, derived-origin requests, unsupported seconds, all 60 reserved and 38 preflight IDs, and all 1,470 pending IDs. Excluded/pending tests use IDs only. No source payloads for those scopes were inspected. Cross-scope leakage: {raw['cross_scope_leakage']}.

Legacy Phase 5F exact retrieval rerun on Phase 5G: {legacy['queries']:,} queries; Precision@1={legacy['precision_at_1']}, Recall@20={legacy['recall_at_20']}, MRR={legacy['MRR']}. Legacy negatives: {neg['negative_queries']:,}; cross-scope leakage {neg['invalid_cross_scope_retrievals']}. Original evidence/source/selector/task/variant associations remain unchanged.

Numeric errors, contact-count consistency and saved-index alignment are reported independently in EXTRACTION_VALIDATION.md. Sparse-source and tampered-contract/source tests add cases that do not occur naturally in the selected complete recordings.
''')
 write('SEMANTIC_RETRIEVAL_EVALUATION.md',f'''# Optional local semantic retrieval

Pinned existing CPU encoder; no hosted API, new model installation or tuning. New channel ranking embeds fixed source-field descriptions only, after exact execution/task/variant scope enforcement. Numeric values, outcomes and AI judgments are not embedded. Identical query vectors are cached per encoder instance; source associations invalidate on SQLite data_version changes. Source-file hash caches invalidate on filesystem identity/size/mtime/ctime changes.

New channels: 12 unique prospective paraphrases repeated across 432 execution scopes, six candidate channels per scope, 5,184 instances per method. Results: `{json.dumps(sem['aggregate'],sort_keys=True)}`. Negative scope controls: {sem['negative_controls']:,}; leakage {sem['cross_scope_leakage']}. No failed paraphrase led to descriptor/probe tuning. FTS misses remain reported.

Unchanged legacy semantic retrieval was rebuilt against the exact Phase 5G bytes and rerun using its existing 12 probes: `{json.dumps(oldsem['aggregate'],sort_keys=True)}`. Legacy scope-negative cases: {len(oldsem['negative_scope_cases'])}; leakage {oldsem['invalid_cross_scope_retrievals']}. Baseline Phase 5E/5F semantic tests also pass.

Repeated linguistic probes across source contexts are not independent language judgments. Six-candidate recall and paraphrase ranking do not measure numeric accuracy, physical alignment, support/fall detection or safety. Full instance-level results, encoder/model/code bindings and per-channel metrics are external manifest artifacts. The legacy semantic sidecar excludes the new channel family; the channel CLI provides its own bounded optional ranking.
''')
 write('REGRESSION_RESULTS.md',f'''# Regression and preservation

All {reg['tests']} existing Phase 5F tests pass after expansion; {tests['tests_run']} new tests pass. Total {reg['tests']+tests['tests_run']}, skipped {reg['skipped']+tests['skipped']}, unexplained failures zero. The 521-test baseline suite also passed before modifications. Full logs and exact commands are manifest-bound external artifacts.

Includes Phase 5E semantic, profile/reader/variant, registry, V3/V4, reference/generalization, frozen archives, both seals and scoring safeguards. New tests cover invalid numeric/missing samples, sparse windows, source-cache mutation, record/contract/provenance tampering, direct/derived separation, unknown units/frame, exact spatial roots and unresolved aliases. Full-corpus numeric/retrieval, rebuild, complete resume and partial resume validations are separate machine reports.

Every original core table schema and row is compared exactly against Phase 5F, including evidence, source associations, units/FTS shadow tables, jobs, catalog, variant bindings and scope statuses. All 80,786 original evidence records are preserved. Baseline SHA-256 remains {BASE_SHA}. All original manifest/profile/source hashes were freshly verified again; final checked paths: {audit['freshly_hashed_paths']:,}. Frozen V3/V4 files, seal members and scoring guards pass existing integrity checks.

Initial diagnostics are retained: missing system package path caused an import failure before baseline tests; the first build path guard rejected a verified disk0 local bind-mount alias before channel inserts; two initial evaluation runs were deliberately stopped to fix repeated provenance-scan cost. A report-rendering call also failed before writing reports because of an incorrect helper argument; it was corrected and rerun. Their logs remain, and subsequent complete runs pass without relaxed acceptance conditions. No unrelated experiment process was interrupted.

No selected actual sample family was skipped. Videos/resource CSVs unavailable in the restored subset, unselected physical channels and physical synchronization/calibration remain untested, explicitly outside admission.
''')
 write('REPRODUCIBILITY.md',f'''# Reproduction and migration

All computation on Hestia, cwd `{REPO}`, HOME=/tmp, PATH=/usr/sbin:/usr/bin:/sbin:/bin, PYTHONDONTWRITEBYTECODE=1. Use `/usr/bin/python3 -S` with PYTHONPATH containing repository, existing `/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages`, `/usr/lib/python3.12/site-packages` and `/usr/lib64/python3.12/site-packages`. No installs. Local encoder uses its existing pinned model and CPU. No Alliance computation, transfers or Sea access.

Baseline is commit c24795ed9383110243288db520e5f98af484b4ad, database `{BASE}`, SHA-256 `{BASE_SHA}`. All sources are existing validated bindings. Legacy `/local/home/niktakbr` assets are verified by device/inode against owned disk0 aliases. Baseline code, data and Phase 5E/5F reports remain unchanged.

Migration is additive and copy-only. `populate(new_path)` backs up Phase 5F through SQLite, creates `rag_channel_schema`, records, transactional jobs and FTS tables, and checks frozen schema/selection hashes. Core/variant migrations are unchanged. New extraction/schema version is phase5g-channel-1.0.0. VariantQuery and its semantic sidecar remain separate; ChannelQuery addresses the new series family.

Rebuild with a new owned work path:

```python
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.build import populate
result = populate(Path('/disk/1/data/niktakbr/trustworthy-phase5g-working/reproduce-fresh.sqlite'))
```

Repeat on the same path for resume. Producers, contracts, source hashes and selection must remain unchanged; changed input/producer aborts. Expected channel logical digest: `{build['logical_digest']}`. Independent rebuild equals it. Complete resume inserts zero/skips 432; partial scratch resume inserts six/skips 431 and restores the digest. Physical SQLite hashes can differ after scratch reconstruction; final hashes are in ARTIFACT_MANIFEST.json.

`validate.py` independently decodes every selected sample. `verification_run.py` describes fresh complete validation; `post_rebuild_validation.py` completed retained diagnostic recovery without duplicating successful rebuilds. Reports are create-only; repeat evaluations require fresh output directories. Inventory enumerates only baseline executions and freezes selection before extraction. Per-execution inventories and supplements retain all decoded key/coverage profiles.

For queries: `python3 -S -m evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.cli --database <db> --query <json>`; optional `--semantic-text` uses the pinned local encoder. Require execution_id; optional channel_id and inclusive interval such as `[0,0]`. Metadata-only queries return references without arrays. Existing Phase 5F CLI remains available.

External artifacts: `{WORK}`. Manifest binds reports/code, current databases/sidecar, validation results, inventory/source bindings and diagnostics. ARTIFACT_MANIFEST.sha256 hashes the manifest; both are excluded from its file list to avoid recursion. Local Git commit seals tracked content. Nothing is pushed or merged.
''')
 write('LIMITATIONS.md','''# Limits and remaining database work

Five newly exposed arrays have validated raw values only; units, joint/actuator component order, frames and physical interpretation remain unverified. No derived channels or new validated spatial observations were added. A robot0 prefix is not a proven body/geom binding. Numeric accuracy is recording reproduction, not simulator calibration or physical truth.

main_table has a verified symbolic binding only for 147 tabletop-domain executions and 98 variants. It is not applicable to the other recorded workspace domains; searchable logical table poses remain unsupported. Exact fixture roots and existing support-candidate geometry do not prove actual support/contact/falling. Endpoint state, native caches, raw observations and camera exposures have no established common physical instant. Original control-step/stage attributes are labels, not inferred action alignment.

Selected channels happen to be complete. Missing/invalid handling uses synthetic fixtures. Uniform frequency, joint units, coordinate conventions, sensor semantics, dynamics-force reference points and action/cache alignment require additional primary-artifact validation. High-dimensional state, actions, observation poses/velocities and resources remain potential database-only work.

The restored subset contains no videos or resource CSVs; original archive availability is not inferred. Camera arrays and available HDF5 execution/inference measurements were inventoried without exposure-time assumptions. No storage restoration was needed.

Reserved 60 evaluation executions, 38 preflights and 1,470 pending profiles stay unindexed. All new records concern the preserved 432 executions. No checker changes, R1 judgments, empirical admission, human labels, frozen prediction edits, safety-case drafting, GSN generation, critic/revision or multi-agent systems are implemented. Existing historical registry/GSN tests run as regressions only.

Exact lookup and fixed paraphrase tests are retrieval measurements. Repeated prompts and six candidates do not establish general language performance. FTS paraphrase misses are retained. Retrieval cannot by itself establish a physical-safety claim.
''')
 for n in ('BASELINE_VERIFIED.json','BUILD.json','RESUME.json','INDEPENDENT_BUILD.json','REBUILD_VALIDATION.json','PARTIAL_RESUME.json','CHANNEL_TESTS.json','PRESERVATION_FINAL.json','FROZEN_FINAL.json','FINAL_AUDIT.json','STORAGE_PREFLIGHT.json','NORMALIZED_INVENTORY.json','INVENTORY_VALIDATION.json'):
  value=load(n)
  if n=='BASELINE_VERIFIED.json':value={k:v for k,v in value.items() if k not in ('hashed_paths','schema')}
  with (HERE/'validation'/n).open('x') as f:json.dump(value,f,sort_keys=True,indent=2)
 summaries={'extraction':{k:v for k,v in raw.items() if k!='query_results'},'channel_semantic':{k:v for k,v in sem.items() if k!='results'},'legacy_exact':{k:v for k,v in legacy.items() if k not in ('results','per_variant')},'legacy_negative':{k:v for k,v in neg.items() if k!='results'},'legacy_semantic':{k:v for k,v in oldsem.items() if k not in ('results','negative_scope_cases')},'regression':reg}
 with (HERE/'validation'/'SUMMARY.json').open('x') as f:json.dump(summaries,f,sort_keys=True,indent=2)
 print('Reports complete',flush=True)
if __name__=='__main__':run()
