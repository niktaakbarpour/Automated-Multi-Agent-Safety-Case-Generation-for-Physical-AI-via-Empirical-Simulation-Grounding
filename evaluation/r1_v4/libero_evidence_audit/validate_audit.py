"""Hestia-only analytical regressions and frozen integrity; no simulator runs."""
import json,os,socket,subprocess,sys
from .audit_sources import ROOT,HERE,BASE,load,save,sha
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite

def main():
 assert socket.gethostname().lower()=='hestia'
 out=HERE/'validation';out.mkdir(exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
 before=verify()
 save(out/'INTEGRITY_BEFORE.json',before)
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 suites={}
 for name,tests in [('phase2a','evaluation/r1_v4/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,ROOT,tests,out,None if name=='phase2a' else packages)
 cmd=[sys.executable,'-m','unittest','evaluation.r1_v4.libero_evidence_audit.analytical','-v']
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 (out/'analytical.log').write_text(p.stdout+p.stderr)
 suites['audit_analytical']={'returncode':p.returncode,'tests_run':2,'scenarios':11,'command':cmd,'log_sha256':sha(out/'analytical.log')}
 after=verify();save(out/'INTEGRITY_AFTER.json',after)
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
 assert all(n.startswith('evaluation/r1_v4/libero_evidence_audit/') for n in changes),changes
 for n,h in load(HERE/'SOURCE_BINDINGS.json').items():assert sha(ROOT/n)==h['sha256']
 for p in (HERE/'ANALYTICAL_FIXTURES').glob('*.json'):
  x=load(p);assert x['synthetic'] and not x['empirical_reference']
 sample=load(HERE/'SAMPLE_VALIDATION.json');assert sample['original_recordings_inspected']==0 and sample['overlap_with_frozen_or_heldout']==0
 matrix=__import__('csv').DictReader((HERE/'CAPABILITY_MATRIX.csv').open())
 statuses={'VERIFIED','CONDITIONALLY_SUPPORTED','BLOCKED_ON_EVIDENCE','UNSUPPORTED'}
 rows=list(matrix);assert len(rows)==18 and all(r['status'] in statuses and r['empirical_runtime_enabled']=='False' for r in rows)
 passed=all(s['returncode']==0 for s in suites.values())
 result=dict(passed=passed,suites=suites,sample=sample,all_existing_tracked_files_unchanged=True,baseline=BASE,frozen_before_after_equal=before==after,empirical_admission_enabled=False,physical_verdicts_issued=0)
 save(out/'RESULTS.json',result);print(json.dumps(result))
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
