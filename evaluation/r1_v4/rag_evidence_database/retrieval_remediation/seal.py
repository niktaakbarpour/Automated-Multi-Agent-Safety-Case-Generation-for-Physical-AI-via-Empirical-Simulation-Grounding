"""Content manifest for K code/reports and bounded external artifacts; not historical attestation."""
import json,datetime,subprocess
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
def artifact(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),classification='RETROSPECTIVE_RELEASE_ARTIFACT')
def run():
 assert subprocess.check_output(['git','branch','--show-current']).decode().strip()=='feat/rag-evidence-retrieval-remediation'
 frozen=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for n,h in frozen['files'].items():assert sha(HERE/n)==h,n
 assert sha(DATABASE)==DATABASE_SHA
 for p in HERE.rglob('*.py'):compile(p.read_text(),str(p),'exec')
 archived=json.loads((HERE/'evaluation_v1/ARCHIVE.json').read_text())
 for n,h in archived['files'].items():assert sha(HERE/'evaluation_v1'/n)==h,n
 internal=[artifact(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json' and '__pycache__' not in p.parts]
 external=[artifact(p) for p in sorted(WORK.rglob('*')) if p.is_file() and p.name not in ('seal.log','seal_final.log','release_verification.log','release_verification_final.log') and 'hf-cache' not in p.parts and 'cache' not in p.parts]
 roots=[DATABASE,HERE.parent/'readiness_evaluation/ARTIFACT_MANIFEST.json',Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/encoder/model.safetensors')]
 for p in roots:assert p.is_file(),p
 result=dict(release='Phase 5K assurance-guard-1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),branch='feat/rag-evidence-retrieval-remediation',parent_revision=BASE_COMMIT,git_commit_binding='Commit containing this manifest; no self-referential commit/hash embedded',recommendation='B. FOCUSED CORRECTION STILL REQUIRED',implementation_complete=True,readiness_success=False,internal_artifacts=internal,external_artifacts=external,trust_roots=[artifact(p) for p in roots],database_preserved=True,counts=dict(executions=432,variants=104,evidence=80786,channels=2592,frames=58075),test_counts=dict(inherited=718,phase5j=7,phase5k=39,total=764,failures=0,skips=0),integrity='Verify this manifest against the trusted local Git commit, then all entries; newly computed hashes establish present bytes only, not historical recording-time identity',excluded=dict(self_manifest='Self hash reported by Git/final response',runtime_caches='Transient caches; model separately pinned',seal_log='Active sealing output; not evidence'),no_push_or_merge=True,empirical_admission_enabled=False,safety_agents_implemented=False)
 (HERE/'ARTIFACT_MANIFEST.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('SEALED',len(internal),len(external),sha(HERE/'ARTIFACT_MANIFEST.json'),flush=True)
if __name__=='__main__':run()
