"""Only original 5J development questions and new source-grounded development cases."""
import json
from .config import *
from .reference import scopes,make

def run():
 j=HERE.parent/'readiness_evaluation';original=[]
 for line in (j/'EVALUATION_DATASET.jsonl').open():
  if '"split": "development"' in line:original.append(json.loads(line))
 assert len(original)==36
 (WORK/'ORIGINAL_5J_DEVELOPMENT.jsonl').write_text(''.join(json.dumps(q,sort_keys=True)+'\n' for q in original))
 excluded={r['execution'] for r in json.loads((j/'EVALUATION_SELECTION.json').read_text())};selected=scopes(dict(goal=2,long=2,object=2,spatial=2),excluded);rows=[]
 for i,s in enumerate(selected):
  specs=[('C1','Show the finger position readings at frame {frame}.',[CHANNELS[0]],'supported'),('C2','Give arm velocities before and after action {action}.',[CHANNELS[3]],'action'),('C3','Which native collision geometry identifies {object}?',['geometry_identity'],'supported'),('C4','Collect gripper state, action metadata and simulator time labels around action {action}.',[CHANNELS[0],CHANNELS[1],'action_metadata','recorded_time'],'action'),('C5','Find calibrated tactile pressure at frame {frame}.',[],'unsupported'),('C6','Return world Cartesian gripper positions at frame {frame}.',[],'unsupported'),('C7','Give the recorded execution metadata and source hash.',['execution_metadata','source_provenance'],'supported'),('C8','Show arm positions at frame {frame} using the incompatible variant.',[],'wrong_variant'),('C9','Does the native motor output at frame {frame} equal {value}?',[CHANNELS[4]],'supported')]
  if i%2:
   specs[0]=('C1','Inspect finger speeds at the terminal snapshot.',[CHANNELS[1]],'end');specs[1]=('C2','Give arm positions at simulator time {time} seconds.',[CHANNELS[2]],'seconds');specs[3]=('C4','Return arm positions, inference metadata and native geometry for {object} around action {action}.',[CHANNELS[2],'inference_metadata','geometry_identity'],'action');specs[4]=('C5','Authenticate the historical producer binary.',[],'historical');specs[5]=('C6','Find simultaneous sensor timestamps at frame {frame}.',[],'unsupported');specs[8]=('C9','Check the first joint angle at the initial snapshot against {value}.',[CHANNELS[2]],'begin')
  other=next(x['binding']['variant_id'] for x in selected if x['binding']['variant_id']!=s['binding']['variant_id'])
  for cat,text,families,kind in specs:
   q=make(s,cat,text,families,kind,i,other);q.update(id=f'KDEV-{cat}-{i:02d}',split='development',label_origin='new independent original-source construction');rows.append(q)
 (HERE/'DEVELOPMENT_DATASET.jsonl').write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in rows));(WORK/'DEVELOPMENT_SELECTION.json').write_text(json.dumps(selected,sort_keys=True,indent=2));print('NEW DEVELOPMENT',len(rows),'plus original',len(original),flush=True)
if __name__=='__main__':run()
