"""Recorded versus extractable versus searchable channel accounting."""
import csv
from collections import Counter,defaultdict
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,WORK,DEST
from .registry import VariantStore
FAMILIES={'object_pose':['body_xpos','body_xquat'],'native_geometry':['geom_xpos','geom_xmat'],'contact':['contacts'],'robot_state':['qpos','qvel','ctrl'],'timestamp':['time'],'camera_reference':['agentview_image','robot0_eye_in_hand_image']}

def write_csv(name,rows):
 with (HERE/name).open('w',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def run():
 db=VariantStore(WORK/'expanded.sqlite');reports=load(HERE/'PROFILE_VALIDATION_PILOT.json')+load(HERE/'PROFILE_VALIDATION_BATCH.json');by={r['execution_id']:r for r in reports if r['passed']};variants=[];relations=[];matrix=[];cohort=load(HERE/'COHORT.json')
 for vid,xmlsha,assetdigest in db.db.execute('SELECT id,xml_sha256,asset_digest FROM rag_env_variants ORDER BY id'):
  executions=[r[0] for r in db.db.execute('SELECT execution FROM rag_execution_env WHERE variant_id=? ORDER BY execution',(vid,))];variants.append({'variant_id':vid,'xml_sha256':xmlsha,'asset_content_digest':assetdigest,'executions':';'.join(executions),'task_ids':';'.join(sorted({db.binding(e)['task_id'] for e in executions})),'status':'VERIFIED_IDENTITY_ONLY','physical_admission':'BLOCKED'})
 for execution,task,suite,variant_id in db.db.execute('SELECT execution,task_id,suite,variant_id FROM rag_execution_env ORDER BY execution'):
  b=db.binding(execution);relations.append({'execution_id':execution,'task_id':task,'suite':suite,'variant_id':variant_id,'xml_path':b['xml_path'],'xml_sha256':b['xml_sha256'],'asset_manifest_path':b['asset_manifest_path'],'asset_manifest_sha256':b['asset_manifest_sha256'],'mapping_path':b['mapping_path'],'mapping_sha256':b['mapping_sha256'],'mapping_version':b['mapping_version'],'scope':'measurement provenance only'})
  if execution not in by:continue
  report=by[execution];inventory=report['field_inventory'];sim=set(inventory['simulator']);raw=set(inventory['raw_observation']);indexed_sim={x for f,fields in FAMILIES.items() if f!='camera_reference' for x in fields};indexed_raw=set(FAMILIES['camera_reference'])
  for family,fields in FAMILIES.items():
   matrix.append({'task':report['task'],'variant_id':variant_id,'execution_id':execution,'family':family,'required_fields':';'.join(fields),'source_fields_present':all(x in (raw if family=='camera_reference' else sim) for x in fields),'separately_searchable':True,'coordinate_frame':'not_applicable_timestamp' if family=='timestamp' else 'unverified_camera_pixel_frame' if family=='camera_reference' else 'MuJoCo_native_mixed_units' if family=='robot_state' else 'MuJoCo_world','saved_frames':report['frames'],'continuous_physical_coverage':False,'physical_checking':'BLOCKED_ON_EVIDENCE','recorded_simulator_without_separate_units':';'.join(sorted(sim-indexed_sim)),'recorded_raw_without_separate_units':';'.join(sorted(raw-indexed_raw)),'unexposed_simulator':';'.join(inventory['unexposed_simulator']),'unexposed_raw':';'.join(inventory['unexposed_raw_observation']),'unsupported_fields':';'.join(report['unsupported_fields']),'unresolved_logical_fixtures':';'.join(report['unresolved_logical_fixtures'])})
 write_csv('VARIANT_REGISTRY.csv',variants);write_csv('EXECUTION_VARIANT_RELATIONS.csv',relations);write_csv('COVERAGE_MATRIX.csv',matrix)
 restored=[]
 for r in cohort['files']:
  path=r['restored_path'];meta=load(DEST/r['task']/'episode_001/run_metadata.json');expected=r['expected_sha256'] or meta['initial_states_sha256'];actual=sha(path);assert expected==actual
  restored.append({**r,'resolved_expected_sha256':expected,'actual_sha256':actual})
 write_csv('RESTORED_SOURCE_MANIFEST.csv',restored)
 records=db.db.execute('SELECT count(*) FROM evidence').fetchone()[0];types=dict(db.db.execute('SELECT type,count(*) FROM rag_units GROUP BY type'));status=dict(db.db.execute('SELECT status,count(*) FROM rag_scope_status GROUP BY status'))
 frame_count=load(HERE.parent/'multitask_expansion/validation/INDEXED_CORPUS.json')['frame_count']+sum(r['frames'] for r in by.values())
 summary={'total_executions':len(relations),'total_records':records,'saved_frames':frame_count,'variants':len(variants),'new_executions':len(by),'new_variant_count':len({r['variant_id'] for r in by.values()}),'source_files_restored':len(restored),'restored_bytes':sum(r['bytes'] for r in restored),'evidence_type_counts':types,'execution_status_counts':status,'searchable_families':FAMILIES,'coverage_matrix_rows':len(matrix),'original_inventory_executions':2000,'metadata_only_catalog_entries':db.db.execute('SELECT count(*) FROM rag_catalog').fetchone()[0],'remaining_candidate_executions':status['unindexed_profile_pending'],'remaining_total_unindexed':2000-len(relations),'logical_main_table_alias':'UNRESOLVED_NOT_EXTRACTED','physically_recorded_vs_searchable':'Archive metadata describes 2000 recordings. Fresh restored original payloads support 432 indexed executions; only six measurement families have separate raw retrieval units. Other saved fields remain source references/inventories, not searchable physical predicates.'}
 write_new(WORK/'COVERAGE_SUMMARY.json',summary);db.close();return summary
if __name__=='__main__':print(run())
