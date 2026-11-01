"""Exclusive-create allowlisted archive receiver; no source writes."""
import hashlib,sys,socket
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase5d-object-task02')

def main():
 assert socket.gethostname().lower()=='hestia';archive,phase=sys.argv[1:]
 plan=load(HERE/'SOURCE_PLAN.json');wanted={r['archive_member']:r for r in plan['files'] if r['archive']==archive and r['phase']==phase};assert wanted
 stream=sys.stdin.buffer;seen=set();rows=[]
 while True:
  line=stream.readline()
  if not line:break
  name=line.decode().rstrip('\n');size=int(stream.readline());r=wanted[name];assert size==r['bytes'] and name not in seen
  p=Path(r['restored_path']);assert p.resolve().is_relative_to(DEST);p.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();left=size
  with p.open('xb') as out:
   while left:
    block=stream.read(min(left,1024**2))
    if not block:raise ValueError('truncated stream')
    out.write(block);h.update(block);left-=len(block)
  actual=h.hexdigest()
  if r['expected_sha256']:assert actual==r['expected_sha256']
  rows.append({**r,'sha256':actual});seen.add(name);print('Received '+str(p.relative_to(DEST)),file=sys.stderr,flush=True)
 assert seen==set(wanted)
 write_new(DEST/('receipt-'+phase+'-'+Path(archive).name+'.json'),rows)
if __name__=='__main__':main()
