"""Run all inherited suites without replacing their release artifacts."""
import json
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import regressions
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import HERE as G
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.config import HERE as H
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.integrity import verify
from .config import WORK,HERE

def run():
 out=WORK/'regressions';out.mkdir();regressions.WORK=out;r=regressions.run();suites={}
 for name,path in (('phase5g',G/'tests'),('phase5h',H/'tests'),('phase5i',HERE/'tests')):
  suites[name]=run_suite(name,REPO,str(path),out/'qa','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');assert suites[name]['returncode']==0 and suites[name]['skipped']==0,suites[name]
 result=dict(passed=True,total_tests=r['tests']+sum(s['tests_run'] for s in suites.values()),suites=suites,frozen=verify());(WORK/'REGRESSION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
