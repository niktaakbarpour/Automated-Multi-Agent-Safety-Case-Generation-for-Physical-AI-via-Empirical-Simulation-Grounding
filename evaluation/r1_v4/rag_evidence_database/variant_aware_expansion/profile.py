"""Closed per-execution measurement profiles; XML is never selected by task alone."""
from pathlib import Path
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,DEST,WORK
PREFIX='variant-v1:'

def entry_for(task,episode):
 cohort=load(HERE/'COHORT.json')
 if task not in cohort['tasks']:raise ValueError('task outside frozen cohort')
 entry=next((e for e in cohort['tasks'][task]['executions'] if e['episode']==episode),None)
 if entry is None or entry['execution_id'] in cohort['excluded_ids']:raise ValueError('unapproved execution')
 return cohort,cohort['tasks'][task],entry

def directory(execution):return WORK/'profiles'/execution

def approved_profile(name,root,episode):
 if not isinstance(name,str) or not name.startswith(PREFIX) or Path(root).resolve()!=DEST:raise ValueError('unapproved variant profile/root')
 key=name[len(PREFIX):];cohort,task,e=entry_for(key,episode);folder=directory(e['execution_id']);p=load(folder/'PROFILE.json');native=load(folder/'NATIVE_PROFILE.json')
 if p['cohort_sha256']!=sha(HERE/'COHORT.json') or p['execution_id']!=e['execution_id'] or p['native_profile_sha256']!=sha(folder/'NATIVE_PROFILE.json'):raise ValueError('profile source/version binding')
 if p['state']!='SOURCE_VERIFIED_MEASUREMENT_ONLY':raise ValueError('profile not verified')
 suite,tag=key.split('/');scope=task['task_scope']
 return {'version':'1.4.0','profile_sha256':sha(folder/'PROFILE.json'),'relative_task':key,'frames':e['frames'],'execution_id':e['execution_id'],'bindings':p['source_bindings'],'geometry_index':native['mapping'],'objects':native['objects'],'surface_ids':native['surface_ids'],'shapes':native['shapes'],'optional_shapes':native['optional_shapes'],'metadata_expectations':{'global_episode_id':e['execution_id'],'episode':episode,'seed':e['seed'],'model_configuration_id':e['model_id'],'task_configuration_id':task['task']['task_id'],'task_id':int(tag.split('_')[1]),'suite_label':suite,'task_suite':scope['canonical_suite'],'checkpoint':scope['checkpoint'],'checkpoint_revision':scope['checkpoint_revision']}}
