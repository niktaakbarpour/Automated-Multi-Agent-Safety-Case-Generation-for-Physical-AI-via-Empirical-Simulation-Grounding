"""Remaining-candidate inventory and frozen, cost-bounded multi-XML cohort."""
import gzip,json,os
from pathlib import Path
from collections import defaultdict
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.rag_evidence_database.inventory import ORIGINAL,TRANSFER
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase5f-evidence')
WORK=Path('/disk/1/data/niktakbr/trustworthy-phase5f-working')
BASE=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/final-validated/corpus-285.sqlite')
BASE_SHA='5d3eb7589ddbf564cf29189af3264fd9861df44780e65e3246b62bbe74bc9934'
NAMES={'trajectory.h5','run_metadata.json','semantic_initial_conditions.json','simulator.xml','simulator_asset_manifest.json','simulator_index.json','evaluator_version.json','integrity_manifest.json','completion.json'}

def create():
 prior=load(HERE.parent/'multitask_expansion/REMAINING_CORPUS_PLAN.json');excluded=set(load(HERE.parent/'multitask_expansion/SOURCE_PLAN.json')['excluded_ids']);indexed={r['execution_id'] for r in load(HERE.parent/'multitask_expansion/validation/INDEXED_CORPUS.json')['per_execution']}
 selected=sorted([r for r in prior['partitions'] if r['xml_variants']>1],key=lambda r:(r['candidate_bytes'],r['partition']))[:3];selected_ids={r['task_id'] for r in selected};runs=load(REPO/'data/runs.json')['records'];tasks=load(REPO/'data/tasks.json')['records'];wanted={};groups={};inventory=[];xmls=defaultdict(list)
 for r in runs:
  if r['run_id'] in excluded or r['run_id'] in indexed:continue
  files=[f for f in r['execution_files'] if f['name'] in NAMES];xml=r['evidence'].get('simulator_xml',{});asset=next((f for f in files if f['name']=='simulator_asset_manifest.json'),{});asset_sha=(asset.get('producer_integrity') or {}).get('sha256');expected_xml=xml.get('sha256');available=[f['name'] for f in files if (ORIGINAL/f['source_relative_path']).is_file()]
  row={'execution_id':r['run_id'],'suite':r['suite'],'task_id':r['task_id'],'partition':r['suite']+f"/task_{r['benchmark_task_id']:02d}",'episode':r['episode'],'source_recording_location':str(ORIGINAL/r['evidence']['trajectory']['source_relative_path']),'expected_xml_sha256':expected_xml,'expected_asset_manifest_sha256':asset_sha,'xml_variant_id':None,'variant_status':'UNRESOLVED_PAYLOAD_NOT_VERIFIED','available_original_files':available,'required_episode_files':len(files),'source_manifest_status':'EXPECTED_HASHES_RECORDED','geometry_mapping_status':'UNVALIDATED','indexing_eligibility':'CANDIDATE_REQUIRES_PROFILE','exclusion_reason':None}
  inventory.append(row)
  if expected_xml:xmls[expected_xml].append({'execution_id':r['run_id'],'task_id':r['task_id'],'asset_manifest_sha256':asset_sha})
  if r['task_id'] not in selected_ids:continue
  partition=next(p for p in selected if p['task_id']==r['task_id']);key=partition['partition']
  if key not in groups:
   t=next(t for t in tasks if t['task_id']==r['task_id']);groups[key]={'task':partition,'task_scope':t['facts']['scope'],'objects':list(t['facts']['scene_description']['declared_objects']),'fixtures':list(t['facts']['scene_description']['declared_fixtures']),'executions':[],'pilot_episode':1}
  groups[key]['executions'].append({'execution_id':r['run_id'],'episode':r['episode'],'seed':r['seed'],'frames':r['available_measurements']['root_groups']['frames'],'model_id':r['source_model_configuration_id'],'expected_xml_sha256':expected_xml})
  for f in files:
   h=(f.get('producer_integrity') or {}).get('sha256');entry=r['evidence'].get(Path(f['name']).stem,{})
   h=h or entry.get('sha256') or entry.get('expected_sha256');assert h
   wanted[str(ORIGINAL/f['source_relative_path'])]={'task':key,'execution_id':r['run_id'],'episode':r['episode'],'expected_sha256':h,'bytes':f['bytes'],'phase':'pilot' if r['episode']==1 else 'batch'}
 assert len(inventory)==1617 and sum(len(t['executions']) for t in groups.values())==147
 for key,t in groups.items():
  pilot=next(r for r in runs if r['run_id']==next(e for e in t['executions'] if e['episode']==1)['execution_id'])
  for name in ('task.bddl','benchmark_initial_states.init'):wanted[str(ORIGINAL/key/name)]={'task':key,'execution_id':'shared','episode':None,'expected_sha256':pilot['evidence']['task_definition']['sha256'] if name=='task.bddl' else None,'bytes':None,'phase':'pilot'}
 receipts={r['destination_path']:r for r in load(TRANSFER/'execution/verified-manifest.json')['archives'] if r['status']=='published_verified'};found=[]
 with gzip.open(TRANSFER/'file-manifest.jsonl.gz','rt') as stream:
  for line in stream:
   r=json.loads(line)
   if r['logical_path'] not in wanted:continue
   item=wanted[r['logical_path']];assert r['destination_archive'] in receipts
   if item['bytes'] is not None:assert item['bytes']==r['size']
   found.append({**item,'bytes':r['size'],'original_path':r['logical_path'],'restored_path':str(DEST/Path(r['logical_path']).relative_to(ORIGINAL)),'archive':r['destination_archive'],'archive_member':r['archive_member']})
 assert len(found)==1329
 write_new(HERE/'INVENTORY.json',{'candidate_count':len(inventory),'executions':inventory,'xml_hash_relationships':dict(xmls),'unresolved_until_payload_and_asset_verification':True,'exclusions':{'reserved':60,'preflight':38},'cross_task_expected_xml_hashes':{h:v for h,v in xmls.items() if len({r['task_id'] for r in v})>1}})
 write_new(HERE/'COHORT.json',{'schema_version':'1.0.0','selection':'Three least nine-file source-footprint remaining multi-XML partitions, tie by partition name; episodes1..49, no outcome labels.','tasks':groups,'files':found,'excluded_ids':sorted(excluded),'baseline_sha256':BASE_SHA,'archives':{a:receipts[a] for a in {f['archive'] for f in found}}})
 write_new(HERE/'STORAGE_PREFLIGHT.json',{'disk1_available':os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize,'source_bytes':sum(f['bytes'] for f in found),'required_members':len(found),'baseline_sha256':sha(BASE)})
 print('Frozen cohort',list(groups),147,len(found),sum(f['bytes'] for f in found),flush=True)
if __name__=='__main__':create()
