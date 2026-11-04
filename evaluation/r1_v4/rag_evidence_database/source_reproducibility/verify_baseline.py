import json
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import regressions
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import HERE as G
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.config import HERE as H
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.integrity import verify
w=Path('/disk/1/data/niktakbr/trustworthy-phase5i-working');out=w/'baseline';out.mkdir();regressions.WORK=out;r=regressions.run();suites={}
for name,path in (('phase5g',G/'tests'),('phase5h',H/'tests')):
 suites[name]=run_suite(name,REPO,str(path),out/'qa','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');assert suites[name]['returncode']==0 and suites[name]['skipped']==0
result=dict(passed=True,total_tests=r['tests']+sum(s['tests_run'] for s in suites.values()),suites=suites,frozen=verify());assert result['total_tests']==665
with (w/'BASELINE_VERIFIED.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2)
print('BASELINE COMPLETE',flush=True)
