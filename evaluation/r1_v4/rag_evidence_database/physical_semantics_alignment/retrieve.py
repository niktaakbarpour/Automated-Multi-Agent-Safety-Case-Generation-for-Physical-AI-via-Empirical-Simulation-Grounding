"""Typed interpretations and descriptor-bound source reads behind immutable scope guards."""
from dataclasses import dataclass,asdict
import json,re,os
import h5py,numpy as np
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import CHANNELS,contract
from .source_integrity import SourceError
from .config import VERSION

@dataclass(frozen=True)
class PhysicalQuery:
 execution_id:str
 task_id:str|None=None
 variant_id:str|None=None
 channel_id:str|None=None
 object_id:str|None=None
 interval:tuple|None=None
 component:str|None=None
 units:str|None=None
 coordinate_frame:str|None=None
 required_properties:tuple=()
 allow_conditional:bool=False
 alignment:str='saved_snapshot_association'
 transformation:str='identity'
 source_sha256:str|None=None
 verification_mode:str='strict'
 text:str|None=None
 limit:int=20

def empty(q,status,reason):return dict(version=VERSION,status=status,reason=reason,query_id='physical-query:'+digest(asdict(q)),results=[],matching_count=0,safety_claim_verified=False,empirical_admission_enabled=False)

def read_samples(file,raw,semantic,indices,execution):
 samples=[]
 with h5py.File(file,'r') as f:
  if f.attrs.get('global_episode_id')!=execution['execution_id']:raise SourceError('source_execution_identity_mismatch')
  for i in indices:
   key=raw['frame_keys'][str(i)];selector='/frames/'+key+'/'+semantic['source_field']
   if selector not in f:raise SourceError('missing_source_dataset')
   d=f[selector]
   if list(d.shape)!=semantic['expected_shape']:raise SourceError('source_dataset_shape_mismatch')
   if d.dtype!=np.dtype(semantic['expected_dtype']):raise SourceError('source_dataset_dtype_mismatch')
   value=d[()]
   if not np.isfinite(value).all():raise SourceError('invalid_source_numeric_value')
   if semantic['channel_id']=='simulator.ncon' and int(value)<0:raise SourceError('invalid_source_count')
   time=execution['temporal_rows'][i]
   if time['saved_frame']!=i:raise SourceError('temporal_index_mismatch')
   samples.append(dict(saved_frame_index=i,source_selector=selector,value=np.asarray(value).tolist(),dtype=str(d.dtype),shape=list(d.shape),temporal_relation=time))
 return samples

