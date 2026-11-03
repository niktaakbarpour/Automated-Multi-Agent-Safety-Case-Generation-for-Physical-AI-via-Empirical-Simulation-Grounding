"""Independent raw decoder audit of every returned measurement, including irrelevant ones."""
import json,sqlite3
from pathlib import Path
import numpy as np,h5py
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import DATABASE,CHANNELS
class RawAudit:
 def __init__(self):self.db=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);self.verified=set()
 def close(self):self.db.close()
 def check(self,items,case):
  errors=[];numeric=metadata=0;files={}
  try:
   for item in items:
    family=item['family'];a=item['source_artifact'];path=a['path'];expected=a['sha256']
    if (path,expected) not in self.verified:
     if sha(Path(path))!=expected:errors.append('independent_source_hash');continue
     self.verified.add((path,expected))
    if family in CHANNELS or family in ('action_metadata','inference_metadata','recorded_time','camera_references','contact_references'):
     if path not in files:files[path]=h5py.File(path,'r')
     f=files[path]
     if f.attrs['global_episode_id']!=case['execution_id']:errors.append('independent_source_execution')
     for sample in item.get('samples',[]):
      d=f[sample['source_selector']];numeric+=1
      if not np.array_equal(np.asarray(d[()]),np.asarray(sample['value'])) or str(d.dtype)!=sample['dtype']:errors.append('independent_numeric')
      if sample['saved_frame_index'] not in case['reference_frame_indices']:errors.append('independent_temporal_scope')
     v=item.get('value',{});selector=a.get('selector')
     if selector and family not in CHANNELS:
      d=f[selector];metadata+=1
      if family=='action_metadata':
       if v['policy_step']!=int(d.attrs['step']):errors.append('independent_action_step')
       if any(v['policy_attributes'].get(k)!=x for k,x in d.attrs.items()):errors.append('independent_policy_attributes')
       for k,x in v.get('transition_labels',{}).items():
        if not np.array_equal(x,f['transitions'][f"{v['policy_step']:06d}"][k]['value'][()]):errors.append('independent_transition_labels')
      if family=='inference_metadata':
       if any(v['recorded_attributes'].get(k)!=x for k,x in d.attrs.items()):errors.append('independent_inference_attributes')
       if v['policy_input_saved_frame']!=10+int(d.attrs['step']):errors.append('independent_input_frame')
      if family=='recorded_time':
       if v['simulator_endpoint_seconds']!=float(d['simulator/time/value'][()]) or v['recorder_host_wall_ns']!=int(d.attrs['wall_time_ns']) or v['recorder_host_monotonic_ns']!=int(d.attrs['monotonic_ns']):errors.append('independent_clock_labels')
      if family=='camera_references' and (v['shape']!=list(d.shape) or v['dtype']!=str(d.dtype)):errors.append('independent_camera_reference')
    if item.get('id_kind')=='original_channel_record':
     row=self.db.execute('select body from rag_channel_records where id=?',(item['id'],)).fetchone()
     if not row:errors.append('independent_original_channel_id')
   return dict(errors=errors,numeric=numeric,metadata=metadata)
  finally:
   for f in files.values():f.close()
