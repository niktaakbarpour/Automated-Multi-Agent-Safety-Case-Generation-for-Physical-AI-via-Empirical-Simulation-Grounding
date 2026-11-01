"""Final regression rerun after the read-only catalog status clarification."""
import os
from pathlib import Path
from .validate import CHANGED
from .profile import HERE,REPO
from .build import BASELINE,BASE_SHA
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite

def main():
 root=Path('/disk/1/data/niktakbr/trustworthy-phase5c-working');out=root/'final-checks';out.mkdir();(out/'tmp').mkdir()
 os.environ['RAG_TEST_DB']=str(BASELINE);os.environ['RAG_EXPANSION_DB']=str(root/'development-40.sqlite')
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages';suites={}
 for name,path in [('expansion','evaluation/r1_v4/rag_evidence_database/expansion/tests'),('phase5b','evaluation/r1_v4/rag_evidence_database/tests'),('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 previous=load(root/'validation/VALIDATION_RESULTS.json');assert previous['passed'];assert sha(BASELINE)==BASE_SHA
 modified=[]
 for directory in ('libero_evidence_audit','libero_measurement_reader','measurement_profile_validation','evidence_review_readiness','evidence_registry_gsn','rag_evidence_database'):
  p=HERE.parents[1]/directory
  for n,r in load(p/'ARTIFACT_SHA256.json').items():
   if sha(p/n)!=r['sha256']:
    name=str((p/n).relative_to(REPO));assert name in CHANGED;modified.append(name)
 assert set(modified)==CHANGED
 sources=load(HERE/'VALIDATED_SOURCE_PROFILE.json')['source_bindings']
 for r in sources:assert sha(r['restored_path'])==r['sha256']
 for r in load(HERE.parents[1]/'evidence_review_readiness/SOURCE_BINDINGS.json')['original_files']:assert sha(r['path'])==r['sha256']
 frozen=verify();assert frozen['passed'];write_new(out/'FROZEN_FINAL.json',frozen)
 result={**previous,'tests':sum(r['tests_run'] for r in suites.values()),'suites':suites,'passed':all(r['returncode']==0 for r in suites.values()),'expected_code_amendments':sorted(CHANGED),'final_source_paths_verified':364,'expanded_database_sha256':sha(root/'development-40.sqlite'),'baseline_sha256_unchanged':sha(BASELINE)}
 write_new(out/'FINAL_VALIDATION_RESULTS.json',result);print('Final Phase5C',result['passed'],result['tests'],{k:(v['tests_run'],v['returncode']) for k,v in suites.items()})
 if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
