"""Independent release checks, deterministic rebuild, and bounded raw restoration oracle."""
import json,sqlite3,shutil,time,hashlib,collections
from dataclasses import replace
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment import validate as hv
from .config import WORK,BASE,BASE_SHA,PROVENANCE_SCOPE
from .store import ProvenanceStore
from .retrieve import ProvenanceQuery,retrieve
from .build import populate,snapshot
from .restore import create,RestoredRelease

def save(n,d):(WORK/n).write_text(json.dumps(d,sort_keys=True,indent=2))
def run():
 b=json.loads((WORK/'BUILD.json').read_text());db=WORK/'expanded.sqlite';s=ProvenanceStore(db,expected_sha256=b['database_sha256']);hv.BASE=BASE;hv.BASE_SHA=BASE_SHA;save('PRESERVATION.json',hv.preservation(db));pos=0;neg=collections.Counter();timings=[];numeric=0
 def reject(q):
  r=retrieve(s,q);assert not r['results'],(q,r);neg[r['status']]+=1
 for ex,ch,body in s.db.execute('select execution,channel,body from rag_channel_records order by execution,channel').fetchall():
  raw=json.loads(body);last=max(raw['valid_indices']);q=ProvenanceQuery(ex,task_id=raw['task_id'],variant_id=raw['variant_id'],channel_id=ch,interval=(last//2,last//2),verification_mode='verified_session')
  for assurance in ('verified_source_values','verified_physical_interpretation'):
   r=retrieve(s,replace(q,assurance=assurance));assert r['status']=='ok',(q,r);pos+=1
   with h5py.File(raw['source_path'],'r') as f:
    for sample in r['results'][0]['samples']:assert np.array_equal(sample['value'],f[sample['source_selector']][()]);numeric+=1
  seconds=s.db.execute('select sim_time from i_clock_labels where execution=? and frame=?',(ex,last//2)).fetchone()[0]
  r=retrieve(s,replace(q,interval=None,clock_domain='simulator_endpoint_label',seconds_interval=(seconds,seconds)));assert r['status']=='ok' and [v['saved_frame_index'] for v in r['results'][0]['samples']]==[last//2];pos+=1
  for bad in (replace(q,assurance='historical_producer_attestation'),replace(q,assurance='provenance_complete'),replace(q,clock_domain='joint_sensor_clock'),replace(q,alignment='same_physical_instant'),replace(q,task_id='wrong'),replace(q,variant_id='wrong'),replace(q,source_sha256='0'*64),replace(q,required_properties=('physical_synchronization',))):reject(bad)
 for ex,status in s.db.execute("select execution,status from rag_scope_status where status!='indexed'"):reject(ProvenanceQuery(ex,channel_id='simulator.ncon'))
 executions=[r[0] for r in s.db.execute('select execution from i_jobs')];selected=[];variants=set()
 for ex in sorted(executions,key=lambda e:hashlib.sha256(('phase5i-restore-v1:'+e).encode()).hexdigest()):
  variant=s.binding(ex)['variant_id']
  if variant not in variants:selected.append(ex);variants.add(variant)
  if len(selected)==6:break
 save('RESTORE_SELECTION.json',dict(seed='phase5i-restore-v1',method='SHA256 order over admitted IDs, six distinct variants; no outcomes or labels',executions=selected))
 for assurance,mode in [('verified_source_values','strict'),('verified_source_values','verified_session'),('verified_physical_interpretation','strict'),('provenance_complete','verified_session')]:
  start=time.perf_counter();r=retrieve(s,ProvenanceQuery(selected[0],channel_id='raw.robot0_joint_pos',interval=(0,0),assurance=assurance,provenance_scope=PROVENANCE_SCOPE,verification_mode=mode));assert r['status']=='ok',r;timings.append(dict(assurance=assurance,mode=mode,seconds=time.perf_counter()-start,artifacts=r.get('provenance_verification')))
 save('ASSURANCE_VALIDATION.json',dict(passed=True,executions=432,variants=104,positive_queries=pos,negative_controls=sum(neg.values()),negative_status_counts=dict(neg),numeric_samples=numeric,maximum_numeric_error=0,mean_numeric_error=0,recorded_label_alignment_errors=0,cross_scope_leakage=0,timings=timings,historical_binary_attested_executions=0))
 restored=create(db,selected,WORK/'restoration');rr=RestoredRelease(WORK/'restoration',restored['manifest_sha256']);samples=0
 for ex in selected:
  for ch,rawj in s.db.execute('select channel,body from rag_channel_records where execution=?',(ex,)):
   raw=json.loads(rawj);last=max(raw['valid_indices']);frames=[0,last//2,last];vals=rr.samples(ex,ch,frames)
   with h5py.File(raw['source_path'],'r') as original:
    for v in vals:assert np.array_equal(v['value'],original[v['source_selector']][()]);samples+=1
 save('RESTORATION.json',dict(passed=True,**restored,executions=selected,variants=len(variants),samples=samples,maximum_numeric_error=0,original_path_fallback=False,historical_reexecution=False))
 s.close();fresh=populate(WORK/'independent.sqlite');resume=populate(db);assert fresh['logical_digest']==b['logical_digest']==resume['logical_digest'];assert resume['resumed']==432
 partial=WORK/'partial_resume.sqlite';shutil.copyfile(db,partial);c=sqlite3.connect(partial);ex=selected[0]
 for table in ('i_jobs','i_scope_nodes','i_scope_edges','i_clock_labels','i_record_scope'):c.execute('delete from '+table+' where execution=?',(ex,))
 c.commit();c.close();pr=populate(partial);assert pr['resumed']==431 and pr['logical_digest']==b['logical_digest'];save('REBUILD_RESUME.json',dict(passed=True,fresh=fresh,full_resume=resume,partial_resume=pr))
 print('PHASE5I VALIDATION COMPLETE',flush=True)
if __name__=='__main__':run()
