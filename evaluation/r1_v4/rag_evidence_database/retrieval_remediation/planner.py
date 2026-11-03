"""Deterministic schema-guided proposals; never interprets source text as instructions."""
import re
from .config import CHANNELS,FAMILIES

def interpret(text,catalogue,context):
 if not isinstance(text,str) or not text.strip() or len(text)>2000:return dict(status='AMBIGUOUS',reason='A bounded query is required',families=[])
 t=text.lower().replace('_',' ');t=re.sub(r'rather than[^,.?]*','',t);hits=[];unsupported=[];assumptions=[]
 def add(k):
  if k not in hits:hits.append(k)
 if 'opening mechanism' in t:add(CHANNELS[0])
 clauses=re.split(r'\b(?:and|plus|along with|together with|with)\b|,',t);previous=None;unqualified=False
 def kinds(segment):
  return (bool(re.search(r'\b(finger|fingers|gripper|claw)\b',segment)),bool(re.search(r'\b(arm|robot joint|revolute|hinge|joint angle|joint position|joint velocit|joint rate|posture|bend)\w*',segment)),bool(re.search(r'\b(speed|speeds|velocity|velocities|rate|rates|angular rate)\b',segment)),bool(re.search(r'\b(position|positions|configuration|configurations|angle|angles|displacement|opening|aperture|separation|gap|spread|posture|bend|displacements)\b',segment)))
 for i,segment in enumerate(clauses):
  finger,arm,vel,pos=kinds(segment);state='state' in segment
  if not finger and not arm and previous and (vel or pos):finger,arm=previous
  if (finger or arm) and not (vel or pos or state) and i+1<len(clauses):
   nf,na,nv,np=kinds(clauses[i+1])
   if nf or na:vel,pos=nv,np
  if finger or arm:
   previous=(finger,arm)
   if not(vel or pos or state):unqualified=True;continue
   if finger and (pos or state):add(CHANNELS[0])
   if finger and (vel or state):add(CHANNELS[1])
   if arm and (pos or state):add(CHANNELS[2])
   if arm and (vel or state):add(CHANNELS[3])
 if re.search(r'\b(motor|actuator|actuators|motors)\b',t) and re.search(r'force|output|effort|torque|load',t):add(CHANNELS[4])
 if 'contact' in t and re.search(r'count|tally|number|entries|entry',t):add(CHANNELS[5])
 if re.search(r'(all|six|every).{0,25}(measurement famil|channel|recorded measurement)',t):
  for k in CHANNELS:add(k)
 if re.search(r'\b(action|policy|chunk|command)\b',t) and re.search(r'action metadata|policy metadata|chunk metadata|action record|policy record|action.related metadata|control metadata|recorded (?:policy|action)',t):add('action_metadata')
 if 'inference' in t:add('inference_metadata')
 if re.search(r'recorded contact|contact pair|contact reference',t):add('contact_references')
 if re.search(r'camera reference|camera frame|image reference|saved image|linked image',t):add('camera_references')
 if re.search(r'recorded time|time label|simulator time|simulator label|timestamp|recorder host|clock label',t):add('recorded_time')
 if re.search(r'provenance|source hash|sha256|source digest|checksum|source identity|source integrity|source bytes|artifact verification|lineage',t):add('source_provenance')
 if re.search(r'geometry|geom |geometries|body index|body identity|body binding|body name|simulator body|native body|object identity|xml variant|collision shape|collision mesh',t):add('geometry_identity')
 if 'main table' in t or 'main_table' in text:
  add('main_table_identity')
  if 'geometry_identity' in hits:hits.remove('geometry_identity')
 if re.search(r'execution metadata|declared.{0,25}version|version.{0,25}declared|package versions|checkpoint|producer revision',t):add('execution_metadata')
 hazard=re.sub(r'without (?:claiming|assuming|inferring|treating)[^,.?]*','',t);hazard=re.sub(r'not (?:a )?contact force','',hazard);hazard=re.sub(r'do not (?:claim|assume|infer|promote)[^,.?]*','',hazard)
 for pattern,name in [(r'world.{0,20}(pose|position|velocity|transform)|cartesian','world_transform'),(r'camera exposure|sensor clock|sensor synchronization|same physical instant|same instant|simultaneous|synchroni[sz]','sensor_synchronization'),(r'historical.{0,25}(binary|binaries|producer|container)|clean checkout|timestamp authority','historical_attestation'),(r'(contact|pair).{0,15}force|tactile|taxel|load.cell','contact_force_or_tactile'),(r'physical support|supported by|falling|contact event|collision event|safety violation|r1 compli|r1 viol','physical_event_claim'),(r'physical calibration|calibration certificate|calibrated world|metrology','physical_calibration')]:
  if re.search(pattern,hazard):unsupported.append(name)
 if re.search(r'(executed|applied).{0,15}action.{0,12}(values|vector|numbers)',t):unsupported.append('new_action_measurement_values_not_indexed')
 conditional='cache' in t or '0.002' in t
 if conditional:
  if context.get('allow_conditional') and re.search(r'conditional|assum|interpret',t):assumptions.append('cache offset remains conditional; no shifted samples')
  else:unsupported.append('unverified_cache_clock')
 object_id=context.get('object_id');names=list(catalogue['objects']);mentioned=[n for n in names if re.search(r'(?<!\w)'+re.escape(n.replace('_',' '))+r'(?!\w)',t)]
 if len(mentioned)>1:return dict(status='AMBIGUOUS',reason='Multiple named objects require an explicit per-object plan',families=hits)
 if mentioned:
  if object_id is not None and object_id!=mentioned[0]:return dict(status='INVALID SCOPE',reason='Object context contradicts query',families=hits)
  object_id=mentioned[0]
 if 'geometry_identity' in hits:
  if object_id is None:
   categories={v['category'] for v in catalogue['objects'].values() if v.get('category')};found=[]
   for category in categories:
    if re.search(r'(?<!\w)'+re.escape(category.replace('_',' '))+r'(?!\w)',t):found += [n for n,v in catalogue['objects'].items() if v['category']==category]
   if len(set(found))==1:object_id=found[0]
  if object_id not in catalogue['objects']:return dict(status='AMBIGUOUS',reason='Exact recorded object identity is required',families=hits)
 frames=context.get('frame_interval');seconds=context.get('seconds_interval');action=context.get('action_index');parsed=None
 ranges=re.findall(r'(?:saved )?(?:frames?|snapshots?)\s+(\d+)\s*(?:through|to|and|-)\s*(\d+)',t)
 single=re.findall(r'(?:saved )?(?:frame|snapshot)(?: index)?\s+(\d+)',t)
 actions=re.findall(r'(?:policy )?action\s+(\d+)',t)
 if len(ranges)>1 or not ranges and len(set(single))>1 or len(set(actions))>1:return dict(status='AMBIGUOUS',reason='Multiple temporal anchors require an explicit window',families=hits)
 if ranges:parsed=[int(x) for x in ranges[0]]
 elif single:parsed=[int(single[0])]*2
 elif 'first and last' in t:parsed=[0,catalogue['frames']-1]
 elif re.search(r'initial|first saved|start of the recording|beginning',t):parsed=[0,0]
 elif re.search(r'terminal|last saved|final snapshot|end of the recording',t):parsed=[catalogue['frames']-1]*2
 elif re.search(r'middle|halfway|midpoint',t):parsed=[catalogue['frames']//2]*2
 if actions:
  ai=int(actions[0])
  if action is not None and action!=ai:return dict(status='INVALID SCOPE',reason='Action context contradicts query',families=hits)
  action=ai;parsed=[ai+10,ai+11] if 'before' in t and 'after' in t or 'around' in t or 'bracket' in t else ([ai+10]*2 if 'before' in t else [ai+11]*2)
 if parsed is not None:
  if frames is not None and list(frames)!=parsed:return dict(status='INVALID SCOPE',reason='Frame context contradicts query',families=hits)
  frames=parsed
 clock=re.search(r'(?:simulator|simulation)(?: endpoint)? (?:time|label)\s*=?\s*([0-9]+(?:\.[0-9]+)?)',t)
 if clock:
  ts=[float(clock.group(1))]*2
  if seconds is not None and any(abs(float(a)-b)>1e-12 for a,b in zip(seconds,ts)):return dict(status='INVALID SCOPE',reason='Clock context contradicts query',families=hits)
  seconds=ts
 if frames is None and seconds is None and any(k in CHANNELS or k in ('action_metadata','inference_metadata','recorded_time','contact_references','camera_references') for k in hits):return dict(status='AMBIGUOUS',reason='Saved-frame/action or explicit simulator-clock scope is required',families=hits)
 if frames is not None and (len(frames)!=2 or any(type(i)!=int or i<0 for i in frames) or frames[0]>frames[1]):return dict(status='INVALID SCOPE',reason='Invalid saved-frame interval',families=hits)
 return dict(status='RESOLVED' if (hits or unsupported) and not(unqualified and not hits) else 'AMBIGUOUS',reason='Schema-guided proposal; no source interpretation is inferred',families=hits,unsupported=sorted(set(unsupported)),frame_interval=frames,seconds_interval=seconds,action_index=action,object_id=object_id,assumptions=assumptions,original_query=text)
