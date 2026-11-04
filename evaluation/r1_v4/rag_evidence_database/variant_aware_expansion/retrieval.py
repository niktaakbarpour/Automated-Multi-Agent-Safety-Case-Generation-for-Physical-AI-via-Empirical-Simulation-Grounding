"""Variant constraints are checked before lexical or semantic ranking."""
from dataclasses import dataclass,asdict,replace
from pathlib import Path
from evaluation.r1_v4.provenance import strict_loads,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.search import Query,search
from .registry import validate_mapping
TYPES={'execution_metadata','task_instruction','requirement_definition','calibration_provenance','evidence_limitations','object_identity','support_surface_identity','object_pose','contact','native_geometry','robot_state','timestamp','camera_reference','ai_reference_interpretation'}
FIELDS={'body_xpos':'object_pose','body_xquat':'object_pose','contacts':'contact','geom_xpos':'native_geometry','geom_xmat':'native_geometry','qpos':'robot_state','qvel':'robot_state','ctrl':'robot_state','time':'timestamp','agentview_image':'camera_reference','robot0_eye_in_hand_image':'camera_reference'}

@dataclass(frozen=True)
class VariantQuery(Query):
 variant_id:str|None=None
 field_name:str|None=None
 comparative:bool=False
 time_interval:tuple|None=None

def empty(status,reason,q):return {'schema_version':'1.0.0','status':status,'reason':reason,'query_id':'variant-query:'+digest(asdict(q)),'groups':[],'matching_count':0,'safety_claim_verified':False,'sufficient_for_physical_checking':False,'empirical_admission_enabled':False}

def guard(store,b,cache):
 v=store.db.execute('SELECT body FROM rag_env_variants WHERE id=?',(b['variant_id'],)).fetchone()
 if not v:raise ValueError('unregistered variant')
 identity=strict_loads(v[0]);expected='xmlenv:'+digest({'identity_version':'1.0.0','xml_sha256':identity['xml_sha256'],'asset_content_digest':identity['asset_content_digest']})
 if expected!=b['variant_id'] or digest(identity['assets'])!=b['asset_content_digest']:raise ValueError('variant identity content mismatch')
 pairs=[(b[k+'_path'],b[k+'_sha256']) for k in ('xml','asset_manifest','mapping')]+[(a['path'],a['sha256']) for a in identity['assets']]
 if b.get('profile_path'):pairs.append((b['profile_path'],b['profile_sha256']))
 for path,expected_sha in pairs:
  if path not in cache:cache[path]=sha(path)
  if cache[path]!=expected_sha:raise ValueError('invalid scoped source:'+path)
 validate_mapping(b)

