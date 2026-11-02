"""Pin release content, preserved baselines and external proof artifacts."""
import json,platform,os,subprocess
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import BASE as F,BASE_SHA as F_SHA
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.plan import BASE as E,BASE_SHA as E_SHA
from .config import HERE,WORK,BASE,BASE_SHA,BASE_COMMIT,VERSION

def entry(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def run():
 originals=[entry(p) for p in (E,F,BASE)];assert [r['sha256'] for r in originals]==[E_SHA,F_SHA,BASE_SHA]
 files=[entry(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ('ARTIFACT_MANIFEST.json','ARTIFACT_MANIFEST.sha256')]
 external=[entry(p) for p in sorted(WORK.rglob('*')) if p.is_file() and not p.is_symlink()]
 release=entry(WORK/'expanded.sqlite');body=dict(version=VERSION,baseline_commit=BASE_COMMIT,branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),release_database=release,original_databases=originals,files=files,external_artifacts=external,baseline_manifest=entry(HERE.parent/'measurement_channel_expansion/ARTIFACT_MANIFEST.json'),counts=dict(executions=432,variants=104,preserved_core_records=80786,preserved_phase5g_series=2592,total_measurement_records=83378,interpretation_annotations=2592,execution_timelines=432,model_maps=104,new_measurement_channels=0,new_execution_profiles=0),runtime=dict(host=os.uname().nodename,python=platform.python_version(),platform=platform.platform()),empirical_admission_enabled=False,pushed_or_merged=False,source_contract='strict descriptor-bound reads or explicit verified-session cache; no unverified mode',self_exclusion='Manifest and its checksum are excluded from file list to avoid recursion; Git commit seals tracked content.')
 dest=HERE/'ARTIFACT_MANIFEST.json'
 with dest.open('x') as f:json.dump(body,f,sort_keys=True,indent=2)
 with (HERE/'ARTIFACT_MANIFEST.sha256').open('x') as f:f.write(sha(dest)+'  ARTIFACT_MANIFEST.json\n')
 print('RELEASE MANIFEST',sha(dest),'files',len(files),'external',len(external),flush=True)
if __name__=='__main__':run()
