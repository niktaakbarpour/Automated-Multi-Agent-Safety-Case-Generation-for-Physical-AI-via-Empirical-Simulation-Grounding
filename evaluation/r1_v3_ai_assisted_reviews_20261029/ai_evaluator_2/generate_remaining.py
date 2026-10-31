from pathlib import Path
import subprocess,csv,json
p=Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027/packages/reviewer_2_R1_20');o=p.parent.parent/'ai_evaluator_2_blind_20261029'
a=list(csv.DictReader((p/'ASSIGNMENTS.csv').open(encoding='utf-8-sig')))
for r in a:
 c=r['case_id'];n=int(c[2:]);end=int(r['available_last_frame'])
 if n not in [10,14,15,16,17,18,19,20]:continue
 for start in range(240 if n==10 else 0,end+1,60):
  last=min(end,start+59);dest=o/'visual'/f'{c}_{start}_{last}.jpg'
  vf=f"select='between(n,{start},{last})',scale=320:-1,tile=5x12:nb_frames={last-start+1}:padding=2:margin=2"
  subprocess.run(['/bin/ffmpeg','-v','error','-i',str(p/r['full_video']),'-vf',vf,'-frames:v','1','-q:v','7','-y',str(dest)],check=True)
  print(dest.name,flush=True)
