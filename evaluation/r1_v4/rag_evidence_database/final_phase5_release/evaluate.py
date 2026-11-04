"""Independent structured evaluation and deterministic replay. No reference from outputs."""
import json,time,hashlib,contextlib
from pathlib import Path
import numpy as np
from jsonschema import Draft202012Validator
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import digest
from .config import *
from .api import StructuredRetriever
from .faults import source_fault

def canonical(r):
 r=json.loads(json.dumps(r));r.pop('latency_seconds',None)
 import re
 if r.get('bundle',{}).get('reason'):r['bundle']['reason']=re.sub(r'/disk/1/data/niktakbr/trustworthy-phase5l-working/fault-[^/ ]+','<scratch>',r['bundle']['reason'])
 # Failed group reasons repeat the same isolated path; no identity/value is removed.
 for g in r.get('bundle',{}).get('groups',[]):
  if g.get('reason'):g['reason']=re.sub(r'/disk/1/data/niktakbr/trustworthy-phase5l-working/fault-[^/ ]+','<scratch>',g['reason'])
 for g in r.get('bundle',{}).get('missing_obligations',[]):
  if g.get('reason'):g['reason']=re.sub(r'/disk/1/data/niktakbr/trustworthy-phase5l-working/fault-[^/ ]+','<scratch>',g['reason'])
 return r

