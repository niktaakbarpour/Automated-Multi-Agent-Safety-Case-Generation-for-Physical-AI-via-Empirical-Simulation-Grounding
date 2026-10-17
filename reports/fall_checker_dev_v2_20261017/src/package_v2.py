"""Package focused v2 release after preservation and output-structure checks."""
import hashlib,json,sys,platform,subprocess,zipfile,gzip,shutil,importlib.metadata
from pathlib import Path

def package(root,old):
 root=root.resolve();old=old.resolve();project=root.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 prior=json.loads((root/'remote_preservation_before.json').read_text())
 prior.update(json.loads((old/'preservation_before.json').read_text()))
 changed=[n for n,h in prior.items() if not (project/n).is_file() or sha(project/n)!=h]
 if changed:raise ValueError('Prior artifact preservation mismatch: '+str(changed))
 (root/'preservation_after.json').write_text(json.dumps({'files_checked':len(prior),'changed':changed,'scope':'Reviewed development release and both ZIPs, plus original pilots and audits named in prior preservation manifest','original_recordings_opened':False,'held_out_recordings_opened':False},indent=2))
 for n in ['config.json','proposed_split.json','corrected_native_geometry_v2.json','corrected_entity_inventory_v2.json']:
  assert sha(root/n)==sha(old/n),n
 baseline=root/'baseline';baseline.mkdir(exist_ok=True)
 for n in ['summary.json','sensitivity.json']:shutil.copyfile(old/'outputs'/n,baseline/n)
 shutil.copyfile(old/'src/checker.py',baseline/'checker.py')
 shutil.copyfile(old/'runtime_provenance.json',root/'previous_runtime_provenance.json')
 split=json.loads((root/'proposed_split.json').read_text());config=json.loads((root/'config.json').read_text());s=json.loads((root/'outputs/summary.json').read_text());access=json.loads((root/'outputs/access_log.json').read_text())
 assert len(access)==40 and {a['run_id'] for a in access}==set(split['development']) and not set(split['held_out'])&{a['run_id'] for a in access}
 records=0
 for d in s['development']:
  with gzip.open(root/f"outputs/episode_{d['episode']:03d}_observations_all_profiles.json.gz",'rt') as f:obs=json.load(f)
  assert set(obs)=={'base','strict','broad'}
  for profile,objects in obs.items():
   assert set(objects)==set(config['objects'])
   for name,rows in objects.items():
    assert len(rows)==d['frames'] and [r['frame'] for r in rows]==list(range(d['frames']))
    records+=len(rows)
  for a in d['objects'].values():
   assert a['human_label'] is None and a['requirement_verdict']=='not_assessed_pending_approval'
   for e in a['events']:
    assert e['ending'] is not None and e['classification_history'] and len(e['confirmation_window'])==config['minimum_descent_intervals']
    assert all(i['both_endpoints_contact_free'] for i in e['confirmation_window'])
 for p in (root/'human_review').glob('*forms.json'):
  for f in json.loads(p.read_text()):assert f['reviewer_identity']=='' and f['decision'] is None
 assert 'Ran 42 tests' in (root/'tests-release.log').read_text() and '\nOK' in (root/'tests-release.log').read_text()
 (root/'release_checks.json').write_text(json.dumps({'software_tests':42,'tests_are_detector_validation':False,'development_runs':40,'held_out_runs_processed':0,'recorded_frames':sum(d['frames'] for d in s['development']),'object_profile_frame_records':records,'exactly_one_record_per_object_profile_frame':True,'physical_config_hash_unchanged':sha(root/'config.json'),'forms_blank':True,'original_recordings_read':False,'large_unchanged_geometry_extracts':'Not duplicated; see access_log.json and previous release'},indent=2))
 (root/'runtime_provenance.json').write_text(json.dumps({'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','h5py']},'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True).strip(),'source_dirty_status':subprocess.check_output(['git','status','--porcelain'],cwd=project,text=True),'new_source_hashes':{str(p.relative_to(root)):sha(p) for folder in ['src','tests'] for p in (root/folder).glob('*.py')},'previous_release':str(old),'physical_parameters_changed':False,'physics_stepped':False,'LLM_rerun':False,'original_recordings_opened':False,'held_out_evaluated':False,'commands':['PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v','PYTHONDONTWRITEBYTECODE=1 python src/reassess_extracts.py --root . --previous-release ../fall_checker_dev_20261017 --output outputs','PYTHONDONTWRITEBYTECODE=1 python src/report_changes.py . ../fall_checker_dev_20261017']},indent=2))
 files=[p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.b64','.pyc'] and p.name!='PACKAGE_MANIFEST.json']
 (root/'PACKAGE_MANIFEST.json').write_text(json.dumps({'release':'fall-checker-dev-v2-20261017','status':'PROVISIONAL_UNAPPROVED_UNVALIDATED','files':{str(p.relative_to(root)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}},indent=2));files.append(root/'PACKAGE_MANIFEST.json')
 zpath=root.parent/'trustworthy-fall-checker-dev-v2-20261017.zip'
 with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:z.write(p,str(p.relative_to(root)))
 with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
 print(json.dumps({'zip':str(zpath),'bytes':zpath.stat().st_size,'sha256':sha(zpath),'files':len(files)},indent=2))
if __name__=='__main__':package(Path(sys.argv[1]),Path(sys.argv[2]))
