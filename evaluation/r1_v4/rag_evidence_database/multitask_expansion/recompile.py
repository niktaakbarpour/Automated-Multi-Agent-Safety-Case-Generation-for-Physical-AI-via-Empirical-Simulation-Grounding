"""Independently reconstruct every task's native mapping without physics execution."""
import h5py
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.native import compile_profile
from .plan import HERE,DEST
from .profile import folder

def main(output=None):
 rows=[]
 for key,task in load(HERE/'SOURCE_PLAN.json')['tasks'].items():
  root=DEST/key/'episode_001';expected=load(folder(key)/'NATIVE_PROFILE.json')
  with h5py.File(root/'trajectory.h5','r') as h:snapshot={n:h['frames/000000/simulator/'+n+'/value'][()] for n in ('body_xpos','body_xquat','geom_xpos','geom_xmat')}
  actual=compile_profile(root/'simulator.xml',root/'simulator_asset_manifest.json',root/'simulator_index.json',snapshot,task['objects'],[e['execution_id'] for e in task['executions']],task['fixtures'])
  assert digest(actual)==digest(expected);rows.append({'task':key,'mapping_reproduced':True,'native_geometries':actual['mapping']['native_geom_count'],'physics_steps':0})
 write_new(output or HERE/'INDEPENDENT_PROFILE_CHECK.json',rows);print(rows)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--report',type=__import__('pathlib').Path);a=p.parse_args();main(a.report)
