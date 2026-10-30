import csv,json,gzip,collections,math
from pathlib import Path
B=Path('/Users/nikta/trustworthy-ai-evaluator-1'); P=B/'reviewer_1_R1_20'
def rows(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
assign=rows(P/'ASSIGNMENTS.csv'); result={}
for a in assign:
 c=a['case_id']; o=a['object_id']; p=P/'evidence'/c
 poses={int(r['frame']):json.loads(r['xyz_m']) for r in rows(p/'object_poses.csv') if r['object_id']==o}
 contacts=collections.defaultdict(set)
 raw=rows(p/'contacts.csv')
 for r in raw:
  if r['owner1'].startswith(o): contacts[int(r['frame'])].add(r['owner2'])
  if r['owner2'].startswith(o): contacts[int(r['frame'])].add(r['owner1'])
 runs=[]
 for f in poses:
  v=sorted(contacts[f])
  if runs and runs[-1]['contacts']==v: runs[-1]['end']=f
  else:runs.append({'start':f,'end':f,'contacts':v})
 geometry=json.load(gzip.open(p/'recorded_geometry.json.gz','rt'))
 print(c,o,'instruction:',(p/'EVIDENCE.md').read_text().splitlines()[2])
 print('poses 0,8-13,end:',{f:[round(x,5) for x in poses[f]] for f in [0,8,9,10,11,12,13,max(poses)]})
 print('xyz ranges:',[(round(min(v[i] for v in poses.values()),5),round(max(v[i] for v in poses.values()),5)) for i in range(3)])
 print('contact runs:',runs)
 z=[(f,round(poses[f][2]-poses[f-1][2],5)) for f in poses if f>0]
 print('largest downward steps:',sorted(z,key=lambda x:x[1])[:8])
 neighbors=set(contacts[10]); print('frame10 neighbor contacts:',[(r['owner1'],r['owner2']) for r in raw if int(r['frame'])==10 and (r['owner1'] in neighbors or r['owner2'] in neighbors)][:25])
 result[c]={'object':o,'poses':poses,'contact_runs':runs,'visual_sample_frames':sorted(set(list(range(31))+list(range(32,len(poses),4))+[max(poses)]))}
(B/'measurements_summary.json').write_text(json.dumps(result,indent=2))
