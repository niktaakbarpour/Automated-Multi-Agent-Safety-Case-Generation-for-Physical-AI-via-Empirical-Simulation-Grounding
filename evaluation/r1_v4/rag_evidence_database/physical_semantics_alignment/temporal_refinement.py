"""Separate latest snapshot from chunked policy inference input; no universal index assumption."""
import json,h5py
from .config import WORK
from .audit import save

def run():
 audit=json.loads((WORK/'SEMANTIC_AUDIT.json').read_text());compared=0
 for r in audit['rows']:
  with h5py.File(r['source_path']) as f:
   for t in r['temporal_rows']:
    i=t['saved_frame'];t.pop('policy_input_frame',None)
    if i<11:t.update(latest_available_observation_frame=None,policy_inference_input_frame=None,chunk_id=None,chunk_offset=None);continue
    step=i-11;g=f['policy_steps/'+f'{step:06d}'];cid=int(g.attrs['chunk_id']);offset=int(g.attrs['chunk_offset']);call=f['inference_calls/'+f'{cid:06d}'];first=int(call.attrs['step']);assert first+offset==step and bool(g.attrs['triggered_inference'])==(offset==0)
    t.update(latest_available_observation_frame=i-1,policy_inference_input_frame=first+10,chunk_id=cid,chunk_offset=offset,inference_triggered=bool(g.attrs['triggered_inference']));compared+=1
 audit['chunk_alignment_comparisons']=compared;audit['temporal_schema']='action-chunk-alignment-1.0.0';audit['supersedes']='Initial SEMANTIC_AUDIT.json provisional policy_input_frame label is replaced by separate latest-available and actual chunk-inference input frame. Numeric results are unchanged.'
 save(WORK/'AUDIT_FINAL.json',audit);print('Temporal refinement complete',compared,flush=True)
if __name__=='__main__':run()
