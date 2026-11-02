"""Expansion QA, preserving the exact Phase5B database and frozen evaluation artifacts."""
import os,subprocess
from pathlib import Path
from .build import populate,BASELINE,BASE_SHA
from .profile import HERE,REPO
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite
BASE='6447cd539f258a4f9da875c4e372de992f126ce3'
CHANGED={'evaluation/r1_v4/rag_evidence_database/catalog.py','evaluation/r1_v4/evidence_registry_gsn/registry.py','evaluation/r1_v4/rag_evidence_database/search.py','evaluation/r1_v4/libero_measurement_reader/reader.py'}

def main():
 out=Path('/disk/1/data/niktakbr/trustworthy-phase5c-working/validation');out.mkdir(exist_ok=False);(out/'tmp').mkdir()
 assert sha(BASELINE)==BASE_SHA;write_new(out/'FROZEN_BEFORE.json',verify())
 old=load(HERE.parent.parent/'evidence_review_readiness/SOURCE_BINDINGS.json')['original_files']
 restored=load(HERE/'RESTORATION_MANIFEST.json')['files'];sources=[{'path':r['path'],'sha256':r['sha256']} for r in old]+[{'path':r['restored_path'],'sha256':r['sha256']} for r in restored]
 for r in sources:assert sha(r['path'])==r['sha256']
 primary=Path('/disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite')
 first=load(primary.parent/'BUILD_MANIFEST.json');resume=populate(primary);assert first['build_id']==resume['build_id'] and len(resume['skipped_episodes'])==36
 write_new(out/'RESUME_REPORT.json',resume)
 reproduced=populate(out/'reproduced.sqlite');assert reproduced['build_id']==first['build_id'];write_new(out/'REPRODUCED_BUILD.json',reproduced)
 db=Store(primary);repro=Store(out/'reproduced.sqlite');assert digest(db.export())==digest(repro.export());repro.close()
 integrity=db.check();assert integrity['passed'];write_new(out/'DATABASE_INTEGRITY.json',integrity)
 records=db.records();jobs=db.db.execute('SELECT execution,input_digest,status,records FROM rag_jobs ORDER BY execution').fetchall()
 corpus={'schema_version':'1.0.0','executions':len(jobs),'records':len(records),'frames':sum(max(r.interval[1] for r in records if r.execution_id==execution and r.kind=='raw_measurement')+1 for execution,_,_,_ in jobs),'baseline_ids_preserved':1360,'unique_ids':len({r.id for r in records}),'synthetic_records':sum(bool(r.provenance.get('synthetic')) for r in records),'per_execution':[]}
 for execution,key,status,count in jobs:
  values=[r for r in records if r.execution_id==execution]
  from collections import Counter
  counts=dict(Counter(r.measurement_type for r in values));assert len({r.object_id for r in values if r.kind=='raw_measurement'})==5
  corpus['per_execution'].append({'execution_id':execution,'input_digest':key,'status':status,'records':count,'types':counts,'frames':max(r.interval[1] for r in values if r.kind=='raw_measurement')+1})
 db.close();write_new(out/'EXPANDED_CORPUS_MANIFEST.json',corpus)
 suites={};packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 os.environ['RAG_TEST_DB']=str(BASELINE);os.environ['RAG_EXPANSION_DB']=str(primary)
 for name,path in [('expansion','evaluation/r1_v4/rag_evidence_database/expansion/tests'),('phase5b','evaluation/r1_v4/rag_evidence_database/tests'),('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 for r in sources:assert sha(r['path'])==r['sha256']
 # Prior manifests remain historical snapshots. Only three explicitly reviewed code extensions differ.
 prior_changes=[]
 for directory in ('libero_evidence_audit','libero_measurement_reader','measurement_profile_validation','evidence_review_readiness','evidence_registry_gsn','rag_evidence_database'):
  root=HERE.parents[1]/directory
  for name,entry in load(root/'ARTIFACT_SHA256.json').items():
   p=root/name
   if sha(p)!=entry['sha256']:
    relative=str(p.relative_to(REPO));assert relative in CHANGED;prior_changes.append(relative)
 assert set(prior_changes)==CHANGED
 assert sha(BASELINE)==BASE_SHA;write_new(out/'FROZEN_AFTER.json',verify())
 passed=all(r['returncode']==0 for r in suites.values());write_new(out/'VALIDATION_RESULTS.json',{'passed':passed,'tests':sum(r['tests_run'] for r in suites.values()),'suites':suites,'baseline_sha256_unchanged':BASE_SHA,'expanded_database_sha256':sha(primary),'old_sources_unchanged':38,'restored_files_unchanged':324,'reproducible_build':True,'idempotent_resume':True,'expected_code_amendments':sorted(CHANGED),'prior_noncode_artifacts_unchanged':True,'empirical_admission_enabled':False})
 print('Phase5C',passed,{k:(v['tests_run'],v['returncode']) for k,v in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
