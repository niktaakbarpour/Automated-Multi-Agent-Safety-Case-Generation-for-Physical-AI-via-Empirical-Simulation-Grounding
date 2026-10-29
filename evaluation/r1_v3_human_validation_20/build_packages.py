"""Actually build two equivalent prediction-blinded packages on Hestia.

Inputs: sampled identity manifest, verified old review evidence and raw recordings.
No checker predictions, reference labels or inference code are loaded.
"""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
CAMS=['agentview_image','robot0_eye_in_hand_image']


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()


def csvwrite(p,fields,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def val(g,p):
    import h5py
    x=g[p]
    if isinstance(x,h5py.Dataset):return x[()]
    if 'value' in x:return x['value'][()]
    return json.loads(x.attrs['json'])


def build(args):
    import numpy as np,h5py
    from PIL import Image,ImageDraw,ImageFont
    old=args.old_review
    expected=json.loads((HERE/'PROVENANCE_FREEZE.json').read_text())
    if sha(args.old_archive)!=expected['source_review_archive_sha256'] or args.old_archive.stat().st_size!=expected['source_review_archive_bytes']:raise ValueError('Original review archive mismatch')
    with tarfile.open(args.old_archive,'r:gz') as archive:
        for name in ['SHA256SUMS.txt','evidence_manifest.json']:
            if archive.extractfile('blinded_review/'+name).read()!=(old/name).read_bytes():raise ValueError('Unbound old archive manifest')
    for n in ['REVIEW_INSTRUCTIONS.md','REQUIREMENT_FOR_REVIEW.md','REQUIREMENT_SCOPE_DECISION.md','requirement_scope.v3.json']:
        if sha(args.protocol/n)!=expected['protected_files']['human_review_package/'+n]:raise ValueError('Authoritative protocol changed')
    checks={}
    for line in (old/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split(maxsplit=1)
        if sha(old/name)!=digest:raise ValueError('Old evidence mismatch: '+name)
        checks[name]=digest
    selection=json.loads((HERE/'COORDINATOR_ASSIGNMENTS.json').read_text())['cases']
    if len(selection)!=20 or len({r['run_id'] for r in selection})!=20:raise ValueError('Expected 20 distinct sampled runs')
    args.output.mkdir(parents=True,exist_ok=False)
    common=args.output/'common';common.mkdir()
    protocol=common/'protocol';protocol.mkdir()
    for n in ['REVIEW_INSTRUCTIONS.md','REQUIREMENT_FOR_REVIEW.md','REQUIREMENT_SCOPE_DECISION.md','requirement_scope.v3.json']:
        shutil.copyfile(args.protocol/n,protocol/n)
    (protocol/'schemas').mkdir()
    for n in ['README.md','requirement_scope.v1.schema.json']:shutil.copyfile(args.protocol/'schemas'/n,protocol/'schemas'/n)
    shutil.copyfile(old/'OBJECT_GUIDE.md',protocol/'OBJECT_GUIDE.md')
    shutil.copyfile(old/'native_geometry.csv',common/'native_geometry.csv')
    shutil.copyfile(HERE/'START_HERE.md',common/'START_HERE.md')
    fontpath=Path('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf')
    font=ImageFont.truetype(str(fontpath),16) if fontpath.exists() else ImageFont.load_default()
    assignments=[];private=[];verified_videos=[]
    for case in selection:
        cid=case['case_id'];src=old/'evidence'/case['run_id'];dest=common/'evidence'/cid;dest.mkdir(parents=True)
        source=args.recordings/('long/task_00' if case['stratum']=='reserved_same_task' else 'long/task_01')/f'episode_{case["episode"]:03d}'/'trajectory.h5'
        if sha(source)!=case['recording_sha256']:raise ValueError('Original recording checksum mismatch')
        before=(source.stat().st_size,source.stat().st_mtime_ns)
        # These exports contain only recorded frame/body/native IDs, no run IDs.
        for n in ['frame_references.csv','object_poses.csv','contacts.csv','raw_image_hashes.csv','recorded_geometry.json.gz']:
            if sha(src/n)!=checks[str((src/n).relative_to(old))]:raise ValueError('Unverified selected measurement')
            shutil.copyfile(src/n,dest/n)
        with (src/'raw_image_hashes.csv').open(encoding='utf-8-sig',newline='') as f:
            image_hashes={(int(r['frame']),r['camera']):r['raw_array_sha256'] for r in csv.DictReader(f)}
        full={};commands={};preview={'agentview':[],'wrist':[],'side_by_side':[]}
        n=case['frame_count'];preview_end=min(30,n-1)
        for view,width in [('agentview',512),('wrist',512),('side_by_side',1024)]:
            path=dest/f'{cid}_{view}_full_1x.mp4'
            cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x624','-framerate','20','-i','-','-map_metadata','-1','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
            full[view]=subprocess.Popen(cmd,stdin=subprocess.PIPE);commands[view]=cmd
        def rendered(arrays,fi,time,stage,view,speed):
            im=Image.new('RGB',(1024 if view=='side_by_side' else 512,624),'black')
            for j,ar in enumerate(arrays):im.paste(Image.fromarray(ar).resize((512,512),Image.Resampling.NEAREST),(j*512,0))
            d=ImageDraw.Draw(im)
            texts=[f'{cid} | original saved frame {fi:06d} | simulator {time:.3f} s',f'recorded phase: {stage} | playback {speed}',('LEFT agentview | RIGHT wrist' if view=='side_by_side' else view),('PRE-POLICY boundary; no policy action completed' if fi==10 else 'FIRST policy-action endpoint' if fi==11 else ''),'camera exposure phase unverified; saved samples only']
            for j,text in enumerate(texts):d.text((5,516+j*21),text,font=font,fill='white')
            return np.asarray(im)
        with h5py.File(source,'r') as h:
            if str(h.attrs['global_episode_id'])!=case['run_id'] or len(h['frames'])!=n:raise ValueError('Wrong selected source')
            for fi in range(n):
                g=h[f'frames/{fi:06d}'];time=float(val(g,'simulator/time'));stage=str(g.attrs['stage'])
                arrays=[np.asarray(val(g,'raw_observation/'+cam)) for cam in CAMS]
                for cam,ar in zip(CAMS,arrays):
                    if ar.shape!=(256,256,3) or hashlib.sha256(ar.tobytes()).hexdigest()!=image_hashes[fi,cam]:raise ValueError('Camera evidence differs from verified 60-run export')
                arrays=[ar[::-1,::-1].copy() for ar in arrays]
                for view,views in [('agentview',[arrays[0]]),('wrist',[arrays[1]]),('side_by_side',arrays)]:
                    image=rendered(views,fi,time,stage,view,'1x');full[view].stdin.write(image.tobytes())
                    if fi<=preview_end:preview[view].append((views,fi,time,stage))
                    if view!='side_by_side' and fi in [0,8,9,10,11,12,13]:Image.fromarray(image).save(dest/f'{cid}_frame{fi:06d}_{view}.png')
        for proc in full.values():
            proc.stdin.close()
            if proc.wait()!=0:raise RuntimeError('Full video encoder failed')
        for view,width in [('agentview',512),('wrist',512),('side_by_side',1024)]:
            for speed,fps in [('1x',20),('025x',5)]:
                path=dest/f'{cid}_{view}_setup_{speed}.mp4'
                cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x624','-framerate',str(fps),'-i','-','-map_metadata','-1','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
                proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
                for views,fi,time,stage in preview[view]:proc.stdin.write(rendered(views,fi,time,stage,view,'0.25x' if fps==5 else '1x').tobytes())
                proc.stdin.close()
                if proc.wait()!=0:raise RuntimeError('Preview encoder failed')
        for path in sorted(dest.glob('*.mp4')):
            st=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate','-of','json',str(path)],text=True))['streams'][0]
            frames=n if '_full_' in path.name else preview_end+1;fps=5 if '_025x' in path.name else 20
            if int(st['nb_read_frames'])!=frames or st['r_frame_rate']!=f'{fps}/1':raise ValueError('Video frame/rate coverage failed')
            verified_videos.append(dict(path=str(path.relative_to(common)),sha256=sha(path),frames=frames,fps=fps))
        if sha(source)!=case['recording_sha256'] or before!=(source.stat().st_size,source.stat().st_mtime_ns):raise ValueError('Original changed during export')
        evidence=f'''# {cid}: neutral evidence summary
Assigned object: `{case['object_id']}`.
Recorded instruction: {case['instruction']}.
Available original saved frames: 0--{n-1}, inclusive ({n} snapshots).
R1 requested interval: 10--{n-1}. This is available scope, not a prefilled review claim.
Both cameras have every saved frame; individual and side-by-side full views are supplied.
Setup previews: frames 0--{preview_end}, normal speed and 0.25x; not whole-run evidence.
Boundary PNGs: frames 0,8,9,10,11,12,13 in both views.
Neutral measurements: complete saved contacts, native geometry transforms, body poses,
frame/time/stage references and raw image hashes. See ../../native_geometry.csv.
Contact/geometry nominal lag is 0.002 s; camera exposure phase is unverified.
Contact lists do not measure load bearing. Missing visibility remains uncertainty.
No support, event, applicability or requirement outcome has been assigned here.
'''
        (dest/'EVIDENCE.md').write_text(evidence)
        assignments.append(dict(case_id=cid,object_id=case['object_id'],available_first_frame=0,available_last_frame=n-1,R1_start_frame=10,full_video=f'evidence/{cid}/{cid}_side_by_side_full_1x.mp4',evidence_summary=f'evidence/{cid}/EVIDENCE.md'))
        private.append(dict(case_id=cid,run_id=case['run_id'],object_id=case['object_id'],recording_sha256=case['recording_sha256'],all_raw_camera_arrays_match_old_export=True,source_stat_preserved=True))
        print('BUILT_NEUTRAL_CASE',cid,flush=True)
    csvwrite(common/'ASSIGNMENTS.csv',list(assignments[0]),assignments)
    headers=json.loads((HERE/'FORM_HEADERS.json').read_text());reports=[]
    # Both reviewers receive byte-identical common evidence and protocol files.
    for reviewer in ['reviewer_1','reviewer_2']:
        out=args.output/f'{reviewer}_R1_20';shutil.copytree(common,out)
        annotations=out/'annotations';annotations.mkdir();(annotations/'physical_stage').mkdir()
        (annotations/'physical_stage/README.md').write_text('Save unchanged copies of initial_support.csv, events.csv and uncertainty_requests.csv here before completing requirement_interpretation.csv. Do not edit the saved physical-stage snapshot.\n')
        for filename,fields in headers.items():
            rows=[]
            if filename!='uncertainty_requests.csv':
                for case in selection:
                    cid=case['case_id'];obj=case['object_id'];kind=filename.split('.')[0]
                    metadata=dict(record_id=f'{cid}:{obj}:{kind}',episode=cid,run_id=cid,object_id=obj,reviewer_copy=reviewer,
                        evidence_links=f'../evidence/{cid}/EVIDENCE.md;../evidence/{cid}/{cid}_side_by_side_full_1x.mp4;../evidence/{cid}/contacts.csv;../evidence/{cid}/object_poses.csv;../evidence/{cid}/recorded_geometry.json.gz')
                    if filename=='initial_support.csv':metadata.update(boundary_frame=10,boundary_simulator_time_s=.5)
                    if filename=='events.csv':metadata.update(excerpt_start_frame=0,excerpt_end_frame=case['frame_count']-1)
                    if filename=='requirement_interpretation.csv':metadata.update(requirement_version='r1-initial-table-support-v3-20261024')
                    rows.append({k:metadata.get(k,'') for k in fields})
            csvwrite(annotations/filename,fields,rows)
        (out/'RETURN_INSTRUCTIONS.md').write_text(f'''# Private submission for {reviewer}
Complete all four original CSV categories in annotations/. Keep neutral NVxx aliases.
Save the physical-stage snapshot before requirement interpretation as START_HERE specifies.
Do not change other package files or consult another reviewer's answers.
From inside this extracted package, create the return ZIP:

    python3 -m zipfile -c {reviewer}_R1_20_return.zip annotations

Send only {reviewer}_R1_20_return.zip privately to the coordinator through the agreed
private channel. Do not upload answers to a public repository or the other reviewer.
Return all twenty cases, including uncertainty and non-applicability. Do not attach
an automatically inferred label file. The coordinator preserves your original bytes;
a separate third researcher adjudicates after both submissions arrive.
''')
        public=dict(reviewer_id=reviewer,case_count=20,recording_count=20,case_ids=[c['case_id'] for c in selection],video_count=180,annotation_categories=list(headers),case_assignments=assignments,files_equivalent_except_reviewer_metadata=True,source_evidence_verified=True,source_answers_included=False,checker_outputs_included=False)
        (out/'REVIEWER_MANIFEST.json').write_text(json.dumps(public,indent=2)+'\n')
        files={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in files.items()))
        archive=args.output/f'{reviewer}_R1_20.tar.gz'
        with tarfile.open(archive,'w:gz') as t:t.add(out,arcname=out.name)
        reports.append(dict(reviewer_id=reviewer,archive_path=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),videos=180,full_videos=60,setup_preview_videos=120,object_execution_cases=20,distinct_recordings=20))
    proof=dict(source_archive_sha256=sha(args.old_archive),source_files_verified=len(checks),selected_source_cases=private,video_verification=verified_videos,archives=reports,unavailable_evidence=[],reviewer_packages_equivalent=True)
    (args.output/'BUILD_REPORT.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('PACKAGES_COMPLETE',json.dumps(reports),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old-review',type=Path,required=True);p.add_argument('--old-archive',type=Path,required=True)
    p.add_argument('--recordings',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    build(p.parse_args())
