"""Bounded authorized inventory, using archived metadata without archive recall."""
import gzip,json,collections,os
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
HERE=Path(__file__).resolve().parent
TRANSFER=Path('/disk/1/data/niktakbr/.alliance-transfer-control/hestia-20261026')
ORIGINAL=Path('/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero')

def inventory():
 runs=load(REPO/'data/runs.json')['records'];split=load(REPO/'reports/fall_review_v2_20261016/proposed_split.json')
 frozen={r['run_id'] for r in load(REPO/'evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json')['cases']}
 receipts=load(TRANSFER/'execution/verified-manifest.json');archives={r['destination_path']:r for r in receipts['archives'] if r['status']=='published_verified'}
 members={};archive_episodes={};by_model=collections.Counter();h5_local=0;archive_bytes=0
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line);path=row['logical_path']
   if 'libero' not in path.lower() or 'issta' in path.lower():continue
   if row['destination_archive'] not in archives:continue
   if path.endswith('/trajectory.h5'):
    archive_episodes[path]=row;archive_bytes+=row['size']
    by_model[row['unit_id'].rsplit('-',1)[0]]+=1
    # Do not inspect symlinked or non-owned roots.
    p=Path(row['source_path'])
    if p.is_relative_to('/disk/1/data/niktakbr') and not any(q.is_symlink() for q in (p,*p.parents)) and p.is_file():h5_local+=1
   if path.startswith(str(ORIGINAL)+'/'):members[path]=row
 rows=[]
 restored={Path(r['restored_path']).relative_to('/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence').as_posix():r for r in load(REPO/'evaluation/r1_v4/libero_measurement_reader/RESTORED_SOURCES.json')}
 for run in runs:
  rel=run['evidence']['trajectory']['source_relative_path'];p=ORIGINAL/rel;member=members.get(str(p));rest=restored.get(rel)
  partition='frozen_NV' if run['run_id'] in frozen else 'held_out' if run['run_id'] in split['held_out'] else 'development_proposed' if run['run_id'] in split['development'] else 'unclassified_not_development'
  available=rest is not None and Path(rest['restored_path']).is_file()
  rows.append(dict(execution_id=run['run_id'],task_id=run['task_id'],suite=run['suite'],episode=run['episode'],partition=partition,held_out=run['run_id'] in split['held_out'],frozen_NV=run['run_id'] in frozen,expected_sha256=run['evidence']['trajectory']['expected_sha256'],expected_bytes=run['evidence']['trajectory']['bytes'],original_path=str(p),original_present=p.is_file(),restored_path=rest['restored_path'] if available else None,archive=member['destination_archive'] if member else None,archive_member=member['archive_member'] if member else None,archive_receipt_verified=bool(member),measurement_index_eligible=available and partition=='development_proposed',completeness='validated_by_reader_at_indexing' if available else 'raw_not_locally_validated'))
 return dict(schema_version='1.0.0',scope='Project inventory plus LIBERO trajectory members in authorized transfer; no other-project payload inspection',project_execution_count=len(rows),held_out_count=len(split['held_out']),frozen_NV_count=len(frozen),held_out_frozen_overlap=len(set(split['held_out']) & frozen),partitions=dict(collections.Counter(r['partition'] for r in rows)),project_original_h5_present=sum(r['original_present'] for r in rows),restored_development_count=sum(r['measurement_index_eligible'] for r in rows),project_archive_mapped=sum(r['archive_receipt_verified'] for r in rows),authorized_archive_trajectory_count=len(archive_episodes),authorized_archive_trajectory_bytes=archive_bytes,archive_model_counts=dict(sorted(by_model.items())),archive_disk1_h5_present=h5_local,archive_status='Historical published_verified Hestia receipts; remote liveness not rechecked; no archive restored',estimated_development_index_bytes=32*1024**2,initial_disk_budget_bytes=128*1024**2,disk1_free_bytes=os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize,source_bindings={str(p):sha(p) for p in (REPO/'data/runs.json',REPO/'data/tasks.json',REPO/'reports/fall_review_v2_20261016/proposed_split.json',TRANSFER/'file-manifest.jsonl.gz',TRANSFER/'execution/verified-manifest.json')},executions=rows)
if __name__=='__main__':write_new(HERE/'SOURCE_COVERAGE_MANIFEST.json',inventory())
