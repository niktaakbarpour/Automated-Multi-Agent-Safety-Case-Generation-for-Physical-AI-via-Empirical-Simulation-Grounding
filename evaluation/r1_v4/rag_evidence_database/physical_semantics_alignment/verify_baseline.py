import json,sqlite3
from pathlib import Path
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import regressions
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import HERE as G
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
w=Path('/disk/1/data/niktakbr/trustworthy-phase5h-working');out=w/'baseline';out.mkdir();regressions.WORK=out;regressions.run()
r=run_suite('phase5g',REPO,str(G/'tests'),out/'qa','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');assert r['returncode']==0 and r['tests_run']==57 and r['skipped']==0
with (w/'BASELINE_VERIFIED.json').open('x') as f:json.dump(dict(passed=True,phase5g_tests=r,total_tests=578,frozen=verify()),f,sort_keys=True,indent=2)
print('BASELINE COMPLETE',flush=True)
