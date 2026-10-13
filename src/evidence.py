"""Resolve raw execution evidence by stable run_id and local step_id."""
from pathlib import Path
import h5py,numpy as np
from facts import load,read
from identifiers import step_id

def records(project,name):return load(Path(project)/'data'/(name+'.json'))['records']
def find(project,kind,value):
 field=kind+'_id';plural={'task':'tasks','run':'runs','requirement':'requirements','case':'cases','claim':'claims','event':'events','objection':'objections'}[kind]
 for record in records(project,plural):
  if record[field]==value:return record
 raise ValueError('Unknown '+field+': '+value)
def plain(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,np.generic):return v.item()
 if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [plain(x) for x in v]
 return v
def transition(project,run_id,step):
 step=step_id(step);run=find(project,'run',run_id)
 if step>=run['benchmark_outcome']['steps']:raise ValueError('Step outside recorded execution')
 root=Path(load(Path(project)/'config/project.json')['source_results']).resolve();path=(root/run['evidence']['trajectory']['source_relative_path']).resolve()
 if not path.is_relative_to(root):raise ValueError('Evidence path escapes source results')
 with h5py.File(path,'r') as h:
  assert h.attrs['global_episode_id']==run_id;g=h[f'transitions/{step:06d}'];value=plain(read(g));assert int(value['step'])==step;offset=run['evidence']['control_transitions']['after_action_frame_offset'];frame=int(step+offset) if offset is not None else None
  out={'run_id':run_id,'task_id':run['task_id'],'step_id':step,'record_kind':'raw_control_transition','transition':value,'trajectory':str(path),'hdf5_path':g.name,'event_id':None,'safety_classification':None,'frame_id':frame,'video_frame_id':frame}
  if frame is not None:
   f=h[f'frames/{frame:06d}'];assert int(f.attrs['control_step'])==step
   out['supporting_measurements']={'robot_and_object_observations':{k:plain(read(v)) for k,v in f['raw_observation'].items() if not k.endswith('_image')},'contacts':plain(read(f['simulator/contacts'])),'body_xpos_path':f.name+'/simulator/body_xpos/value','sensor_data':plain(read(f['simulator/sensordata'])) if 'sensordata' in f['simulator'] else None,'raw_image_paths':{k:f.name+'/raw_observation/'+k+'/value' for k in f['raw_observation'] if k.endswith('_image')}}
  return out

