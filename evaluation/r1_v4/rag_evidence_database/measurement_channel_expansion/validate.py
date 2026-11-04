"""Independent h5py oracle, numeric/temporal retrieval and exact preservation."""
import sqlite3,json,time,hashlib,collections
from pathlib import Path
from dataclasses import replace
import h5py,numpy as np
from evaluation.r1_v4.provenance import canonical,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .channels import WORK,BASE,BASE_SHA,HERE,CHANNELS,ChannelStore,require_hestia
from .retrieve import ChannelQuery,retrieve
# Independent field/shape declarations; do not reuse extraction decoder.
ORACLE={
 'raw.robot0_gripper_qpos':('raw_observation/robot0_gripper_qpos/value',(2,)),
 'raw.robot0_gripper_qvel':('raw_observation/robot0_gripper_qvel/value',(2,)),
 'raw.robot0_joint_pos':('raw_observation/robot0_joint_pos/value',(7,)),
 'raw.robot0_joint_vel':('raw_observation/robot0_joint_vel/value',(7,)),
 'raw.simulator_actuator_force':('simulator/actuator_force/value',(9,)),
 'simulator.ncon':('simulator/ncon/value',()),
}
def save(name,value):
 with (WORK/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2)
def preserve(database):
 a=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(Path(database).as_uri()+'?mode=ro',uri=True);checks={}
 for name,sql in a.execute("select name,sql from sqlite_master where type='table' and sql is not null order by name"):
  assert b.execute('select sql from sqlite_master where name=?',(name,)).fetchone()==(sql,),name
  h1=hashlib.sha256();h2=hashlib.sha256();count=0
  cols=len(a.execute('select * from "'+name+'" limit 0').description);q='select * from "'+name+'" order by '+','.join(str(i+1) for i in range(cols))
  def pack(row):return canonical([{'blob_hex':x.hex()} if isinstance(x,bytes) else x for x in row])
  import itertools
  for x,y in itertools.zip_longest(a.execute(q),b.execute(q)):
   assert x==y,(name,count);h1.update(pack(x));h2.update(pack(y));count+=1
  checks[name]=dict(rows=count,sha256=h1.hexdigest(),identical=h1.digest()==h2.digest())
 assert sha(BASE)==BASE_SHA
 a.close();b.close();return dict(passed=True,tables=checks,preserved_evidence_records=checks['evidence']['rows'],baseline_database_sha256=BASE_SHA)
