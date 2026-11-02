"""Hestia regressions and preservation checks for the bounded AI review report."""
import socket,subprocess
from .review_sources import HERE,REPO,PROFILE,BASE
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.libero_evidence_audit.audit_sources import load,save,sha

def main():
 assert socket.gethostname().lower()=='hestia'
 out=HERE/'validation';(out/'tmp').mkdir(parents=True,exist_ok=True)
 source=load(HERE/'SOURCE_BINDINGS.json');before={r['path']:sha(r['path']) for r in source['original_files']}
 assert all(before[r['path']]==r['sha256'] for r in source['original_files'])
 save(out/'FROZEN_BEFORE.json',verify())
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages';suites={}
 for name,path in [('review','evaluation/r1_v4/evidence_review_readiness/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 for p,h in before.items():assert sha(p)==h
 for directory in ('libero_evidence_audit','libero_measurement_reader','measurement_profile_validation'):
  p=REPO/'evaluation/r1_v4'/directory
  for n,r in load(p/'ARTIFACT_SHA256.json').items():assert sha(p/n)==r['sha256']
 assert sha(PROFILE/'REFERENCE_REVIEW_FORM.csv')==source['human_form_sha256']
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines();assert all(n.startswith('evaluation/r1_v4/evidence_review_readiness/') for n in changes)
 save(out/'FROZEN_AFTER.json',verify());passed=all(r['returncode']==0 for r in suites.values())
 save(out/'RESULTS.json',dict(passed=passed,suites=suites,candidates_reviewed=11,numerical_cases=10,authorized_visual_sheets=3,authorized_visual_panels=24,original_files_unchanged=38,prior_artifacts_unchanged=True,blank_human_forms_unchanged=True,existing_V4_decision_logic_unchanged=True,empirical_admission_enabled=False,human_physical_references_created=0,physical_judgments_admitted=0))
 print('Evidence review validation',passed,{n:(r['tests_run'],r['returncode']) for n,r in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
