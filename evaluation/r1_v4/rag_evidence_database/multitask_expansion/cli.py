"""Measurement retrieval only; bounded optional semantic ranking."""
import argparse,json
from pathlib import Path
from evaluation.r1_v4.provenance import canonical,write_new,load
from evaluation.r1_v4.rag_evidence_database.store import Store
from evaluation.r1_v4.rag_evidence_database.search import Query,search

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=('build','check','query','semantic-build','semantic-check','semantic-query'));p.add_argument('--database',type=Path,required=True);p.add_argument('--query',type=Path);p.add_argument('--sidecar',type=Path);p.add_argument('--text');p.add_argument('--report',type=Path);a=p.parse_args()
 if a.command in ('query','semantic-query') and a.query is None:p.error('--query is required')
 if a.command.startswith('semantic-') and a.sidecar is None:p.error('--sidecar is required')
 if a.command=='semantic-query' and not a.text:p.error('--text is required')
 if a.command!='semantic-query' and a.text is not None:p.error('--text is semantic only; put FTS text in query JSON')
 if a.command=='build':
  from .build import populate
  result=populate(a.database)
 else:
  db=Store(a.database)
  try:
   if a.command=='check':result=db.check()
   elif a.command=='query':result=search(db,Query(**load(a.query)))
   else:
    from .semantic import Encoder,SemanticIndex,build,integrity
    encoder=Encoder()
    if a.command=='semantic-build':result=build(db,a.sidecar,encoder)
    else:
     index=SemanticIndex(a.sidecar,db,encoder)
     try:result=integrity(index) if a.command=='semantic-check' else index.retrieve(Query(**load(a.query)),a.text)
     finally:index.close()
  finally:db.close()
 if a.report:write_new(a.report,result)
 print(canonical(result).decode())
if __name__=='__main__':main()
