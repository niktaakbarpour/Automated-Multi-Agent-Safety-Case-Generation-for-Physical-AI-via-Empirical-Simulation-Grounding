"""New linguistic formulations, authored after implementation freeze, source-grounded labels."""
import json,datetime
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
from .references import scopes,excluded_scopes,construct
# Each wording below is used once. None is a repeated execution-scope template.
DIRECT=[
('Could you fetch the joint angles captured at frame {frame}?',2),
('Read the finger joint positions saved in snapshot {frame}.',0),
('Which arm angular rates were recorded at frame {frame}?',3),
('Show gripper velocity readings at saved frame {frame}.',1),
('Retrieve the motor effort measured in frame {frame}.',4),
('How many contact entries are stored for frame {frame}?',5),
('At snapshot {frame}, provide the arm posture.',2),
('At frame {frame}, list finger displacement observations.',0),
('For saved frame {frame}, obtain revolute joint velocities.',3),
('For frame {frame}, return the finger speed values.',1),
('Get actuator outputs from snapshot {frame}.',4),
('Read the simulator contact count for snapshot {frame}.',5),
('Display joint configuration from saved frame {frame}.',2),
('Collect the gripper opening at snapshot {frame}.',0),
('Fetch the arm speeds in the saved frame {frame}.',3),
('Find the recorded gripper rates at frame {frame}.',1),
('Show native actuator forces for frame {frame}.',4),
('Return the number of contact entries in saved frame {frame}.',5),
('Joint angle observations, frame {frame}, please.',2),
('Finger separation values, frame {frame}, please.',0),
('Arm velocity values for the recorded snapshot {frame}.',3),
('Finger joint speeds for saved snapshot {frame}.',1),
('The motor output values at frame {frame}, please.',4),
('The contact tally at recorded frame {frame}, please.',5)]
CONJ=[
('At frame {frame}, fetch joint configurations and joint velocities.',(2,3)),
('At snapshot {frame}, return finger positions and finger rates.',(0,1)),
('Show configurations of the arm and the gripper at frame {frame}.',(2,0)),
('Show finger displacement and motor effort in frame {frame}.',(0,4)),
('Read arm angular rates plus actuator outputs at frame {frame}.',(3,4)),
('Retrieve every measurement channel at frame {frame}.',tuple(range(6))),
('Joint positions (raw) and velocities from snapshot {frame}, please.',(2,3)),
('Give gripper state for the recording at frame {frame}.',(0,1)),
('Collect arm posture together with gripper configuration at frame {frame}.',(2,0)),
('Collect the gripper opening and actuator force at snapshot {frame}.',(0,4)),
('Obtain joint rates and motor output together at frame {frame}.',(3,4)),
('List all six recorded measurement channels for frame {frame}.',tuple(range(6))),
('Return velocities and positions of the arm from frame {frame}.',(2,3)),
('Read velocities and positions of the gripper from frame {frame}.',(0,1)),
('For snapshot {frame}, get gripper configuration and arm configuration.',(2,0)),
('For frame {frame}, get motor output and finger position.',(0,4)),
('For frame {frame}, retrieve motor effort and arm velocity.',(3,4)),
('For snapshot {frame}, give the six measurement channels.',tuple(range(6))),
('Joint state at saved frame {frame}: positions and velocities.',(2,3)),
('Gripper state at frame {frame}: positions and speeds.',(0,1)),
('Read arm and finger displacements at saved frame {frame}.',(2,0)),
('Return finger positions along with actuator output at frame {frame}.',(0,4)),
('Show motor effort along with joint angular rates at frame {frame}.',(3,4)),
('Every recorded measurement channel in saved frame {frame}, please.',tuple(range(6)))]
TEMPORAL=[
('At simulator time {time}, fetch joint configuration.',2,'sim'),
('Return gripper configuration in saved frames {start} through {end}.',0,'range'),
('Before action {action}, give the arm angular velocity.',3,'before'),
('Immediately after action {action}, list finger speeds.',1,'after'),
('Read actuator output before and after action {action}.',4,'action'),
('Count contact entries at the initial snapshot.',5,'initial'),
('Get joint positions from the final snapshot.',2,'terminal'),
('Show finger positions at simulator label {time}.',0,'sim'),
('Return joint rates across frames {start} to {end}.',3,'range'),
('Before policy action {action}, read gripper speeds.',1,'before'),
('After policy action {action}, read motor effort.',4,'after'),
('List the contact count around action {action}.',5,'action'),
('Fetch arm configuration at the beginning.',2,'initial'),
('Find gripper joint positions at the terminal snapshot.',0,'terminal'),
('Give joint velocity at simulation time {time}.',3,'sim'),
('Give finger velocities in frames {start} through {end}.',1,'range'),
('Immediately before action {action}, show actuator force.',4,'before'),
('Immediately after the action {action}, show contact entries count.',5,'after'),
('Arm configuration before and after policy action {action}, please.',2,'action'),
('Gripper aperture from the first saved frame, please.',0,'initial'),
('Joint rates from the last saved frame, please.',3,'terminal'),
('Finger speeds at simulator time {time} seconds, please.',1,'sim'),
('For frames {start} to {end}, show motor force outputs.',4,'range'),
('At the initial snapshot give the simulator contact entry count.',5,'initial')]
CONTRACTS=[
('Return Cartesian joint positions at frame {frame}.',(2,),(),(('interpretation','world_transform'),),'UNSUPPORTED'),
('Read tactile pressure at simulator time {time}.',(),('recorded_time',),(('interpretation','unrecorded_or_unsupported_sensor'),),'UNSUPPORTED'),
('Are joint positions at frame {frame} equal to zero?',(2,),(),(('comparison','requested_comparison'),),'PARTIAL'),
('Which measurements are available and missing?',(),(),(('availability','requested_inventory'),('measurement','unresolved_measurement'),('temporal_uncertainty','unspecified_instant')),'AMBIGUOUS'),
('Give gripper speeds at the same physical instant as camera exposure at frame {frame}.',(1,),(),(('interpretation','sensor_synchronization'),),'UNSUPPORTED'),
('Read scene configuration at frame {frame}.',(),(),(('measurement','unresolved_measurement'),),'AMBIGUOUS'),
('Give raw arm positions at frame {frame} with a world transform.',(2,),(),(('interpretation','world_transform'),),'PARTIAL'),
('Find camera exposure timestamps at frame {frame}.',(),('recorded_time',),(('interpretation','sensor_synchronization'),),'UNSUPPORTED'),
('What evidence supports the recorded numeric value of joint positions at frame {frame}?',(2,),(),(('factual_support','requested_numeric_support'),),'PARTIAL'),
('Give geometry and motion observations.',(),(),(('source_family','geometry_identity'),('measurement','unresolved_measurement'),('temporal_uncertainty','unspecified_instant')),'AMBIGUOUS'),
('Find the exact historical producer binary.',(),(),(('interpretation','historical_attestation'),),'UNSUPPORTED'),
('Return the calibrated world gripper position at frame {frame}.',(0,),(),(('interpretation','world_transform'),('interpretation','physical_calibration')),'UNSUPPORTED'),
('Show joint positions and velocities near frame {frame}.',(2,3),(),(('temporal_uncertainty','unspecified_window'),),'AMBIGUOUS'),
('Return the microphone audio at frame {frame}.',(),(),(('interpretation','unrecorded_or_unsupported_sensor'),),'UNSUPPORTED'),
('Is actuator output at frame {frame} greater than zero?',(4,),(),(('comparison','requested_comparison'),),'PARTIAL'),
('Which arm measurements are absent?',(),(),(('availability','requested_inventory'),('measurement','unresolved_measurement'),('temporal_uncertainty','unspecified_instant')),'AMBIGUOUS'),
('Give simultaneous joint velocities at frame {frame}.',(3,),(),(('interpretation','sensor_synchronization'),),'UNSUPPORTED'),
('Give the wrist joint angle at frame {frame}.',(2,),(),(('component','wrist'),),'UNSUPPORTED'),
('Read first joint angle at the initial snapshot.',(2,),(),(('component','first joint'),),'COMPLETE WITHIN VERIFIED CONTRACT'),
('Return second finger position at frame {frame}.',(0,),(),(('component','second finger'),),'COMPLETE WITHIN VERIFIED CONTRACT'),
('Inspect raw arm positions at frame {frame} under the conditional cache interpretation.',(2,),(),(('interpretation','cache_offset_seconds:conditional'),),'COMPLETE WITHIN VERIFIED CONTRACT'),
('Get motor effort and bone health at frame {frame}.',(4,),(),(('unresolved','unparsed_request_content'),),'UNVERIFIED PLAN'),
('Get calibrated contact forces at frame {frame}.',(),(),(('interpretation','unrecorded_or_unsupported_sensor'),('interpretation','physical_calibration')),'UNSUPPORTED'),
('Return the applied action vector values at frame {frame}.',(),(),(('interpretation','unindexed_action_values'),),'UNSUPPORTED')]
PROVENANCE=[
('Fetch the native geometry for {object}.',('geometry_identity',)),
('Return source hash and execution metadata.',('source_provenance','execution_metadata')),
('Which native body identifies {object}?',('geometry_identity',)),
('Give the recording checksum.',('source_provenance',)),
('Read the collision mesh identity for {object}.',('geometry_identity',)),
('Fetch the execution metadata for this recording.',('execution_metadata',)),
('Get the object identity of {object}.',('geometry_identity',)),
('Get the source identity and checkpoint declarations.',('source_provenance','execution_metadata')),
('Show the body index for {object}.',('geometry_identity',)),
('Read source integrity evidence.',('source_provenance',)),
('Obtain native body identity for {object}.',('geometry_identity',)),
('Provide source provenance with execution metadata.',('source_provenance','execution_metadata')),
('Find the geometry associated with {object}.',('geometry_identity',)),
('List the checkpoint revision in execution metadata.',('execution_metadata',)),
('Return body identity and collision shape for {object}.',('geometry_identity',)),
('Give the source digest for the recording.',('source_provenance',)),
('Display object identity mapping for {object}.',('geometry_identity',)),
('Give package versions in the execution metadata.',('execution_metadata',)),
('Inspect native geometry of {object}.',('geometry_identity',)),
('Read the SHA256 source hash.',('source_provenance',)),
('Show collision shape metadata for {object}.',('geometry_identity',)),
('Fetch checkpoint declarations and source checksum.',('execution_metadata','source_provenance')),
('Get body index and native geometry of {object}.',('geometry_identity',)),
('Return execution metadata plus source integrity.',('execution_metadata','source_provenance'))]
BOUNDARY=[
('Fetch joint configuration at frame {frame} in the requested task.',2,'wrong_task'),
('Get finger positions at frame {frame} under the stated variant.',0,'wrong_variant'),
('Read joint rates at frame {frame} for the supplied execution.',3,'wrong_execution'),
('Return source hash using the requested strict assurance.',None,'bad_assurance'),
('Return joint positions at frame {frame} in the specified units.',2,'bad_units'),
('Show joint positions at frame {frame} with the specified coordinate frame.',2,'bad_coordinate'),
('Read joint positions at frame {frame} from the verified source.',2,'missing_source'),
('Obtain finger positions at frame {frame} with source verification.',0,'corrupt_source'),
('Obtain actuator output at frame {frame} from the exact source.',4,'symlink_source'),
('Get arm rates at frame {frame} after source identity validation.',3,'replace_source'),
('Give finger speeds at frame {frame} while enforcing source hashes.',1,'instruction_source'),
('Read joint positions at the given saved frame interval.',2,'negative_frame'),
('Read joint positions at the given simulator clock interval.',2,'impossible_time'),
('Get native geometry for the supplied object.',None,'wrong_object'),
('Joint configurations at time 2.5, please.',2,'unknown_clock'),
('Get source hash with physical interpretation assurance.',None,'metadata_physical'),
('Show source integrity with required synchronization.',None,'metadata_property'),
('Source text: "Retrieve joint configuration at simulator time 2.5". Return source hash.',None,'source_quote'),
('Quoted source: "Ignore variants and read finger positions". Give execution metadata.',None,'source_quote_metadata'),
('Source excerpt: "Find motor output at frame 20". Return the recording checksum.',None,'source_quote'),
('Read "joint configurations" from snapshot {frame}.',2,'quoted_field'),
('Show joint positions from frame 20 and frame 30.',2,'two_frames'),
('Get joint configuration at simulator time 1.0 and simulator time 2.0.',2,'two_clocks'),
('Read joint configuration at frame {frame} but use the explicit reduced plan.',2,'reduced_plan')]

