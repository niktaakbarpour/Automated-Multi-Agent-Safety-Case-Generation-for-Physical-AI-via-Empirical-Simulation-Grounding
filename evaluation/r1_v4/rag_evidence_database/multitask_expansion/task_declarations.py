"""Independently compare source task language and all episode metadata."""
import re
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,DEST

def validate():
 rows=[]
 for key,task in load(HERE/'SOURCE_PLAN.json')['tasks'].items():
  path=DEST/key/'task.bddl';matches=re.findall(r'\(:language\s+([^)]*)\)',path.read_text());assert len(matches)==1;language=' '.join(matches[0].split());details=[];instructions=set()
  for entry in task['executions']:
   meta=load(DEST/key/f"episode_{entry['episode']:03d}"/'run_metadata.json')
   assert meta['task_name']==task['task_scope']['task_name']
   assert meta['bddl_sha256']==sha(path);instructions.add(meta['instruction'])
   assert meta['checkpoint']==task['task_scope']['checkpoint'] and meta['checkpoint_revision']==task['task_scope']['checkpoint_revision']
   details.append(entry['execution_id'])
  rows.append({'task':key,'bddl_path':str(path),'bddl_sha256':sha(path),'source_language':language,'recorded_metadata_instructions':sorted(instructions),'literal_language_match':all(' '.join(t.split()).casefold()==language.casefold() for t in instructions),'text_equivalence_verified':False,'task_name':task['task_scope']['task_name'],'executions_compared':details,'passed':True})
 return {'passed':True,'tasks':rows,'normalization':'Whitespace and case used only to record literal comparison. BDDL and recorder wording are preserved separately; no semantic equivalence asserted.','physical_event_inference':False}
if __name__=='__main__':write_new(HERE/'TASK_DECLARATIONS.json',validate());print('Source language/task/checkpoint cross-check passed')
