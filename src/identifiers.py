"""Shared identities. Existing task/run IDs remain unchanged; safety identifiers are reserved only."""
import json,fcntl
from pathlib import Path
KINDS={'task':'task_id','requirement':'requirement_id','case':'case_id','claim':'claim_id','run':'run_id','event':'event_id','objection':'objection_id'}
class Registry:
 def __init__(self,project):self.project=Path(project);self.path=self.project/'data/identifier_registry.json';self.lock=self.project/'data/identifier_registry.lock'
 def require(self,kind,value):
  db=json.loads(self.path.read_text())
  if value not in db['records'][kind]:raise ValueError(f'Unknown {KINDS[kind]}: {value}')
  return db['records'][kind][value]
 def register_many(self,entries):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.lock.open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);db=json.loads(self.path.read_text()) if self.path.exists() else {'schema_version':'1.0.0','records':{k:{} for k in KINDS}};owners={v:k for k,items in db['records'].items() for v in items}
   for kind,value,record in entries:
    if kind not in ["task","run"] or not isinstance(value,str) or not value:raise ValueError("Only existing task/run identifiers may be registered at this stage")
    if value in owners and (owners[value]!=kind or db['records'][kind][value]!=record):raise ValueError('Conflicting source identifier '+value)
    owners[value]=kind;db['records'][kind][value]=record
   tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(db,indent=2));tmp.replace(self.path)

def step_id(step):
 if not isinstance(step,int) or isinstance(step,bool) or step<0:raise ValueError('step_id must be a nonnegative recorded control-step index')
 return step