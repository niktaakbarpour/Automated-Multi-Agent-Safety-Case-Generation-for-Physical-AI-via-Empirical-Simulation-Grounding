"""Audit-only QA while production-profile expansion scope is unresolved."""
import os
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.audit import HERE
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.validate import run_suite

def main():
 out=Path('/disk/1/data/niktakbr/trustworthy-phase5d-working/audit-validation');out.mkdir();(out/'tmp').mkdir()
 before=verify();write_new(out/'FROZEN_BEFORE.json',before)
 os.environ['RAG_TEST_DB']='/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite'
 os.environ['RAG_EXPANSION_DB']='/disk/1/data/niktakbr/trustworthy-phase5c-working/development-40.sqlite'
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages';suites={}
 for name,path in [('partition_audit','evaluation/r1_v4/rag_evidence_database/corpus_expansion/tests'),('phase5c','evaluation/r1_v4/rag_evidence_database/expansion/tests'),('phase5b','evaluation/r1_v4/rag_evidence_database/tests'),('registry_gsn','evaluation/r1_v4/evidence_registry_gsn/tests'),('phase2a','evaluation/r1_v4/tests'),('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('profile','evaluation/r1_v4/measurement_profile_validation/tests'),('review','evaluation/r1_v4/evidence_review_readiness/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,path,out,None if name=='phase2a' else packages)
 previous=HERE.parent/'expansion'
 for n,r in load(previous/'ARTIFACT_SHA256.json').items():assert sha(previous/n)==r['sha256']
 assert sha(os.environ['RAG_EXPANSION_DB'])=='e5dc6aadd9444d945abe9aeb1c54461b0cd6ad5308b43c6fdc40fac65c8d07ca'
 write_new(out/'FROZEN_AFTER.json',verify());passed=all(r['returncode']==0 for r in suites.values())
 write_new(out/'RESULTS.json',{'passed':passed,'tests':sum(r['tests_run'] for r in suites.values()),'suites':suites,'new_executions_restored':0,'new_executions_indexed':0,'status':'AUDIT_COMPLETE_EXPANSION_BLOCKED_ON_PROFILE_SCOPE','previous_release_unchanged':True,'empirical_admission_enabled':False})
 print('Partition audit QA',passed,{n:(r['tests_run'],r['returncode']) for n,r in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
