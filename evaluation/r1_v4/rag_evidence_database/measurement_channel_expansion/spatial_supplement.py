"""Audit existing support candidates and recorder bindings without support inference."""
import json,sqlite3,collections,csv
from .channels import WORK,BASE,HERE
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO

def run():
 c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);rows=[];recorders=collections.Counter();geofields=collections.defaultdict(lambda:dict(executions=set(),types=collections.Counter(),example=None))
 recorder=REPO/'reports/fall_review_v2_20261016/source_evidence/recording_base.py';recorder_sha=sha(recorder)
 for execution,body in c.execute('select execution,body from rag_execution_env order by execution'):
  b=json.loads(body);m=json.load(open(b['mapping_path']));mapping=m.get('mapping',m)
  metadata=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(execution,)).fetchone()[0];meta=json.load(open(metadata));hashes={k:v for k,v in meta.get('source_files_sha256',{}).items() if k.endswith('recording_base.py')};recorders.update(hashes.values())
  candidates=[]
  for source,selector,prov in c.execute("select json_extract(body,'$.source_path'),json_extract(body,'$.selector'),json_extract(body,'$.provenance') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='support_surface_identity'",(execution,)):
   candidates.append(dict(source=source,source_sha256=sha(source),selector=selector,provenance=json.loads(prov)))
  geometries=mapping.get('geometries',[])
  if isinstance(geometries,dict):geometries=list(geometries.values())
  for geom in geometries:
   for key,value in geom.items():
    a=geofields[key];a['executions'].add(execution);a['types'][type(value).__name__]+=1;a['example']=b['mapping_path']+'#/geometries/*/'+key
  rows.append(dict(execution_id=execution,task_id=b['task_id'],variant_id=b['variant_id'],mapping_path=b['mapping_path'],mapping_sha256=sha(b['mapping_path']),support_surface_records=candidates,declared_surface_ids=m.get('surface_ids'),declared_surface_roots=m.get('surface_roots'),logical_fixture_bindings=m.get('logical_fixture_bindings'),unresolved_logical_fixtures=m.get('unresolved_logical_fixtures'),physical_support_inferred=False,recorder_bindings=hashes,metadata_sha256=sha(metadata)))
 report=dict(executions=432,recorders_by_hash=dict(recorders),inspected_recorder_path=str(recorder),inspected_recorder_sha256=recorder_sha,matching_recorder_bindings=recorders[recorder_sha],rows=rows,qualification='Support-surface candidates are the sealed map declarations only. No geometry-only inference of actual support/contact/falling. Main_table remains unresolved.')
 with (WORK/'SPATIAL_SUPPLEMENT.json').open('x') as f:json.dump(report,f,sort_keys=True)
 with (HERE/'GEOMETRY_CHANNEL_INVENTORY.csv').open('x') as f:
  w=csv.writer(f);w.writerow(['source_field','executions','types','example_path_selector','representation','validation_limit'])
  for k,a in sorted(geofields.items()):w.writerow([k,len(a['executions']),json.dumps(a['types'],sort_keys=True),a['example'],'existing native mapping/support identity references','Declared/derived geometry metadata; never actual support/contact or safety truth'])
 print('Recorder matches',report['matching_recorder_bindings'],'geometry fields',len(geofields),flush=True)
if __name__=='__main__':run()
