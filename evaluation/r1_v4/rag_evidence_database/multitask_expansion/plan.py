"""Reproducible four-task batch, never selected using safety outcomes."""
import gzip,json
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO
from evaluation.r1_v4.rag_evidence_database.inventory import ORIGINAL,TRANSFER
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase5e-evidence')

def create():
 root=REPO/'evaluation/r1_v4/rag_evidence_database/corpus_expansion'
 audit=load(root/'PARTITION_DETAILS.json');old=load(root/'task_profile/validation/INDEXED_CORPUS.json');indexed={r['execution_id'] for r in old['per_execution']}
 excluded=set(load(root/'task_profile/SOURCE_PLAN.json')['excluded_ids'])
 candidates=[r for r in audit['partitions'] if r['candidate_database_only'] and r['xml_variants']==1 and r['task_id'] not in {r['task_id'] for r in old['per_execution']}]
 selected=sorted(candidates,key=lambda r:(r['candidate_bytes'],r['partition']))[:4];assert len(selected)==4
 runs=load(REPO/'data/runs.json')['records'];tasks=load(REPO/'data/tasks.json')['records'];wanted={};groups={}
 names={'trajectory.h5','run_metadata.json','semantic_initial_conditions.json','simulator.xml','simulator_asset_manifest.json','simulator_index.json','evaluator_version.json','integrity_manifest.json','completion.json'}
 for task in selected:
  key=task['partition'];group=sorted([r for r in runs if r['task_id']==task['task_id'] and r['run_id'] not in excluded|indexed],key=lambda r:r['run_id']);assert len(group)==49
  pilot=group[0];info=next(t for t in tasks if t['task_id']==task['task_id'])
  groups[key]={'task':task,'task_scope':info['facts']['scope'],'objects':list(info['facts']['scene_description']['declared_objects']),'fixtures':list(info['facts']['scene_description']['declared_fixtures']),'pilot_episode':pilot['episode'],'executions':[{'execution_id':r['run_id'],'episode':r['episode'],'seed':r['seed'],'frames':r['available_measurements']['root_groups']['frames'],'model_id':r['source_model_configuration_id']} for r in group]}
  for r in group:
   for f in r['execution_files']:
    if f['name'] not in names:continue
    h=(f.get('producer_integrity') or {}).get('sha256')
    if not h:
     entry=r['evidence'].get(Path(f['name']).stem,{});h=entry.get('sha256') or entry.get('expected_sha256')
    assert h
    wanted[str(ORIGINAL/f['source_relative_path'])]={'task':key,'execution_id':r['run_id'],'episode':r['episode'],'expected_sha256':h,'bytes':f['bytes'],'phase':'pilot' if r is pilot else 'batch'}
  for name in ('task.bddl','benchmark_initial_states.init'):wanted[str(ORIGINAL/key/name)]={'task':key,'execution_id':'shared','episode':None,'expected_sha256':pilot['evidence']['task_definition']['sha256'] if name=='task.bddl' else None,'bytes':None,'phase':'pilot'}
 receipts={r['destination_path']:r for r in load(TRANSFER/'execution/verified-manifest.json')['archives'] if r['status']=='published_verified'};files=[]
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line)
   if row['logical_path'] not in wanted:continue
   item=wanted[row['logical_path']];assert row['destination_archive'] in receipts
   if item['bytes'] is not None:assert item['bytes']==row['size']
   rel=Path(row['logical_path']).relative_to(ORIGINAL);files.append({**item,'bytes':row['size'],'original_path':row['logical_path'],'restored_path':str(DEST/rel),'archive':row['destination_archive'],'archive_member':row['archive_member']})
 assert len(files)==1772 and sum(len(t['executions']) for t in groups.values())==196
 report={'schema_version':'1.0.0','selection':'Four lowest recorded nine-file footprints among remaining nonreserved single-XML task partitions, then partition name; exclude all60 reserved and all38 preflight examples. No outcomes/predictions used.','tasks':groups,'files':files,'excluded_ids':sorted(excluded),'archives':{a:{k:receipts[a][k] for k in ('container_bytes','sha256','status')} for a in {r['archive'] for r in files}}}
 write_new(HERE/'SOURCE_PLAN.json',report);print('Selected',list(groups),'executions',196,'files',len(files),'bytes',sum(r['bytes'] for r in files))
if __name__=='__main__':create()
