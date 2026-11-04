"""Verified obligations, not physical-safety sufficiency or answer generation."""
import json,sqlite3,re,math,os
from pathlib import Path
from dataclasses import dataclass,asdict
import numpy as np,h5py
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.retrieve import ProvenanceQuery,retrieve as physical
from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder
from .config import *
from .build import producer
from .planner import interpret
from .store import BundleStore,SourceError,SourceVerifier
@dataclass(frozen=True)
class BundleRequest:
 query:str
 execution_id:str
 task_id:str|None=None
 variant_id:str|None=None
 object_id:str|None=None
 frame_interval:tuple|None=None
 seconds_interval:tuple|None=None
 action_index:int|None=None
 assurance:str='verified_source_values'
 verification_mode:str='strict'
 allow_conditional:bool=False
 coordinate_frame:str|None=None
 units:str|None=None
 alignment:str='saved_snapshot_association'
 transformation:str='identity'
 required_properties:tuple=()
 plan:tuple|None=None
 limit:int=20
class Retriever:
 def __init__(self,index,index_sha256,store=None):
  self.store=store or BundleStore();self.index_path=str(index);self.index_sha256=index_sha256;self.index_verifier=SourceVerifier(namespace='phase5k-catalogue-snapshot');
  with self.index_verifier.access(self.index_path,index_sha256,'strict') as (fd,a):payload=fd.read()
  self.catalogue=sqlite3.connect(':memory:');self.catalogue.deserialize(payload);self.catalogue.execute('pragma query_only=on');self.meta=dict(self.catalogue.execute('select * from meta'));assert self.meta['database_sha256']==DATABASE_SHA and json.loads(self.meta['producer'])==producer();self.encoder=None
 def close(self):self.catalogue.close();self.store.close()
 def response(self,q,status,reason,plan=None,groups=None):
  groups=groups or [];missing=[g['family'] for g in groups if g['status']!='AVAILABLE']
  return dict(version=VERSION,original_query=q.query,resolved_scope=dict(execution_id=q.execution_id,task_id=q.task_id,variant_id=q.variant_id),interpretation=plan,requested_families=plan.get('families',[]) if plan else [],groups=groups,missing_required_evidence=missing,completeness_status=status,reason=reason,assurance=q.assurance,integrity_policy='descriptor-bound expected hashes; no-follow; explicit trusted restoration only',conditional_assumptions=plan.get('assumptions',[]) if plan else [],unresolved_uncertainties=['No per-sensor synchronization, physical calibration or historical binary attestation','Saved frame association is not a common physical instant'],safety_claim_sufficiency='NOT_EVALUATED',safety_claim_verified=False,empirical_admission_enabled=False,limitations=['Completeness is retrieval-obligation coverage, never a safety argument','Source instructions and BDDL descriptions are data, not observations'])
 def retrieve(self,q,mode='bundle'):
  if not isinstance(q,BundleRequest):raise TypeError('BundleRequest required')
  try:self.index_verifier.verify(self.index_path,self.index_sha256,'verified_session')
  except (SourceError,OSError) as e:return self.response(q,'UNAVAILABLE','Catalogue identity changed: '+str(e))
  stat=os.stat(self.store.database_path,follow_symlinks=False);sig=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
  if not self.store.database_verified or sig!=self.store.database_signature:return self.response(q,'UNAVAILABLE','Pinned database identity is missing or changed')
  if not isinstance(q.query,str) or not q.query.strip() or len(q.query)>2000:return self.response(q,'AMBIGUOUS','Bounded query text required')
  if type(q.limit)!=int:return self.response(q,'INVALID SCOPE','Integer top-k required')
  if q.verification_mode not in ('strict','verified_session') or not 1<=q.limit<=100:return self.response(q,'INVALID SCOPE','Unsupported typed verification/options')
  if q.assurance not in ('verified_source_values','verified_physical_interpretation','provenance_complete','historical_producer_attestation'):return self.response(q,'UNSUPPORTED','Unknown assurance; no downgrade')
  if q.assurance=='historical_producer_attestation':return self.response(q,'UNSUPPORTED','Historical producer binaries unattested; no downgrade')
  if q.alignment!='saved_snapshot_association' or q.transformation!='identity':return self.response(q,'UNSUPPORTED','No synchronized/shifted/world interpretation')
  status=self.store.db.execute('select status from rag_scope_status where execution=?',(q.execution_id,)).fetchone()
  if status is None or status[0]!='indexed':return self.response(q,'INVALID SCOPE','Unknown, reserved, excluded or unindexed execution; no payload access')
  row=self.catalogue.execute('select body from catalogue where execution=?',(q.execution_id,)).fetchone()
  if row is None:return self.response(q,'UNAVAILABLE','No catalogue entry')
  c=json.loads(row[0]);b=self.store.binding(q.execution_id)
  if q.task_id is not None and q.task_id!=c['task_id'] or q.variant_id is not None and q.variant_id!=c['variant_id']:return self.response(q,'INVALID SCOPE','Task/variant context contradicts registered execution')
  if any(v!=q.execution_id for v in re.findall(r'libero_\w+_cfafd9ddc3db',q.query)):return self.response(q,'INVALID SCOPE','Query contains a different execution')
  if any(v!=c['variant_id'] for v in re.findall(r'xmlenv:[a-f0-9]{64}',q.query)):return self.response(q,'INVALID SCOPE','Query contains a different XML variant')
  if q.object_id is not None and q.object_id not in set(c['objects'])|{'robot0','*','main_table'}:return self.response(q,'AMBIGUOUS','Object identifier is not an exact registered identity')
  plan=interpret(q.query,c,asdict(q))
  if plan['status']=='INVALID SCOPE':return self.response(q,plan['status'],plan['reason'],plan)
  if q.plan is not None and 'frame_interval' in plan:
   if any(k not in FAMILIES for k in q.plan):return self.response(q,'UNSUPPORTED','Explicit plan contains unsupported evidence obligation')
   plan.update(families=list(dict.fromkeys(q.plan)),status='RESOLVED')
  if plan['status']!='RESOLVED':return self.response(q,plan['status'],plan['reason'],plan)
  if q.object_id not in (None,'robot0','*') and any(k in CHANNELS for k in plan['families']) and not any(k in plan['families'] for k in ('geometry_identity','main_table_identity')):return self.response(q,'INVALID SCOPE','Object-specific scope cannot be silently applied to robot measurements',plan)
  self.store.set_scope(q.execution_id,c['variant_id'])
  if 'raw' not in q.query.lower() and any(k in plan['unsupported'] for k in ('world_transform','sensor_synchronization','physical_calibration')):
   return self.response(q,'UNSUPPORTED','Requested physical interpretation is not verified; no raw substitute',plan,[dict(family=k,status='UNSUPPORTED',items=[],coverage={},reason='Unavailable interpretation') for k in plan['unsupported']])
  frames=plan['frame_interval'];seconds=plan['seconds_interval']
  if seconds is not None:
   if frames is not None or not isinstance(seconds,(tuple,list)) or len(seconds)!=2 or any(type(x) not in (float,int) or not math.isfinite(x) for x in seconds) or seconds[0]>seconds[1]:return self.response(q,'INVALID SCOPE','Conflicting/invalid clock intervals',plan)
   import xml.etree.ElementTree as ET
   try:
    with self.store.verifier.access(b['xml_path'],b['xml_sha256'],q.verification_mode) as (fd,a):option=ET.parse(fd).getroot().find('option');step=float(option.get('timestep')) if option is not None and option.get('timestep') is not None else None
    h=json.loads(self.store.db.execute('select body from h_execution where execution=?',(q.execution_id,)).fetchone()[0]);model,a=self.store.read_json(h['model_map_path'],h['model_map_sha256'],q.verification_mode)
    if model['variant_id']!=c['variant_id'] or model['xml_sha256']!=b['xml_sha256']:raise SourceError('compiled_model_scope_mismatch')
    if step is None:step=float(model['timestep'])
    if step!=h['timestep'] or step!=model['timestep']:raise SourceError('compiled_model_timestep_mismatch')
   except (SourceError,OSError,ValueError,KeyError) as e:return self.response(q,'UNAVAILABLE','Clock proof failure: '+str(e),plan)
   if step<=0:return self.response(q,'UNSUPPORTED','No verified native-model step for decimal-label resolution',plan)
   maximum=self.store.db.execute('select max(sim_time) from i_clock_labels where execution=?',(q.execution_id,)).fetchone()[0];n=math.ceil(maximum/step)+1;eps=np.finfo(np.float64).eps;gamma=n*eps/(1-n*eps);tolerance=(2*gamma+4*eps)*max(1.,abs(seconds[0]),abs(seconds[1]));rows=self.store.db.execute('select frame,sim_time from i_clock_labels where execution=? and sim_time>=? and sim_time<=? order by frame',(q.execution_id,seconds[0]-tolerance,seconds[1]+tolerance)).fetchall()
   if not rows:return self.response(q,'UNAVAILABLE','No recorded simulator labels; no interpolation',plan)
   if seconds[0]==seconds[1] and len(rows)>1:return self.response(q,'AMBIGUOUS','Decimal label matches multiple saved labels',plan)
   frames=[rows[0][0],rows[-1][0]];plan['clock_resolution']=dict(requested=seconds,recorded_labels=rows,absolute_roundoff_bound=tolerance,physical_synchronization=False)
  if frames and (frames[1]>=c['frames'] or frames[1]-frames[0]>=4096):return self.response(q,'UNAVAILABLE','Requested saved samples do not exist within bounds',plan)
  plan['resolved_frame_interval']=frames;self.store.set_scope(q.execution_id,c['variant_id']);groups=[]
  try:
   self.store.check_binding(b,q.verification_mode)
   proof=physical(self.store,ProvenanceQuery(q.execution_id,channel_id=CHANNELS[0],verification_mode=q.verification_mode))
   if not proof['results']:raise SourceError('primary_proof_verification_failed:'+proof['reason'])
   families=list(plan['families'])
   if mode in ('field_single','hybrid_single') and families:
    if mode=='hybrid_single':families=self.hybrid_order(q.query,families)
    families=families[:1]
   for family in plan['families']:
    if family not in families:groups.append(dict(family=family,status='UNAVAILABLE',reason='Planning ablation retrieves one obligation',items=[],coverage={}));continue
    groups.append(self.family(q,plan,c,b,family,frames))
   for name in plan['unsupported']:groups.append(dict(family=name,status='UNSUPPORTED',reason='Not established by existing contract',items=[],coverage={}))
   if q.assurance=='provenance_complete':self.store.provenance(q.execution_id,q.verification_mode)
  except (SourceError,OSError,ValueError,KeyError,AssertionError) as e:return self.response(q,'UNAVAILABLE','Integrity/contract failure: '+str(e),plan,[])
  available=sum(g['status']=='AVAILABLE' for g in groups);complete=bool(groups) and available==len(groups)
  result=self.response(q,'COMPLETE WITHIN VERIFIED CONTRACT' if complete else ('PARTIAL' if available else ('UNSUPPORTED' if any(g['status']=='UNSUPPORTED' for g in groups) else 'UNAVAILABLE')),'Every requested obligation checked separately',plan,groups);result['resolved_scope']=dict(execution_id=q.execution_id,task_id=c['task_id'],variant_id=c['variant_id']);return result
 def hybrid_order(self,text,families):
  # Fixed reciprocal-rank fusion over existing schema descriptions; no learned weights.
  descriptions={k:k.replace('raw.','').replace('robot0_','').replace('_',' ') for k in families};tokens=set(re.findall(r'\w+',text.lower()));lex=sorted(families,key=lambda k:(-len(tokens&set(re.findall(r'\w+',descriptions[k]))),k))
  if self.encoder is None:self.encoder=Encoder()
  vectors=self.encoder.encode([text]+[descriptions[k] for k in families]);semantic=sorted(families,key=lambda k:(-float(np.dot(vectors[0],vectors[1+families.index(k)])),k));return sorted(families,key=lambda k:(-(1/(60+lex.index(k)+1)+1/(60+semantic.index(k)+1)),k))
 def item(self,c,family,path,h,selector,value,original_ids=None):
  return dict(id='source-ref:'+digest([path,h,selector]),id_kind='verified_source_reference_not_new_measurement_record',family=family,original_evidence_ids=original_ids or [],execution_id=c['execution_id'],task_id=c['task_id'],variant_id=c['variant_id'],source_artifact=dict(path=path,sha256=h,selector=selector),value=value,integrity_status='verified_source',origin='recorded_metadata_or_existing_derived_identity',units=None,interpretation_status='VERIFIED_RECORDED_METADATA',synchronized_physical_instant=False)
 def family(self,q,plan,c,b,family,frames):
  def group(items,ok=True,coverage=None,reason=''):
   return dict(family=family,status='AVAILABLE' if ok else ('PARTIAL' if items else 'UNAVAILABLE'),items=items,coverage=coverage or {},reason=reason)
  if family in CHANNELS:
   props=q.required_properties or (('cache_offset_seconds',) if plan['assumptions'] else ())
   r=physical(self.store,ProvenanceQuery(q.execution_id,task_id=c['task_id'],variant_id=c['variant_id'],channel_id=family,interval=tuple(frames) if frames else None,verification_mode=q.verification_mode,assurance=q.assurance if q.assurance!='provenance_complete' else 'verified_source_values',allow_conditional=q.allow_conditional,required_properties=props,units=q.units,coordinate_frame=q.coordinate_frame))
   # PhysicalQuery has no assurance field; this call uses the Phase5I typed query.
   items=[];covered=[]
   for x in r['results']:
    raw=x['raw_record'];sem=x['semantic_record'];covered += [s['saved_frame_index'] for s in x['samples']];items.append(dict(id=raw['id'],id_kind='original_channel_record',family=family,original_evidence_ids=[raw['id']],execution_id=q.execution_id,task_id=c['task_id'],variant_id=c['variant_id'],source_artifact=dict(path=raw['source_path'],sha256=raw['source_sha256'],selector=raw['source_field']),samples=x['samples'],units=sem['properties']['units'],coordinate_frame=sem['properties']['coordinate_frame'],interpretation_properties=sem['properties'],integrity_status=x['source_attestation']['status'],origin='direct_recording',derived_interpretation=sem['id'],synchronized_physical_instant=False))
   missing=[] if frames is None else sorted(set(range(frames[0],frames[1]+1))-set(covered));return group(items,bool(items) and not missing,dict(clock='saved_frame_index',requested=frames,returned=sorted(covered),missing=missing,physical_continuity=False),r['status'])
  if family in ('geometry_identity','main_table_identity'):
   m=self.store.check_binding(b,q.verification_mode);scene,a=self.store.read_json(c['scene_path'],c['scene_sha256'],q.verification_mode)
   if family=='geometry_identity':
    name=plan['object_id'];obj=c['objects'][name];assert m['body_names'][obj['body_id']]==obj['root_body'];value=dict(object_id=name,root_body=obj['root_body'],body_id=obj['body_id'],collision_geom_ids=obj['collision_geom_ids'],symbolic_identity_only=True,physical_support_inferred=False)
    ids=[r[0] for r in self.store.db.execute("select id from evidence where execution_id=? and object_id=? and json_extract(body,'$.measurement_type')='object_identity'",(q.execution_id,name))];return group([self.item(c,family,b['mapping_path'],b['mapping_sha256'],'/body_names,/geometries',value,ids)])
   alias=c['main_table']
   if alias['status']!='verified_symbolic_alias':return dict(family=family,status='UNSUPPORTED',items=[],coverage={},reason='No verified alias in this task/domain/variant')
   audit,a=self.store.read_json(self.meta['alias_audit_path'],self.meta['alias_audit_sha256'],q.verification_mode)
   actual=next(r for r in audit['rows'] if r['execution_id']==q.execution_id);assert actual==alias and actual['variant_id']==c['variant_id']
   for source in alias['sources']:self.store.verifier.verify(source['owned_path'],source['expected_sha256'],q.verification_mode)
   value=alias['exact_mapping'];geom=m['geometries'][value['geom_id']];assert geom['name']==value['geom_name'] and geom['owner_body']==value['body_name'];item=self.item(c,family,self.meta['alias_audit_path'],self.meta['alias_audit_sha256'],'/rows/execution_id='+q.execution_id,value);item['origin']='existing_derived_symbolic_identity';item['interpretation_status']='VERIFIED_SYMBOLIC_ONLY';return group([item])
  if family=='execution_metadata':
   value,a=self.store.read_json(c['metadata_path'],c['metadata_sha256'],q.verification_mode);assert value['global_episode_id']==q.execution_id;ids=[r[0] for r in self.store.db.execute("select id from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(q.execution_id,))];safe={k:value.get(k) for k in ('source_commit','versions','python','platform','checkpoint_revision','checkpoint_weight_sha256','control_frequency_hz','settling_steps')};safe['historical_running_binary_attested']=False;return group([self.item(c,family,c['metadata_path'],c['metadata_sha256'],'/',safe,ids)])
  if family=='source_provenance':
   self.store.verifier.verify(c['source_path'],c['source_sha256'],q.verification_mode);return group([self.item(c,family,c['source_path'],c['source_sha256'],'/',dict(source_sha256=c['source_sha256'],historical_binary_attestation='UNATTESTED',provenance_scope='current_source_identity_only',database_sha256=DATABASE_SHA))])
  if family in ('contact_references','camera_references'):
   typ='contact' if family=='contact_references' else 'camera_reference';ids=[]
   for rid,body in self.store.db.execute("select id,body from evidence where execution_id=? and json_extract(body,'$.measurement_type')=?",(q.execution_id,typ)):
    r=json.loads(body)
    if r['interval'][0]<=frames[1] and r['interval'][1]>=frames[0] and (plan['object_id'] is None or r['object_id']==plan['object_id']):ids.append(rid)
   items=[]
   with self.store.verifier.access(c['source_path'],c['source_sha256'],q.verification_mode) as (fd,a):
    with h5py.File(fd,'r') as f:
     for i in range(frames[0],frames[1]+1):
      selectors=[f'/frames/{i:06d}/simulator/contacts'] if typ=='contact' else [f'/frames/{i:06d}/raw_observation/'+k+'/value' for k in ('agentview_image','robot0_eye_in_hand_image')]
      for selector in selectors:
       if selector not in f:continue
       d=f[selector];value=dict(saved_frame_index=i,materialized=False,reference_kind=typ,physical_contact_or_support_inferred=False,camera_exposure_time=None)
       if isinstance(d,h5py.Dataset):value.update(shape=list(d.shape),dtype=str(d.dtype))
       items.append(self.item(c,family,c['source_path'],c['source_sha256'],selector,value,ids))
   return group(items,len(items)==(frames[1]-frames[0]+1)*(2 if typ=='camera_reference' else 1) and bool(ids),dict(saved_frame_indices=list(range(frames[0],frames[1]+1)),reference_only=True))
  if family in ('recorded_time','action_metadata','inference_metadata'):
   items=[];missing=[]
   with self.store.verifier.access(c['source_path'],c['source_sha256'],q.verification_mode) as (fd,att):
    with h5py.File(fd,'r') as f:
     if f.attrs['global_episode_id']!=q.execution_id:raise SourceError('metadata_execution_mismatch')
     def attrs(g):return {k:(v.item() if hasattr(v,'item') else v.decode() if isinstance(v,bytes) else v) for k,v in g.attrs.items() if isinstance(v,(str,bytes,int,float,bool,np.integer,np.floating,np.bool_))}
     if family=='recorded_time':
      for i in range(frames[0],frames[1]+1):
       key=f'{i:06d}';g=f['frames'][key];a=attrs(g);value=dict(saved_frame_index=i,simulator_endpoint_seconds=float(g['simulator/time/value'][()]),recorder_host_wall_ns=int(a['wall_time_ns']),recorder_host_monotonic_ns=int(a['monotonic_ns']),recorder_utc=a['utc'],clock_domains='simulator label and host recorder calls; no sensor timestamps',synchronized_physical_instant=False);items.append(self.item(c,family,c['source_path'],c['source_sha256'],'/frames/'+key,value))
      return group(items,True,dict(saved_frame_indices=list(range(frames[0],frames[1]+1)),clock='recorded_labels_only',sensor_synchronization=False))
     actions=[plan['action_index']] if plan['action_index'] is not None else sorted({i-11 for i in range(frames[0],frames[1]+1) if i>=11});seen=set()
     for action in actions:
      key=f'{action:06d}'
      if key not in f['policy_steps']:missing.append(action);continue
      policy=f['policy_steps'][key];a=attrs(policy)
      if family=='action_metadata':
       value=dict(policy_step=action,policy_attributes=a,temporal_relation='Policy scheduling record, associated saved snapshots only',same_physical_instant=False)
       if key in f['transitions']:
        transition=f['transitions'][key];value['transition_labels']={k:np.asarray(transition[k]['value'][()]).tolist() for k in ('wall_time_ns','monotonic_ns','simulator_time') if k in transition}
        if 'executed_action' in transition:
         d=transition['executed_action']['value'];value['executed_action_reference']=dict(selector='/transitions/'+key+'/executed_action/value',shape=list(d.shape),dtype=str(d.dtype),materialized=False,interpretation='reference to existing recording only; no new searchable measurement channel')
       items.append(self.item(c,family,c['source_path'],c['source_sha256'],'/policy_steps/'+key,value))
      else:
       chunk=int(a['chunk_id']);ck=f'{chunk:06d}'
       if ck in seen:continue
       seen.add(ck)
       if ck not in f['inference_calls']:missing.append(chunk);continue
       call=f['inference_calls'][ck];value=dict(chunk_id=chunk,recorded_attributes=attrs(call),policy_input_relation='Recorded call step and preserved recorder ordering; no sensor simultaneity',policy_input_saved_frame=10+int(call.attrs['step']));items.append(self.item(c,family,c['source_path'],c['source_sha256'],'/inference_calls/'+ck,value))
     return group(items,bool(items) and not missing,dict(action_indices=actions,missing=missing,clock='recorded policy/call labels; no synchronized physical time'),'No invented metadata for settling/missing policy actions')
  return dict(family=family,status='UNSUPPORTED',items=[],coverage={},reason='No verified contract')
