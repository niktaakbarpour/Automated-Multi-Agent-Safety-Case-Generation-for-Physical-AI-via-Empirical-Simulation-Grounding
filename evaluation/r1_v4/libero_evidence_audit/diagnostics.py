"""Reproduce small measurement windows from the same selected development exports."""
import gzip,json,socket
from .audit_sources import ROOT,HERE,V2,load,bounds,csvwrite,sha

def main():
 assert socket.gethostname().lower()=='hestia'
 rows=[];gs=load(ROOT/(V2+'corrected_native_geometry_v2.json'))['geometries']
 for ep,window in [(0,range(9,12)),(2,range(7,13)),(14,range(274,286))]:
  p=ROOT/f'reports/fall_checker_dev_20261017/outputs/episode_{ep:03d}_geometry_contacts.json.gz'
  fs=json.loads(gzip.decompress(p.read_bytes()))
  for i in window:
   f=fs[i];cs=[c for c in f['contacts'] if 104 in (c['geom1'],c['geom2'])]
   rows.append(dict(episode=ep,run_id=f['run_id'],frame=i,time=f['time'],nominal_geometry_time=f['geometry_nominal_time'],object_id='cream_cheese_1',bounds=json.dumps(bounds(f,gs[104])),contact_partners=json.dumps(sorted({c['geom2'] if c['geom1']==104 else c['geom1'] for c in cs})),contact_count=len(cs),physical_event_verdict='not_assigned',source=str(p.relative_to(ROOT)),source_sha256=sha(p)))
 csvwrite(HERE/'DIAGNOSTIC_WINDOWS.csv',rows)
if __name__=='__main__':main()
