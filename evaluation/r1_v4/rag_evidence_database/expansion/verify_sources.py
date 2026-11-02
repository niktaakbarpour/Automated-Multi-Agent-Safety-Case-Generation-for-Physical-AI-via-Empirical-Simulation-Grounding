"""Verify only the exact restored development allowlist and build a pinned profile."""
from pathlib import Path
import shutil
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha,ROOT as OLDROOT
from .profile import HERE,ROOT,NAME

def verify_sources():
 plan=load(HERE/'RESTORATION_PLAN.json');resolved={r['original_path']:r for r in load(HERE/'RESOLVED_EXPECTED_HASHES.json')}
 runs={r['run_id']:r for r in load(REPO/'data/runs.json')['records']};bindings=[];executions={};rows=[]
 receipts=[]
 for archive in sorted(plan['archive_receipts']):receipts+=load(ROOT/('receipt-'+Path(archive).name+'.json'))
 received={r['original_path']:r for r in receipts};assert len(received)==324
 for row in plan['files']:
  rel=Path(row['original_path']).relative_to('/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero')
  p=ROOT/rel;expected=row['expected_sha256'] or resolved[row['original_path']]['expected_sha256'];actual=sha(p)
  assert actual==expected==received[row['original_path']]['sha256'] and p.stat().st_size==row['expected_bytes']
  bindings.append({'restored_path':str(p),'sha256':actual})
  rows.append({**row,'restored_path':str(p),'sha256':actual,'expected_sha256':expected,'verified':True,'hash_expectation_source':'Phase5B selected plan' if row['expected_sha256'] else resolved[row['original_path']]['source_pointer']})
  r=runs[row['execution_id']];executions[str(r['episode'])]={'execution_id':r['run_id'],'frames':r['available_measurements']['root_groups']['frames'],'task_id':r['task_id']}
 assert len(executions)==36
 shared=[]
 for name in ('task.bddl','benchmark_initial_states.init'):
  source=OLDROOT/'long/task_00'/name;target=ROOT/'long/task_00'/name
  if not target.exists():
   with source.open('rb') as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
  assert sha(target)==sha(source)
  entry={'restored_path':str(target),'sha256':sha(target)};bindings.append(entry);shared.append({**entry,'source_path':str(source),'reused_verified_shared_source':True})
 approvals={n:sha(REPO/n) for n in ('reports/fall_review_v2_20261016/proposed_split.json','evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json','data/runs.json','reports/fall_review_v2_20261016/corrected_native_geometry_v2.json')}
 profile={'profile_version':NAME,'measurement_only':True,'empirical_admission_enabled':False,'approval_bindings':approvals,'executions':executions,'source_bindings':bindings}
 write_new(HERE/'VALIDATED_SOURCE_PROFILE.json',profile)
 report={'schema_version':'1.0.0','restored_executions':36,'restored_files':324,'restored_bytes':sum(r['expected_bytes'] for r in rows),'freshly_hash_verified':324,'reused_shared_sources':shared,'files':rows,'all_expected_hashes_matched':True,'baseline_sha256':sha('/disk/1/data/niktakbr/trustworthy-phase5b-working/validated/development.sqlite')}
 write_new(HERE/'RESTORATION_MANIFEST.json',report);print('Restoration verification:',len(rows),'files',len(executions),'executions')
 return report
if __name__=='__main__':verify_sources()
