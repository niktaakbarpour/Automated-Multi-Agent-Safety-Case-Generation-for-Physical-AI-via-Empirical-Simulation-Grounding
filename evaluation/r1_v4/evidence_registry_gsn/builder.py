"""Build compact development metadata through the verified measurement reader."""
from pathlib import Path
from dataclasses import replace
import hashlib
from evaluation.r1_v4.provenance import load,digest
from evaluation.r1_v4.libero_measurement_reader.reader import read,MAP
from evaluation.r1_v4.libero_measurement_reader.bridge import observations
from .adapter import typed_observation
from .models import Record

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ROOT=Path('/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence')

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def build(registry):
 result=read(ROOT,0,[9,10,11])
 if result.status!='verified_measurements':raise ValueError('reader rejected source: '+str(result.diagnostics))
 meta=result.metadata;h5=result.source_hashes['trajectory.h5'];typed={e.id:typed_observation(e) for e in observations(result)}
 base=dict(schema_version='1.0.0',requirement_id='R1',requirement_version='2.0.0',execution_id=result.execution_id,object_id='cream_cheese_1',kind='document',source_path=str(MAP),source_sha256=sha(MAP),selector='/geometries',measurement_type='native_mapping',validation_status='verified_source',capability={'source_identity':'VERIFIED'},clock='saved_frame_index',domain='frame',interval=(9,11),coordinate_frame='MuJoCo_world',model_checkpoint=meta['checkpoint']+'@'+meta['checkpoint_revision'],benchmark=meta['task_suite'],task_id=meta['task_configuration_id'],producer='libero-measurement-reader:1.0.0',original=False,uncertainty=('Physical geometry uncertainty and cache phase remain uncalibrated.',),limitations=('No support, fall or negative witness admitted.',),provenance={'reader_binding':result.reader_binding,'registry_builder_version':'1.0.0','registry_code_binding':{n:sha(HERE/n) for n in ('builder.py','models.py','registry.py','retrieval.py','gsn.py','adapter.py')},'native_count':161,'includes_anonymous_geometry':True,'physical_truth':'U','development_only':True,'requirement_spec_sha256':sha(REPO/'requirements/r1_generalized_v2/R1_V2_SPECIFICATION.md'),'gate_snapshot_sha256':sha(HERE.parent/'evidence_review_readiness/UPDATED_EVIDENCE_GATES.csv')})
 mapping=Record(**base).validate()
 run=result.source_hashes['run_metadata.json']
 metadata=replace(mapping,source_path=run['path'],source_sha256=run['sha256'],selector='/',measurement_type='execution_metadata',original=True,dependencies=())
 records=[mapping,metadata]
 for snapshot in result.frames:
  frame=snapshot.index;bind=snapshot.object_bindings['cream_cheese_1']
  for kind,selector,quantity in [
   ('object_pose',f'/frames/{frame:06d}/simulator/body_xpos/value[22];body_xquat/value[22]','simulator:body_xpos'),
   ('native_geometry',f'/frames/{frame:06d}/simulator/geom_xpos/value[10:16,104];geom_xmat/value[10:16,104]; static BOX dimensions via native_mapping dependency','simulator:geom_xpos'),
   ('contact',f'/frames/{frame:06d}/simulator/contacts @json; filter native owner body_id=22','simulator:ncon'),
   ('timestamp',f'/frames/{frame:06d}/simulator/time/value','simulator:time'),
   ('camera_reference',f'/frames/{frame:06d}/raw_observation/{{agentview_image,robot0_eye_in_hand_image}}/value',None)]:
   cap={'measurement_availability':'VERIFIED','physical_support':'BLOCKED_ON_EVIDENCE','physical_fall':'BLOCKED_ON_EVIDENCE'}
   if kind=='native_geometry':cap['geometry_admission']='CONDITIONALLY_SUPPORTED'
   if kind=='camera_reference':cap['exposure_alignment']='UNSUPPORTED'
   prov={**base['provenance'],'source_metadata_id':metadata.id,'native_binding':{k:bind[k] for k in ('body_id','collision_geom_ids','pose_phase')},'recorded_endpoint_time':snapshot.endpoint_time,'host_timestamps':snapshot.host_timestamps,'source_selector_scope':'Selected object view; full native source retained; camera references show scene, not an object detection.'}
   if quantity:
    e=typed[f'{result.execution_id}:frame:{frame}:{quantity}'];prov['v4_observation_digest']=digest(e);prov['v4_truth']=e['truth'];prov['v4_evidence_schema_version']='1.0.0'
   if kind=='camera_reference':prov['camera_references']=list(snapshot.camera_references)
   records.append(Record(**{**base,'kind':'raw_measurement','source_path':h5['path'],'source_sha256':h5['sha256'],'selector':selector,'measurement_type':kind,'validation_status':'verified_measurement','capability':cap,'interval':(frame,frame),'original':True,'dependencies':(mapping.id,metadata.id),'provenance':prov,'coordinate_frame':'camera_pixel_axes_unverified' if kind=='camera_reference' else 'MuJoCo_world'}).validate())
 review=HERE.parent/'evidence_review_readiness/AI_REFERENCE_REVIEWS.csv'
 records.append(Record(**{**base,'kind':'ai_reference_judgment','producer':'phase2b4:exposed_ai_review','source_path':str(review),'source_sha256':sha(review),'selector':'CSV candidate_id=C01','measurement_type':'ai_interpretation','validation_status':'provisional','capability':{'independent_physical_reference':'BLOCKED_ON_EVIDENCE'},'dependencies':tuple(r.id for r in records),'provenance':{'producer':'One exposed AI review; no independent human ground truth','development_only':True,'physical_truth':'U'}}).validate())
 registry.add(records)
 return {'reader_status':result.status,'execution_id':result.execution_id,'source_hashes':result.source_hashes,'records':len(records),'synthetic':False,'empirical_admission_enabled':False}
