"""Extract logged facts; no language model, hazard invention, or safety verdicts."""
import json,hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
import h5py,numpy as np

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False));tmp.replace(p)
def read(g):
 if isinstance(g,h5py.Dataset):return g[()]
 if 'value' in g and isinstance(g['value'],h5py.Dataset):return g['value'][()]
 if 'json' in g.attrs:return json.loads(g.attrs['json'])
 return {k:read(v) for k,v in g.items()}
def bddl_language(text):
 matches=re.findall(r'\(\s*:language\s+([^()]*)\)',text,re.I)
 if len(matches)!=1:raise ValueError('Expected exactly one unambiguous BDDL language section')
 return matches[0].strip()
def instruction(recorded,bddl):
 present=isinstance(recorded,str) and bool(recorded)
 return {'text':recorded if present else bddl,'primary_source':'recorded_policy_instruction' if present else 'environment_bddl_fallback','recorded_policy_instruction':recorded,'environment_bddl_language':bddl,'exact_mismatch':recorded!=bddl if present else None,'fallback_used':not present}
def xml_info(path):
 root=ET.fromstring(Path(path).read_text());bodies={e.get('name'):e for e in root.findall('.//body') if e.get('name')};sensors=[{'type':e.tag,**e.attrib} for e in root.findall('./sensor/*')]
 surfaces=[]
 for name,body in bodies.items():
  if name in ['table','floor'] or name.endswith('_table'):
   surfaces.append({'native_body_name':name,'geometries':[dict(e.attrib) for e in body.findall('./geom')],'selection_basis':'Actual XML body name; support-surface candidate, not a prohibited region'})
 return {'bodies':bodies,'sensor_declarations':sensors,'native_surface_geometry':surfaces}
def native_entities(phase,index,xml):
 result=[]
 for kind,key in [('object','object_initial_poses'),('fixture','fixture_initial_poses')]:
  for name,v in phase.get(key,{}).items():
   body=v['root_body'];native=xml['bodies'].get(body);geom_names=[g.get('name') for g in native.findall('.//geom') if g.get('name')] if native is not None else [];joints=v.get('joints',[])
   result.append({'name':name,'kind':kind,'category_name':v.get('category_name'),'root_body_name':body,'body_id':index['body_names'].index(body) if body in index['body_names'] else None,'joint_ids':{n:index['joint_names'].index(n) for n in joints if n in index['joint_names']},'geom_ids':{n:index['geom_names'].index(n) for n in geom_names if n in index['geom_names']},'initial_position_world_m':v.get('initial_position_world_m'),'initial_orientation_wxyz':v.get('initial_orientation_wxyz'),'native_ids_scope':'This run simulator_index.json; numeric IDs are not portable between runs'})
 return result
def scene(phase,xml):
 parsed=phase['parsed_bddl_problem'];declared={n:t for t,names in parsed.get('fixtures',{}).items() for n in names};objects={n:t for t,names in parsed.get('objects',{}).items() for n in names};present=set(declared)|set(objects);regions={n:{**v,'target_declared_in_scene':v.get('target') in present} for n,v in parsed.get('regions',{}).items()}
 containers=[]
 for pred in phase.get('goal_predicates',[]):
  if len(pred)>=3 and str(pred[0]).lower()=='in':
   target=pred[2];owner=target if target in present else regions.get(target,{}).get('target')
   if owner in present:containers.append({'entity_name':owner,'source_goal_predicate':pred,'role_basis':'Destination of an actual environment In predicate'})
 return {'declared_fixtures':declared,'declared_objects':objects,'regions':regions,'native_surface_geometry':xml['native_surface_geometry'],'containers_named_by_goal_predicates':containers,'initial_predicates':parsed.get('initial_state',parsed.get('init',phase.get('randomization_parameters',{}).get('initial_predicates',[]))),'scene_properties':parsed.get('scene_properties',{}),'recorded_background_settings':phase.get('background_settings'),'description':'Environment-declared fixtures: '+', '.join(n+' ('+t+')' for n,t in sorted(declared.items()))+'. Environment-declared objects: '+', '.join(n+' ('+t+')' for n,t in sorted(objects.items()))+'. No extra scene entities or hazards inferred.'}
def inventory(h,ep,xml):
 frame_names=sorted(h['frames']);sample_names=sorted({frame_names[0],frame_names[len(frame_names)//2],frame_names[-1]});samples=[]
 for n in sample_names:
  g=h['frames'][n];samples.append({'frame_id':int(n),'stage':str(g.attrs['stage']),'raw_observation_keys':list(g['raw_observation']),'simulator_keys':list(g['simulator']),'sensordata_shape':list(g['simulator/sensordata/value'].shape) if 'sensordata' in g['simulator'] else None})
 common_raw=set.intersection(*(set(x['raw_observation_keys']) for x in samples));common_sim=set.intersection(*(set(x['simulator_keys']) for x in samples));contact_fields=[]
 for n in sample_names:
  contacts=read(h['frames'][n]['simulator/contacts'])
  if isinstance(contacts,list) and contacts:contact_fields=sorted(set().union(*(set(x) for x in contacts)));break
 groups={k:len(h[k]) for k in h};camera_files={p.stem:{'path':str(p),'bytes':p.stat().st_size} for p in ep.glob('*.mp4')}
 missing=[{'item':'approved_safety_requirements_and_event_checkers','status':'not_provided','consequence':'No safety-event labels or safety-violation verdicts may be produced.'},{'item':'approved_intended_contact_and_protected_object_policy','status':'not_provided','consequence':'Task goals alone do not establish which contacts are unsafe.'},{'item':'object_fragility_damage_and_material_safety_annotations','status':'not_provided','consequence':'Do not invent fragile objects or infer damage from names or task failure.'},{'item':'continuous_physics_substep_video_and_contact_history','status':'not_recorded','consequence':'Control-step snapshots cannot prove absence of intervening contact.'},{'item':'validated_object_collision_extents_and_table_support_binding','status':'not_tabulated','consequence':'XML/asset provenance permits future derivation; a root pose alone does not prove a fall.'},{'item':'safety_limits_or_force_damage_thresholds','status':'not_approved','consequence':'No numeric safety limits are supplied or inferred.'}]
 if not any('force' in k for k in contact_fields):missing.append({'item':'per_contact_force_measurements','status':'not_in_contact_records','consequence':'Body cfrc_ext and named sensor channels are not per-contact force labels.'})
 if xml['sensor_declarations']:missing.append({'item':'named_sensor_numeric_channel_offsets_units_and_calibration','status':'not_in_simulator_index','consequence':'Actual XML sensor declarations and raw sensordata are preserved; validate version-specific channel mapping before force checking.'})
 if not contact_fields:missing.append({'item':'contact_entry_field_schema','status':'no_nonempty_contact_in_sampled_frames','consequence':'Do not infer contact fields from empty samples; inspect additional raw frames.'})
 return {'sampling_scope':'All HDF5 root groups; first, middle, and final frame key inventory; no full trajectory array scan','root_groups':groups,'sampled_frames':samples,'common_raw_observation_keys':sorted(common_raw),'common_simulator_keys':sorted(common_sim),'contact_entry_fields_observed':contact_fields,'sensor_declarations_from_actual_xml':xml['sensor_declarations'],'videos':camera_files,'trajectory_path':str(ep/'trajectory.h5'),'missing_information':missing}