def retrieve(store,query,*,semantic_index=None,semantic_text=None):
 q=query
 try:Query(**{k:getattr(q,k) for k in Query.__dataclass_fields__}).validate()
 except (ValueError,TypeError) as error:return empty('invalid_query_scope',str(error),q)
 if q.field_name is not None and not isinstance(q.field_name,str):return empty('invalid_query_scope','field_name must be a string',q)
 if type(q.comparative)!=bool or q.variant_id is not None and (not isinstance(q.variant_id,str) or not q.variant_id):return empty('invalid_query_scope','variant/comparative type',q)
 if q.time_interval is not None:return empty('unsupported_temporal_domain','Only explicit saved-frame intervals are supported; no inferred camera exposure clock.',q)
 if not q.execution_id and not q.comparative:return empty('invalid_query_scope','Explicit execution required unless comparative=True',q)
 if q.execution_id:
  row=store.db.execute('SELECT status,reason FROM rag_scope_status WHERE execution=?',(q.execution_id,)).fetchone()
  if row is None:return empty('unknown_execution','Execution is not in authorized inventory',q)
  status,reason=row
  if status.startswith('excluded_'):return empty(status,'Excluded scope; no source evidence inspected',q)
  if status!='indexed':return empty({'unindexed_profile_pending':'unindexed_execution','validated_unindexed':'unindexed_execution'}.get(status,status),reason,q)
  bindings=[store.binding(q.execution_id)]
 else:
  where=["s.status='indexed'"];args=[]
  if q.task_id:where.append('b.task_id=?');args.append(q.task_id)
  if q.variant_id:where.append('b.variant_id=?');args.append(q.variant_id)
  if not args:return empty('invalid_query_scope','Comparative queries need a task or variant constraint',q)
  bindings=[strict_loads(r[0]) for r in store.db.execute('SELECT b.body FROM rag_execution_env b JOIN rag_scope_status s ON s.execution=b.execution WHERE '+' AND '.join(where)+' ORDER BY b.execution LIMIT 101',args)]
  if len(bindings)>100:return empty('unsupported_mode_scope','Comparison exceeds 100 explicit execution groups',q)
 if q.variant_id and not store.db.execute('SELECT 1 FROM rag_env_variants WHERE id=?',(q.variant_id,)).fetchone():return empty('unresolved_variant','Variant has no verified content/dependency registration',q)
 if any(b is None for b in bindings):return empty('unresolved_variant','Indexed execution has no verified environment binding',q)
 for b in bindings:
  if q.task_id is not None and b['task_id']!=q.task_id:return empty('invalid_query_scope','wrong_task',q)
  if q.variant_id is not None and b['variant_id']!=q.variant_id:return empty('invalid_query_scope','wrong_variant',q)
 if not bindings:return empty('no_matching_indexed_record','No indexed execution matches the requested environment/task',q)
 if set(q.evidence_types)-TYPES:return empty('unsupported_field','Requested evidence family is not indexed by this contract',q)
 if q.field_name in ('camera_exposure_timestamp','camera_capture_time'):return empty('unavailable_timestamp','Camera exposure timestamps were not saved',q)
 if q.field_name=='logical_main_table_pose':return empty('unsupported_mapping','Logical fixture alias is not validated by this extraction contract',q)
 if q.field_name in ('root_height_fall','geometry_bounds','raw_eef_world_pose'):return empty('unsupported_spatial_field','No calibrated/inferred spatial extraction contract',q)
 if q.field_name is not None:
  if q.field_name not in FIELDS:return empty('unsupported_field','No source-field extraction contract',q)
  family=FIELDS[q.field_name]
  if q.evidence_types and family not in q.evidence_types:return empty('invalid_query_scope','Field and requested family disagree',q)
  q=replace(q,evidence_types=(family,))
 groups=[];cache={}
 for b in bindings:
  try:guard(store,b,cache)
  except (ValueError,OSError,KeyError) as error:return empty('invalid_source_or_mapping',str(error),q)
  base=Query(**{k:getattr(q,k) for k in Query.__dataclass_fields__});base=replace(base,execution_id=b['execution_id'])
  try:r=semantic_index.retrieve(base,semantic_text) if semantic_index is not None else search(store,base)
  except ValueError as error:return empty('unsupported_mode_scope',str(error),q)
  if any(item['record']['execution_id']!=b['execution_id'] or item['record']['task_id']!=b['task_id'] for item in r['results']):raise ValueError('retrieval isolation failure')
  groups.append({'execution_id':b['execution_id'],'task_id':b['task_id'],'variant_id':b['variant_id'],'mapping_sha256':b['mapping_sha256'],'result':r})
 count=sum(g['result']['matching_count'] for g in groups);returned=sum(len(g['result']['results']) for g in groups);status='ok' if count else 'no_matching_indexed_record'
 if not count and any(g['result'].get('unindexed_evidence_ids') for g in groups):status='unindexed_semantic_family'
 if not count and any(g['result']['rejected'] for g in groups):status='invalid_or_insufficient_evidence'
 return {'schema_version':'1.0.0','query_id':'variant-query:'+digest({'query':asdict(q),'semantic_text':semantic_text}),'status':status,'groups':groups,'matching_count':count,'returned_count':returned,'comparative':q.comparative,'coverage_composed_across_executions':False,'safety_claim_verified':False,'sufficient_for_physical_checking':False,'empirical_admission_enabled':False}