def run(database):
 require_hestia();start=time.perf_counter();db=ChannelStore(database);rows=[];negative=collections.Counter();numeric=collections.Counter();maxerror=0.;sample_total=0;returned_samples=0;scopes={}
 allrows=db.db.execute('select execution,channel,body from rag_channel_records order by execution,channel').fetchall();by=collections.defaultdict(list)
 for execution,channel,body in allrows:by[execution].append(json.loads(body))
 assert len(by)==432 and len(allrows)==2592
 def reject(q,expected):
  r=retrieve(db,q);assert r['status']==expected and not r['results'] and not r['matching_count'],(q,r['status'],expected);negative[expected]+=1
 for e,records in by.items():
  binding=db.binding(e);p=records[0]['source_path'];db.verify_file(p,records[0]['source_sha256']);scopes[e]=binding['variant_id']
  with h5py.File(p,'r') as f:
   keys={int(k):k for k in f['frames']};ids=sorted(keys);points=sorted(set((ids[0],ids[len(ids)//2],ids[-1])));windows=[(p,p) for p in points]
   if 31 in keys and 32 in keys:windows.append((31,32))
   for r in records:
    channel=r['channel_id'];field,shape=ORACLE[channel];hasher=hashlib.sha256();valid=[];invalid={}
    for frame,key in sorted(keys.items()):
     selector='/frames/'+key+'/'+field
     if selector not in f:invalid[str(frame)]='missing_dataset';continue
     a=np.asarray(f[selector][()]);assert a.shape==shape and a.dtype.kind in 'fiu' and np.isfinite(a).all(),(e,selector)
     if channel=='simulator.ncon':
      assert a.dtype.kind in 'iu' and int(a)>=0
      contact=f['frames/'+key+'/simulator/contacts']
      if 'json' in contact.attrs:length=len(json.loads(contact.attrs['json']))
      elif 'value' in contact:length=len(contact['value'])
      else:raise ValueError('unrecognized contact representation')
      assert int(a)==length;numeric['contact_length_comparisons']+=1
     valid.append(frame);hasher.update(canonical({'frame':frame,'selector':selector,'dtype':str(a.dtype),'shape':list(a.shape)}));hasher.update(a.tobytes());sample_total+=1;numeric[channel]+=a.size
    assert valid==r['valid_indices'] and invalid==r['invalid_samples'] and hasher.hexdigest()==r['sample_digest'],(e,channel)
    q=ChannelQuery(execution_id=e,task_id=binding['task_id'],variant_id=binding['variant_id'],channel_id=channel,object_id=r['object_id'])
    for lo,hi in windows:
     result=retrieve(db,replace(q,interval=(lo,hi)));assert result['status']=='ok' and result['matching_count']==1 and result['results'][0]['id']==r['id']
     actual=result['results'][0];expected_ids=[i for i in ids if lo<=i<=hi];assert [s['saved_frame_index'] for s in actual['samples']]==expected_ids
     for s in actual['samples']:
      key=keys[s['saved_frame_index']];oracle=f['frames/'+key+'/'+field][()];assert np.array_equal(np.asarray(s['value']),oracle);error=float(np.max(np.abs(np.asarray(s['value'])-oracle))) if np.size(oracle) else 0.;maxerror=max(maxerror,error)
      attrs=f['frames/'+key].attrs;assert s['control_step']==(int(attrs['control_step']) if 'control_step' in attrs else None);assert s['stage']==(str(attrs['stage']) if 'stage' in attrs else None);assert s['units']==r['contract']['units'] and s['coordinate_frame']==r['contract']['coordinate_frame'];returned_samples+=1
     rows.append(dict(execution=e,variant=binding['variant_id'],channel=channel,interval=[lo,hi],target_id=r['id'],precision_at_1=1.,recall_at_20=1.,MRR=1.))
    reject(replace(q,object_id='wrong-object'),'no_matching_channel_record');reject(replace(q,interval=(ids[-1]+1,ids[-1]+1)),'no_matching_channel_record');reject(replace(q,task_id='wrong-task'),'invalid_query_scope');reject(replace(q,variant_id='wrong-variant'),'invalid_query_scope');reject(replace(q,execution_id='unknown:'+e),'unknown_execution');reject(replace(q,units='N'),'unsupported_units');reject(replace(q,coordinate_frame='MuJoCo_world'),'unsupported_coordinate_frame');reject(replace(q,origin='derived'),'unsupported_origin');reject(replace(q,temporal_domain='seconds'),'unsupported_temporal_domain');reject(replace(q,channel_id='logical_main_table_pose'),'unsupported_channel')
  if len(scopes)%25==0:print('Independent numeric/retrieval executions',len(scopes),flush=True)
 for status in ('excluded_reserved','excluded_preflight','unindexed_profile_pending'):
  ids=[r[0] for r in db.db.execute('select execution from rag_scope_status where status=?',(status,))]
  for e in ids:reject(ChannelQuery(e,channel_id='simulator.ncon'),status)
 assert db.db.execute('select count(*) from rag_channel_fts').fetchone()[0]==len(allrows)
 assert not db.db.execute('pragma foreign_key_check').fetchall() and db.db.execute('pragma integrity_check').fetchall()==[('ok',)]
 report=dict(passed=True,executions=len(by),variants=len(set(scopes.values())),channel_records=len(allrows),raw_source_samples_validated=sample_total,numeric_components_by_channel=dict(numeric),retrieved_samples_compared=returned_samples,max_absolute_value_error=maxerror,alignment_errors_saved_indices=0,unit_frame_inconsistencies=0,missing_samples=sum(len(json.loads(b)['invalid_samples']) for _,_,b in allrows),source_target_queries=len(rows),precision_at_1=1.,recall_at_20=1.,MRR=1.,negative_controls=sum(negative.values()),negative_status_counts=dict(negative),cross_scope_leakage=0,seconds=time.perf_counter()-start,qualification='Exact channel lookup metrics measure source retrieval only. Numeric comparisons use independently decoded arrays. Zero saved-index alignment error does not establish physical phase alignment.',query_results=rows)
 save('EXTRACTION_RETRIEVAL_VALIDATION.json',report);save('PRESERVATION_VALIDATION.json',preserve(database));db.close();print({k:v for k,v in report.items() if k!='query_results'},flush=True);return report
if __name__=='__main__':run(WORK/'expanded.sqlite')
