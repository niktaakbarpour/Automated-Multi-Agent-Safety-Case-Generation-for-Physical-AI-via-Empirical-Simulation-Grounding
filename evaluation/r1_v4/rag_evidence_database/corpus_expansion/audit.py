"""Partition audit uses source identity metadata only, never safety outcomes."""
import csv,gzip,json
from collections import defaultdict,Counter
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.rag_evidence_database.inventory import TRANSFER,ORIGINAL
HERE=Path(__file__).resolve().parent

def audit():
 runs=load(REPO/'data/runs.json')['records'];tasks={r['task_id']:r for r in load(REPO/'data/tasks.json')['records']}
 split=load(REPO/'reports/fall_review_v2_20261016/proposed_split.json')
 evaluation=load(REPO/'evaluation/r1_v3_generalization/inventory/inventory.json')['records']
 reserved={r['run_id'] for r in evaluation if r['partition'] in ('same_task_reserved','cross_task_same_scene')}
 frozen={r['run_id'] for r in load(REPO/'evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json')['cases']}
 excluded=reserved|frozen|set(split['held_out']);existing=set(split['development']);groups=defaultdict(list)
 for r in runs:groups[(r['suite'],r['benchmark_task_id'])].append(r)
 verified={r['destination_path']:r for r in load(TRANSFER/'execution/verified-manifest.json')['archives'] if r['status']=='published_verified'};members={}
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as f:
  for line in f:
   r=json.loads(line)
   if r['logical_path'].startswith(str(ORIGINAL)+'/') and r['destination_archive'] in verified:members[r['logical_path']]=r
 rows=[];plans=[]
 names={'trajectory.h5','run_metadata.json','semantic_initial_conditions.json','simulator.xml','simulator_asset_manifest.json','simulator_index.json','evaluator_version.json','integrity_manifest.json','completion.json'}
 mapsha=load(REPO/'reports/fall_review_v2_20261016/corrected_native_geometry_v2.json')['source_xml_sha256']
 for (suite,task),group in sorted(groups.items()):
  xmls={r['evidence']['simulator_xml']['sha256'] for r in group};eligible=[r for r in group if r['run_id'] not in excluded|existing]
  paths=[str(ORIGINAL/f['source_relative_path']) for r in eligible for f in r['execution_files'] if f['name'] in names]
  mapped=all(p in members for p in paths);same_xml=xmls=={mapsha}
  row={'partition':suite+'/task_'+str(task).zfill(2),'task_id':group[0]['task_id'],'task_name':tasks[group[0]['task_id']]['task_name'],'executions':len(group),'already_indexed':sum(r['run_id'] in existing for r in group),'restricted_evaluation':sum(r['run_id'] in excluded for r in group),'candidate_database_only':len(eligible),'model_configuration_ids':';'.join(sorted({r['source_model_configuration_id'] for r in group})),'xml_variants':len(xmls),'xml_identical_to_existing':same_xml,'reader_disposition':'EXISTING_SCOPE_ONLY' if same_xml else 'REQUIRES_NEW_MEASUREMENT_PROFILE','recorder_schema_status':'Existing reader schema 4.0; other source metadata must be freshly verified, not inferred from inventory envelope 1.0.0','all_required_members_mapped':mapped,'candidate_member_count':len(paths),'candidate_bytes':sum(members[p]['size'] for p in paths if p in members),'archives':';'.join(sorted({members[p]['destination_archive'] for p in paths if p in members}))}
  rows.append(row);plans.append({k:row[k] for k in ('partition','executions','candidate_database_only','restricted_evaluation','candidate_member_count','candidate_bytes','archives','reader_disposition','all_required_members_mapped')})
 write_new(HERE/'PARTITION_DETAILS.json',{'schema_version':'1.0.0','partitions':rows,'excluded_execution_ids':sorted(excluded),'source_inventory_sha256':sha(REPO/'data/runs.json'),'tasks_sha256':sha(REPO/'data/tasks.json'),'policy':'Database-only eligibility is not calibration-development designation. All sixty sealed transfer-evaluation IDs excluded, including NV20; no safety outcomes consulted.'})
 with (HERE/'EXPANSION_PLAN.csv').open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(plans[0]),lineterminator='\n');w.writeheader();w.writerows(plans)
 print('Partitions',len(rows),'excluded',len(excluded),'new candidates',sum(r['candidate_database_only'] for r in rows),'compatible additional',sum(r['candidate_database_only'] for r in rows if r['xml_identical_to_existing']))
 return rows
if __name__=='__main__':audit()
