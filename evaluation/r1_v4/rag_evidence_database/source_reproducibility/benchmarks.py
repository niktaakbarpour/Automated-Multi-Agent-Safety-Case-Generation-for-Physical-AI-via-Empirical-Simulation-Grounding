"""Unchanged prior benchmarks against the additive release."""
import sys,json
from .config import WORK

def run(which):
 out=WORK/('legacy_'+which)
 if which in ('f','g'):
  from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment import legacy_benchmarks as m
  m.WORK=WORK;m.run(which)
 elif which=='h':
  from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment import validate,semantic_benchmark
  validate.WORK=WORK;validate.run(out);semantic_benchmark.WORK=WORK;semantic_benchmark.run(output=out)
 else:raise ValueError(which)
if __name__=='__main__':run(sys.argv[1])
