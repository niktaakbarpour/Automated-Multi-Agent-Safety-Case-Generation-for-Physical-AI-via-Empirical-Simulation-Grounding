"""Read-only development export audit; never issues physical verdicts."""
import csv,gzip,hashlib,itertools,json,math,socket,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BASE='c98a2b81e125bc60b6062b21eebdb75c426e30db'
ORIGINAL=Path('/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero')
SAMPLE=(0,1,2,14)
V2='reports/fall_review_v2_20261016/'
def load(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def csvwrite(p,rows):
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def bounds(frame,g):
 i=g['native_geom_id'];pos=frame['geom_xpos'][i];rot=frame['geom_xmat'][i]
 if len(rot)==9:rot=[rot[j:j+3] for j in (0,3,6)]
 pts=[[pos[a]+sum(rot[a][b]*sgn[b]*g['size'][b] for b in range(3)) for a in range(3)] for sgn in itertools.product((-1,1),repeat=3)]
 return [[min(p[a] for p in pts) for a in range(3)],[max(p[a] for p in pts) for a in range(3)]]
def main():
 assert socket.gethostname().lower()=='hestia'
 assert ROOT.is_relative_to('/disk/1/data/niktakbr')
 assert ORIGINAL.resolve().is_relative_to('/disk/1/data/niktakbr')
 sources={}
 def source(n):
  p=ROOT/n;h=sha(p)
  assert hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)).hexdigest()==h,n
  sources[n]={'sha256':h,'bytes':p.stat().st_size,'baseline_identical':True};return p
 split=load(source(V2+'proposed_split.json'))
 frozen=load(source('evaluation/r1_v3_human_validation_20/COORDINATOR_ASSIGNMENTS.json'))
 excluded={r['run_id'] for r in frozen['cases']}|set(split['held_out'])
 runs=load(source('data/runs.json'))['records']
 index=load(source(V2+'corrected_native_geometry_v2.json'))
 geoms=index['geometries'];assert [g['native_geom_id'] for g in geoms]==list(range(161))
 constraints=load(source(V2+'constraints_and_identities.json'))
 assert sha(source('evidence/geometry_v2/simulator.xml'))==index['source_xml_sha256']
 for n in ['data/tasks.json',V2+'example_manifest.json','evidence/task_definitions/2448c758145ae5ad500f.bddl','data/requirement_inputs/v2-confirmed/provenance.json',V2+'measurement_findings_v2.md',V2+'targeted_measurements.json',V2+'initial_sites_vs_collision_geometry.json',V2+'prepolicy_static_endpoint_geometry.json',V2+'source_provenance.json','reports/fall_review_20261016/measurement_audit.md','evaluation/r1_v3/execute.py','evaluation/r1_v3/r1_checker.py','evaluation/r1_v3_generalization/V4_PROPOSALS.md','requirements/r1_generalized_v2/EVIDENCE_CONTRACT.md','requirements/r1_generalized_v2/FALL_DEFINITION.md']:
  source(n)
 for n in ['run_oft.py','recording_base.py','semantic_scene.py']:
  p=source('reports/fall_review_20261016/source_evidence/'+n)
  expected=next(x['sha256'] for x in load(ROOT/(V2+'source_provenance.json')) if x['copy']==n)
  assert sha(p)==expected
 assert sha(ROOT/'evidence/task_definitions/2448c758145ae5ad500f.bddl')=='2e661058917f683a25bce480015197f0a2c1911bcbc2b9dd9d947199069c9618'
 selected=[];restore=[];summaries=[];objectrows=[];surfacerows=[]
 for ep in SAMPLE:
  r=next(r for r in runs if r['suite']=='long' and r['benchmark_task_id']==0 and r['episode']==ep)
  rid=r['run_id'];assert rid in split['development'] and rid not in excluded
  trajectory=r['evidence']['trajectory'];raw=ORIGINAL/trajectory['source_relative_path']
  assert not raw.is_symlink()
  if raw.exists():raise RuntimeError('Original restored: review protocol before raw inspection')
  n=f'reports/fall_checker_dev_20261017/outputs/episode_{ep:03d}_geometry_contacts.json.gz'
  p=source(n);frames=json.loads(gzip.decompress(p.read_bytes()))
  expected_count=r['available_measurements']['root_groups']['frames']
  assert len(frames)==expected_count
  assert [f['frame'] for f in frames]==list(range(expected_count))
  for f in frames:
   assert f['run_id']==rid and f['hdf5_frame']==f"{f['frame']:06d}"
   assert len(f['geom_xpos'])==len(f['geom_xmat'])==161
   assert all(math.isfinite(x) for p in f['geom_xpos'] for x in p)
   assert all(math.isfinite(x) for rot in f['geom_xmat'] for row in (rot if isinstance(rot[0],list) else [rot]) for x in row)
   assert all(0<=c[k]<161 for c in f['contacts'] for k in ('geom1','geom2'))
   assert all(math.isfinite(c['dist']) and all(math.isfinite(x) for x in c['pos']) for c in f['contacts'])
   assert f['identity_guard']['position_error_m']<=f['identity_guard']['position_arithmetic_allowance_m']
   assert f['identity_guard']['rotation_component_error']<=f['identity_guard']['rotation_arithmetic_allowance']
   if f['frame'] in range(1,11):assert f['stage']=='settling'
   if f['frame']>=11:assert f['control_step']==f['frame']-11
  deltas=[b['time']-a['time'] for a,b in zip(frames,frames[1:])]
  roots=[g for g in geoms if 'living_room_table' in g['body_ancestry'] and g['collision_capable']]
  assert [g['native_geom_id'] for g in roots]==list(range(10,16))
  for obj,info in constraints['objects'].items():
   gs=[geoms[i] for i in info['collision_geom_ids']];assert all(g['type']=='mjGEOM_BOX' for g in gs)
   assert all(g['owner_body_id']==info['body_id'] for g in gs)
   ids=set(info['collision_geom_ids']);cs=[c for c in frames[10]['contacts'] if c['geom1'] in ids or c['geom2'] in ids]
   bb=[bounds(frames[10],g) for g in gs]
   partners=sorted({c['geom2'] if c['geom1'] in ids else c['geom1'] for c in cs})
   objectrows.append(dict(run_id=rid,object_id=obj,body_id=info['body_id'],collision_geom_ids=json.dumps(sorted(ids)),shape='BOX_union',frame=10,min_z=min(b[0][2] for b in bb),max_z=max(b[1][2] for b in bb),contact_partner_ids=json.dumps(partners),support_status='BLOCKED_ON_EVIDENCE',reason='No calibrated load-bearing or boundary inference profile',source=n,source_sha256=sha(p)))
  for g in roots:
   i=g['native_geom_id'];stationary=all(f['geom_xpos'][i]==frames[0]['geom_xpos'][i] and f['geom_xmat'][i]==frames[0]['geom_xmat'][i] for f in frames)
   assert stationary
   surfacerows.append(dict(run_id=rid,surface_id='living_room_table',geom_id=i,type=g['type'],half_sizes=json.dumps(g['size']),frame10_bounds=json.dumps(bounds(frames[10],g)),exact_static_in_saved_export=stationary,capability='CONDITIONALLY_SUPPORTED',source=n,source_sha256=sha(p)))
  selected.append(dict(run_id=rid,episode=ep,seed=r['seed'],split='historical_development',original_trajectory=str(raw),expected_original_sha256=trajectory['expected_sha256'],expected_original_bytes=trajectory['bytes'],original_present=False,original_inspected=False,preserved_export=n,export_sha256=sha(p),export_frames=len(frames),model_configuration_id=r['source_model_configuration_id'],task_id=r['task_id'],selection_reason={0:'setup flight and initial support context',1:'ordinary configuration and occlusion',2:'setup departure before monitoring',14:'handling and release diagnostic'}[ep]))
  summaries.append(dict(run_id=rid,frames=len(frames),first_time=frames[0]['time'],last_time=frames[-1]['time'],min_saved_interval_s=min(deltas),max_saved_interval_s=max(deltas),max_reported_position_recomposition_error_m=max(f['identity_guard']['position_error_m'] for f in frames),max_reported_rotation_recomposition_error=max(f['identity_guard']['rotation_component_error'] for f in frames),contacts=sum(len(f['contacts']) for f in frames),phase_status='inherited nominal lag; uncalibrated',raw_ncon_available=False,physical_conclusion=None))
  for item in r['execution_files']:
   if item['name'] in {'trajectory.h5','run_metadata.json','simulator.xml','simulator_index.json','integrity_manifest.json','completion.json','semantic_initial_conditions.json','evaluator_version.json','simulator_asset_manifest.json'}:
    restore.append(dict(run_id=rid,path=str(ORIGINAL/item['source_relative_path']),bytes=item['bytes'],expected_sha256=(item['producer_integrity'] or {}).get('sha256'),hash_status='historical expectation; not fresh verification',purpose='raw identity/format/geometry/clock regeneration'))
  for key in ('task_definition','completion','integrity_manifest'):
   item=r['evidence'][key]
   restore.append(dict(run_id=rid,path=str(ORIGINAL/item['source_relative_path']),bytes=item['bytes'],expected_sha256=item['sha256'],hash_status='historical expected bytes',purpose=key))
 restore.append(dict(run_id='shared_task00',path=str(ORIGINAL/'long/task_00/benchmark_initial_states.init'),bytes=None,expected_sha256=None,hash_status='resolve from restored run_metadata initial_states_sha256 before transfer',purpose='independent initial-state archive provenance; conditional restoration'))
 availability=[]
 for item in {r['path']:r for r in restore}.values():
  q=Path(item['path']);assert q.resolve().is_relative_to(ORIGINAL.resolve()) and not q.is_symlink()
  availability.append(dict(path=str(q),present=q.is_file(),current_bytes=q.stat().st_size if q.is_file() else None,expected_sha256=item['expected_sha256'],fresh_sha256=None))
 save(HERE/'ORIGINAL_AVAILABILITY.json',availability)
 csvwrite(HERE/'DEVELOPMENT_SAMPLE_MANIFEST.csv',selected)
 csvwrite(HERE/'OBJECT_GEOMETRY_AUDIT.csv',objectrows);csvwrite(HERE/'SURFACE_GEOMETRY_AUDIT.csv',surfacerows)
 save(HERE/'SOURCE_BINDINGS.json',sources);save(HERE/'MEASUREMENT_SUMMARY.json',summaries);save(HERE/'SELECTIVE_RESTORATION.json',restore)
 save(HERE/'SAMPLE_VALIDATION.json',dict(original_recordings_inspected=0,development_exports_inspected=len(selected),export_frames_inspected=sum(r['export_frames'] for r in selected),excluded_run_count=len(excluded),all_selected_in_development=True,overlap_with_frozen_or_heldout=0,original_hashes_freshly_verified=0,source_files_baseline_verified=len(sources),empirical_admission_enabled=False,physical_verdicts_issued=0))
 print(json.dumps(load(HERE/'SAMPLE_VALIDATION.json')))
if __name__=='__main__':main()
