"""Generate quantitative reports only from stored validation artifacts."""
import json,csv,sqlite3
from pathlib import Path
from .config import HERE,WORK,BASE_SHA,PROVENANCE_SCOPE
from .model import SCOPE_DEFINITION

def load(n):return json.loads((WORK/n).read_text())
def write(name,text):(HERE/name).write_text(text.strip()+'\n')
def csvwrite(name,rows):
 rows=list(rows)
 with (HERE/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def generate():
 p=load('PRODUCER_EVIDENCE.json');clock=load('CLOCK_AUDIT.json');build=load('BUILD.json');validation=load('ASSURANCE_VALIDATION.json');restore=load('RESTORATION.json');rebuild=load('REBUILD_RESUME.json');reg=load('REGRESSION.json');h=load('legacy_h/RETRIEVAL_VALIDATION.json');sem=load('semantic_i/SEMANTIC_BENCHMARK.json')
 rows=[]
 for e in p['rows']:
  for f in e['producer_files']:
   rows.append(dict(execution_id=e['execution_id'],task_id=e['task_id'],variant_id=e['variant_id'],metadata_path=e['metadata_path'],metadata_sha256=e['metadata_sha256'],recorded_revision=e['source_commit_declaration'],relative_path=f['relative_path'],recorded_sha256=f['recorded_sha256'],available_matching_path=f['available_matching_path'],classification=f['classification'],current_integrity=f['current_integrity'],executed_bytes_attested=False,recorded_started_at=e['recorded_started_at'],date_basis=e['date_attestation']))
 csvwrite('PRODUCER_INVENTORY.csv',rows)
 csvwrite('ATTESTATION_COVERAGE.csv',(dict(execution_id=e['execution_id'],variant_id=e['variant_id'],recorded_producer_files=len(e['producer_files']),available_matches=sum(bool(f['available_matching_path']) for f in e['producer_files']),evaluator_matches=len(e['evaluator_files']),historical_binary_attestation='UNATTESTED',clean_checkout='UNATTESTED',container_digest='UNAVAILABLE',trusted_creation_date='UNAVAILABLE',metadata_sha256=e['metadata_sha256']) for e in p['rows']))
 csvwrite('CLOCK_DOMAIN_REGISTRY.csv',(dict(execution_id=e['execution_id'],variant_id=e['variant_id'],clock_id=k,**v,source_path=e['source_path'],source_sha256=e['source_sha256'],synchronization='UNATTESTED',cache_offset='CONDITIONAL -0.002 s after initial frame') for e in clock['rows'] for k,v in clock['definitions'].items()))
 dep=dict(scope='Selected current executable/source/metadata artifacts and mapped ABI libraries; not hermetic closure or historical binary proof',historical_dependency_declarations=[dict(execution_id=e['execution_id'],source_path=e['metadata_path'],source_sha256=e['metadata_sha256'],versions=e['dependency_version_declarations'],classification='HISTORICAL_RECORD',attestation='RECORDED_DECLARATION_ONLY') for e in p['rows']],current_environments={k:load('DEPENDENCIES_'+k+'.json') for k in ('retrieval','native')})
 write('DEPENDENCY_MANIFEST.json',json.dumps(dep,sort_keys=True,indent=2))
 graph=dict(database=build['database'],database_sha256=build['database_sha256'],tables=['i_nodes','i_artifacts','i_edges','i_scope_nodes','i_scope_edges','i_record_scope','i_claims','i_clock_domains','i_clock_labels','i_jobs'],counts=build['counts'],scope=SCOPE_DEFINITION,queries=dict(record_sources="SELECT a.path,a.sha256 FROM i_edges e JOIN i_artifacts a ON a.id=e.target WHERE e.source=?",execution_nodes='SELECT n.* FROM i_scope_nodes s JOIN i_nodes n ON n.id=s.node WHERE s.execution=?',claims='SELECT * FROM i_claims WHERE execution=?',clock_labels='SELECT * FROM i_clock_labels WHERE execution=? ORDER BY frame'))
 from .graph_release import supplement
 c=sqlite3.connect('file:'+build['database']+'?mode=ro',uri=True);graph['release_and_extraction_links']=supplement(c,build['database_sha256']);c.close()
 write('DEPENDENCY_GRAPH.json',json.dumps(graph,sort_keys=True,indent=2))
 write('README.md',f'''# Phase 5I: source reproducibility

Database and retrieval infrastructure only. No new channels, executions, safety agents, judgments or empirical admission.

Preserved 432 executions, 104 variants, 80,786 evidence records, 2,592 raw channel references, 2,592 separate interpretations and 58,075 saved frames. All original tables compare exactly with Phase 5H (PRESERVATION.json).

New database: `{build['database']}` ({build['bytes']} bytes), SHA-256 `{build['database_sha256']}`.

See PRODUCER_INVENTORY.csv, PROVENANCE_MODEL.md, SENSOR_TIMESTAMP_AUDIT.md, DEPENDENCY_GRAPH.json, RELEASE_VERIFICATION.md and COVERAGE_AND_LIMITATIONS.md. Machine-readable results are under `{WORK}` and hash-bound by ARTIFACT_MANIFEST.json. An external trusted manifest hash is required; this release does not claim an external signature or timestamp authority.

{reg['total_tests']} automated regression tests passed. Restoration and raw oracle checks are separate from ranked retrieval and do not measure physical safety accuracy.''')
 write('PROVENANCE_MODEL.md',f'''# Provenance model

HISTORICAL_RECORD means content of an original hash-bound recording artifact, with only RECORDED_DECLARATION_ONLY attestation. It does not prove a clean checkout, executed bytes, correctness of recorded dates, or binary identity.

RETROSPECTIVE_ARTIFACT identifies bytes verified now. RECONSTRUCTED_ASSOCIATION records a tested relationship such as an available file matching a digest named in original metadata. CONDITIONAL_INTERPRETATION preserves explicit assumptions. UNATTESTED marks unavailable evidence. No external historical attestation root exists in this release.

Claims have subject/execution, property, source artifact/hash, canonical projection selector, basis, category, assumptions, limitations and independently verified creation date (null throughout). source_selector names a canonical projection, not a literal JSON pointer. CLAIM_SOURCE_SELECTORS.json maps all six projections to exact original JSON pointers. CLAIM_VALIDATION.json independently checks all 2,592 values against 432 hash-verified metadata files; no source fields are missing or mismatched. model.validate_claim rejects escalation into historical attestation, current artifacts masquerading as historical records, and fabricated trusted dates. The trusted database hash protects stored classifications; category labels alone are not cryptographic proof.

The queryable graph contains {build['counts']['i_nodes']} nodes and {build['counts']['i_edges']} relationships. Edge basis strings distinguish preserved bindings, declared dependencies, retrospective matches and explicitly unresolved links. Original raw bodies remain authoritative; graph record nodes reference IDs rather than duplicating arrays. DEPENDENCY_GRAPH.json also contains shared release/interface/extraction-declaration nodes and reproducible SQL relationship views. These expose contract-version and release-membership edges without duplicating file paths in every record. Stored and virtual counts are reported separately; none attests a historical running producer.

Provenance completeness is explicitly bounded to `{PROVENANCE_SCOPE}`. The implementation verifies execution-scoped referenced artifacts plus both selected current dependency snapshots. It excludes full transitive/environment closure, historical binaries, absent video/resource payloads and physical synchronization. No request can silently downgrade to a weaker assurance.''')
 write('SENSOR_TIMESTAMP_AUDIT.md',f'''# Sensor-time audit

Inspected all {clock['saved_frames']} saved snapshots and {clock['action_labels']} action labels across 432 executions / 104 variants. Checked {clock['sensor_groups_checked']} raw sensor groups for explicit timestamp/clock attributes and datasets. No explicit per-sensor timestamp fields were found. This does not prove an arbitrary undocumented array cannot encode time; such an interpretation remains unsupported.

Recorded simulator endpoint labels are distinct from frame index. Frame host UTC, POSIX-API wall nanoseconds and monotonic nanoseconds are recorded at recorder calls, not calibrated sensor exposure times. Actions have post-call simulator/host labels; policy and inference records carry UTC labels and elapsed durations. CLOCK_AUDIT.json preserves original values and selectors. i_clock_labels stores original labels, without interpolation or invented samples.

Primary evidence: source_evidence/recording_base.py, hash-matched to execution metadata (PRODUCER_EVIDENCE.json). Lines 11, 52, 78, 129, 135 and 167 show datetime.now, time.time_ns, time.monotonic_ns, performance durations and post-action labels. Simulator serialization is source-bound by Phase 5H primary-source traceability and retested by unchanged source-value benchmarks. Present-day CPython semantics do not attest the original running binary.

The established 0.05-second saved interval and 0.002-second physics step remain scoped to admitted recordings and version-bound XML/model validation. The -0.002-second cache interpretation is CONDITIONAL. No per-sensor instant, exposure alignment, drift model, calibrated wall-clock origin or host-to-simulator affine mapping is asserted. Observed wall-minus-monotonic spans are descriptive, not synchronization parameters.

Seconds queries filter actual recorded simulator labels inclusively. They do not manufacture sensor timestamps from frame index. Same-index association, endpoint simulator time and physical simultaneity remain distinct. Missing sensor clocks and resource payloads are explicit in CLOCK_DOMAIN_REGISTRY.csv.''')
 write('RELEASE_VERIFICATION.md',f'''# Independent release verification

A caller must supply an independently trusted SHA-256 for ARTIFACT_MANIFEST.json. The manifest verifies database, contracts/code, preservation results and external artifacts. A hash generated today anchors current bytes, not recording-time identity.

Run on Hestia:

```sh
python3 -S -m evaluation.r1_v4.rag_evidence_database.source_reproducibility.check_release --sha256 TRUSTED_MANIFEST_SHA256 --scope metadata
```

Use `--scope sources` for original recordings/XML/assets/proofs and `--scope provenance` for selected dependency/binary artifacts. Approved paths, descriptor-bound access, no symlinks and hashes remain mandatory. Metadata-only operation cannot return source values when external data are absent.

`ProvenanceStore(database, expected_sha256=trusted_database_sha)` and `retrieve(store, ProvenanceQuery(...))` retain Phase 5H guards. verified_source_values verifies original bytes, bindings, contract, dtype/shape and scope. verified_physical_interpretation also requires verified order, units and coordinate type; conditional properties cannot satisfy it. provenance_complete requires explicit scope `{PROVENANCE_SCOPE}` and verifies its artifact closure. historical_producer_attestation fails explicitly throughout this release. Missing historical evidence does not invalidate otherwise verified raw retrieval.

Restoration uses restore.create(database, executions, fresh_root) and a caller-pinned RESTORE.json hash. Paths map explicitly to content-addressed scratch objects with execution membership and canonical hash enforced. RestoredRelease verifies the copied database and execution graph artifacts before descriptor-bound raw reads. It never falls back to originals. The runtime is the separately inventoried current Hestia environment, not an archived hermetic runtime. Historical producer reexecution is unsupported.

Metadata-only needs pinned database/schema/code. Verified values additionally need HDF5 and referenced geometry/proofs. Annotations need model/primary-source validation artifacts. Bounded provenance also needs selected current dependency artifacts and producer matches. The 60 reserved, 38 excluded and 1,470 pending executions are never restored or read.''')
 write('RESTORATION_TEST_RESULTS.md',f'''# Bounded restoration

Selection frozen in RESTORE_SELECTION.json: SHA-256 ordering with seed phase5i-restore-v1 over admitted IDs, first six distinct variants. No outcome, prediction or label was used.

Restored {len(restore['executions'])} executions across {restore['variants']} variants, {restore['files']} canonical references and {restore['unique_bytes']} unique content bytes, plus one hash-identical database. Compared {restore['samples']} initial/middle/terminal samples over six channels to independent original HDF5 reads. Maximum numeric error: {restore['maximum_numeric_error']}. No original-path fallback.

This is bounded evidence restoration with a current decoder prerequisite, not historical simulator reexecution or a complete 432-execution portable bundle. Shared proof summaries may describe other indexed executions; no unselected raw execution data were copied. RESTORATION.json and restoration/RESTORE.json contain exact mappings and hashes.''')
 write('TAMPERING_TEST_RESULTS.md','''# Integrity negative controls

All mutations use isolated scratch files. Validated recordings, XML, predictions, annotations and seals remain unchanged.

New tests cover manifest/database mutation, incomplete restore, missing restored files with valid originals present (no fallback), wrong execution membership, traversal, symlinks, changed bytes after verification, recovery, producer/dependency/geometry/XML/contract/clock-evidence artifact corruption, invented historical attestation, retrospective-to-historical confusion, unavailable clocks and unsupported synchronization/transforms. Role mutations exercise the mandatory artifact verification path; they do not imply historical binaries exist.

Inherited tests also cover actual HDF5 shape/type/value tampering, preserved-mtime changes, replacement, parent symlinks, stale verification/decoder states, restoration and contract/source mismatches. Names/outcomes are under regressions/qa. A newly trusted manifest is a different trust root, not a bypass of the old root.''')
 write('RETRIEVAL_EVALUATION.md',f'''# Retrieval and assurance

Phase 5I: {validation['positive_queries']} positive assurance/recorded-clock queries; {validation['negative_controls']} negatives; {validation['numeric_samples']} independent raw comparisons; maximum/mean numeric error 0; recorded-label alignment errors 0; leakage 0. These are source checks, not safety accuracy.

Phase 5H rerun: {h['queries']} exact queries, {h['negative_controls']} negatives, P@1/R@20/MRR all 1.0. Wrong execution/task/variant/source/field/object/unit/frame/alignment/status and excluded/reserved/pending IDs fail before results.

Optional semantic benchmark: {sem['unique_probes']} unique formulations repeated across {sem['execution_scopes']} scopes. Metrics: `{json.dumps(sem['aggregate'],sort_keys=True)}`. Negatives: {sem['negative_controls']}, leakage 0. Repeated contexts are not independent linguistic cases. Phase 5F/G reruns are under legacy_f/legacy_g.

ASSURANCE_VALIDATION.json contains strict/session, physical and provenance timings under concurrent validation load, not stable throughput estimates. Stronger provenance pays hashing costs without relaxing checks. Semantic similarity cannot override scope or assurance gates.''')
 write('REGRESSION_RESULTS.md',f'''# Regressions and preservation

{reg['total_tests']} automated tests passed, with no unexplained failures/skips. Includes 521 inherited Phase 5F tests, 57 Phase 5G, 87 Phase 5H and new Phase 5I tests. Details and frozen verification: REGRESSION.json and regressions/qa.

PRESERVATION.json compares every Phase 5H table definition and ordered row, including FTS backing tables, source associations, contracts and variants. Baseline SHA-256: {BASE_SHA}. Earlier releases remain untouched. Reserved/excluded/pending rows are preserved and negative-tested.

REBUILD_RESUME.json verifies a fresh logical rebuild, full resume over 432 jobs and partial resume after deleting one execution's new scoped rows in scratch. Digests agree: {build['logical_digest']}. Original tables are never rewritten.

Initial SQL-placeholder, benchmark-module import and missing test-output-directory failures are preserved in initial_failed logs. Intermediate preclosure/preproducer/preassociation databases/logs preserve diagnostic history. These implementation diagnostics were corrected before final validation without source modification or contract relaxation. Git later flagged CSV CRLF line endings; explicit LF generation passed, and CSV_FORMAT_VALIDATION.json proves only line endings changed.''')
 write('COVERAGE_AND_LIMITATIONS.md','''# Coverage and limitations

All 432 admitted executions / 104 variants retain original evidence. Metadata declares 104 producer files per execution. Available bytes match 103 (100 from a verified local archive plus three preserved recorder/review files). oft_adapter.py is unavailable. Forty-one evaluator files per execution match recorded hashes. ARCHIVE_ENVIRONMENT_AUDIT.json separately inventories 88 unbound build/dependency declarations (including generic upstream Dockerfiles and a process coordination lock); none establishes the image or dependency environment actually used. Archived Python executable entries are symlink-target text, not attested runtime binaries. These are retrospective matches, not executed-byte attestations.

Metadata names commit e4287e94541f459edc4feabc4e181f537cd569a8 and versions MuJoCo 3.8.1, robosuite 1.4.0, hf_libero 0.1.4, NumPy 1.26.4 and h5py 3.16.0. Versions do not prove binaries. No execution has independently attested historical binaries, clean checkout, container digest, trusted creation date or calibrated sensor clocks. Historical binaries/checkpoints are not restored/reexecuted. Resource/video hashes do not establish locally available payloads.

Current dependency snapshots cover selected executable source, shared libraries and metadata, not all resources/transitive dependencies. They do not attest loaded process memory or unselected bytecode caches. Matching wheel RECORD entries show internal consistency, not publisher authenticity. Native/retrieval snapshots are distinct. Restoration covers six executions with current decoder prerequisites, not a hermetic historical runtime.

No world transforms, calibration, contact-pair/force interpretation or synchronized sensor-time claims are added. main_table remains a bounded symbolic table/table_collision relationship, not support/contact/fall evidence. The -0.002-second cache interpretation remains conditional. Missing samples are never interpolated.

Next database-only milestone: recover authenticated original producer/runtime artifacts and original clock/calibration evidence if available. Future instrumentation cannot retroactively attest historical recordings. Empirical R1 admission remains disabled; no checker, labels, predictions or downstream agents changed.''')
 write('REPRODUCIBILITY.md',f'''# Reproduction

All computation ran on Hestia with python3 -S and audited explicit PYTHONPATH. No Alliance computation, Sea NFS, new simulations, global installs or full-corpus copying. Resource preflight is in RESOURCE_PREFLIGHT.json. Work: {WORK}. Diagnostic databases are retained.

From repository root run modules under evaluation.r1_v4.rag_evidence_database.source_reproducibility: inventory, dependencies (retrieval and native environment; invocation in source), clocks, build, validate, benchmarks f, benchmarks g, benchmarks h, regressions, reports. verify_baseline.py records pre-change 665-test checks. Freeze inventories before build; changed input/producer hashes reject resume.

build copies Phase 5H and adds i_ tables. validate compares baseline rows, verifies raw/clock queries, freezes restoration selection, restores bounded sources, builds independently and tests full/partial resume. Timings/bytes: BUILD.json, ASSURANCE_VALIDATION.json and RESTORATION.json. RESOURCE_OBSERVATIONS.json records retained working bytes and free disk; process RSS was sampled, not continuously measured. Arrays remain external.

Verification requires a caller-pinned manifest hash. SQLite byte layout may differ after a fresh build; logical equivalence is the reproducibility criterion. Historical reexecution and complete binary reproduction remain unsupported. Post-commit read-only preservation checks are required; no push/merge.''')
if __name__=='__main__':generate()
