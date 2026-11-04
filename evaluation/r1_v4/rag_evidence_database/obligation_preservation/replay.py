"""Fresh/full/partial replay; verify saved outputs instead of trusting cached scores."""
import json,shutil
from .config import *
from .evaluate import run,canonical
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def replay():
 dataset=HERE/'FROZEN_EVALUATION_DATASET.jsonl';first=run(dataset,'final_v2');assert first['resumed']==288
 independent=run(dataset,'independent_v2');assert independent['canonical_digest']==first['canonical_digest']
 partial=run(dataset,'partial_v2',limit=37);assert partial['instances']==37
 full=run(dataset,'partial_v2');assert full['resumed']==37 and full['canonical_digest']==first['canonical_digest']
 dictionaries={};count=0
 for label in ('final_v2','independent_v2','partial_v2'):
  rows={}
  for p in (WORK/label).glob('*.json'):
   r=json.loads(p.read_text());assert r['canonical_digest']==digest(canonical({k:v for k,v in r.items() if k!='canonical_digest'}));rows[p.name]=r['canonical_digest'];count+=1
  dictionaries[label]=rows
 assert dictionaries['final_v2']==dictionaries['independent_v2']==dictionaries['partial_v2']
 example=json.loads(next((WORK/'final_v2').glob('*.json')).read_text());example['output']['completeness_status']='forged';assert example['canonical_digest']!=digest(canonical({k:v for k,v in example.items() if k!='canonical_digest'}))
 result=dict(passed=True,fresh=independent,full_resume=first,partial_resume=full,exact_case_equivalence=True,validated_case_files=count,changed_output_detected=True,database_sha256=sha(DATABASE),catalogue_sha256=sha(CATALOGUE),human_replication=False);assert result['database_sha256']==DATABASE_SHA and result['catalogue_sha256']==CATALOGUE_SHA;(WORK/'REPLAY_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('REPLAY VERIFIED',count,flush=True)
if __name__=='__main__':replay()
