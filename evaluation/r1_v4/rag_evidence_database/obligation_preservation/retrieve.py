"""Two independent gates: original-query preservation, then verified fulfillment."""
import json
from dataclasses import asdict,replace
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import Retriever as Backend,BundleRequest
from .config import *
from .intent import derive
from .validator import validate
from .model import obligation

class Retriever:
 def __init__(self,index=CATALOGUE,index_sha256=CATALOGUE_SHA,store=None):
  self.backend=Backend(index,index_sha256,store=store);self.store=self.backend.store;self.catalogue=self.backend.catalogue
 def close(self):self.backend.close()
 def decorate(self,result,query,model,check,fulfillment):
  result.update(version=VERSION,original_query=query,query_obligations=model['obligations'],obligation_preservation=check,evidence_fulfillment=fulfillment,completeness_basis='Original-query preservation AND evidence fulfillment; never just backend plan',untrusted_source_spans=model['ignored_source_spans']);return result
 def retrieve(self,q,mode='bundle'):
  if not isinstance(q,BundleRequest):raise TypeError('BundleRequest required')
  request=asdict(q);row=self.catalogue.execute('select body from catalogue where execution=?',(q.execution_id,)).fetchone();c=json.loads(row[0]) if row else {};model=derive(q.query,request,c);plan=list(q.plan) if q.plan is not None else model['families'];check=validate(q.query,request,model,plan,c)
  def early(status,reason):return self.decorate(self.backend.response(q,status,reason),q.query,model,check,dict(passed=False,obligations=[],reason='No complete evidence assertion made'))
  # Cheap scope rejection before any source payload. Keep every obligation visible.
  if not row or q.task_id is not None and q.task_id!=c['task_id'] or q.variant_id is not None and q.variant_id!=c['variant_id']:return early('INVALID SCOPE','Nonindexed or contradictory execution/task/variant')
  if not check['passed']:
   for failure in check['failures']:
    e=failure.get('expectation')
    if e and not any(o['type']==e['type'] and o['target']==e['target'] for o in model['obligations']):model['obligations'].append(obligation(q.query,e['type'],e['target'],tuple(e['span']),e['families'],'UNRESOLVED',{k:request.get(k) for k in ('execution_id','task_id','variant_id','object_id')},uncertainty='Independent validator found a missing request obligation'))
   # Noncomplete raw inspection is distinct from accepting an unverified request.
   residual_only=all(f.get('kind')=='missing_original_obligation' and f.get('expectation',{}).get('type')=='unresolved' for f in check['failures'])
   uncertain_semantics=any(o['resolution_status'] in ('AMBIGUOUS','UNSUPPORTED') for o in model['obligations'])
   if residual_only and not uncertain_semantics and q.plan is None and q.assurance=='verified_source_values' and plan:
    inspected=self.backend.retrieve(replace(q,query=model['linguistic_text'],plan=tuple(plan)),mode);inspected['inspection_source_status']=inspected['completeness_status'];inspected['completeness_status']='UNVERIFIED PLAN';inspected['reason']='Verified identified source evidence only; original request preservation remains unverified';inspected['inspection_only']=True;inspected['assurance_satisfied_for_original_request']=False
    return self.decorate(inspected,q.query,model,check,dict(passed=False,obligations=[],reason='Unresolved original obligations; inspection is not fulfillment'))
   return early('UNVERIFIED PLAN','Independent original-query preservation check failed')
  uncertain=[o for o in model['obligations'] if o['resolution_status'] in ('UNRESOLVED','AMBIGUOUS')]
  if uncertain:return early('AMBIGUOUS','Mandatory original-query obligation is unresolved')
  unsupported=[o for o in model['obligations'] if o['resolution_status']=='UNSUPPORTED']
  # Exposing raw evidence never fulfills an unsupported comparison/interpretation.
  allow_partial_raw=bool(unsupported) and any(f in CHANNELS for f in plan) and q.assurance=='verified_source_values' and (all(o['type'] in ('comparison','factual_support') for o in unsupported) or 'raw' in q.query.lower())
  if unsupported and not allow_partial_raw:return early('UNSUPPORTED','Mandatory interpretation/source/comparison has no validated contract')
  if not plan:return early('AMBIGUOUS','No bounded evidence obligation identified')
  for family in plan:
   if family not in FAMILIES:return early('UNSUPPORTED','Unregistered evidence family')
  backend_query=replace(q,query=model['linguistic_text'],plan=tuple(plan))
  result=self.backend.retrieve(backend_query,mode);rows=[];groups={g['family']:g for g in result['groups']};all_items=[i for g in result['groups'] for i in g['items']]
  for o in model['obligations']:
   ok=o['resolution_status']!='UNSUPPORTED';reason='Verified bounded obligation'
   if o['required_families']:ok=all(f in groups and groups[f]['status']=='AVAILABLE' for f in o['required_families'])
   if o['type']=='scope':ok=ok and result['resolved_scope'].get(o['target'].split('=',1)[0])==o['target'].split('=',1)[1]
   if o['type']=='assurance':ok=ok and result['assurance']==o['target'] and bool(all_items) and all(i['integrity_status']=='verified_source' for i in all_items)
   if o['type']=='entity':
    named=[i['value'].get('object_id') for i in all_items if i['family']=='geometry_identity'];ok=ok and (o['target'] in named if named else q.object_id in (None,'robot0','*'))
   if o['type']=='component':
    import re
    target=o['target'];index=0 if target.startswith('first') else 1 if target.startswith('second') else 2 if target.startswith('third') else int(re.search(r'\d+',target)[0])-1;bindings=[]
    for item in all_items:
     if item['family'] not in o['required_families']:continue
     semantic=self.store.db.execute('select body from h_semantics where raw_id=?',(item['id'],)).fetchone();components=json.loads(semantic[0])['components'] if semantic else []
     if 0<=index<len(components):bindings.append(dict(record_id=item['id'],array_index=index,native_component=components[index],basis='Existing Phase5H component contract; full raw array unchanged'))
    ok=bool(bindings) and len(bindings)==len(o['required_families']);o['component_bindings']=bindings
   if o['type']=='interpretation' and o['target']=='cache_offset_seconds:conditional':
    channels=[i for i in all_items if i['family'] in CHANNELS];ok=bool(channels) and q.allow_conditional and all(i['interpretation_properties'].get('cache_offset_seconds',{}).get('status')=='CONDITIONAL' for i in channels)
   if o['type']=='temporal':
    # Endpoints/associations were resolved against pinned labels and original raw samples.
    ip=result.get('interpretation') or {};ok=ok and ip.get('resolved_frame_interval') is not None
    selector=o.get('selector',{});actual=ip.get('resolved_frame_interval');expected=None
    if selector.get('clock')=='saved_frame_index':
     expected=selector.get('interval')
     if selector.get('relative'):expected=[0,0] if selector['relative']=='initial' else [c['frames']-1]*2 if selector['relative']=='terminal' else [c['frames']//2]*2
    if selector.get('clock')=='policy_action_association':
     ai=selector['action'];expected=[ai+10,ai+11] if selector['relation']=='around' else [ai+10]*2 if selector['relation']=='before' else [ai+11]*2
    if expected is not None:ok=ok and list(actual or [])==expected
    if selector.get('clock')=='simulator_recorded_label':
     clock=ip.get('clock_resolution',{});ok=ok and bool(clock.get('recorded_labels')) and clock.get('requested')==[selector['value'],selector['value']]

   if o['type']=='measurement':ok=ok and bool(groups.get(o['target'],{}).get('coverage',{}).get('returned'))
   rows.append(dict(obligation_id=o['id'],satisfied=bool(ok),reason=reason if ok else 'Required verified scoped evidence or identity absent'))
  result['unsatisfied_obligation_ids']=[r['obligation_id'] for r in rows if not r['satisfied']]
  fulfillment=dict(passed=bool(rows) and all(r['satisfied'] for r in rows),obligations=rows)
  if result['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT' and not fulfillment['passed']:result['completeness_status']='PARTIAL';result['reason']='Independent obligation fulfillment did not pass'
  return self.decorate(result,q.query,model,check,fulfillment)
