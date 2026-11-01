"""Compatible persistent index extension; no new evidence schema."""
import sqlite3
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.registry import Registry,source_status,dependency_issues
from evaluation.r1_v4.evidence_registry_gsn.models import Record
from evaluation.r1_v4.provenance import canonical,strict_loads,digest
HERE=Path(__file__).resolve().parent

class Store(Registry):
 def __init__(self,path,create=False,writable=False):
  super().__init__(path,create=create)
  if writable and not create:
   self.db.close();self.db=sqlite3.connect(self.path)
  self.db.execute('PRAGMA foreign_keys=ON')
  self.db.execute('PRAGMA busy_timeout=5000')
  exists=self.db.execute("SELECT 1 FROM sqlite_master WHERE name='rag_migrations'").fetchone()
  if not exists:
   if not (create or writable):raise ValueError('extension migration required')
   # Transactional additive migration; original evidence table and IDs untouched.
   self.db.executescript('BEGIN IMMEDIATE;\n'+(HERE/'migration.sql').read_text()+'\nCOMMIT;')
  versions=self.db.execute('SELECT version FROM rag_migrations ORDER BY version').fetchall()
  if versions==[('1.0.0',)] and (create or writable):
   self.db.executescript('BEGIN IMMEDIATE;\n'+(HERE/'catalog_migration.sql').read_text()+'\nCOMMIT;')
   versions=self.db.execute('SELECT version FROM rag_migrations ORDER BY version').fetchall()
  if versions!=[('1.0.0',),('1.1.0',)]:raise ValueError('unsupported RAG schema; explicit migration required')
 def put_execution(self,execution,input_digest,units,*,stratum='development',independent=False):
  if stratum not in ('development','corpus_expansion'):raise ValueError('unapproved indexing stratum')
  units=list(units)
  if any(r.execution_id!=execution for r,_,_ in units):raise ValueError('execution/job identity mismatch')
  if independent:
   if self.db.execute('SELECT 1 FROM evidence WHERE execution_id=? LIMIT 1',(execution,)).fetchone():raise ValueError('independent append requires new execution')
   ids={r.id for r,_,_ in units}
   if any(set(tuple(r.dependencies)+tuple(r.conflicts))-ids for r,_,_ in units):raise ValueError('independent append requires closed dependency/conflict scope')
   for body, in self.db.execute("SELECT body FROM evidence WHERE json_array_length(body,'$.conflicts')>0"):
    if set(Record.parse(strict_loads(body)).conflicts)&ids:raise ValueError('incoming conflict')
   existing={}
  else:existing={r.id:r for r in self.records()}
  cache={}
  for record,text,parent in units:
   record.validate()
   if stratum=='corpus_expansion' and record.provenance.get('development_only') is not False:raise ValueError('corpus sources must not be relabeled calibration development')
   if source_status(record,cache)!='verified_source':raise ValueError('source hash mismatch/missing')
   if not text.strip() or len(text)>16000:raise ValueError('bounded descriptive text required')
   existing[record.id]=record
  issues=dependency_issues(existing)
  if any(issues.values()):raise ValueError('dependency integrity')
  with self.db:
   for r,text,parent in units:
    self.db.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?,?,?)',(r.id,r.requirement_id,r.requirement_version,r.execution_id,r.object_id,r.kind,canonical(r.export()).decode()))
    values=(r.id,r.task_id,r.measurement_type,*r.interval,text,parent,stratum)
    old=self.db.execute('SELECT * FROM rag_units WHERE id=?',(r.id,)).fetchone()
    if old and tuple(old)!=values:raise ValueError('immutable unit differs')
    if not old:
     self.db.execute('INSERT INTO rag_units VALUES(?,?,?,?,?,?,?,?)',values)
     self.db.execute('INSERT INTO rag_fts(id,text) VALUES(?,?)',(r.id,text))
   self.db.execute('INSERT OR REPLACE INTO rag_jobs VALUES(?,?,?,?)',(execution,input_digest,'complete',len(units)))
 def finished(self,execution,input_digest):
  return self.db.execute('SELECT 1 FROM rag_jobs WHERE execution=? AND input_digest=? AND status=?',(execution,input_digest,'complete')).fetchone() is not None
 def snapshot(self):
  # Logical build identity excludes timings, failures and physical SQLite layout.
  records=self.export();units=self.db.execute('SELECT * FROM rag_units ORDER BY id').fetchall()
  manifest={'schema_version':'1.0.0','policy_version':'1.0.0','records':len(records['records']),'record_digest':digest(records),'unit_digest':digest(units),'extension_version':'1.1.0','catalog_digest':digest(self.db.execute('SELECT * FROM rag_catalog ORDER BY execution').fetchall()),'catalog_count':self.db.execute('SELECT count(*) FROM rag_catalog').fetchone()[0],'executions':[dict(zip(('execution','input_digest','status','records'),r)) for r in self.db.execute('SELECT * FROM rag_jobs ORDER BY execution')],'empirical_admission_enabled':False}
  key='build:'+digest(manifest)
  with self.db:self.db.execute('INSERT OR IGNORE INTO rag_builds VALUES(?,?)',(key,canonical(manifest).decode()))
  return {'build_id':key,**manifest}
 def check(self):
  base=self.integrity();count=self.db.execute('SELECT count(*) FROM rag_units').fetchone()[0]
  fts=self.db.execute('SELECT id,text FROM rag_fts ORDER BY id').fetchall();units=self.db.execute('SELECT id,text FROM rag_units ORDER BY id').fetchall()
  catalog=self.db.execute('SELECT execution,body FROM rag_catalog ORDER BY execution').fetchall()
  catalog_fts=self.db.execute('SELECT execution,text FROM rag_catalog_fts ORDER BY execution').fetchall()
  catalog_expected=[];catalog_cache={}
  for execution,body in catalog:
   item=strict_loads(body);catalog_expected.append((execution,item['task_instruction']['text']))
   from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
   if item['catalog_source']!=str(REPO/'data/runs.json'):raise ValueError('unapproved catalog source')
   key=(item['catalog_source'],item['catalog_source_sha256'])
   if key not in catalog_cache:
    if sha(key[0])!=key[1]:raise ValueError('catalog source integrity')
    catalog_cache[key]=True
  problems=[k for k,v in base['records'].items() if v['source']!='verified_source' or v['dependencies']]
  return {'schema_version':'1.0.0','passed':base['sqlite']=='ok' and not problems and fts==units and catalog_fts==catalog_expected and not self.db.execute('PRAGMA foreign_key_check').fetchall(),'records':len(base['records']),'units':count,'catalog_records':len(catalog),'source_problems':problems,'fts_matches':fts==units,'physical_safety_conclusion':False}
