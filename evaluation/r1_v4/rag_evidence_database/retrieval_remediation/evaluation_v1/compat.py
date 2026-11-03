"""Strict descriptor-bound compatibility route for legacy record-reference queries."""
import json,re
from dataclasses import asdict
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.rag_evidence_database.search import Query
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.retrieval import FIELDS,TYPES
from .store import SourceError

def retrieve(store,q):
 def empty(status,reason):return dict(status=status,reason=reason,groups=[],matching_count=0,safety_claim_verified=False,empirical_admission_enabled=False)
 if q.comparative:return empty('unsupported_mode_scope','Strict compatibility requires one explicit execution; use explicit grouped calls')
 if q.time_interval is not None:return empty('unsupported_temporal_domain','Only saved-index intervals in this legacy contract')
 try:Query(**{k:getattr(q,k) for k in Query.__dataclass_fields__}).validate()
 except (ValueError,TypeError) as e:return empty('invalid_query_scope',str(e))
 status=store.db.execute('select status from rag_scope_status where execution=?',(q.execution_id,)).fetchone()
 if not status or status[0]!='indexed':return empty('invalid_query_scope','Not an indexed execution; no payload access')
 b=store.binding(q.execution_id)
 if q.task_id is not None and q.task_id!=b['task_id'] or q.variant_id is not None and q.variant_id!=b['variant_id']:return empty('invalid_query_scope','Wrong task/variant')
 types=q.evidence_types
 if q.field_name is not None:
  if q.field_name not in FIELDS:return empty('unsupported_field','No validated legacy source-field contract')
  if types and FIELDS[q.field_name] not in types:return empty('invalid_query_scope','Field/family mismatch')
  types=(FIELDS[q.field_name],)
 if set(types)-TYPES:return empty('unsupported_field','Unknown evidence family')
 store.set_scope(q.execution_id,b['variant_id']);where=['e.requirement_id=?','e.requirement_version=?','e.execution_id=?',"json_extract(e.body,'$.provenance.input_binding_digest')=j.input_digest"];args=[q.requirement_id,q.requirement_version,q.execution_id];join='';score='0.0'
 if types:where.append('u.type in ('+','.join('?' for _ in types)+')');args+=list(types)
 if q.stratum:where.append('u.stratum=?');args.append(q.stratum)
 if q.object_id:where.append('e.object_id=?');args.append(q.object_id)
 if q.interval:where+=['u.hi>=?','u.lo<=?'];args+=list(q.interval)
 if q.text:
  tokens=re.findall(r'\w+',q.text)
  if not tokens:return empty('invalid_query_scope','No lexical tokens')
  join=' join rag_fts on rag_fts.id=e.id';score='bm25(rag_fts)';where.append('rag_fts match ?');args+=[' AND '.join('"'+t+'"' for t in tokens)]
 rows=store.db.execute('select e.body,u.text,'+score+' from evidence e join rag_units u on u.id=e.id join rag_jobs j on j.execution=e.execution_id'+join+' where '+' and '.join(where)+' order by 3,e.id limit 10001',args).fetchall()
 if len(rows)>10000:return empty('unsupported_mode_scope','Narrow scope required')
 matched=[];cache=set()
 def verify_record(r,stack=()):
  if r['id'] in stack:raise SourceError('dependency_cycle')
  if r['id'] in cache:return
  if r['task_id']!=b['task_id']:raise SourceError('wrong_task_record')
  if r['execution_id']!=q.execution_id:raise SourceError('cross_execution_dependency')
  store.verifier.verify(r['source_path'],r['source_sha256'],'strict')
  if r['validation_status'] in ('invalid','missing','unsupported') or r['conflicts']:raise SourceError('invalid_or_conflicting_record')
  for dep in r['dependencies']:
   row=store.db.execute('select body from evidence where id=?',(dep,)).fetchone()
   if not row:raise SourceError('missing_dependency')
   verify_record(json.loads(row[0]),stack+(r['id'],))
  cache.add(r['id'])
 try:
  store.check_binding(b,'strict')
  for body,text,rank in rows:
   r=json.loads(body)
   if q.validation_status and r['validation_status']!=q.validation_status:continue
   if q.uncertainty_contains and not any(q.uncertainty_contains.lower() in v.lower() for v in r['uncertainty']):continue
   if any(r['capability'].get(k)!=v for k,v in q.capabilities.items()):continue
   verify_record(r);matched.append(dict(id=r['id'],record=r,text=text,rank=rank,integrity_policy='descriptor-bound strict'))
 except (SourceError,OSError,ValueError,KeyError,AssertionError) as e:return empty('invalid_source_or_mapping',str(e))
 return dict(status='ok' if matched else 'no_matching_indexed_record',matching_count=len(matched),groups=[dict(execution_id=q.execution_id,task_id=b['task_id'],variant_id=b['variant_id'],result=dict(results=matched[:q.limit]))],safety_claim_verified=False,empirical_admission_enabled=False,assurance='verified_source_references_strict',query_id='strict-legacy:'+digest(asdict(q)))
