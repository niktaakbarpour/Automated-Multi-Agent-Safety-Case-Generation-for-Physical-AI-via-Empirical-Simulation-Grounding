import csv,json,gzip,math
from pathlib import Path
B=Path('/Users/nikta/trustworthy-ai-evaluator-1');P=B/'reviewer_1_R1_20'
def rows(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
g=rows(P/'native_geometry.csv');ass=rows(P/'ASSIGNMENTS.csv');out=[]
for a in ass:
 c=a['case_id'];o=a['object_id']; data=json.load(gzip.open(P/'evidence'/c/'recorded_geometry.json.gz','rt'))
 geoms=[r for r in g if r['owner_body']==o+'_main' and r['collision_capable']=='True']
 for frame in data:
  ranges=[]
  for r in geoms:
   k=int(r['native_geom_id']);v=frame['geom_xpos'][k];m=frame['geom_xmat'][k];s=json.loads(r['half_size_xyz'])
   if isinstance(m[0],list):m=sum(m,[])
   e=sum(abs(m[6+j])*s[j] for j in range(3))
   ranges.append((v[2]-e,v[2]+e))
  t=frame['geom_xpos'][10];m=frame['geom_xmat'][10];s=json.loads(g[10]['half_size_xyz'])
  if isinstance(m[0],list):m=sum(m,[])
  top=t[2]+sum(abs(m[6+j])*s[j] for j in range(3))
  out.append(dict(case_id=c,object_id=o,frame=frame['frame'],time=frame['time'],collision_min_z_m=min(r[0] for r in ranges),collision_max_z_m=max(r[1] for r in ranges),tabletop_z_m=top,gap_above_tabletop_m=min(r[0] for r in ranges)-top))
with open(B/'geometry_by_frame.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
for a in ass:
 rr=[r for r in out if r['case_id']==a['case_id'] and r['frame']==10][0];print(a['case_id'],{k:round(v,6) for k,v in rr.items() if isinstance(v,float)})
