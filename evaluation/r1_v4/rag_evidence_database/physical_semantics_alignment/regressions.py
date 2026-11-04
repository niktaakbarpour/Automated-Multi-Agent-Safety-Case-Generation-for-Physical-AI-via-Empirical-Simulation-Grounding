"""Full 578-test baseline plus Phase 5H contract and adversarial tests."""
import json
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import regressions as old
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import HERE as G
from .config import WORK,HERE
from .audit import save

def run():
 out=WORK/'regressions';out.mkdir();old.WORK=out;r=old.run();suites={}
 for name,path in (('phase5g',G/'tests'),('phase5h',HERE/'tests')):
  s=run_suite(name,REPO,str(path),out/'qa','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');suites[name]=s;print(name,s['tests_run'],s['returncode'],flush=True)
 result=dict(passed=r['passed'] and all(s['returncode']==0 for s in suites.values()),tests=r['tests']+sum(s['tests_run'] or 0 for s in suites.values()),skipped=r['skipped']+sum(s['skipped'] for s in suites.values()),baseline_tests=r['tests']+suites['phase5g']['tests_run'],new_tests=suites['phase5h']['tests_run'],suites=suites)
 save(WORK/'REGRESSION_RESULTS.json',result);assert result['passed'] and result['skipped']==0;print('REGRESSIONS COMPLETE',result['tests'],flush=True)
if __name__=='__main__':run()
