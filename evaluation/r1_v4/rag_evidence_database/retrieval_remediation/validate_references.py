"""Independent reference integrity checks; no target retrieval calls."""
import json,collections
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
def run():
 p=HERE/'FROZEN_HOLDOUT_DATASET.jsonl';qs=[json.loads(l) for l in p.read_text().splitlines()];assert sha(p)==json.loads((HERE/'HOLDOUT_FREEZE.json').read_text())['dataset_sha256'];checks=0;artifacts={};cases=[]
 for q in qs:
  for a in q['source_artifacts']:artifacts[a['path']]=a['sha256']
  with h5py.File(q['source_path'],'r') as f:
   assert f.attrs['global_episode_id']==q['execution_id']
   for family,rows in q['reference_samples'].items():
    for row in rows:
     d=f[row['selector']];assert str(d.dtype)==row['dtype'] and list(d.shape)==row['shape'] and np.array_equal(d[()],row['value']);checks+=1
   for family,m in q['reference_metadata'].items():
    if family=='action_metadata':assert dict(f[m['selector']].attrs)==m['attributes']
    if family=='inference_metadata':assert int(f[m['selector']].attrs['step'])==m['step']
  assert not q['critical_abstention'] or not q['ranking_eligible'];cases.append(dict(id=q['id'],passed=True))
 for path,h in artifacts.items():assert sha(Path(path))==h,path
 result=dict(passed=True,questions=len(qs),source_sample_checks=checks,hashed_artifacts=len(artifacts),dataset_sha256=sha(p),categories=dict(collections.Counter(q['category'] for q in qs)),ranking_eligible=sum(q['ranking_eligible'] for q in qs),critical_abstentions=sum(q['critical_abstention'] for q in qs),multisource_questions=sum(q['multisource_eligible'] for q in qs),cases=cases);(WORK/'REFERENCE_VALIDATION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print({k:v for k,v in result.items() if k!='cases'},flush=True)
if __name__=='__main__':run()
