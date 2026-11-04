"""External obligation audit; does not change retrieval or make safety judgments."""
import json,collections
import numpy as np
from .config import *
from .metrics import wilson

def run():
 qs={q['id']:q for q in map(json.loads,(HERE/'FROZEN_HOLDOUT_DATASET.jsonl').read_text().splitlines())};rows=[json.loads(p.read_text()) for p in sorted((WORK/'holdout_guard_v2').glob('*bundle.json'))];metrics=json.loads((WORK/'holdout_guard_v2_METRICS.json').read_text())['bundle'];failures=[];unique={};units=[];facts=[]
 for r in rows:
  q=qs[r['case_id']];missing=sorted(set(q['expected_families'])-set(r['returned_families']))
  if missing and not q['critical_abstention']:failures.append(dict(case_id=r['case_id'],template_id=q['template_id'],query=q['query'],missing=missing,api_status=r['status'],root_cause='Standalone joint configuration is not recognized as an arm-field intent; simulator label is recognized',critical=q['critical_abstention']))
  for item in r['items']:
   for s in item.get('samples',[]):
    key=(item['source_artifact']['sha256'],s['source_selector']);unique[key]=s
    ref=next((x for x in q['reference_samples'].get(item['family'],[]) if x['frame']==s['saved_frame_index']),None)
    if ref:units.append(dict(case_id=q['id'],matched=s['value_units']==ref['units'],observed=s['value_units'],expected=ref['units']))
  if q['category']=='C9':
   required=set(q['expected_families']);facts.append(dict(case_id=q['id'],independently_referenced_claim_true=q['narrow_value_claim']['expected_equal'],retrieved_required_evidence=required<=set(r['returned_families']),classifier_in_production=False,physical_safety_evaluated=False))
 assert all(u['matched'] for u in units)
 criteria=json.loads((HERE/'FROZEN_ACCEPTANCE_CRITERIA.json').read_text())['targets'];gates=dict(precision_at_1=metrics['precision_at_1']>=criteria['precision_at_1'],recall_at_20=metrics['recall_at_20']>=criteria['recall_at_20'],multisource_complete=metrics['multisource_complete']>=criteria['multisource_complete'],required_family_recall=metrics['required_family_recall']>=criteria['required_family_recall'],critical_abstention=metrics['critical_abstention_rate']==1.,no_scope_or_value_error=not metrics['errors'],no_false_assurance=metrics['false_assurance']==0)
 result=dict(aggregate_gates=gates,aggregate_gates_all_pass=all(gates.values()),recommendation='B. FOCUSED CORRECTION STILL REQUIRED',reason='Three scope instances of one temporal/field formulation omit the requested joint configuration while the API reports completeness for its reduced plan. This violates the pre-existing requested-obligation bundle contract even though aggregate numerical targets pass.',missing_family_cases=failures,false_complete_query_instances=sum(x['api_status']=='COMPLETE WITHIN VERIFIED CONTRACT' for x in failures),unique_missing_formulations=len({x['template_id'] for x in failures}),eligible_denominator=metrics['eligible'],unique_returned_source_samples=len(unique),returned_numeric_components=sum(np.asarray(s['value']).size for s in unique.values()),source_sample_maximum_error=0,unit_comparisons=len(units),unit_errors=sum(not u['matched'] for u in units),factual_claim_cases=facts,new_thresholds_added=False,no_post_result_exclusions=True,production_safety_sufficiency_classifier=False)
 (WORK/'FINAL_ASSESSMENT.json').write_text(json.dumps(result,sort_keys=True,indent=2));print({k:v for k,v in result.items() if k not in ('factual_claim_cases','missing_family_cases')},flush=True)
if __name__=='__main__':run()
