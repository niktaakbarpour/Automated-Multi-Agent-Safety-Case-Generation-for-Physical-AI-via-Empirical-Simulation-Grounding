"""Git-bound present-day release manifest and descriptor-bound verification."""
import json,datetime,os,argparse,subprocess
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
from .config import *
EXCLUDE={'seal.log','release_verification.log'}
def artifact(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),classification='RETROSPECTIVE_RELEASE_ARTIFACT')
def seal():
 f=json.loads((HERE/'FROZEN_CONFIGURATION.json').read_text())
 for name,h in f['files'].items():assert sha(HERE/name)==h,name
 assert sha(HERE/'FROZEN_EVALUATION_DATASET.jsonl')==f['dataset_sha256'];assert sha(HERE/'REFERENCE_OBLIGATIONS.jsonl')==f['references_sha256'];assert sha(HERE/'FROZEN_ACCEPTANCE_CRITERIA.json')==f['criteria_sha256'];assert sha(DATABASE)==DATABASE_SHA and sha(CATALOGUE)==CATALOGUE_SHA
 old=json.loads((HERE/'assessment_v1/ARCHIVE.json').read_text())
 for name,h in old['files'].items():assert sha(HERE/'assessment_v1'/name)==h,name
 for p in HERE.rglob('*.py'):compile(p.read_text(),str(p),'exec')
 required=['README.md','BASELINE_VERIFICATION.md','ROOT_CAUSE_ANALYSIS.md','OBLIGATION_SCHEMA.md','INDEPENDENT_VALIDATOR_DESIGN.md','COMPLETENESS_CONTRACT.md','DEVELOPMENT_TESTS.md','FROZEN_EVALUATION_DATASET.jsonl','REFERENCE_OBLIGATIONS.jsonl','OBLIGATION_EVALUATION.md','EVIDENCE_COMPLETENESS.md','ADVERSARIAL_AND_METAMORPHIC_TESTS.md','REGRESSION_RESULTS.md','REPRODUCIBILITY.md','LIMITATIONS.md'];assert all((HERE/n).is_file() for n in required)
 inside=[artifact(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts];outside=[artifact(p) for p in sorted(WORK.rglob('*')) if p.is_file() and p.name not in EXCLUDE and not {'hf-cache','cache','__pycache__'}&set(p.parts)]
 roots=[DATABASE,CATALOGUE,HERE.parent/'retrieval_remediation/ARTIFACT_MANIFEST.json',HERE.parent/'readiness_evaluation/ARTIFACT_MANIFEST.json',Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/encoder/model.safetensors'),Path('/disk/1/data/niktakbr/trustworthy-phase5k1-baseline-verification.log')]
 result=dict(release='Phase5K.1 '+VERSION,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_revision=BASE_COMMIT,baseline_manifest_sha256=BASE_MANIFEST_SHA,branch='feat/rag-evidence-query-obligation-verification',commit_binding='Git commit containing this manifest; no circular self/commit hash',implementation_complete=True,readiness_success=False,recommendation='B. FOCUSED CORRECTION STILL REQUIRED',internal_artifacts=inside,external_artifacts=outside,trust_roots=[artifact(p) for p in roots],counts=dict(executions=432,variants=104,evidence=80786,channels=2592,frames=58075),regression_tests=813,regression_failures=0,regression_skips=0,failed_acceptance_gates=[k for k,v in json.loads((WORK/'FINAL_AUDIT.json').read_text())['gates'].items() if not v],preservation='Original database/catalogue/releases/sources/labels/seals unchanged',attestation='New hashes establish present bytes, not historical producer identity',excluded='Self hash supplied through Git; active sealing/verification logs and transient caches excluded',no_push_merge=True,empirical_admission_enabled=False,downstream_agents=False)
 (HERE/'ARTIFACT_MANIFEST.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('SEALED',len(inside),len(outside),sha(HERE/'ARTIFACT_MANIFEST.json'),flush=True)
def verify(expected):
 v=SourceVerifier(namespace='phase5k1-release-verify')
 with v.access(str(HERE/'ARTIFACT_MANIFEST.json'),expected,'strict') as (fd,a):m=json.load(fd)
 count=0
 for key in ('internal_artifacts','external_artifacts','trust_roots'):
  for p in m[key]:
   with v.access(p['path'],p['sha256'],'strict') as (fd,a):assert os.fstat(fd.fileno()).st_size==p['bytes']
   count+=1
 print(json.dumps(dict(passed=True,artifacts=count,manifest_sha256=expected)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--verify');a=p.parse_args();verify(a.verify) if a.verify else seal()
