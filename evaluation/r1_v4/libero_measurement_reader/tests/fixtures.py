"""Small synthetic measurements, no physics; original evidence remains read-only."""
import copy,json,shutil
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.libero_measurement_reader.reader import HERE,MAP,SHAPES,OPTIONAL
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha
REAL=Path('/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence')
class Fixture:
 def __init__(self,root):
  self.root=Path(root);self.ep=self.root/'long/task_00/episode_000';self.ep.mkdir(parents=True)
  original=REAL/'long/task_00/episode_000';rows=json.loads((HERE/'RESTORED_SOURCES.json').read_text())
  selected=[r for r in rows if Path(r['restored_path']).parent.name=='episode_000' or Path(r['restored_path']).name in ('task.bddl','benchmark_initial_states.init')]
  self.expected=copy.deepcopy(selected)
  for r in self.expected:
   p=Path(r['restored_path']);parts=p.parts;dest=self.root/Path(*parts[parts.index('long'):]);dest.parent.mkdir(parents=True,exist_ok=True)
   if p.name!='trajectory.h5':shutil.copyfile(p,dest)
   r['restored_path']=str(dest)
  self.h5=self.ep/'trajectory.h5';self.meta=json.loads((self.ep/'run_metadata.json').read_text());self.meta.update(synthetic=True,synthetic_expected_frames=13)
  (self.ep/'run_metadata.json').write_text(json.dumps(self.meta))
  index=json.loads(MAP.read_text());geoms=index['geometries']
  with h5py.File(self.h5,'w') as h:
   h.attrs.update({k:self.meta[k] for k in ['global_episode_id','episode','seed','model_configuration_id','task_configuration_id','recorder_schema_version','dataset_schema_version','task_id']});h.attrs['schema_version']='4.0'
   h.create_group('transitions')
   for i in range(13):
    g=h.create_group(f'frames/{i:06d}');g.attrs.update(stage='before_settling' if i==0 else 'settling' if i<=10 else 'terminal' if i==12 else 'control',control_step=0 if i<=10 else i-11,utc='synthetic',wall_time_ns=i,monotonic_ns=i)
    sim=g.create_group('simulator')
    for name,shape in {**SHAPES,**OPTIONAL}.items():
     a=np.zeros(shape,dtype=np.int64 if name=='ncon' else np.float64)
     if name=='time':a=np.asarray(i/20,dtype=np.float64)
     if name=='body_xquat':a[:,0]=1
     if name=='geom_xpos':a=np.array([x['local_position_derived_from_recorded_snapshot'] for x in geoms])
     if name=='geom_xmat':a=np.array([x['local_rotation_derived_from_recorded_snapshot'] for x in geoms]).reshape(161,9)
     sim.create_group(name).create_dataset('value',data=a)
    sim.create_group('contacts').attrs['json']='[]'
    raw=g.create_group('raw_observation')
    for cam in ('agentview_image','robot0_eye_in_hand_image'):raw.create_group(cam).create_dataset('value',shape=(256,256,3),dtype=np.uint8)
    if i>=11:
     t=h['transitions'].create_group(f'{i-11:06d}')
     t.create_group('step').create_dataset('value',data=np.int64(i-11));t.create_group('simulator_time').create_dataset('value',data=np.float64(i/20))
  with h5py.File(self.h5,'r+') as h:
   for i in range(13):
    g=h[f'frames/{i:06d}/simulator'];g['flattened/value'][()]=np.concatenate(([i/20],g['qpos/value'][()],g['qvel/value'][()]))
   h.create_group('benchmark_initial_state').create_dataset('value',data=h['frames/000000/simulator/flattened/value'][()])
  self.reseal()
 def reseal(self):
  producer=json.loads((self.ep/'integrity_manifest.json').read_text())
  for r in self.expected:
   p=Path(r['restored_path'])
   if p.name not in ('completion.json','integrity_manifest.json') and p.exists():producer['files'][p.name]={'sha256':sha(p),'bytes':p.stat().st_size}
  (self.ep/'integrity_manifest.json').write_text(json.dumps(producer))
  completion=json.loads((self.ep/'completion.json').read_text());completion['integrity_manifest_sha256']=sha(self.ep/'integrity_manifest.json');(self.ep/'completion.json').write_text(json.dumps(completion))
  for r in self.expected:
   p=Path(r['restored_path'])
   if p.exists():r['sha256']=sha(p)
 def mutate(self,fn):
  with h5py.File(self.h5,'r+') as h:fn(h)
  self.reseal()
