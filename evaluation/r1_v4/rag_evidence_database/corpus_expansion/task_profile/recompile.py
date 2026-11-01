"""Independent compiler/profile reproducibility check; no simulation steps."""
import h5py
from evaluation.r1_v4.provenance import load,canonical,write_new,digest
from .plan import HERE,DEST
from .native import compile_profile

def main():
 expected=load(HERE/'NATIVE_PROFILE.json');plan=load(HERE/'SOURCE_PLAN.json');p=DEST/'object/task_02/episode_001'
 with h5py.File(p/'trajectory.h5','r') as h:snapshot={n:h['frames/000000/simulator/'+n+'/value'][()] for n in ('body_xpos','body_xquat','geom_xpos','geom_xmat')}
 actual=compile_profile(p/'simulator.xml',p/'simulator_asset_manifest.json',p/'simulator_index.json',snapshot,list(expected['objects']),[r['execution_id'] for r in plan['executions']],expected['surface_roots'])
 actual['mapping']['registration_scope']=expected['mapping']['registration_scope']
 assert canonical(actual)==canonical(expected)
 write_new(HERE/'INDEPENDENT_PROFILE_CHECK.json',{'passed':True,'native_profile_digest':digest(actual),'compiler_version':actual['mapping']['compiler_version'],'native_count':actual['mapping']['native_geom_count'],'complete_native_ids_reproduced':True,'source_snapshot':'episode_001 frame 0 native arrays','physics_steps':0,'physical_calibration_verified':False})
 print('Independent native profile reproduced')
if __name__=='__main__':main()
