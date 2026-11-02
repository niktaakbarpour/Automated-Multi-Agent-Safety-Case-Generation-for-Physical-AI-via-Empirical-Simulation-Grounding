"""Per-execution native geometry validation, without replay or physics stepping."""
import sys
from pathlib import Path
import h5py
from evaluation.r1_v4.provenance import load,write_new,canonical
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.native import compile_profile
from evaluation.r1_v4.libero_measurement_reader.reader import read
from .plan import HERE,DEST
from .profile import PREFIX,directory
from .identity import identify

def save_checked(path,value):
 if Path(path).exists():
  if canonical(load(path))!=canonical(value):raise ValueError('existing generated artifact differs; preserve diagnostics and use a new version:'+str(path))
 else:write_new(path,value)

def validate(phase):
 cohort=load(HERE/'COHORT.json');reports=[]
 for key,task in sorted(cohort['tasks'].items()):
  for e in sorted(task['executions'],key=lambda e:e['episode']):
   if phase=='pilot' and e['episode']!=1:continue
   if phase=='batch' and e['episode']==1:continue
   folder=directory(e['execution_id']);folder.mkdir(parents=True,exist_ok=True);root=DEST/key/f"episode_{e['episode']:03d}";meta=load(root/'run_metadata.json');sources=[r for r in cohort['files'] if r['task']==key and (r['episode']==e['episode'] or r['execution_id']=='shared')];assert len(sources)==11;bindings=[]
   try:
    for r in sources:
     p=Path(r['restored_path']);expected=r['expected_sha256'] or meta['initial_states_sha256'];assert p.stat().st_size==r['bytes'] and sha(p)==expected;bindings.append({'restored_path':str(p),'sha256':expected})
    identity=identify(root/'simulator.xml',root/'simulator_asset_manifest.json');assert identity['xml_sha256']==e['expected_xml_sha256']
    with h5py.File(root/'trajectory.h5','r') as h:snapshot={n:h['frames/000000/simulator/'+n+'/value'][()] for n in ('body_xpos','body_xquat','geom_xpos','geom_xmat')}
    semantic=load(root/'semantic_initial_conditions.json')['phases'];recorded=semantic['before_settling']['fixture_initial_poses'];second=semantic['before_first_action']['fixture_initial_poses'];legacy=load(root/'simulator_index.json')
    fixture_bindings={name:recorded[name]['root_body'] for name in task['fixtures'] if name in recorded}
    if any(name not in second or second[name]['root_body']!=body or body not in legacy['body_names'] for name,body in fixture_bindings.items()):raise ValueError('fixture identity changes or missing native body')
    for obj in task['objects']:
     if semantic['before_settling']['object_initial_poses'][obj]['root_body']!=obj+'_main':raise ValueError('unsupported object root binding')
    native=compile_profile(root/'simulator.xml',root/'simulator_asset_manifest.json',root/'simulator_index.json',snapshot,task['objects'],[e['execution_id']],list(fixture_bindings.values()))
    native['logical_fixture_bindings']=fixture_bindings;native['unresolved_logical_fixtures']=sorted(set(task['fixtures'])-set(fixture_bindings))
    save_checked(folder/'NATIVE_PROFILE.json',native);save_checked(folder/'VARIANT.json',identity)
    save_checked(folder/'PROFILE.json',{'schema_version':'1.0.0','execution_id':e['execution_id'],'variant_id':identity['variant_id'],'cohort_sha256':sha(HERE/'COHORT.json'),'native_profile_sha256':sha(folder/'NATIVE_PROFILE.json'),'state':'SOURCE_VERIFIED_MEASUREMENT_ONLY','source_bindings':bindings,'empirical_admission_enabled':False})
    result=read(DEST,e['episode'],task_profile=PREFIX+key)
    if result.status!='verified_measurements' or result.synthetic:raise ValueError('reader rejected:'+str(result.diagnostics))
    if any(len(f.camera_references)!=2 for f in result.frames):raise ValueError('camera reference channel incomplete')
    report={'passed':True,'task':key,'execution_id':e['execution_id'],'variant_id':identity['variant_id'],'xml_sha256':identity['xml_sha256'],'asset_content_digest':identity['asset_content_digest'],'frames':len(result.frames),'geometry_count':native['mapping']['native_geom_count'],'object_ids':list(native['objects']),'static_fixture_geometry_ids':native['surface_ids'],'logical_fixture_bindings':fixture_bindings,'unresolved_logical_fixtures':native['unresolved_logical_fixtures'],'field_inventory':result.metadata['field_inventory'],'unsupported_fields':sorted({d.code for d in result.diagnostics}),'reader_version':result.reader_version,'source_bindings':bindings,'empirical_admission_enabled':False}
    save_checked(folder/'VALIDATION.json',report);reports.append(report);print('Verified',key,e['episode'],len(result.frames),identity['variant_id'],flush=True)
   except Exception as error:
    report={'passed':False,'task':key,'execution_id':e['execution_id'],'error_type':type(error).__name__,'reason':str(error)};write_new(folder/('FAILURE-'+str(len(list(folder.glob('FAILURE*.json')))+1)+'.json'),report);reports.append(report);print(report,flush=True)
 save_checked(HERE/('PROFILE_VALIDATION_'+phase.upper()+'.json'),reports)
 if phase=='pilot' and not all(r['passed'] for r in reports):raise SystemExit('pilot validation blocked; do not restore batch')
 return reports
if __name__=='__main__':validate(sys.argv[1])
