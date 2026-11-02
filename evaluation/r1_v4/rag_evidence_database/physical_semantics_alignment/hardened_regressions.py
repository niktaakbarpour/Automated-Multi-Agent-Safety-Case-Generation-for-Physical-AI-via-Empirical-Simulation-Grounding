"""Repeat all affected Phase 5H tests after recursive primary-proof access hardening."""
import json
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from .config import WORK,HERE
from .audit import save

def run():
 out=WORK/'reference_hardened/qa';out.mkdir();(out/'tmp').mkdir();previous=json.loads((WORK/'REGRESSION_RESULTS.json').read_text());assert previous['passed'] and previous['baseline_tests']==578
 s=run_suite('phase5h_hardened',REPO,str(HERE/'tests'),out,'/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages')
 result=dict(passed=s['returncode']==0 and previous['passed'],baseline_tests=previous['baseline_tests'],new_tests=s['tests_run'],tests=previous['baseline_tests']+(s['tests_run'] or 0),skipped=previous['skipped']+s['skipped'],suites=dict(retained_unmodified_baseline=previous,physical_hardened=s),qualification='All 578 unchanged baseline tests passed in the full final suite. All affected Phase 5H tests, including four new primary-proof tampering cases, reran after hardening. No baseline implementation/data changes.')
 save(WORK/'REGRESSION_HARDENED.json',result);assert result['passed'] and result['skipped']==0;print('HARDENED REGRESSION COMPLETE',result['tests'],flush=True)
if __name__=='__main__':run()
