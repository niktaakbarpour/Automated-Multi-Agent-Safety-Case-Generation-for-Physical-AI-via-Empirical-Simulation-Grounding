"""Closed, versioned measurement-only task registration."""
from pathlib import Path
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from .plan import HERE,DEST
NAME='object-task02:1.0.0'

def approved_profile(name,root,episode):
 if name!=NAME or Path(root).resolve()!=DEST:raise ValueError('unapproved task profile/root')
 profile=load(HERE/'PROFILE.json');plan=load(HERE/'SOURCE_PLAN.json')
 if profile['name']!=NAME or profile['state'] not in ('PILOT_VALIDATION','BATCH_SOURCES_VERIFIED_PILOT_PASSED'):raise ValueError('profile registration state/version')
 if profile['name']!=NAME or episode not in profile['allowed_episodes']:raise ValueError('episode outside validated task scope')
 if sha(HERE/'SOURCE_PLAN.json')!=profile['source_plan_sha256']:raise ValueError('source plan changed')
 entry=next(r for r in plan['executions'] if r['episode']==episode)
 if entry['execution_id'] in plan['excluded_ids']:raise ValueError('restricted evaluation execution')
 native=load(HERE/'NATIVE_PROFILE.json')
 if sha(HERE/'NATIVE_PROFILE.json')!=profile['native_profile_sha256']:raise ValueError('native profile changed')
 return {'version':'1.2.0','profile_sha256':sha(HERE/'PROFILE.json'),'relative_task':'object/task_02','frames':entry['frames'],'execution_id':entry['execution_id'],'bindings':profile['source_bindings'],'geometry_index':native['mapping'],'objects':native['objects'],'surface_ids':native['surface_ids'],'shapes':native['shapes'],'optional_shapes':native['optional_shapes'],'metadata_expectations':{'global_episode_id':entry['execution_id'],'episode':episode,'seed':entry['seed'],'model_configuration_id':'497495005f5e820a10c9','task_configuration_id':'b12b2d70fe80d3547b1e','task_id':2,'suite_label':'object','task_suite':'libero_object'}}
