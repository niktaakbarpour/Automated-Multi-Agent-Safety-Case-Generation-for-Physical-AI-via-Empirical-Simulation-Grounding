"""Development diagnostics only; no R1 applicability/events/outcomes."""
import csv,json,socket,subprocess
from pathlib import Path
import h5py,numpy as np
from .geometry import corners,union,displacement,contact_metrics
from .temporal import phase_residual,clock_summary
from evaluation.r1_v4.libero_measurement_reader.reader import MAP,CONSTRAINTS,native_index,run_id
from evaluation.r1_v4.provenance import load,strict_loads
from evaluation.r1_v4.libero_evidence_audit.audit_sources import sha,save,csvwrite
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
DATA=Path('/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence')
WORK=Path('/disk/1/data/niktakbr/r1-v4-phase2b3-working')
BASE='51cf76ad47bccff9f6a4de1c3651141f1e5c954b'
SELECTED={0:{0,9,10,11,14,16},1:{9,10,11,40},2:{0,1,7,8,9,10,11,12},14:{9,10,11,260,270,274,275,276,277,278,279,280,281,282,283,284,285}}
def readv(g,n):return np.asarray(g[n+'/value'][()])
def range_of(rows,key):
 values=[float(r[key]) for r in rows if r.get(key) is not None]
 return {'min':min(values),'max':max(values)} if values else None

