"""Execution-local channel retrieval; exact raw samples, never inferred spatial values."""
from dataclasses import dataclass,asdict
import json,re,hashlib
import h5py
from evaluation.r1_v4.provenance import digest
from .channels import CHANNELS,VERSION,contract,sample

@dataclass(frozen=True)
class ChannelQuery:
 execution_id:str
 task_id:str|None=None
 variant_id:str|None=None
 channel_id:str|None=None
 object_id:str|None=None
 interval:tuple|None=None
 text:str|None=None
 units:str|None=None
 coordinate_frame:str|None=None
 origin:str|None=None
 limit:int=20
 temporal_domain:str='saved_frame_index'

def empty(q,status,reason):return dict(version=VERSION,status=status,reason=reason,query_id='channel-query:'+digest(asdict(q)),results=[],matching_count=0,empirical_admission_enabled=False,safety_claim_verified=False,sufficient_for_physical_checking=False)

def retrieve(store,q,*,encoder=None,semantic_text=None):
 if not isinstance(q,ChannelQuery):raise TypeError('ChannelQuery required')
 for k in ('execution_id','task_id','variant_id','channel_id','object_id','text','units','coordinate_frame','origin'):
  v=getattr(q,k)
  if v is not None and (not isinstance(v,str) or not v or len(v)>1000):return empty(q,'invalid_query_scope','Invalid '+k)
 if not q.execution_id or type(q.limit)!=int or not 1<=q.limit<=100:return empty(q,'invalid_query_scope','Execution and bounded limit required')
 if q.temporal_domain!='saved_frame_index':return empty(q,'unsupported_temporal_domain','Only explicit saved-frame indices supported')
 if q.interval is not None and (not isinstance(q.interval,(tuple,list)) or len(q.interval)!=2 or any(type(x)!=int or x<0 for x in q.interval) or q.interval[1]<q.interval[0] or q.interval[1]-q.interval[0]>=4096):return empty(q,'invalid_query_scope','Inclusive bounded frame window required')
 if semantic_text is not None and (encoder is None or q.text is not None or not isinstance(semantic_text,str) or not semantic_text.strip() or len(semantic_text)>1000):return empty(q,'invalid_query_scope','Invalid semantic request')
 status=store.db.execute('select status from rag_scope_status where execution=?',(q.execution_id,)).fetchone()
 if not status:return empty(q,'unknown_execution','Not in authorized inventory')
 if status[0]!='indexed':return empty(q,status[0],'Scope excluded or unindexed; no source payload read')
 b=store.binding(q.execution_id)
 if q.task_id is not None and q.task_id!=b['task_id']:return empty(q,'invalid_query_scope','wrong_task')
 if q.variant_id is not None and q.variant_id!=b['variant_id']:return empty(q,'invalid_query_scope','wrong_variant')
 if q.channel_id is not None and q.channel_id not in CHANNELS:return empty(q,'unsupported_channel','No frozen evidence contract')
 if q.origin is not None and q.origin!='direct_recording':return empty(q,'unsupported_origin','No derived channel implemented')
 if q.units not in (None,'count'):return empty(q,'unsupported_units','No verified unit conversion or physical array units')
 if q.coordinate_frame not in (None,'not_applicable_count','uninterpreted_raw_array'):return empty(q,'unsupported_coordinate_frame','No validated spatial observations in this extension')
 where=['execution=?'];args=[q.execution_id]
 for field,value in (('channel',q.channel_id),('object_id',q.object_id)):
  if value is not None:where.append(field+'=?');args.append(value)
 records=[json.loads(r[0]) for r in store.db.execute('select body from rag_channel_records where '+' and '.join(where)+' order by id',args)]
 if q.units is not None:records=[r for r in records if r['contract']['units']==q.units]
 if q.coordinate_frame is not None:records=[r for r in records if r['contract']['coordinate_frame']==q.coordinate_frame]
 if q.text:
  tokens=re.findall(r'\w+',q.text)
  if not tokens:return empty(q,'invalid_query_scope','No lexical terms')
  matches=dict(store.db.execute('select id,bm25(rag_channel_fts) from rag_channel_fts where rag_channel_fts match ?',(' OR '.join('"'+x+'"' for x in tokens),)))
  records=[r for r in records if r['id'] in matches];records.sort(key=lambda r:(matches[r['id']],r['id']))
 if semantic_text is not None:
  import numpy as np
  # Only fixed, source-field descriptors are embedded. No raw values or outcome labels.
  if not hasattr(encoder,'channel_vectors'):encoder.channel_vectors={k:encoder.encode([contract(k)['description']])[0] for k in CHANNELS}
  if not hasattr(encoder,'channel_query_vectors'):encoder.channel_query_vectors={}
  if semantic_text not in encoder.channel_query_vectors:encoder.channel_query_vectors[semantic_text]=encoder.encode([semantic_text])[0]
  vector=encoder.channel_query_vectors[semantic_text];records.sort(key=lambda r:(-float(np.dot(vector,encoder.channel_vectors[r['channel_id']])),r['id']))
 try:
  store.verify_binding(b)
  for r in records:
   content={k:v for k,v in r.items() if k!='id'}
   if r['id']!='channel:'+digest(content):raise ValueError('channel content digest mismatch')
   if (r['execution_id'],r['task_id'],r['variant_id'])!=(b['execution_id'],b['task_id'],b['variant_id']):raise ValueError('channel scope mismatch')
   if r['channel_id'] not in CHANNELS or r['contract']!=contract(r['channel_id']) or r['contract_sha256']!=digest(r['contract']):raise ValueError('channel contract mismatch')
   if r['object_id']!=r['contract']['object_id'] or r['derived'] or r['origin']!='direct_recording' or r['spatial_observation']:raise ValueError('channel semantics mismatch')
   if r['xml_sha256']!=b['xml_sha256'] or r['mapping_sha256']!=b['mapping_sha256']:raise ValueError('channel variant lineage mismatch')
   generation=store.db.execute('pragma data_version').fetchone()[0]
   if getattr(store,'channel_association_generation',None)!=generation:
    store.channel_source_associations=set(store.db.execute("select distinct execution_id,json_extract(body,'$.source_path'),json_extract(body,'$.source_sha256') from evidence where kind='raw_measurement'"));store.channel_association_generation=generation
   if (b['execution_id'],r['source_path'],r['source_sha256']) not in store.channel_source_associations:raise ValueError('channel source association mismatch')
   store.verify_file(r['source_path'],r['source_sha256'])
 except (ValueError,OSError,KeyError) as e:return empty(q,'invalid_source_or_mapping',str(e))
 results=[]
 for r in records:
  indices=r['valid_indices'] if q.interval is None else [x for x in r['valid_indices'] if q.interval[0]<=x<=q.interval[1]]
  if not indices:continue
  samples=[]
  if q.interval is not None:
   with h5py.File(r['source_path'],'r') as f:
    for i in indices:
     key=r['frame_keys'][str(i)];path='/frames/'+key+'/'+r['contract']['field'];a,reason=sample(f.get(path),r['channel_id'])
     if reason:return empty(q,'invalid_source_or_mapping','Source sample no longer satisfies contract')
     attrs=f['frames/'+key].attrs
     samples.append(dict(saved_frame_index=i,source_selector=path,value=a.tolist(),dtype=str(a.dtype),shape=list(a.shape),control_step=int(attrs['control_step']) if 'control_step' in attrs else None,stage=str(attrs['stage']) if 'stage' in attrs else None,phase=r['contract']['phase'],units=r['contract']['units'],coordinate_frame=r['contract']['coordinate_frame']))
  results.append(dict(id=r['id'],record=r,samples=samples,returned_sample_count=len(samples),sample_values_included=q.interval is not None))
 count=len(results);results=results[:q.limit]
 return {**empty(q,'ok' if count else 'no_matching_channel_record','Exact source-field records; raw arrays have no validated physical units or frame'), 'results':results,'matching_count':count,'returned_count':len(results),'ranking':'local_semantic' if semantic_text is not None else 'fts5' if q.text else 'stable_id','scope':dict(execution_id=q.execution_id,task_id=b['task_id'],variant_id=b['variant_id']),'query_id':'channel-query:'+digest({'query':asdict(q),'semantic_text':semantic_text})}
