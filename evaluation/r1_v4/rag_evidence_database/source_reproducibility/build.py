"""Additive deterministic lineage graph; original tables are never rewritten."""
import json,sqlite3,shutil,time
from pathlib import Path
from evaluation.r1_v4.provenance import canonical,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import HERE,WORK,BASE,BASE_SHA,VERSION
from .model import claim,SCOPE_DEFINITION

def enc(x):return canonical(x).decode()
def inputs():return {n:sha(WORK/n) for n in ('PRODUCER_EVIDENCE.json','CLOCK_AUDIT.json','DEPENDENCIES_retrieval.json','DEPENDENCIES_native.json')}
def producers():return {n:sha(HERE/n) for n in ('config.py','build.py','model.py','store.py','retrieve.py','restore.py')}|{'schema.sql':sha(HERE/'schema.sql')}
def snapshot(c):
 return digest({t[0]:c.execute('select * from '+t[0]+' order by '+','.join(str(i+1) for i in range(len(c.execute('pragma table_info('+t[0]+')').fetchall())))).fetchall() for t in c.execute("select name from sqlite_master where type='table' and name like 'i_%' order by name").fetchall()})
def scope_digest(c,ex):return digest([c.execute('select node from i_scope_nodes where execution=? order by node',(ex,)).fetchall(),c.execute('select edge from i_scope_edges where execution=? order by edge',(ex,)).fetchall(),c.execute('select * from i_clock_labels where execution=? order by frame',(ex,)).fetchall(),c.execute('select * from i_record_scope where execution=? order by node',(ex,)).fetchall()])
def populate(path):
 start=time.monotonic();path=Path(path)
 if not path.exists():
  assert sha(BASE)==BASE_SHA;shutil.copyfile(BASE,path)
 c=sqlite3.connect(path);c.execute('pragma foreign_keys=on')
 meta={'version':VERSION,'baseline':BASE_SHA,'inputs':enc(inputs()),'producer':enc(producers()),'scope':enc(SCOPE_DEFINITION)}
 if not c.execute("select 1 from sqlite_master where name='i_meta'").fetchone():
  c.executescript((HERE/'schema.sql').read_text());c.executemany('insert into i_meta values(?,?)',meta.items());c.commit()
 assert dict(c.execute('select * from i_meta'))==meta,'frozen input/producer mismatch'
 def node(kind,body,exe=None,id=None):
  id=id or kind+':'+digest(body);row=(id,kind,enc(body));c.execute('insert or ignore into i_nodes values(?,?,?)',row)
  assert c.execute('select * from i_nodes where id=?',(id,)).fetchone()==row
  if exe:c.execute('insert or ignore into i_scope_nodes values(?,?)',(exe,id))
  return id
 def edge(s,t,relation,basis,exe=None):
  row=(digest([s,t,relation,basis]),s,t,relation,basis);c.execute('insert or ignore into i_edges values(?,?,?,?,?)',row)
  if exe:c.execute('insert or ignore into i_scope_edges values(?,?)',(exe,row[0]))
 def artifact(p,h,exe=None):
  id=node('artifact',dict(path=str(p),sha256=h),exe);c.execute('insert or ignore into i_artifacts values(?,?,?,?,?)',(id,str(p),h,None,'HASH_DECLARED_REQUIRES_ACCESS_VERIFICATION'));return id
 def paths(value,parent,exe):
  if isinstance(value,dict):
   if value.get('path') and value.get('sha256'):
    edge(parent,artifact(value['path'],value['sha256'],exe),'artifact_reference','verbatim preserved hash binding',exe)
    if str(value['path']).endswith('/PRIMARY_SOURCES.json'):
     from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
     with SourceVerifier().access(value['path'],value['sha256'],'strict') as (f,a):proof=json.load(f)
     paths(proof,parent,exe)
   if value.get('source_path') and value.get('source_sha256'):edge(parent,artifact(value['source_path'],value['source_sha256'],exe),'source','verbatim preserved source binding',exe)
   for k,v in value.items():
    if k.endswith('_path') and isinstance(v,str) and value.get(k[:-5]+'_sha256'):edge(parent,artifact(v,value[k[:-5]+'_sha256'],exe),'artifact_reference','verbatim preserved hash binding',exe)
    if isinstance(v,(dict,list)):paths(v,parent,exe)
  elif isinstance(value,list):
   for v in value:paths(v,parent,exe)
 deps=[]
 for name in ('retrieval','native'):
  d=json.loads((WORK/f'DEPENDENCIES_{name}.json').read_text());dn=node('current_environment',dict(environment=name,classification='RETROSPECTIVE_ARTIFACT',historical_attestation='NOT_ATTESTED'))
  for a in d['artifacts']:
   an=artifact(a['path'],a['sha256']);edge(dn,an,'current_artifact','current dependency scan; not historical execution identity')
  deps.append(dn)
 clocks=json.loads((WORK/'CLOCK_AUDIT.json').read_text());clockrows={r['execution_id']:r for r in clocks['rows']}
 for k,v in clocks['definitions'].items():c.execute('insert or ignore into i_clock_domains values(?,?)',(k,enc(v)))
 c.commit()
 rows=json.loads((WORK/'PRODUCER_EVIDENCE.json').read_text())['rows'];resumed=0
 for p in rows:
  ex=p['execution_id'];inp=digest([meta,p,clockrows[ex]])
  existing=c.execute('select input_digest,scope_digest from i_jobs where execution=?',(ex,)).fetchone()
  if existing:
   assert existing==(inp,scope_digest(c,ex));resumed+=1;continue
  with c:
   en=node('execution',dict(execution_id=ex,task_id=p['task_id'],variant_id=p['variant_id']),ex)
   vb=json.loads(c.execute('select body from rag_env_variants where id=?',(p['variant_id'],)).fetchone()[0]);vn=node('variant',vb,ex,id='variant:'+p['variant_id']);edge(en,vn,'variant','preserved verified execution binding',ex)
   paths(json.loads(c.execute('select body from rag_execution_env where execution=?',(ex,)).fetchone()[0]),en,ex)
   for a in vb.get('assets',[]):edge(vn,artifact(a['path'],a['sha256'],ex),'geometry_asset','verified variant asset manifest',ex)
   for family,table,col in [('evidence','evidence','execution_id'),('channel','rag_channel_records','execution'),('interpretation','h_semantics','execution')]:
    for r in c.execute('select * from '+table+' where '+col+'=?',(ex,)).fetchall():
     body=json.loads(r[-1]);rid=r[0];rn=node(family,dict(record_id=rid),ex,id=family+':'+rid);c.execute('insert or ignore into i_record_scope values(?,?,?,?)',(rn,ex,rid,family));edge(rn,en,'execution','preserved row execution association',ex);paths(body,rn,ex)
     if body.get('selector') or body.get('source_field'):
      field=node('source_selector',dict(selector=body.get('selector',body.get('source_field')),record_id=rid),ex);edge(rn,field,'field','verbatim preserved selector; no new temporal meaning',ex)
     if body.get('raw_record_id'):
      target=node('channel',dict(record_id=body['raw_record_id']),ex,id='channel:'+body['raw_record_id']);edge(rn,target,'interprets','preserved raw_record_id; values unchanged',ex)
     for dep in body.get('dependencies',[]):
      if isinstance(dep,str):
       target=node('evidence',dict(record_id=dep),ex,id='evidence:'+dep);edge(rn,target,'declared_dependency','verbatim preserved evidence dependencies',ex)
   for prop in ('source_commit_declaration','dependency_version_declarations','python_declaration','hardware_backend_declarations','recording_configuration','checkpoint_hash_declarations'):
    cl=claim(ex,prop,p[prop],'HISTORICAL_RECORD',dict(path=p['metadata_path'],sha256=p['metadata_sha256']),prop,'Content of hash-bound original execution metadata; self-declaration only')
    cn=node('claim',cl,ex,id=cl['id']);c.execute('insert or ignore into i_claims values(?,?,?,?,?,?)',(cl['id'],ex,prop,cl['category'],cl['historical_attestation'],enc(cl)));edge(en,cn,'recorded_declaration','original metadata content does not attest running process',ex)
   for group in ('producer_files','evaluator_files'):
    for f in p[group]:
     ap=f.get('current_owned_path') or f.get('available_matching_path') or f.get('current_path');ah=f.get('recorded_sha256') or f.get('sha256')
     if ap and ah:edge(en,artifact(ap,ah,ex),'retrospective_source_match','available bytes match recorded digest; runtime use unattested',ex)
   edge(en,node('unattested',dict(property='historical_producer_binary',status='UNATTESTED'),ex),'unresolved','No exact running binary/container attestation available',ex)
   for dn in deps:edge(en,dn,'current_validation_environment','retrospective reproducibility prerequisite, not historical producer',ex)
   for s in clockrows[ex]['samples']:c.execute('insert or ignore into i_clock_labels values(?,?,?,?,?,?)',(ex,s['frame'],s['simulator_endpoint_label'],s['recorder_host_wall_ns'],s['recorder_host_monotonic_ns'],s['recorder_utc']))
   for k,v in clocks['definitions'].items():edge(en,node('clock_domain',dict(id=k,definition=v),ex),'clock_audit','direct source labels or explicit unavailable clock; no synchronization inference',ex)
   c.execute('insert into i_jobs values(?,?,?,?)',(ex,inp,scope_digest(c,ex),'complete'))
 assert c.execute('pragma integrity_check').fetchone()[0]=='ok';c.commit()
 result=dict(database=str(path),database_sha256=sha(path),bytes=path.stat().st_size,logical_digest=snapshot(c),executions=len(rows),resumed=resumed,seconds=time.monotonic()-start,counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('i_nodes','i_edges','i_artifacts','i_claims','i_clock_labels')});c.close();return result
if __name__=='__main__':
 r=populate(WORK/'expanded.sqlite');(WORK/'BUILD.json').write_text(json.dumps(r,indent=2));print(r,flush=True)
