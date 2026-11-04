"""Additive normalized environment relations over the existing 1.1 RAG schema."""
from pathlib import Path
from evaluation.r1_v4.provenance import canonical,strict_loads,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.store import Store
from .plan import HERE

class VariantStore(Store):
 def __init__(self,path,create=False,writable=False):
  super().__init__(path,create=create,writable=writable)
  exists=self.db.execute("SELECT 1 FROM sqlite_master WHERE name='rag_variant_schema'").fetchone()
  if not exists:
   if not (writable or create):raise ValueError('variant migration required on a new working copy')
   self.db.executescript("BEGIN IMMEDIATE;\n"+(HERE/'schema.sql').read_text()+"\nINSERT INTO rag_variant_schema VALUES('1.0.0','"+sha(HERE/'schema.sql')+"');\nCOMMIT;")
  if self.db.execute('SELECT * FROM rag_variant_schema').fetchall()!=[('1.0.0',sha(HERE/'schema.sql'))]:raise ValueError('unsupported variant schema/migration hash')
 def register(self,identity,binding):
  validate_mapping(binding)
  core={k:identity[k] for k in ('variant_id','xml_sha256','asset_content_digest','assets','identity_version','equivalence_rule')};variant=(identity['variant_id'],identity['xml_sha256'],identity['asset_content_digest'],canonical(core).decode());scope=(binding['execution_id'],binding['task_id'],binding['suite'],identity['variant_id'],canonical(binding).decode())
  if binding['xml_sha256']!=identity['xml_sha256'] or binding['variant_id']!=identity['variant_id']:raise ValueError('binding identity mismatch')
  with self.db:
   old=self.db.execute('SELECT * FROM rag_env_variants WHERE id=?',(variant[0],)).fetchone()
   if old and tuple(old)!=variant:raise ValueError('variant collision')
   self.db.execute('INSERT OR IGNORE INTO rag_env_variants VALUES(?,?,?,?)',variant)
   old=self.db.execute('SELECT * FROM rag_execution_env WHERE execution=?',(scope[0],)).fetchone()
   if old and tuple(old)!=scope:raise ValueError('execution binding changed')
   self.db.execute('INSERT OR IGNORE INTO rag_execution_env VALUES(?,?,?,?,?)',scope)
 def binding(self,execution):
  row=self.db.execute('SELECT body FROM rag_execution_env WHERE execution=?',(execution,)).fetchone();return strict_loads(row[0]) if row else None
 def set_status(self,execution,status,partition,reason):
  if status not in ('indexed','unindexed_profile_pending','validated_unindexed','excluded_reserved','excluded_preflight','unsupported_mapping','unresolved_variant'):raise ValueError('scope status')
  with self.db:self.db.execute('INSERT OR REPLACE INTO rag_scope_status VALUES(?,?,?,?)',(execution,status,partition,reason))
 def variant_snapshot(self):
  core=super().snapshot();relations={t:self.db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in ('rag_env_variants','rag_execution_env','rag_scope_status','rag_variant_schema')};body={'schema_version':'1.0.0','core_build':core,'relation_digest':digest(relations),'variants':len(relations['rag_env_variants']),'bound_executions':len(relations['rag_execution_env']),'empirical_admission_enabled':False};key='variant-build:'+digest(body)
  with self.db:self.db.execute('INSERT OR IGNORE INTO rag_variant_builds VALUES(?,?)',(key,canonical(body).decode()))
  return {'build_id':key,**body}
 def variant_check(self):
  core=super().check();cache={};issues=[]
  for execution,variant_id,body in self.db.execute('SELECT execution,variant_id,body FROM rag_execution_env'):
   b=strict_loads(body);v=self.db.execute('SELECT xml_sha256,asset_digest FROM rag_env_variants WHERE id=?',(variant_id,)).fetchone()
   if v!=(b['xml_sha256'],b['asset_content_digest']):issues.append(execution+':identity')
   for prefix in ('xml','asset_manifest','mapping'):
    path=b[prefix+'_path'];expected=b[prefix+'_sha256']
    if path not in cache:cache[path]=sha(path)
    if cache[path]!=expected:issues.append(execution+':'+prefix)
  for body, in self.db.execute('SELECT body FROM rag_env_variants'):
   for asset in strict_loads(body)['assets']:
    if asset['path'] not in cache:cache[asset['path']]=sha(asset['path'])
    if cache[asset['path']]!=asset['sha256']:issues.append('asset:'+asset['path'])
  missing=[r[0] for r in self.db.execute('SELECT DISTINCT e.execution_id FROM evidence e LEFT JOIN rag_execution_env b ON e.execution_id=b.execution WHERE b.execution IS NULL')]
  mismatched=[]
  for execution,mapsha,profile in self.db.execute("SELECT DISTINCT execution_id,json_extract(body,'$.provenance.native_map_sha256'),json_extract(body,'$.provenance.reader_binding.profile_sha256') FROM evidence WHERE kind='raw_measurement'"):
   b=self.binding(execution)
   if b and (b['mapping_sha256']!=mapsha or (b.get('profile_sha256') and b['profile_sha256']!=profile)):mismatched.append(execution)
  return {'passed':core['passed'] and not issues and not missing and not mismatched,'core':core,'variant_issues':issues,'missing_execution_bindings':missing,'record_binding_mismatches':sorted(set(mismatched)),'variant_count':self.db.execute('SELECT count(*) FROM rag_env_variants').fetchone()[0],'empirical_admission_enabled':False}

def validate_mapping(binding):
 from evaluation.r1_v4.provenance import load
 p=Path(binding['mapping_path']);assert sha(p)==binding['mapping_sha256'];raw=load(p);m=raw.get('mapping',raw)
 if m['source_xml_sha256']!=binding['xml_sha256'] or binding['execution_id'] not in m['validated_run_ids']:raise ValueError('mapping does not validate exact XML/execution')
 geoms=m['geometries'];count=m['native_geom_count']
 if [g['native_geom_id'] for g in geoms]!=list(range(count)):raise ValueError('incomplete native mapping')
 for obj,identity in binding['objects'].items():
  bid=identity['body_id']
  if m['body_names'][bid]!=obj+'_main' or any(geoms[g]['owner_body_id']!=bid for g in identity['collision_geom_ids']):raise ValueError('object/body/geometry binding mismatch')
 if raw.get('objects') is not None:
  for obj,identity in binding['objects'].items():
   if raw['objects'][obj]['body_id']!=identity['body_id'] or raw['objects'][obj]['collision_geom_ids']!=identity['collision_geom_ids']:raise ValueError('profile object map mismatch')
 return True
