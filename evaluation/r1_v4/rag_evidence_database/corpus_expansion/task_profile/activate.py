"""Verify the entire exact source closure before enabling batch reads."""
from pathlib import Path
import csv
from evaluation.r1_v4.provenance import load,canonical,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,DEST

def activate():
 assert load(HERE/'PILOT_VALIDATION.json')['passed']
 plan=load(HERE/'SOURCE_PLAN.json');pilot=load(DEST/'object/task_02/episode_001/run_metadata.json');rows=[];bindings=[]
 native=load(HERE/'NATIVE_PROFILE.json');xml_sha=native['mapping']['source_xml_sha256']
 for r in plan['files']:
  p=Path(r['restored_path']);expected=r['expected_sha256'] or pilot['initial_states_sha256'];actual=sha(p)
  assert actual==expected and p.stat().st_size==r['bytes'],str(p)
  rows.append({**r,'expected_sha256':expected,'actual_sha256':actual,'verified':True});bindings.append({'restored_path':str(p),'sha256':actual})
 for r in plan['executions']:
  root=DEST/'object/task_02'/f"episode_{r['episode']:03d}"
  assert sha(root/'simulator.xml')==xml_sha
  meta=load(root/'run_metadata.json');assert meta['global_episode_id']==r['execution_id'] and meta['task_configuration_id']=='b12b2d70fe80d3547b1e' and meta['model_configuration_id']=='497495005f5e820a10c9'
  assert meta['recorder_schema_version']==meta['dataset_schema_version']=='4.0'
  index=load(root/'simulator_index.json');assert index['body_names']==native['mapping']['body_names']
 native['mapping']['validated_run_ids']=[r['execution_id'] for r in plan['executions']]
 native['mapping']['registration_scope']='Exact serialized model identity registered after source hashes; full snapshot validation remains mandatory for every read.'
 (HERE/'NATIVE_PROFILE.json').write_bytes(canonical(native)+b'\n')
 profile=load(HERE/'PROFILE.json');profile.update(state='BATCH_SOURCES_VERIFIED_PILOT_PASSED',native_profile_sha256=sha(HERE/'NATIVE_PROFILE.json'),allowed_episodes=[r['episode'] for r in plan['executions']],source_bindings=bindings)
 (HERE/'PROFILE.json').write_bytes(canonical(profile)+b'\n')
 write_new(HERE/'RESTORED_SOURCES.json',{'schema_version':'1.0.0','files':rows,'executions':49,'files_verified':443,'bytes':sum(r['bytes'] for r in rows),'empirical_admission_enabled':False})
 with (HERE.parent/'RESTORATION_MANIFEST.csv').open('w',newline='') as f:
  fields=['execution_id','episode','archive','archive_member','restored_path','bytes','expected_sha256','actual_sha256','verified'];w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
 print('Activated source profile',len(bindings),'files',len(plan['executions']),'executions')
if __name__=='__main__':activate()
