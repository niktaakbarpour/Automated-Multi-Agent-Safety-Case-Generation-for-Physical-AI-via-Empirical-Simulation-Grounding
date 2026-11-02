"""Frozen twelve probes through the Phase 5I assurance interface."""
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment import semantic_benchmark as benchmark
from .config import WORK
from .store import ProvenanceStore
from .retrieve import ProvenanceQuery,retrieve
if __name__=='__main__':
 benchmark.WORK=WORK;benchmark.PhysicalStore=ProvenanceStore;benchmark.PhysicalQuery=ProvenanceQuery;benchmark.retrieve=retrieve;benchmark.run(output=WORK/'semantic_i')
