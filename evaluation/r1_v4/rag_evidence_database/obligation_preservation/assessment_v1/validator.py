"""Independent original-request audit. Does not import planner, intent, or its vocabulary.
Uses token relations and measurement heads; shared canonical field contracts are explicit.
"""
import re
from .config import CHANNELS

def validation_text(question):
 text=re.sub(r'(?:source text|source excerpt|quoted source)\s*:\s*"[^"]*"',lambda m:' '*len(m[0]),question,flags=re.I)
 text=re.sub(r"(?:source text|source excerpt|quoted source)\s*:\s*'[^']*'",lambda m:' '*len(m[0]),text,flags=re.I)
 return text.lower().replace('_',' ')

def expectations(question,request,catalogue=None):
 text=validation_text(question);tokens=list(re.finditer(r'[a-z]+|\d+(?:\.\d+)?',text));words=[m[0] for m in tokens];requirements={};entities=[];properties=[]
 def need(kind,target,span=(0,len(question)),families=()):requirements[(kind,target)]=dict(type=kind,target=target,span=list(span),families=list(families))
 for k in ('execution_id','task_id','variant_id'):
  if request.get(k) is not None:need('scope',k+'='+str(request[k]))
 if request.get('object_id') is not None:need('entity',str(request['object_id']))
 need('assurance',request.get('assurance','verified_source_values'))
 for k in ('units','coordinate_frame','required_properties','alignment','transformation'):
  if request.get(k) not in (None,(),[],'identity','saved_snapshot_association'):need('interpretation',k+'='+str(request[k]))
 for i,w in enumerate(words):
  if w in ('joint','joints','arm','revolute','articulation','articulations') and not (w in ('joint','joints') and i and words[i-1] in ('gripper','finger','fingers')):entities.append((i,2))
  if w in ('finger','fingers','gripper','claw'):entities.append((i,0))
  if w in ('position','positions','configuration','configurations','posture','angle','angles','displacement','displacements','qpos','aperture','opening','gap','separation'):properties.append((i,(0,)))
  if w in ('velocity','velocities','speed','speeds','rate','rates','qvel'):properties.append((i,(1,)))
  if w in ('state','states'):properties.append((i,(0,1)))
 for i,dims in properties:
  candidates=sorted(entities,key=lambda e:(abs(i-e[0]),e[0]));chosen=[]
  if candidates:
   nearest=candidates[0];chosen=[nearest]
   for e in candidates[1:]:
    between=words[min(e[0],nearest[0])+1:max(e[0],nearest[0])]
    if between and set(between)<=set(('and','the','robot','both','its')):chosen.append(e)
  elif words[i] in ('aperture','opening','gap','separation'):chosen=[(i,0)]
  else:need('measurement','unresolved_measurement',tokens[i].span())
  for ei,base in chosen:
   for d in dims:need('measurement',CHANNELS[base+d],(min(tokens[ei].start(),tokens[i].start()),max(tokens[ei].end(),tokens[i].end())),(CHANNELS[base+d],))
 if any(w in words for w in ('actuator','actuators','motor','motors')) and any(w in words for w in ('force','forces','effort','output','outputs','torque')):need('measurement',CHANNELS[4],tuple(sorted([next(m.start() for m in tokens if m[0] in ('actuator','actuators','motor','motors')),max(m.end() for m in tokens if m[0] in ('output','outputs','effort','force','forces','torque'))])),(CHANNELS[4],))
 if any(w.startswith('contact') for w in words) and any(w in words for w in ('count','counts','entries','tally','number')):need('measurement',CHANNELS[5],(min(m.start() for m in tokens if m[0].startswith('contact') or m[0] in ('count','counts','entries','tally','number')),max(m.end() for m in tokens if m[0].startswith('contact') or m[0] in ('count','counts','entries','tally','number'))),(CHANNELS[5],))
 if re.search(r'\b(?:all|six|every)\b.{0,25}(?:channels|measurement famil|recorded measurement)',text):
  for ch in CHANNELS:need('measurement',ch,re.search(r'\b(?:all|six|every)\b.{0,25}(?:channels|measurement famil\w*|recorded measurement\w*)',text).span(),(ch,))
 # Metadata heads do not substitute for independently recognised measurement heads.
 metadata={'source_provenance':('provenance','checksum','sha256','source hash','source identity','source integrity','source digest','source bytes','lineage'),'recorded_time':('time label','recorded time','simulator time','simulator label','timestamp','host time'),'action_metadata':('action metadata','policy metadata','action record','policy record','chunk metadata'),'inference_metadata':('inference',),'geometry_identity':('geometry','geometries','native body','body index','body identity','collision mesh','collision shape','object identity'),'execution_metadata':('execution metadata','package version','checkpoint','producer revision'),'camera_references':('camera reference','camera frame','image reference','saved image'),'contact_references':('recorded contact','contact reference')}
 for family,terms in metadata.items():
  for term in terms:
   where=text.find(term)
   if where>=0:need('source_family',family,(where,where+len(term)),(family,))
 if 'main table' in text:requirements.pop(('source_family','geometry_identity'),None);need('source_family','main_table_identity',families=('main_table_identity',))
 # Independently read numeric clock words, rather than reuse the planner selector.
 temporal=[]
 for i,w in enumerate(words):
  if w in ('time','label') and i and words[i-1] in ('simulator','simulation') and i+1<len(words) and words[i+1][0].isdigit():temporal.append('simulator_time:'+str(float(words[i+1])))
  if w in ('frame','frames','snapshot','snapshots') and i+1<len(words):
   j=i+1+(words[i+1]=='index')
   if j<len(words) and words[j].isdigit():
    end=words[j+2] if j+2<len(words) and words[j+1] in ('through','to') and words[j+2].isdigit() else words[j];temporal.append('frames:'+words[j]+':'+end)
  if w=='action' and i+1<len(words) and words[i+1].isdigit():
   relation='around' if ('before' in words and 'after' in words) or 'around' in words or 'bracketing' in words else 'before' if 'before' in words else 'after';temporal.append('action:'+words[i+1]+':'+relation)
 if not temporal:
  if any(w in words for w in ('initial','beginning')) or 'first saved' in text or 'first snapshot' in text:temporal=['initial']
  elif 'terminal' in words or 'last saved' in text or 'final snapshot' in text:temporal=['terminal']
  elif 'middle' in words or 'midpoint' in words:temporal=['middle']
 for key in temporal:need('temporal',key)
 if not temporal:
  for key in ('frame_interval','seconds_interval','action_index'):
   if request.get(key) is not None:need('temporal',key+'='+str(request[key]))
 if 'near frame' in text or 'near snapshot' in text:need('temporal_uncertainty','unspecified_window')
 if len(set(temporal))>1:need('temporal_uncertainty','multiple_anchors')
 hazard=re.split(r'without (?:claiming|assuming|inferring)|do not (?:claim|assume|infer|promote)',text)[0]
 for heads,target in [(('world','cartesian'),'world_transform'),(('synchron','simultaneous','sensor clock','camera exposure'),'sensor_synchronization'),(('historical','clean checkout'),'historical_attestation'),(('tactile','taxel','pressure','temperature','thermal','microphone','audio','accelerometer','wrist force','contact force'),'unrecorded_or_unsupported_sensor'),(('physical support','collision event','falling','safety violation'),'physical_event'),(('calibrat','metrolog'),'physical_calibration')]:
  if any(h in hazard for h in heads):need('interpretation',target)
 if re.search(r'(?:applied|executed).{0,15}action.{0,10}(?:values|vector)',text):need('interpretation','unindexed_action_values')
 if 'cache' in text:need('interpretation','cache_offset_seconds:conditional',(text.index('cache'),text.index('cache')+5))
 if any(w in text for w in ('comparison','compare','what changed','difference','subtract','delta','change between','equal','greater than','less than')):need('comparison','requested_comparison')
 if ('evidence' in words and 'supports' in words or 'evidence' in words and 'support' in words) or re.search(r'support.{0,20}(?:numeric|recorded).{0,10}value',text):need('factual_support','requested_numeric_support')
 if any(w in words for w in ('available','missing','absent')):need('availability','requested_inventory')
 if 'motion' in words and not any(k[0]=='measurement' for k in requirements):need('measurement','unresolved_measurement')
 for m in re.finditer(r'\b(?:first|second|third)\s+(?:joint|finger|actuator)\b|\b(?:elbow|wrist|joint\s*\d+)\b',text):need('component',m[0],m.span())
 # Unknown measurement heads must not disappear merely because a clock was recognised.
 for m in re.finditer(r'\b(?:telemetry|magnetometer|odometry|haptic|ultrasound|signals|readouts)\b',text):need('unresolved','unbound_measurement_head',m.span())
 # Residual argument check: unrecognised request content cannot vanish behind a known field.
 ignored=set('conditional interpretation assumption under assuming a an the of in at on by for to from with and or plus also both each all every only raw native actual simulator simulation time label labels frame frames snapshot snapshots seconds before after immediately near around between same execution task variant metadata reference references exact source current simply together inspect collect supply provide document list fetch find display obtain read tell check show give return retrieve get what which were was is are been there this that it these those please can could you me how many number numeric values value stored recorded captured readings measurements observations data supports support evidence specified requested contains contain includes include include available missing absent first last terminal initial final beginning middle midpoint policy action'.split())
 covered=[tuple(e['span']) for e in requirements.values() if e['type'] not in ('scope','assurance','temporal','entity')]
 # Clock/source identifiers are independently recognised context, not measurement content.
 for match in re.finditer(r'(?:simulator|simulation) (?:time|label)\s*=?\s*[0-9.]+|(?:frames?|snapshots?)\s+\d+(?:\s*(?:through|to)\s*\d+)?|action\s+\d+',text):covered.append(match.span())
 for name in (catalogue or {}).get('objects',{}):
  start=text.find(name.replace('_',' '))
  if start>=0:covered.append((start,start+len(name)))
 for key in ('execution_id','task_id','variant_id','object_id'):
  value=request.get(key)
  if isinstance(value,str) and value.lower().replace('_',' ') in text:
   start=text.find(value.lower().replace('_',' '));covered.append((start,start+len(value)))
 residual=[m for m in tokens if m[0] not in ignored and not m[0][0].isdigit() and not any(a<=m.start() and m.end()<=b for a,b in covered)]
 if residual:need('unresolved','unparsed_request_content',(residual[0].start(),residual[-1].end()))
 return list(requirements.values())

