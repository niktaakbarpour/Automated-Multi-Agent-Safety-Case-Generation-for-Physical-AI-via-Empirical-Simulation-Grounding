"""Typed GSN scaffold with explicit unresolved physical goals."""
from dataclasses import dataclass,asdict
from evaluation.r1_v4.provenance import canonical,digest
from .models import interval

TYPES={'goal','strategy','context','assumption','justification','solution','defeater','unresolved_claim'}
ORIGINS={'llm_proposal','retrieved_observation','checker_assessment','ai_reference_judgment','human_reference_judgment','normative_document','unresolved_conclusion'}

@dataclass(frozen=True)
class Node:
 id:str
 type:str
 statement:str
 scope:dict
 provenance:dict
 validation_status:str
 origin:str
 evidence_id:str|None=None
 physical_claim:bool=False

@dataclass(frozen=True)
class Edge:
 source:str
 target:str
 type:str

@dataclass(frozen=True)
class Graph:
 nodes:tuple
 edges:tuple
 schema_version:str='1.0.0'

 def validate(self,registry):
  if self.schema_version!='1.0.0':raise ValueError('graph version')
  nodes={n.id:n for n in self.nodes};records={r.id:r for r in registry.records()}
  if len(nodes)!=len(self.nodes):raise ValueError('duplicate node')
  for n in self.nodes:
   if not n.id or not n.statement or n.type not in TYPES or n.origin not in ORIGINS:raise ValueError('node identity/type/origin')
   if n.validation_status not in ('proposed','unresolved','verified_source','verified_measurement','provisional','checker_qualified'):raise ValueError('unsupported status/promotion')
   if not n.provenance or not all(n.scope.get(k) for k in ('requirement_id','requirement_version','execution_id','object_id')):raise ValueError('node scope/provenance')
   if n.type in ('goal','unresolved_claim') and n.validation_status not in ('proposed','unresolved'):raise ValueError('goal promotion disabled')
   if any(k in n.scope for k in ('interval','domain','clock')):
    if not all(k in n.scope for k in ('interval','domain','clock')):raise ValueError('incomplete temporal scope')
    interval(n.scope['interval'])
    if n.scope['domain'] not in ('frame','time') or not n.scope['clock']:raise ValueError('temporal scope')
   if n.physical_claim and (n.type not in ('goal','unresolved_claim') or n.validation_status!='unresolved'):raise ValueError('physical promotion disabled')
   if n.type=='solution':
    if n.evidence_id not in records:raise ValueError('unregistered solution')
    r=records[n.evidence_id]
    if any(n.provenance.get(k)!=getattr(r,k) for k in ('source_path','source_sha256','selector')):raise ValueError('solution source mismatch')
    if 'interval' not in n.scope:raise ValueError('solution temporal scope required')
    if (tuple(n.scope['interval'])!=tuple(r.interval) or n.scope['domain']!=r.domain or n.scope['clock']!=r.clock):raise ValueError('solution interval mismatch')
    if any(n.scope[k]!=getattr(r,k) for k in ('requirement_id','requirement_version','execution_id','object_id')):raise ValueError('solution scope mismatch')
    permitted={'raw_measurement':'retrieved_observation','derived_measurement':'retrieved_observation','ai_reference_judgment':'ai_reference_judgment','human_reference_judgment':'human_reference_judgment','checker_assessment':'checker_assessment','document':'normative_document'}
    if n.origin!=permitted[r.kind] or n.validation_status!=r.validation_status:raise ValueError('solution provenance/status mismatch')
   elif n.evidence_id is not None:raise ValueError('evidence ID only on solution')
  adjacency={k:[] for k in nodes};seen=set()
  for e in self.edges:
   if e.source not in nodes or e.target not in nodes or e.source==e.target:raise ValueError('invalid edge endpoint')
   if (e.source,e.target,e.type) in seen:raise ValueError('duplicate edge')
   seen.add((e.source,e.target,e.type));a,b=nodes[e.source],nodes[e.target]
   if e.type=='supported_by':ok=a.type in ('goal','strategy','unresolved_claim') and b.type in ('strategy','goal','solution','unresolved_claim')
   elif e.type=='in_context_of':ok=a.type in ('goal','strategy','unresolved_claim') and b.type in ('context','assumption','justification')
   elif e.type=='challenged_by':ok=a.type in ('goal','strategy','unresolved_claim') and b.type=='defeater'
   else:ok=False
   if not ok:raise ValueError('invalid edge type')
   if any(a.scope[k]!=b.scope[k] for k in ('requirement_id','requirement_version','execution_id','object_id')):raise ValueError('edge scope mismatch')
   if 'interval' in a.scope or 'interval' in b.scope:
    if not all('interval' in n.scope for n in (a,b)) or a.scope['domain']!=b.scope['domain'] or a.scope['clock']!=b.scope['clock']:raise ValueError('edge temporal scope mismatch')
    if a.scope['interval'][0]>b.scope['interval'][0] or a.scope['interval'][1]<b.scope['interval'][1]:raise ValueError('edge target outside parent scope')
   adjacency[e.source].append(e.target)
  def visit(key,path):
   if key in path:raise ValueError('argument cycle')
   for child in adjacency[key]:visit(child,path+(key,))
  for key in nodes:visit(key,())
  canonical(self.export());return self

 def export(self):
  return {'schema_version':self.schema_version,'nodes':[asdict(n) for n in sorted(self.nodes,key=lambda n:n.id)],'edges':[asdict(e) for e in sorted(self.edges,key=lambda e:(e.source,e.target,e.type))],'empirical_admission_enabled':False}

 @property
 def id(self):return 'gsn:'+digest(self.export())
