"""Closed production scope extension, never a synthetic bypass."""
from pathlib import Path
from evaluation.r1_v4.provenance import load
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
HERE=Path(__file__).resolve().parent
ROOT=Path('/disk/1/data/niktakbr/r1-v4-phase5c-development-evidence')
NAME='development-40:1.0.0'

def approved_profile(name,root,episode):
 if name!=NAME or Path(root).resolve()!=ROOT:raise ValueError('unsupported development profile/root')
 profile=load(HERE/'VALIDATED_SOURCE_PROFILE.json')
 if profile['profile_version']!=NAME:raise ValueError('profile version')
 for path,expected in profile['approval_bindings'].items():
  if sha(REPO/path)!=expected:raise ValueError('approval source changed:'+path)
 split=load(REPO/'reports/fall_review_v2_20261016/proposed_split.json')
 frozen={r['run_id'] for r in load(REPO/'evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json')['cases']}
 entry=profile['executions'].get(str(episode))
 if not entry or entry['execution_id'] not in split['development'] or entry['execution_id'] in set(split['held_out'])|frozen:raise ValueError('execution outside approved development scope')
 return {'bindings':profile['source_bindings'],'frames':entry['frames'],'profile_sha256':sha(HERE/'VALIDATED_SOURCE_PROFILE.json'),'version':'1.1.0'}