def retrieve(store,q,*,encoder=None,semantic_text=None):
 if not isinstance(q,PhysicalQuery):raise TypeError('PhysicalQuery required')
 for key in ('execution_id','task_id','variant_id','channel_id','object_id','component','units','coordinate_frame','source_sha256','text'):
  v=getattr(q,key)
  if v is not None and (not isinstance(v,str) or not v or len(v)>1000):return empty(q,'invalid_query','Invalid '+key)
 if not q.execution_id or type(q.limit)!=int or not 1<=q.limit<=100 or type(q.allow_conditional)!=bool:return empty(q,'invalid_query','Explicit execution and typed bounded options required')
 if not isinstance(q.required_properties,(tuple,list)) or any(not isinstance(x,str) for x in q.required_properties):return empty(q,'invalid_query','Property names required')
 if q.interval is not None and (not isinstance(q.interval,(tuple,list)) or len(q.interval)!=2 or any(type(x)!=int or x<0 for x in q.interval) or q.interval[1]<q.interval[0] or q.interval[1]-q.interval[0]>=4096):return empty(q,'invalid_query','Inclusive bounded saved-frame interval required')
 if q.channel_id is None and (q.component is not None or q.units is not None or q.coordinate_frame is not None or q.required_properties):return empty(q,'invalid_query','Typed semantic filters require an explicit channel')
 if q.verification_mode not in ('strict','verified_session'):return empty(q,'unsupported_verification','No unverified inspection mode')
 if q.alignment!='saved_snapshot_association':return empty(q,'unsupported_alignment','Same-index association does not establish a physical common instant; no shifted retrieval')
 if q.transformation not in ('identity','component_projection'):return empty(q,'unsupported_transformation','No world transform, normalization or endpoint shift')
 if q.transformation=='component_projection' and q.component is None:return empty(q,'invalid_query','Component projection requires an exact identity')
 if semantic_text is not None and (encoder is None or q.text is not None or not isinstance(semantic_text,str) or not semantic_text.strip() or len(semantic_text)>1000):return empty(q,'invalid_query','Invalid semantic request')
 if not store.database_verified:return empty(q,'unverified_database','Caller must supply a trusted database SHA-256')
 stat=os.stat(store.database_path,follow_symlinks=False);current=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
 if current!=store.database_signature:return empty(q,'invalid_database_identity','Verified database changed; reopen with a trusted release hash')
 status=store.db.execute('select status from rag_scope_status where execution=?',(q.execution_id,)).fetchone()
 if not status:return empty(q,'unknown_execution','Outside authorized inventory')
 if status[0]!='indexed':return empty(q,status[0],'Excluded/pending ID; no payload access')
 b=store.binding(q.execution_id)
 if q.task_id is not None and q.task_id!=b['task_id']:return empty(q,'invalid_query_scope','wrong_task')
 if q.variant_id is not None and q.variant_id!=b['variant_id']:return empty(q,'invalid_query_scope','wrong_variant')
 if q.channel_id is not None and q.channel_id not in CHANNELS:return empty(q,'unsupported_channel','No physical interpretation contract')
 clauses=['s.execution=?'];args=[q.execution_id]
 if q.channel_id is not None:clauses.append('s.channel=?');args.append(q.channel_id)
 pairs=[(json.loads(r),json.loads(s)) for r,s in store.db.execute('select r.body,s.body from h_semantics s join rag_channel_records r on r.id=s.raw_id where '+' and '.join(clauses)+' order by s.raw_id',args)]
 execution=json.loads(store.db.execute('select body from h_execution where execution=?',(q.execution_id,)).fetchone()[0]);selected=[]
 for raw,sem in pairs:
  if q.object_id is not None and raw['object_id']!=q.object_id:continue
  props=sem['properties'];names=[c['name'] for c in sem['components']]
  if q.component is not None and q.component not in names:continue
  component=names.index(q.component) if q.component is not None else None
  if q.coordinate_frame is not None and q.coordinate_frame!=props['coordinate_frame']['value']:return empty(q,'unsupported_coordinate_frame','Exact model coordinate type required; no world frame inference')
  if q.source_sha256 is not None and q.source_sha256!=raw['source_sha256']:return empty(q,'invalid_source_scope','wrong_source_hash')
  requested=list(q.required_properties)
  unit=props['units']['value'];unit_status=props['units']['status']
  if q.units is not None and q.units!=unit:
   si=props.get('si_component_units')
   if si is None or component is None or q.units!=si['value'][component]:return empty(q,'unsupported_units','No conversion or unit substitution')
   unit=q.units;unit_status=si['status'];requested.append('si_component_units')
  for name in requested:
   if name not in props:return empty(q,'unsupported_property','No property contract: '+name)
   state=props[name]['status']
   if state!='VERIFIED' and not(q.allow_conditional and state=='CONDITIONAL'):return empty(q,'unsupported_semantic_status',name+': '+state)
  selected.append((raw,sem,component,unit,unit_status))
 if not selected:return empty(q,'no_matching_record','No exact channel/object/component matches')
 if q.text:
  tokens=re.findall(r'\w+',q.text)
  if not tokens:return empty(q,'invalid_query','No lexical tokens')
  ranks=dict(store.db.execute('select id,bm25(rag_channel_fts) from rag_channel_fts where rag_channel_fts match ?',(' OR '.join('"'+t+'"' for t in tokens),)))
  selected=[v for v in selected if v[0]['id'] in ranks];selected.sort(key=lambda v:(ranks[v[0]['id']],v[0]['id']))
 if semantic_text is not None:
  if not hasattr(encoder,'physical_descriptors'):encoder.physical_descriptors={k:encoder.encode([contract(k)['description']])[0] for k in CHANNELS}
  if not hasattr(encoder,'physical_queries'):encoder.physical_queries={}
  if semantic_text not in encoder.physical_queries:encoder.physical_queries[semantic_text]=encoder.encode([semantic_text])[0]
  v=encoder.physical_queries[semantic_text];selected.sort(key=lambda item:(-float(np.dot(v,encoder.physical_descriptors[item[0]['channel_id']])),item[0]['id']))
 results=[]
 try:
  # Cryptographic DB binding protects annotations/temporal maps. Revalidate primary lineage too.
  store.check_binding(b,q.verification_mode)
  for raw,sem,component,unit,unit_status in selected:
   if raw['id']!='channel:'+digest({k:v for k,v in raw.items() if k!='id'}) or sem['id']!='semantics:'+digest({k:v for k,v in sem.items() if k!='id'}):raise SourceError('record_content_digest_mismatch')
   if sem['raw_record_id']!=raw['id'] or raw['contract']!=contract(raw['channel_id']):raise SourceError('raw_contract_identity_mismatch')
   for value in (raw,sem,execution):
    if (value['execution_id'],value['task_id'],value['variant_id'])!=(b['execution_id'],b['task_id'],b['variant_id']):raise SourceError('record_scope_mismatch')
   if (sem['source_path'],sem['source_sha256'],sem['source_field'])!=(raw['source_path'],raw['source_sha256'],raw['source_field']):raise SourceError('source_association_mismatch')
   if not hasattr(store,'source_associations'):store.source_associations=set(store.db.execute("select distinct execution_id,json_extract(body,'$.source_path'),json_extract(body,'$.source_sha256') from evidence where kind='raw_measurement'"))
   if (q.execution_id,raw['source_path'],raw['source_sha256']) not in store.source_associations:raise SourceError('original_source_binding_mismatch')
   for proof in sem['traceability']+[dict(path=sem['model_map_path'],sha256=sem['model_map_sha256']),dict(path=sem['metadata_path'],sha256=sem['metadata_sha256'])]:
    store.verifier.verify(proof['path'],proof['sha256'],q.verification_mode)
    if proof['path'].endswith('/PRIMARY_SOURCES.json'):
     if not hasattr(store,'primary_proof_cache'):store.primary_proof_cache={}
     key=(proof['path'],proof['sha256'])
     if key not in store.primary_proof_cache:
      with store.verifier.access(proof['path'],proof['sha256'],q.verification_mode) as (source,_):store.primary_proof_cache[key]=json.load(source)['files']
     for primary in store.primary_proof_cache[key]:store.verifier.verify(primary['path'],primary['sha256'],q.verification_mode)
   indices=raw['valid_indices'] if q.interval is None else [i for i in raw['valid_indices'] if q.interval[0]<=i<=q.interval[1]]
   if not indices:continue
   with store.verifier.access(raw['source_path'],raw['source_sha256'],q.verification_mode) as (file,attestation):
    if q.interval is None:
     with h5py.File(file,'r') as f:
      if f.attrs.get('global_episode_id')!=q.execution_id:raise SourceError('source_execution_identity_mismatch')
     samples=[]
    else:samples=read_samples(file,raw,sem,indices,execution)
   for s in samples:
    s['value_units']=sem['properties']['units']['value'];s['coordinate_frame']=sem['properties']['coordinate_frame']['value'];s['source_status']='verified_source';s['origin']='direct_recording';s['value_transformation']='identity'
    if component is not None:s.update(selected_component=sem['components'][component],selected_value=s['value'][component],selected_value_units=unit,selected_unit_status=unit_status,projection='y=x[j]; direct component view')
   results.append(dict(id=raw['id'],raw_record=raw,semantic_record=sem,samples=samples,source_attestation=attestation,interpretation_units=unit,unit_status=unit_status,query_unit_applies_to='selected_value' if component is not None else 'value',spatial_observation=False,synchronized_physical_instant=False))
 except (SourceError,OSError,ValueError,KeyError,AssertionError) as e:return empty(q,'invalid_source_or_contract',str(e))
 count=len(results)
 return {**empty(q,'ok' if count else 'no_matching_record','Source-verified raw values with separately classified model semantics'),'matching_count':count,'results':results[:q.limit],'scope':dict(execution_id=q.execution_id,task_id=b['task_id'],variant_id=b['variant_id']),'query_id':'physical-query:'+digest(dict(query=asdict(q),semantic_text=semantic_text))}
