"""Reuse sealed baseline measurement maps; add verified environment associations."""
from pathlib import Path
from collections import defaultdict
from evaluation.r1_v4.provenance import load,write_new,strict_loads
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.rag_evidence_database.store import Store
from .identity import identify
from .plan import HERE,BASE,BASE_SHA,WORK
from .registry import validate_mapping

def discover():
 assert sha(BASE)==BASE_SHA;db=Store(BASE);bindings=[];objects=defaultdict(dict)
 for execution,obj,bid,geoms in db.db.execute("SELECT DISTINCT execution_id,object_id,json_extract(body,'$.provenance.body_id'),json_extract(body,'$.provenance.collision_geom_ids') FROM evidence WHERE kind='raw_measurement'"):
  objects[execution][obj]={'body_id':bid,'collision_geom_ids':strict_loads(geoms)}
 maps={e:(p,h) for e,p,h in db.db.execute("SELECT DISTINCT execution_id,json_extract(body,'$.source_path'),json_extract(body,'$.source_sha256') FROM evidence WHERE json_extract(body,'$.measurement_type')='support_surface_identity'")}
 for execution,meta_path,meta_sha,task_id in db.db.execute("SELECT execution_id,json_extract(body,'$.source_path'),json_extract(body,'$.source_sha256'),json_extract(body,'$.task_id') FROM evidence WHERE json_extract(body,'$.measurement_type')='execution_metadata' ORDER BY execution_id"):
  assert sha(meta_path)==meta_sha;root=Path(meta_path).parent;meta=load(meta_path);xml=root/'simulator.xml';assets=root/'simulator_asset_manifest.json';identity=identify(xml,assets);mapping,mapsha=maps[execution];assert sha(mapping)==mapsha;model=load(mapping);model=model.get('mapping',model)
  b={'execution_id':execution,'task_id':task_id,'suite':meta['suite_label'],'partition':meta['suite_label']+f"/task_{meta['task_id']:02d}",'variant_id':identity['variant_id'],'xml_path':str(xml),'xml_sha256':identity['xml_sha256'],'asset_content_digest':identity['asset_content_digest'],'asset_manifest_path':str(assets),'asset_manifest_sha256':sha(assets),'mapping_path':mapping,'mapping_sha256':mapsha,'mapping_version':model['schema_version'],'profile_sha256':None,'objects':objects[execution],'validation_scope':'Reused sealed Phase5E measurement map; fresh XML/assets/hash verification. No physical predicate admission.'}
  validate_mapping(b);bindings.append({'identity':identity,'binding':b})
 db.close();assert len(bindings)==285
 write_new(WORK/'BASELINE_ENVIRONMENTS.json',bindings);print('Verified baseline environment bindings',len(bindings),len({r['identity']['variant_id'] for r in bindings}),flush=True)
 return bindings

def initialize(store):
 for r in load(WORK/'BASELINE_ENVIRONMENTS.json'):
  store.register(r['identity'],r['binding']);store.set_status(r['binding']['execution_id'],'indexed',r['binding']['partition'],'Preserved Phase5E release')
 inventory=load(HERE/'INVENTORY.json')
 for r in inventory['executions']:
  if not store.db.execute('SELECT 1 FROM rag_scope_status WHERE execution=?',(r['execution_id'],)).fetchone():store.set_status(r['execution_id'],'unindexed_profile_pending',r['partition'],'Original payload/profile not yet verified in Phase5F')
 reserved=set(load(HERE.parent/'corpus_expansion/PARTITION_DETAILS.json')['excluded_execution_ids']);excluded=set(load(HERE/'COHORT.json')['excluded_ids']);assert len(reserved)==60 and len(excluded-reserved)==38
 for execution in sorted(excluded):store.set_status(execution,'excluded_reserved' if execution in reserved else 'excluded_preflight',None,'Preserved exclusion; no source payload inspected')
if __name__=='__main__':discover()
