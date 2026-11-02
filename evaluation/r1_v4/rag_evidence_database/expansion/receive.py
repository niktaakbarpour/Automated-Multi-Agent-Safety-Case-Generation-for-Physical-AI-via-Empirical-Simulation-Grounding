"""Exact allowlist streaming receiver, Hestia only, originals never overwritten."""
import hashlib,socket,sys
from pathlib import Path
from evaluation.r1_v4.provenance import load,write_new
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase5c-development-evidence')

def main():
 assert socket.gethostname().lower()=='hestia'
 plan=load(HERE/'RESTORATION_PLAN.json');archive=sys.argv[1]
 wanted={r['archive_member']:r for r in plan['files'] if r['archive']==archive}
 assert wanted;seen=set();rows=[];stream=sys.stdin.buffer
 while True:
  line=stream.readline()
  if not line:break
  name=line.decode().rstrip('\n');size=int(stream.readline());r=wanted[name]
  assert name not in seen and size==r['receipt_member_bytes']
  rel=Path(r['original_path']).relative_to('/disk/1/data/niktakbr/openvla-7b-oft-finetuned-libero-spatial-object-goal-10-libero')
  p=DEST/rel;assert p.resolve().is_relative_to(DEST);p.parent.mkdir(parents=True,exist_ok=True)
  h=hashlib.sha256();left=size
  with p.open('xb') as output:
   while left:
    block=stream.read(min(left,1024**2))
    if not block:raise ValueError('truncated stream:'+name)
    output.write(block);h.update(block);left-=len(block)
  checksum=h.hexdigest()
  if r['expected_sha256'] is not None:assert checksum==r['expected_sha256'],name
  rows.append({**r,'restored_path':str(p),'bytes':size,'sha256':checksum,'historical_hash_match':checksum==r['expected_sha256'] if r['expected_sha256'] else None})
  seen.add(name);print('Received '+str(rel),file=sys.stderr,flush=True)
 assert seen==set(wanted),(len(seen),len(wanted))
 write_new(DEST/('receipt-'+Path(archive).name+'.json'),rows)
if __name__=='__main__':main()
