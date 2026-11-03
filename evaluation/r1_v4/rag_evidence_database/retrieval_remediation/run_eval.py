"""Deterministic reusable runs; target code is frozen before holdout evaluation."""
import json,time,argparse,hashlib
from pathlib import Path
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
from .evaluate import Evaluator

def canonical(r):
 r=json.loads(json.dumps(r));r.pop('latency_seconds',None)
 if r.get('output',{}).get('reason'):r['output']['reason']=__import__('re').sub(__import__('re').escape(str(WORK))+r'/fault-[^/ ]+','<scratch>',r['output']['reason'])
 return r

def run(dataset,label,modes=MODES,limit=None):
 target={n:sha(HERE/n) for n in ('config.py','store.py','planner.py','bundle.py','evaluate.py','run_eval.py','audit_values.py')}
 cases=[json.loads(x) for x in Path(dataset).read_text().splitlines()];out=WORK/label;out.mkdir(exist_ok=True)
 if 'HOLDOUT' in str(dataset):
  frozen=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
  for n,h in frozen['files'].items():assert sha(HERE/n)==h,n
 pairs=sorted([(q,m) for q in cases for m in modes],key=lambda x:hashlib.sha256((SEED+x[0]['id']+x[1]).encode()).hexdigest());pairs=pairs if limit is None else pairs[:limit];(WORK/(label+'_CONFIGURATION.json')).write_text(json.dumps(dict(code=target,dataset_sha256=sha(Path(dataset)),sidecar_sha256=sha(WORK/'catalogue.sqlite')),sort_keys=True,indent=2));e=Evaluator();records=[];resumed=0
 try:
  for i,(q,mode) in enumerate(pairs):
   p=out/(q['id']+'-'+mode+'.json');binding=digest([q,mode,DATABASE_SHA,sha(WORK/'catalogue.sqlite'),target])
   if p.exists():r=json.loads(p.read_text());assert r['input_digest']==binding;resumed+=1
   else:
    r=e.run(q,mode);r['input_digest']=binding;r['canonical_digest']=digest(canonical(r));tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,sort_keys=True,allow_nan=False));tmp.rename(p)
   records.append(r)
   if i%50==0:print(label,i+1,'/',len(pairs),flush=True)
 finally:e.close()
 result=dict(passed=True,dataset_sha256=sha(Path(dataset)),mode_instances=len(records),questions=len(cases),resumed=resumed,canonical_digest=digest([(r['case_id'],r['mode'],r['canonical_digest']) for r in records]));(WORK/(label+'_SUMMARY.json')).write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--run',required=True);a=p.parse_args();run(a.dataset,a.run)
