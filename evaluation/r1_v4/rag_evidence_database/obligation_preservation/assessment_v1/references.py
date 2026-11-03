"""Manual obligation specifications + original-source decoder. No target imports."""
import json,sqlite3,hashlib
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.reference import scopes,make as source_reference
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def excluded_scopes():
 k=HERE.parent/'retrieval_remediation';j=HERE.parent/'readiness_evaluation';out={r['execution'] for r in json.loads((j/'EVALUATION_SELECTION.json').read_text())}
 for filename in ('DEVELOPMENT_SELECTION.json','HOLDOUT_SELECTION.json','HOLDOUT_SELECTION_V2.json'):out|={r['execution_id'] for r in json.loads((Path('/disk/1/data/niktakbr/trustworthy-phase5k-working')/filename).read_text())}
 return out

def construct(scope,identifier,text,measurements=(),metadata=(),kind='mid',extra=(),expected_status='COMPLETE WITHIN VERIFIED CONTRACT',overrides=None,category='direct'):
 # The field list and obligation list are authored inputs, never inferred from target output.
 families=list(measurements)+list(metadata);oldkind={'sim':'seconds','range':'range','initial':'begin','terminal':'end','action':'action','before':'action','after':'action'}.get(kind,'supported');q=source_reference(scope,category,text,families,oldkind);request=q['request'];request.update(overrides or {});mid=scope['frames']//2;frames=[mid]
 if kind=='range':frames=[mid-1,mid]
 if kind=='initial':frames=[0]
 if kind=='terminal':frames=[scope['frames']-1]
 if kind=='before':frames=[mid-1]
 if kind=='action':frames=[mid-1,mid]
 # source_reference substitutes {frame} using oldkind. Resolve before/after explicitly.
 if kind=='before':q['query']=text.format(frame=mid-1,start=mid-1,end=mid,action=mid-11,object=next(iter(scope['binding']['objects'])))
 refs=[]
 def add(kind,target,families=()):refs.append(dict(type=kind,target=target,mandatory=True,required_families=list(families),basis='Authored original-question obligation; verified field/source contract',source_artifacts=q['source_artifacts']))
 for field in ('execution_id','task_id','variant_id'):add('scope',field+'='+str(request[field]))
 if request.get('object_id') is not None:add('entity',request['object_id'])
 add('assurance',request.get('assurance','verified_source_values'))
 for key in ('units','coordinate_frame','required_properties','alignment','transformation'):
  v=request.get(key)
  if v not in (None,(),[],'identity','saved_snapshot_association'):add('interpretation',key+'='+str(v))
 for ch in measurements:add('measurement',ch,(ch,))
 for family in metadata:add('source_family',family,(family,))
 if kind=='sim':
  label=round(float(request['seconds_interval'][0]),9);add('temporal','simulator_time:'+str(label),('recorded_time',))
 elif kind in ('action','before','after'):add('temporal','action:'+str(mid-11)+':'+('around' if kind=='action' else kind))
 elif kind in ('initial','terminal'):add('temporal',kind)
 elif kind in ('mid','range'):add('temporal','frames:'+str(frames[0])+':'+str(frames[-1]))
 for typ,target in extra:add(typ,target)
 if any(f in ('geometry_identity',) for f in metadata):
  obj=q['reference_metadata']['geometry_identity']['object_id'];add('entity',obj)
 # Independently read every requested array and exact original frame selector.
 facts={}
 with h5py.File(scope['source_path'],'r') as f:
  assert f.attrs['global_episode_id']==scope['execution_id']
  for ch in measurements:
   rows=[]
   for frame in frames:
    selector=f'/frames/{frame:06d}/'+FIELDS[CHANNELS.index(ch)];d=f[selector];rows.append(dict(frame=frame,value=np.asarray(d[()]).tolist(),dtype=str(d.dtype),shape=list(d.shape),selector=selector,units=UNITS[CHANNELS.index(ch)]))
   facts[ch]=rows
 source_hash=sha(Path(scope['source_path']));assert source_hash==scope['source_sha256']
 return dict(id=identifier,category=category,query=q['query'],request=request,reference_obligations=refs,expected_families=families,reference_samples=facts,reference_metadata=q['reference_metadata'],source_path=scope['source_path'],source_sha256=source_hash,source_artifacts=q['source_artifacts'],reference_frame_indices=frames,execution_id=scope['execution_id'],task_id=scope['binding']['task_id'],variant_id=scope['binding']['variant_id'],suite=scope['suite'],expected_status=expected_status,critical=expected_status not in ('COMPLETE WITHIN VERIFIED CONTRACT','PARTIAL'),human_reference=False,independent_reference='Authored obligation inventories plus original HDF5/XML/JSON; no target planner/validator outputs')
