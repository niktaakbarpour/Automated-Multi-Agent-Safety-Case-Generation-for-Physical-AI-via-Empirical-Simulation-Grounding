"""Audit every returned sample/source/scope, independent of ranking relevance labels."""
import json,collections,contextlib
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
from .config import *
from .dataset import CH,FIELD,UNITS

def run():
 cases={q['id']:q for q in map(json.loads,(HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines())};links=json.loads((HERE/'SOURCE_ASSOCIATIONS.json').read_text())['rows'];rows=[json.loads(p.read_text()) for p in (WORK/'final_v1').glob('*.json')];sources={q['execution_id']:q['reference_artifacts'][0] for q in cases.values()};counts=collections.Counter();errors=[];verifier=SourceVerifier();by={m:collections.Counter() for m in MODES}
 with contextlib.ExitStack() as stack:
  handles={}
  for ex,src in sources.items():
   fd,a=stack.enter_context(verifier.access(src['path'],src['sha256'],'strict'));f=stack.enter_context(h5py.File(fd,'r'));assert f.attrs['global_episode_id']==ex;handles[ex]=f
  for r in rows:
   q=cases[r['case_id']]['request'];mode=r['mode']
   for item in r['output']['items']:
    counts['returned_records']+=1;by[mode]['returned_records']+=1;link=links.get(item['id'])
    for name in ('execution_id','task_id','variant_id','object_id'):
     if q.get(name) is not None:
      counts[name+'_checks']+=1
      if item[name]!=q[name]:errors.append(dict(case=r['case_id'],mode=mode,kind=name))
    counts['source_association_checks']+=1
    if link is None or any(item[k]!=link[k] for k in ('source_path','source_sha256')):errors.append(dict(case=r['case_id'],mode=mode,kind='source_association'))
    if item.get('channel'):
     k=CH.index(item['channel']);f=handles[item['execution_id']]
     for s in item['samples']:
      i=s['saved_frame_index'];selector=f'/frames/{i:06d}/'+FIELD[k];d=f[selector];value=d[()];counts['raw_samples']+=1;by[mode]['raw_samples']+=1;counts['numeric_components']+=int(np.asarray(value).size)
      if s['source_selector']!=selector or s['dtype']!=str(d.dtype) or s['shape']!=list(d.shape) or not np.array_equal(np.asarray(s['value']),value):errors.append(dict(case=r['case_id'],mode=mode,kind='numeric_or_selector',frame=i))
      counts['unit_checks']+=1
      if s['value_units']!=UNITS[k]:errors.append(dict(case=r['case_id'],mode=mode,kind='units',frame=i))
      if q.get('interval'):
       counts['saved_index_checks']+=1
       if not q['interval'][0]<=i<=q['interval'][1]:errors.append(dict(case=r['case_id'],mode=mode,kind='saved_interval',frame=i))
      if q.get('seconds_interval'):
       counts['recorded_clock_checks']+=1;t=float(f[f'/frames/{i:06d}/simulator/time/value'][()]);w=q['seconds_interval']
       if not w[0]<=t<=w[1]:errors.append(dict(case=r['case_id'],mode=mode,kind='recorded_clock',frame=i))
 result=dict(passed=not errors,counts=dict(counts),by_mode={m:dict(v) for m,v in by.items()},errors=errors,maximum_numeric_error=0 if not errors else None,physical_time_synchronization='NOT_INFERRED',reference_path='Every returned array independently indexed from original hash-verified HDF5; units from preserved verified contracts, no target decoder called')
 (WORK/'INDEPENDENT_OUTPUT_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));assert not errors,errors[:5];print('INDEPENDENT OUTPUT AUDIT',dict(counts),flush=True)
if __name__=='__main__':run()
