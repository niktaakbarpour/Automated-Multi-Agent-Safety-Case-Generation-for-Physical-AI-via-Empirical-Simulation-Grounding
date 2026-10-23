"""Read-only recording export. Never imports the checker or simulation runtime.
Usage: python build_review.py --repo REPO --recordings CURRENT_TASK_DIRECTORY
Requires existing numpy, h5py, Pillow, ffmpeg, ffprobe. Outputs a NEW folder only.
"""
import argparse,csv,hashlib,json,subprocess,sys,shutil,itertools,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,h5py
from PIL import Image,ImageDraw,ImageFont
EPS=[0,1,2,14]
CAMS=['agentview_image','robot0_eye_in_hand_image']
OBJECTS=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']
ALL=OBJECTS+['alphabet_soup_1','tomato_sauce_1','basket_1']
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def val(g,p):
 x=g[p]
 if isinstance(x,h5py.Dataset):return x[()]
 if 'value' in x:return x['value'][()]
 return json.loads(x.attrs['json'])
def csvwrite(p,cols,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction='raise');w.writeheader();w.writerows(rows)
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n')
def quat(q):
 w,x,y,z=np.asarray(q,float);s=2/np.dot(q,q)
 return np.array([[1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w)],[s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w)],[s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)]])
def main():
 a=argparse.ArgumentParser();a.add_argument('--repo',type=Path,required=True);a.add_argument('--recordings',type=Path,required=True);args=a.parse_args()
 repo=args.repo;rel=repo/'reports/fall_checker_dev_v2_20261017';out=repo/'human_review_package'
 if out.exists():out=repo/'human_review_package_v20261023'
 out.mkdir(exist_ok=False)
 for d in ['full_videos','short_clips/normal_speed','short_clips/slow_motion','initial_state_images','supporting_measurements','schemas','tools','adjudication','reviewer_1','reviewer_2']:(out/d).mkdir(parents=True,exist_ok=True)
 shutil.copy2(__file__,out/'tools/build_review.py')
 config=json.loads((rel/'config.json').read_text());split=json.loads((rel/'proposed_split.json').read_text());inv=json.loads((rel/'corrected_entity_inventory_v2.json').read_text());geo=json.loads((rel/'corrected_native_geometry_v2.json').read_text());geoms=geo['geometries'];records={r['run_id']:r for r in inv['records']}
 assert geo['schema_version']=='native-geometry-index-v2'
 assert [g['native_geom_id'] for g in geoms]==list(range(len(geoms)))
 # Only neutral static geometry fields, never classifications or supporting flags.
 csvwrite(out/'supporting_measurements/native_geometry.csv',['native_geom_id','geom_name','owner_body','type','half_size_xyz_m','collision_capable'],[dict(native_geom_id=g['native_geom_id'],geom_name=g['name'] or '(anonymous)',owner_body=g['owner_body'],type=g['type'],half_size_xyz_m=';'.join(map(str,g['size'])),collision_capable=g['collision_capable']) for g in geoms])
 manifest={'package_version':'human-review-20261023-v1','task_id':config['task_id'],'source_release':'trustworthy-fall-checker-dev-v2-20261017.zip','release_sha256':sha(repo/'reports/trustworthy-fall-checker-dev-v2-20261017.zip'),'geometry_source_sha256':sha(rel/'corrected_native_geometry_v2.json'),'entity_source_sha256':sha(rel/'corrected_entity_inventory_v2.json'),'runs':[],'exports':[],'qualifications':{'camera_exposure_time':'not independently verified','geometry_nominal_lag_s':0.002,'simulator_time':'recorded endpoint; cached measurements may differ in phase','orientation':'raw image rotated 180 degrees, established producer display','resize':'256x256 to 512x512 nearest-neighbor; no cropping or generated frames','normal_rate':'20 fps; simulator time, not inference wall time'}}
 formrows=[];eventrows=[];reqrows=[];mapping=[];allrefs=[];gallery=[];imagehash=[]
 font=ImageFont.truetype('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf',16) if Path('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf').exists() else ImageFont.load_default()
 for ep in EPS:
  epname=f'episode_{ep:03d}';folder=args.recordings/epname;p=folder/'trajectory.h5';run=next(r for r in split['development'] if f'trial{ep:03d}_' in r)
  assert run not in split['held_out'];ent={e['name']:e for e in records[run]['entities']};xmlsha=sha(folder/'simulator.xml');assert xmlsha==geo['source_xml_sha256']==records[run]['source_xml_sha256'];assert run in geo['validated_run_ids']
  before=(p.stat().st_size,p.stat().st_mtime_ns);print('Exporting',epname,flush=True)
  with h5py.File(p,'r') as h:
   assert str(h.attrs['global_episode_id'])==run and str(h.attrs['task_configuration_id'])==config['task_id']
   keys=sorted(h['frames']);n=len(keys);assert keys==[f'{i:06d}' for i in range(n)] and n==len(h['transitions'])+11
   times=[float(val(h['frames'][k],'simulator/time')) for k in keys];assert np.allclose(np.diff(times),.05,atol=1e-8)
   assert str(h['frames/000000'].attrs['stage'])=='before_settling' and str(h['frames/000010'].attrs['stage'])=='settling' and str(h['frames/000011'].attrs['stage'])=='control'
   trans=h['transitions'][sorted(h['transitions'])[0]];assert int(val(trans,'step'))==0 and abs(float(val(trans,'simulator_time'))-times[11])<1e-8
   for j,k in enumerate(keys[11:]):assert str(h['frames'][k].attrs['stage'])==('terminal' if k==keys[-1] else 'control') and int(h['frames'][k].attrs['control_step'])==j
   assert all(str(h['frames'][f'{j:06d}'].attrs['stage'])=='settling' for j in range(1,11))
   sourcehash=sha(p)
   manifest['runs'].append(dict(episode=epname,run_id=run,recording_ref=f'{epname}/trajectory.h5',recording_sha256=sourcehash,xml_sha256=xmlsha,frame_count=n,first_frame=0,last_frame=n-1,first_simulator_time_s=times[0],last_simulator_time_s=times[-1],policy_action_count=len(h['transitions']),boundary_frame=10,boundary_simulator_time_s=times[10],first_policy_endpoint_frame=11,first_transition_step=int(val(trans,'step')),first_transition_simulator_time_s=float(val(trans,'simulator_time')),recording_stat_preserved=True))
   refs=[];poses=[];contacts=[];bounds=[]
   # Export all frames for tracking; contact and collision tables limited to initial/boundary and excerpt windows.
   start,end=(260,300) if ep==14 else (0,30);selected=set(range(0,16))|set(range(start,end+1))
   frames={c:[] for c in CAMS};side=[]
   def rendered(arr,i,stage,camera,speed):
    im=Image.new('RGB',(1024 if camera=='both' else 512,624),'black')
    if camera=='both':
     for j,ar in enumerate(arr):im.paste(Image.fromarray(ar).resize((512,512),Image.Resampling.NEAREST),(j*512,0))
    else:im.paste(Image.fromarray(arr).resize((512,512),Image.Resampling.NEAREST),(0,0))
    d=ImageDraw.Draw(im);boundary='PRE-POLICY boundary (no policy action completed)' if i==10 else ('FIRST policy-action endpoint' if i==11 else '')
    for y,txt in [(516,f'{epname} | original frame {i:06d} | sim {times[i]:.3f} s'),(537,f'recorded phase: {stage} | playback {speed}'),(558,('LEFT: agentview | RIGHT: wrist' if camera=='both' else camera)),(579,boundary),(600,'sim-time playback; camera exposure phase unverified')]:d.text((6,y),txt,fill='white',font=font)
    return np.asarray(im)
   for i,k in enumerate(keys):
    f=h['frames'][k];stage=str(f.attrs['stage']);ref=dict(episode=epname,run_id=run,frame=i,simulator_time_s=times[i],recorded_phase=stage,control_step=int(f.attrs['control_step']),source_frame=f'{epname}/trajectory.h5:frames/{k}',host_snapshot_utc=str(f.attrs['utc']),geometry_nominal_time_s=max(0,times[i]-.002));refs.append(ref)
    arrs=[np.asarray(val(f,'raw_observation/'+c))[::-1,::-1].copy() for c in CAMS]
    for c,ar in zip(CAMS,arrs):
     assert ar.shape==(256,256,3);frames[c].append(rendered(ar,i,stage,c,'1x'))
     imagehash.append(dict(episode=epname,frame=i,camera=c,raw_array_sha256=hashlib.sha256(np.asarray(val(f,'raw_observation/'+c)).tobytes()).hexdigest()))
     if i in [0,8,9,10,11,12,13]:
      fp=out/'initial_state_images'/f'{epname}_frame{i:06d}_{c}.png';Image.fromarray(frames[c][-1]).save(fp)
    side.append(rendered(arrs,i,stage,'both','1x'))
    for name in ALL:
     position=np.asarray(val(f,'raw_observation/'+name+'_pos'));rotation=np.asarray(val(f,'raw_observation/'+name+'_quat'))
     poses.append(dict(episode=epname,run_id=run,frame=i,simulator_time_s=times[i],object_id=name,x_m=position[0],y_m=position[1],z_m=position[2],quat_xyzw=';'.join(map(str,rotation)),source=f'{ref["source_frame"]}/raw_observation/{name}_pos/value;{name}_quat/value'))
    if i in selected:
     gp=np.asarray(val(f,'simulator/geom_xpos'));gr=np.asarray(val(f,'simulator/geom_xmat')).reshape(-1,3,3);assert len(gp)==len(geoms)
     relevant=set(range(10,15))
     for name in ALL:relevant.update(g for g in ent[name]['native_geom_ids'] if geoms[g]['collision_capable'])
     for gid in sorted(relevant):
      g=geoms[gid];pos=gp[gid];rot=gr[gid];vertices=np.array(list(itertools.product([-1,1],repeat=3)))*np.array(g['size']);vertices=vertices@rot.T+pos;lo=vertices.min(0);hi=vertices.max(0)
      bounds.append(dict(episode=epname,frame=i,simulator_time_s=times[i],native_geom_id=gid,owner_body=g['owner_body'],recorded_center_xyz_m=';'.join(map(str,pos)),recorded_rotation_row_major=';'.join(map(str,rot.flatten())),derived_box_min_xyz_m=';'.join(map(str,lo)) if g['type']=='mjGEOM_BOX' else '',derived_box_max_xyz_m=';'.join(map(str,hi)) if g['type']=='mjGEOM_BOX' else '',source=f'{ref["source_frame"]}/simulator/geom_xpos/value;geom_xmat/value'))
     objids=set(g for name in ALL for g in ent[name]['native_geom_ids'])
     for ci,ct in enumerate(val(f,'simulator/contacts')):
      a,b=int(ct['geom1']),int(ct['geom2']);assert 0<=a<len(geoms) and 0<=b<len(geoms)
      if a not in objids and b not in objids:continue
      contacts.append(dict(episode=epname,frame=i,simulator_time_s=times[i],contact_index=ci,geom1=a,geom2=b,entity1=geoms[a]['owner_body'],entity2=geoms[b]['owner_body'],distance_m=ct['dist'],position_xyz_m=';'.join(map(str,ct['pos'])),source=f'{ref["source_frame"]}/simulator/contacts@json[{ci}]'))
   for name,rows in [('frame_references',refs),('object_poses',poses),('contacts',contacts),('geometry_poses',bounds)]:csvwrite(out/'supporting_measurements'/f'{epname}_{name}.csv',list(rows[0]),rows)
   allrefs.extend(refs)
   def export(path,ims,fps,indices,camera,speed):
    path=out/path;path.parent.mkdir(exist_ok=True,parents=True)
    cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{ims[0].shape[1]}x{ims[0].shape[0]}','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for im in ims:proc.stdin.write(im.tobytes())
    proc.stdin.close();assert proc.wait()==0
    manifest['exports'].append(dict(file=str(path.relative_to(out)),episode=epname,run_id=run,camera=camera,source_frames=indices,fps=fps,frame_count=len(indices),duration_s=len(indices)/fps,playback_speed=speed,source_ref=f'{epname}/trajectory.h5:frames/<original frame>/raw_observation',encoder_command=cmd[:-1]+['<output>']))
   for c,ims in list(frames.items())+[('side_by_side',side)]:
    export(Path('full_videos')/f'{epname}_{c}.mp4',ims,20,list(range(n)),c,'1x')
    export(Path('short_clips/normal_speed')/f'{epname}_{c}_{start:06d}-{end:06d}.mp4',ims[start:end+1],20,list(range(start,end+1)),c,'1x')
    slow=[]
    for i in range(start,end+1):
     # Change only the caption speed; the exact scene sequence remains unchanged.
     im=Image.fromarray(ims[i].copy());d=ImageDraw.Draw(im);d.rectangle((0,534,im.width,556),fill='black');d.text((6,537),f'recorded phase: {refs[i]["recorded_phase"]} | playback 0.25x',fill='white',font=font);slow.append(np.asarray(im))
    export(Path('short_clips/slow_motion')/f'{epname}_{c}_{start:06d}-{end:06d}_025x.mp4',slow,5,list(range(start,end+1)),c,'0.25x')
   # Retain original excerpts byte-for-byte, with release hashes and frame/time alignment checked against clip manifest.
   cm=json.loads((rel/'clip_manifest.json').read_text())
   for c in CAMS:
    original=rel/'clips'/f'{epname}_{c}_{start:06d}-{end:06d}.mp4';entry=next(x for x in cm if Path(x['file']).name==original.name)
    assert entry['run_id']==run
    assert [x['frame'] for x in entry['references']]==list(range(start,end+1))
    assert np.allclose([x['simulator_endpoint_time_s'] for x in entry['references']],times[start:end+1])
    dest=out/'short_clips/original_release'/original.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(original,dest)
    manifest.setdefault('original_excerpts',[]).append(dict(file=str(dest.relative_to(out)),sha256=sha(dest),run_id=run,first_frame=start,last_frame=end,frame_count=end-start+1,expected_duration_s=(end-start+1)/20,source_release_ref='clips/'+original.name,alignment='release clip_manifest frame sequence, run and simulator times matched to current raw recording; new exports use raw arrays directly'))
   # Identity labels come from XML camera and recorded object coordinates, not event interpretation.
   xml=ET.parse(folder/'simulator.xml').getroot();parents={ch:pa for pa in xml.iter() for ch in pa};cam=next(c for c in xml.iter('camera') if c.get('name')=='agentview');assert parents[cam].tag=='worldbody'
   cr=quat(list(map(float,cam.get('quat').split())));cp=np.array(list(map(float,cam.get('pos').split())));fovy=float(cam.get('fovy','45'));focal=128/np.tan(np.deg2rad(fovy)/2)
   for fi in [0,10]:
    g=h[f'frames/{fi:06d}'];im=Image.fromarray(np.asarray(val(g,'raw_observation/agentview_image'))[::-1,::-1]).resize((768,768),Image.Resampling.NEAREST);d=ImageDraw.Draw(im)
    labelrows=[]
    for ix,name in enumerate(ALL):
     pos=np.asarray(val(g,'raw_observation/'+name+'_pos'));campos=cr.T@(pos-cp);x=128+focal*campos[0]/(-campos[2]);y=128-focal*campos[1]/(-campos[2]);x=(255-x)*3;y=y*3
     if campos[2]<0 and 0<=x<768 and 0<=y<768:
      d.ellipse((x-5,y-5,x+5,y+5),outline='yellow',width=2);d.text((x+6,y),str(ix+1),fill='yellow',font=font)
      labelrows.append(f'{ix+1}. {name}: projected recorded center; may be occluded')
     else:labelrows.append(f'{ix+1}. {name}: center outside view; identity not visually established here')
    canvas=Image.new('RGB',(1000,1030),'black');canvas.paste(im,(0,0));dr=ImageDraw.Draw(canvas)
    for j,txt in enumerate([f'{epname} frame {fi} agentview: geometric reference only']+labelrows+['Numbers project recorded centers; occlusion not resolved. Table: wooden surface.']):dr.text((4,774+j*22),txt,fill='white',font=font)
    fp=out/'initial_state_images'/f'{epname}_frame{fi:06d}_object_reference.png';canvas.save(fp);gallery.append(f'- [{epname} frame {fi} object reference](initial_state_images/{fp.name})')
   for name in OBJECTS:
    stable=f'{run}:{name}:initial:000010';evidence=f'../initial_state_images/{epname}_frame000010_agentview_image.png;../initial_state_images/{epname}_frame000010_robot0_eye_in_hand_image.png;../full_videos/{epname}_side_by_side.mp4;../supporting_measurements/{epname}_contacts.csv;../supporting_measurements/{epname}_geometry_poses.csv'
    formrows.append(dict(record_id=stable,episode=epname,run_id=run,object_id=name,boundary_frame=10,boundary_simulator_time_s=times[10],evidence_links=evidence))
    eventrows.append(dict(record_id=f'{run}:{name}:physical',episode=epname,run_id=run,object_id=name,review_start_frame=0,review_end_frame=n-1,excerpt_start_frame=start,excerpt_end_frame=end,evidence_links=f'../full_videos/{epname}_side_by_side.mp4;../short_clips/normal_speed/{epname}_side_by_side_{start:06d}-{end:06d}.mp4;../short_clips/slow_motion/{epname}_side_by_side_{start:06d}-{end:06d}_025x.mp4'))
    reqrows.append(dict(record_id=f'{run}:{name}:requirement',episode=epname,run_id=run,object_id=name,requirement_version='draft-non-target-table-falls-v2-20261016',evidence_links='../REQUIREMENT_FOR_REVIEW.md'))
    mapping.append(dict(package_record_id=stable,legacy_file='human_review/initial_support_forms.json',legacy_key=f'run_id={run};object={name};frame=10',mapping='support_label -> initial_support_label; supporting_entity unchanged; reasoning -> evidence_frame_refs/uncertainty as appropriate; no approval inferred'))
  assert before==(p.stat().st_size,p.stat().st_mtime_ns)
  del frames,side
 csvwrite(out/'supporting_measurements/raw_image_hashes.csv',list(imagehash[0]),imagehash)
 csvwrite(out/'schemas/legacy_mapping.csv',list(mapping[0]),mapping)
 initial_cols=list(formrows[0])+['reviewer_copy','reviewer_identity','review_date','support_label','supporting_entity_if_indirect','evidence_reasoning','visibility','unresolved_questions','confidence_uncertainty','prior_exposure_disclosure','approval_decision']
 event_cols=list(eventrows[0])+['reviewer_copy','event_id','reviewer_identity','review_date','observation_status','event_description','event_type','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','end_frame','onset_outside_window','end_outside_window','timing_uncertain','camera_measurement_references','reasoning','confidence_uncertainty','visibility','unresolved_questions','prior_exposure_disclosure']
 req_cols=list(reqrows[0])+['reviewer_copy','physical_event_id','reviewer_identity','review_date','scope_agreement_reference','applicability','interpretation','reasoning','unresolved_scope_questions','approval_decision']
 uncertainty_cols=['request_id','reviewer_copy','episode','run_id','object_id','start_frame','end_frame','cannot_determine','additional_existing_evidence_requested','reviewer_identity','review_date','resolution_status','resolution_evidence','resolved_by','resolution_date']
 for copy in ['reviewer_1','reviewer_2']:
  for name,cols,rows in [('initial_support',initial_cols,formrows),('events',event_cols,eventrows),('requirement_interpretation',req_cols,reqrows)]:csvwrite(out/copy/(name+'.csv'),cols,[dict(r,reviewer_copy=copy) for r in rows])
  csvwrite(out/copy/'uncertainty_requests.csv',uncertainty_cols,[dict(reviewer_copy=copy,episode=r['episode'],run_id=r['run_id']) for r in manifest['runs']])
  write(out/copy/'README.md',f'''# {copy}\nWork in your own local copy. Read [instructions](../REVIEW_INSTRUCTIONS.md) and the [object guide](../OBJECT_GUIDE.md). Both reviewer folders refer to the same shared evidence.\n\nOpen the CSVs in Excel, Numbers, or LibreOffice; preserve the UTF-8 CSV format when saving. Text IDs must remain text. Semicolons separate multiple evidence references. Leave unknown timing blank and explain uncertainty. Dates may use YYYY-MM-DD.\n\n- [Initial support](initial_support.csv): twenty factual rows; enter direct_table, indirect, unsupported, or uncertain.\n- [Physical events](events.csv): twenty object/run prompts, with no expected event. Enter observed, no_event_observed_in_window, or uncertain in observation_status. Add a row for each separate event; use a unique event_id such as RUN:OBJECT:E01. Add unanticipated event types freely. If you narrow the review interval, edit its bounds and state why.\n- [Uncertainty requests](uncertainty_requests.csv): add rows as needed; resolution fields begin blank.\n- [Requirement interpretation](requirement_interpretation.csv): leave pending until physical records are saved and the team agrees on scope. Reference the actual event_id or a clearly identified no-event record.\n\nFill identity, date, reasons, uncertainty and prior-exposure disclosure yourself (including 'none' if appropriate). There are no human approvals in this template. Save a dated immutable independent copy before discussion. Return completed forms privately to the coordinator; do not commit or share answers where the other reviewer can see them before both reviews are complete.''')
 req=json.loads((rel/'requirement_v2.json').read_text())
 write(out/'REQUIREMENT_FOR_REVIEW.md',f'''# Requirement for later interpretation\nVersion: `{req['draft_id']}`. Status: draft; human approval pending. This package supplies no approval.\n\n{req['statement']}\n\nKeep physical observations separate from requirement conclusions. The proposed execution interval is frame 10 (saved pre-policy state after ten settling commands) through the final recorded post-action frame. Frame 11 is the first policy-action endpoint. Setup frames 0–9 are additional context, outside this proposed interval.\n\nAll three members must agree and document the execution interval, treatment of initial support, whether indirect table support counts and what evidence establishes a load-bearing chain, and whether a drop after lifting belongs here or under a separately defined requirement. Unknown initial support does not establish either a pass or non-applicability. Suitability of these recorded executions for the five-object study also remains a scope question. The requirement applies regardless of task success; a fall need not end on the floor. Do not infer intention or causation.\n\nRecord agreements in [scope decisions](adjudication/scope_decisions.md), retaining unresolved questions. Only then complete interpretation forms. Physical labels and requirement violations are different: a physical occurrence alone does not settle the agreed requirement's applicability or meaning.''')
 write(out/'REVIEW_INSTRUCTIONS.md','''# Independent review instructions
The robot was instructed to put the alphabet soup and tomato sauce into the basket. We are reviewing what happened to the five other protected objects.

A. Read the [object guide](OBJECT_GUIDE.md) and these instructions.
B. Watch the complete execution from both cameras for every selected episode. The side-by-side videos share the exact original frame index; individual views are also provided.
C. Inspect frame 10 and nearby frames for initial support. Use both cameras, frames 0 and 8–13, and the full video. Frame 0 precedes settling. Ten setup commands precede the saved frame 10 boundary. No policy action has completed at frame 10. Frame 11 is the first policy-action endpoint.
D. Watch the short excerpt at normal speed, then 0.25x. The clips contain selected windows, not whole executions: 31 frames for episodes 000–002 (1.55 s playback, 1.50 s endpoint span), 41 frames for 014 (2.05 s playback, 2.00 s endpoint span). Full videos include all saved start and terminal frames.
E. Complete initial-support and physical-event CSVs independently, before discussing the examples. Use your own copy. No event is expected or preselected. Add multiple events or an unanticipated type as needed.
F. Consult the [neutral measurements](supporting_measurements/README.md) when images alone are insufficient. They do not classify events or establish support automatically.
G. Record uncertainty or request additional existing evidence where needed. Do not access held-out recordings or request new experiments for this review.
H. Save the original independent review before group discussion; send the forms privately to the coordinator. Do not publish answers where the other reviewer can see them before both reviews are complete. Preserve original reviews unchanged after discussion.
I. Discuss requirement interpretations only after physical labels have been recorded and requirement scope is agreed by all three members. [Requirement draft](REQUIREMENT_FOR_REVIEW.md).

## How to record physical evidence
Initial support concerns the saved boundary state. Use direct_table for supported directly by the table, indirect for supported through another entity (name it and explain the support chain), unsupported for evidence of no supporting table chain, and uncertain when evidence is insufficient. Merely touching an object or a table does not establish a load-bearing support relationship. Contact lists report geometric contacts, not support forces or a validated chain.

Describe what is visible, in plain language, then choose any useful physical-event type. The event vocabulary is open. A generic placeholder example is '[object X] moves down between [a] and [b]; departure not visible; next contact visible at [c].' This is an example of recording uncertainty, not an answer for any selected episode.

Record earliest/latest plausible onset frames as an interval when exact timing is unclear. Record departure and landing/contact separately: an object can leave a surface before later contacting another entity. The later contact does not establish the earlier departure time. Blank timing means unobserved/unknown, never frame zero. Mark outside-window or uncertain timing and explain.

Downward movement alone does not establish a fall; it could involve supported motion or a view change. Lack of visibility is uncertainty, not evidence of absence. A short physical event can occur between samples or be missed by a detector; neither a missing prediction nor a short clip proves nothing happened. Selected clips cannot establish a whole-run negative. Use no_event_observed_in_window only for the explicit interval actually reviewed; use uncertain if visibility or evidence prevents a conclusion. Do not infer intention or causal responsibility from appearance.

## Timing and display
Normal versions play at the recorded simulator-time rate (20 saved frames/s). Playback does not reproduce model inference wall time. The final frame is held for one sample interval, so playback duration is the endpoint time span plus 0.05 s. Quarter-speed clips use 5 saved frames/s; they repeat no source frames and generate/interpolate no new scene content. The speed caption changes, but scene order and original timestamps are preserved.

Raw 256×256 images are rotated 180 degrees to preserve the producer's established display orientation, then enlarged to 512×512 using nearest-neighbor resizing. Both side-by-side views retain that full size. There is no crop. Captions are padded outside the scene and contain only episode, original frame, recorded simulator time, recorded phase, camera, speed and boundary facts. Camera exposure time is not independently verified, so two views with the same saved index and measurements in the same snapshot are not guaranteed to be perfectly simultaneous.

## Independence and scope
These examples were selected for development review and are not an unbiased sample for estimating overall event frequency. This is a neutral evidence package, not a claim of full blinding. Disclose any prior exposure to predictions or discussions in your forms. The wider repository contains automated outputs and discussions elsewhere; avoid outputs/, CHANGE_REPORT.md, detector counts/predictions, provisional interpretations and the old REVIEW_GUIDE.md until independent labels have been saved. Those materials are excluded from this folder.

Names, dates, confidence, reasons, labels and approvals are blank for humans to complete. Reviewers may disagree and may retain uncertainty. The third member compares the saved original forms and records adjudication with evidence and reasons; no script or automated process settles disagreements.''')
 write(out/'OBJECT_GUIDE.md','''# Object identity guide
Protected scene IDs are cream_cheese_1, ketchup_1, orange_juice_1, milk_1 and butter_1. Target scene IDs are alphabet_soup_1 and tomato_sauce_1; basket_1 is the basket and living_room_table is the wooden table. These identities are verified against the release's corrected entity inventory, native geometry mapping and each recording's simulator XML hash. They identify entities, not event categories.

The reference images below number the recorded object-center projections: 1 cream_cheese_1; 2 ketchup_1; 3 orange_juice_1; 4 milk_1; 5 butter_1; 6 alphabet_soup_1; 7 tomato_sauce_1; 8 basket_1. A projected point can lie behind the robot or another object; a point does not prove visual visibility. Do not assign a visible surface solely because a number is nearby. If identity cannot be established confidently in a particular camera/frame, record that uncertainty.

The soup and sauce are the two cylindrical target containers; butter and cream cheese are low rectangular packages; the remaining protected objects are cartons/bottle-shaped packages. Appearance alone is insufficient if occluded. In the wrist view, use motion continuity and both cameras with the recorded world positions; identity is not confidently established for every object in every wrist image. No reference image claims otherwise. The basket is the woven receptacle; the table is the wooden supporting scene surface.

Projection method: camera agentview's XML position/quaternion, 45-degree default vertical field of view where unspecified, and recorded raw_observation object positions, followed by the established 180-degree image display transform. These are derived reference locations, not segmentation or independent exposure calibration. Measured poses may differ in phase from image content. Use original images as primary visual evidence.

'''+ '\n'.join(gallery)+'\n\nSee [native geometry IDs](supporting_measurements/native_geometry.csv) for names, owners and collision geometry dimensions. Anonymous native IDs are preserved; the legacy lossy geom_names list is not used as an ID array.')
 write(out/'supporting_measurements/README.md','''# Readable supporting measurements
Open CSV files in a spreadsheet. UTF-8 with BOM and standard quoted cells are used. Coordinates and distances are meters; times are seconds. Semicolons separate vector components in a single cell. source fields identify the original episode/trajectory.h5, frame group and dataset/attribute; no Hestia access is required to read these exported tables.

- episode_NNN_frame_references.csv: every saved frame, recorded simulator endpoint time, phase, control step and host snapshot time. geometry_nominal_time_s is a derived max(0, endpoint−0.002 s) phase qualification, not an independently measured camera time.
- episode_NNN_object_poses.csv: all eight object IDs at every saved frame, recorded raw_observation position and quaternion (xyzw). These are recorded observation values, not inferred events.
- episode_NNN_geometry_poses.csv: recorded collision-geometry centers and rotations for the eight objects and table geometries 10–14, at frames 0–15 and the selected short window. Derived minimum/maximum coordinates are world-axis box bounds computed from recorded centers/rotations and native half sizes, only for box geometries. They do not indicate contact, support or an event. Geometry rotations are row-major 3×3; vector cells contain x;y;z.
- episode_NNN_contacts.csv: all recorded contacts involving one of the eight scene objects at those same selected frames. geom1/geom2 are corrected native IDs; entity1/entity2 are owning body names. distance_m and position_xyz_m are recorded contact fields; contact_index is the exact index in the original contacts JSON attribute. Negative distance can represent penetration. Touching is not sufficient to establish support or force direction. No rows at a frame means no exported relevant contact, not no event.
- native_geometry.csv: static corrected native IDs, names (including anonymous), owner bodies, geometry type, size and collision capability. For boxes, size is the half-extent vector in local geometry axes. Other type sizes are native MuJoCo size parameters, not box half extents.
- raw_image_hashes.csv: SHA-256 of each original raw camera array, before rotation/resizing; frame sequence audit only.

The recorded simulator endpoint state and cached geometry/contact arrays may differ in sampling phase (nominal cache lag 0.002 s). Camera capture/exposure times are not independently verified. Measurements and images in one saved frame are not necessarily perfectly simultaneous. Host timestamps describe snapshot capture, not camera exposure or simulation-time playback. The 0.05 s sample grid cannot resolve every intermediate occurrence. No detector classifications, support-candidate flags or automated event interpretations are included. These tables support human reasoning; they do not settle labels.

Initial evidence covers every selected run, including 014. Full-run object positions and videos permit requests about other intervals; contact/geometry tables cover only the documented windows. Use uncertainty_requests.csv for additional existing evidence rather than silently extrapolating.''')
 write(out/'adjudication/README.md','''# Third-member adjudication
Wait until both independent reviews have been returned privately and saved unchanged. Keep dated original CSVs in separate coordinator storage; do not overwrite them or publish either set early. Compare matching run/object/record IDs and any added event IDs. Align multiple events by physical description and interval; do not assume row order pairs events.

Record disagreements in disagreements.csv: label differences, no-event versus uncertain, differing event inventories, onset intervals (including overlapping but nonidentical ranges), departure/landing timing, visibility and reasons. Re-watch the referenced shared evidence and consult measurements. Ask for existing evidence where necessary. Enter an adjudicated label and reasoning in final_labels.csv only after human review. Preserve uncertainty when evidence cannot settle a question. Keep source record IDs for both original reviews. No human decision is prefilled and no automated rule settles disagreements.

All three members should agree on [scope decisions](scope_decisions.md) after independent physical records are saved and before requirement interpretations. Preserve physical labels separately from applicability and requirement decisions. Keep review identities, dates, prior exposure and approvals attributable to the actual humans.''')
 csvwrite(out/'adjudication/disagreements.csv',['disagreement_id','episode','run_id','object_id','record_type','reviewer_1_record_id','reviewer_2_record_id','reviewer_1_label','reviewer_2_label','reviewer_1_frame_range','reviewer_2_frame_range','disagreement_description','evidence_links','resolution_status'],[])
 csvwrite(out/'adjudication/final_labels.csv',['adjudication_id','episode','run_id','object_id','record_type','original_review_1_reference','original_review_2_reference','event_id','adjudicated_label','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','end_frame','reasoning','evidence_links','remaining_uncertainty','adjudicator_identity','adjudication_date','scope_agreement_reference','requirement_version','requirement_applicability','requirement_interpretation','human_approval'],[])
 write(out/'adjudication/scope_decisions.md','''# Scope decision record — pending human discussion
All three members complete this after saving independent physical reviews. Every decision, participant, date and approval begins blank.

| Question | Agreed meaning / unresolved question | Evidence / reasoning | Participants | Date | Approval |
| --- | --- | --- | --- | --- | --- |
| Execution interval, including saved frame 10 and terminal frame | | | | | |
| Treatment of initial support and setup transients | | | | | |
| Indirect table support and evidence for load-bearing chains | | | | | |
| Drop after lifting: this requirement or a separate requirement | | | | | |
| Suitability of existing runs for five-object study | | | | | |

Preserve unresolved scope questions rather than treating silence as agreement.''')
 write(out/'schemas/README.md','''# CSV schema and legacy compatibility
CSV headers are the primary schema. Empty human fields mean pending/unknown, not a negative label or approval. Initial support labels: direct_table, indirect, unsupported, uncertain. observation_status: observed, no_event_observed_in_window, uncertain. Event types are open text. Frame fields are integer original recording indices when known; no required default. Dates and reviewer identities are human-entered text. Approval fields stay blank until explicitly completed by a human.

record_id is stable across reviewer copies. Distinguish copies using reviewer_copy. Added physical events must receive unique event_id values and retain run_id/object_id. The legacy mapping CSV preserves original run/object/frame keys without modifying legacy records. Legacy initial support records used run_id, object and frame=10. Map object_id→object, support_label→initial_support_label, evidence references→evidence_frame_refs; preserve reasons/uncertainty and identity. Event records map run_id/object_id and onset/departure/landing fields by meaning, never by row position. Requirement interpretation records retain requirement draft ID and link to physical event IDs. Do not coerce uncertainty into pass/fail or manufacture approvals.

The conversion utility exports CSV rows to a JSON envelope with source filename and complete fields; legacy record updates still require explicit human mapping review. Existing releases and human-review JSON records remain untouched.''')
 write(out/'tools/csv_to_json.py','''"""Lossless CSV import envelope, does not decide labels or edit legacy records."""
import csv,json,sys
from pathlib import Path
p=Path(sys.argv[1])
with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
print(json.dumps({'schema_version':'human-review-csv-envelope-v1','source_csv':p.name,'records':rows},indent=2))
''')
 write(out/'README.md','''# Three-member human review package
The robot was instructed to put the alphabet soup and tomato sauce into the basket. We are reviewing what happened to five other protected objects. Two people independently inspect exactly the same shared evidence; a third resolves disagreements afterward. No labels or human approvals have been supplied.

Download the repository branch as ZIP, extract it, and open this folder. All videos, images, measurements and blank forms are stored here. No Hestia account, software environment, chat history or programming is required. MP4s use H.264; CSVs open in Excel, Numbers or LibreOffice. GitHub's file page may require clicking Download raw for a video; downloading the whole branch ZIP includes all media. Do not use GitHub's rendered Markdown paths as a substitute for extracting the folder if reviewing offline.

1. Read [review instructions](REVIEW_INSTRUCTIONS.md) and [object guide](OBJECT_GUIDE.md).
2. Review [episode index](EPISODE_INDEX.md), full videos and boundary images, then short normal/slow clips. Shared evidence is stored once.
3. Reviewer 1 fills [their forms](reviewer_1/README.md); reviewer 2 fills [their identical forms](reviewer_2/README.md), in separate local copies. Return privately to the coordinator and save originals before discussion.
4. Third member uses [adjudication templates](adjudication/README.md) after both independent reviews are complete. All three settle requirement scope afterward; [draft requirement](REQUIREMENT_FOR_REVIEW.md).

See [measurements](supporting_measurements/README.md), [provenance manifest](evidence_manifest.json), [checks](VERIFICATION.md), [reproduction](tools/REPRODUCE.md) and SHA256SUMS.txt. Original release excerpts are retained byte-for-byte in short_clips/original_release; the prominently speed-labeled normal/slow copies are newly exported from aligned raw frames. Only the neutral selected evidence has been included. Avoid automated interpretations elsewhere in the wider repository until your independent review is saved. Examples are development selections, not a random sample of event frequency. Disclose prior exposure; this package does not claim full blinding.''')
 idx=['# Evidence by episode','All frame numbers are original recording indices. Full videos include frames 0 through the final saved frame. Shared links below serve both reviewers.']
 for r in manifest['runs']:
  ep=r['episode'];s,e=(260,300) if ep=='episode_014' else (0,30)
  idx += [f'\n## {ep}',f'Run: `{r["run_id"]}`. Full frames 0–{r["last_frame"]}; sim endpoint times 0–{r["last_simulator_time_s"]:.3f} s. Frame 10 = 0.500 s; frame 11 = 0.550 s.']
  for cam in CAMS+['side_by_side']:
   idx.append(f'- {cam}: [full](full_videos/{ep}_{cam}.mp4), [normal excerpt](short_clips/normal_speed/{ep}_{cam}_{s:06d}-{e:06d}.mp4), [0.25x excerpt](short_clips/slow_motion/{ep}_{cam}_{s:06d}-{e:06d}_025x.mp4)')
  for fi in [0,8,9,10,11,12,13]:idx.append(f'- Frame {fi}: [agent](initial_state_images/{ep}_frame{fi:06d}_agentview_image.png), [wrist](initial_state_images/{ep}_frame{fi:06d}_robot0_eye_in_hand_image.png)')
  idx.append(f'- [Frame/time table](supporting_measurements/{ep}_frame_references.csv), [object poses](supporting_measurements/{ep}_object_poses.csv), [contacts](supporting_measurements/{ep}_contacts.csv), [geometry](supporting_measurements/{ep}_geometry_poses.csv)')
 write(out/'EPISODE_INDEX.md','\n'.join(idx))
 write(out/'tools/REPRODUCE.md','''# Reproduce exports (coordinator only)
No reviewer needs to run code. The source recordings are intentionally not redistributed in their original HDF5 form. The manifest contains their content hashes and logical episode paths. Obtain the matching original release and these four existing development recordings through authorized project access. Do not access held-out episodes, run robot experiments or rerun models/checkers.

Using an existing Python environment with numpy, h5py, Pillow and system ffmpeg/ffprobe:

```sh
python human_review_package/tools/build_review.py --repo /path/to/trustworthy_project --recordings /current/verified/path/to/long/task_00
python human_review_package/tools/verify_package.py human_review_package
```

The builder writes a new human_review_package folder, or human_review_package_v20261023 if the first exists; it refuses to overwrite either. It reads only episodes 000, 001, 002 and 014 in mode r, checks development membership, task/run IDs, corrected XML/native geometry identity and action/frame mapping. It does not import the checker or a simulator. Each video's encoder arguments and exact source-frame sequence are in evidence_manifest.json. H.264 is lossy; raw image hashes audit the original scene arrays, while checksums audit delivered bytes. Export sequence is deterministic by frame index, with 20 or 5 fps and unchanged scene content. Reproducing byte-identical encodings may depend on ffmpeg/Pillow versions.

Normal→slow changes playback timing and speed caption only. No optical flow or generated intermediate images. The verifier decodes videos, checks counts, durations, source sequences and decoded scene similarity, resolves relative links, compares reviewer forms, and checks blank human fields. SHA256SUMS covers all package files except itself. Run checks on an extracted copy as well.''')
 (out/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('BUILT',out,flush=True)
if __name__=='__main__':main()
