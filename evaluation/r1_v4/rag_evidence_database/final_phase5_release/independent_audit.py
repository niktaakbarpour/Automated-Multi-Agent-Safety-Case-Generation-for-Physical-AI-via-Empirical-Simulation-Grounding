"""Independent source-reference set/cardinality audit supplements frozen case scoring."""
import json,collections
from .config import *
def run():
 cases={r['id']:r for r in map(json.loads,(HERE/'FINAL_EVALUATION_DATASET.jsonl').read_text().splitlines())};errors=[];groups=0;items=0
 for p in (WORK/'final').glob('*.json'):
  r=json.loads(p.read_text());c=cases[r['case_id']]
  for g in r['bundle']['groups']:
   if g['status']!='AVAILABLE':continue
   groups+=1;ref=c['source_references'][g['obligation_id']];family=g['family'];values=g['items'];items+=len(values)
   if family in CHANNELS:
    if len(values)!=1:errors.append([c['id'],'raw_record_cardinality'])
    observed=[s['saved_frame_index'] for i in values for s in i['samples']]
    if len(observed)!=len(set(observed)) or set(observed)!={s['frame'] for s in ref['samples']}:errors.append([c['id'],'raw_sample_cardinality'])
   elif family in ('camera_references','contact_references'):
    expected={(v['saved_frame_index'],v['selector']) for v in ref['metadata']};observed=[(i['value']['saved_frame_index'],i['source_artifact']['selector']) for i in values]
    if len(observed)!=len(expected) or set(observed)!=expected:errors.append([c['id'],'metadata_reference_cardinality'])
   elif family in ('action_metadata','inference_metadata','recorded_time'):
    key='policy_step' if family=='action_metadata' else 'chunk_id' if family=='inference_metadata' else 'saved_frame_index';expected={v[key] for v in ref['metadata']};observed=[i['value'][key] for i in values]
    if len(observed)!=len(expected) or set(observed)!=expected:errors.append([c['id'],'metadata_event_cardinality'])
   elif len(values)!=1:errors.append([c['id'],'identity_cardinality'])
 result=dict(passed=not errors,cases=len(cases),available_groups=groups,items=items,errors=errors,method='Complete original-source reference sets vs returned sets; not production group-status alone',no_labels_or_thresholds_changed=True);(WORK/'INDEPENDENT_SET_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));assert result['passed'],errors;print(result,flush=True)
if __name__=='__main__':run()
