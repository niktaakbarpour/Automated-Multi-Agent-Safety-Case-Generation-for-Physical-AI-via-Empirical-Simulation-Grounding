"""Metadata-filtered deterministic SQL/FTS retrieval; no safety labels."""
import re
from dataclasses import dataclass,field,asdict
from evaluation.r1_v4.evidence_registry_gsn.models import Record,interval,CAPABILITIES
from evaluation.r1_v4.evidence_registry_gsn.registry import source_status
from evaluation.r1_v4.evidence_registry_gsn.retrieval import subtract
from evaluation.r1_v4.provenance import strict_loads,digest

@dataclass(frozen=True)
class Query:
 execution_id:str|None=None
 object_id:str|None=None
 task_id:str|None=None
 evidence_types:tuple=()
 interval:tuple|None=None
 text:str|None=None
 requirement_id:str='R1'
 requirement_version:str='2.0.0'
 validation_status:str|None=None
 capabilities:dict=field(default_factory=dict)
 uncertainty_contains:str|None=None
 limit:int=20

 def validate(self):
  if not isinstance(self.evidence_types,(tuple,list)) or any(not isinstance(t,str) or not t for t in self.evidence_types):raise ValueError('evidence type list')
  if any(v not in CAPABILITIES for v in self.capabilities.values()):raise ValueError('capability status')
  if any(v is not None and (not isinstance(v,str) or not v) for v in (self.execution_id,self.object_id,self.task_id,self.uncertainty_contains)):raise ValueError('metadata filter')
  if type(self.limit)!=int or not 1<=self.limit<=100:raise ValueError('limit 1..100')
  if self.interval is not None:
   interval(self.interval)
   if any(type(x)!=int or x<0 for x in self.interval):raise ValueError('saved-frame interval required')
  if self.text is not None and (not isinstance(self.text,str) or not self.text.strip() or len(self.text)>1000):raise ValueError('text query')
  if len(set(self.evidence_types))!=len(self.evidence_types):raise ValueError('duplicate evidence type')
  if self.validation_status not in (None,'verified_measurement','verified_source','provisional','invalid','missing','unsupported'):raise ValueError('validity filter')
  return self

def search(store,query):
 q=query.validate();where=['e.requirement_id=?','e.requirement_version=?',"json_extract(e.body,'$.provenance.input_binding_digest')=j.input_digest"]
 args=[q.requirement_id,q.requirement_version];join='';score='0.0'
 for col,value in [('e.execution_id',q.execution_id),('e.object_id',q.object_id),('u.task',q.task_id)]:
  if value is not None:where.append(col+'=?');args.append(value)
 if q.evidence_types:
  where.append('u.type IN ('+','.join('?' for _ in q.evidence_types)+')');args.extend(q.evidence_types)
 if q.interval is not None:where+=['u.hi>=?','u.lo<=?'];args.extend(q.interval)
 if q.validation_status:where.append("json_extract(e.body,'$.validation_status')=?");args.append(q.validation_status)
 if q.uncertainty_contains:where.append("lower(json_extract(e.body,'$.uncertainty')) LIKE ?");args.append('%'+q.uncertainty_contains.lower()+'%')
 if q.text:
  tokens=re.findall(r'\w+',q.text,flags=re.UNICODE)
  if not tokens:raise ValueError('text has no searchable tokens')
  join=' JOIN rag_fts ON rag_fts.id=e.id';score='bm25(rag_fts)'
  where.append('rag_fts MATCH ?');args.append(' AND '.join('"'+t+'"' for t in tokens))
 sql='SELECT e.body,u.text,'+score+' AS score FROM evidence e JOIN rag_units u ON u.id=e.id JOIN rag_jobs j ON j.execution=e.execution_id'+join+' WHERE '+' AND '.join(where)+' ORDER BY score,e.id LIMIT 10001'
 rows=store.db.execute(sql,args).fetchall()
 if len(rows)>10000:raise ValueError('query too broad; narrow metadata filters')
 cache={};dependency_cache={};rejected=[];matched=[];conflict_map={}
 for key,body in store.db.execute("SELECT id,body FROM evidence WHERE json_array_length(body,'$.conflicts')>0"):
  record=Record.parse(strict_loads(body))
  for other in record.conflicts:
   conflict_map.setdefault(key,set()).add(other);conflict_map.setdefault(other,set()).add(key)
 def check_dep(key,stack=()):
  if key in dependency_cache:return dependency_cache[key]
  if key in stack:return ['dependency_cycle']
  row=store.db.execute('SELECT body FROM evidence WHERE id=?',(key,)).fetchone()
  if row is None:return ['missing_dependency:'+key]
  r=Record.parse(strict_loads(row[0]));issues=[]
  if source_status(r,cache)!='verified_source':issues.append('invalid_dependency_source:'+key)
  if r.validation_status in ('invalid','missing','unsupported'):issues.append('invalid_dependency:'+key)
  conflicts=conflict_map.get(key,set())
  if conflicts:issues.append('dependency_conflict:'+key)
  for d in r.dependencies:issues+=check_dep(d,stack+(key,))
  dependency_cache[key]=issues;return issues
 for body,text,rank in rows:
  r=Record.parse(strict_loads(body));issues=[]
  if source_status(r,cache)!='verified_source':issues.append('missing_or_invalid_source')
  if r.validation_status in ('invalid','missing','unsupported'):issues.append('invalid_measurement_status')
  for d in r.dependencies:issues+=check_dep(d)
  for name,status in q.capabilities.items():
   if r.capability.get(name)!=status:issues.append('capability:'+name+':'+r.capability.get(name,'missing'))
  conflicts=conflict_map.get(r.id,set())
  if conflicts:issues.append('explicit_conflict')
  if issues:rejected.append({'id':r.id,'reasons':sorted(set(issues))});continue
  matched.append({'id':r.id,'record':r.export(),'text':text,'rank':rank})
 coverage={}
 if q.interval is not None:
  for typ in sorted(q.evidence_types or {m['record']['measurement_type'] for m in matched}):
   cells=[]
   for m in matched:
    r=m['record']
    if r['measurement_type']!=typ:continue
    # Frame-domain windows only; explicitly exclude declared missing frames.
    available=set(range(max(r['interval'][0],q.interval[0]),min(r['interval'][1],q.interval[1])+1))
    for a,b in r['missing_intervals']:available.difference_update(range(a,b+1))
    for frame in sorted(available):cells.append((frame,frame))
   coverage[typ]={'missing_intervals':subtract(tuple(q.interval),cells),'saved_frame_availability_only':True,'physical_coverage_qualified':False}
 return {'schema_version':'1.0.0','query_id':'query:'+digest(asdict(q)),'query':asdict(q),'matching_count':len(matched),'results':matched[:q.limit],'rejected':rejected,'coverage':coverage,'uncertainty':sorted({u for m in matched for u in m['record']['uncertainty']}),'retrieval_rationale':'Exact SQL metadata filters before source and dependency integrity; literal FTS5 token conjunction, BM25 then stable ID. Coverage is over all valid matches before top-k truncation.','evidence_exists':bool(rows),'evidence_retrieved':bool(matched),'measurement_records_valid':sum(m['record']['validation_status']=='verified_measurement' for m in matched),'sufficient_for_physical_checking':False,'safety_claim_verified':False,'empirical_admission_enabled':False}
