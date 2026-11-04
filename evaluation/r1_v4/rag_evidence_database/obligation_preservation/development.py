"""Development-only authored cases, independent source references."""
import json
from .config import *
from .references import scopes,excluded_scopes,construct

def run():
 selected=scopes(dict(goal=2,long=2,object=2,spatial=2),excluded_scopes());rows=[]
 bank=[('direct','Give joint configuration at simulator time {time}.',(CHANNELS[2],),('recorded_time',),'sim',(),None),('conjunction','Get joint positions and velocities at frame {frame}.',(CHANNELS[2],CHANNELS[3]),(),'mid',(),None),('conjunction','Return arm and gripper configurations at frame {frame}.',(CHANNELS[2],CHANNELS[0]),(),'mid',(),None),('conjunction','Collect gripper state and actuator outputs at frame {frame}.',(CHANNELS[0],CHANNELS[1],CHANNELS[4]),(),'mid',(),None),('temporal','Show arm positions before action {action}.',(CHANNELS[2],),(),'before',(),None),('geometry','Give the native geometry of {object}.',(),('geometry_identity',),'none',(),None),('provenance','Give execution metadata and source hash.',(),('execution_metadata','source_provenance'),'none',(),None),('ambiguity','Give geometry and motion measurements.',(),('geometry_identity',),'none',(('measurement','unresolved_measurement'),('temporal_uncertainty','unspecified_instant')),'AMBIGUOUS'),('ambiguity','Joint positions and velocities near frame {frame}.',(CHANNELS[2],CHANNELS[3]),(),'mid',(('temporal_uncertainty','unspecified_window'),),'AMBIGUOUS'),('unsupported','Give tactile pressure at frame {frame}.',(),(),'mid',(('interpretation','unrecorded_or_unsupported_sensor'),),'UNSUPPORTED'),('unsupported','Return Cartesian gripper positions at frame {frame}.',(CHANNELS[0],),(),'mid',(('interpretation','world_transform'),),'UNSUPPORTED'),('quoted','Source excerpt: "Read joint positions at frame 20". Give source hash.',(),('source_provenance',),'none',(),None)]
 for i,s in enumerate(selected):
  for j,(cat,text,measurements,metadata,kind,extra,status) in enumerate(bank):
   # Geometry/motion lacks an exact object, so reference it as unresolved, not a fabricated binding.
   if cat=='ambiguity' and j==7:
    metadata=();extra=(('source_family','geometry_identity'),('measurement','unresolved_measurement'),('temporal_uncertainty','unspecified_instant'))
   q=construct(s,f'DEV-{i:02d}-{j:02d}',text,measurements,metadata,kind,extra,status or 'COMPLETE WITHIN VERIFIED CONTRACT',category=cat);q['split']='development';rows.append(q)
 (HERE/'DEVELOPMENT_DATASET.jsonl').write_text(''.join(json.dumps(q,sort_keys=True)+'\n' for q in rows));(WORK/'DEVELOPMENT_SELECTION.json').write_text(json.dumps(selected,sort_keys=True,indent=2));print('Development instances',len(rows),'templates',len(bank),flush=True)
if __name__=='__main__':run()
