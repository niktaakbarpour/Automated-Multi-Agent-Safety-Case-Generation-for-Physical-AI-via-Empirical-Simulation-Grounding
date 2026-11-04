"""Full Phase5E suite plus additive variant tests; no skipped/failed tests hidden."""
import os
from evaluation.r1_v4.provenance import write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.validate import run_suite
from evaluation.r1_v4.integrity import verify
from .plan import WORK,BASE

def run():
 out=WORK/'qa';out.mkdir();(out/'tmp').mkdir();write_new(out/'FROZEN_BEFORE.json',verify())
 os.environ.update(RAG_TEST_DB='/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite',RAG_EXPANSION_DB='/disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite',RAG_NEW_TASK_DB='/disk/1/data/niktakbr/trustworthy-phase5d-working/final-validated/corpus-89.sqlite',RAG_MULTITASK_DB=str(BASE),RAG_SEMANTIC_DB='/disk/1/data/niktakbr/trustworthy-phase5e-working/final-validated/semantic.sqlite')
 groups=[('variant','evaluation/r1_v4/rag_evidence_database/variant_aware_expansion/tests'),('phase5e','evaluation/r1_v4/rag_evidence_database/multitask_expansion/tests'),('phase5e_semantic','evaluation/r1_v4/rag_evidence_database/multitask_expansion/semantic_tests'),('new_profile','evaluation/r1_v4/rag_evidence_database/corpus_expansion/task_profile/tests'),('partition','evaluation/r1_v4/rag_evidence_database/corpus_expansion/tests'),('phase5c','evaluation/r1_v4/rag_evidence_database/expansion/tests'),('phase5b','evaluation/r1_v4/rag_evidence_database/tests'),('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]
 suites={}
 for name,path in groups:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else '/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages');print(name,suites[name]['tests_run'],suites[name]['returncode'],flush=True)
 write_new(out/'FROZEN_AFTER.json',verify());report={'passed':all(v['returncode']==0 for v in suites.values()),'tests':sum(v['tests_run'] or 0 for v in suites.values()),'skipped':sum(v['skipped'] for v in suites.values()),'suites':suites};write_new(WORK/'REGRESSION_RESULTS.json',report)
 if not report['passed']:raise SystemExit('Regression failure; preserve logs and fix')
 return report
if __name__=='__main__':run()
