"""Resolve canonical claim projection IDs to exact original JSON fields independently."""
import json,sqlite3
from .config import HERE,WORK
from .model import validate_claim
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
MAP={'source_commit_declaration':['source_commit'],'dependency_version_declarations':['versions'],'python_declaration':['python'],'checkpoint_hash_declarations':['checkpoint_weight_sha256'],'hardware_backend_declarations':['gpu','gpu_driver','physical_gpu_index','model_family','checkpoint_revision'],'recording_configuration':['recorder_schema_version','dataset_schema_version','control_frequency_hz','settling_steps','observation_size','seed','inference_configuration','resolved_policy_configuration','recording_notes']}
SCALARS={'source_commit_declaration','dependency_version_declarations','python_declaration','checkpoint_hash_declarations'}
def run():
 c=sqlite3.connect('file:'+str(WORK/'expanded.sqlite')+'?mode=ro',uri=True);v=SourceVerifier();cache={};count=0;missing=[]
 for body, in c.execute('select body from i_claims order by execution,property'):
  cl=json.loads(body);validate_claim(cl);p=cl['source_artifact'];key=(p['path'],p['sha256'])
  if key not in cache:
   with v.access(*key,'strict') as (f,a):cache[key]=json.load(f)
  m=cache[key];prop=cl['source_selector'];fields=MAP[prop]
  absent=[f for f in fields if f not in m]
  if absent:missing.append(dict(execution_id=cl['execution_id'],projection=prop,absent_fields=absent))
  expected=m.get(fields[0],{} if prop=='checkpoint_hash_declarations' else None) if prop in SCALARS else {f:m.get(f) for f in fields}
  assert expected==cl['value'],(cl['id'],prop);count+=1
 definition=dict(selector_namespace='canonical_projection_id, not literal original JSON pointer',projections={k:dict(original_json_pointers=['/'+f for f in fields],transformation='single-field identity' if k in SCALARS else 'named object projection; absent members explicitly represented as null without asserting null was recorded') for k,fields in MAP.items()})
 (HERE/'CLAIM_SOURCE_SELECTORS.json').write_text(json.dumps(definition,sort_keys=True,indent=2)+'\n');(WORK/'CLAIM_VALIDATION.json').write_text(json.dumps(dict(passed=True,claims=count,executions=len(cache),missing_source_fields=missing,value_mismatches=0,historical_running_environment_attested=False),sort_keys=True,indent=2));print('CLAIMS',count,'executions',len(cache),'missing fields',len(missing),flush=True)
if __name__=='__main__':run()
