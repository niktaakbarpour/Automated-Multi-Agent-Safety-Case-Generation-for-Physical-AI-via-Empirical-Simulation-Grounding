"""Rerun unchanged previous benchmarks against the new DB using path aliases only."""
import sys
from .config import WORK

def run(which):
 out=WORK/('legacy_'+which);out.mkdir();(out/'expanded.sqlite').symlink_to(WORK/'expanded.sqlite')
 if which=='f':
  from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import evaluate,negative_evaluate,semantic_evaluate
  for m in (evaluate,negative_evaluate,semantic_evaluate):m.WORK=out;m.run()
 elif which=='g':
  from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion import validate,semantic_evaluate
  validate.WORK=out;validate.run(out/'expanded.sqlite');semantic_evaluate.WORK=out;semantic_evaluate.run()
 else:raise ValueError('f or g')
 print('LEGACY '+which+' COMPLETE',flush=True)
if __name__=='__main__':run(sys.argv[1])
