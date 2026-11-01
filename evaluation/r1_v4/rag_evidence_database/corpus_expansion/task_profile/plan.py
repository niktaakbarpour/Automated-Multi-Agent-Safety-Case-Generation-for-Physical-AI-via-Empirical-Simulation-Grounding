"""One-task source plan; no event labels or predictions participate in selection."""
import gzip,json,shlex
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.rag_evidence_database.inventory import TRANSFER,ORIGINAL
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase5d-object-task02')

def create():
 audit=load(HERE.parent/'PARTITION_DETAILS.json');candidates=[r for r in audit['partitions'] if r['candidate_database_only'] and r['xml_variants']==1]
 chosen=min(candidates,key=lambda r:(r['candidate_bytes'],r['partition']));assert chosen['partition']=='object/task_02'
 previous=load(REPO/'evaluation/r1_v3_generalization/inventory/inventory.json')['records'];exclude=set(audit['excluded_execution_ids'])|{r['run_id'] for r in previous if r['partition']=='cross_scene_preflight'}
 runs=[r for r in load(REPO/'data/runs.json')['records'] if r['suite']=='object' and r['benchmark_task_id']==2 and r['run_id'] not in exclude]
 runs.sort(key=lambda r:r['run_id']);assert len(runs)==49
 pilot=runs[0];assert pilot['episode']==1
 wanted={};names={'trajectory.h5','run_metadata.json','semantic_initial_conditions.json','simulator.xml','simulator_asset_manifest.json','simulator_index.json','evaluator_version.json','integrity_manifest.json','completion.json'}
 for r in runs:
  for f in r['execution_files']:
   if f['name'] not in names:continue
   h=(f.get('producer_integrity') or {}).get('sha256')
   if h is None:
    item=r['evidence'].get(Path(f['name']).stem,{})
    h=item.get('sha256') or item.get('expected_sha256')
   assert h,f['name']
   wanted[str(ORIGINAL/f['source_relative_path'])]={'execution_id':r['run_id'],'episode':r['episode'],'expected_sha256':h,'bytes':f['bytes'],'phase':'pilot' if r['run_id']==pilot['run_id'] else 'batch'}
 root=str(ORIGINAL/'object/task_02')
 for name in ('task.bddl','benchmark_initial_states.init'):wanted[root+'/'+name]={'execution_id':'shared','episode':None,'expected_sha256':pilot['evidence']['task_definition']['sha256'] if name=='task.bddl' else None,'bytes':None,'phase':'pilot'}
 verified={r['destination_path']:r for r in load(TRANSFER/'execution/verified-manifest.json')['archives'] if r['status']=='published_verified'};files=[]
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line)
   if row['logical_path'] in wanted:
    assert row['destination_archive'] in verified
    item=wanted[row['logical_path']]
    if item['bytes'] is not None:assert row['size']==item['bytes']
    rel=Path(row['logical_path']).relative_to(ORIGINAL)
    files.append({**item,'bytes':row['size'],'original_path':row['logical_path'],'restored_path':str(DEST/rel),'archive':row['destination_archive'],'archive_member':row['archive_member']})
 assert len(files)==443
 report={'schema_version':'1.0.0','status':'PILOT_RESTORATION_ONLY_UNTIL_PROFILE_PASSES','selection_rule':'Of unrestricted candidate partitions with one recorded XML, smallest total nine-file bytes, then partition name. Exclude all60 reserved plus all38 cross-scene preflight IDs. Pilot is lexicographically first remaining ID. No outcomes used.','task':chosen,'executions':[{'execution_id':r['run_id'],'episode':r['episode'],'seed':r['seed'],'frames':r['available_measurements']['root_groups']['frames'],'metadata_hashes':r['evidence']} for r in runs],'files':files,'archives':{a:{k:verified[a][k] for k in ('container_bytes','sha256','status')} for a in {r['archive'] for r in files}},'excluded_ids':sorted(exclude)}
 write_new(HERE/'SOURCE_PLAN.json',report);return report
if __name__=='__main__':
 x=create();print('Candidate',x['task']['partition'],'batch',len(x['executions']),'files',len(x['files']),'bytes',sum(r['bytes'] for r in x['files']))