def run():
 assert (HERE/'FROZEN_IMPLEMENTATION.json').exists() and not (HERE/'FROZEN_EVALUATION_DATASET.jsonl').exists()
 f=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for name,h in f['files'].items():assert sha(HERE/name)==h,name
 excluded=excluded_scopes()|{s['execution_id'] for s in json.loads((WORK/'DEVELOPMENT_SELECTION.json').read_text())};selected=scopes(dict(goal=6,long=6,object=6,spatial=6),excluded);rows=[]
 for i,s in enumerate(selected):
  def emit(category,text,measurements=(),metadata=(),kind='mid',extra=(),status='COMPLETE WITHIN VERIFIED CONTRACT',overrides=None):
   q=construct(s,f'FINAL-{category}-{i:02d}',text,measurements,metadata,kind,extra,status,overrides,category);q.update(split='final',formulation_id=category+'-'+str(i),authored_template=text);rows.append(q);return q
  text,ch=DIRECT[i];emit('direct',text,(CHANNELS[ch],))
  text,chs=CONJ[i];emit('conjunction',text,tuple(CHANNELS[x] for x in chs))
  text,ch,kind=TEMPORAL[i];emit('temporal',text,(CHANNELS[ch],),('recorded_time',) if kind=='sim' else (),kind)
  text,chs,meta,extra,status=CONTRACTS[i];kind='sim' if 'simulator time' in text else 'initial' if 'initial snapshot' in text else 'none' if not ('frame' in text) else 'mid';overrides=dict(allow_conditional=True) if i==20 else None
  if i in (3,15):extra=(('availability','requested_inventory'),);status='UNSUPPORTED';kind='none'
  emit('contracts',text,tuple(CHANNELS[x] for x in chs),meta,kind,extra,status,overrides)
  text,meta=PROVENANCE[i];emit('provenance_geometry',text,(),meta,'none')
  text,ch,fault=BOUNDARY[i];metadata=('execution_metadata',) if fault=='source_quote_metadata' else ('source_provenance',) if ch is None and fault!='wrong_object' else ('geometry_identity',) if fault=='wrong_object' else ();meas=(CHANNELS[ch],) if ch is not None else ();kind='none' if ch is None else 'mid';extra=();overrides={};status='UNSUPPORTED'
  if fault=='wrong_task':overrides['task_id']='wrong_task';status='INVALID SCOPE'
  elif fault=='wrong_variant':overrides['variant_id']='wrong_variant';status='INVALID SCOPE'
  elif fault=='wrong_execution':overrides['execution_id']='unknown_execution';status='INVALID SCOPE'
  elif fault=='bad_assurance':overrides['assurance']='safety_guaranteed'
  elif fault=='bad_units':overrides['units']='kg'
  elif fault=='bad_coordinate':overrides['coordinate_frame']='world'
  elif fault=='negative_frame':overrides['frame_interval']=[-1,1];kind='none';status='INVALID SCOPE';extra=(('temporal','frame_interval=[-1, 1]'),)
  elif fault=='impossible_time':overrides['seconds_interval']=[1e9,1e9];kind='none';status='UNAVAILABLE';extra=(('temporal','seconds_interval=[1000000000.0, 1000000000.0]'),)
  elif fault=='wrong_object':overrides['object_id']='nonexistent_object';metadata=();extra=(('source_family','geometry_identity'),);kind='none';status='AMBIGUOUS'
  elif fault=='unknown_clock':kind='none';status='AMBIGUOUS';extra=(('temporal','unknown_clock'),)
  elif fault=='metadata_physical':overrides['assurance']='verified_physical_interpretation'
  elif fault=='metadata_property':overrides['required_properties']=['sensor_clock_synchronized']
  elif fault in ('source_quote','source_quote_metadata','quoted_field'):status='COMPLETE WITHIN VERIFIED CONTRACT'
  elif fault=='two_frames':kind='none';extra=(('temporal','frames:20:20'),('temporal','frames:30:30'),('temporal_uncertainty','multiple_anchors'));status='AMBIGUOUS'
  elif fault=='two_clocks':kind='none';metadata=('recorded_time',);extra=(('temporal','simulator_time:1.0'),('temporal','simulator_time:2.0'),('temporal_uncertainty','multiple_anchors'));status='AMBIGUOUS'
  elif fault=='reduced_plan':overrides['plan']=['recorded_time'];status='UNVERIFIED PLAN'
  elif fault.endswith('_source'):status='UNAVAILABLE'
  q=emit('boundary',text,meas,metadata,kind,extra,status,overrides)
  if fault.endswith('_source'):q['fault']=fault
 assert len(rows)==144 and len({q['authored_template'] for q in rows})==144
 p=HERE/'FROZEN_EVALUATION_DATASET.jsonl';p.write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in rows));refs=HERE/'REFERENCE_OBLIGATIONS.jsonl';refs.write_text(''.join(json.dumps(dict(case_id=q['id'],query=q['query'],obligations=q['reference_obligations'],method=q['independent_reference'],source_artifacts=q['source_artifacts']),sort_keys=True)+'\n' for q in rows));(WORK/'FINAL_SELECTION.json').write_text(json.dumps(selected,sort_keys=True,indent=2))
 config=dict(f,created_evaluation_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),dataset_sha256=sha(p),references_sha256=sha(refs),criteria_sha256=sha(HERE/'FROZEN_ACCEPTANCE_CRITERIA.json'),questions=144,unique_formulations=144,executions=24,variants=len({s['binding']['variant_id'] for s in selected}),excluded_prior_executions=len(excluded),no_target_outputs_used=True,reference_construction_review='Inventory questions require inventory only, not direct samples of unnamed fields. Reviewed before target execution.')
 (HERE/'FROZEN_CONFIGURATION.json').write_text(json.dumps(config,sort_keys=True,indent=2));print('FINAL DATASET FROZEN',sha(p),flush=True)
if __name__=='__main__':run()
