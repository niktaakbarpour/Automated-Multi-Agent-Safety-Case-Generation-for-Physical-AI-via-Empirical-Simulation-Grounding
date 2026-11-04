"""Authored after implementation freeze; independent original-source references."""
import json,datetime
from .config import *
from .reference import scopes,make
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
BANK={
'C1':[
('Read the opening mechanism displacement at saved frame {frame}.',[CHANNELS[0]],'supported'),
('Show finger velocity measurements at the last saved frame.',[CHANNELS[1]],'end'),
('Fetch revolute joint configurations at the beginning.',[CHANNELS[2]],'begin'),
('What arm angular rates are stored at frame {frame}?',[CHANNELS[3]],'supported'),
('Retrieve native actuator effort at frame {frame}; do not infer contact forces.',[CHANNELS[4]],'supported'),
('How many simulator contact entries are recorded at frame {frame}?',[CHANNELS[5]],'supported'),
('Return the gripper aperture observations at the recording midpoint.',[CHANNELS[0]],'supported'),
('Inspect robot joint speeds at saved snapshot {frame}.',[CHANNELS[3]],'supported')],
'C2':[
('Find finger positions in saved frames {start} through {end}.',[CHANNELS[0]],'range'),
('Get arm angular rates immediately before and after action {action}.',[CHANNELS[3]],'action'),
('Show joint configuration at simulator label {time} seconds.',[CHANNELS[2],'recorded_time'],'seconds'),
('Return motor output at the final snapshot.',[CHANNELS[4]],'end'),
('Read the contact entry count at the initial snapshot.',[CHANNELS[5]],'begin'),
('Obtain gripper speeds across frames {start} to {end}.',[CHANNELS[1]],'range'),
('Show the recorded time labels bracketing action {action}.',['recorded_time'],'action'),
('What finger displacement is saved at simulator time {time}?',[CHANNELS[0],'recorded_time'],'seconds')],
'C3':[
('Find the native body identity of {object}.',['geometry_identity'],'supported'),
('Which collision mesh IDs belong to {object}?',['geometry_identity'],'supported'),
('Identify the simulator geometry for the logical main_table.',['main_table_identity'],'supported'),
('Give the XML native geometry binding of {object}.',['geometry_identity'],'supported'),
('Report the body index and collision shape identifiers for {object}.',['geometry_identity'],'supported'),
('Does main_table have a verified body identity here?',['main_table_identity'],'supported'),
('Retrieve the object identity mapping for {object}.',['geometry_identity'],'supported'),
('Which native geometries are associated with {object}?',['geometry_identity'],'supported')],
'C4':[
('Collect finger positions and arm angular rates at frame {frame}.',[CHANNELS[0],CHANNELS[3]],'supported'),
('Retrieve gripper state, recorded action metadata and time labels around action {action}.',[CHANNELS[0],CHANNELS[1],'action_metadata','recorded_time'],'action'),
('Gather arm configurations, inference metadata and the native geometry of {object} before and after action {action}.',[CHANNELS[2],'inference_metadata','geometry_identity'],'action'),
('Fetch motor effort, contact entry count and source hash at frame {frame}.',[CHANNELS[4],CHANNELS[5],'source_provenance'],'supported'),
('Show finger velocities, camera references and recorded time labels at frame {frame}.',[CHANNELS[1],'camera_references','recorded_time'],'supported'),
('Get arm joint positions, recorded contact references and source provenance in frames {start} through {end}.',[CHANNELS[2],'contact_references','source_provenance'],'range'),
('Collect all six recorded measurement channels at frame {frame}.',list(CHANNELS),'supported'),
('Retrieve action metadata, inference metadata, execution metadata and source hash around action {action}.',['action_metadata','inference_metadata','execution_metadata','source_provenance'],'action')],
'C5':[
('Find tactile pressure readings at frame {frame}.',[],'unsupported'),
('Return contact force vectors for the table at frame {frame}.',[],'unsupported'),
('Find a calibration certificate for physical calibration.',[],'unsupported'),
('Identify which object was in physical support at frame {frame}.',[],'unsupported'),
('Give camera exposure timestamps at frame {frame}.',[],'unsupported'),
('Report a verified collision event at frame {frame}.',[],'unsupported'),
('Retrieve the applied action vector values at frame {frame}.',[],'unsupported'),
('Authenticate a clean checkout of the historical producer binary.',[],'historical')],
'C6':[
('Return world Cartesian finger positions at frame {frame}.',[],'unsupported'),
('Give joint velocities at the same physical instant as camera exposure at frame {frame}.',[],'unsupported'),
('Map gripper positions into world position at frame {frame}.',[],'unsupported'),
('Show raw finger position values at frame {frame} plus a world transform.',[CHANNELS[0]],'partial'),
('Provide simultaneous sensor timestamps at frame {frame}.',[],'unsupported'),
('Report raw arm joint positions at frame {frame} under the conditional cache interpretation.',[CHANNELS[2]],'conditional'),
('Give calibrated world gripper position at frame {frame}.',[],'unsupported'),
('Return robot joint positions at frame {frame} with verified sensor synchronization.',[],'unsupported')],
'C7':[
('Verify the source hash for this recording.',['source_provenance'],'supported'),
('Return execution metadata and checkpoint declarations.',['execution_metadata'],'supported'),
('Can the exact historical producer binary be authenticated?',[],'historical'),
('Give recorded package versions and source provenance.',['execution_metadata','source_provenance'],'supported'),
('Retrieve source integrity evidence at frame {frame}.',['source_provenance'],'supported'),
('Show the declared producer revision; do not promote it to historical binary attestation.',['execution_metadata'],'supported'),
('Return the recording checksum with verified source bytes.',['source_provenance'],'supported'),
('Report the execution metadata for the checkpoint revision.',['execution_metadata'],'supported')],
'C8':[
('Show arm positions at frame {frame} within the requested incompatible variant.',[],'wrong_variant'),
('Get finger positions at frame {frame} in the stated execution.',[],'unknown_execution'),
('Return native geometry for the ambiguous object.',[],'unknown_object'),
('Return arm angular rates at the requested simulator time.',[],'impossible_time'),
('Read gripper positions at frame {frame} from the required source.',[],'missing_source'),
('Get finger speeds at frame {frame} with verified source integrity.',[],'corrupt_source'),
('Return arm configurations at frame {frame} from the exact source.',[],'symlink_source'),
('Retrieve motor effort at frame {frame} after source verification.',[],'replace_source')],
'C9':[
('Can the finger position recorded at frame {frame} support the number {value}?',[CHANNELS[0]],'supported'),
('Does the first joint angle at the initial snapshot equal {value}?',[CHANNELS[2]],'begin'),
('Is the native actuator output at frame {frame} equal to {value}?',[CHANNELS[4]],'supported'),
('Check whether finger speed at the final snapshot equals {value}.',[CHANNELS[1]],'end'),
('Is the contact entry count at frame {frame} recorded as {value}?',[CHANNELS[5]],'supported'),
('Does the arm angular rate at frame {frame} equal {value}?',[CHANNELS[3]],'supported'),
('Which source hash supports the finger position number {value} at frame {frame}?',[CHANNELS[0],'source_provenance'],'supported'),
('Check the saved arm configuration against {value} at frame {frame}.',[CHANNELS[2]],'supported')]
}
def run():
 assert (HERE/'FROZEN_IMPLEMENTATION.json').exists() and not (HERE/'FROZEN_HOLDOUT_DATASET.jsonl').exists()
 frozen=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for n,h in frozen['files'].items():assert sha(HERE/n)==h,n
 j=HERE.parent/'readiness_evaluation';excluded={r['execution'] for r in json.loads((j/'EVALUATION_SELECTION.json').read_text())};excluded|={r['execution_id'] for r in json.loads((WORK/'DEVELOPMENT_SELECTION.json').read_text())};selected=scopes(dict(goal=6,long=6,object=6,spatial=6),excluded);rows=[]
 for i,s in enumerate(selected):
  other=next(x['binding']['variant_id'] for x in selected if x['binding']['variant_id']!=s['binding']['variant_id'])
  for category,bank in BANK.items():
   k=i%8;text,families,kind=bank[k];q=make(s,category,text,families,kind,i,other);q.update(id=f'KH-{category}-{i:02d}',split='holdout',template_id=category+'-'+str(k),template=text)
   if category=='C9':q['narrow_value_claim']=dict(component=0,expected_equal=i%2==0,rule='Source component compared exactly with requested scalar; no safety assertion')
   rows.append(q)
 assert len(rows)==216 and len({q['template_id'] for q in rows})==72
 # Freeze before any target call. Hashes are now fixed for every request and reference.
 path=HERE/'FROZEN_HOLDOUT_DATASET.jsonl';path.write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in rows));(WORK/'HOLDOUT_SELECTION.json').write_text(json.dumps(selected,sort_keys=True,indent=2));result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),dataset_sha256=sha(path),implementation_sha256=sha(HERE/'FROZEN_IMPLEMENTATION.json'),acceptance_sha256=sha(HERE/'FROZEN_ACCEPTANCE_CRITERIA.json'),questions=len(rows),templates=72,executions=len(selected),variants=len({s['binding']['variant_id'] for s in selected}),excluded_scopes=len(excluded),original_source_reference=True,human_evaluation=False);(HERE/'HOLDOUT_FREEZE.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
