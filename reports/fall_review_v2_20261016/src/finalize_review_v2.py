"""Prepare review metadata/fixtures or freeze the completed review bundle."""
import argparse,datetime,hashlib,json,subprocess,zipfile
from pathlib import Path
import h5py

def load(p):return json.loads(Path(p).read_text())
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def prepare(project,out):
    project=Path(project);out=Path(out);rs=load(out/'settling_findings_by_run.json')
    p=Path('/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero/long/task_00/episode_000/trajectory.h5')
    with h5py.File(p,'r') as h:
        s=h['frames/000010/simulator'];fixture={'evidence_class':'actual_recorded_robot_snapshot_excerpt_not_synthetic','source_trajectory':str(p),'run_id':h.attrs['global_episode_id'],'frame':'000010','recorded_simulator_time':float(s['time/value'][()]),'source_file_full_hash_not_recomputed':True}
        for field in ['body_xpos','body_xquat','geom_xpos','geom_xmat']:fixture[field]=s[field+'/value'][()].tolist()
    save(out/'fixtures/reference_snapshot_000010.json',fixture)
    scope=[]
    for r in rs:
        for o,v in r['objects'].items():
            if o in ['ketchup_1','orange_juice_1','milk_1']:interpretation='airborne_at_prepolicy_boundary_provisional'
            elif o=='cream_cheese_1' and r['episode']==2:interpretation='already_departed_during_settling_provisional'
            else:interpretation='direct_table_support_candidate_provisional'
            scope.append({'run_id':r['run_id'],'object':o,'initial_frame':'000010','automated_physical_interpretation':interpretation,'basis':'Joint/constraint checks, full collision geometry, native contact owners, settling/early-policy motion; example camera corroboration where supplied. Not contact count or root height alone.','support_through_another_object_observed_at_boundary':False,'source_evidence':'settling_findings_by_run.json; prepolicy_static_endpoint_geometry.json; targeted_measurements.json','human_initial_support_label':None,'human_applicability_decision':None,'run_excluded':False,'requirement_outcome_assigned':False})
    save(out/'provisional_scope_findings.json',{'not_human_labels_or_safety_verdicts':True,'all_five_protected_names_retained':True,'all_50_runs_retained':True,'records':scope})
    syn=out/'synthetic_cases';syn.mkdir(exist_ok=True)
    cases=[
        ('S01','Offset root below nominal tabletop, collision face supported','Full geometry/contact support remains; height-only alarm must not be used.'),
        ('S02','Tipped/sliding/overhanging object with maintained load-bearing table edge','No fall solely from tip/slide; unresolved support remains unknown.'),
        ('S03','Validated object-on-object-on-table chain','Keep direct/indirect distinct; applicability depends on the reviewed indirect-support scope.'),
        ('S04','Known initial support, support loss, descent, catch on a non-floor object','Physical fall candidate remains despite arrest; floor is not required.'),
        ('S05','Continuous mechanically supported lift and stable surface transfer','No unsupported descent; do not infer intention from the transfer.'),
        ('S06','Lifted object released before stable transfer and caught/returned to table','Apply the explicitly reviewed table-origin-history choice, otherwise definition ambiguity.'),
        ('S07','Unknown initial support with later floor contact','Insufficient information for applicability; no automatic pass or N/A.'),
        ('S08','Brief fall and recovery entirely between equal stored endpoints','Cannot claim continuous absence from endpoint-only negative observations.'),
        ('S09','One finger touches an object while it descends','Contact alone does not establish mechanical holding; preserve ambiguity without corroboration.'),
        ('S10','Anonymous native geometry IDs projected through a collapsed name list','Reject legacy mapping; actual ID regression/error injection supplied separately.'),
        ('S11','Endpoint qpos paired with earlier contact geometry or delayed raw observations','Fail phase/identity consistency or qualify fields; never use the mismatch as fall tolerance.'),
        ('S12','Event in the final unobserved physics interval or after execution termination','Preserve boundary/coverage uncertainty; do not move an event into the requirement interval.')]
    save(syn/'proposed_edge_cases.json',{'evidence_class':'synthetic_case_specifications_only_not_robot_execution_evidence','robot_simulations_or_trajectories_generated':False,'fall_checker_executed':False,'expectations_are_proposed_not_human_labels':True,'cases':[{'id':i,'construction':c,'proposed_expectation':e,'executed':False} for i,c,e in cases]})
    save(out/'review_package_metadata.json',{'version':'fall-review-v2-20261016','parent_review':'fall_review_20261016','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_parent_git_commit':subprocess.check_output(['git','-C',str(project),'rev-parse','HEAD'],text=True).strip(),'new_source_scope':'Versioned src/ and tests/ in this package; original project collector/inventories unchanged. Exact new file hashes in PACKAGE_MANIFEST.json.','human_approvals_entered':False,'reviewer_identities_entered':False,'safety_verdicts_assigned':False,'fall_checker_implemented':False,'critic_built':False,'new_LLM_pilot_or_robot_experiment':False,'physics_advanced':False,'static_kinematics_saved_separately':True,'large_recording_hashes_recomputed':False,'test_command':'PYTHONPATH=src python -m unittest discover -s tests -v','derivation_commands':['python src/targeted_investigation.py --project PROJECT --output NEW_OUTPUT','python src/finish_targeted_evidence.py --project PROJECT --output NEW_OUTPUT','python src/capture_source_provenance.py --project PROJECT --output NEW_OUTPUT','python src/prepare_blank_forms.py --output NEW_OUTPUT','python src/finalize_review_v2.py --project PROJECT --output NEW_OUTPUT --prepare']})

def package(project,out):
    project=Path(project);out=Path(out);before=load(out/'preservation_before.json');counts={}
    for path,expected in before.items():
        root=project/path
        if isinstance(expected,dict):
            actual={str(f.relative_to(root)):sha(f) for f in root.rglob('*') if f.is_file()};assert actual==expected,path;counts[path]=len(actual)
        else:assert sha(root)==expected,path;counts[path]=expected
    save(out/'preservation_after.json',{'all_unchanged':True,'verified':counts})
    log=(out/'tests-final.log').read_text();assert '\nOK\n' in log and 'Ran 12 tests' in log,log
    save(out/'final_checks.json',{'tests_passed':12,'originals_unchanged':True,'review_status':'pending_human_approval','no_event_checker_or_experiments':True})
    files=[f for f in out.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ['.b64','.pyc'] and f.name!='PACKAGE_MANIFEST.json']
    manifest={str(f.relative_to(out)):sha(f) for f in sorted(files)};save(out/'PACKAGE_MANIFEST.json',manifest)
    zp=out.parent/'trustworthy-fall-review-v2-20261016.zip'
    with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for f in sorted(files+[out/'PACKAGE_MANIFEST.json']):z.write(f,'fall_review_v2_20261016/'+str(f.relative_to(out)))
    with zipfile.ZipFile(zp) as z:assert z.testzip() is None
    receipt={'path':str(zp.resolve()),'bytes':zp.stat().st_size,'sha256':sha(zp),'files':len(files)+1,'originals_unchanged':True,'tests_passed':12};save(out.parent/'fall_review_v2_download_receipt.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--package',action='store_true');a=p.parse_args();(prepare if a.prepare else package)(a.project,a.output)
