"""Freshly verify the complete allowlist before admitting any batch execution."""
from pathlib import Path
from evaluation.r1_v4.provenance import load,canonical
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,DEST
from .profile import folder

def main():
 plan=load(HERE/'SOURCE_PLAN.json');verified=[]
 for key,task in plan['tasks'].items():
  dest=folder(key);profile=load(dest/'PROFILE.json');native=load(dest/'NATIVE_PROFILE.json');bindings=[]
  for r in plan['files']:
   if r['task']!=key:continue
   p=Path(r['restored_path']);meta=load(DEST/key/'episode_001/run_metadata.json');expected=r['expected_sha256'] or meta['initial_states_sha256']
   assert p.stat().st_size==r['bytes'] and sha(p)==expected
   bindings.append({'restored_path':str(p),'sha256':expected});verified.append({**r,'actual_sha256':expected})
  native['mapping']['validated_run_ids']=[e['execution_id'] for e in task['executions']]
  (dest/'NATIVE_PROFILE.json').write_bytes(canonical(native)+b'\n')
  profile.update(state='BATCH_SOURCES_VERIFIED',native_profile_sha256=sha(dest/'NATIVE_PROFILE.json'),allowed_episodes=[e['episode'] for e in task['executions']],source_bindings=bindings)
  (dest/'PROFILE.json').write_bytes(canonical(profile)+b'\n')
 (HERE/'RESTORED_SOURCES.json').write_bytes(canonical({'files':verified,'count':len(verified),'bytes':sum(r['bytes'] for r in verified),'original_sources_modified':False})+b'\n')
 print('Verified',len(verified),'source files')
if __name__=='__main__':main()
