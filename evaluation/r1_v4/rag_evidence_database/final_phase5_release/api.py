"""Supported structured route: no NLP parser, ranking, or inferred obligations."""
import json,math,os
from jsonschema import Draft202012Validator
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.bundle import Retriever as Internals,BundleRequest
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.retrieve import ProvenanceQuery,retrieve as read_channel
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceError
from .config import *
from .completeness import validate as independently_validate
class QueryError(Exception):
 def __init__(self,status,reason):self.status=status;self.reason=reason
class StructuredRetriever:
 def __init__(self,store=None,verification_mode='strict'):
  if verification_mode not in ('strict','verified_session'):raise ValueError('Verified modes only')
  self.backend=Internals(CATALOGUE,CATALOGUE_SHA,store=store);self.store=self.backend.store;self.mode=verification_mode;self.schema_sha=QUERY_SCHEMA_SHA
  with self.backend.index_verifier.access(str(HERE/'STRUCTURED_QUERY_SCHEMA.json'),QUERY_SCHEMA_SHA,'strict') as (fd,a):self.validator=Draft202012Validator(json.load(fd))
 def close(self):self.backend.close()
 def response(self,q,status,reason,groups=None,scope=None,validation=None,provenance=None):
  groups=groups or []
  if not groups and isinstance(q.get('obligations'),list) and len(q['obligations'])<=16:
   groups=[dict(obligation_id=o['id'],mandatory=o.get('mandatory',True),family=o.get('family','unknown'),request_digest=digest(o),status=status,items=[],coverage={},reason=reason) for o in q['obligations'] if isinstance(o,dict) and isinstance(o.get('id'),str)]
  missing=[dict(obligation_id=g['obligation_id'],mandatory=g['mandatory'],status=g['status'],reason=g.get('reason','')) for g in groups if g['status']!='AVAILABLE'];complete=status=='COMPLETE WITHIN VERIFIED CONTRACT'
  return dict(schema_version=VERSION,route='production_structured',query_id='query:'+digest(q),resolved_scope=scope or dict(execution_id=q.get('execution_id'),task_id=q.get('task_id'),variant_id=q.get('variant_id')),requested_obligations=q.get('obligations',[]),groups=groups,missing_obligations=missing,completeness_status=status,reason=reason,independent_validation=validation or dict(passed=False,reason='Request not accepted'),assurance_status=dict(requested=q.get('assurance'),satisfied=complete,verification_mode=self.mode,returned_values_verified=any(g['items'] for g in groups) and all(i['integrity_status']=='verified_source' for g in groups for i in g['items']),historical_runtime_attested=False,provenance=provenance),conditional_assumptions=[dict(obligation_id=g['obligation_id'],properties=g.get('conditional_assumptions',[])) for g in groups if g.get('conditional_assumptions')],limitations=['Completeness covers mandatory explicit obligations only, never safety-claim sufficiency','Saved-index/recorded-label association is not sensor synchronization','Metadata/geometry/counts do not establish support/contact/falling','Historical binary identity and physical calibration remain unattested'],safety_claim_sufficiency='NOT_EVALUATED',safety_claim_verified=False,empirical_admission_enabled=False)
 def prepare(self,q):
  errors=sorted(self.validator.iter_errors(q),key=lambda e:str(list(e.path)))
  if errors:raise QueryError('INVALID SCOPE','Schema: '+errors[0].message)
  if not any(o['mandatory'] for o in q['obligations']):raise QueryError('INVALID SCOPE','At least one mandatory evidence obligation required')
  if len({o['id'] for o in q['obligations']})!=len(q['obligations']):raise QueryError('INVALID SCOPE','Duplicate obligation IDs')
  if q['assurance']=='historical_producer_attestation':raise QueryError('UNSUPPORTED','Historical running producer binaries are not attested')
  if q['assurance']=='provenance_complete' and q['provenance']['level']!='release_graph':raise QueryError('INVALID SCOPE','Provenance assurance requires explicit release_graph level')
  graph=q['assurance']=='provenance_complete' or q['provenance']['level']=='release_graph'
  if graph and q['provenance'].get('scope')!=PROVENANCE_SCOPE:raise QueryError('UNSUPPORTED','Explicit bounded provenance scope required; no historical closure')
  if not graph and q['provenance'].get('scope') is not None:raise QueryError('INVALID SCOPE','Provenance scope requires release_graph')
  row=self.backend.catalogue.execute('select body from catalogue where execution=?',(q['execution_id'],)).fetchone()
  if not row:raise QueryError('INVALID SCOPE','Execution is not indexed; no payload access')
  c=json.loads(row[0]);scope={k:c[k] for k in ('execution_id','task_id','variant_id')}
  if any(q.get(k,c[k])!=c[k] for k in ('task_id','variant_id')):raise QueryError('INVALID SCOPE','Wrong task or variant')
  for o in q['obligations']:
   if any(o.get(k,scope[k])!=scope[k] for k in scope):raise QueryError('INVALID SCOPE','Obligation crosses execution/task/variant scope')
   if o.get('assurance',q['assurance'])!=q['assurance']:raise QueryError('INVALID SCOPE','Per-obligation assurance cannot override or downgrade root assurance')
   family=o['family']
   if family not in REGISTRY or o['field']!=REGISTRY[family]:raise QueryError('UNSUPPORTED','No exact frozen family/field contract')
   if family in TEMPORAL_FAMILIES and 'selector' not in o:raise QueryError('INVALID SCOPE','Explicit temporal selector required')
   if family not in TEMPORAL_FAMILIES and 'selector' in o:raise QueryError('UNSUPPORTED','Timeless identity/metadata cannot fulfill temporal observations')
   interpretation=o.get('interpretation','recorded')
   if family not in CHANNELS:
    if interpretation!='recorded' or q['assurance']=='verified_physical_interpretation' or any(k in o for k in ('component','units','coordinate_frame','required_properties','source_sha256','record_id')):raise QueryError('UNSUPPORTED','Measurement semantics cannot be satisfied by metadata')
    if family=='geometry_identity' and o.get('object_id') not in c['objects']:raise QueryError('INVALID SCOPE','Exact registered object required')
    if family=='main_table_identity' and o.get('object_id','main_table')!='main_table':raise QueryError('INVALID SCOPE','No other logical alias is supported')
    if family not in ('geometry_identity','main_table_identity') and 'object_id' in o:raise QueryError('UNSUPPORTED','This field group has no object filter')
   else:
    raw,sem=self.store.db.execute('select r.body,s.body from rag_channel_records r join h_semantics s on r.id=s.raw_id where s.execution=? and s.channel=?',(q['execution_id'],family)).fetchone();raw=json.loads(raw);sem=json.loads(sem)
    if o.get('record_id',raw['id'])!=raw['id'] or o.get('source_sha256',raw['source_sha256'])!=raw['source_sha256']:raise QueryError('INVALID SCOPE','Wrong original record/source identity')
    if o.get('object_id',raw['object_id'])!=raw['object_id']:raise QueryError('INVALID SCOPE','Wrong measurement object')
    if o.get('component') is not None and o['component'] not in [x['name'] for x in sem['components']]:raise QueryError('INVALID SCOPE','Unknown native component; no guessed aliases')
    if interpretation=='conditional' and not(o.get('allow_conditional') and o.get('required_properties')):raise QueryError('INVALID SCOPE','Conditional interpretation requires explicit properties and permission')
    if o.get('allow_conditional') and interpretation!='conditional':raise QueryError('INVALID SCOPE','Conditional permission must be explicit interpretation')
    if (interpretation=='verified_physical' or q['assurance']=='verified_physical_interpretation') and o.get('allow_conditional'):raise QueryError('UNSUPPORTED','Verified physical assurance cannot accept conditional properties')
   if 'selector' in o:
    s=o['selector']
    if not all(math.isfinite(s[k]) for k in ('start','end')) or s['start']>s['end']:raise QueryError('INVALID SCOPE','Ordered finite selectors required')
    if s['kind']=='frames' and s['end']-s['start']>=4096:raise QueryError('INVALID SCOPE','Bounded frame window required')
  return c,scope,graph
 def frames(self,o,c):
  s=o.get('selector')
  if s is None:return None
  if s['kind']=='frames':return [s['start'],s['end']] if s['end']<c['frames'] else []
  rows=self.store.db.execute('select frame from i_clock_labels where execution=? and sim_time>=? and sim_time<=? order by frame',(c['execution_id'],s['start'],s['end'])).fetchall()
  if not rows:return []
  if len(rows)>4096:raise QueryError('INVALID SCOPE','Bounded recorded-label window required')
  return [rows[0][0],rows[-1][0]]
 def raw(self,o,c,frames,root):
  props=list(o.get('required_properties',[]));interpretation=o.get('interpretation','recorded')
  if interpretation=='verified_physical':props=list(set(props)|{'component_order','units','coordinate_frame'})
  q=ProvenanceQuery(c['execution_id'],task_id=c['task_id'],variant_id=c['variant_id'],channel_id=o['family'],object_id=o.get('object_id'),interval=tuple(frames),component=o.get('component'),units=o.get('units'),coordinate_frame=o.get('coordinate_frame'),required_properties=tuple(props),allow_conditional=o.get('allow_conditional',False),source_sha256=o.get('source_sha256'),verification_mode=self.mode,assurance=root['assurance'],provenance_scope=PROVENANCE_SCOPE if root['assurance']=='provenance_complete' else None)
  r=read_channel(self.store,q)
  if r['status']=='invalid_source_or_contract' or r['status']=='provenance_integrity_failure':raise SourceError(r['reason'])
  items=[]
  for x in r['results']:
   raw=x['raw_record'];sem=x['semantic_record'];items.append(dict(id=raw['id'],family=o['family'],original_evidence_ids=[raw['id']],execution_id=c['execution_id'],task_id=c['task_id'],variant_id=c['variant_id'],source_artifact=dict(path=raw['source_path'],sha256=raw['source_sha256'],selector=raw['source_field']),samples=x['samples'],units=sem['properties']['units'],coordinate_frame=sem['properties']['coordinate_frame'],interpretation_properties=sem['properties'],derived_interpretation=sem['id'],integrity_status=x['source_attestation']['status'],origin='direct_recording',synchronized_physical_instant=False))
  covered=sorted({s['saved_frame_index'] for i in items for s in i['samples']});complete=covered==list(range(frames[0],frames[1]+1));status='AVAILABLE' if items and complete else 'PARTIAL' if items else 'UNSUPPORTED' if r['status'].startswith('unsupported') else 'UNAVAILABLE'
  assumptions=[p for p in props if items and items[0]['interpretation_properties'][p]['status']=='CONDITIONAL']
  if any(s.get('selected_unit_status')=='CONDITIONAL' for i in items for s in i['samples']):assumptions.append('si_component_units')
  return dict(family=o['family'],status=status,items=items,coverage=dict(requested_frames=frames,returned=covered),reason=r['reason'],conditional_assumptions=sorted(set(assumptions)))
 def retrieve(self,request):
  try:
   if not isinstance(request,dict):raise ValueError('Object required')
   wire=json.dumps(request,sort_keys=True,allow_nan=False)
   if len(wire)>128000:raise ValueError('Bounded request required')
   q=json.loads(wire)
  except (ValueError,TypeError,RecursionError):return self.response({},'INVALID SCOPE','Finite bounded JSON object required')
  groups=[];scope=None
  try:
   self.backend.index_verifier.verify(self.backend.index_path,CATALOGUE_SHA,'verified_session')
   if hasattr(self,'schema_sha'):self.backend.index_verifier.verify(str(HERE/'STRUCTURED_QUERY_SCHEMA.json'),self.schema_sha,'verified_session')
   stat=os.stat(self.store.database_path,follow_symlinks=False)
   if not self.store.database_verified or (stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)!=self.store.database_signature:raise SourceError('Pinned database identity changed')
   c,scope,graph=self.prepare(q);self.store.set_scope(c['execution_id'],c['variant_id']);self.store.execution=c['execution_id'];b=self.store.binding(c['execution_id']);windows={o['id']:self.frames(o,c) for o in q['obligations']}
   if sum(w[1]-w[0]+1 for w in windows.values() if w)>16384:raise QueryError('INVALID SCOPE','Total sample budget exceeded')
   proof=read_channel(self.store,ProvenanceQuery(c['execution_id'],channel_id=CHANNELS[0],verification_mode=self.mode))
   if not proof['results']:raise SourceError('Primary source proof rejected: '+proof['reason'])
   for o in q['obligations']:
    family=o['family'];frames=windows[o['id']]
    if frames==[]:g=dict(family=family,status='UNAVAILABLE',items=[],coverage={},reason='No recorded samples in requested scope')
    elif family in CHANNELS:g=self.raw(o,c,frames,q)
    else:
     plan=dict(object_id=o.get('object_id'),action_index=None,assumptions=[]);internal=BundleRequest('explicit structured obligation',c['execution_id'],task_id=c['task_id'],variant_id=c['variant_id'],verification_mode=self.mode)
     g=self.backend.family(internal,plan,c,b,family,frames)
     if family in ('action_metadata','inference_metadata') and any(i<11 for i in range(frames[0],frames[1]+1)):
      g['status']='PARTIAL' if g['items'] else 'UNAVAILABLE';g['coverage']['missing_settling_frames']=[i for i in range(frames[0],frames[1]+1) if i<11]
    g.update(obligation_id=o['id'],mandatory=o['mandatory'],request_digest=digest(o),requested_interpretation=o.get('interpretation','recorded'))
    for item in g['items']:
     selectors=[s['source_selector'] for s in item.get('samples',[])] or [item['source_artifact'].get('selector')];basis=dict(citation_version='1',database_sha256=DATABASE_SHA,record_id=item['id'],source_sha256=item['source_artifact']['sha256'],execution_id=c['execution_id'],task_id=c['task_id'],variant_id=c['variant_id'],selectors=selectors,component=o.get('component'),units=o.get('units'),interpretation=o.get('interpretation','recorded'),required_properties=sorted(o.get('required_properties',[])))
     item['citation_id']='evidence-citation:'+digest(basis);item['citation_basis']=basis
    groups.append(g)
   provenance=self.store.provenance(c['execution_id'],self.mode) if graph else dict(scope='current_source_identity_only',historical_runtime_attested=False)
   provisional=self.response(q,'PARTIAL','Explicit obligations evaluated',groups,scope,provenance=provenance);check=independently_validate(q,provisional,self.store)
   if not check['passed']:return self.response(q,'UNVERIFIED PLAN','Independent source/scope/completeness validation failed',[],scope,check,provenance)
   mandatory=[g for g in groups if g['mandatory']];complete=check['mandatory_fulfilled'];status='COMPLETE WITHIN VERIFIED CONTRACT' if complete else 'PARTIAL' if any(g['items'] for g in groups) else 'UNSUPPORTED' if any(g['status']=='UNSUPPORTED' for g in mandatory) else 'UNAVAILABLE'
   return self.response(q,status,'All mandatory explicit obligations fulfilled' if complete else 'Missing mandatory evidence remains explicit',groups,scope,check,provenance)
  except QueryError as e:return self.response(q,e.status,e.reason,scope=scope)
  except (SourceError,OSError,ValueError,KeyError,AssertionError) as e:return self.response(q,'UNAVAILABLE','Integrity/contract failure: '+str(e),scope=scope)
