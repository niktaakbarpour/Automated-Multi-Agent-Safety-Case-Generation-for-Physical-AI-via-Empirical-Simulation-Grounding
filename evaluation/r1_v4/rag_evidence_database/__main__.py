"""Build, resume, query, integrity and export commands; Hestia only."""
import argparse,socket,resource
from pathlib import Path
from evaluation.r1_v4.provenance import load,canonical
from .store import Store
from .build import populate
from .search import search,Query

def main():
 if socket.gethostname().lower()!='hestia':raise RuntimeError('Hestia only')
 resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 for cmd in ('build','query','integrity','export','migrate','catalog'):
  q=s.add_parser(cmd);q.add_argument('database',type=Path)
  if cmd=='query':q.add_argument('query',type=Path)
  if cmd=='catalog':q.add_argument('--execution');q.add_argument('--text')
 args=p.parse_args()
 if args.command=='build':value=populate(args.database)
 else:
  db=Store(args.database,writable=args.command=='migrate')
  try:
   from .catalog import catalog_search
   value=catalog_search(db,args.execution,text=args.text) if args.command=='catalog' else search(db,Query(**load(args.query))) if args.command=='query' else db.check() if args.command=='integrity' else db.export() if args.command=='export' else {'extension_version':'1.0.0','evidence_ids_preserved':True}
  finally:db.close()
 print(canonical(value).decode())
if __name__=='__main__':main()
