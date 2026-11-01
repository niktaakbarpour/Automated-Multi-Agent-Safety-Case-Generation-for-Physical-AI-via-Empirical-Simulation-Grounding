"""Verify pilot bytes and compiled identities, then validate all recorded snapshots."""
import h5py
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from .plan import HERE,DEST
from .native import compile_profile
from .profile import NAME

def main():
 plan=load(HERE/'SOURCE_PLAN.json');rows=[r for r in plan['files'] if r['phase']=='pilot'];assert len(rows)==11
 ep=DEST/'object/task_02/episode_001';meta=load(ep/'run_metadata.json');bindings=[]
 for r in rows:
  p=Path(r['restored_path']);expected=r['expected_sha256'] or meta['initial_states_sha256'];assert sha(p)==expected and p.stat().st_size==r['bytes'];bindings.append({'restored_path':str(p),'sha256':expected})
 task=next(r for r in load(REPO/'data/tasks.json')['records'] if r['task_id']==plan['task']['task_id'])
 assert meta['checkpoint']==task['facts']['scope']['checkpoint'] and meta['checkpoint_revision']==task['facts']['scope']['checkpoint_revision']
 names=list(task['facts']['scene_description']['declared_objects'])
 with h5py.File(ep/'trajectory.h5','r') as h:
  g=h['frames/000000/simulator'];snapshot={n:g[n+'/value'][()] for n in ('body_xpos','body_xquat','geom_xpos','geom_xmat')}
 native=compile_profile(ep/'simulator.xml',ep/'simulator_asset_manifest.json',ep/'simulator_index.json',snapshot,names,[meta['global_episode_id']],list(task['facts']['scene_description']['declared_fixtures']))
 write_new(HERE/'NATIVE_PROFILE.json',native)
 write_new(HERE/'PROFILE.json',{'name':NAME,'state':'PILOT_VALIDATION','source_plan_sha256':sha(HERE/'SOURCE_PLAN.json'),'native_profile_sha256':sha(HERE/'NATIVE_PROFILE.json'),'allowed_episodes':[1],'source_bindings':bindings,'empirical_admission_enabled':False})
 from evaluation.r1_v4.libero_measurement_reader.reader import read
 result=read(DEST,1,task_profile=NAME)
 print('Pilot',result.status,'snapshots',len(result.frames),'objects',len(native['objects']),'native geoms',native['mapping']['native_geom_count'],[d.code for d in result.diagnostics],flush=True)
 if result.status!='verified_measurements' or result.synthetic:raise ValueError('pilot validation failed')
 write_new(HERE/'PILOT_VALIDATION.json',{'passed':True,'execution_id':result.execution_id,'frames':len(result.frames),'objects':list(native['objects']),'native_geometry_count':native['mapping']['native_geom_count'],'source_files':result.source_hashes,'reader_version':result.reader_version,'source_binding':result.reader_binding,'profile_sha256':sha(HERE/'PROFILE.json'),'physical_safety_conclusion':False,'empirical_admission_enabled':False,'simulation_steps':0})
if __name__=='__main__':main()
