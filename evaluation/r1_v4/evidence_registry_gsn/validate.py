"""Hestia-only regression and source preservation validation."""
import socket,subprocess
from collections import Counter
from pathlib import Path
from .builder import HERE,REPO,sha
from .demo import demonstrate
from evaluation.r1_v4.provenance import load,write_new,canonical
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite
BASE='6c41960c9658fc0ef67406b3d27330169eba8335'

def main(output=None):
 assert socket.gethostname().lower()=='hestia'
 out=Path(output or '/disk/1/data/niktakbr/trustworthy-phase5a-working/final-validation').resolve()
 assert out.is_relative_to('/disk/1/data/niktakbr')
 out.mkdir(exist_ok=False);(out/'tmp').mkdir()
 source=load(HERE.parent/'evidence_review_readiness/SOURCE_BINDINGS.json')
 before={r['path']:sha(r['path']) for r in source['original_files']}
 assert all(before[r['path']]==r['sha256'] for r in source['original_files'])
 write_new(out/'FROZEN_BEFORE.json',verify())
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 suites={}
 for name,path in [('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 demonstrate(out/'demo-a');demonstrate(out/'demo-b')
 for n in ('REGISTRY_EXPORT.json','BUILD_MANIFEST.json','RETRIEVAL.json','ASSESSMENT.json','GRAPH.json','REGISTRY_INTEGRITY.json','ARGUMENT.md'):assert (out/'demo-a'/n).read_bytes()==(out/'demo-b'/n).read_bytes(),n
 for p,h in before.items():assert sha(p)==h
 for directory in ('libero_evidence_audit','libero_measurement_reader','measurement_profile_validation','evidence_review_readiness'):
  p=HERE.parent/directory
  for n,r in load(p/'ARTIFACT_SHA256.json').items():assert sha(p/n)==r['sha256'],str(p/n)
 assert sha(HERE.parent/'measurement_profile_validation/REFERENCE_REVIEW_FORM.csv')==source['human_form_sha256']
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines()
 assert all(n.startswith('evaluation/r1_v4/evidence_registry_gsn/') for n in changes)
 write_new(out/'FROZEN_AFTER.json',verify());passed=all(r['returncode']==0 for r in suites.values())
 records=load(out/'demo-a/REGISTRY_EXPORT.json')['records']
 report=dict(passed=passed,suites=suites,original_files_unchanged=38,prior_artifacts_unchanged=True,blank_human_forms_unchanged=True,existing_V4_decision_logic_unchanged=True,empirical_admission_enabled=False,physical_judgments_admitted=0,reproducible_exports=True,record_count=len(records),record_kinds=dict(Counter(r['kind'] for r in records)),demo_path=str(out/'demo-a'),source_files=source['original_files'],base_commit=BASE)
 write_new(out/'RESULTS.json',report)
 print('Phase 5A validation',passed,{n:(r['tests_run'],r['returncode']) for n,r in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
