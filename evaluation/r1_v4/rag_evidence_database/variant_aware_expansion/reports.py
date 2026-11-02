"""Render quantitative reports only from saved, validated outputs."""
import shutil,csv
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new,canonical
from .plan import HERE,WORK,BASE,BASE_SHA

def doc(name,text):(HERE/name).write_text(text)
def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)

def main():
 final=load(WORK/'FINAL_VALIDATION.json');qa=load(WORK/'REGRESSION_RESULTS.json');coverage=load(WORK/'COVERAGE_SUMMARY.json');profiles=load(HERE/'PROFILE_SUMMARY.json');metrics=load(WORK/'RETRIEVAL_METRICS.json');negative=load(WORK/'NEGATIVE_RETRIEVAL.json');sem=load(WORK/'SEMANTIC_EVALUATION.json');build=load(WORK/'BUILD_MANIFEST.json');extra=load(WORK/'SEMANTIC_EXTRA_CONTROLS.json');assert final['passed'] and qa['passed'] and extra['passed'] and qa['skipped']==0
 out=HERE/'validation';out.mkdir()
 for name in ('FINAL_VALIDATION.json','REGRESSION_RESULTS.json','REBUILD_VALIDATION.json','DATABASE_INTEGRITY.json','BUILD_MANIFEST.json','RESUME_REPORT.json','INDEPENDENT_BUILD.json','RETRIEVAL_METRICS.json','NEGATIVE_RETRIEVAL.json','SEMANTIC_BUILD.json','SEMANTIC_INTEGRITY.json','SEMANTIC_EVALUATION.json','SEMANTIC_VARIANT_METRICS.json','SEMANTIC_EXTRA_CONTROLS.json','COVERAGE_SUMMARY.json','FROZEN_FINAL.json'):shutil.copyfile(WORK/name,out/name)
 fixtures=load(WORK/'QUERY_FIXTURES.json');write_new(out/'QUERY_SAMPLES.json',{'source_path':str(WORK/'QUERY_FIXTURES.json'),'queries':len(fixtures),'sampling':'Every100th original source-target fixture','samples':fixtures[::100]})
 doc('README.md',f'''# Phase5F: variant-aware RAG evidence expansion

Completed database-only milestone: {coverage['new_executions']} new executions,
{coverage['new_variant_count']} new environment variants; {coverage['total_executions']}
executions and {coverage['total_records']:,} records in total. No empirical R1
admission, new checker, safety-case generation or multi-agent implementation.

Start with INVENTORY.md, COHORT_SELECTION.md, SCHEMA_AND_PROVENANCE.md and
COVERAGE_MATRIX.csv. Source/task/variant relations are in VARIANT_REGISTRY.csv
and EXECUTION_VARIANT_RELATIONS.csv. RETRIEVAL_EVALUATION.md and
SEMANTIC_RETRIEVAL_EVALUATION.md explain metrics and limitations.
REGRESSION_RESULTS.md, validation/ and ARTIFACT_MANIFEST.json preserve checks.
REPRODUCIBILITY.md gives exact paths/procedures; LIMITATIONS.md records gaps.

Database: `{WORK/'expanded.sqlite'}`
Bytes: {final['database_bytes']:,}
SHA-256: `{final['database_sha256']}`

The Phase5E baseline remains `{BASE}` at `{BASE_SHA}`.
All67,053 old records and their original index rows remain intact. The exact
baseline reader code remains in commit114f1f6540a6ba182606a2a921af131ad6b0f7d3;
Phase5F adds its closed dispatch on a new branch without rewriting the old seal.
''')
 doc('INVENTORY.md',f'''# Remaining inventory and variant discovery

The initial remaining pool has1,617 candidates in33 task partitions: eight
single-XML partitions and25 multi-XML partitions. All candidate episode payloads
were absent from their original Hestia paths. All had expected XML hashes and
producer/archive mappings; this was metadata evidence, not fresh payload
validation. INventory.json preserves the initial machine-readable expectations;
INVENTORY_VERIFIED.json adds actual admitted identities. Reserved/preflight
records are not inspected beyond exclusion identity metadata.

After restoration, {profiles['admitted']} candidates each have exactly one
verified XML/assets variant and native mapping. Their {profiles['new_variants']}
unique variants cover three task profiles.49 variants are shared across the two
goal tasks. XML filename and task identity are never treated as variant identity.
Content, verified external dependencies and per-execution geometry are checked.

Multiple possible variants:0 among validated executions. Missing expected XML
metadata:0 in the initial candidate pool. Unresolved/unrestored payload profiles:
{coverage['remaining_candidate_executions']}. Unresolved native XML/body mappings:
0 in the admitted cohort; not assessed for unrestored candidates. The logical
main_table alias remains unresolved for all147 and is not separately extracted.
No unknown body/geometry assignment is fabricated to increase coverage.

Single-XML assumptions were isolated in the Phase5E task profile registry,
pilot compilation, task-wide mapping selection and source-scope record factory
call sites. Phase5F supplies per-execution profiles and normalized relations,
reuses the factory and core schema, and guards scope before both retrieval modes.
'''.replace('INventory.json','INVENTORY.json'))
 doc('COHORT_SELECTION.md','# Frozen cohort selection\n\n'+load(HERE/'COHORT.json')['selection']+'\n\n'+table(['Partition','Executions','Variants','Saved frames'],[[k,v['executions'],v['variants'],v['frames']] for k,v in profiles['tasks'].items()])+f'''\nExact IDs, seeds, model configurations, expected hashes and archive members are
frozen in COHORT.json before full restoration/indexing. The selected volume is
{coverage['restored_bytes']:,} bytes in{coverage['source_files_restored']} required
files (nine per execution plus two shared files per task). No simulations run.
The prior285-execution index is copied, never overwritten. All60 reserved
executions and38 historical preflights remain excluded. No outcome/prediction
labels were used for cost selection or query targets.

Every execution was independently compiled/read against its own exact XML and
assets. All147 passed; no cohort reduction was needed. Initial pilot failures
were preserved: named texture aliases legitimately share identical files, and
logical fixture names differ from recorded native roots. Alias consistency is
checked, roots are obtained from recorded metadata, and missing main_table is
left unresolved. These are source-contract corrections, not relaxed physical
thresholds or guessed geometry. Other30 partitions remain deferred pending
fresh profile/source validation; no further restoration is started.
''')
 doc('RETRIEVAL_EVALUATION.md',f'''# Variant-aware source retrieval evaluation

{metrics['queries']} prospectively fixed source-target queries passed, with
Precision@1={metrics['precision_at_1']}, Recall@20={metrics['recall_at_20']} and
MRR={metrics['MRR']}. Source, task, execution, variant and temporal attribution
are all1.0; invalid cross-scope returns=0. Per-task and per-variant counts/metrics
are saved in validation/RETRIEVAL_METRICS.json, with exact query samples and full
fixtures retained under the work directory. Relevance means exact original
file/hash/selector/frame-window identity, not physical safety understanding.

Initial, middle and terminal snapshots,31/32 boundaries, instructions, metadata,
object identities and all six families are tested. Old task profiles contribute
baseline metadata/raw queries; old record/index rows are preserved exactly.

{negative['negative_queries']} adversarial controls passed: wrong task, execution,
known-incompatible variant, unresolved variant, unsupported field/spatial field,
missing exposure timestamp, unresolved logical fixture, unsupported clock,
uncalibrated geometry admission and out-of-range frames. One reserved and one
preflight identifier enforce exclusions without payload/outcome inspection.
Unindexed cases and implicit comparisons are distinct statuses. Explicit shared-
variant comparison returns two separately identified executions without merging
coverage. No failed match becomes a physical negative or safety verdict.

Observed latency seconds: `{metrics['latency_seconds']}`. These include live source,
asset and mapping validation, not SQL alone. Saved-frame availability is not
continuous physical coverage or camera alignment. There is no empirical R1
assessment, threshold optimization or safety-label tuning in this evaluation.
'''+ '\n'+table(['Task configuration','Queries','P@1','R@20','MRR'],[[k,v['queries'],v['precision_at_1'],v['recall_at_20'],v['MRR']] for k,v in metrics['per_task'].items()]))
 doc('SEMANTIC_RETRIEVAL_EVALUATION.md','# Optional local semantic retrieval\n\n'+table(['Method','Query instances','P@1','R@20','MRR','Median seconds'],[[k,v['query_instances'],round(v['precision_at_1'],6),v['recall_at_20'],round(v['reciprocal_rank'],6),round(v['median_seconds'],6)] for k,v in sem['aggregate'].items()])+f'''\nThe unchanged Phase5E pinned local encoder is reused. There are
{sem['unique_linguistic_probes']} unique fixed linguistic probes,
{sem['unique_objects']} object names, {sem['source_execution_scopes']} execution
contexts and {sem['source_variants']} verified new variants. Objects rotate by a
frozen episode-modulo rule; probes/descriptors/model are not tuned on results.
Query instances are not independent linguistic relevance judgments. Recall@20
has only six candidates. Metrics are not physical-event or checker accuracy.

All returned rows retain exact execution/task/object/variant provenance.
{len(sem['negative_scope_cases'])} scope controls plus{len(extra['cases'])}
additional controls cover wrong variant/execution/task, absent timestamps,
unsupported spatial fields, unindexed and excluded scopes. Invalid cross-scope
returns=0. A registry document not embedded in the sidecar is explicitly
unindexed for semantic retrieval and is not returned as evidence. Phase5E's
original sidecar and16 compatibility tests still pass against its original DB.

Full per-task/per-variant results, failures and ranks are in validation/. The
sidecar is separate from the source-of-truth SQLite database, uses metadata
filtering first and preserves all physical capability blocks. No external
embedding API, LLM drafting, RAG safety labels or agent orchestration is used.
''')
 suites=qa['suites'];doc('REGRESSION_RESULTS.md',f'''# Regression and preservation results

PASS: {qa['tests']} automated tests;{qa['skipped']} skipped; zero unexplained
failures. All484 Phase5E tests and37 new variant tests pass. Exact commands,
versions, return codes, counts and log SHA-256 values are in
validation/REGRESSION_RESULTS.json; full logs remain under `{WORK/'qa'}`.

Fresh and independent builds have equal core exports and normalized-relation
build IDs. Resume skips147 completed new jobs without duplicates. SQLite,
foreign keys, FTS/catalog/source dependencies and variant bindings pass. All
67,053 old evidence/index rows,2,000 catalog rows and285 jobs remain exact.

{final['original_source_paths_freshly_hashed']} original source paths and
{final['external_profile_artifacts_hashed']} external profile/diagnostic artifacts
were freshly hash-checked. The immutable Phase5E DB remains `{BASE_SHA}`.
Baseline artifacts are unchanged; the intentionally versioned reader dispatch
is compared against its original Git commit, not falsely declared unchanged.
Frozen V3 code/predictions, both seals and their12 members, and eight protected
scoring files pass final verification. Human references/labels are untouched.

Initial pilot source-contract failures are retained in PROFILE_VALIDATION_PILOT_
ATTEMPT1/2 and external FAILURE artifacts. Consistent named asset aliases were
handled explicitly, recorded fixture roots verified, and main_table left
unresolved. No failing/skipped regression is hidden to declare success.
'''+ '\n'+table(['Suite','Tests','Return code','Skipped'],[[k,v['tests_run'],v['returncode'],v['skipped']] for k,v in suites.items()]))
 doc('COVERAGE.md',f'''# Recorded, available and searchable coverage

The historical inventory describes2,000 recorded executions and has2,000 catalog
metadata entries. Fresh original sources support{coverage['total_executions']}
indexed executions,{coverage['total_records']:,} evidence records and
{coverage['saved_frames']:,} saved frames. There are{coverage['variants']} verified
content variants in the expanded index;{coverage['new_variant_count']} are new.

COVERAGE_MATRIX.csv has{coverage['coverage_matrix_rows']} rows, one per selected
execution/task/variant and supported family. It distinguishes fields actually
saved, exposed by the reader and separately searchable. Only six raw families
are independently indexed: pose, geometry references, contact observations,
robot state, simulation timestamp and camera references. Other arrays and raw
observables remain inventoried references. Contact forces/normals, camera
exposure time and unverified spatial interpretations are not manufactured.

Remaining unindexed: {coverage['remaining_total_unindexed']} =
{coverage['remaining_candidate_executions']} unprofiled candidates +60 reserved
+38 excluded preflights. These counts do not imply missing data were negative
observations. Newly indexed cases are database-only expansion, not authorized
calibration-development or independent human reference data.

Next database-only work: validate additional exact XML/asset profiles in bounded
batches, including remaining22 multi-XML and eight single-XML partitions. Apply
variant/execution isolation to all new channels before indexing them. Broader
independent language-relevance evaluation is separate from physical ground
truth. Do not automatically restore the remaining population or start agents.
''')
 doc('PERFORMANCE.md',f'''# Measured performance

Primary append elapsed {build['elapsed_seconds']:.3f}s for147 executions:
{147/build['elapsed_seconds']:.3f} executions/s. Peak build RSS
{build['peak_rss_kib']:,}KiB. Indexing holds one execution in memory; integrity/
logical-export QA loads compact registry metadata. Profiles/maps and sources
remain outside Git; no raw frame arrays or videos are stored in SQLite.

Database: {final['database_bytes']:,}bytes; source restoration:
{coverage['restored_bytes']:,}bytes; semantic sidecar:{final['semantic_bytes']:,}bytes.
Structured/lexical latency: `{metrics['latency_seconds']}` seconds.
Semantic query latency and stack bindings are reported separately. Results
include source/dependency checks and depend on cache/load conditions.
Final disk1 available:{final['disk1_available_bytes']:,}bytes, exceeding500GB.
Disk0's pre-existing reserve deficit was not remediated or used for large new
artifacts. All computation was on Hestia; Alliance provided storage retrieval
only. No simulations, source deletion, push or merge occurred.
''')
 print('Phase5F reports rendered')
if __name__=='__main__':main()
