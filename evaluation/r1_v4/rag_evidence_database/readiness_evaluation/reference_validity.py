"""Post-run annotation audit; preserve frozen data/scores and expose invalid judgments."""
import json,collections
from .config import *
def run():
 cases={q['id']:q for q in map(json.loads,(HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines())};invalid={}
 for k,q in cases.items():
  raw=[f for f in q['required_facets'] if f.startswith('raw.') or f=='simulator.ncon']
  if q['endpoint']=='legacy' and not q['channels'] and raw:invalid[k]=dict(reason='Superseded raw-channel facet left in a metadata-only request during pre-final reference revision',extra_facets=raw,affected_measure='Evidence completeness/sufficiency only; relevance IDs, facts, scope and assurance results remain valid',question_unchanged=True)
 assert set(invalid)=={'C7-06','C7-20'}
 statuses={}
 for split,folder in [('development','dev_v3'),('final','final_v1')]:
  statuses[split]={}
  for mode in MODES:
   allrows=[json.loads(p.read_text()) for p in (WORK/folder).glob('*-'+mode+'.json')];valid=[r for r in allrows if r['case_id'] not in invalid];statuses[split][mode]=dict(raw_denominator=len(allrows),invalid_sufficiency_judgments=len(allrows)-len(valid),valid_denominator=len(valid),validated_sufficiency_counts=dict(collections.Counter(r['assessment']['sufficiency'] for r in valid)))
 r=dict(invalid_case_annotations=invalid,exclusion_rule='All legacy metadata-only cases with superseded required raw-channel facets; applied to entire dataset, not selected by scores',post_hoc=True,frozen_dataset_modified=False,frozen_acceptance_criteria_modified=False,frozen_results_modified=False,ranking_metrics_changed=False,readiness_recommendation_changed=False,validation_counts=statuses,remediation='Add cross-field reference-schema validation before any future frozen evaluation. Do not tune to the current final cases.')
 (WORK/'REFERENCE_VALIDITY_AUDIT.json').write_text(json.dumps(r,sort_keys=True,indent=2));print('ANNOTATION VALIDITY',invalid.keys(),flush=True)
if __name__=='__main__':run()
