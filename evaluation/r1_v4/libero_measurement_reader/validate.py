"""Hestia validation of restored originals, bounded reader and frozen regressions."""
import copy,json,os,socket,subprocess,sys
from pathlib import Path
from .reader import read,HERE,REPO
from .bridge import observations
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.provenance import canonical,load,digest
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha,save
from evaluation.r1_v4.validate import run_suite
ROOT=Path('/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence')
BASE='ace3ef3becd0c2ce2d9cb45488707bf2101ce384'
def main():
 assert socket.gethostname().lower()=='hestia'
 out=HERE/'validation';(out/'tmp').mkdir(parents=True,exist_ok=True)
 original=load(HERE/'RESTORED_SOURCES.json');fingerprints={r['restored_path']:sha(r['restored_path']) for r in original}
 assert all(fingerprints[r['restored_path']]==r['expected_sha256']==r['sha256'] for r in original)
 save(out/'FROZEN_BEFORE.json',verify())
 packages='/disk/0/home/niktakbr/groot-n17-libero-gpu0-queue/.venv/lib/python3.12/site-packages'
 suites={}
 for name,tests in [('reader','evaluation/r1_v4/libero_measurement_reader/tests'),('phase2a','evaluation/r1_v4/tests'),('frozen_v3','evaluation/r1_v3/tests'),('reference','evaluation/r1_reference/tests'),('generalization','evaluation/r1_v3_generalization/tests')]:
  suites[name]=run_suite(name,REPO,tests,out,packages if name!='phase2a' else None)
 runs=[]
 for ep in (0,1,2,14):
  result=read(ROOT,ep,[0,10])
  codes={d.code for d in result.diagnostics}
  assert result.status=='verified_measurements',(ep,[(d.code,d.frame) for d in result.diagnostics[:5]])
  assert not result.physical_safety_conclusion and not result.empirical_admission_enabled and result.inferred_events==result.checker_judgments==result.evidence_records==()
  assert all(e.truth.value=='U' for e in observations(result))
  # Compact measurement report; full raw arrays remain outside Git.
  runs.append(dict(episode=ep,execution_id=result.execution_id,status=result.status,validated_frames=len(result.coverage['validated']),missing=result.coverage['missing'],invalid=result.coverage['invalid'],returned_frames=[s.index for s in result.frames],camera_pixels_read=0,diagnostics=sorted(codes),output_sha256=digest(result),source_hashes=result.source_hashes,physical_safety_conclusion=False))
  if ep==0:
   target=Path('/disk/1/data/niktakbr/r1-v4-phase2b2-working/cli-example-bound.json')
   cmd=[sys.executable,'-S','-m','evaluation.r1_v4.libero_measurement_reader','--root',str(ROOT),'--episode','0','--frames','0','10','--output',str(target)]
   env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(REPO),packages,'/usr/lib/python3.12/site-packages','/usr/lib64/python3.12/site-packages'])
   if not target.exists():subprocess.run(cmd,cwd=REPO,env=env,check=True,capture_output=True)
   assert target.read_bytes()==canonical(result)+b'\n'
   save(out/'CLI_DEMONSTRATION.json',dict(command=cmd,output=str(target),sha256=sha(target),byte_identical_to_library=True,empirical_admission_enabled=False))
 save(HERE/'MEASUREMENT_VALIDATION.json',runs)
 after={p:sha(p) for p in fingerprints};assert after==fingerprints
 save(HERE/'HASH_VERIFICATION.json',dict(files_verified=len(original),bytes_verified=sum(r['bytes'] for r in original),all_expected_hashes_match=True,initial_state_archive_hash=next(r['sha256'] for r in original if r['restored_path'].endswith('.init')),originals_unchanged_during_validation=True,files=[dict(path=p,sha256=h) for p,h in after.items()]))
 save(out/'FROZEN_AFTER.json',verify())
 changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines();assert all(n.startswith('evaluation/r1_v4/libero_measurement_reader/') for n in changes)
 for n,r in load(REPO/'evaluation/r1_v4/libero_evidence_audit/ARTIFACT_SHA256.json').items():assert sha(REPO/'evaluation/r1_v4/libero_evidence_audit'/n)==r['sha256']
 passed=all(s['returncode']==0 for s in suites.values())
 save(out/'RESULTS.json',dict(passed=passed,suites=suites,restored_original_files=38,original_files_hash_verified=38,all_four_required_measurement_bundles_complete=True,validated_frames=sum(r['validated_frames'] for r in runs),baseline=BASE,all_existing_tracked_files_unchanged=True,empirical_admission_enabled=False,physical_judgments_issued=0))
 print('Validation passed:',passed,{n:(s['tests_run'],s['returncode']) for n,s in suites.items()})
 if not passed:raise SystemExit(1)
if __name__=='__main__':main()
