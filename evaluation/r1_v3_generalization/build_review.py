"""Evidence-only export for blinded independent R1 annotation.

Reads original recordings and an identity inventory. Never imports the checker,
loads its predictions, chooses event windows, or fills any human answer.
"""
import argparse
import csv
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
CAMS=['agentview_image','robot0_eye_in_hand_image']
OBJECTS=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def val(g,p):
    import h5py
    node=g[p]
    if isinstance(node,h5py.Dataset):return node[()]
    if 'value' in node:return node['value'][()]
    return json.loads(node.attrs['json'])


def write_csv(p,fields,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def build(args):
    import numpy as np,h5py
    from PIL import Image,ImageDraw,ImageFont
    inventory=json.loads((args.inventory/'inventory.json').read_text())['records']
    selected=[r for r in inventory if r['selected'] and r['eligible']]
    args.output.mkdir(parents=True,exist_ok=False)
    for name in ['REQUIREMENT_SCOPE_DECISION.md','requirement_scope.v3.json','OBJECT_GUIDE.md']:
        (args.output/name).write_bytes((args.protocol/name).read_bytes())
    geometries=json.loads(args.geometry.read_text())['geometries']
    write_csv(args.output/'native_geometry.csv',['native_geom_id','name','owner_body','type','half_size_xyz','collision_capable'],[dict(native_geom_id=g['native_geom_id'],name=g['name'] or '(anonymous)',owner_body=g['owner_body'],type=g['type'],half_size_xyz=json.dumps(g['size']),collision_capable=g['collision_capable']) for g in geometries])
    initial=[];requirements=[];events=[];manifest=[]
    schema_fields={
      'initial_support.csv':['record_id','run_id','episode','object_id','boundary_frame','boundary_simulator_time_s','evidence_links','reviewer_copy','reviewer_identity','review_date','support_label','supporting_entity_if_indirect','evidence_reasoning','visibility','unresolved_questions','confidence_uncertainty','prior_exposure_disclosure','approval_decision'],
      'events.csv':['record_id','run_id','episode','object_id','review_start_frame','review_end_frame','evidence_links','reviewer_copy','event_id','reviewer_identity','review_date','observation_status','event_description','event_type','earliest_onset_frame','latest_onset_frame','departure_frame','landing_contact_frame','end_frame','onset_outside_window','end_outside_window','timing_uncertain','camera_measurement_references','reasoning','confidence_uncertainty','visibility','unresolved_questions','prior_exposure_disclosure'],
      'requirement_interpretation.csv':['record_id','run_id','episode','object_id','requirement_version','evidence_links','reviewer_copy','physical_event_id','reviewer_identity','review_date','scope_agreement_reference','applicability','interpretation','reasoning','unresolved_scope_questions','approval_decision','review_start_frame','review_end_frame','evidence_coverage','supporting_frame_references','confidence_uncertainty'],
      'uncertainty_requests.csv':['request_id','reviewer_copy','run_id','episode','object_id','start_frame','end_frame','cannot_determine','additional_existing_evidence_requested','reviewer_identity','review_date','resolution_status','resolution_evidence','resolved_by','resolution_date']}
    fontpath=Path('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf')
    font=ImageFont.truetype(str(fontpath),12) if fontpath.exists() else ImageFont.load_default()
    for r in selected:
        run=r['run_id'];source=Path(r['receipts_before'][0]['path']);expected=r['receipts_before'][0]['sha256']
        if sha(source)!=expected:raise ValueError('Source hash mismatch')
        st=source.stat();folder=args.output/'evidence'/run;folder.mkdir(parents=True)
        refs=[];poses=[];contacts=[];imagehashes=[]
        video=folder/'full_side_by_side.mp4'
        cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size','512x336','-framerate','20','-i','-','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            with h5py.File(source,'r') as h,gzip.open(folder/'recorded_geometry.json.gz','wt') as geometry:
                geometry.write('[')
                for fi in range(r['frame_count']):
                    g=h[f'frames/{fi:06d}'];time=float(val(g,'simulator/time'));stage=str(g.attrs['stage'])
                    ref=dict(frame=fi,simulator_time_s=time,recorded_stage=stage,source=f'trajectory.h5:frames/{fi:06d}')
                    refs.append(ref)
                    im=Image.new('RGB',(512,336),'black')
                    for j,camera in enumerate(CAMS):
                        raw=np.asarray(val(g,'raw_observation/'+camera))
                        if raw.shape!=(256,256,3):raise ValueError('Unexpected camera shape')
                        imagehashes.append(dict(frame=fi,camera=camera,raw_array_sha256=hashlib.sha256(raw.tobytes()).hexdigest()))
                        image=Image.fromarray(raw[::-1,::-1].copy());im.paste(image,(j*256,0))
                        if fi in [0,8,9,10,11,12,13]:image.save(folder/f'frame_{fi:06d}_{camera}.png')
                    draw=ImageDraw.Draw(im)
                    for y,text in [(258,f'{r["suite"]} task {r["benchmark_task_id"]:02d} episode {r["episode"]:03d} | saved frame {fi:06d}'),(277,f'simulator {time:.3f}s | {stage} | 20 saved fps'),(296,'LEFT agentview | RIGHT wrist | exposure phase unverified'),(315,'Frame 10: pre-policy boundary; frame 11: first action endpoint')]:draw.text((3,y),text,font=font,fill='white')
                    proc.stdin.write(np.asarray(im).tobytes())
                    bp=np.asarray(val(g,'simulator/body_xpos'));bq=np.asarray(val(g,'simulator/body_xquat'))
                    for name in r['objects_present']:
                        # Native body names are validated per recording; positions remain neutral.
                        body=next((i for i,n in enumerate(r['body_names']) if n==name+'_main'),None)
                        if body is not None:poses.append(dict(frame=fi,simulator_time_s=time,object_id=name,body_native_id=body,xyz_m=json.dumps(bp[body].tolist()),quat_wxyz=json.dumps(bq[body].tolist()),source=ref['source']+'/simulator/body_xpos;body_xquat'))
                    for ci,ct in enumerate(val(g,'simulator/contacts')):
                        a,b=ct['geom1'],ct['geom2']
                        contacts.append(dict(frame=fi,simulator_time_s=time,contact_index=ci,geom1=a,geom2=b,owner1=geometries[a]['owner_body'],owner2=geometries[b]['owner_body'],recorded_signed_distance_m=ct['dist'],position_xyz_m=json.dumps(ct['pos']),source=ref['source']+'/simulator/contacts'))
                    if fi:geometry.write(',')
                    json.dump(dict(frame=fi,time=time,geom_xpos=np.asarray(val(g,'simulator/geom_xpos')).tolist(),geom_xmat=np.asarray(val(g,'simulator/geom_xmat')).tolist()),geometry)
                geometry.write(']')
            proc.stdin.close()
            if proc.wait()!=0:raise RuntimeError('Video encoder failed')
        except Exception:
            if proc.stdin and not proc.stdin.closed:proc.stdin.close()
            proc.wait();raise
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate','-of','json',str(video)],text=True))['streams'][0]
        if int(probe['nb_read_frames'])!=r['frame_count'] or probe['r_frame_rate']!='20/1':raise ValueError('Video frame coverage mismatch')
        for name,rows in [('frame_references',refs),('object_poses',poses),('contacts',contacts),('raw_image_hashes',imagehashes)]:
            if rows:write_csv(folder/(name+'.csv'),list(rows[0]),rows)
        if sha(source)!=expected or source.stat().st_size!=st.st_size or source.stat().st_mtime_ns!=st.st_mtime_ns:raise ValueError('Source changed during export')
        for obj in OBJECTS:
            common=dict(run_id=run,episode=f'episode_{r["episode"]:03d}',object_id=obj,evidence_links=f'../evidence/{run}/full_side_by_side.mp4;../evidence/{run}/frame_references.csv;../evidence/{run}/contacts.csv;../evidence/{run}/object_poses.csv;../evidence/{run}/recorded_geometry.json.gz')
            initial.append(dict(common,record_id=f'{run}:{obj}:initial',boundary_frame=10,boundary_simulator_time_s=.5))
            events.append(dict(common,record_id=f'{run}:{obj}:physical-review',review_start_frame=0,review_end_frame=r['terminal_frame']))
            requirements.append(dict(common,record_id=f'{run}:{obj}:R1',requirement_version='r1-initial-table-support-v3-20261024',review_start_frame=10,review_end_frame=r['terminal_frame']))
        manifest.append(dict(run_id=run,task_id=r['task_id'],episode=r['episode'],frame_count=r['frame_count'],recording_sha256=expected,xml_sha256=r['receipts_before'][1]['sha256'],instruction=json.loads((source.parent/'metadata.json').read_text())['instruction'],video=str(video.relative_to(args.output)),video_sha256=sha(video),video_verified_frames=r['frame_count'],source_stat_preserved=True))
        print('EXPORTED_NEUTRAL',r['suite'],r['benchmark_task_id'],r['episode'],flush=True)
    for reviewer in ['reviewer_1','reviewer_2']:
        for name,rows in [('initial_support.csv',initial),('events.csv',events),('requirement_interpretation.csv',requirements),('uncertainty_requests.csv',[])]:
            fields=schema_fields[name]
            write_csv(args.output/reviewer/name,fields,[{k:(reviewer if k=='reviewer_copy' else row.get(k,'')) for k in fields} for row in rows])
    instructions=(HERE/'REVIEW_INSTRUCTIONS.md').read_text();(args.output/'REVIEW_INSTRUCTIONS.md').write_text(instructions)
    (args.output/'evidence_manifest.json').write_text(json.dumps(dict(runs=manifest,source='original recordings only',predictions_included=False,answers_prefilled=False,scope_unchanged=True,display='Both original 256x256 views rotated 180 degrees; no crop or interpolated frames; 20 saved fps; neutral captions outside images.',qualifications='Geometry nominal lag 0.002 s and camera exposure phase remain unverified. Contacts are geometric, not measured support forces.'),indent=2)+'\n')
    (args.output/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(args.output))+'\n' for p in sorted(args.output.rglob('*')) if p.is_file()))
    print('REVIEW_PACKAGE_COMPLETE',len(manifest),'runs',len(initial),'blank object units',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
    p.add_argument('--geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    build(p.parse_args())
