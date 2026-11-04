"""Complete reproducibility validation; create-only reports preserve failed diagnostics."""
from pathlib import Path
import json
from .channels import WORK,HERE,ChannelStore
from .build import populate
from .validate import run,save,preserve

def main():
 primary=WORK/'expanded.sqlite';fresh=WORK/'independent.sqlite'
 first=json.loads((WORK/'BUILD.json').read_text());resume=populate(primary);save('RESUME.json',resume)
 assert resume['inserted']==0 and resume['skipped']==432 and resume['logical_digest']==first['logical_digest']
 second=populate(fresh);save('INDEPENDENT_BUILD.json',second)
 assert second['logical_digest']==first['logical_digest'];save('REBUILD_VALIDATION.json',dict(passed=True,logical_digest=first['logical_digest'],resume_inserted=0,resume_skipped=432,independent_records=second['records'],independent_preservation=preserve(fresh)))
 run(primary)
 from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import evaluate,negative_evaluate,semantic_evaluate,regressions
 legacy=WORK/'legacy';legacy.mkdir();
 # Existing routines operate on a read-only primary DB via a path alias to avoid a duplicate.
 (legacy/'expanded.sqlite').symlink_to(primary)
 for module in (evaluate,negative_evaluate,semantic_evaluate):module.WORK=legacy
 evaluate.run();negative_evaluate.run();semantic_evaluate.run()
 regressions.WORK=WORK/'regressions';regressions.WORK.mkdir();regressions.run()
 from evaluation.r1_v4.validate import run_suite
 from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
 result=run_suite('channels',REPO,str(HERE/'tests'),regressions.WORK/'qa','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');save('CHANNEL_TESTS.json',result);assert result['returncode']==0 and result['skipped']==0
 print('FULL VERIFICATION COMPLETE',flush=True)
if __name__=='__main__':main()
