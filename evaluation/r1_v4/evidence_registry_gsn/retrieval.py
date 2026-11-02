"""Deterministic scoped discovery, never a safety assessment."""
from dataclasses import dataclass,asdict,field
from .models import interval,CAPABILITIES
from evaluation.r1_v4.provenance import digest
from .registry import source_status,dependency_issues

@dataclass(frozen=True)
class Query:
 claim_id:str
 requirement_id:str
 requirement_version:str
 execution_id:str
 object_id:str
 evidence_types:tuple
 interval:tuple
 domain:str
 clock:str
 minimum_capabilities:dict=field(default_factory=dict)

 def validate(self):
  if any(not isinstance(x,str) or not x for x in (self.claim_id,self.requirement_id,self.requirement_version,self.execution_id,self.object_id,self.clock)):raise ValueError('query scope required')
  interval(self.interval)
  if self.domain not in ('frame','time') or not self.evidence_types or len(set(self.evidence_types))!=len(self.evidence_types):raise ValueError('query domain/types')
  if self.domain=='frame' and any(type(x)!=int or x<0 for x in self.interval):raise ValueError('frame query')
  if any(x not in CAPABILITIES for x in self.minimum_capabilities.values()):raise ValueError('capability query')
  return self


def subtract(domain,cells):
 """Closed frame spans, continuous-time availability spans; no certification."""
 a,b=domain;cursor=a;gaps=[]
 for x,y in sorted(cells):
  if y<a or x>b:continue
  x=max(x,a);y=min(y,b)
  if x>cursor:gaps.append([cursor,x-1] if all(type(v)==int for v in domain) else [cursor,x])
  cursor=max(cursor,y+1 if all(type(v)==int for v in domain) else y)
 if (cursor<=b if all(type(v)==int for v in domain) else cursor<b):gaps.append([cursor,b])
 if a==b and not any(x<=a<=y for x,y in cells):gaps=[[a,b]]
 return gaps


def retrieve(registry,query):
 q=query.validate();all_records={r.id:r for r in registry.records()};deps=dependency_issues(all_records);cache={};matches=[];rejected=[]
 for r in all_records.values():
  if (r.requirement_id,r.requirement_version,r.execution_id,r.object_id)!=(q.requirement_id,q.requirement_version,q.execution_id,q.object_id):continue
  if r.measurement_type not in q.evidence_types:continue
  reasons=[]
  if r.domain!=q.domain or r.clock!=q.clock:reasons.append('incompatible_clock_or_domain')
  elif r.interval[1]<q.interval[0] or r.interval[0]>q.interval[1]:continue
  reasons+=deps[r.id]
  status=source_status(r,cache)
  if status!='verified_source':reasons.append(status)
  def check_sources(key,visited):
   if key in visited or key not in all_records:return
   visited.add(key)
   for d in all_records[key].dependencies:
    if d in all_records and source_status(all_records[d],cache)!='verified_source':reasons.append('dependency_source_invalid:'+d)
    check_sources(d,visited)
  check_sources(r.id,set())
  if r.validation_status in ('missing','invalid','unsupported'):reasons.append('invalid_evidence_status:'+r.validation_status)
  for k,v in q.minimum_capabilities.items():
   # No implicit ordering or upgrade between conditional/blocked statuses.
   if r.capability.get(k)!=v:reasons.append('capability:'+k+':'+r.capability.get(k,'missing'))
  conflicts=sorted(k for k in all_records if k in r.conflicts or r.id in all_records[k].conflicts)
  if conflicts:reasons.append('conflict:'+','.join(conflicts))
  if reasons:rejected.append({'id':r.id,'reasons':sorted(set(reasons)),'record':r.export()})
  else:matches.append(r)
 coverage={};missing=[]
 for kind in sorted(q.evidence_types):
  cells=[]
  for r in matches:
   if r.measurement_type!=kind:continue
   # Subtract explicitly declared missing spans before reporting availability.
   remaining=[list(r.interval)]
   for ga,gb in r.missing_intervals:
    next_cells=[]
    for a,b in remaining:
     if gb<a or ga>b:next_cells.append([a,b]);continue
     if a<ga:next_cells.append([a,ga-1 if q.domain=='frame' else ga])
     if gb<b:next_cells.append([gb+1 if q.domain=='frame' else gb,b])
    remaining=next_cells
   cells+=remaining
  gaps=subtract(tuple(int(v) for v in q.interval) if q.domain=='frame' else tuple(float(v) for v in q.interval),cells)
  coverage[kind]={'availability_cells':sorted(cells),'missing_intervals':gaps,'qualified_physical_coverage':False}
  if gaps:missing.append({'type':kind,'intervals':gaps})
 dependency_ids=set()
 def collect(key):
  if key in dependency_ids or key not in all_records:return
  dependency_ids.add(key)
  for dep in all_records[key].dependencies:collect(dep)
 for r in matches:
  for dep in r.dependencies:collect(dep)
 return {'schema_version':'1.0.0','query_id':'query:'+digest(asdict(q)),'query':asdict(q),'dependency_records':[all_records[k].export() for k in sorted(dependency_ids)],'capability_restrictions':[{ 'id':r.id,'capabilities':r.capability} for r in matches if any(v!='VERIFIED' for v in r.capability.values())],'matching_evidence_ids':[r.id for r in matches],
  'evidence':[r.export() for r in matches],'rejected':rejected,'coverage':coverage,'missing_evidence':missing,
  'uncertainty':sorted({u for r in matches for u in r.uncertainty}),
  'limitations':sorted({u for r in matches for u in r.limitations}),
  'rationale':'Exact version/execution/object/type filter; compatible domain, overlap, source, dependencies and exact requested capabilities; stable evidence-ID order.',
  'physical_safety_conclusion':False,'safety_claim_supported':False}
