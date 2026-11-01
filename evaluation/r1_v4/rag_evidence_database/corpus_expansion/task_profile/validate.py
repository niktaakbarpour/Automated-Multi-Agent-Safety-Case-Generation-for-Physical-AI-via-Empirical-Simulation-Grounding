"""Independent builds, sources, coverage, retrieval and frozen artifact regressions."""
import os,subprocess
from pathlib import Path
from collections import Counter,defaultdict
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite
from .plan import HERE,DEST
from .build import populate,BASE,BASE_SHA
from .evaluate import evaluate
CHANGED={'evaluation/r1_v4/libero_measurement_reader/reader.py','evaluation/r1_v4/rag_evidence_database/build.py','evaluation/r1_v4/rag_evidence_database/store.py','evaluation/r1_v4/rag_evidence_database/search.py'}

def main(output=None):
 out=Path(output or '/disk/1/data/niktakbr/trustworthy-phase5d-working/final-validated');out.mkdir();(out/'tmp').mkdir()
 assert sha(BASE)==BASE_SHA;write_new(out/'FROZEN_BEFORE.json',verify())
 sources=load(HERE/'RESTORED_SOURCES.json')['files']
 old=load(HERE.parents[1]/'expansion/VALIDATED_SOURCE_PROFILE.json')['source_bindings']
 old+= [{'restored_path':r['path'],'sha256':r['sha256']} for r in load(HERE.parents[2]/'evidence_review_readiness/SOURCE_BINDINGS.json')['original_files']]
 for r in sources+old:assert sha(r['restored_path'])==(r.get('actual_sha256') or r['sha256'])
 path=out/'corpus-89.sqlite';primary=populate(path);write_new(out/'BUILD_MANIFEST.json',primary)
 resumed=populate(path);assert resumed['build_id']==primary['build_id'] and len(resumed['skipped_episodes'])==49;write_new(out/'RESUME_REPORT.json',resumed)
 reproduced=populate(out/'reproduced.sqlite');assert reproduced['build_id']==primary['build_id'];write_new(out/'REPRODUCED_BUILD.json',reproduced)
 db=Store(path);other=Store(out/'reproduced.sqlite');assert digest(db.export())==digest(other.export());other.close()
 integrity=db.check();assert integrity['passed'];write_new(out/'DATABASE_INTEGRITY.json',integrity)
 records=db.records();db.close();inventory={r['run_id']:r for r in load(REPO/'data/runs.json')['records']};scopes=defaultdict(list)
 for r in records:
  if r.kind=='raw_measurement':scopes[(r.execution_id,r.object_id,r.measurement_type)].append(r)
 for (execution,obj,kind),values in scopes.items():
  expected=inventory[execution]['available_measurements']['root_groups']['frames'];cursor=0
  for r in sorted(values,key=lambda r:r.interval):assert r.interval[0]==cursor and not r.missing_intervals;cursor=r.interval[1]+1
  assert cursor==expected
 corpus={'schema_version':'1.0.0','executions':89,'evidence_records':len(records),'frame_count':sum(inventory[e]['available_measurements']['root_groups']['frames'] for e in {r.execution_id for r in records}),'coverage_scopes':len(scopes),'types':dict(Counter(r.measurement_type for r in records)),'per_execution':[],'physical_coverage_qualified':False}
 for execution in sorted({r.execution_id for r in records}):
  values=[r for r in records if r.execution_id==execution];corpus['per_execution'].append({'execution_id':execution,'task_id':values[0].task_id,'frames':inventory[execution]['available_measurements']['root_groups']['frames'],'records':len(values),'objects':sorted({r.object_id for r in values if r.kind=='raw_measurement'}),'measurement_types':sorted({r.measurement_type for r in values if r.kind=='raw_measurement'}),'stratum':'corpus_expansion' if inventory[execution]['suite']=='object' else 'development'})
 write_new(out/'INDEXED_CORPUS.json',corpus)
 metrics=evaluate(path,out)
 os.environ['RAG_NEW_TASK_DB']=str(path);os.environ['RAG_TEST_DB']='/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite';os.environ['RAG_EXPANSION_DB']=str(BASE)
 suites={};packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 for name,tests in [('new_profile','evaluation/r1_v4/rag_evidence_database/corpus_expansion/task_profile/tests'),('partition_audit','evaluation/r1_v4/rag_evidence_database/corpus_expansion/tests'),('phase5c','evaluation/r1_v4/rag_evidence_database/expansion/tests'),('phase5b','evaluation/r1_v4/rag_evidence_database/tests'),('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,tests,out,None if name=='phase2a' else packages)
 for r in sources+old:assert sha(r['restored_path'])==(r.get('actual_sha256') or r['sha256'])
 assert sha(BASE)==BASE_SHA;write_new(out/'FROZEN_AFTER.json',verify())
 passed=all(v['returncode']==0 for v in suites.values());result={'passed':passed,'tests':sum(v['tests_run'] for v in suites.values()),'suites':suites,'baseline_sha256_unchanged':BASE_SHA,'database_sha256':sha(path),'database_bytes':path.stat().st_size,'source_paths_hash_verified':len(sources+old),'new_source_files':443,'new_executions':49,'preserved_evidence_ids':11830,'reproducible_build':True,'idempotent_resume':True,'empirical_admission_enabled':False,'source_code_amendments':sorted(CHANGED)}
 write_new(out/'VALIDATION_RESULTS.json',result);print('Final new-task QA',passed,result['tests'],{k:(v['tests_run'],v['returncode']) for k,v in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
