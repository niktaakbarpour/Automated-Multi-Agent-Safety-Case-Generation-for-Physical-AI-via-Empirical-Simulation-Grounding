"""Minimum missing development sources; planning only, no transfers."""
import gzip,json
from pathlib import Path
from .inventory import TRANSFER,ORIGINAL,HERE
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.provenance import load,write_new

def plan():
 coverage=load(HERE/'SOURCE_COVERAGE_MANIFEST.json')
 needed={r['execution_id']:r for r in coverage['executions'] if r['partition']=='development_proposed' and not r['measurement_index_eligible']}
 runs={r['run_id']:r for r in load(REPO/'data/runs.json')['records']};expected={}
 names={'trajectory.h5','run_metadata.json','semantic_initial_conditions.json','simulator.xml','simulator_asset_manifest.json','simulator_index.json','evaluator_version.json','integrity_manifest.json','completion.json'}
 for rid,row in needed.items():
  run=runs[rid]
  for f in run['execution_files']:
   if f['name'] in names:
    integrity=f.get('producer_integrity') or {}
    expected[str(ORIGINAL/f['source_relative_path'])]={'execution_id':rid,'expected_sha256':integrity.get('sha256') or (row['expected_sha256'] if f['name']=='trajectory.h5' else None),'expected_bytes':f['bytes']}
 files=[]
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line)
   if row['logical_path'] in expected:files.append({**expected[row['logical_path']],'original_path':row['logical_path'],'archive':row['destination_archive'],'archive_member':row['archive_member'],'receipt_member_bytes':row['size']})
 return {'schema_version':'1.0.0','missing_development_executions':len(needed),'requested_file_count':len(expected),'mapped_files':len(files),'bytes':sum(r['receipt_member_bytes'] for r in files),'files':files,'shared_sources':'Existing verified task.bddl and benchmark_initial_states.init may be reused only after task/hash identity verification. No raw videos required.','restriction':'Planning only; 36 new executions need an explicit versioned reader capability extension before measurement population. No restoration performed. Unknown member hashes remain null until producer/source verification.'}
if __name__=='__main__':write_new(HERE/'SELECTIVE_RESTORATION_PLAN.json',plan())
