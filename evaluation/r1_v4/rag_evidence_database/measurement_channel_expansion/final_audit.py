"""Fresh baseline/source/frozen preservation checks after all validations."""
import json,subprocess,os,csv
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.final_validation import source_rows
from .channels import WORK,HERE,BASE,BASE_SHA
from .validate import save,preserve

def run():
 baseline='c24795ed9383110243288db520e5f98af484b4ad';assert subprocess.check_output(['git','rev-parse',baseline],text=True).strip()==baseline
 previous=HERE.parent/'variant_aware_expansion';manifest=json.loads((previous/'ARTIFACT_MANIFEST.json').read_text());checked=[]
 for r in manifest['files']+manifest['external_release_artifacts']:
  p=Path(r['path']);p=p if p.is_absolute() else REPO/p
  assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);checked.append(str(p))
 for r in source_rows():assert sha(r['restored_path'])==(r.get('actual_sha256') or r['sha256']);checked.append(r['restored_path'])
 for r in json.loads((previous/'EXTERNAL_PROFILE_ARTIFACTS.json').read_text())['files']:assert sha(r['path'])==r['sha256'];checked.append(r['path'])
 for p,h in json.loads((WORK/'INVENTORY_SUPPLEMENT.json').read_text())['sources'].items():assert sha(p)==h;checked.append(p)
 for r in json.loads((WORK/'MAIN_TABLE_AUDIT.json').read_text())['rows']:
  for source in r['sources']:assert sha(source['owned_path'])==source['expected_sha256'];checked.append(source['owned_path'])
 assert sha(BASE)==BASE_SHA
 checks=verify();save('FROZEN_FINAL.json',checks);save('PRESERVATION_FINAL.json',preserve(WORK/'expanded.sqlite'))
 # No existing tracked file may be altered by this phase.
 changed=subprocess.check_output(['git','diff','--name-only',baseline],text=True).splitlines()
 assert all(p.startswith(str(HERE.relative_to(REPO))+'/') for p in changed),changed
 for name in ('EXTRACTION_RETRIEVAL_VALIDATION.json','PRESERVATION_VALIDATION.json','REBUILD_VALIDATION.json','PARTIAL_RESUME.json','CHANNEL_SEMANTIC_EVALUATION.json','INVENTORY_VALIDATION.json','MAIN_TABLE_AUDIT.json','CLI_VALIDATION.json'):
  assert json.loads((WORK/name).read_text())['passed'],name
 for name in ('legacy/NEGATIVE_RETRIEVAL.json','legacy/SEMANTIC_EVALUATION.json','regressions/REGRESSION_RESULTS.json'):assert json.loads((WORK/name).read_text())['passed'],name
 tests=json.loads((WORK/'CHANNEL_TESTS.json').read_text());assert tests['returncode']==0 and tests['skipped']==0
 report=dict(passed=True,baseline_commit=baseline,baseline_database_sha256=BASE_SHA,freshly_hashed_paths=len(checked),database_path=str(WORK/'expanded.sqlite'),database_sha256=sha(WORK/'expanded.sqlite'),database_bytes=(WORK/'expanded.sqlite').stat().st_size,empirical_admission_enabled=False,new_execution_profiles=0,push_or_merge=False,simulation_steps=0,source_corpus_duplicated=False,free_disk1_bytes=os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize,frozen_checks=checks)
 save('FINAL_AUDIT.json',report)
 rows=json.loads((WORK/'SPATIAL_AUDIT.json').read_text())
 with (HERE/'SPATIAL_BINDINGS.csv').open('x') as f:
  w=csv.writer(f);w.writerow(['execution_id','task_id','variant_id','phase','category','logical_entity','exact_root_body','root_verified','semantic_source','semantic_sha256','xml_path','xml_sha256','mapping_path','mapping_sha256'])
  for r in rows:
   for b in r['logical_bindings']:w.writerow([r['execution_id'],r['task_id'],r['variant_id'],b['phase'],b['category'],b['logical'],b['root_body'],b['exact_root_verified'],r['semantic_path'],r['semantic_sha256'],r['xml_path'],r['xml_sha256'],r['mapping_path'],r['mapping_sha256']])
 with (HERE/'MAIN_TABLE_BINDINGS.csv').open('x') as f:
  w=csv.writer(f);w.writerow(['execution_id','task_id','variant_id','problem_name','status','derived_symbolic_mapping','source_lineage'])
  for r in json.loads((WORK/'MAIN_TABLE_AUDIT.json').read_text())['rows']:w.writerow([r['execution_id'],r['task_id'],r['variant_id'],r['problem_name'],r['status'],json.dumps(r['exact_mapping'],sort_keys=True),json.dumps(r['sources'],sort_keys=True)])
 print(report,flush=True)
if __name__=='__main__':run()
