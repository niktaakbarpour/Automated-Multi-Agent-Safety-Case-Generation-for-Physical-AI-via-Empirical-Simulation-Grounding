"""Retain inherited results and rerun expanded new tests after final implementation."""
import json
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.integrity import verify
from .config import WORK,HERE
if __name__=='__main__':
 result=json.loads((WORK/'REGRESSION.json').read_text());(WORK/'REGRESSION_PRE_RELEASE_CHECK_TESTS.json').write_text(json.dumps(result,sort_keys=True,indent=2))
 (WORK/'regressions'/'qa_release').mkdir(exist_ok=True)
 suite=run_suite('phase5i_final',REPO,str(HERE/'tests'),WORK/'regressions'/'qa_release','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');assert suite['returncode']==0 and suite['skipped']==0,suite
 result['suites']['phase5i']=suite;result['total_tests']=665+suite['tests_run'];result['frozen']=verify();(WORK/'REGRESSION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('FINAL REGRESSIONS',result['total_tests'],flush=True)
