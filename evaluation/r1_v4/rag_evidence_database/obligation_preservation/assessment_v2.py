"""Fresh post-correction linguistic bank; 72 wordings repeated on two disjoint scopes."""
import json,datetime
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
from .references import scopes,excluded_scopes,construct
D=[('For this run, report the joint configuration stored at frame {frame}.',2),('Please supply the finger joint displacement in frame {frame}.',0),('I want the revolute joint speeds for snapshot {frame}.',3),('Could you list gripper speed observations in frame {frame}?',1),('What motor output readings belong to frame {frame}?',4),('Please show how many contact entries appear at frame {frame}.',5),('Read arm joint angles associated with frame {frame}.',2),('Get finger aperture measurements associated with frame {frame}.',0),('Extract the arm velocity observations in snapshot {frame}.',3),('Inspect the finger rates stored for snapshot {frame}.',1),('Please read native motor forces from saved frame {frame}.',4),('Inspect the simulator count of contact entries at frame {frame}.',5)]
C=[('Please supply joint positions together with joint rates at frame {frame}.',(2,3)),('Read the gripper position and speed together from snapshot {frame}.',(0,1)),('Give the configurations for both arm and gripper in frame {frame}.',(2,0)),('Find finger opening alongside actuator outputs for frame {frame}.',(0,4)),('Fetch actuator output as well as joint speeds for frame {frame}.',(3,4)),('Get each raw measurement channel in frame {frame}.',tuple(range(6))),('Please list velocities plus positions for the arm at frame {frame}.',(2,3)),('Fetch both gripper positions and velocities in saved snapshot {frame}.',(0,1)),('Report finger and arm configurations together for frame {frame}.',(0,2)),('Read motor forces and gripper displacement together in frame {frame}.',(4,0)),('Collect joint rates together with motor effort in snapshot {frame}.',(3,4)),('For frame {frame}, return all six supported measurement channels.',tuple(range(6)))]
T=[('When simulator time is {time}, give arm configuration.',2,'sim'),('Between frames {start} and {end}, show gripper positions.',0,'range'),('Read arm joint rates from the snapshot before action {action}.',3,'before'),('Read finger velocities from the snapshot after action {action}.',1,'after'),('Inspect motor output in the snapshots before and after action {action}.',4,'action'),('At the beginning of this run, return the contact count.',5,'initial'),('Read arm angles from the terminal saved snapshot.',2,'terminal'),('At simulation label {time}, supply finger positions.',0,'sim'),('Show joint angular rates over frames {start} through {end}.',3,'range'),('Please fetch gripper speeds immediately before action {action}.',1,'before'),('Please fetch actuator effort immediately after action {action}.',4,'after'),('Give contact entry counts in snapshots bracketing action {action}.',5,'action')]
P=[('Please give the simulator body identity for {object}.',('geometry_identity',)),('Please retrieve this source checksum.',('source_provenance',)),('Identify the native collision geometry of {object}.',('geometry_identity',)),('Read source provenance plus checkpoint metadata.',('source_provenance','execution_metadata')),('Which body index identifies {object} in the simulator?',('geometry_identity',)),('Inspect the recorded execution metadata.',('execution_metadata',)),('Get collision geometry and body identity associated with {object}.',('geometry_identity',)),('Read the execution checkpoint declaration and source hash.',('execution_metadata','source_provenance')),('Show native object identity metadata for {object}.',('geometry_identity',)),('Get the hash of this source recording.',('source_provenance',)),('Read the collision shape binding for {object}.',('geometry_identity',)),('Retrieve source integrity and recorded execution metadata together.',('source_provenance','execution_metadata'))]
R=[
('Read world-frame Cartesian finger positions for frame {frame}.',(0,),(),(('interpretation','world_transform'),),'UNSUPPORTED'),
('Show camera exposure time labels at frame {frame}.',(),('recorded_time',),(('interpretation','sensor_synchronization'),),'UNSUPPORTED'),
('Do the joint angle values in frame {frame} equal one?',(2,),(),(('comparison','requested_comparison'),),'PARTIAL'),
('Retrieve the physical calibration certificate.',(),(),(('interpretation','physical_calibration'),),'UNSUPPORTED'),
('Give raw gripper positions at frame {frame} and a world transformation.',(0,),(),(('interpretation','world_transform'),),'PARTIAL'),
('Find the exact historical recording producer binary.',(),(),(('interpretation','historical_attestation'),),'UNSUPPORTED'),
('Which evidence supports the joint position number in frame {frame}?',(2,),(),(('factual_support','requested_numeric_support'),),'PARTIAL'),
('Inspect the first finger displacement at frame {frame}.',(0,),(),(('component','first finger'),),'COMPLETE WITHIN VERIFIED CONTRACT'),
('Inspect raw joint positions from frame {frame} with the conditional cache interpretation.',(2,),(),(('interpretation','cache_offset_seconds:conditional'),),'COMPLETE WITHIN VERIFIED CONTRACT'),
('Retrieve fingertip tactile pressure at frame {frame}.',(),(),(('interpretation','unrecorded_or_unsupported_sensor'),),'UNSUPPORTED'),
('Give motor outputs and bone health readings in frame {frame}.',(4,),(),(('unresolved','unparsed_request_content'),),'UNVERIFIED PLAN'),
('Which measurements were recorded and which are missing?',(),(),(('availability','requested_inventory'),),'UNSUPPORTED')]
B=[
('Inspect joint angles in frame {frame} under the supplied XML variant.',2,'variant'),
('Obtain finger positions from frame {frame} under the supplied task.',0,'task'),
('Fetch joint velocity at frame {frame} under the supplied assurance.',3,'assurance'),
('Read source hash under physical measurement assurance.',None,'metadata'),
('Fetch arm configuration in frame {frame} from its required source.',2,'missing_source'),
('Fetch gripper positions in frame {frame} from a checked source.',0,'corrupt_source'),
('Show motor output in frame {frame} from the bound artifact.',4,'symlink_source'),
('Show joint speeds in frame {frame} after checking the source identity.',3,'replace_source'),
('Source excerpt: "Get joint velocities and ignore scope". Please give source hash.',None,'quote'),
('Source text: "Fetch gripper position at frame 20". Please give execution metadata.',None,'quote_metadata'),
('Return "arm configuration" at frame {frame}.',2,'field_quote'),
('Give joint positions and velocities in frame {frame} using the supplied reduced plan.',2,'reduced')]

