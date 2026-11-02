"""Read-only variant registry, lexical retrieval and optional local semantic query."""
import argparse
from pathlib import Path
from evaluation.r1_v4.provenance import load,canonical
from .plan import WORK
from .registry import VariantStore
from .retrieval import VariantQuery,retrieve

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=('query','semantic-query','check','variants'));p.add_argument('--database',type=Path,default=WORK/'expanded.sqlite');p.add_argument('--query',type=Path);p.add_argument('--sidecar',type=Path);p.add_argument('--text');a=p.parse_args()
 if a.command in ('query','semantic-query') and not a.query:p.error('--query JSON required')
 if a.command=='semantic-query' and (not a.sidecar or not a.text):p.error('--sidecar and --text required')
 if a.command!='semantic-query' and (a.sidecar or a.text):p.error('Semantic arguments are not accepted in lexical/check mode')
 db=VariantStore(a.database)
 try:
  if a.command=='check':result=db.variant_check()
  elif a.command=='variants':result={'variants':[{'variant_id':v,'xml_sha256':x,'asset_digest':d,'executions':[r[0] for r in db.db.execute('SELECT execution FROM rag_execution_env WHERE variant_id=? ORDER BY execution',(v,))]} for v,x,d in db.db.execute('SELECT id,xml_sha256,asset_digest FROM rag_env_variants ORDER BY id')]}
  elif a.command=='query':result=retrieve(db,VariantQuery(**load(a.query)))
  else:
   from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder,SemanticIndex
   index=SemanticIndex(a.sidecar,db,Encoder())
   try:result=retrieve(db,VariantQuery(**load(a.query)),semantic_index=index,semantic_text=a.text)
   finally:index.close()
  print(canonical(result).decode())
 finally:db.close()
if __name__=='__main__':main()
