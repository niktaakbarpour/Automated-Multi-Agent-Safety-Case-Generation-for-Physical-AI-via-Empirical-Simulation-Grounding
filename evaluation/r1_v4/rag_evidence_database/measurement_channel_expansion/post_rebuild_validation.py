"""Resume validation after retained initial performance diagnostic runs."""
from .channels import WORK,HERE
from .validate import run,save

def main():
 run(WORK/'expanded.sqlite')
 from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import evaluate,negative_evaluate,semantic_evaluate,regressions
 legacy=WORK/'legacy';legacy.mkdir();(legacy/'expanded.sqlite').symlink_to(WORK/'expanded.sqlite')
 for module in (evaluate,negative_evaluate,semantic_evaluate):module.WORK=legacy
 evaluate.run();negative_evaluate.run();semantic_evaluate.run()
 regressions.WORK=WORK/'regressions';regressions.WORK.mkdir();regressions.run()
 from evaluation.r1_v4.validate import run_suite
 from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
 result=run_suite('channels',REPO,str(HERE/'tests'),regressions.WORK/'qa','/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');save('CHANNEL_TESTS.json',result);assert result['returncode']==0 and result['skipped']==0
 print('FULL VERIFICATION COMPLETE',flush=True)
if __name__=='__main__':main()
