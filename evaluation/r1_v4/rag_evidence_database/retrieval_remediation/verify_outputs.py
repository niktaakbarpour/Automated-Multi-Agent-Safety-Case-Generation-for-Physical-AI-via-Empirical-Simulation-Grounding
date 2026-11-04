"""Independent saved-output/binding validation, required before trusting a resumed run."""
import json,tempfile
from pathlib import Path
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
from .run_eval import canonical

def check_record(r):
 assert r['canonical_digest']==digest(canonical({k:v for k,v in r.items() if k!='canonical_digest'})),'changed_case_output'
def run():
 qs={q['id']:q for q in map(json.loads,(HERE/'FROZEN_HOLDOUT_DATASET.jsonl').read_text().splitlines())};outputs={};count=0
 for label in ('holdout_guard_v2','holdout_guard_independent','holdout_guard_partial'):
  config=json.loads((WORK/(label+'_CONFIGURATION.json')).read_text());assert config['dataset_sha256']==sha(HERE/'FROZEN_HOLDOUT_DATASET.jsonl');hashes={}
  for p in sorted((WORK/label).glob('*.json')):
   r=json.loads(p.read_text());check_record(r);q=qs[r['case_id']];assert r['input_digest']==digest([q,r['mode'],DATABASE_SHA,sha(WORK/'catalogue.sqlite'),config['code']]);hashes[p.name]=r['canonical_digest'];count+=1
  assert len(hashes)==1296;outputs[label]=hashes
 assert outputs['holdout_guard_v2']==outputs['holdout_guard_independent']==outputs['holdout_guard_partial']
 original=json.loads(next((WORK/'holdout_guard_v2').glob('*.json')).read_text());tampered=json.loads(json.dumps(original));tampered['status']='forged_complete';detected=False
 try:check_record(tampered)
 except AssertionError:detected=True
 assert detected
 result=dict(passed=True,case_files_independently_validated=count,exact_case_output_equivalence=True,changed_output_negative_control_detected=detected,output_validation_required_before_resume=True);(WORK/'OUTPUT_REPLAY_VERIFICATION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
