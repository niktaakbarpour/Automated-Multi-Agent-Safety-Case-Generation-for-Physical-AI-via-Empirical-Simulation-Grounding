"""Secondary raw-output assurance audit. Frozen scorer/results remain byte-identical."""
import json,collections
from .config import *

def run():
 qs={q['id']:q for q in map(json.loads,(HERE/'FROZEN_EVALUATION_DATASET.jsonl').read_text().splitlines())};rows=[];unique={};goldtotal=correct=predtotal=0;missing=[]
 for p in sorted((WORK/'final_v1').glob('*.json')):
  r=json.loads(p.read_text());q=qs[r['case_id']];o=r['output'];request=q['request'];requested=request.get('assurance','verified_source_values');complete=o['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';items=[i for g in o['groups'] for i in g['items']];actual=o['assurance'];false=bool(o.get('safety_claim_verified') or o.get('empirical_admission_enabled') or complete and (actual!=requested or requested not in ('verified_source_values','verified_physical_interpretation','provenance_complete')) or items and requested=='historical_producer_attestation')
  rows.append(dict(case_id=q['id'],mode=r['mode'],actual_assurance=actual,requested_assurance=requested,frozen_counter=r['metrics']['false_assurance'],audited_false_assurance=false,default_omitted='assurance' not in request))
  if r['mode']=='checked':
   gold={(x['type'],x['target']) for x in q['reference_obligations']};pred={(x['type'],str(x['target'])) for x in o['query_obligations'] if x['mandatory']};goldtotal+=len(gold);correct+=len(gold&pred);predtotal+=len(pred)
   if gold-pred:missing.append(dict(case_id=q['id'],missing=[list(x) for x in sorted(gold-pred)],complete=complete,returned_families=[g['family'] for g in o['groups'] if g['status']=='AVAILABLE']))
   for i in items:
    for s in i.get('samples',[]):
     assert s['value_units']==UNITS[CHANNELS.index(i['family'])];unique[(i['source_artifact']['sha256'],s['source_selector'])]=s
 result=dict(method='Read actual output assurance and apply the documented default; no altered thresholds/labels/target',frozen_scoring_defect='Scorer tests omitted request.assurance as None instead of verified_source_values; invalid false-assurance counters retained in frozen results',audited_false_assurance={mode:sum(r['audited_false_assurance'] for r in rows if r['mode']==mode) for mode in ('legacy_k','checked')},frozen_false_assurance={mode:sum(r['frozen_counter'] for r in rows if r['mode']==mode) for mode in ('legacy_k','checked')},gold_obligation_count=goldtotal,correct_obligation_count=correct,predicted_obligation_count=predtotal,micro_obligation_recall=correct/goldtotal,micro_obligation_precision=correct/predtotal,missing_obligations=missing,unique_checked_source_samples=len(unique),unit_errors=0,rows=rows,strict_false_complete_counter_not_changed=True)
 (WORK/'INDEPENDENT_ASSURANCE_AND_NODE_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));print({k:v for k,v in result.items() if k not in ('rows','missing_obligations')},flush=True)
if __name__=='__main__':run()
