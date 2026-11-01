"""Cross-check indexed saved-frame availability with authoritative source counts."""
from collections import defaultdict,Counter
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from .profile import HERE

def check(path,out):
 db=Store(path);records=db.records();db.close();source={r['run_id']:r for r in load(REPO/'data/runs.json')['records']};scopes=defaultdict(list)
 for r in records:
  if r.kind=='raw_measurement':scopes[(r.execution_id,r.object_id,r.measurement_type)].append(r)
 assert len(scopes)==40*5*6
 for (execution,obj,kind),values in scopes.items():
  expected=source[execution]['available_measurements']['root_groups']['frames'];cursor=0
  for r in sorted(values,key=lambda r:r.interval):
   assert r.domain=='frame' and r.clock=='saved_frame_index' and not r.missing_intervals
   assert r.interval[0]==cursor and r.interval[1]>=cursor;cursor=r.interval[1]+1
   assert r.validation_status=='verified_measurement' and r.capability.get('physical_checking')!='VERIFIED'
  assert cursor==expected,(execution,obj,kind,cursor,expected)
 result={'schema_version':'1.0.0','passed':True,'execution_object_type_scopes_validated':len(scopes),'source_frame_counts_match':True,'unique_source_frames':sum(source[e]['available_measurements']['root_groups']['frames'] for e in {r.execution_id for r in records}),'evidence_types':dict(Counter(r.measurement_type for r in records)),'physical_coverage_qualified':False,'scope':'Every saved frame in all five object bindings and all six measurement types; no claim of unsampled continuous observation.'}
 write_new(out/'COVERAGE_VALIDATION.json',result);return result
