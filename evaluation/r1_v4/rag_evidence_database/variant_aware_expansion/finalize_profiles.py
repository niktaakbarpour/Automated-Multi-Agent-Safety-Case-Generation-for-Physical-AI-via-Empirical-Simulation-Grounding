"""Freeze admitted scopes and exact external geometry artifact checksums."""
from collections import Counter,defaultdict
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,WORK,DEST
from .profile import directory

def main():
 reports=load(HERE/'PROFILE_VALIDATION_PILOT.json')+load(HERE/'PROFILE_VALIDATION_BATCH.json');assert len(reports)==147
 good=[r for r in reports if r['passed']];write_new(HERE/'ADMITTED_COHORT.json',{'cohort_sha256':sha(HERE/'COHORT.json'),'execution_ids':sorted(r['execution_id'] for r in good),'rejected':[r for r in reports if not r['passed']],'frozen_after_per_execution_validation':True})
 files=[]
 for p in sorted((WORK/'profiles').rglob('*.json')):files.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'role':'failure_diagnostic' if p.name.startswith('FAILURE') else 'verified_profile_artifact'})
 write_new(HERE/'EXTERNAL_PROFILE_ARTIFACTS.json',{'files':files,'profile_directory':str(WORK/'profiles'),'large_geometry_maps_outside_git':True})
 inventory=load(HERE/'INVENTORY.json');by={r['execution_id']:r for r in good}
 for e in inventory['executions']:
  if e['execution_id'] in by:
   r=by[e['execution_id']];e.update(xml_variant_id=r['variant_id'],variant_status='VERIFIED_XML_AND_ASSET_CONTENT',geometry_mapping_status='VERIFIED_NATIVE_MAPPING_LOGICAL_MAIN_TABLE_UNRESOLVED',indexing_eligibility='VERIFIED_FOR_DATABASE_ONLY',restored_location=str(DEST/e['partition']/f"episode_{e['episode']:03d}"),available_required_files=9)
 write_new(HERE/'INVENTORY_VERIFIED.json',inventory)
 summaries={key:{'executions':sum(r['task']==key for r in good),'variants':len({r['variant_id'] for r in good if r['task']==key}),'frames':sum(r['frames'] for r in good if r['task']==key)} for key in sorted({r['task'] for r in reports})}
 write_new(HERE/'PROFILE_SUMMARY.json',{'admitted':len(good),'rejected':len(reports)-len(good),'new_variants':len({r['variant_id'] for r in good}),'tasks':summaries,'baseline_variants':len({r['identity']['variant_id'] for r in load(WORK/'BASELINE_ENVIRONMENTS.json')}),'unresolved_remaining_payloads':1617-len(good),'logical_fixture_alias_missing':'main_table','physical_admission_enabled':False})
 print('Frozen admitted profiles',len(good),summaries,flush=True)
if __name__=='__main__':main()
