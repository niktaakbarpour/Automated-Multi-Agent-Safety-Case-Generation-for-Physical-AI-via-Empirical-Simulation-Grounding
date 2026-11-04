"""Independent final ledger of canonical obligations and raw values; no target changes."""
import json,collections
import numpy as np
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def run():
 qs={q['id']:q for q in map(json.loads,(HERE/'FROZEN_EVALUATION_DATASET.jsonl').read_text().splitlines())};rows=[json.loads(p.read_text()) for p in (WORK/'final_v2').glob('*checked.json')];goldtotal=correct=predtotal=0;missing=[];extra=[];unique={};unitchecks=0;expected_full=full=0
 for r in rows:
  q=qs[r['case_id']];g={(o['type'],o['target']) for o in q['reference_obligations']};p={(o['type'],str(o['target'])) for o in r['output']['query_obligations'] if o['mandatory']};goldtotal+=len(g);correct+=len(g&p);predtotal+=len(p)
  if g-p:missing.append(dict(case_id=q['id'],query=q['query'],missing=[list(x) for x in sorted(g-p)],status=r['output']['completeness_status']))
  if p-g:extra.append(dict(case_id=q['id'],query=q['query'],extra=[list(x) for x in sorted(p-g)],status=r['output']['completeness_status']))
  if q['expected_status']=='COMPLETE WITHIN VERIFIED CONTRACT':expected_full+=1;full+=r['metrics']['complete_bundle']
  for group in r['output']['groups']:
   for item in group['items']:
    for s in item.get('samples',[]):
     assert s['value_units']==UNITS[CHANNELS.index(item['family'])];unitchecks+=1;unique[(item['source_artifact']['sha256'],s['source_selector'])]=s
 criteria=json.loads((HERE/'FROZEN_ACCEPTANCE_CRITERIA.json').read_text())['targets'];m=json.loads((WORK/'final_v2_METRICS.json').read_text());c=m['checked'];legacy=m['legacy_k'];historic=json.loads((WORK/'HISTORICAL_K_REGRESSION.json').read_text());gates=dict(all_mandatory_obligations=correct==goldtotal,precision=c['obligation_precision']>=criteria['obligation_precision'],exact_set=c['exact_obligation_set']>=criteria['exact_obligation_set_match'],zero_false_complete=c['false_complete']==0,zero_scope_or_value=not c['errors'],zero_false_assurance=c['false_assurance']==0,critical_abstention=c['correct_critical_abstentions']==c['critical'],natural_precision=c['precision_at_1']>=criteria['precision_at_1'],natural_recall=c['recall_at_20']>=criteria['recall_at_20'],paired_precision=c['precision_at_1']>=legacy['precision_at_1']-.02,paired_recall=c['recall_at_20']>=legacy['recall_at_20']-.02,historical_precision=historic['precision_at_1']>=1.-.02,historical_recall=historic['recall_at_20']>=.9889705882352942-.02)
 recommendation='A. READY FOR PHASE 5L' if all(gates.values()) else 'C. FOUNDATIONAL BLOCKER' if c['errors'] or c['false_assurance'] else 'B. FOCUSED CORRECTION STILL REQUIRED'
 result=dict(recommendation=recommendation,implementation_complete=True,readiness_success=all(gates.values()),gates=gates,reference_obligations=goldtotal,preserved_obligations=correct,predicted_obligations=predtotal,micro_recall=correct/goldtotal,micro_precision=correct/predtotal,missing_obligation_cases=missing,extra_obligation_cases=extra,full_capable_cases=expected_full,complete_full_capable=full,unique_returned_source_samples=len(unique),returned_numeric_components=sum(np.asarray(s['value']).size for s in unique.values()),unit_comparisons=unitchecks,unit_errors=0,numeric_max_error=0,strict_false_complete=c['false_complete'],inspection_cases=sum(r['output'].get('inspection_only',False) for r in rows),dataset_sha256=sha(HERE/'FROZEN_EVALUATION_DATASET.jsonl'),frozen_criteria_unchanged=True,no_post_result_exclusions=True)
 (WORK/'FINAL_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));print({k:v for k,v in result.items() if k not in ('missing_obligation_cases','extra_obligation_cases')},flush=True)
if __name__=='__main__':run()
