"""Post-freeze, exposed 5J historical comparison. Never used for rule selection."""
import json,collections,datetime
from .config import *
from .evaluate import Evaluator
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
def main():
 frozen=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for n,h in frozen['files'].items():assert sha(HERE/n)==h,n
 j=HERE.parent/'readiness_evaluation';qs=[json.loads(l) for l in (j/'EVALUATION_DATASET.jsonl').read_text().splitlines() if '"split": "final"' in l];taxonomy=[];adapted=[]
 convert={'source_hash':'source_provenance','simulator_time_label':'recorded_time','recorder_host_timestamp':'recorded_time','producer_version_declaration':'execution_metadata','checkpoint_declaration':'execution_metadata','same_execution':None,'identity_document':'geometry_identity','main_table_alias':'main_table_identity','action_chunk_metadata':'action_metadata'}
 for q in qs:
  for mode in ('exact','lexical','semantic'):
   p=Path('/disk/1/data/niktakbr/trustworthy-phase5j-working/final_v1')/(q['id']+'-'+mode+'.json');r=json.loads(p.read_text());a=r['assessment'];causes=[]
   if q['id']=='C7-20':causes.append('KNOWN_INVALID_COMPLETENESS_REFERENCE_UNCHANGED')
   elif q['abstention_required']:causes.append('CORRECT_RESTRICTION' if not r['output']['items'] else 'RAW_EVIDENCE_IS_NOT_UNSUPPORTED_CLAIM_ACCEPTANCE')
   else:
    if a['relevance_eligible'] and not a['precision_at_1']:causes.append('MISRANKED_RELEVANT_RECORD' if a['recall_at_20'] else 'NO_RELEVANT_CANDIDATE_OR_VOCABULARY_MISMATCH')
    if not a['complete_required_evidence']:causes.append('MISSING_OBLIGATION_OR_SUPPORTED_CONTRACT_LIMIT')
    if not causes:causes.append('SUPPORTED_SUCCESS')
   taxonomy.append(dict(case_id=q['id'],mode=mode,query=q['natural_language_query'],causes=causes,missing_facets=a['missing_facets'],precision_at_1=a['precision_at_1'],recall_at_20=a['recall_at_20'],historical_result_sha256=sha(p),post_implementation_freeze=True,hypotheses_not_causal_experiments=True))
  request={k:v for k,v in q['request'].items() if k in ('execution_id','task_id','variant_id','object_id','seconds_interval','assurance','allow_conditional','coordinate_frame','units','alignment','transformation','required_properties')}
  if q['request'].get('interval') is not None:request['frame_interval']=q['request']['interval']
  families=list(q['channels']);unmapped=[]
  for facet in q['required_facets']:
   f=convert.get(facet,facet)
   if f is None:continue
   if f in FAMILIES:
    if f not in families:families.append(f)
   else:unmapped.append(facet)
  samples={}
  for s in q['reference_samples']:samples.setdefault(s['channel'],[]).append(s)
  adapted.append(dict(id='JH-'+q['id'],category=q['category'],query=q['natural_language_query'],request=request,expected_families=families,reference_samples=samples,reference_metadata={},execution_id=q['execution_id'],task_id=q['task_id'],variant_id=q['variant_id'],suite=q['suite'],reference_frame_indices=q['temporal_reference']['saved_indices'] or [0],source_path=q['reference_artifacts'][0]['path'],source_sha256=q['reference_artifacts'][0]['sha256'],fault={None:None,'missing':'missing_source','corrupt':'corrupt_source','symlink':'symlink_source','instruction_tamper':'instruction_source'}[q['fault']],critical_abstention=q['abstention_required'],ranking_eligible=bool(families) and not q['abstention_required'],multisource_eligible=q['category']=='C4',unmapped_original_obligations=unmapped,known_invalid_completeness=q['id']=='C7-20'))
 (WORK/'HISTORICAL_FAILURE_TAXONOMY.json').write_text(json.dumps(taxonomy,sort_keys=True,indent=2));e=Evaluator();results=[]
 try:
  for q in adapted:
   r=e.run(q,'bundle');r['unmapped_original_obligations']=q['unmapped_original_obligations'];r['known_invalid_completeness']=q['known_invalid_completeness'];results.append(r)
 finally:e.close()
 (WORK/'HISTORICAL_5J_COMPARISON_RESULTS.json').write_text(json.dumps(dict(exposed_nonindependent=True,questions=len(adapted),implementation_manifest_sha256=sha(HERE/'FROZEN_IMPLEMENTATION.json'),original_record_id_metrics_not_comparable_with_family_metrics=True,results=results),sort_keys=True,indent=2));print('HISTORICAL COMPLETE',len(results),flush=True)
if __name__=='__main__':
 from pathlib import Path
 main()
