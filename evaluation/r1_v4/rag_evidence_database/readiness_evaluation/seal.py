"""Current-byte evaluation manifest; not a historical attestation or readiness score."""
import json
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *

def run():
 rows={}
 def add(p,h=None,role='evaluation'):
  p=Path(p);row=dict(path=str(p),bytes=p.stat().st_size,sha256=h or sha(p),role=role)
  if str(p) in rows:assert rows[str(p)]['sha256']==row['sha256']
  else:rows[str(p)]=row
 exclude={'ARTIFACT_MANIFEST.json','ARTIFACT_MANIFEST.sha256','RELEASE_VERIFICATION_RESULT.json'}
 for p in sorted(HERE.rglob('*')):
  if p.is_file() and p.name not in exclude and '__pycache__' not in p.parts:add(p)
 for p in sorted(WORK.rglob('*')):
  if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:add(p)
 config=json.loads((HERE/'FROZEN_EVALUATION_CONFIGURATION.json').read_text());data=json.loads((HERE/'DATASET_FREEZE.json').read_text());assoc=json.loads((HERE/'SOURCE_ASSOCIATIONS.json').read_text())
 for p,h in config['implementation_files'].items():add(REPO/p,h,'evaluated_implementation')
 for p,h in data['reference_artifacts'].items():add(p,h,'reference_source')
 for p,h in assoc['verified_artifacts'].items():add(p,h,'index_source_binding')
 for n in ('encoder_manifest','legacy_semantic_sidecar'):add(config[n]['path'],config[n]['sha256'],'semantic_artifact')
 model=json.loads(Path(config['encoder_manifest']['path']).read_text())
 for row in model['files']:add(row['path'],row['sha256'],'semantic_model_file')
 add(DATABASE,DATABASE_SHA,'preserved_database');parent=HERE.parent/'source_reproducibility'/'ARTIFACT_MANIFEST.json';add(parent,'d9953192386904e5778050b89770e0f4693c9c86e6cc9ba3b622826e7fe93e93','parent_release')
 result=dict(version='phase5j-readiness-evaluation-1',baseline_commit=BASE_COMMIT,baseline_database_sha256=DATABASE_SHA,recommendation='B',physical_safety_accuracy='NOT_EVALUATED',artifacts=sorted(rows.values(),key=lambda x:x['path']),self_exclusions=dict(manifest='Cannot hash itself',checksum='References manifest hash',verification_result='References manifest hash; committed with manifest'),frozen_results_unchanged=True,known_invalid_sufficiency_cases=['C7-06','C7-20'])
 p=HERE/'ARTIFACT_MANIFEST.json';p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(HERE/'ARTIFACT_MANIFEST.sha256').write_text(sha(p)+'  ARTIFACT_MANIFEST.json\n');print('SEALED',len(rows),sha(p),flush=True)
if __name__=='__main__':run()
