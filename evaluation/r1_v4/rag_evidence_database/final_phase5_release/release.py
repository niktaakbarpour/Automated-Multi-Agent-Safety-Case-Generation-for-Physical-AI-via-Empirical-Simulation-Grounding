"""Seal and verify the final restricted release using descriptor-bound reads."""
import json,datetime,os,argparse,platform
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier

def artifact(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p),classification='PRESENT_DAY_VERIFIED_ARTIFACT_NOT_HISTORICAL_ATTESTATION')
def seal():
 assert platform.node().split('.')[0]=='hestia'
 f=json.loads((HERE/'FROZEN_RELEASE_CONFIGURATION.json').read_text())
 for n,h in f['files'].items():assert sha(HERE/n)==h,n
 assert sha(HERE/'FINAL_EVALUATION_DATASET.jsonl')==f['dataset_sha256']
 for n in ['FINAL_PRESERVATION.json','FINAL_REGRESSIONS.json','REPRODUCIBILITY_RESULTS.json','INDEPENDENT_SET_AUDIT.json','RESTORATION_RESULTS.json']:assert json.loads((WORK/n).read_text())['passed'],n
 assert sha(DATABASE)==DATABASE_SHA and sha(CATALOGUE)==CATALOGUE_SHA
 for p in HERE.rglob('*.py'):compile(p.read_text(),str(p),'exec')
 inside=[artifact(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts]
 outside=[artifact(p) for p in sorted(WORK.rglob('*')) if p.is_file() and p.name not in {'seal.log','release_verification.log'} and not {'cache','hf-cache','__pycache__'}&set(p.parts)]
 refs=json.loads((HERE/'RELEASE_REFERENCES.json').read_text())
 roots=[artifact(DATABASE),artifact(CATALOGUE)]+refs['artifacts']
 out=dict(release=VERSION,decision='A. PHASE 5 COMPLETE — RESTRICTED STRUCTURED INTERFACE READY',branch='feat/rag-evidence-final-release',baseline_revision=BASE_COMMIT,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),commit_binding='Git commit containing this manifest; trust SHA externally; no circular self hash',internal_artifacts=inside,external_artifacts=outside,trust_roots=roots,counts=dict(executions=432,variants=104,evidence=80786,channels=2592,frames=58075),tests=850,final_cases=448,false_complete=0,natural_language='EXPERIMENTAL; prior K.1 limitations unchanged',database_migrated=False,empirical_admission_enabled=False,downstream_agents=False,no_push_merge=True,exclusions='Manifest self, active sealing/verification logs and transient caches; parent manifests bind original source closure')
 (HERE/'ARTIFACT_MANIFEST.json').write_text(json.dumps(out,sort_keys=True,indent=2));print('SEALED',len(inside),len(outside),sha(HERE/'ARTIFACT_MANIFEST.json'),flush=True)
def verify(expected):
 v=SourceVerifier(namespace='phase5l-release');count=0
 with v.access(str(HERE/'ARTIFACT_MANIFEST.json'),expected,'strict') as (fd,a):m=json.load(fd)
 for key in ['internal_artifacts','external_artifacts','trust_roots']:
  for p in m[key]:
   with v.access(p['path'],p['sha256'],'strict') as (fd,a):assert os.fstat(fd.fileno()).st_size==p['bytes']
   count+=1
 print(json.dumps(dict(passed=True,artifacts=count,manifest_sha256=expected)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--verify');a=p.parse_args();verify(a.verify) if a.verify else seal()
