"""Compact capability reports; no empirical safety capability is granted."""
import csv,json,socket
from pathlib import Path
from .reader import HERE
ROWS=[
 ('restored_original_identity','VERIFIED','38 exact original files freshly match expected hashes; HASH_VERIFICATION.json','Four approved development executions only','None for this bounded byte-identity claim'),
 ('recorder_schema_metadata','VERIFIED','Schema4.0 metadata/HDF5/producer manifest/completion consistency','Exact checkpoint/task/episode bindings','New recorder/model scopes need separate validation'),
 ('recorded_endpoint_state','VERIFIED','Array shapes/dtypes/finiteness and flattened/time/qpos/qvel equality','Native mixed model coordinates; no motion inference','Physical uncertainty and variable-specific reference interpretation'),
 ('recorded_initial_state','VERIFIED','HDF5 benchmark initial state equals frame0 flattened state; archive hash resolved','Archive pickle not decoded or executed','Independent initial-state selection checks if broader scope is proposed'),
 ('native_geometry_identity','VERIFIED','Complete161-ID corrected map, body ownership and raw transform guard pass','Exact XML and registered run IDs only; anonymous pieces retained','New model mappings require new source audit'),
 ('saved_table_geometry','VERIFIED','All six collision pieces10-15 invariant at all saved snapshots','Saved projection only; no load-bearing or continuous-static proof','Admitted support-face and uncertainty profile for physical claims'),
 ('recorded_contact_bundle','VERIFIED','Native IDs/dist/pos finite and list length equals recorded ncon','At recorded cache configurations only','Load-bearing interpretation still needs a validated profile'),
 ('camera_dataset_references','VERIFIED','Two camera dataset references with expected shape/dtype per snapshot','No pixel decoding or actual inspection assertion','Decode/inspection coverage if camera corroboration is requested'),
 ('robot_gripper_observables','CONDITIONALLY_SUPPORTED','Available raw/native channels exposed with exact provenance','Raw observable frame/unit/quaternion conventions unverified','Bind version-specific producer observables and channel units'),
 ('box_collision_extent_interpretation','CONDITIONALLY_SUPPORTED','BOX sizes/transforms and complete protected collision-piece references','No calibrated clearance/contact/support tolerance','Independent geometry checks and uncertainty propagation'),
 ('native_cache_phase','CONDITIONALLY_SUPPORTED','Coherent raw body/geom transform bundle; prior lag audit retained','Endpoint/native-cache/raw/camera phases remain distinct','Bound source-specific phase before physical witness admission'),
 ('raw_observable_common_frame','BLOCKED_ON_EVIDENCE','Values retained but no conversion to a common frame is admitted','No silent world-frame or wxyz claim for raw observables','Producer-specific frame/unit/quaternion mapping and phase validation'),
 ('camera_exposure_synchronization','BLOCKED_ON_EVIDENCE','No independently recorded exposure timestamps','Snapshot index/FPS/host UTC are insufficient','Validated exposure/observable profile or qualitative-only usage'),
 ('per_contact_force_normal','UNSUPPORTED','Recorder did not save force/normal fields','Body wrench/sensors are not per-contact force labels','Validated alternative support witness or new independently justified producer'),
 ('sensor_force_interpretation','BLOCKED_ON_EVIDENCE','Native sensor/body-wrench arrays are available','No validated channel mapping or calibrated force semantics','Version/model-specific units/frame/channel calibration'),
 ('initial_load_bearing_applicability','BLOCKED_ON_EVIDENCE','No empirical support profile or independent references','No support/absence inference from contact counts or geometry alone','Independent support/unsupported/ambiguous cases and validated boundary profile'),
 ('fall_and_handling_predicates','BLOCKED_ON_EVIDENCE','Only direct measurements; no inferred events','Setup flight/post-lift drops cannot supply R1 positives','Validated origin/loss/downward/holding/boundary evidence and calibration'),
 ('negative_certificates','BLOCKED_ON_EVIDENCE','Measurement availability is not qualified clear coverage','No missing-to-negative or static-support assumption','Validated support/transition cell certificates and joins'),
 ('dynamic_nonbox_continuous_claims','UNSUPPORTED','Restricted V4 profile excludes these physical capabilities','No moving-root/multiple-parent/dynamic-coverage/continuous solver','Separate approved contract and empirical capability evidence'),
 ('accuracy_or_certification','BLOCKED_ON_EVIDENCE','No independent empirical evaluation performed','No synthetic or AI-only agreement accuracy claim','Frozen independent positive/negative/NA/U references and evaluation protocol'),
]
def main():
 assert socket.gethostname().lower()=='hestia'
 with (HERE/'CAPABILITY_MATRIX.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['capability','status','justification','scope','required_evidence','empirical_runtime_enabled'],lineterminator='\n');w.writeheader()
  for c,s,j,scope,e in ROWS:w.writerow(dict(capability=c,status=s,justification=j,scope=scope,required_evidence=e,empirical_runtime_enabled=False))
 report=json.loads((HERE/'validation/RESULTS.json').read_text());assert report['passed']
 print('Capabilities:',len(ROWS),'Tests:',sum(r['tests_run'] for r in report['suites'].values()))
if __name__=='__main__':main()