def validate(question,request,model,plan,catalogue=None):
 expected=expectations(question,request,catalogue)
 for name in (catalogue or {}).get('objects',{}):
  match=re.search(r'(?<!\w)'+re.escape(name.replace('_',' '))+r'(?!\w)',validation_text(question))
  if match:expected.append(dict(type='entity',target=name,span=list(match.span()),families=[]))
 represented={(o['type'],str(o['target'])):o for o in model['obligations'] if o['mandatory']};failures=[]
 for e in expected:
  o=represented.get((e['type'],e['target']))
  if o is None:failures.append(dict(kind='missing_original_obligation',expectation=e));continue
  if any(f not in plan for f in e['families']):failures.append(dict(kind='missing_plan_family',expectation=e))
  if o['type']=='temporal':
   selector=o.get('selector',{});target=e['target']
   if target.startswith('simulator_time:') and selector.get('value')!=float(target.split(':')[1]):failures.append(dict(kind='clock_selector_changed',expectation=e))
   if target.startswith('frames:') and selector.get('interval')!=[int(x) for x in target.split(':')[1:]]:failures.append(dict(kind='frame_selector_changed',expectation=e))
   if target.startswith('action:') and (selector.get('action')!=int(target.split(':')[1]) or selector.get('relation')!=target.split(':')[2]):failures.append(dict(kind='action_selector_changed',expectation=e))
  if o['type']=='measurement':
   selectors={x['id'] for x in model['obligations'] if x['type']=='temporal'}
   if set(o['required_temporal_scope'] or [])!=selectors:failures.append(dict(kind='temporal_attachment_changed',expectation=e))
  if any(o['scope'].get(k)!=request.get(k) for k in ('execution_id','task_id','variant_id','object_id')):failures.append(dict(kind='scope_changed',expectation=e))
 # Also enforce every declared mandatory obligation: this check alone would be circular.
 for o in model['obligations']:
  if o['mandatory'] and any(f not in plan for f in o['required_families']):failures.append(dict(kind='declared_obligation_omitted',obligation_id=o['id']))
 return dict(passed=not failures,expected=expected,failures=failures,implementation='independent token-relation audit v1; no intent/planner import',limitation='Shared verified ontology and finite overlapping vocabularies can correlate; uncertain cases abstain, no universal NL completeness proof')
