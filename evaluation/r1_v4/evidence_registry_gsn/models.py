"""Closed metadata schema; payloads remain in the source V4 contracts."""
from dataclasses import dataclass, field, asdict
import math,re
from pathlib import Path
from evaluation.r1_v4.provenance import digest,canonical

CAPABILITIES={'VERIFIED','CONDITIONALLY_SUPPORTED','BLOCKED_ON_EVIDENCE','UNSUPPORTED'}
KINDS={'raw_measurement','derived_measurement','ai_reference_judgment','human_reference_judgment','checker_assessment','document'}
VALIDATION={'verified_measurement','verified_source','provisional','invalid','missing','unsupported'}


def interval(value):
 if not isinstance(value,(list,tuple)) or len(value)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in value) or value[0]>value[1]:
  raise ValueError('invalid interval')
 return tuple(value)

@dataclass(frozen=True)
class Record:
 schema_version:str
 requirement_id:str
 requirement_version:str
 execution_id:str
 object_id:str
 kind:str
 source_path:str
 source_sha256:str
 selector:str
 measurement_type:str
 validation_status:str
 capability:dict
 clock:str
 domain:str
 interval:tuple
 coordinate_frame:str
 model_checkpoint:str
 benchmark:str
 task_id:str
 producer:str
 original:bool
 dependencies:tuple=()
 missing_intervals:tuple=()
 uncertainty:tuple=()
 limitations:tuple=()
 conflicts:tuple=()
 provenance:dict=field(default_factory=dict)

 def validate(self):
  if self.schema_version!='1.0.0' or self.requirement_version!='2.0.0' or self.requirement_id!='R1':raise ValueError('unsupported record/requirement version')
  if self.kind not in KINDS or self.validation_status not in VALIDATION:raise ValueError('record kind/status')
  for key in ('execution_id','object_id','selector','measurement_type','clock','coordinate_frame','model_checkpoint','benchmark','task_id','producer'):
   if not isinstance(getattr(self,key),str) or not getattr(self,key):raise ValueError('missing '+key)
  if self.domain not in ('frame','time'):raise ValueError('domain')
  if not isinstance(self.original,bool) or (self.original and self.kind not in ('raw_measurement','document')):raise ValueError('provenance origin')
  source=Path(self.source_path)
  if not source.is_relative_to('/disk/1/data/niktakbr') or '..' in source.parts or any('issta' in part.lower() for part in source.parts):raise ValueError('source outside approved research scope')
  if any(p.is_symlink() for p in (source,*source.parents)):raise ValueError('symlink source unsupported')
  if not self.source_path.startswith('/') or not re.fullmatch('[0-9a-f]{64}',self.source_sha256):raise ValueError('source binding')
  interval(self.interval)
  if self.domain=='frame' and any(type(x)!=int or x<0 for x in self.interval):raise ValueError('frame index')
  for gap in self.missing_intervals:
   a,b=interval(gap)
   if a<self.interval[0] or b>self.interval[1]:raise ValueError('gap outside scope')
  for seq in (self.dependencies,self.conflicts,self.uncertainty,self.limitations):
   if any(not isinstance(x,str) or not x for x in seq) or len(set(seq))!=len(seq):raise ValueError('invalid/duplicate list')
  if not self.capability or any(not isinstance(k,str) or not k or v not in CAPABILITIES for k,v in self.capability.items()):raise ValueError('capability')
  if self.validation_status=='verified_measurement' and self.kind not in ('raw_measurement','derived_measurement'):raise ValueError('judgment is not measurement')
  if self.kind in ('raw_measurement','derived_measurement') and self.measurement_type not in ('object_pose','native_geometry','contact','camera_reference','robot_state','timestamp','recorded_state'):
   raise ValueError('physical events are not measurement types')
  if self.provenance.get('physical_truth') not in (None,'U'):raise ValueError('unsupported physical truth')
  canonical(asdict(self))
  return self

 @property
 def id(self):return 'ev:'+digest(asdict(self))

 def export(self):return {'id':self.id,**asdict(self)}

 @classmethod
 def parse(cls,value):
  value=dict(value);expected=value.pop('id',None)
  obj=cls(**value).validate()
  if expected is not None and expected!=obj.id:raise ValueError('record content hash mismatch')
  return obj
