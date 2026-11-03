"""Planner: clause/entity/property composition from a source-grounded vocabulary."""
import json,re
from .config import *
from .model import obligation
VOCAB=json.loads((HERE/'vocabulary.json').read_text())

def linguistic_text(text):
 chars=list(text);ignored=[]
 # Only explicitly attributed source quotations are excluded, not user-quoted fields.
 pattern=r'(?:source (?:text|excerpt)|quoted source)\s*:\s*(["\'])'
 for m in re.finditer(pattern,text,re.I):
  close=text.find(m.group(1),m.end())
  if close<0:continue
  ignored.append(dict(span=[m.start(),close+1],kind='untrusted_source_quotation'))
  for i in range(m.start(),close+1):chars[i]=' '
 return ''.join(chars),ignored

def derive(text,request,catalogue):
 clean,ignored=linguistic_text(text);t=clean.lower().replace('_',' ');t=re.sub(r'(?<=gripper )joints?|(?<=finger )joints?',lambda m:' '*len(m[0]),t);scope={k:request.get(k) for k in ('execution_id','task_id','variant_id','object_id')};out=[]
 def add(kind,target,basis,families=(),status='RESOLVED',uncertainty=None):
  if any(o['type']==kind and o['target']==target for o in out):return
  out.append(obligation(text,kind,target,basis,families,status,scope,uncertainty=uncertainty))
 for k in ('execution_id','task_id','variant_id'):
  if request.get(k) is not None:add('scope',k+'='+str(request[k]),'request.'+k)
 if request.get('object_id') is not None:add('entity',str(request['object_id']),'request.object_id')
 add('assurance',request.get('assurance','verified_source_values'),'request.assurance')
 for key in ('units','coordinate_frame','required_properties','alignment','transformation'):
  v=request.get(key)
  if v not in (None,(),[],'identity','saved_snapshot_association'):add('interpretation',key+'='+str(v),'request.'+key)
 # Numeric temporal selectors remain separate obligations, never measurements.
 temporal=[]
 for m in re.finditer(r'(?:simulator|simulation)(?: endpoint)?\s+(?:time|label)\s*=?\s*(\d+(?:\.\d+)?)',t):temporal.append(('simulator_time:'+str(float(m[1])),m.span(),dict(clock='simulator_recorded_label',value=float(m[1]))))
 for m in re.finditer(r'(?:frames?|snapshots?)(?: index)?\s+(\d+)(?:\s*(?:through|to|-)\s*(\d+))?',t):temporal.append(('frames:'+m[1]+':'+(m[2] or m[1]),m.span(),dict(clock='saved_frame_index',interval=[int(m[1]),int(m[2] or m[1])])) )
 for m in re.finditer(r'action\s+(\d+)',t):
  before='before' in t;after='after' in t;relation='around' if before and after or re.search(r'around|bracket',t) else 'before' if before else 'after';temporal.append(('action:'+m[1]+':'+relation,m.span(),dict(clock='policy_action_association',action=int(m[1]),relation=relation)))
 for word,key in [('initial','initial'),('beginning','initial'),('first saved','initial'),('first snapshot','initial'),('terminal','terminal'),('last saved','terminal'),('final snapshot','terminal'),('middle','middle'),('midpoint','middle')]:
  if word in t and not temporal:
   i=t.index(word);temporal.append((key,(i,i+len(word)),dict(clock='saved_frame_index',relative=key)))
 for key,span,details in temporal:add('temporal',key,span,('recorded_time',) if details['clock']=='simulator_recorded_label' else ());out[-1]['selector']=details
 if not temporal:
  for key in ('frame_interval','seconds_interval','action_index'):
   if request.get(key) is not None:add('temporal',key+'='+str(request[key]),'request.'+key)
 if re.search(r'\btime\s+\d',t) and not temporal:add('temporal','unknown_clock',(0,len(text)),status='AMBIGUOUS',uncertainty='Clock domain not specified')
 if 'near frame' in t or 'near snapshot' in t:add('temporal_uncertainty','unspecified_window',(0,len(text)),status='AMBIGUOUS',uncertainty='Near has no defined radius')
 def tokens(s):return set(re.findall(r'\b\w+\b',s))
 all_tokens=tokens(t);all_entities={e for e,terms in VOCAB['entities'].items() if all_tokens&set(terms)};all_props={p for p,terms in VOCAB['properties'].items() if all_tokens&set(terms)};previous=set()
 for segment in re.finditer(r'[^,;]+?(?=\band\b|\bplus\b|[,;]|$)',t):
  s=segment.group();words=tokens(s);entities={e for e,terms in VOCAB['entities'].items() if words&set(terms)};props={p for p,terms in VOCAB['properties'].items() if words&set(terms)}
  if entities and not props:props=all_props
  if props and not entities:entities=previous or (all_entities if len(all_entities)==1 else set())
  if entities:previous=entities
  for entity in sorted(entities):
   pos='position' in props or 'state' in props;vel='velocity' in props or 'state' in props
   for k in ([0] if pos else [])+([1] if vel else []):
    family=CHANNELS[k+(2 if entity=='arm' else 0)];add('measurement',family,segment.span(),(family,))
 if re.search(r'\b(?:actuator|motor)s?\b',t) and re.search(r'\b(?:outputs?|forces?|effort|torque)\b',t):add('measurement',CHANNELS[4],(0,len(text)),(CHANNELS[4],))
 if re.search(r'contact',t) and re.search(r'count|entries|tally|number',t):add('measurement',CHANNELS[5],(0,len(text)),(CHANNELS[5],))
 if re.search(r'(?:all|six|every).{0,25}(?:channels|measurement famil|recorded measurement)',t):
  for ch in CHANNELS:add('measurement',ch,(0,len(text)),(ch,))
 patterns={'action_metadata':r'action metadata|policy metadata|action record|policy record|chunk metadata','inference_metadata':r'inference','recorded_time':r'time labels?|simulator time|simulator label|recorded time|timestamps?|host time','source_provenance':r'provenance|source hash|source identity|source integrity|checksum|sha256|source digest|source bytes|lineage','geometry_identity':r'geometr|native body|body index|body identity|collision mesh|collision shape|object identity','execution_metadata':r'execution metadata|declared.{0,25}version|package version|checkpoint|producer revision','contact_references':r'recorded contact|contact reference','camera_references':r'camera reference|camera frame|image reference|saved image'}
 for family,pattern in patterns.items():
  m=re.search(pattern,t)
  if m:add('source_family',family,m.span(),(family,))
 if 'main table' in t:
  out=[o for o in out if o['target']!='geometry_identity'];add('source_family','main_table_identity',(t.index('main table'),t.index('main table')+10),('main_table_identity',))
 # Unsupported requests remain mandatory visible obligations, including source absence.
 hazard=re.sub(r'without (?:claiming|assuming|inferring)[^,.?]*','',t);hazard=re.sub(r'do not (?:claim|assume|infer|promote)[^,.?]*','',hazard)
 unsupported={r'world|cartesian':'world_transform',r'simultaneous|synchroni[sz]|sensor clock|camera exposure':'sensor_synchronization',r'historical.{0,30}(?:binar|producer)|clean checkout':'historical_attestation',r'tactile|taxel|wrist force|contact force|pressure|temperature|thermal|microphone|audio|accelerometer':'unrecorded_or_unsupported_sensor',r'physical support|collision event|falling|safety violation':'physical_event',r'calibrat|metrolog':'physical_calibration',r'(?:applied|executed).{0,15}action.{0,10}(?:values|vector)':'unindexed_action_values'}
 for pattern,target in unsupported.items():
  m=re.search(pattern,hazard)
  if m:add('interpretation',target,m.span(),status='UNSUPPORTED',uncertainty='No validated interpretation contract')
 if 'cache' in t:
  add('interpretation','cache_offset_seconds:conditional',(t.index('cache'),t.index('cache')+5),status='CONDITIONAL' if request.get('allow_conditional') else 'UNSUPPORTED',uncertainty='Inherited conditional cache offset, never synchronized samples')
 if re.search(r'compar|what changed|difference|subtract|delta|change between|equal|greater than|less than',t):add('comparison','requested_comparison',(0,len(text)),status='UNSUPPORTED',uncertainty='No validated comparison-result contract; raw operands do not fulfill a comparison')
 if re.search(r'(?:evidence.{0,20}support|support.{0,20}(?:numeric|recorded).{0,10}value)',t):add('factual_support','requested_numeric_support',(0,len(text)),status='UNSUPPORTED',uncertainty='Retrieval API does not classify factual support; raw values can be requested explicitly')
 if re.search(r'available|missing|absent',t):add('availability','requested_inventory',(0,len(text)),status='UNSUPPORTED',uncertainty='An unbounded available/missing inventory is not an evidence measurement')
 if re.search(r'\b(?:motion|configuration|configurations|pose|poses|state|states|measurements?|readings?)\b',t) and not any(o['type']=='measurement' for o in out) and not any(o['resolution_status']=='UNSUPPORTED' for o in out):add('measurement','unresolved_measurement',(0,len(text)),status='AMBIGUOUS',uncertainty='Measurement entity/property not uniquely bound')
 for m in re.finditer(r'\b(?:first|second|third)\s+(?:joint|finger|actuator)\b|\b(?:elbow|wrist|joint\s*\d+)\b',t):
  component=m[0];compatible=[o['target'] for o in out if o['type']=='measurement' and o['target'] in (CHANNELS[2:4] if 'joint' in component else CHANNELS[:2] if 'finger' in component else CHANNELS[4:5] if 'actuator' in component else ())]
  add('component',component,m.span(),tuple(compatible),status='RESOLVED' if compatible else 'UNSUPPORTED',uncertainty='Existing native component order only; no elbow/wrist logical alias')
 for name in catalogue.get('objects',{}):
  if re.search(r'(?<!\w)'+re.escape(name.replace('_',' '))+r'(?!\w)',t):add('entity',name,(t.index(name.replace('_',' ')),t.index(name.replace('_',' '))+len(name)))
 selectors=[o['id'] for o in out if o['type']=='temporal']
 for o in out:
  if o['type']=='measurement':o['required_temporal_scope']=selectors.copy()
 if len(selectors)>1:add('temporal_uncertainty','multiple_anchors',(0,len(text)),status='AMBIGUOUS',uncertainty='No per-clause multi-instant binding contract')
 if any(o['type']=='measurement' for o in out) and not selectors:add('temporal_uncertainty','unspecified_instant',(0,len(text)),status='AMBIGUOUS',uncertainty='Explicit saved-frame/action/clock scope required')
 families=list(dict.fromkeys(f for o in sorted(out,key=lambda x:0 if x['type']=='measurement' else 1 if x['type']=='source_family' else 2) for f in o['required_families']))
 return dict(version=VERSION,original_query=text,linguistic_text=clean,ignored_source_spans=ignored,obligations=out,families=families,temporal_selector_ids=selectors)
