"""Pre-final reference correction; wording/criteria and production code stay fixed."""
import json,shutil,sqlite3,collections
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
from .dataset import CH,FIELD,UNITS

def run():
 assert not (WORK/'final_v1_SUMMARY.json').exists();assert not (WORK/'final_v1').exists()
 old=HERE/'EVALUATION_DATASET.jsonl';assert sha(old)=='b2ae9bf9a18b0a08d0a09ed01ee902ba3248d68af64333f5fc58aac5229b3d72'
 archive=WORK/'reference_v1';archive.mkdir()
 for n in ('EVALUATION_DATASET.jsonl','DATASET_FREEZE.json','EVALUATION_SELECTION.json'):shutil.copyfile(HERE/n,archive/n)
 cases=[json.loads(x) for x in old.read_text().splitlines()];c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);changes=[]
 def samples(q,channels,frames):
  out=[];p=q['reference_artifacts'][0]
  with h5py.File(p['path'],'r') as f:
   for ch in channels:
    k=CH.index(ch)
    for frame in frames:
     sel=f'/frames/{frame:06d}/'+FIELD[k];d=f[sel];out.append(dict(channel=ch,frame=frame,selector=sel,dtype=str(d.dtype),shape=list(d.shape),value=np.asarray(d[()]).tolist(),units=UNITS[k],source_sha256=p['sha256']))
  return out
 for q in cases:
  before=json.dumps(q,sort_keys=True);j=int(q['id'].split('-')[1]);cat=q['category'];ex=q['execution_id']
  if cat=='C7' and j in (1,2):
   channels=[CH[2] if j==1 else CH[0]];q['channels']=channels;q['exact_channel']=channels[0];q['required_facets']=channels+(['source_hash'] if j==1 else []);q['expected_source_ids']=[c.execute('select id from rag_channel_records where execution=? and channel=?',(ex,channels[0])).fetchone()[0]];q['reference_samples']=samples(q,channels,q['temporal_reference']['saved_indices'])
  if (cat=='C7' and j in (4,10,12,17,19,21)) or (cat=='C9' and j==17):
   q['channels']=[];q['exact_channel']=None;q['required_facets']=['source_hash']+(['provenance_report'] if cat=='C7' and j in (4,17) else []);q['expected_source_ids']=[r[0] for r in c.execute('select id from rag_channel_records where execution=? order by id',(ex,))];q['reference_samples']=[]
  if cat=='C7' and j in (6,20):
   q['endpoint']='legacy';q['channels']=[];q['exact_channel']=None;q['request']={k:v for k,v in q['request'].items() if k in ('execution_id','task_id','variant_id','interval','limit')};q['request']['evidence_types']=['execution_metadata'];q['reference_samples']=[];q['expected_source_ids']=[r[0] for r in c.execute("select id from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(ex,))];q['expected_assurance_status']='legacy_source_hash';q['expected_status']='CONDITIONALLY_SUFFICIENT';q['known_ambiguity']='A verified document reference supports the declaration after explicit metadata-field inspection; target does not generate the answer.'
  if cat=='C6' and j==16:
   frames=[0,q['recording_frames']-1];q['request']['interval']=frames;q['temporal_reference']['saved_indices']=frames;q['reference_samples']=samples(q,q['channels'],frames)
  if cat=='C8' and j==8:q['expected_source_ids']=[];q['reference_samples']=[];q['channels']=[];q['required_facets']=['exact_temporal_scope']
  if json.dumps(q,sort_keys=True)!=before:changes.append(dict(case_id=q['id'],reason='Source/contract review corrected specificity, document endpoint, endpoint-frame scope or ambiguous relevance; not based on final outputs'))
 assert all(a['natural_language_query']==b['natural_language_query'] for a,b in zip(cases,[json.loads(x) for x in old.read_text().splitlines()]))
 tmp=HERE/'DATASET.v2.tmp';tmp.write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in cases));tmp.replace(old);old.chmod(0o444)
 freeze=json.loads((archive/'DATASET_FREEZE.json').read_text());freeze.update(version='readiness-questions-v2',dataset_sha256=sha(old),prior_version_sha256=sha(archive/'EVALUATION_DATASET.jsonl'),reference_revision_log=str(WORK/'REFERENCE_REVISIONS.json'),final_target_queries_run=0,independent_reference_sample_checks=sum(len(q['reference_samples']) for q in cases));tmp=HERE/'FREEZE.v2.tmp';tmp.write_text(json.dumps(freeze,sort_keys=True,indent=2));tmp.replace(HERE/'DATASET_FREEZE.json');(HERE/'DATASET_FREEZE.json').chmod(0o444)
 (WORK/'REFERENCE_REVISIONS.json').write_text(json.dumps(dict(before_final_target_run=True,question_texts_unchanged=True,criteria_sha256=sha(HERE/'ACCEPTANCE_CRITERIA.json'),prior_development_run_preserved='dev_v1',changes=changes),sort_keys=True,indent=2));print('REFERENCES V2',len(changes),sha(old),flush=True)
if __name__=='__main__':run()
