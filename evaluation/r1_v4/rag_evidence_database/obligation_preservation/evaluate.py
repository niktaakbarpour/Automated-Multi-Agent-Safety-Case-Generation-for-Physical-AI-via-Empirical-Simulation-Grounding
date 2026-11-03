"""Frozen external evaluation: authored references never derived from target output."""
import json,time,hashlib
from pathlib import Path
import numpy as np
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.audit_values import RawAudit
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import Retriever as Legacy,BundleRequest
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.evaluate import fault
from .config import *
from .retrieve import Retriever
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation import evaluate as old_evaluation
old_evaluation.WORK=WORK

def canonical(r):
 r=json.loads(json.dumps(r));r.pop('latency_seconds',None)
 # Scratch error paths contain no evidence identity; preserve all other status/values.
 import re
 if r.get('output',{}).get('reason'):r['output']['reason']=re.sub(r'/disk/1/data/niktakbr/trustworthy-phase5k1-working/fault-[^/ ]+','<scratch>',r['output']['reason'])
 return r

def assess(case,out,audit):
 items=[i for g in out['groups'] for i in g['items']];ranked=list(dict.fromkeys(g['family'] for g in out['groups'] if g['status']=='AVAILABLE'));gold={(o['type'],o['target']) for o in case['reference_obligations']};pred={(o['type'],str(o['target'])) for o in out.get('query_obligations',[]) if o['mandatory']};intersection=gold&pred;required=set(case['expected_families']);errors=[]
 for item in items:
  for k in ('execution_id','task_id','variant_id'):
   if item[k]!=case['request'][k]:errors.append('wrong_'+k)
  if item['integrity_status']!='verified_source':errors.append('unverified_source')
  if item['family']=='geometry_identity':
   ref=case['reference_metadata']['geometry_identity']
   if any(item['value'][k]!=ref[k] for k in ('object_id','root_body','body_id','collision_geom_ids')):errors.append('wrong_geometry')
 direct=audit.check(items,case);errors+=direct['errors'];critical=case['critical'];eligible=not critical and bool(required);rank=next((i+1 for i,f in enumerate(ranked) if f in required),None);missing=sorted(required-set(ranked));complete=out['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';fulfilled=not missing and not errors;measurement={s for s in gold if s[0]=='measurement'};temporal={s for s in gold if s[0] in ('temporal','temporal_uncertainty')};scope={s for s in gold if s[0] in ('scope','entity')};has_inventory='query_obligations' in out;false_complete=complete and (case['expected_status']!='COMPLETE WITHIN VERIFIED CONTRACT' or not fulfilled or has_inventory and not gold<=pred)
 return dict(obligation_recall=len(intersection)/len(gold) if has_inventory else None,obligation_precision=(len(intersection)/len(pred) if pred else 0.) if has_inventory else None,exact_obligation_set=gold==pred if has_inventory else None,missing_obligations=[list(x) for x in sorted(gold-pred)],extra_obligations=[list(x) for x in sorted(pred-gold)],measurement_recall=len(measurement&pred)/len(measurement) if measurement else None,temporal_preserved=temporal<=pred,scope_preserved=scope<=pred,conjunctive=len(measurement)>1,conjunction_preserved=measurement<=pred,required_families=sorted(required),missing_families=missing,critical=critical,correct_abstention=critical and not items,incorrect_abstention=eligible and not items,status_correct=out['completeness_status']==case['expected_status'],false_complete=false_complete,eligible=eligible,precision_at_1=float(bool(ranked) and ranked[0] in required) if eligible else None,recall_at_20=len(required&set(ranked[:20]))/len(required) if eligible else None,MRR=1/rank if rank and eligible else (0. if eligible else None),complete_bundle=eligible and complete and fulfilled and (gold<=pred if has_inventory else True),family_recall=len(required&set(ranked))/len(required) if eligible else None,false_assurance=bool(out.get('safety_claim_verified') or out.get('empirical_admission_enabled') or complete and case['request'].get('assurance','verified_source_values') not in ('verified_source_values','verified_physical_interpretation','provenance_complete')),source_scope_errors=errors,source_sample_checks=direct['numeric'],metadata_checks=direct['metadata'])

def run(dataset,label,modes=('legacy_k','checked'),limit=None):
 dataset=Path(dataset);qs=[json.loads(l) for l in dataset.read_text().splitlines()];directory=WORK/label;directory.mkdir(exist_ok=True);files={p.name:sha(p) for p in sorted(HERE.glob('*.py')) if p.name in ('config.py','model.py','intent.py','validator.py','retrieve.py','evaluate.py')};files['vocabulary.json']=sha(HERE/'vocabulary.json');binding=dict(database=DATABASE_SHA,catalogue=CATALOGUE_SHA,implementation=files,dataset=sha(dataset));cfg=WORK/(label+'_CONFIGURATION.json')
 if cfg.exists():assert json.loads(cfg.read_text())==binding,'Changed evaluation identity'
 else:cfg.write_text(json.dumps(binding,sort_keys=True,indent=2))
 if 'FROZEN' in dataset.name:
  frozen=json.loads((HERE/'FROZEN_CONFIGURATION.json').read_text())
  for name,h in frozen['files'].items():assert sha(HERE/name)==h,name
  assert sha(dataset)==frozen['dataset_sha256']
 pairs=sorted([(q,m) for q in qs for m in modes],key=lambda p:hashlib.sha256((SEED+p[0]['id']+p[1]).encode()).hexdigest());pairs=pairs[:limit] if limit is not None else pairs;new=Retriever();old=Legacy(CATALOGUE,CATALOGUE_SHA);audit=RawAudit();rows=[];resumed=0
 try:
  for j,(q,mode) in enumerate(pairs):
   path=directory/(q['id']+'-'+mode+'.json');inp=digest([binding,q,mode])
   if path.exists():
    r=json.loads(path.read_text());assert r['input_digest']==inp;assert r['canonical_digest']==digest(canonical({k:v for k,v in r.items() if k!='canonical_digest'}));resumed+=1
   else:
    target=new if mode=='checked' else old;start=time.perf_counter();request=BundleRequest(q['query'],**q['request'])
    # Faults are bound to scratch copies; no original source byte is changed.
    with fault(target.store,dict(q,fault=q.get('fault'))):out=target.retrieve(request)
    metrics=assess(q,out,audit);r=dict(case_id=q['id'],mode=mode,query=q['query'],output=out,metrics=metrics,latency_seconds=time.perf_counter()-start,input_digest=inp);r['canonical_digest']=digest(canonical(r));tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(r,sort_keys=True,allow_nan=False));tmp.rename(path)
   rows.append(r)
   if j%40==0:print(label,j+1,'/',len(pairs),flush=True)
 finally:new.close();old.close();audit.close()
 result=dict(passed=True,instances=len(rows),questions=len(qs),resumed=resumed,canonical_digest=digest([(r['case_id'],r['mode'],r['canonical_digest']) for r in rows]),dataset_sha256=sha(dataset));(WORK/(label+'_SUMMARY.json')).write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True);return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--run',required=True);a=p.parse_args();run(a.dataset,a.run)
