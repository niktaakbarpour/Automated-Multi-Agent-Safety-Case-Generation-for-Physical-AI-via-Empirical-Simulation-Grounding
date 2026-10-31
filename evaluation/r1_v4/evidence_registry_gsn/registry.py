"""Immutable SQLite index, byte integrity and dependency validation."""
import hashlib,sqlite3
from pathlib import Path
from .models import Record
from evaluation.r1_v4.provenance import canonical,strict_loads


def source_status(record,cache=None):
 key=(record.source_path,record.source_sha256)
 if cache is not None and key in cache:return cache[key]
 p=Path(record.source_path)
 try:
  with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  result='verified_source' if actual==record.source_sha256 else 'hash_mismatch'
 except (OSError,ValueError):result='missing_source'
 if cache is not None:cache[key]=result
 return result

class Registry:
 def __init__(self,path,create=False):
  self.path=Path(path).resolve()
  if not self.path.is_relative_to('/disk/1/data/niktakbr') or any('issta' in x.lower() for x in self.path.parts):raise ValueError('database outside approved disk1 scope')
  if create:
   if self.path.exists():raise ValueError('refuse overwrite database')
   self.db=sqlite3.connect(self.path)
   self.db.executescript(Path(__file__).with_name('schema.sql').read_text())
  else:self.db=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True)
  if self.db.execute('PRAGMA user_version').fetchone()[0]!=1:raise ValueError('database version')
 def close(self):self.db.close()
 def records(self):
  rows=self.db.execute('SELECT id,body,requirement_id,requirement_version,execution_id,object_id,kind FROM evidence ORDER BY id').fetchall()
  result=[]
  for key,body,*scope in rows:
   r=Record.parse(strict_loads(body))
   if key!=r.id or scope!=[r.requirement_id,r.requirement_version,r.execution_id,r.object_id,r.kind]:raise ValueError('database index/content mismatch')
   result.append(r)
  return result
 def add(self,records):
  records=list(records);existing={r.id:r for r in self.records()}
  cache={}
  for r in records:
   r.validate()
   if r.validation_status in ('verified_measurement','verified_source') and source_status(r,cache)!='verified_source':raise ValueError('verified record source invalid')
   existing[r.id]=r
  issues=dependency_issues(existing)
  if any(issues.values()):raise ValueError('dependency integrity: '+str(issues))
  with self.db:
   for r in records:
    self.db.execute('INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?,?)',(r.id,r.requirement_id,r.requirement_version,r.execution_id,r.object_id,r.kind,canonical(r.export()).decode()))
 def export(self):return {'schema_version':'1.0.0','records':[r.export() for r in self.records()]}
 def integrity(self):
  records={r.id:r for r in self.records()};cache={};deps=dependency_issues(records)
  return {'sqlite':self.db.execute('PRAGMA integrity_check').fetchone()[0],
   'records':{k:{'source':source_status(r,cache),'dependencies':deps[k]} for k,r in records.items()},
   'physical_safety_conclusion':False}


def dependency_issues(records):
 issues={k:[] for k in records}
 def walk(key,stack):
  if key in stack:return ['dependency_cycle']
  r=records[key];out=[]
  for other_id,other in records.items():
   if stack and (other_id in r.conflicts or key in other.conflicts):out.append('dependency_conflict:'+other_id)
  for d in r.dependencies:
   if d not in records:out.append('missing_dependency:'+d);continue
   other=records[d]
   if (r.requirement_id,r.requirement_version,r.execution_id,r.object_id)!=(other.requirement_id,other.requirement_version,other.execution_id,other.object_id):out.append('dependency_scope:'+d)
   if other.kind!='document' and (r.clock!=other.clock or r.domain!=other.domain):out.append('dependency_clock:'+d)
   if other.validation_status in ('missing','invalid','unsupported'):out.append('invalid_dependency:'+d)
   if d in r.conflicts or key in other.conflicts:out.append('conflicting_dependency:'+d)
   out+=walk(d,stack+(key,))
  return sorted(set(out))
 for key in records:issues[key]=walk(key,())
 return issues
