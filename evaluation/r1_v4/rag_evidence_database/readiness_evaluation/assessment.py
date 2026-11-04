"""External narrow-fact assessment, never an R1 or general-purpose safety classifier."""
import numpy as np
import json
from functools import lru_cache
from .config import HERE
@lru_cache(None)
def source_links():return json.loads((HERE/"SOURCE_ASSOCIATIONS.json").read_text())["rows"]

def assess(case,result):
 out=result['output'];items=out['items'];rel=set(case['expected_source_ids']);ids=[x['id'] for x in items];ranks=[i+1 for i,x in enumerate(ids) if x in rel];eligible=bool(rel) and not case['abstention_required'];q=case['request'];scope_errors=[];temporal_errors=[];numeric_errors=[];comparisons=0;facets=set();reference={(s['channel'],s['frame']):s for s in case['reference_samples']};source_errors=[];matched_samples=set();conditional_labels=[]
 hashes={a['path']:a['sha256'] for a in case['reference_artifacts']}
 for item in items:
  if any(item[k]!=q.get(k) for k in ('execution_id','task_id','variant_id') if q.get(k) is not None):scope_errors.append(item['id'])
  if q.get('object_id') is not None and item['object_id']!=q['object_id']:scope_errors.append(item['id'])
  link=source_links().get(item['id'])
  if link is None or any(item[k]!=link[k] for k in ('source_path','source_sha256')):source_errors.append(item['id'])
  if item.get('channel'):
   ch=item['channel'];required=[s for s in case['reference_samples'] if s['channel']==ch];observed={s['saved_frame_index']:s for s in item['samples']}
   for s in item['samples']:
    frame=s['saved_frame_index'];window=q.get('interval')
    if window is not None and not window[0]<=frame<=window[1]:temporal_errors.append((item['id'],frame))
    if q.get('seconds_interval') is not None and frame not in case['temporal_reference']['saved_indices']:temporal_errors.append((item['id'],frame))
    expected=reference.get((ch,frame))
    if expected:
     comparisons+=1;value=np.asarray(s['value']);actual=np.asarray(expected['value']);ok=value.shape==actual.shape and np.array_equal(value,actual) and s['dtype']==expected['dtype'] and s['source_selector']==expected['selector']
     if not ok:numeric_errors.append(dict(id=item['id'],frame=frame,maximum_error=float(np.max(abs(value-actual))) if value.shape==actual.shape else None))
     else:matched_samples.add((ch,frame))
     if s['value_units']!=expected['units']:numeric_errors.append(dict(id=item['id'],frame=frame,error='unit_mismatch'))
   if required and all((ch,s['frame']) in matched_samples for s in required):facets.add(ch)
   props=item['properties'];conditional_labels.append(props.get('cache_offset_seconds',{}).get('status'))
   if any(s.get('temporal_relation',{}).get('simulator_endpoint_seconds') is not None for s in item['samples']):facets.add('simulator_time_label')
   if item['source_sha256']==case['reference_artifacts'][0]['sha256']:facets.add('source_hash')
  else:
   geom=case.get('geometry_reference',{});p=item.get('provenance',{})
   if geom.get('body_id')==p.get('body_id') and set(geom.get('collision_geom_ids',[]))==set(p.get('collision_geom_ids',[])):facets.add('geometry_identity')
   if item.get('measurement_type')=='execution_metadata' and item['id'] in rel:
    for name in ('producer_version_declaration','checkpoint_declaration'):
     if name in case['required_facets']:facets.add(name)
   if item.get('measurement_type')=='object_identity' and item['id'] in rel:facets.add('identity_document')
   window=q.get('interval');iv=item.get('interval')
   if window and iv and not(iv[0]<=window[1] and iv[1]>=window[0]):temporal_errors.append((item['id'],iv))
 if len(case['channels'])>=2 and all(ch in facets for ch in case['channels']) and all(x['execution_id']==case['execution_id'] for x in items):facets.add('same_execution')
 if out.get('provenance_verification',{}):
  p=out['provenance_verification']
  if p['scope']=='release-evidence-graph-v1' and p['verified_artifacts']>0 and p['current_dependency_artifacts']>0 and p['historical_runtime_attested'] is False:facets.add('provenance_report')
 # Summaries of action indices/chunks do not substitute for original action arrays,
 # recorded policy/inference entries and their own explicit field attribution.
 required=set(case['required_facets']);covered=required&facets;complete=bool(required) and covered==required and not(scope_errors or temporal_errors or numeric_errors or source_errors)
 credible=not source_errors and all(x['source_status'] in ('verified_source','verified_source','verified_measurement') for x in items)
 genuine_abstention=not items
 false_assurance=bool(out.get('safety_claim_verified') or out.get('empirical_admission_enabled'))
 if items and q.get('assurance')=='historical_producer_attestation':false_assurance=True
 if items and case['fault']:false_assurance=True
 unsupported_acceptance=false_assurance or any(x.get('synchronized_physical_instant') is True for x in items)
 conditional_ok=all(x=='CONDITIONAL' for x in conditional_labels) if case['expected_status']=='CONDITIONALLY_SUFFICIENT' and items else True
 if case['expected_status']=='AMBIGUOUS':status='AMBIGUOUS'
 elif not items:status='INVALID' if case['expected_status']=='INVALID' else 'UNAVAILABLE'
 elif not complete or not credible:status='INSUFFICIENT'
 elif case['expected_status']=='CONDITIONALLY_SUFFICIENT':status='CONDITIONALLY_SUFFICIENT' if conditional_ok else 'INSUFFICIENT'
 else:status='SUFFICIENT'
 return dict(relevance_eligible=eligible,precision_at_1=float(bool(ids) and ids[0] in rel) if eligible else None,recall_at_5=len(rel&set(ids[:5]))/len(rel) if eligible else None,recall_at_20=len(rel&set(ids[:20]))/len(rel) if eligible else None,MRR=1/min(ranks) if eligible and ranks else (0. if eligible else None),relevant_returned=len(rel&set(ids)),required_evidence_coverage=len(covered)/len(required) if required else None,complete_required_evidence=complete,fulfilled_facets=sorted(covered),missing_facets=sorted(required-facets),source_errors=source_errors,scope_errors=scope_errors,temporal_errors=temporal_errors,numeric_errors=numeric_errors,numeric_comparisons=comparisons,credible=credible,genuine_retriever_abstention=genuine_abstention,correct_abstention=case['abstention_required'] and genuine_abstention,incorrect_abstention=case['expected_status'] in ('SUFFICIENT','CONDITIONALLY_SUFFICIENT') and genuine_abstention,unsupported_claim_acceptance=unsupported_acceptance,false_assurance=false_assurance,uncertainty_label_correct=conditional_ok and not unsupported_acceptance,sufficiency=status,sufficiency_assessor='external_predefined_checklist',physical_safety_sufficiency='NOT_EVALUATED',classifier_in_production=False,factual_statement_true=case.get('factual_claim',{}).get('claim_true'),supports_positive_factual_assertion=bool(complete and case.get('factual_claim',{}).get('claim_true')) if 'factual_claim' in case else None)