def assess(case,b):
 errors=[];comparisons=0;metadata=0;items=[i for g in b['groups'] for i in g['items']];source_refs=case['source_references'];q=case['request'];required={o['id'] for o in q['obligations'] if o['mandatory']};groups={g['obligation_id']:g for g in b['groups']};returned={g['obligation_id'] for g in b['groups'] if g['status']=='AVAILABLE'}
 for g in b['groups']:
  ref=source_refs.get(g['obligation_id'])
  for item in g['items']:
   for field in ('execution_id','task_id','variant_id'):
    if item[field]!=case[field]:errors.append('wrong_'+field)
   if not ref or item['family']!=ref['family'] or item['source_artifact']['sha256']!=ref['artifact_sha256']:errors.append('wrong_source_attribution');continue
   if item['integrity_status']!='verified_source':errors.append('unverified_source')
   if item['citation_id']!='evidence-citation:'+digest(item['citation_basis']):errors.append('citation_digest')
   if item['family'] in CHANNELS:
    if item['id']!=ref['original_id']:errors.append('original_record_id')
    actual={s['saved_frame_index']:s for s in item['samples']};gold={s['frame']:s for s in ref['samples']}
    if set(actual)!=set(gold):errors.append('temporal_sample_set')
    for i,s in actual.items():
     if i not in gold:continue
     expected=gold[i];comparisons+=1
     if not np.array_equal(s['value'],expected['value']) or s['dtype']!=expected['dtype'] or s['shape']!=expected['shape'] or s['source_selector']!=expected['selector'] or s['value_units']!=expected['units']:errors.append('numeric_dtype_unit_selector')
     if 'component_index' in ref:
      if s.get('selected_value')!=expected['value'][ref['component_index']] or s.get('selected_component',{}).get('name')!=ref['component_name']:errors.append('component_order')
   else:
    value=item['value'];family=item['family'];metadata+=1
    if family=='geometry_identity' and any(value[k]!=ref['geometry'][k] for k in ref['geometry']):errors.append('geometry_binding')
    if family=='main_table_identity' and value!=ref['alias_mapping']:errors.append('symbolic_alias')
    if family=='execution_metadata' and any(value[k]!=v for k,v in ref['execution_metadata'].items()):errors.append('execution_declaration')
    if family=='source_provenance' and value['source_sha256']!=case['source_sha256']:errors.append('source_identity')
    if ref['metadata']:
     if family in ('camera_references','contact_references'):
      candidates=[v for v in ref['metadata'] if v['selector']==item['source_artifact']['selector']];keys=('saved_frame_index',)
     elif family=='action_metadata':candidates=[v for v in ref['metadata'] if v['policy_step']==value['policy_step']];keys=tuple(candidates[0]) if candidates else ()
     elif family=='inference_metadata':candidates=[v for v in ref['metadata'] if v['chunk_id']==value['chunk_id']];keys=tuple(candidates[0]) if candidates else ()
     else:candidates=[v for v in ref['metadata'] if v['saved_frame_index']==value['saved_frame_index']];keys=tuple(candidates[0]) if candidates else ()
     if not candidates or any(value[k]!=candidates[0][k] for k in keys):errors.append('recorded_metadata_value')
 complete=b['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';expected_complete=case['expected_status']=='COMPLETE WITHIN VERIFIED CONTRACT';critical=case['expected_status'] in ('INVALID SCOPE','UNSUPPORTED','UNAVAILABLE');false_complete=complete and (not expected_complete or bool(required-returned) or bool(errors));false_assurance=bool(b.get('safety_claim_verified') or b.get('empirical_admission_enabled') or complete and not b['assurance_status']['satisfied'] or items and q['assurance']=='historical_producer_attestation')
 return dict(status_correct=b['completeness_status']==case['expected_status'],expected_complete=expected_complete,actual_complete=complete,false_complete=false_complete,false_assurance=false_assurance,critical=critical,critical_rejected=critical and not items,errors=errors,source_sample_comparisons=comparisons,metadata_comparisons=metadata,mandatory_obligations=len(required),mandatory_available=len(required&returned),missing_mandatory=sorted(required-returned),missing_reporting_correct=all(x in {m['obligation_id'] for m in b['missing_obligations']} for x in required-returned),returned_citations=[i['citation_id'] for i in items])

def run(label='final',limit=None,verification_mode='verified_session'):
 cfg=json.loads((HERE/'FROZEN_RELEASE_CONFIGURATION.json').read_text())
 for name,h in cfg['files'].items():assert sha(HERE/name)==h,name
 assert sha(HERE/'FINAL_EVALUATION_DATASET.jsonl')==cfg['dataset_sha256']
 cases=[json.loads(l) for l in (HERE/'FINAL_EVALUATION_DATASET.jsonl').read_text().splitlines()];cases=sorted(cases,key=lambda r:hashlib.sha256(('phase5l-20261103'+r['id']).encode()).hexdigest());cases=cases[:limit] if limit is not None else cases;root=WORK/label;root.mkdir(exist_ok=True);engine=StructuredRetriever(verification_mode=verification_mode);validator=Draft202012Validator(json.loads((HERE/'EVIDENCE_BUNDLE_SCHEMA.json').read_text()));rows=[];resumed=0
 try:
  for i,case in enumerate(cases):
   p=root/(case['id']+'.json');binding=digest([case,cfg,verification_mode])
   if p.exists():
    r=json.loads(p.read_text());assert r['input_digest']==binding;assert r['canonical_digest']==digest(canonical({k:v for k,v in r.items() if k!='canonical_digest'}));resumed+=1
   else:
    start=time.perf_counter();context=source_fault(engine,case['source_path'],case['source_sha256'],case['fault']) if case['fault'] else contextlib.nullcontext()
    with context:b=engine.retrieve(case['request'])
    validator.validate(b);metrics=assess(case,b);r=dict(case_id=case['id'],kind=case['kind'],request=case['request'],bundle=b,metrics=metrics,input_digest=binding,latency_seconds=time.perf_counter()-start);r['canonical_digest']=digest(canonical(r));tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,sort_keys=True,allow_nan=False));tmp.rename(p)
   rows.append(r)
   if i%32==0:print(label,i+1,'/',len(cases),flush=True)
 finally:engine.close()
 summary=dict(executed=len(rows),resumed=resumed,canonical_digest=digest([(r['case_id'],r['canonical_digest']) for r in rows]),dataset_sha256=cfg['dataset_sha256'],verification_mode=verification_mode);(WORK/(label+'_SUMMARY.json')).write_text(json.dumps(summary,sort_keys=True,indent=2));print(summary,flush=True);return summary
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--run',default='final');p.add_argument('--limit',type=int);p.add_argument('--mode',choices=['strict','verified_session'],default='verified_session');a=p.parse_args();run(a.run,a.limit,a.mode)
