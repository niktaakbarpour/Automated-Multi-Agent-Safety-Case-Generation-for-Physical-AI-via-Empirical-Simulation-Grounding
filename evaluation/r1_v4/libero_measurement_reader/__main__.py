"""Read-only CLI; outputs are new disk1 files or stdout, never evidence sources."""
import argparse,socket,sys
from pathlib import Path
from evaluation.r1_v4.provenance import canonical,write_new
from .reader import read

def main(argv=None):
 if socket.gethostname().lower()!='hestia':raise RuntimeError('Reader runs on Hestia')
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
 p.add_argument('--episode',type=int,required=True);p.add_argument('--frames',type=int,nargs='*')
 p.add_argument('--output',type=Path);args=p.parse_args(argv)
 result=read(args.root,args.episode,args.frames)
 if args.output:
  out=args.output.resolve()
  if not out.is_relative_to('/disk/1/data/niktakbr') or out.is_relative_to(args.root.resolve()):p.error('Output must be fresh owned disk1 path outside source root')
  write_new(out,result)
 else:sys.stdout.buffer.write(canonical(result)+b'\n')
 return 0 if result.status=='verified_measurements' else 1
if __name__=='__main__':raise SystemExit(main())
