"""Hestia-only selective archive receiver. Sources are never modified."""
import hashlib,json,socket,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEST=Path('/disk/1/data/niktakbr/r1-v4-phase2b2-development-evidence')
def main():
 assert socket.gethostname().lower()=='hestia'
 plan=json.loads((HERE/'RESTORATION_PLAN.json').read_text())
 selected={r['archive_member']:r for r in plan['files'] if r['destination_archive']==sys.argv[1]}
 assert selected and DEST.resolve().is_relative_to('/disk/1/data/niktakbr')
 seen=set();rows=[];stream=sys.stdin.buffer
 while True:
  name=stream.readline()
  if not name:break
  name=name.decode().rstrip('\n');size=int(stream.readline());r=selected[name]
  assert name not in seen and size==r['size']
  rel=Path(r['restoration_relative_path']);assert not rel.is_absolute() and '..' not in rel.parts
  p=DEST/rel;assert p.resolve().is_relative_to(DEST.resolve())
  p.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256()
  with p.open('xb') as out:
   left=size
   while left:
    block=stream.read(min(left,1024*1024))
    if not block:raise ValueError('truncated_transport:'+name)
    out.write(block);h.update(block);left-=len(block)
  digest=h.hexdigest()
  if r['expected_sha256'] is not None:assert digest==r['expected_sha256'],name
  seen.add(name);rows.append(dict(original_path=r['logical_path'],restored_path=str(p),archive=r['destination_archive'],archive_member=name,bytes=size,sha256=digest,expected_sha256=r['expected_sha256'],expected_match=digest==r['expected_sha256'] if r['expected_sha256'] else None))
  print('Received '+rel.as_posix(),file=sys.stderr,flush=True)
 assert seen==set(selected),(set(selected)-seen)
 report=DEST/('receipt-'+Path(sys.argv[1]).name+'.json')
 with report.open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
if __name__=='__main__':main()
