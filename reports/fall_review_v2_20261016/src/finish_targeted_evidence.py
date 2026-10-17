"""Separate endpoint kinematics, timing fixtures, and focused camera sheet.

This performs static kinematics only. No physics advancement or contact solving.
"""
import argparse,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import h5py,mujoco,numpy as np
from PIL import Image,ImageDraw,ImageFont
from targeted_investigation import load,save,sha,val,bounds,OBJECTS

def main(project,out):
    project=Path(project);out=Path(out);runs=load(project/'reports/fall_review_20261016/runs.json')['runs'];ref=Path(runs[0]['source_episode']);m=mujoco.MjModel.from_xml_path(str(ref/'simulator.xml'));index=load(out/'corrected_native_geometry_v2.json');geoms=index['geometries'];bid={o:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,o+'_main') for o in OBJECTS};ids={o:[g['native_geom_id'] for g in geoms if g['owner_body']==o+'_main' and g['collision_capable']] for o in OBJECTS}
    endpoints=[];fixtures=[]
    for r in runs:
      with h5py.File(r['trajectory']['path']) as h:
        s=h['frames/000010/simulator'];d=mujoco.MjData(m);d.qpos[:]=val(s,'qpos');mujoco.mj_kinematics(m,d)
        endpoints.append({'run_id':r['run_id'],'frame':'000010','recorded_state_time':float(val(s,'time')),'method':'Static mj_kinematics on unmodified recorded endpoint qpos, no mj_step/mj_forward/contact solve. Separate derived geometry, not a replacement for recorded poses or contacts.','contact_records_at_this_reconstructed_pose':'not_computed','objects':{o:{'static_endpoint_root_world':d.xpos[b].tolist(),'collision_bounds':list(map(lambda x:x.tolist(),bounds(m,d.geom_xpos,d.geom_xmat.reshape(-1,3,3),ids[o])))} for o,b in bid.items()}})
        if r['episode'] in [0,2,14]:
          for fi in ([1,10,11] if r['episode']!=14 else [280,281,282,283,284]):
            f=h[f'frames/{fi:06d}'];s=f['simulator'];q=val(s,'qpos');v=val(s,'qvel');a=val(s,'qacc');bp=val(s,'body_xpos')
            for o,b in bid.items():
              j=m.body_jntadr[b];qa=m.jnt_qposadr[j];va=m.jnt_dofadr[j]
              fixtures.append({'run_id':r['run_id'],'frame':f'{fi:06d}','object':o,'source_trajectory':r['trajectory']['path'],'source_hdf5_full_hash_not_independently_recomputed':True,'dt':m.opt.timestep,'qpos_xyz':q[qa:qa+3].tolist(),'qvel_xyz':v[va:va+3].tolist(),'qacc_xyz':a[va:va+3].tolist(),'recorded_body_xyz':bp[b].tolist(),'recorded_raw_xyz':val(f,'raw_observation/'+o+'_pos').tolist()})
    save(out/'prepolicy_static_endpoint_geometry.json',{'no_physics_steps':True,'records':endpoints});save(out/'fixtures/actual_recorded_timing_samples.json',{'evidence_class':'recorded_robot_measurement_excerpt_not_synthetic','samples':fixtures})
    root=ET.parse(ref/'simulator.xml');sites=[x.attrib for x in root.findall('.//site') if (x.get('name') or '').startswith('living_room_table_')]
    save(out/'initial_sites_vs_collision_geometry.json',{'source_xml_sha256':sha(ref/'simulator.xml'),'initial_region_sites':sites,'site_z_declared_in_saved_xml':0.41,'native_table_upper_box_face_z':0.43676000000000015,'difference_m':0.026760000000000173,'source_of_height':'Saved table collision sizes/transforms, never object root positions','model_explicit_contact_pair_count':m.npair,'model_equality_count':m.neq,'qualification':'Mismatch is a recorded setup fact; it does not by itself establish the historical origin of the archive/scene inconsistency.'})
    r=runs[14];frames=[10,270,276,280,281,282,283,284,286];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12);sheet=Image.new('RGB',(len(frames)*256,680),'white');draw=ImageDraw.Draw(sheet);draw.text((8,2),r['run_id'],fill='black',font=font);draw.text((8,18),'Existing recorded cameras; selected times (not a continuous clip); interpretations provisional.',fill='black',font=font);entries=[]
    with h5py.File(r['trajectory']['path']) as h:
      for col,fi in enumerate(frames):
        f=h[f'frames/{fi:06d}'];t=float(val(f,'simulator/time'));stage=str(f.attrs['stage']);step=int(f.attrs['control_step'])
        for ci,cam in enumerate(['agentview_image','robot0_eye_in_hand_image']):
          sheet.paste(Image.fromarray(val(f,'raw_observation/'+cam)[::-1,::-1].copy()),(col*256,82+ci*305));draw.text((col*256+3,39+ci*305),f'f{fi:06d} t={t:.3f}s\n{stage} step={step}\n{cam}',fill='black',font=font)
        entries.append({'run_id':r['run_id'],'frame':f'{fi:06d}','stage':stage,'control_step':step,'simulator_time':t,'image_paths':[f'frames/{fi:06d}/raw_observation/{cam}/value' for cam in ['agentview_image','robot0_eye_in_hand_image']],'trajectory':r['trajectory']['path'],'host_snapshot_utc':str(f.attrs['utc']),'camera_capture_time_not_independently_recorded':True})
    sheet.save(out/'examples/episode_014_sheet.png');manifest=load(out/'example_manifest.json');next(x for x in manifest if x['example_id']=='recorded-example-014')['frames']=entries;save(out/'example_manifest.json',manifest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);a=p.parse_args();main(a.project,a.output)
