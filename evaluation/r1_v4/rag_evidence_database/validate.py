"""Complete database milestone checks, with frozen-source regression preservation."""
import os,socket,subprocess,time
from pathlib import Path
from .store import Store,HERE
from .build import populate
from .evaluate import evaluate
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite
BASE='eefa9c36607ece47f0d8a57718a1d87d9969d07f'

def main(output):
 assert socket.gethostname().lower()=='hestia'
 out=Path(output).resolve();assert out.is_relative_to('/disk/1/data/niktakbr');out.mkdir(exist_ok=False);(out/'tmp').mkdir()
 sources=load(HERE.parent/'evidence_review_readiness/SOURCE_BINDINGS.json')['original_files']
 before={r['path']:sha(r['path']) for r in sources};assert all(before[r['path']]==r['sha256'] for r in sources)
 write_new(out/'FROZEN_BEFORE.json',verify())
 dbpath=out/'development.sqlite';build=populate(dbpath);write_new(out/'BUILD_MANIFEST.json',build)
 resumed=populate(dbpath);assert resumed['build_id']==build['build_id'] and resumed['skipped_episodes']==[0,1,2,14]
 write_new(out/'RESUME_REPORT.json',resumed)
 other=out/'reproduced.sqlite';reproduced=populate(other);assert reproduced['build_id']==build['build_id'];write_new(out/'REPRODUCED_BUILD.json',reproduced)
 store=Store(dbpath);integrity=store.check();assert integrity['passed'];write_new(out/'DATABASE_INTEGRITY.json',integrity)
 # Canonical export equivalence, not SQLite physical layout.
 repeat=Store(other)
 assert digest(store.export())==digest(repeat.export());repeat.close();store.close()
 metrics=evaluate(dbpath,out)
 suites={};packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 os.environ['RAG_TEST_DB']=str(dbpath)
 for name,path in [('rag','evaluation/r1_v4/rag_evidence_database/tests'),('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 for p,h in before.items():assert sha(p)==h
 for directory in ('libero_evidence_audit','libero_measurement_reader','measurement_profile_validation','evidence_review_readiness','evidence_registry_gsn'):
  p=HERE.parent/directory
  for n,r in load(p/'ARTIFACT_SHA256.json').items():assert sha(p/n)==r['sha256'],str(p/n)
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines();assert all(n.startswith('evaluation/r1_v4/rag_evidence_database/') for n in changes)
 write_new(out/'FROZEN_AFTER.json',verify())
 passed=all(r['returncode']==0 for r in suites.values()) and integrity['passed']
 result={'passed':passed,'suites':suites,'tests':sum(r['tests_run'] for r in suites.values()),'original_files_unchanged':38,'all_prior_artifacts_unchanged':True,'reproducible_build':True,'idempotent_resume':True,'database_sha256':sha(dbpath),'base_commit':BASE,'no_downstream_generation':True,'empirical_admission_enabled':False}
 write_new(out/'VALIDATION_RESULTS.json',result)
 print('Phase 5B',passed,{n:(r['tests_run'],r['returncode']) for n,r in suites.items()},'records',build['records'],'catalog',build['catalog_count'])
 if not passed:raise SystemExit(1)
if __name__=='__main__':main('/disk/1/data/niktakbr/trustworthy-phase5b-working/validated')
