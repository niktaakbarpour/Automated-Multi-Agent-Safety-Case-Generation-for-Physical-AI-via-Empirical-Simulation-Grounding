"""Independent frozen-reference consistency and raw source validation; no target calls."""
import json,collections
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
def run():
 cfg=json.loads((HERE/'FROZEN_CONFIGURATION.json').read_text());assert sha(HERE/'FROZEN_EVALUATION_DATASET.jsonl')==cfg['dataset_sha256'];assert sha(HERE/'REFERENCE_OBLIGATIONS.jsonl')==cfg['references_sha256'];rows=[json.loads(l) for l in (HERE/'FROZEN_EVALUATION_DATASET.jsonl').read_text().splitlines()];ref={q['case_id']:q for q in map(json.loads,(HERE/'REFERENCE_OBLIGATIONS.jsonl').read_text().splitlines())};artifacts={};comparisons=0
 for q in rows:
  assert q['reference_obligations']==ref[q['id']]['obligations'];assert q['request']['execution_id']==q['execution_id'] or q['expected_status']=='INVALID SCOPE'
  with h5py.File(q['source_path'],'r') as f:
   assert f.attrs['global_episode_id']==q['execution_id']
   for ch,values in q['reference_samples'].items():
    for v in values:
     d=f[v['selector']];assert np.array_equal(v['value'],d[()]) and v['dtype']==str(d.dtype) and v['shape']==list(d.shape);comparisons+=1
  for a in q['source_artifacts']:artifacts[a['path']]=a['sha256']
 for path,h in artifacts.items():assert sha(Path(path))==h,path
 result=dict(passed=True,questions=len(rows),formulations=len({q['authored_template'] for q in rows}),source_sample_comparisons=comparisons,hashed_artifacts=len(artifacts),mandatory_obligations=sum(len(q['reference_obligations']) for q in rows),categories=dict(collections.Counter(q['category'] for q in rows)),critical=sum(q['critical'] for q in rows),full_expected=sum(q['expected_status']=='COMPLETE WITHIN VERIFIED CONTRACT' for q in rows),partial_expected=sum(q['expected_status']=='PARTIAL' for q in rows));(WORK/'REFERENCE_VALIDATION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
