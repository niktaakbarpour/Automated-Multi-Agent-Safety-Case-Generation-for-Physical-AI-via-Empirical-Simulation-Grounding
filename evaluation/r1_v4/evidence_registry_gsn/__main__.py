"""Bounded registry CLI, with explicit new-output writes."""
import argparse,socket
from pathlib import Path
from evaluation.r1_v4.provenance import load,canonical
from .registry import Registry
from .retrieval import Query,retrieve
from .demo import demonstrate

def main():
 if socket.gethostname().lower()!='hestia':raise RuntimeError('Research execution requires Hestia')
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 d=sub.add_parser('demo');d.add_argument('output',type=Path)
 for cmd in ('export','integrity','query'):
  parser=sub.add_parser(cmd);parser.add_argument('database',type=Path)
  if cmd=='query':parser.add_argument('query',type=Path)
 args=p.parse_args()
 if args.command=='demo':value=demonstrate(args.output)
 else:
  r=Registry(args.database)
  try:value=retrieve(r,Query(**load(args.query))) if args.command=='query' else r.export() if args.command=='export' else r.integrity()
  finally:r.close()
 print(canonical(value).decode())
if __name__=='__main__':main()
