"""Release manifest for tracked reports and external validation/source references."""
import json,platform,subprocess,os
from pathlib import Path
from .channels import HERE,WORK,BASE,BASE_SHA,VERSION
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO

def entry(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def run():
 # Reports/code are frozen before this step; manifest and own checksum are excluded.
 files=[entry(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ('ARTIFACT_MANIFEST.json','ARTIFACT_MANIFEST.sha256')]
 external=[]
 for p in sorted(WORK.rglob('*')):
  if p.is_file() and not p.is_symlink():external.append(entry(p))
 for p in (Path('/disk/1/data/niktakbr/trustworthy-phase5g-working-baseline.log'),Path('/disk/1/data/niktakbr/trustworthy-phase5g-working-baseline-attempt2.log'),Path('/disk/1/data/niktakbr/trustworthy-phase5g-working-inventory.log'),Path('/disk/1/data/niktakbr/trustworthy-phase5g-working-spatial.log'),Path('/disk/1/data/niktakbr/trustworthy-phase5g-finalize.log')):
  if p.exists():external.append(entry(p))
 body=dict(version=VERSION,baseline_commit='c24795ed9383110243288db520e5f98af484b4ad',branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),baseline_database=entry(BASE),files=files,external_artifacts=external,source_manifest_references=[str(HERE.parent/'variant_aware_expansion/ARTIFACT_MANIFEST.json'),str(HERE.parent/'variant_aware_expansion/RESTORED_SOURCE_MANIFEST.csv'),str(WORK/'INVENTORY_SUMMARY.json'),str(WORK/'INVENTORY_SUPPLEMENT.json')],counts=dict(executions=432,variants=104,preserved_core_evidence_records=80786,new_channel_records=2592,total_records_across_families=83378,saved_frames=58075,new_channels=6,derived_channels=0),runtime=dict(host=os.uname().nodename,python=platform.python_version(),platform=platform.platform()),empirical_admission_enabled=False,pushed_or_merged=False,scope='Database/retrieval only; physical safety not established',self_checksum='ARTIFACT_MANIFEST.sha256; manifest excludes itself/checksum to avoid recursion')
 assert body['baseline_database']['sha256']==BASE_SHA
 dest=HERE/'ARTIFACT_MANIFEST.json'
 with dest.open('x') as f:json.dump(body,f,sort_keys=True,indent=2)
 with (HERE/'ARTIFACT_MANIFEST.sha256').open('x') as f:f.write(sha(dest)+'  ARTIFACT_MANIFEST.json\n')
 print('Manifest',sha(dest),'tracked',len(files),'external',len(external),flush=True)
if __name__=='__main__':run()
