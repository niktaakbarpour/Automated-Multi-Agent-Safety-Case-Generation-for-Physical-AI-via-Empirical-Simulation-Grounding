"""Closed multi-task source registry, independently compiled per task."""
from pathlib import Path
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,DEST
PREFIX='multitask-v1:'

def folder(key):
 if key not in load(HERE/'SOURCE_PLAN.json')['tasks']:raise ValueError('unregistered task')
 return HERE/'profiles'/key.replace('/','_')

def approved_profile(name,root,episode):
 if not name.startswith(PREFIX) or Path(root).resolve()!=DEST:raise ValueError('unapproved multi-task profile/root')
 key=name[len(PREFIX):];path=folder(key);plan=load(HERE/'SOURCE_PLAN.json');p=load(path/'PROFILE.json');task=plan['tasks'][key]
 if p['name']!=name or p['state'] not in ('PILOT_VALIDATION','BATCH_SOURCES_VERIFIED'):raise ValueError('profile state/version')
 if episode not in p['allowed_episodes'] or sha(HERE/'SOURCE_PLAN.json')!=p['source_plan_sha256']:raise ValueError('episode/plan not approved')
 entry=next(r for r in task['executions'] if r['episode']==episode)
 if entry['execution_id'] in plan['excluded_ids']:raise ValueError('reserved execution')
 native=load(path/'NATIVE_PROFILE.json')
 if sha(path/'NATIVE_PROFILE.json')!=p['native_profile_sha256']:raise ValueError('native map changed')
 suite,tag=key.split('/');index=int(tag.split('_')[1]);scope=task['task_scope']
 return {'version':'1.3.0','profile_sha256':sha(path/'PROFILE.json'),'relative_task':key,'frames':entry['frames'],'execution_id':entry['execution_id'],'bindings':p['source_bindings'],'geometry_index':native['mapping'],'objects':native['objects'],'surface_ids':native['surface_ids'],'shapes':native['shapes'],'optional_shapes':native['optional_shapes'],'metadata_expectations':{'global_episode_id':entry['execution_id'],'episode':episode,'seed':entry['seed'],'model_configuration_id':entry['model_id'],'task_configuration_id':task['task']['task_id'],'task_id':index,'suite_label':suite,'task_suite':scope['canonical_suite'],'checkpoint':scope['checkpoint'],'checkpoint_revision':scope['checkpoint_revision']}}
