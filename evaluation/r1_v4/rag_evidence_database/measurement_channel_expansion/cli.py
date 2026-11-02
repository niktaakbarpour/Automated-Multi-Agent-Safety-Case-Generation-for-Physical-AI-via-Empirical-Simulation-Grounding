"""JSON channel queries, preserving the separate Phase5F VariantQuery interface."""
import argparse,json
from pathlib import Path
from .channels import ChannelStore,WORK
from .retrieve import ChannelQuery,retrieve

def main():
 p=argparse.ArgumentParser();p.add_argument('--database',type=Path,default=WORK/'expanded.sqlite');p.add_argument('--query',type=Path,required=True);p.add_argument('--semantic-text');a=p.parse_args();q=ChannelQuery(**json.loads(a.query.read_text()));db=ChannelStore(a.database)
 try:
  encoder=None
  if a.semantic_text:
   from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder
   encoder=Encoder()
  print(json.dumps(retrieve(db,q,encoder=encoder,semantic_text=a.semantic_text),sort_keys=True))
 finally:db.close()
if __name__=='__main__':main()
