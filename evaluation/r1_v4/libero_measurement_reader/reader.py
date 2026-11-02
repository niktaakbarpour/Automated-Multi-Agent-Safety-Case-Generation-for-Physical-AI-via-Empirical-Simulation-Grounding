"""Bounded read-only LIBERO schema4.0 reader; no support/event classification."""
import importlib.util,math,socket
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.provenance import load,strict_loads,digest,primitive
from evaluation.r1_v4.contracts import Frame,Measurement,Contact,Camera,Uncertainty
from .models import Channel,Snapshot,ContactRecord,Diagnostic,ReadResult
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
MAP=REPO/'reports/fall_review_v2_20261016/corrected_native_geometry_v2.json'
CONSTRAINTS=REPO/'reports/fall_review_v2_20261016/constraints_and_identities.json'
NATIVE=REPO/'reports/fall_checker_dev_v2_20261017/src/native_geometry_v2.py'
COORDINATES=dict(common_frame='MuJoCo_world',length_unit='m',time_unit='s',handedness='right_handed',quaternion='wxyz',gravity=(0.,0.,-9.81))
SHAPES={'flattened':(123,),'time':(),'qpos':(65,),'qvel':(57,),'ctrl':(9,),'body_xpos':(29,3),'body_xquat':(29,4),'geom_xpos':(161,3),'geom_xmat':(161,9),'ncon':()}
OPTIONAL={'qacc':(57,),'act':(0,),'sensordata':(6,),'actuator_force':(9,),'cfrc_ext':(29,6),'cvel':(29,6)}
class Invalid(ValueError):pass
class Missing(ValueError):pass
class Unsupported(ValueError):pass

def native_index(record):
 spec=importlib.util.spec_from_file_location('r1v4_retained_native_index',NATIVE)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod.NativeGeometryIndex(record)
def node(group,path):
 current=group
 for key in path.split('/'):
  if key not in current:raise Missing('missing_field:'+path)
  if not isinstance(current.get(key,getlink=True),h5py.HardLink):raise Invalid('external_or_soft_link:'+path)
  current=current[key]
 return current
def array(group,name,shape,integer=False):
 x=node(group,name+'/value')
 if not isinstance(x,h5py.Dataset) or x.shape!=shape:raise Invalid('array_shape:'+name)
 if x.dtype.kind not in ('iu' if integer else 'f') or x.dtype.itemsize!=8:raise Invalid('array_dtype:'+name)
 if x.external or x.is_virtual:raise Invalid('external_or_virtual_dataset:'+name)
 a=x[()]
 if not np.isfinite(a).all():raise Invalid('nonfinite:'+name)
 return np.asarray(a)
def run_id(ep):return f'libero_long_openvla_oft_task00_seed{1000+ep}_trial{ep:03d}_cfafd9ddc3db'

