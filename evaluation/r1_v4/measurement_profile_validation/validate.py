"""Hestia-only profile QA; existing runtime and historical artifacts are immutable."""
import json,socket,subprocess
from .analyze import HERE,REPO,BASE
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha,load,save
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite

def main():
 assert socket.gethostname().lower()=='hestia'
 out=HERE/'validation';(out/'tmp').mkdir(parents=True,exist_ok=True)
 sources=load(HERE/'SOURCE_BINDINGS.json');before={r['path']:sha(r['path']) for r in sources['recordings']}
 assert all(before[r['path']]==r['sha256'] for r in sources['recordings'])
 save(out/'FROZEN_BEFORE.json',verify())
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 suites={}
 for name,path in [('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 assert all(sha(p)==h for p,h in before.items())
 for directory in ('libero_evidence_audit','libero_measurement_reader'):
  root=REPO/'evaluation/r1_v4'/directory
  for n,r in load(root/'ARTIFACT_SHA256.json').items():assert sha(root/n)==r['sha256']
 for n,h in sources['prior_files'].items():assert sha(REPO/n)==h
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines();assert all(n.startswith('evaluation/r1_v4/measurement_profile_validation/') for n in changes)
 save(out/'FROZEN_AFTER.json',verify())
 passed=all(r['returncode']==0 for r in suites.values())
 save(out/'RESULTS.json',dict(passed=passed,suites=suites,original_source_files_unchanged=38,prior_audit_reader_artifacts_unchanged=True,existing_V4_logic_unchanged=True,empirical_admission_enabled=False,physical_judgments_issued=0,independent_reference_cases=0,visual_review_performed=False))
 print('Profile validation',passed,{n:(r['tests_run'],r['returncode']) for n,r in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
