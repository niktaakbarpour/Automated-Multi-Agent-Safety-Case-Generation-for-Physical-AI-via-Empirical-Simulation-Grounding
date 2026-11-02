"""Hash and independently compile each pilot; no raw-profile shortcut."""
from pathlib import Path
import h5py
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.native import compile_profile
from .plan import HERE,DEST
from .profile import PREFIX,folder

def main():
 plan=load(HERE/'SOURCE_PLAN.json');reports=[]
 for key,task in plan['tasks'].items():
  dest=folder(key);dest.mkdir(parents=True,exist_ok=True);episode=task['pilot_episode'];root=DEST/key/f'episode_{episode:03d}';meta=load(root/'run_metadata.json');rows=[r for r in plan['files'] if r['task']==key and r['phase']=='pilot'];assert len(rows)==11
  bindings=[]
  for r in rows:
   expected=r['expected_sha256'] or meta['initial_states_sha256'];assert sha(r['restored_path'])==expected and Path(r['restored_path']).stat().st_size==r['bytes'];bindings.append({'restored_path':r['restored_path'],'sha256':expected})
  with h5py.File(root/'trajectory.h5','r') as h:snapshot={n:h['frames/000000/simulator/'+n+'/value'][()] for n in ('body_xpos','body_xquat','geom_xpos','geom_xmat')}
  native=compile_profile(root/'simulator.xml',root/'simulator_asset_manifest.json',root/'simulator_index.json',snapshot,task['objects'],[meta['global_episode_id']],task['fixtures'])
  write_new(dest/'NATIVE_PROFILE.json',native)
  write_new(dest/'PROFILE.json',{'name':PREFIX+key,'state':'PILOT_VALIDATION','source_plan_sha256':sha(HERE/'SOURCE_PLAN.json'),'native_profile_sha256':sha(dest/'NATIVE_PROFILE.json'),'allowed_episodes':[episode],'source_bindings':bindings,'empirical_admission_enabled':False})
  from evaluation.r1_v4.libero_measurement_reader.reader import read
  result=read(DEST,episode,task_profile=PREFIX+key)
  if result.status!='verified_measurements' or result.synthetic or any(len(s.camera_references)!=2 for s in result.frames):raise ValueError('pilot failed '+key+': '+str(result.diagnostics))
  report={'passed':True,'task':key,'execution_id':result.execution_id,'frames':len(result.frames),'reader_version':result.reader_version,'native_shapes':native['shapes'],'objects':list(native['objects']),'surface_ids':native['surface_ids'],'source_hashes':result.source_hashes,'physical_safety_conclusion':False,'physics_steps':0}
  write_new(dest/'PILOT_VALIDATION.json',report);reports.append(report);print('Pilot passed',key,len(result.frames),len(native['objects']),flush=True)
 write_new(HERE/'PILOT_VALIDATIONS.json',reports)
if __name__=='__main__':main()
