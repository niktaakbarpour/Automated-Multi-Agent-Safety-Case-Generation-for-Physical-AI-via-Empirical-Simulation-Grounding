"""Deterministic independent replay with atomic case files and idempotent resume."""
import json,argparse,hashlib,time,re
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import digest
from .config import *
from .harness import Harness
from .assessment import assess

def canonical(r):
 r=json.loads(json.dumps(r))
 if r.get('fault'):
  r['fault'].pop('scratch_sha256',None)
  if r.get('output',{}).get('reason'):r['output']['reason']=re.sub(re.escape(str(WORK))+r'/fault-[^/ ]+','<scratch>',r['output']['reason'])
 return r

def run(split,label,case_limit=None):
 out=WORK/label;out.mkdir(exist_ok=True);cases=[json.loads(x) for x in (HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines()];cases=[q for q in cases if q['split']==split]
 if split=='final':
  h=json.loads((HERE/'HARNESS_VERSION.json').read_text())
  for n,v in h['files'].items():assert sha(HERE/n)==v,n
 pairs=sorted([(q,m) for q in cases for m in MODES],key=lambda qm:hashlib.sha256((SEED+qm[0]['id']+qm[1]).encode()).hexdigest())
 if case_limit is not None:pairs=pairs[:case_limit]
 harness=Harness();resumed=0;completed=[];start=time.perf_counter()
 try:
  for i,(q,mode) in enumerate(pairs):
   p=out/(q['id']+'-'+mode+'.json');binding=digest(dict(case=q,mode=mode,database=DATABASE_SHA,configuration=sha(HERE/'FROZEN_EVALUATION_CONFIGURATION.json')))
   if p.exists():
    r=json.loads(p.read_text());assert r['input_digest']==binding;assert r['canonical_digest']==digest(canonical({k:v for k,v in r.items() if k not in ('canonical_digest',)}));resumed+=1
   else:
    r=harness.run(q,mode);r['assessment']=assess(q,r);r['input_digest']=binding;r['canonical_digest']=digest(canonical(r));tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,sort_keys=True,allow_nan=False));tmp.rename(p)
   completed.append(r)
   if i%25==0:print(label,split,i+1,'/',len(pairs),flush=True)
 finally:harness.close()
 result=dict(passed=True,split=split,mode_instances=len(completed),unique_questions=len(cases),resumed=resumed,canonical_digest=digest([(r['case_id'],r['mode'],r['canonical_digest']) for r in completed]),dataset_sha256=sha(HERE/'EVALUATION_DATASET.jsonl'),seconds=time.perf_counter()-start)
 (WORK/(label+'_SUMMARY.json')).write_text(json.dumps(result,sort_keys=True,indent=2));print('RUN COMPLETE',result,flush=True);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['development','final'],required=True);p.add_argument('--run',required=True);p.add_argument('--limit',type=int);a=p.parse_args();run(a.split,a.run,a.limit)
