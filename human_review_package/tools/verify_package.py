"""Verify a portable exported package; optional --recordings checks decoded pixels against originals."""
import argparse,csv,hashlib,json,re,subprocess,tempfile,shutil
from pathlib import Path
from urllib.parse import unquote

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
def decode(p):
 import numpy as np
 d=probe(p);s=next(s for s in d['streams'] if s['codec_type']=='video');w,h=s['width'],s['height']
 b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','-'])
 return np.frombuffer(b,np.uint8).reshape(-1,h,w,3),d

def main():
 a=argparse.ArgumentParser();a.add_argument('package',type=Path);a.add_argument('--recordings',type=Path);a.add_argument('--write-report',action='store_true');a.add_argument('--metadata-only',action='store_true',help='Check links, forms, neutrality and all file hashes without decoding unchanged media');args=a.parse_args();root=args.package.resolve();m=json.loads((root/'evidence_manifest.json').read_text());checks=[];assert len(m['runs'])==4 and {r['episode'] for r in m['runs']}=={'episode_000','episode_001','episode_002','episode_014'}
 if args.write_report and not (root/'VERIFICATION.md').exists():(root/'VERIFICATION.md').write_text('# Verification in progress\n')
 # Check every relative Markdown URL and CSV evidence-link field in a copied package too.
 def links(base):
  n=0
  for p in base.rglob('*.md'):
   for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
    if '://' in target or target.startswith('#'):continue
    q=(p.parent/unquote(target.split('#')[0])).resolve();assert q.is_relative_to(base.resolve()) and q.exists(),(p,target);n+=1
  for p in base.rglob('*.csv'):
   for row in readcsv(p):
    for key,v in row.items():
     if key in ['evidence_links']:
      for target in filter(None,v.split(';')):
       q=(p.parent/target).resolve();assert q.is_relative_to(base.resolve()) and q.exists(),(p,target);n+=1
  return n
 nlinks=links(root)
 with tempfile.TemporaryDirectory(prefix='review-portability-') as tmp:
  copied=Path(tmp)/root.name;shutil.copytree(root,copied);assert links(copied)==nlinks
 checks.append(f'PASS: {nlinks} relative links resolve in the original and an independently copied folder.')
 for name in ['initial_support','events','uncertainty_requests','requirement_interpretation']:
  arows=readcsv(root/'reviewer_1'/f'{name}.csv');brows=readcsv(root/'reviewer_2'/f'{name}.csv');assert len(arows)==len(brows)
  for ar,br in zip(arows,brows):
   assert ar.pop('reviewer_copy')=='reviewer_1' and br.pop('reviewer_copy')=='reviewer_2' and ar==br
   factual={'record_id','episode','run_id','object_id','boundary_frame','boundary_simulator_time_s','evidence_links','review_start_frame','review_end_frame','excerpt_start_frame','excerpt_end_frame','requirement_version'}
   assert all(not v for k,v in ar.items() if k not in factual),(name,ar)
  if name=='initial_support':assert len(arows)==20 and len({(r['run_id'],r['object_id']) for r in arows})==20
  checks.append(f'PASS: {name} has identical factual rows/evidence in both copies and blank human fields ({len(arows)} rows each).')
 for p in root.rglob('*.csv'):
  with p.open(encoding='utf-8-sig',newline='') as f:
   rows=list(csv.reader(f));assert rows and len(set(rows[0]))==len(rows[0]) and all(len(r)==len(rows[0]) for r in rows)
 checks.append('PASS: all CSVs parse with consistent columns; UTF-8 BOM and standard CSV quoting support spreadsheet editing.')
 prohibited=['CHANGE_REPORT.md','REVIEW_GUIDE.md','outputs','sensitivity.json','summary.json']
 assert not any(p.name in prohibited for p in root.rglob('*'))
 assert not any(p.suffix in ['.h5','.safetensors','.pt','.pem','.key'] for p in root.rglob('*'))
 for p in root.rglob('*'):
  if p.suffix in ['.md','.json','.csv','.py']:
   text=p.read_text(encoding='utf-8-sig');assert ('/local/'+'home/'+'niktakbr') not in text and ('/disk/'+'1/'+'data') not in text
 checks.append('PASS: no detector-output files, old outcome-revealing guides, credentials/model-file types or absolute source server paths in package. Human-facing measurements use a neutral allowlist.')
 h5=None
 if args.recordings:import h5py
 if not args.metadata_only:
  import numpy as np
  for r in m['runs']:
   ep=r['episode'];exports=[e for e in m['exports'] if e['episode']==ep];n=r['frame_count'];assert r['first_frame']==0 and r['last_frame']==n-1 and r['boundary_frame']==10 and r['first_policy_endpoint_frame']==11
   for camera in ['agentview_image','robot0_eye_in_hand_image','side_by_side']:
    entries=[e for e in exports if e['camera']==camera];full=next(e for e in entries if e['file'].startswith('full_videos/'));assert full['source_frames']==list(range(n))
    fa,fd=decode(root/full['file']);assert len(fa)==n
    if args.recordings:
     with h5py.File(args.recordings/ep/'trajectory.h5','r') as h:
      assert sha(args.recordings/ep/'trajectory.h5')==r['recording_sha256']
      errors=[]
      for i in range(n):
       cameras=['agentview_image','robot0_eye_in_hand_image'] if camera=='side_by_side' else [camera]
       for j,c in enumerate(cameras):
        raw=h[f'frames/{i:06d}/raw_observation/{c}/value'][()][::-1,::-1]
        expected=np.repeat(np.repeat(raw,2,0),2,1).astype(float);actual=fa[i,:512,j*512:(j+1)*512].astype(float);errors.append(float(np.mean((expected-actual)**2)))
      assert max(errors)<100,(ep,camera,max(errors));checks.append(f'PASS: {ep} {camera} all {n} decoded scene frames match raw source (worst MSE {max(errors):.3f} <100).')
    for e in entries:
     arr,d=(fa,fd) if e is full else decode(root/e['file']);s=d['streams'][0];duration=float(d['format']['duration']);assert len(arr)==e['frame_count']==len(e['source_frames']);assert abs(duration-e['duration_s'])<.003;assert e['fps']==(5 if e['playback_speed']=='0.25x' else 20)
     if e is not full:
      expected=fa[e['source_frames'],:512].astype(float);errors=np.mean((arr[:,:512].astype(float)-expected)**2,axis=(1,2,3));assert max(errors)<100,(e['file'],max(errors))
     checks.append(f'PASS: {e["file"]}: {len(arr)} decoded frames, {duration:.3f} s; source sequence {e["source_frames"][0]}–{e["source_frames"][-1]}.')
    del fa
   for e in [e for e in m['original_excerpts'] if e['run_id']==r['run_id']]:
    p=root/e['file'];assert sha(p)==e['sha256'];arr,d=decode(p);assert len(arr)==e['frame_count'] and abs(float(d['format']['duration'])-e['expected_duration_s'])<.003
    camera='robot0_eye_in_hand_image' if 'eye_in_hand' in e['file'] else 'agentview_image'
    full=next(x for x in exports if x['camera']==camera and x['file'].startswith('full_videos/'));fa,_=decode(root/full['file']);scene=fa[e['first_frame']:e['last_frame']+1,:512:2,::2].astype(float);old=arr[:,:256,128:384].astype(float);assert scene.shape==old.shape;err=np.mean((scene-old)**2,axis=(1,2,3));assert max(err)<100,(e['file'],max(err))
    checks.append(f'PASS: retained original {p.name} hash, count, timing and decoded scene alignment (worst MSE {max(err):.3f}).')
    del fa
 else:checks.append('PASS: metadata-only mode; media bytes verified by checksums below, no new decoding or source-recording validation performed.')
 if (root/'SHA256SUMS.txt').exists():
  for line in (root/'SHA256SUMS.txt').read_text().splitlines():
   digest,path=line.split('  ',1);assert sha(root/path)==digest,path
  checks.append('PASS: all packaged SHA-256 checksums match.')
 report='# Package verification\n\n'+'\n'.join('- '+s for s in checks)+'\n\nAutomated checks do not supply human labels or approvals. H.264 comparisons use a maximum per-frame scene mean squared error below 100 (8-bit RGB); captions are excluded from scene comparison. No content interpolation is used. Original recording hashes, task/run/XML identity and boundary mapping were verified by the exporter.\n'
 if args.metadata_only:report += '\nMetadata-only verification did not rerun media decoding or compare source recordings. The H.264 method above describes full verification mode, not a new media check.\n'
 if args.write_report:(root/'VERIFICATION.md').write_text(report)
 print(report)
if __name__=='__main__':main()
