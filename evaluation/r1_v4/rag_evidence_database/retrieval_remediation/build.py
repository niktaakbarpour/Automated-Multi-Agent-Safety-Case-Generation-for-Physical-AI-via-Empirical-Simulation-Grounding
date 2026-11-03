"""Small additive retrieval catalogue: existing artifacts/IDs, never measurement arrays."""
import json,sqlite3,hashlib,subprocess,time
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import digest,canonical
from .config import *
from .store import BundleStore

def enc(x):return canonical(x).decode()
def producer():return {n:sha(HERE/n) for n in ('build.py','config.py','store.py')}
def artifact_rows(value):
 if isinstance(value,dict):
  if value.get('path') and value.get('sha256'):yield value
  for v in value.values():yield from artifact_rows(v)
 elif isinstance(value,list):
  for v in value:yield from artifact_rows(v)
def populate(path):
 start=time.perf_counter();s=BundleStore();inputs=json.loads(dict(s.db.execute('select * from i_meta'))['inputs']);ip=DATABASE.parent/'PRODUCER_EVIDENCE.json';inventory,_=s.read_json(str(ip),inputs['PRODUCER_EVIDENCE.json'],'strict');inv={r['execution_id']:r for r in inventory['rows']}
 gm=HERE.parent/'measurement_channel_expansion/ARTIFACT_MANIFEST.json';git_bytes=subprocess.check_output(['git','show',BASE_COMMIT+':'+str(gm.relative_to(REPO))]);g,_=s.read_json(str(gm),hashlib.sha256(git_bytes).hexdigest(),'strict');ar=[r for r in artifact_rows(g) if Path(r['path']).name=='MAIN_TABLE_AUDIT.json'];assert len(ar)==1;alias,a=s.read_json(ar[0]['path'],ar[0]['sha256'],'strict');aliases={r['execution_id']:r for r in alias['rows']}
 meta=dict(version=VERSION,database_sha256=DATABASE_SHA,producer=enc(producer()),producer_inventory_sha256=inputs['PRODUCER_EVIDENCE.json'],alias_audit_path=ar[0]['path'],alias_audit_sha256=ar[0]['sha256'])
 c=sqlite3.connect(path)
 if not c.execute("select 1 from sqlite_master where name='meta'").fetchone():
  c.executescript('create table meta(key text primary key,value text);create table catalogue(execution text primary key,body text not null);create table jobs(execution text primary key,input_digest text,row_digest text);');c.executemany('insert into meta values(?,?)',meta.items());c.commit()
 assert dict(c.execute('select * from meta'))==meta,'sidecar requires separate rebuild after producer/input change';resumed=0
 for ex,body in s.db.execute('select execution,body from rag_execution_env order by execution').fetchall():
  b=json.loads(body);p=inv[ex];h=json.loads(s.db.execute('select body from h_execution where execution=?',(ex,)).fetchone()[0]);inp=digest([meta,p,b]);old=c.execute('select input_digest,row_digest from jobs where execution=?',(ex,)).fetchone()
  if old:
   saved=c.execute('select body from catalogue where execution=?',(ex,)).fetchone();assert saved and old==(inp,digest(json.loads(saved[0])));resumed+=1;continue
  files=p['original_manifest_inventory'];directory=Path(p['metadata_path']).parent;scene_path=directory/'semantic_initial_conditions.json';scene,att=s.read_json(str(scene_path),files['semantic_initial_conditions.json']['sha256']);ph=next(iter(scene.get('phases',{'legacy':scene}).values()));objs=ph.get('object_initial_poses',ph.get('objects',{}));objects={k:(b['objects'][k]|dict(root_body=v['root_body'],category=v.get('category_name'))) for k,v in objs.items() if k in b['objects']};assert len(objects)==len(b['objects'])
  record=dict(execution_id=ex,task_id=b['task_id'],variant_id=b['variant_id'],suite=b['suite'],frames=len(h['temporal_rows']),source_path=h['source_path'],source_sha256=h['source_sha256'],metadata_path=p['metadata_path'],metadata_sha256=p['metadata_sha256'],scene_path=str(scene_path),scene_sha256=files['semantic_initial_conditions.json']['sha256'],objects=objects,main_table=aliases[ex],catalogue_kind='retrieval references only; no new measurement series',original_channel_ids={ch:rid for rid,ch in s.db.execute('select id,channel from rag_channel_records where execution=?',(ex,))},metadata_anchor='h_execution:'+ex)
  with c:c.execute('insert into catalogue values(?,?)',(ex,enc(record)));c.execute('insert into jobs values(?,?,?)',(ex,inp,digest(record)))
 result=dict(path=str(path),sha256=sha(Path(path)),bytes=Path(path).stat().st_size,logical_digest=digest({t:c.execute('select * from '+t+' order by 1').fetchall() for t in ('meta','catalogue','jobs')}),executions=c.execute('select count(*) from jobs').fetchone()[0],resumed=resumed,seconds=time.perf_counter()-start);c.close();s.close();return result
if __name__=='__main__':
 r=populate(WORK/'catalogue.sqlite');(WORK/'BUILD.json').write_text(json.dumps(r,sort_keys=True,indent=2));print(r,flush=True)