def read(root,episode,frames=None,*,expected=None,geometry=None,coordinates=None,synthetic=False,development_profile=None,task_profile=None):
 """Production pins restored hashes; injected contracts require synthetic=True."""
 if socket.gethostname().lower()!='hestia':raise RuntimeError('Research inspection requires Hestia')
 result=ReadResult(synthetic=synthetic)
 def diagnostic(status,code,source,frame=None):result.diagnostics.append(Diagnostic(status,code,str(source),frame))
 try:
  extension=None
  if development_profile is not None:
   if synthetic or expected is not None or geometry is not None or coordinates is not None:raise Unsupported('profile_does_not_accept_injected_measurements')
   from evaluation.r1_v4.rag_evidence_database.expansion.profile import approved_profile
   extension=approved_profile(development_profile,root,episode)
  if task_profile is not None:
   if extension is not None or synthetic or expected is not None or geometry is not None or coordinates is not None:raise Unsupported('task_profile_rejects_injected_or_synthetic_contract')
   if task_profile.startswith('multitask-v1:'):
    from evaluation.r1_v4.rag_evidence_database.multitask_expansion.profile import approved_profile
   else:
    from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.profile import approved_profile
   extension=approved_profile(task_profile,root,episode)
  if extension is None and episode not in (0,1,2,14):raise Unsupported('execution_outside_development_scope')
  if (expected is not None or geometry is not None or coordinates is not None) and not synthetic:raise Unsupported('custom_contract_requires_synthetic_fixture')
  contract=load(HERE/'SOURCE_CONTRACT.json')
  result.reader_binding=dict(version='1.0.0',purpose='measurement_only',source_contract_sha256=sha(HERE/'SOURCE_CONTRACT.json'),files={n:sha(HERE/n) for n in ('reader.py','models.py','bridge.py','__main__.py')})
  if extension is not None:
   result.reader_version=extension['version'];result.reader_binding.update(version=extension['version'],development_profile=development_profile,task_profile=task_profile,profile_sha256=extension['profile_sha256'])
  for n,h in contract['bindings'].items():
   if sha(REPO/n)!=h:raise Invalid('retained_dependency_hash:'+n)
  coords=COORDINATES if coordinates is None else coordinates
  if coords!=COORDINATES:raise Invalid('coordinate_contract_mismatch')
  root=Path(root)
  if not root.resolve().is_relative_to('/disk/1/data/niktakbr'):raise Unsupported('source_root_outside_owned_disk1')
  relative=extension.get('relative_task','long/task_00') if extension is not None else 'long/task_00'
  ep=root/relative/f'episode_{episode:03d}'
  bindings=extension['bindings'] if extension is not None else load(HERE/'RESTORED_SOURCES.json') if expected is None else expected
  required=[r for r in bindings if Path(r['restored_path']).parent.name==ep.name or Path(r['restored_path']).name in ('task.bddl','benchmark_initial_states.init')]
  if len(required)!=11:raise Invalid('source_manifest_incomplete')
  paths={}
  for r in required:
   rel=Path(r['restored_path']).parts;rel=Path(*rel[rel.index(relative.split('/')[0]):]);p=root/rel
   if not p.resolve().is_relative_to(root.resolve()) or p.is_symlink():raise Invalid('source_path_escape')
   if not p.is_file():raise Missing('missing_file:'+p.name)
   actual=sha(p)
   if actual!=r['sha256']:raise Invalid('hash_mismatch:'+p.name)
   paths[p.name]=p;result.source_hashes[p.name]={'path':str(p),'sha256':actual,'bytes':p.stat().st_size}
  metadata=load(paths['run_metadata.json']);rid=extension.get('execution_id',run_id(episode)) if extension is not None else run_id(episode)
  expectations={'global_episode_id':rid,'episode':episode,'seed':1000+episode,'model_configuration_id':'85620572476d4a08fc0d','task_configuration_id':'2448c758145ae5ad500f','recorder_schema_version':'4.0','dataset_schema_version':'4.0','task_id':0,'suite_label':'long','task_suite':'libero_10','settling_steps':10,'control_frequency_hz':20,'observation_size':[256,256],'checkpoint':'moojink/openvla-7b-oft-finetuned-libero-spatial-object-goal-10','checkpoint_revision':'638918f3d1c2e43a39a8a20772bdb8b91835e4b7'}
  if extension is not None:expectations.update(extension.get('metadata_expectations',{}))
  for k,v in expectations.items():
   if k not in metadata:raise Missing('metadata_missing:'+k)
   if metadata[k]!=v or type(metadata[k]) is not type(v):raise Invalid('metadata_identity:'+k)
  for k in ('task_name','instruction','initial_state_index','initial_states_sha256','bddl_sha256'):
   if k not in metadata:raise Missing('metadata_missing:'+k)
  if metadata['initial_state_index']!=episode:raise Invalid('initial_state_index')
  result.execution_id=rid
  result.metadata={k:metadata[k] for k in [*expectations,'task_name','instruction','initial_state_index','initial_states_sha256','bddl_sha256']}
  if metadata['bddl_sha256']!=sha(paths['task.bddl']) or metadata['initial_states_sha256']!=sha(paths['benchmark_initial_states.init']):raise Invalid('task_or_initial_archive_binding')
  for n in ('run_oft.py','recording_base.py','semantic_scene.py'):
   source=REPO/'reports/fall_review_20261016/source_evidence'/n
   if metadata.get('source_files_sha256',{}).get(n)!=sha(source):raise Invalid('recorder_provenance:'+n)
  index_record=extension['geometry_index'] if extension is not None and 'geometry_index' in extension else load(MAP) if geometry is None else geometry;idx=native_index(index_record)
  native_count=index_record['native_geom_count']
  idx.validate_recording(rid,sha(paths['simulator.xml']),native_count)
  legacy=load(paths['simulator_index.json'])
  if legacy['body_names']!=index_record['body_names']:raise Invalid('body_identity_mismatch')
  constraints=extension['objects'] if extension is not None and 'objects' in extension else load(CONSTRAINTS)['objects']
  surface_ids=extension.get('surface_ids',list(range(10,16))) if extension is not None else list(range(10,16))
  shapes={k:tuple(v) for k,v in extension['shapes'].items()} if extension is not None and 'shapes' in extension else SHAPES
  optional={k:tuple(v) for k,v in extension['optional_shapes'].items()} if extension is not None and 'optional_shapes' in extension else OPTIONAL
  for obj,info in constraints.items():
   if legacy['body_names'][info['body_id']]!=obj+'_main':raise Invalid('object_identity:'+obj)
   if any(idx.by_id(i)['owner_body_id']!=info['body_id'] for i in info['collision_geom_ids']):raise Invalid('object_geometry_ownership:'+obj)
  result.native_geometry=dict(source_sha256=digest(index_record) if extension is not None and 'geometry_index' in extension else sha(MAP) if geometry is None else digest(index_record),reader_contract_sha256=sha(HERE/'SOURCE_CONTRACT.json'),native_count=native_count,complete_anonymous_ids=True,geometries=index_record['geometries'],objects=constraints,table_collision_ids=surface_ids,frame=coords)
  completeness=load(paths['completion.json'])
  if completeness.get('global_episode_id')!=rid or not completeness.get('complete') or completeness.get('integrity_manifest_sha256')!=sha(paths['integrity_manifest.json']):raise Invalid('completion_binding')
  producer=load(paths['integrity_manifest.json'])
  if producer.get('global_episode_id')!=rid:raise Invalid('producer_manifest_identity')
  for n,p in paths.items():
   if n in producer['files'] and producer['files'][n]['sha256']!=sha(p):raise Invalid('producer_hash:'+n)
  fpath=paths['trajectory.h5'];saved_root=None;prior_time=None;valid=[];invalid=[];times=[]
  sim_fields=set();raw_fields=set();exposed_raw=set()
  expected_count=extension['frames'] if extension is not None else {0:258,1:277,2:246,14:531}[episode]
  if synthetic:expected_count=metadata['synthetic_expected_frames']
  result.coverage={'requested_saved_frames':list(range(expected_count)),'available':[],'validated':[],'missing':[],'invalid':[],'negative_certificates':[],'projection':'saved_measurement_snapshot','continuous_coverage':False}
  with h5py.File(fpath,'r') as h:
   for k in ['global_episode_id','episode','seed','model_configuration_id','task_configuration_id','recorder_schema_version','dataset_schema_version','task_id']:
    if h.attrs.get(k)!=metadata[k]:raise Invalid('hdf5_identity:'+k)
   if h.attrs.get('schema_version')!='4.0':raise Unsupported('hdf5_schema_version')
   initial=array(h,'benchmark_initial_state',shapes['flattened'])
   fg=node(h,'frames');available=sorted(int(k) for k in fg if k.isdigit())
   if any(f'{i:06d}' not in fg for i in available) or len(available)!=len(fg):raise Invalid('frame_identifier_format')
   result.coverage['available']=available
   result.coverage['missing']=sorted(set(range(expected_count))-set(available))
   if available!=list(range(expected_count)):diagnostic('invalid','frame_count_or_gap',fpath)
   selected=set(available if frames is None else frames)
   if any(type(i) is not int or i not in range(expected_count) for i in selected):raise Invalid('requested_frame_outside_domain')
   result.coverage['requested_output_frames']=sorted(selected)
   transitions=node(h,'transitions')
   if len(transitions)!=max(0,expected_count-11):diagnostic('invalid','transition_count',fpath)
   for i in available:
    try:
     g=node(fg,f'{i:06d}');sim=node(g,'simulator');raw=node(g,'raw_observation')
     sim_fields.update(sim.keys());raw_fields.update(raw.keys())
     values={n:array(sim,n,shape,n=='ncon') for n,shape in shapes.items()}
     time=float(values['time']);times.append(time)
     if not np.array_equal(values['flattened'],np.concatenate(([time],values['qpos'],values['qvel']))):raise Invalid('flattened_endpoint_state_mismatch')
     if i==0 and not np.array_equal(initial,values['flattened']):raise Invalid('benchmark_initial_state_mismatch')
     if prior_time is not None and time<=prior_time:raise Invalid('non_monotonic_simulator_time')
     prior_time=time
     stage=g.attrs.get('stage');step=g.attrs.get('control_step')
     expected_stage='before_settling' if i==0 else 'settling' if i<=10 else 'terminal' if i==expected_count-1 else 'control'
     if stage!=expected_stage or step!=(0 if i<=10 else i-11):raise Invalid('frame_state_offset')
     if i>=11:
      transition=node(transitions,f'{i-11:06d}')
      if int(array(transition,'step',(),True))!=i-11 or float(array(transition,'simulator_time',()))!=time:raise Invalid('transition_time_or_index')
     guard=idx.validate_snapshot_transforms(values['body_xpos'],values['body_xquat'],values['geom_xpos'],values['geom_xmat'])
     current_root=(values['geom_xpos'][surface_ids].copy(),values['geom_xmat'][surface_ids].copy())
     if saved_root is None:saved_root=current_root
     elif not all(np.array_equal(a,b) for a,b in zip(saved_root,current_root)):raise Invalid('static_surface_changed')
     contact_node=node(sim,'contacts')
     if 'json' in contact_node.attrs:contacts=strict_loads(contact_node.attrs['json'])
     elif 'value' in contact_node and contact_node['value'].shape==(0,):contacts=[]
     else:raise Missing('missing_contact_bundle')
     if not isinstance(contacts,list) or len(contacts)!=int(values['ncon']):raise Invalid('contact_count')
     records=[]
     for c in contacts:
      if not isinstance(c,dict) or not {'geom1','geom2','dist','pos'}<=set(c):raise Missing('contact_fields')
      a,b=idx.contact_pair(c)
      if type(c['dist']) not in (int,float) or not math.isfinite(c['dist']) or len(c['pos'])!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in c['pos']):raise Invalid('contact_numerics')
      records.append(ContactRecord(c['geom1'],c['geom2'],a['owner_body'],b['owner_body'],float(c['dist']),tuple(c['pos'])))
     for n,shape in optional.items():
      if n in sim:values[n]=array(sim,n,shape)
      else:diagnostic('missing','optional_native_field:'+n,fpath,i)
     rawvalues={}
     for n,shape in [('robot0_eef_pos',(3,)),('robot0_eef_quat',(4,)),('robot0_joint_pos',(7,)),('robot0_joint_vel',(7,)),('robot0_gripper_qpos',(2,)),('robot0_gripper_qvel',(2,))]+[(o+s,shape) for o in constraints for s,shape in [('_pos',(3,)),('_quat',(4,))]]:
      if n in raw:rawvalues[n]=array(raw,n,shape);exposed_raw.add(n)
      else:diagnostic('missing','optional_raw_observable:'+n,fpath,i)
     cams=[];refs=[]
     for camera in ('agentview_image','robot0_eye_in_hand_image'):
      try:
       ds=node(raw,camera+'/value')
       if not isinstance(ds,h5py.Dataset) or ds.external or ds.is_virtual or ds.shape!=(256,256,3) or ds.dtype!=np.uint8:raise Invalid('camera_shape_dtype:'+camera)
       refs.append(dict(camera_id=camera,source_sha256=result.source_hashes['trajectory.h5']['sha256'],hdf5_path=ds.name,shape=list(ds.shape),dtype=str(ds.dtype),snapshot_index=i,capture_time=None,alignment_status='unsupported',pixels_read=False))
       cams.append(Camera(camera,(i,),(),()))
      except Missing as e:diagnostic('missing',str(e),fpath,i)
     valid.append(i)
     if i not in selected:continue
     channels=[];uncertainty=Uncertainty(None,('Physical and phase uncertainty uncalibrated',))
     for prefix,items in [('simulator',values),('raw_observation',rawvalues)]:
      for name,a in sorted(items.items()):
       phase='endpoint_state' if prefix=='simulator' and name in ('time','qpos','qvel','ctrl','flattened') else 'native_last_forward_cache_uncalibrated_phase' if prefix=='simulator' else 'raw_observable_cache_phase_unknown'
       unit='m' if name in ('body_xpos','geom_xpos') else 'dimensionless_wxyz' if name=='body_xquat' else 'dimensionless_rotation_matrix' if name=='geom_xmat' else 's' if name=='time' else 'count' if name=='ncon' else 'native_observable_units_and_convention_unverified' if prefix=='raw_observation' else 'native_model_channel_units'
       frame_id='raw_observable_frame_unverified' if prefix=='raw_observation' else 'MuJoCo_world' if name in ('body_xpos','body_xquat','geom_xpos','geom_xmat') else 'native_configuration_or_channel_frame'
       channels.append(Channel('raw_measurement','trajectory.h5',result.source_hashes['trajectory.h5']['sha256'],f'/frames/{i:06d}/{prefix}/{name}/value',phase,tuple(a.shape),str(a.dtype),Frame(frame_id,'recorded_endpoint_time; channel phase retained','m','s','right_handed'),uncertainty,Measurement(prefix+':'+name,tuple(float(x) for x in a.ravel()),unit)))
     objects={o:dict(body_id=c['body_id'],body_position=values['body_xpos'][c['body_id']].tolist(),body_quaternion_wxyz=values['body_xquat'][c['body_id']].tolist(),collision_geom_ids=c['collision_geom_ids'],root_is_not_com=True,pose_phase='native_last_forward_cache_uncalibrated_phase') for o,c in constraints.items()}
     host={k:g.attrs[k].item() if hasattr(g.attrs[k],'item') else g.attrs[k] for k in ('utc','wall_time_ns','monotonic_ns') if k in g.attrs}
     result.frames.append(Snapshot(i,stage,int(step),time,host,tuple(channels),tuple(records),Contact(tuple((str(c.geom1),str(c.geom2)) for c in records),True,None),tuple(cams),tuple(refs),objects,guard,synthetic))
    except (Missing,Invalid,ValueError,KeyError,TypeError,OSError) as e:
     invalid.append(i);diagnostic('missing' if isinstance(e,Missing) else 'invalid',str(e),fpath,i)
   result.metadata['field_inventory']={'simulator':sorted(sim_fields),'raw_observation':sorted(raw_fields),'unexposed_simulator':sorted(sim_fields-set(shapes)-set(optional)-{'contacts'}),'unexposed_raw_observation':sorted(raw_fields-exposed_raw-{'agentview_image','robot0_eye_in_hand_image'})}
   result.coverage['validated']=valid;result.coverage['invalid']=invalid
   result.coverage['unreturned']=sorted(set(available)-{f.index for f in result.frames})
   if times:result.metadata['observed_time_range']=[min(times),max(times)]
  for n,p in paths.items():
   if sha(p)!=result.source_hashes[n]['sha256']:raise Invalid('source_changed_during_read:'+n)
  diagnostic('unsupported','camera_exposure_alignment',fpath)
  diagnostic('unsupported','raw_observable_frame_units_and_quaternion_conventions_unverified',fpath)
  diagnostic('unsupported','per_contact_forces_and_normals_not_recorded',fpath)
  diagnostic('unsupported','empirical_support_fall_negative_certificates_disabled',fpath)
  result.status='invalid' if any(d.status=='invalid' for d in result.diagnostics) else 'missing' if invalid or result.coverage['missing'] else 'verified_measurements'
 except (Missing,Unsupported,Invalid,ValueError,KeyError,TypeError,OSError) as e:
  result.status='missing' if isinstance(e,Missing) else 'unsupported' if isinstance(e,Unsupported) else 'invalid'
  diagnostic(result.status,str(e),'input_contract')
  result.frames=[]
  if result.coverage:result.coverage['validated']=[]
 return result
