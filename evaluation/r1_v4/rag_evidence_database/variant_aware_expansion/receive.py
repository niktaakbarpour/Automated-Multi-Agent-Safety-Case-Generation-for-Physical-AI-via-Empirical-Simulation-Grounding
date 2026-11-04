"""Allowlisted exclusive-create streaming receiver; no analysis on Alliance."""
import hashlib,socket,sys
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase5f-evidence')

def main():
 assert socket.gethostname().lower()=='hestia';archive,phase=sys.argv[1:3];plan=load(HERE/'COHORT.json');transfer=sys.argv[3] if len(sys.argv)>3 else None
 wanted={r['archive_member']:r for r in plan['files'] if r['archive']==archive and r['phase']==phase};assert wanted
 if transfer:
  batch=load(HERE/'TRANSFER_BATCHES.json')[transfer];assert batch['archive']==archive and batch['phase']==phase;wanted={name:wanted[name] for name in batch['members']}
 stream=sys.stdin.buffer;rows=[];seen=set()
 while True:
  line=stream.readline()
  if not line:break
  name=line.decode().rstrip('\n');size=int(stream.readline());r=wanted[name];assert name not in seen and size==r['bytes'];p=Path(r['restored_path']);assert p.resolve().is_relative_to(DEST);p.parent.mkdir(parents=True,exist_ok=True)
  h=hashlib.sha256();left=size
  with p.open('xb') as out:
   while left:
    block=stream.read(min(left,1024**2))
    if not block:raise ValueError('truncated transfer')
    out.write(block);h.update(block);left-=len(block)
  actual=h.hexdigest()
  if r['expected_sha256']:assert actual==r['expected_sha256']
  rows.append({**r,'sha256':actual});seen.add(name);print('Received '+str(p.relative_to(DEST)),file=sys.stderr,flush=True)
 assert seen==set(wanted);write_new(DEST/('receipt-'+(transfer or phase+'-'+Path(archive).name)+'.json'),rows)
if __name__=='__main__':main()
