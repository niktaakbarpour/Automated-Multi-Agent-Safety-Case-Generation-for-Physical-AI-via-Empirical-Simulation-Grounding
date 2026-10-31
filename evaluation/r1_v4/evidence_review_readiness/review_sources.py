"""Inspect candidate numerical windows on Hestia; no physical outcome admission."""
import csv,json,socket,subprocess
from pathlib import Path
import h5py,numpy as np
from evaluation.r1_v4.libero_evidence_audit.audit_sources import load,save,sha
from evaluation.r1_v4.measurement_profile_validation.geometry import corners,union
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
PROFILE=REPO/'evaluation/r1_v4/measurement_profile_validation'
READER=REPO/'evaluation/r1_v4/libero_measurement_reader'
BASE='f15d3a9da13e535db49b19f023f762824b4ea26c'
SHEETS={0:('c2f08248d428f264db8c8c9e6c6e5fe070d8ade454d320926d77e3e2f4308ddc',39207),2:('ea0a058a1dfc75e4e8eecefe7e7976461514b88436a1213c0d6ba58f61cf4210',38183),14:('8e60c7bf21f8dab834d0bb95c5968b98bfc673775bb2f631751978f28caeef19',43542)}
def main():
 assert socket.gethostname().lower()=='hestia'
 for root in (PROFILE,READER,REPO/'evaluation/r1_v4/libero_evidence_audit'):
  for n,r in load(root/'ARTIFACT_SHA256.json').items():assert sha(root/n)==r['sha256']
 sources=load(READER/'RESTORED_SOURCES.json')
 for r in sources:assert sha(r['restored_path'])==r['sha256']==r['expected_sha256']
 prior=load(PROFILE/'SOURCE_BINDINGS.json');full=Path(prior['full_diagnostics']['path']);assert sha(full)==prior['full_diagnostics']['sha256']
 rows={(int(r['episode']),r['object_id'],int(r['frame'])):r for r in csv.DictReader(full.open())}
 map_path=REPO/'reports/fall_review_v2_20261016/corrected_native_geometry_v2.json';mapping=load(map_path)
 constraints=load(REPO/'reports/fall_review_v2_20261016/constraints_and_identities.json')['objects']
 cases=list(csv.DictReader((PROFILE/'DEVELOPMENT_REFERENCE_CANDIDATES.csv').open()));summaries=[]
 for c in cases:
  if not c['source_path']:
   summaries.append(dict(candidate_id=c['candidate_id'],available=False,numerical_frames_inspected=[],reason='No verified sliding example exists in the prepared candidate set'));continue
  ep=int(c['episode']);p=Path(c['source_path']);assert ep in (0,1,2,14) and sha(p)==c['source_sha256']
  indices=json.loads(c['frames']);window=list(range(max(0,min(indices)-1),max(indices)+1));obj=c['object_id'];info=constraints[obj];ids=set(info['collision_geom_ids'])
  observed=[];raw_counts=[];finger_groups=[];times=[];relative_finger_distances=[];motion_points=[]
  with h5py.File(p,'r') as h:
   rid=str(h.attrs['global_episode_id']);assert rid==f'libero_long_openvla_oft_task00_seed{1000+ep}_trial{ep:03d}_cfafd9ddc3db'
   for i in window:
    sim=h[f'frames/{i:06d}/simulator'];gpos=sim['geom_xpos/value'][()];grot=sim['geom_xmat/value'][()]
    root_position=sim['body_xpos/value'][()][info['body_id']];left=gpos[[76,77]].mean(axis=0);right=gpos[[79,80]].mean(axis=0)
    relative_finger_distances.append([float(np.linalg.norm(root_position-left)),float(np.linalg.norm(root_position-right))]);motion_points.append([float(root_position[2]),float(left[2]),float(right[2])])
    contacts=json.loads(sim['contacts'].attrs['json']) if 'json' in sim['contacts'].attrs else []
    assert len(contacts)==int(sim['ncon/value'][()])
    own=[r for r in contacts if r['geom1'] in ids or r['geom2'] in ids]
    partners={r['geom2'] if r['geom1'] in ids else r['geom1'] for r in own}
    row=rows[(ep,obj,i)];assert int(row['contact_count'])==len(own) and row['run_id']==rid
    b=union([corners(gpos[j],grot[j],mapping['geometries'][j]['size']) for j in sorted(ids)])
    assert b['min'][2]==float(row['aabb_min_z']) and b['max'][2]==float(row['aabb_max_z'])
    time=float(sim['time/value'][()]);assert time==float(row['time']);times.append(time)
    observed.append(row);raw_counts.append(len(own));finger_groups.append(bool(partners & {76,77}) and bool(partners & {79,80}))
   metadata=load(p.parent/'run_metadata.json')
  summaries.append(dict(candidate_id=c['candidate_id'],available=True,execution_id=rid,episode=ep,object_id=obj,task_name=metadata['task_name'],task_configuration_id=metadata['task_configuration_id'],checkpoint=metadata['checkpoint'],checkpoint_revision=metadata['checkpoint_revision'],numerical_frames_inspected=window,original_candidate_frames=indices,endpoint_time_range=[min(times),max(times)],source_path=str(p),source_sha256=sha(p),body_id=info['body_id'],collision_geom_ids=sorted(ids),contact_count_range=[min(raw_counts),max(raw_counts)],frames_with_table_contacts=sum(int(r['table_contacts'])>0 for r in observed),frames_with_robot_contacts=sum(int(r['robot_contacts'])>0 for r in observed),frames_with_other_contacts=sum(int(r['other_contacts'])>0 for r in observed),frames_with_floor_contacts=sum(int(r['floor_contacts'])>0 for r in observed),frames_with_two_finger_groups=sum(finger_groups),nominal_adjacent_pairs_with_three_upward_z_components=int(np.all(np.diff(np.asarray(motion_points),axis=0)>0,axis=1).sum()),root_to_finger_collision_center_distance_ranges=[[min(x[j] for x in relative_finger_distances),max(x[j] for x in relative_finger_distances)] for j in (0,1)],finger_geometry_groups=[[76,77],[79,80]],co_motion_measurement_is_not_holding_proof=True,collision_min_z_range=[min(float(r['aabb_min_z']) for r in observed),max(float(r['aabb_min_z']) for r in observed)],max_corresponding_vertex_displacement=max(float(r['max_vertex_displacement'] or 0) for r in observed),pairs_with_all_nominal_vertex_dz_negative=sum(r['max_vertex_dz']!='' and float(r['max_vertex_dz'])<0 for r in observed[1:]),measurement_status='verified recorded structure and model-bound numerical agreement',physical_support_validated=False,physical_event_admitted=False))
 save(HERE/'NUMERICAL_REVIEW_SUMMARY.json',summaries)
 excerpts=load(PROFILE/'CAMERA_EXCERPT_MANIFEST.json');visual=[]
 for r in excerpts:
  ep=r['episode'];digest,size=SHEETS[ep];p=Path(r['derived_sheet']);assert sha(p)==digest and p.stat().st_size==size
  source=Path(r['source'])
  with h5py.File(source,'r') as h:
   frame_group=h[f"frames/{r['frame']:06d}"];time=float(frame_group['simulator/time/value'][()]);rid=str(h.attrs['global_episode_id']);host=dict(utc=str(frame_group.attrs['utc']),wall_time_ns=int(frame_group.attrs['wall_time_ns']),monotonic_ns=int(frame_group.attrs['monotonic_ns']))
  visual.append(dict(r,execution_id=rid,snapshot_endpoint_time=time,snapshot_host_timestamps=host,exposure_time=None,viewed_in_current_Codex_session=True,authorized_local_path=f'/tmp/trustworthy-phase2b4-approved-contact-sheets/episode_{ep:03d}.jpg',authorization='Explicit user authorization of only three specified sheets for Phase2B4 visual review',interpretation_scope='Qualitative visual corroboration only; no image-only support or falling claim'))
 save(HERE/'AUTHORIZED_VISUAL_EVIDENCE.json',dict(files=[dict(episode=ep,source=f'/disk/1/data/niktakbr/r1-v4-phase2b3-working/reference_sheets/episode_{ep:03d}.jpg',sha256=h,bytes=size) for ep,(h,size) in SHEETS.items()],total_bytes=120932,panels=visual,raw_HDF5_or_video_transferred=False,additional_images_transferred=False,local_payload_hash_recomputed=False))
 save(HERE/'SOURCE_BINDINGS.json',dict(baseline=BASE,prior_profile_manifest_sha256=sha(PROFILE/'ARTIFACT_SHA256.json'),prior_reader_manifest_sha256=sha(READER/'ARTIFACT_SHA256.json'),original_files=[dict(path=r['restored_path'],sha256=r['sha256']) for r in sources],full_diagnostics=dict(path=str(full),sha256=sha(full)),human_form_sha256=sha(PROFILE/'REFERENCE_REVIEW_FORM.csv')))
 print('Reviewed entries',len(cases),'numerical cases',sum(r['available'] for r in summaries),'authorized visual panels',len(visual))
if __name__=='__main__':main()
