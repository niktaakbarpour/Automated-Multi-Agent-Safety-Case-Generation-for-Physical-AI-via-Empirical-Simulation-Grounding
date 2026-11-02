"""Plan only: no remaining-corpus restoration or held-out outcome use."""
from pathlib import Path
from collections import Counter
import gzip,json,math
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.rag_evidence_database.inventory import TRANSFER,ORIGINAL
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from .profile import HERE

def audit():
 runs=load(REPO/'data/runs.json')['records'];split=load(REPO/'reports/fall_review_v2_20261016/proposed_split.json');development=set(split['development']);frozen={r['run_id'] for r in load(REPO/'evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json')['cases']}
 remaining=[r for r in runs if r['run_id'] not in development];assert len(remaining)==1960
 verified={r['destination_path']:r for r in load(TRANSFER/'execution/verified-manifest.json')['archives'] if r['status']=='published_verified'}
 archive={}
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line)
   if row['logical_path'].startswith(str(ORIGINAL)+'/') and row['destination_archive'] in verified:archive[row['logical_path']]=row
 names={'trajectory.h5','run_metadata.json','semantic_initial_conditions.json','simulator.xml','simulator_asset_manifest.json','simulator_index.json','evaluator_version.json','integrity_manifest.json','completion.json'}
 rows=[]
 for run in remaining:
  files=[x for x in run['execution_files'] if x['name'] in names];paths=[str(ORIGINAL/x['source_relative_path']) for x in files]
  complete_archive=len(files)==9 and all(p in archive for p in paths);complete_local=len(files)==9 and all(Path(p).is_file() for p in paths)
  rows.append({'execution_id':run['run_id'],'task_id':run['task_id'],'suite':run['suite'],'episode':run['episode'],'partition':'frozen_NV' if run['run_id'] in frozen else 'unclassified_not_development','complete_local_nine_file_set':complete_local,'complete_archive_nine_file_set':complete_archive,'minimum_file_bytes':sum(x['bytes'] for x in files),'expected_frames':run['available_measurements']['root_groups']['frames'],'five_object_index_unit_scenario':15+30*math.ceil(run['available_measurements']['root_groups']['frames']/32)})
 return {'schema_version':'1.0.0','remaining_executions':1960,'complete_local_source_sets':sum(r['complete_local_nine_file_set'] for r in rows),'archive_complete_sets':sum(r['complete_archive_nine_file_set'] for r in rows),'missing_or_uncertain_archive_sets':sum(not r['complete_archive_nine_file_set'] for r in rows),'partitions':dict(Counter(r['partition'] for r in rows)),'minimum_restore_bytes':sum(r['minimum_file_bytes'] for r in rows),'five_object_index_unit_scenario':sum(r['five_object_index_unit_scenario'] for r in rows),'archive_paths':{a:{'expected_container_bytes':verified[a]['container_bytes'],'historical_sha256':verified[a]['sha256']} for a in sorted({r['destination_archive'] for r in archive.values()})},'shared_task_files_additional':'Task BDDL and initial archives must be separately verified/restored per new task; not included in nine-file estimate.','qualification':'Archive membership/receipts and historical frame metadata, not fresh raw validation or a compatible reader profile. Five-object density is a planning scenario only. No further restoration authorized/performed.','executions':rows}
if __name__=='__main__':write_new(HERE/'REMAINING_INVENTORY.json',audit())
