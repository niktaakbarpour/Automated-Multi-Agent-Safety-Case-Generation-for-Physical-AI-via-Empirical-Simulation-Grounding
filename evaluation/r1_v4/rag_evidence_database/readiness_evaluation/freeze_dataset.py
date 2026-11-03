"""Audit original-source reference values, then freeze final questions before target execution."""
import json,collections,sqlite3,shutil
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *

def run():
 cases=[json.loads(x) for x in (WORK/'DATASET_DRAFT.jsonl').read_text().splitlines()];c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);checked=0;sourcehash={};metadata={}
 for q in cases:
  assert c.execute("select status from rag_scope_status where execution=?",(q['execution_id'],)).fetchone()==('indexed',)
  assert q['physical_safety_sufficiency']=='NOT_EVALUATED' and not q['reference_supports_safety_claim'];q['known_ambiguity']=q['ambiguity'];q['expected_assurance_status']=q['request'].get('assurance','legacy_source_hash' if q['endpoint']=='legacy' else 'verified_source_values')
  q['expected_factual_result']=q.get('factual_claim',q.get('geometry_reference',dict(required_facets=q['required_facets'],contract_boundary=q['expected_status'])))
  for s in q['reference_samples']:
   p=q['reference_artifacts'][0]['path']
   with h5py.File(p,'r') as f:
    d=f[s['selector']];assert str(d.dtype)==s['dtype'] and list(d.shape)==s['shape'];assert np.array_equal(d[()],np.asarray(s['value']));checked+=1
  for a in q['reference_artifacts']:
   p=a['path']
   if p not in sourcehash:sourcehash[p]=sha(p)
   assert sourcehash[p]==a['sha256']
  if 'producer_version_declaration' in q['required_facets']:
   p=Path(q['reference_artifacts'][0]['path']).parent/'run_metadata.json';q['expected_factual_result']=dict(mujoco_version_declaration=json.loads(p.read_text())['versions']['mujoco'],historical_binary_attested=False)
  if 'checkpoint_declaration' in q['required_facets']:
   p=Path(q['reference_artifacts'][0]['path']).parent/'run_metadata.json';q['expected_factual_result']=dict(checkpoint_hash_declarations=json.loads(p.read_text())['checkpoint_weight_sha256'],historical_binary_attested=False)
 assert len(cases)==198;assert len({q['natural_language_query'] for q in cases})==198
 with (HERE/'EVALUATION_DATASET.jsonl').open('x') as f:
  for q in cases:f.write(json.dumps(q,sort_keys=True,allow_nan=False)+'\n')
 shutil.copyfile(WORK/'SELECTION_DRAFT.json',HERE/'EVALUATION_SELECTION.json')
 info=dict(version='readiness-questions-v1',dataset_sha256=sha(HERE/'EVALUATION_DATASET.jsonl'),configuration_sha256=sha(HERE/'FROZEN_EVALUATION_CONFIGURATION.json'),criteria_sha256=sha(HERE/'ACCEPTANCE_CRITERIA.json'),unique_questions=198,unique_authored_formulations=198,splits=dict(collections.Counter(q['split'] for q in cases)),categories=dict(collections.Counter(q['category'] for q in cases)),executions=len({q['execution_id'] for q in cases}),variants=len({q['variant_id'] for q in cases}),suite_distribution=dict(collections.Counter(q['suite'] for q in cases)),independent_reference_sample_checks=checked,reference_artifacts=sourcehash,reference_method='Original HDF5/JSON/XML through an independent inspection path, same installed h5py library. Registry IDs enumerate existing index links only; no target retrieval output copied.',human_evaluation=False,expert_review_performed=False,final_target_queries_run=0)
 with (HERE/'DATASET_FREEZE.json').open('x') as f:json.dump(info,f,sort_keys=True,indent=2)
 for n in ('EVALUATION_DATASET.jsonl','DATASET_FREEZE.json','EVALUATION_SELECTION.json','FROZEN_EVALUATION_CONFIGURATION.json','ACCEPTANCE_CRITERIA.json'):(HERE/n).chmod(0o444)
 print('DATASET FROZEN',info['dataset_sha256'],info['splits'],checked,flush=True)
if __name__=='__main__':run()
