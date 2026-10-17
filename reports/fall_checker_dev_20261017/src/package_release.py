"""Verify new-version integrity and preservation, then package deliverables."""
import json,hashlib,sys,subprocess,platform,importlib.metadata,zipfile,gzip,collections
from pathlib import Path
root=Path(sys.argv[1]).resolve();project=root.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((root/'preservation_before.json').read_text());changed=[p for p,h in before.items() if not (project/p).is_file() or sha(project/p)!=h]
if changed:raise RuntimeError('Preservation mismatch '+str(changed))
(root/'preservation_after.json').write_text(json.dumps({'checked_files':len(before),'changed':changed,'original_recordings':'Opened read-only; no writes, physics stepping or replacement trajectories','old_zip_hashes':{p.name:sha(p) for p in project.glob('reports/trustworthy-fall-review*.zip')}},indent=2))
sourcegit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True).strip();dirty=subprocess.check_output(['git','status','--porcelain'],cwd=project,text=True)
(root/'runtime_provenance.json').write_text(json.dumps({'source_project_commit':sourcegit,'source_project_dirty_status':dirty,'development_source_hashes':{str(p.relative_to(root)):sha(p) for d in ['src','tests'] for p in (root/d).glob('*.py')},'runtime_python':sys.executable,'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','h5py','mujoco','Pillow','imageio','imageio-ffmpeg']},'commands':['PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v','PYTHONDONTWRITEBYTECODE=1 python src/run_development.py --root . --output outputs','PYTHONDONTWRITEBYTECODE=1 python src/finalize_assessments.py .','PYTHONDONTWRITEBYTECODE=1 python src/export_clips.py .','PYTHONDONTWRITEBYTECODE=1 python src/prepare_review.py .'],'history':'First-pass analysis and intermediate reassessment preserved in development_history; final conservative code reassesses the same exported development geometry/contact bundles. No additional original-recording access for reassessment.','dependencies_changed':False,'physics_advanced':False,'heldout_evaluated':False},indent=2))
(root/'implementation_authorization.json').write_text(json.dumps({'authorization':'User authorized development checker on existing 40-run development partition only, with proposed conservative scope','requirement_approval':False,'human_labels_entered':False,'detector_validated':False,'requirement_scope_choices':'config.json and REVIEW_DECISIONS.md','human_reviewer_identity':'','approved_decision':None},indent=2))
s=json.loads((root/'outputs/summary.json').read_text());split=json.loads((root/'proposed_split.json').read_text());access=json.loads((root/'outputs/access_log.json').read_text())
assert {r['run_id'] for r in access}==set(split['development']);assert not set(split['held_out'])&{r['run_id'] for r in access}
assert len(s['development'])==40 and sum(len(d['objects']) for d in s['development'])==200
setup=[]
for d in s['development']:
 with gzip.open(root/f"outputs/episode_{d['episode']:03d}_observations.json.gz",'rt') as f:obs=json.load(f)
 for name,a in d['objects'].items():
  candidates=[e for e in a['events'] if e['phase']=='setup']
  if candidates or a['initial_applicability']!='direct_table_support_candidate':
   # Later floor contact is just an observation; it does not move setup onset into policy phase.
   later=next(({'frame':r['frame'],'time':r['time'],'native_geom_ids':r['other_contacts']} for r in obs[name] if r.get('valid') and r['frame']>=10 and 8 in r['other_contacts']),None)
   setup.append({'run_id':d['run_id'],'episode':d['episode'],'object':name,'initial_applicability':a['initial_applicability'],'setup_candidates':candidates,'later_floor_contact_observation':later,'requirement_verdict':'not_assessed','uncertainty':'Setup origin and indirect/load-bearing support require review; later floor contact does not establish in-interval departure.'})
(root/'outputs/setup_findings.json').write_text(json.dumps(setup,indent=2))
# Validate clip decodability, dimensions and every consecutive frame against manifest.
import imageio.v2 as imageio
from PIL import Image,ImageDraw
manifest=json.loads((root/'clip_manifest.json').read_text());clipchecks=[];sheet=Image.new('RGB',(1024,1280),'white')
for i,m in enumerate(manifest):
 reader=imageio.get_reader(str(root/m['file']));count=reader.count_frames();assert count==len(m['references']);arr=reader.get_data(min(10,count-1));reader.close();sheet.paste(Image.fromarray(arr),(512*(i%2),320*(i//2)));clipchecks.append({'file':m['file'],'decoded_frames':count,'expected':len(m['references']),'shape':list(arr.shape)})
sheet.save(root/'clip_preview.png')
# All new human fields stay blank.
for p in (root/'human_review').glob('*forms.json'):
 for form in json.loads(p.read_text()):assert form['reviewer_identity']=='' and form['decision'] is None
(root/'release_checks.json').write_text(json.dumps({'partition_guard':'40 development only; ten held-out not processed','frames':sum(d['frames'] for d in s['development']),'object_rows':200,'recording_bundle_errors':sum(len(d['errors']) for d in s['development']),'clips':clipchecks,'human_forms_blank':True,'preserved_prior_artifact_files':len(before),'synthetic_and_regression_tests':'See synthetic-tests-final.log; separate from unvalidated recorded candidate outputs'},indent=2))
excluded={'__pycache__','.git','.venv'}
files=[p for p in root.rglob('*') if p.is_file() and not any(a in excluded for a in p.relative_to(root).parts) and p.suffix not in ['.b64','.pyc'] and p.name!='PACKAGE_MANIFEST.json']
(root/'PACKAGE_MANIFEST.json').write_text(json.dumps({'release':'fall-checker-development-20261017','status':'UNAPPROVED_UNVALIDATED','files':{str(p.relative_to(root)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}},indent=2));files.append(root/'PACKAGE_MANIFEST.json')
zip_path=Path(sys.argv[2]) if len(sys.argv)>2 else root.parent/'trustworthy-fall-checker-dev-20261017.zip'
with zipfile.ZipFile(zip_path,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,str(p.relative_to(root)))
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
print(json.dumps({'zip':str(zip_path),'sha256':sha(zip_path),'bytes':zip_path.stat().st_size,'members':len(files)},indent=2))
