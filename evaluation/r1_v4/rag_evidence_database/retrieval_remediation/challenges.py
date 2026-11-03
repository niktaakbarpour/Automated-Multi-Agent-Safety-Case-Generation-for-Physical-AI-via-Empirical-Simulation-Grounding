"""Post-freeze integrity challenges; no rule changes or holdout exclusions."""
import json
from dataclasses import replace
from .config import *
from .reference import make
from .run_eval import run
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
def main():
 scopes=json.loads((WORK/'HOLDOUT_SELECTION.json').read_text());rows=[]
 for i in (0,8,16):
  s=scopes[i]
  specs=[('unit',dict(units='kg'),'Read finger positions at frame {frame}.'),('coordinate',dict(coordinate_frame='world'),'Read finger positions at frame {frame}.'),('assurance',dict(assurance='guaranteed_safety'),'Read finger positions at frame {frame}.'),('property',dict(required_properties=['sensor_clock_synchronized']),'Read finger positions at frame {frame}.'),('task',dict(task_id='wrong_task'),'Read finger positions at frame {frame}.'),('time',dict(frame_interval=[-1,1]),'Read finger positions.'),('anchors',{},'Read finger positions at frame 20 and frame 30.'),('instruction',{},'Read finger positions at frame {frame}.')]
  for name,overrides,text in specs:
   kind='instruction_source' if name=='instruction' else 'unsupported';q=make(s,'CHALLENGE',text,[],kind,i);q['request'].update(overrides);q.update(id=f'KC-{name}-{i:02d}',split='challenge',template_id=name);rows.append(q)
 p=HERE/'FROZEN_CHALLENGE_DATASET.jsonl'
 if p.exists():assert p.read_text()==''.join(json.dumps(q,sort_keys=True)+'\n' for q in rows)
 else:p.write_text(''.join(json.dumps(q,sort_keys=True)+'\n' for q in rows))
 run(p,'challenges_v1',modes=('bundle',))
if __name__=='__main__':main()
