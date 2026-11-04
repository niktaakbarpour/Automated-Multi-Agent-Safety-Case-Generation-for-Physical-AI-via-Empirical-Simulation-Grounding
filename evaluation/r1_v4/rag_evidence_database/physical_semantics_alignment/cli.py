"""Verified physical-contract queries require an explicitly trusted release database hash."""
import argparse,json
from pathlib import Path
from .config import WORK,HERE
from .store import PhysicalStore
from .retrieve import PhysicalQuery,retrieve

def main():
 p=argparse.ArgumentParser();p.add_argument('--database',type=Path,default=WORK/'expanded.sqlite');p.add_argument('--database-sha256',required=True);p.add_argument('--query',required=True,type=Path);p.add_argument('--semantic-text');a=p.parse_args();db=PhysicalStore(a.database,expected_sha256=a.database_sha256)
 try:
  encoder=None
  if a.semantic_text:
   from evaluation.r1_v4.rag_evidence_database.multitask_expansion.semantic import Encoder
   encoder=Encoder()
  print(json.dumps(retrieve(db,PhysicalQuery(**json.loads(a.query.read_text())),encoder=encoder,semantic_text=a.semantic_text),sort_keys=True))
 finally:db.close()
if __name__=='__main__':main()