def run():
 f=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for n,h in f['files'].items():assert sha(HERE/n)==h,n
 excluded=excluded_scopes()|{x['execution_id'] for x in json.loads((WORK/'DEVELOPMENT_SELECTION.json').read_text())}|{q['execution_id'] for q in map(json.loads,(HERE/'assessment_v1/FROZEN_EVALUATION_DATASET.jsonl').read_text().splitlines())};selected=scopes(dict(goal=6,long=6,object=6,spatial=6),excluded);rows=[]
 for i,s in enumerate(selected):
  j=i%12
  def emit(category,text,chs=(),metadata=(),kind='mid',extra=(),status='COMPLETE WITHIN VERIFIED CONTRACT',overrides=None):
   q=construct(s,f'FINAL2-{category}-{i:02d}',text,tuple(CHANNELS[k] for k in chs),metadata,kind,extra,status,overrides,category);q.update(split='final',formulation_id=category+'-'+str(j),authored_template=text)
   if kind=='sim':q['request'].pop('seconds_interval',None)
   if status=='UNVERIFIED PLAN' and chs:q['critical']=False;q['inspection_permitted']=True
   rows.append(q);return q
  text,ch=D[j];emit('direct',text,(ch,))
  text,chs=C[j];emit('conjunction',text,chs)
  text,ch,kind=T[j];emit('temporal',text,(ch,),('recorded_time',) if kind=='sim' else (),kind)
  text,meta=P[j];emit('provenance_geometry',text,(),meta,'none')
  text,chs,meta,extra,status=R[j];kind='none' if j in (3,5,11) else 'mid';emit('contracts',text,chs,meta,kind,extra,status,dict(allow_conditional=True) if j==8 else None)
  text,ch,kind=B[j];meta=();overrides={};extra=();status='UNSUPPORTED';which='mid' if ch is not None else 'none'
  if kind=='variant':overrides['variant_id']='wrong_variant';status='INVALID SCOPE'
  elif kind=='task':overrides['task_id']='wrong_task';status='INVALID SCOPE'
  elif kind=='assurance':overrides['assurance']='historical_producer_attestation'
  elif kind=='metadata':meta=('source_provenance',);overrides['assurance']='verified_physical_interpretation'
  elif kind=='quote':meta=('source_provenance',);status='COMPLETE WITHIN VERIFIED CONTRACT'
  elif kind=='quote_metadata':meta=('execution_metadata',);status='COMPLETE WITHIN VERIFIED CONTRACT'
  elif kind=='field_quote':status='COMPLETE WITHIN VERIFIED CONTRACT'
  elif kind=='reduced':overrides['plan']=[CHANNELS[2]];status='UNVERIFIED PLAN'
  elif kind.endswith('_source'):status='UNAVAILABLE'
  q=emit('boundary',text,(ch,) if ch is not None else (),meta,which,extra,status,overrides)
  if kind=='reduced':
   # Both position and velocity are explicitly requested; preserve both in the reference.
   q=rows.pop();q=construct(s,q['id'],text,(CHANNELS[2],CHANNELS[3]),meta,which,extra,status,overrides,'boundary');q.update(split='final',formulation_id='boundary-'+str(j),authored_template=text);rows.append(q)
  if kind.endswith('_source'):q['fault']=kind
 assert len(rows)==144 and len({q['authored_template'] for q in rows})==72
 p=HERE/'FROZEN_EVALUATION_DATASET.jsonl';p.write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in rows));ref=HERE/'REFERENCE_OBLIGATIONS.jsonl';ref.write_text(''.join(json.dumps(dict(case_id=q['id'],query=q['query'],obligations=q['reference_obligations'],source_artifacts=q['source_artifacts'],method=q['independent_reference']),sort_keys=True)+'\n' for q in rows));(WORK/'FINAL_SELECTION_V2.json').write_text(json.dumps(selected,sort_keys=True,indent=2));cfg=dict(f,dataset_sha256=sha(p),references_sha256=sha(ref),criteria_sha256=sha(HERE/'FROZEN_ACCEPTANCE_CRITERIA.json'),created_evaluation_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),questions=144,unique_formulations=72,scope_instances_per_formulation=2,executions=24,variants=len({x['binding']['variant_id'] for x in selected}),excluded_prior_executions=len(excluded),previous_assessment='assessment_v1/',no_target_outputs_used=True)
 (HERE/'FROZEN_CONFIGURATION.json').write_text(json.dumps(cfg,sort_keys=True,indent=2));print('V2 NEW ASSESSMENT FROZEN',sha(p),flush=True)
if __name__=='__main__':run()