def main():
 assert socket.gethostname().lower()=='hestia'
 sources={}
 def source(p):
  p=Path(p);rel=str(p.relative_to(REPO));h=sha(p)
  assert h==__import__('hashlib').sha256(subprocess.check_output(['git','show',BASE+':'+rel],cwd=REPO)).hexdigest(),rel
  sources[rel]=h;return p
 reader=REPO/'evaluation/r1_v4/libero_measurement_reader'
 records=load(source(reader/'RESTORED_SOURCES.json'))
 for r in records:assert sha(r['restored_path'])==r['sha256']==r['expected_sha256']
 for directory in ('libero_evidence_audit','libero_measurement_reader'):
  d=REPO/'evaluation/r1_v4'/directory
  for n,r in load(d/'ARTIFACT_SHA256.json').items():assert sha(d/n)==r['sha256']
 for n in ['requirements/r1_generalized_v2/R1_V2_SPECIFICATION.md','requirements/r1_generalized_v2/FORMAL_SEMANTICS.md','requirements/r1_generalized_v2/EVIDENCE_CONTRACT.md','requirements/r1_generalized_v2/FALL_DEFINITION.md','requirements/r1_generalized_v2/finalization/EMPIRICAL_GATES.md','reports/fall_review_v2_20261016/measurement_findings_v2.md','reports/fall_review_v2_20261016/rotation_serialization_evidence.json','reports/fall_review_v2_20261016/initial_sites_vs_collision_geometry.json','reports/fall_review_v2_20261016/example_manifest.json','reports/fall_review_v2_20261016/example_interpretations_provisional.json','human_review_package/supporting_measurements/README.md']:
  source(REPO/n)
 for n,h_expected in load(reader/'SOURCE_CONTRACT.json')['bindings'].items():assert sha(source(REPO/n))==h_expected
 index=load(source(MAP));constraints=load(source(CONSTRAINTS));idx=native_index(index);geoms=index['geometries'];objects=constraints['objects'];h=constraints['physics_timestep']
 assert constraints['gravity_world']==[0.,0.,-9.81]
 ids=sorted({i for v in objects.values() for i in v['collision_geom_ids']}|set(range(10,16)))
 assert all(geoms[i]['type']=='mjGEOM_BOX' for i in ids)
 allrows=[];selected=[];summaries=[];clocks=[];tables=[];guards=[]
 for ep in (0,1,2,14):
  p=DATA/'long/task_00'/f'episode_{ep:03d}'/'trajectory.h5';source_hash=sha(p);previous={};times=[];host_times=[];episode_rows=[]
  with h5py.File(p,'r') as f:
   assert f.attrs['global_episode_id']==run_id(ep)
   frames=sorted(f['frames']);assert len(frames)=={0:258,1:277,2:246,14:531}[ep]
   for key in frames:
    i=int(key);frame=f['frames'][key];sim=frame['simulator'];raw=frame['raw_observation'];time=float(readv(sim,'time'));times.append(time);host_times.append(int(frame.attrs['monotonic_ns']))
    gp=readv(sim,'geom_xpos');gr=readv(sim,'geom_xmat');bp=readv(sim,'body_xpos');bq=readv(sim,'body_xquat');q=readv(sim,'qpos');v=readv(sim,'qvel');acc=readv(sim,'qacc')
    guards.append(idx.validate_snapshot_transforms(bp,bq,gp,gr))
    cgroup=sim['contacts'];contacts=strict_loads(cgroup.attrs['json']) if 'json' in cgroup.attrs else []
    assert len(contacts)==int(readv(sim,'ncon'))
    pieces={gid:corners(gp[gid],gr[gid],geoms[gid]['size']) for gid in ids}
    bounds={gid:union([pieces[gid]]) for gid in ids}
    if ep==0 and i==0:
     for gid in range(10,16):
      r=gr[gid].reshape(3,3)
      tables.append(dict(geom_id=gid,half_sizes=geoms[gid]['size'],world_position=gp[gid].tolist(),world_rotation=r.tolist(),bounds=bounds[gid],vertical_face_axis_residual=min(max(abs(r[0,j]),abs(r[1,j]),abs(abs(r[2,j])-1)) for j in range(3))))
    for obj,info in objects.items():
     own=info['collision_geom_ids'];parts=[pieces[j] for j in own];combo=tuple(np.concatenate([part[k] for part in parts]) for k in range(3));b=union(parts);cm=contact_metrics(contacts,own,geoms,bounds)
     phase=phase_residual(q,v,acc,bp[info['body_id']],readv(raw,obj+'_pos'),info['joint_qpos_address'],info['joint_dof_address'],h)
     motion=displacement(previous[obj],combo) if obj in previous else dict(min_vertex_dz=None,max_vertex_dz=None,max_vertex_displacement=None)
     previous[obj]=combo
     row=dict(episode=ep,run_id=run_id(ep),object_id=obj,frame=i,time=time,root_z=float(bp[info['body_id'],2]),aabb_min_z=b['min'][2],aabb_max_z=b['max'][2],root_minus_lower=float(bp[info['body_id'],2]-b['min'][2]),upper_minus_root=float(b['max'][2]-bp[info['body_id'],2]),box_roundoff_width=b['max_computational_interval_width'],contact_count=cm['recorded_contact_count'],table_contacts=cm['categories']['table'],robot_contacts=cm['categories']['robot'],floor_contacts=cm['categories']['floor'],other_contacts=cm['categories']['other'],contact_partners=json.dumps(cm['partners']),min_vertex_dz=motion['min_vertex_dz'],max_vertex_dz=motion['max_vertex_dz'],max_vertex_displacement=motion['max_vertex_displacement'],endpoint_cache_residual=phase['endpoint_cache_residual'] if i else None,raw_phase_hypothesis_residual=phase['raw_two_substep_hypothesis_residual'] if i else None,source_sha256=source_hash)
     allrows.append(row);episode_rows.append(row)
     if i in SELECTED[ep]:selected.append(dict(row,contact_proxies=json.dumps(cm['table_contact_proxies']),hdf5_path=f'/frames/{key}/simulator',physical_support=None,physical_event=None))
   clock=clock_summary(list(range(len(frames))),times);clock.update(episode=ep,host_interval_min_s=min(np.diff(host_times))/1e9,host_interval_max_s=max(np.diff(host_times))/1e9);clocks.append(clock)
  for obj in objects:
   rows=[r for r in episode_rows if r['object_id']==obj]
   summaries.append(dict(episode=ep,object_id=obj,samples=len(rows),collision_geom_ids=objects[obj]['collision_geom_ids'],ranges={k:range_of(rows,k) for k in ('root_minus_lower','upper_minus_root','box_roundoff_width','endpoint_cache_residual','raw_phase_hypothesis_residual','min_vertex_dz','max_vertex_dz')},contact_frames={k:sum(r[k]>0 for r in rows) for k in ('table_contacts','robot_contacts','floor_contacts','other_contacts')}))
 csvwrite(WORK/'object_geometry_contacts.csv',allrows);csvwrite(HERE/'DIAGNOSTIC_SAMPLES.csv',selected)
 summary=dict(executions=4,frames=len(guards),object_frames=len(allrows),BOX_pieces=len(ids),objects=summaries,table_pieces=tables,clocks=clocks,transform_residuals={k:{'min':min(g[k] for g in guards),'max':max(g[k] for g in guards)} for k in ('position_error_m','rotation_component_error','position_arithmetic_allowance_m','rotation_arithmetic_allowance')},global_ranges={k:range_of(allrows,k) for k in ('box_roundoff_width','endpoint_cache_residual','raw_phase_hypothesis_residual','root_minus_lower','upper_minus_root','min_vertex_dz','max_vertex_dz')},empirical_admission_enabled=False,physical_judgments_issued=0,independent_physical_reference_cases=0)
 save(HERE/'DIAGNOSTIC_SUMMARY.json',summary)
 save(HERE/'SOURCE_BINDINGS.json',dict(baseline=BASE,prior_files=sources,recordings=[dict(path=r['restored_path'],sha256=r['sha256']) for r in records],full_diagnostics=dict(path=str(WORK/'object_geometry_contacts.csv'),sha256=sha(WORK/'object_geometry_contacts.csv'))))
 print(json.dumps({k:summary[k] for k in ('frames','object_frames','BOX_pieces','global_ranges')}))
if __name__=='__main__':main()
