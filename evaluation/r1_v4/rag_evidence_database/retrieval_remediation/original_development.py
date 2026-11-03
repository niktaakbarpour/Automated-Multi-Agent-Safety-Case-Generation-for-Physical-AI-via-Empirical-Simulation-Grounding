"""Adapt only original 36 exposed-development questions; keep old labels unchanged."""
import json
from .config import *
from .evaluate import Evaluator

def run():
 original=[json.loads(x) for x in (WORK/'ORIGINAL_5J_DEVELOPMENT.jsonl').read_text().splitlines()];rows=[];e=Evaluator()
 convert={'source_hash':'source_provenance','simulator_time_label':'recorded_time','recorder_host_timestamp':'recorded_time','producer_version_declaration':'execution_metadata','checkpoint_declaration':'execution_metadata','same_execution':None,'identity_document':'geometry_identity'}
 try:
  for q in original:
   request={k:v for k,v in q['request'].items() if k in ('execution_id','task_id','variant_id','object_id','seconds_interval','assurance','allow_conditional','coordinate_frame','units','alignment','transformation','required_properties')}
   if q['request'].get('interval') is not None:request['frame_interval']=q['request']['interval']
   families=list(q['channels'])
   for f in q['required_facets']:
    f=convert.get(f,f)
    if f in FAMILIES and f not in families:families.append(f)
   if q['id']=='C7-06':families=['execution_metadata']
   samples={}
   for s in q['reference_samples']:samples.setdefault(s['channel'],[]).append(s)
   c=dict(id='JDEV-'+q['id'],category=q['category'],query=q['natural_language_query'],request=request,expected_families=families,reference_samples=samples,reference_metadata={},source_artifacts=q['reference_artifacts'],execution_id=q['execution_id'],task_id=q['task_id'],variant_id=q['variant_id'],suite=q['suite'],reference_frame_indices=q['temporal_reference']['saved_indices'] or [0],source_path=q['reference_artifacts'][0]['path'],source_sha256=q['reference_artifacts'][0]['sha256'],fault=None,critical_abstention=q['abstention_required'],ranking_eligible=bool(families) and not q['abstention_required'],multisource_eligible=q['category']=='C4',historical_annotation_note='C7-06 known-invalid old completeness facet excluded; original labels not changed')
   for mode in MODES:rows.append(e.run(c,mode))
 finally:e.close()
 (WORK/'ORIGINAL_DEVELOPMENT_RESULTS.json').write_text(json.dumps(rows,sort_keys=True,indent=2));print('ORIGINAL DEV',len(rows),flush=True)
if __name__=='__main__':run()
